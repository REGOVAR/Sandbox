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


from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, Sequence, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.ext.declarative import declarative_base

from pysam import VariantFile
from poc_tools import *



print("Benchmark n°7\n - PySam\n - Model : Sample & Variant & SampleVariant (id on chr, pos, ref, alt)\n - SQLAlchemy using raw sql query\n - Parsing on main thread - SQL query exec on multithread")




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODEL
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Init SQLAlchemy database engine thanks to a connection string
Base = declarative_base()

class SampleVariant(Base):
	__tablename__ = '_3_sample_variant'
	sample_id = Column(Integer, ForeignKey('_3_sample.id'),   primary_key=True, nullable=False)
	chr       = Column(String,   primary_key=True, nullable=False)
	pos       = Column(Integer,  primary_key=True, nullable=False)
	ref       = Column(String,   primary_key=True, nullable=False)
	alt       = Column(String,   primary_key=True, nullable=False)
	# genotype = Column(JSONB, nullable=True)
	# infos = Column(Array(String, dimensions=2))
	__table_args__ = (Index('_3_sample_variant_idx', 'sample_id', 'chr', 'pos', 'ref', 'alt', unique=True), UniqueConstraint('sample_id', 'chr', 'pos', 'ref', 'alt', name='_3_sample_variant_uc'), )
	#variants = relationship("Variant", back_populates="samples")
	#samples  = relationship("Sample", back_populates="variants")

class Sample(Base):
	__tablename__ = '_3_sample'
	id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
	name = Column(String)
	description = Column(String)
	#variants = relationship("SampleVariant", back_populates="samples")
	def __str__(self):
		return "<Sample(name='%s')>" % (self.name)


class Variant(Base):
	__tablename__ = '_3_variant'
	bin = Column(Integer)
	chr = Column(String,  primary_key=True, nullable=False)
	pos = Column(Integer, primary_key=True, nullable=False)
	ref = Column(String,  primary_key=True, nullable=False)
	alt = Column(String,  primary_key=True, nullable=False)
	is_transition = Column(Boolean)
	#samples = relationship("SampleVariant", back_populates="variants")
	__table_args__ = (Index('_3_variant_idx', 'chr', 'pos', 'ref', 'alt', unique=True), UniqueConstraint('chr', 'pos', 'ref', 'alt', name='_3_variant_uc'), )

	def __str__(self):
		return "<Variant(id='%s', chr='%s', pos='%s', ref='%s', alt='%s')>" % (self.id, self.chr, self.pos, self.ref, self.alt)





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
		samples = {i : get_or_create(session, Sample, name=i)[0] for i in vcf_reader.samples}
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
		bar = Bar('\tparsing  : ', max=records_count, suffix='%(percent).1f%% - %(elapsed_td)s')
		sql_head1 = "INSERT INTO _7_variant (chr, pos, ref, alt, is_transition) VALUES "
		sql_head2 = "INSERT INTO _7_sample_variant (sample_id, chr, pos, ref, alt) VALUES "
		sql_tail = " ON CONFLICT DO NOTHING"
		sql_query1 = ""
		sql_query2 = ""
		count = 0
		for r in vcf_reader: 
			bar.next()
			chrm = normalize_chr(str(r.chrom))
			
			for sn in r.samples:
				s = r.samples.get(sn)

				pos, ref, alt = normalize(r.pos, r.ref, s.alleles[0])

				if alt != ref :
					sql_query1 += "(%s, '%s', %s, '%s', '%s', %s)," % (chrm, str(pos), ref, alt, is_transition(ref, alt))
					sql_query2 += "(%s, '%s', %s, '%s', '%s', %s)," % (str(samples[sn].id), chrm, str(pos), ref, alt)
					count += 1

				pos, ref, alt = normalize(r.pos, r.ref, s.alleles[1])
				if alt != ref :
					sql_query1 += "(%s, '%s', %s, '%s', '%s', %s)," % (chrm, str(pos), ref, alt, is_transition(ref, alt))
					sql_query2 += "(%s, '%s', %s, '%s', '%s', %s)," % (str(samples[sn].id), chrm, str(pos), ref, alt)
					count += 1

				# manage split big request to avoid sql out of memory transaction
				if count >= 1000000:
					count = 0
					transaction1 = sql_head1 + sql_query1[:-1] + sql_tail
					transaction2 = sql_head2 + sql_query2[:-1] + sql_tail
					threading.Thread(target=exec_sql_query, args=(transaction1, transaction2)).start()
					sql_query1 = ""
					sql_query2 = ""

		bar.finish()
		end = datetime.datetime.now()
		print("\tparsing done   : " , end, " => " , (end - start).seconds, "s")
		transaction1 = sql_head1 + sql_query1[:-1] + sql_tail
		transaction2 = sql_head2 + sql_query2[:-1] + sql_tail
		connection.execute(transaction1)
		connection.execute(transaction2)

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
	result = connection.execute("SELECT COUNT(*) FROM _7_sample")
print("Sample total : " , result.first()[0], " (", t, ")")

#count sample_variant
with Timer() as t:
	result = connection.execute("SELECT COUNT(*) FROM _7_sample_variant")
print("Variant total : " , result.first()[0], " (", t, ")")

#count variant
with Timer() as t:
	result = connection.execute("SELECT COUNT(*) FROM _7_variant")
print("Distinct Variant total : " , result.first()[0], " (", t, ")")


#count variant / sample
with Timer() as t:
	result = connection.execute("SELECT sample_id, COUNT(*) FROM _7_sample_variant GROUP BY sample_id")
print("\nCount variant by sample (", t, ")")
for r in result:
	print ("\tSample n°", r[0], " : ", r[1], " variants")


# Get all variant with REF=A on chr5 for the sample 1
with Timer() as t:
	result = connection.execute("SELECT pos, alt FROM _7_sample_variant WHERE sample_id = 1 AND chr = '5' AND ref = 'A'")
print("\nList variant of sample n°1, on chr5, with ref A : " , result.rowcount, " results (", t, ")")
print ("\t", reprlib.repr((result)))


# Test group by same table : 
with Timer() as t:
	result = connection.execute("SELECT chr, pos, ref, alt, count(sample_id ) as \"used\" FROM _7_sample_variant GROUP BY chr, pos, ref, alt ORDER BY \"used\" DESC")

print("\nCount how many variant are common by sample : " , result.rowcount, " results (", t, ")")
t = 0
c = 0
print("    sample : variant count")
for r in result:
	if t > int(r[4]):
		print("\t", t, " : ", c)
		c = 0
	t = int(r[4])
	c += 1


with Timer() as t:
	result = connection.execute("SELECT s.sample_id, v.is_transition, count(*) FROM _7_variant v INNER JOIN _7_sample_variant s ON v.chr = s.chr AND v.pos = s.pos AND v.ref = s.ref AND v.alt = s.alt GROUP BY v.is_transition, s.sample_id ORDER BY s.sample_id, v.is_transition")
print("\nCheck Sequencing integrity : " , result.rowcount, " results (", t, ")")
print("    sample : transition / transversion")
s = 0
tv = 0
for r in result:
	if int(r[0]) > s :
		print("\tSample n°", s, " : ", r[2], "/", tv, " ", round(tv / r[2],2))
		c = 0
	s = int(r[0])
	tv = int(r[2])