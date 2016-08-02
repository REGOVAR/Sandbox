#!env/python3
# coding: utf-8
import os
import sys
import datetime
import sqlalchemy
import subprocess
import reprlib
import time
import psycopg2
import threading

from progress.bar import Bar


from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, Sequence, UniqueConstraint, Index, func, distinct
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.ext.declarative import declarative_base

from pysam import VariantFile
from poc_tools import *



print("Benchmark n°9\n - PySam\n - Model : Sample & Variant + FK on array field in Variant\n - SQLAlchemy using raw sql query\n - Parsing on main thread - SQL query exec on multithread")



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODEL
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Init SQLAlchemy database engine thanks to a connection string
Base = declarative_base()


class Sample(Base):
	__tablename__ = '_9_sample'
	id = Column(Integer, Sequence('_9_sample_1_seq'), primary_key=True, nullable=False)
	name = Column(String)
	def __str__(self):
		return "<Sample(name='%s')>" % (self.name)


class Variant(Base):
	__tablename__ = '_9_variant'
	bin = Column(Integer)
	chr = Column(String,  primary_key=True, nullable=False)
	pos = Column(Integer, primary_key=True, nullable=False)
	ref = Column(String,  primary_key=True, nullable=False)
	alt = Column(String,  primary_key=True, nullable=False)
	sample = Column (postgresql.ARRAY(Integer))
	is_transition = Column(Boolean)
	__table_args__ = (Index('_9_variant_idx', 'chr', 'pos', 'ref', 'alt', unique=True), UniqueConstraint('chr', 'pos', 'ref', 'alt', name='_9_variant_uc'), Index('_9_sample_idx', 'sample'))
	def __str__(self):
		return "<Variant(chr='%s', pos='%s', ref='%s', alt='%s'>" % (self.chr, self.pos, self.ref, self.alt)





#Connect to database
connection, meta = connect('regovar', 'regovar', 'regovar-dev')
# Associate model with connected database
Base.metadata.create_all(connection)





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# IMPORT VCF Data
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
print("IMPORT VCF FILES")
# Start a worker processes.


start_0 = datetime.datetime.now()
session = Session(connection)
total_sql_execution = 0
job_in_progress = 0

def exec_sql_query(raw_sql):
	global job_in_progress
	job_in_progress += 1
	connection.execute(raw_sql)
	job_in_progress -= 1

for file in os.listdir("."):
	if file.endswith(".vcf") or file.endswith(".vcf.gz"):
		start = datetime.datetime.now()

		vcf_reader = VariantFile(file)

		# get samples in the VCF 
		samples = {i : get_or_create(session, Sample, name=i)[0] for i in list((vcf_reader.header.samples))}
		session.commit()

		# console verbose
		bashCommand = 'grep -v "^#" ' + str(file) +' | wc -l'
		if file.endswith(".vcf.gz"):
			bashCommand = "z" + bashCommand
		
		# process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
		process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		cmd_out = process.communicate()[0]
		records_count = int(cmd_out.decode('utf8'))		
		# records_count = 5000

		# parsing vcf file
		print("Importing file ", file, "\n\r\trecords  : ", records_count, "\n\r\tsamples  :  (", len(samples.keys()), ") ", reprlib.repr([s for s in samples.keys()]), "\n\r\tstart    : ", start)
		bar = Bar('\tparsing  : ', max=records_count, suffix='%(percent).1f%% - %(elapsed_td)s' + " (" + str(job_in_progress) + " sql job in progress) " )
		sql_query = ""
		sql_head = "INSERT INTO _9_variant (sample, chr, pos, ref, alt, is_transition) VALUES "
		sql_tail = " ON CONFLICT (chr, pos, ref, alt) DO UPDATE SET sample = _9_variant.sample || EXCLUDED.sample"
		count = 0
		for r in vcf_reader.fetch(): 
			bar.next()
			chrm = normalize_chr(str(r.chrom))
			

			for a in r.alleles:
				pos, ref, alt = normalize(r.pos, r.ref, a)

				if alt != ref :
					query_sample = ""
					for sn in r.samples:
						s = r.samples.get(sn)
						if s.alleles[0] == a:
							query_sample += str(samples[sn].id) + ","
						if s.alleles[1] == a:
							query_sample += str(samples[sn].id) + ","

					if query_sample != "":
						sql_query += "(ARRAY[%s], '%s', %s, '%s', '%s', %s)," % (query_sample[:-1], chrm, str(pos), ref, alt, is_transition(ref, alt))
						count += 1


				# manage split big request to avoid sql out of memory transaction
				if count >= 500000:
					count = 0
					transaction = sql_head + sql_query[:-1] + sql_tail
					connection.execute(transaction)
					#threading.Thread(target=exec_sql_query, args=(transaction,)).start()
					sql_query = ""



		bar.finish()
		end = datetime.datetime.now()
		print("\tparsing done   : " , end, " => " , (end - start).seconds, "s")
		if count > 0:
			transaction = sql_head + sql_query[:-1] + sql_tail
			connection.execute(transaction)
			#connection.execute(transaction)	

		while job_in_progress > 0:
			pass

		end = datetime.datetime.now()

		print("\tdb import done : " , end, " => " , (end - start).seconds, "s")
		print("")


end = datetime.datetime.now()

print("IMPORT ALL VCF FILES DONE in ", (end - start_0).seconds), "s"
print("")
print("TEST SOME REQUESTS")



# count sample
with Timer() as t:
	result = connection.execute("SELECT COUNT(*) FROM _9_sample")
print("Sample total (raw query): " , result.first()[0], " (", t, ")")





#count variant
with Timer() as t:
	result = connection.execute("SELECT SUM(array_length(sample, 1)) FROM _9_variant")
print("\nVariant total : " , result.first()[0], " (", t, ")")

with Timer() as t:
	result = connection.execute("SELECT COUNT(*) FROM _9_variant")
print("Distinct Variant total : " , result.first()[0], " (", t, ")")
result.close()


# #count variant / sample
# with Timer() as t:
# 	result = connection.execute("SELECT sample_id, COUNT(*) FROM _9_variant GROUP BY sample_id")
# print("\nCount variant by sample (", t, ")")
# for r in result:
# 	print ("\tSample n°", r[0], " : ", r[1], " variants")

# Get all variant with REF=A on chr5 for the sample 1
with Timer() as t:
	result = connection.execute("SELECT pos, alt FROM _9_variant WHERE sample @> ARRAY[1] AND chr = '5' AND ref = 'A'")
print("\nList variant of sample n°1, on chr5, with ref A : " , result.rowcount, " results (", t, ")")
print ("\t", reprlib.repr((result)))


# Test group by same table : 
with Timer() as t:
	result = connection.execute("SELECT COUNT(*) as \"total\", array_length(sample, 1) as \"used\" FROM _9_variant GROUP BY \"used\" ORDER BY \"total\" DESC")

print("\nCount how many variant are common by sample : " , result.rowcount, " results (", t, ")")
print("    samples : variant count")
for r in result:
	print ("\t", r[1], " : ", r[0])


# with Timer() as t:
# 	result = connection.execute("SELECT sample_id, is_transition, count(*) FROM _9_variant GROUP BY is_transition, sample_id ORDER BY sample_id, is_transition")
# print("\nCheck Sequencing integrity : " , result.rowcount, " results (", t, ")")
# print("    sample : transition / transversion")
# s = 0
# tv = 0
# for r in result:
# 	if int(r[0]) > s :
# 		print("\tSample n°", s, " : ", r[2], "/", tv, " ", round(tv / r[2],2))
# 		c = 0
# 	s = int(r[0])
# 	tv = int(r[2])





