#!env/python3
# coding: utf-8
import os
import sys
import datetime
import sqlalchemy
import subprocess
import reprlib
import time

from progress.bar import Bar

from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, Sequence, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.ext.declarative import declarative_base

import vcf
from poc_tools import *

print("Benchmark SQLAlchemy - Model schema n°2")




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

# List tables
#for t in Base.metadata.tables: print(t)



# Test create session/data
#session = Session(connection)
#s = Sample(name="SampleX01")
#session.add(s)
# s.id <- not set
#session.commit()
# s.id <- set with DB auto increment id = 1





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# IMPORT VCF Data
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def normalize_chr(chrm):
	chrm = str(r.CHROM).upper()
	if (chrm.startswith("CHROM")):
		chrm = chrm[5:]
	if (chrm.startswith("CHRM")):
		chrm = chrm[4:]
	if (chrm.startswith("CHR")):
		chrm = chrm[3:]
	return chrm


def get_alt(alt):
	if ('|' in alt):
		return alt.split('|')
	else:
		return alt.split('/')

# retrieve all vcf in the current directory
#directory = os.path.dirname(os.path.realpath(__file__))


print("IMPORT VCF FILES")
start_0 = datetime.datetime.now()

session = Session(connection)

for file in os.listdir("."):
	if file.endswith(".vcf") or file.endswith(".vcf.gz"):

		start = datetime.datetime.now()

		vcf_reader = vcf.Reader(filename=file)

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
		sql_query1 = "INSERT INTO _3_variant (chr, pos, ref, alt, is_transition) VALUES "
		sql_query2 = "INSERT INTO _3_sample_variant (sample_id, chr, pos, ref, alt) VALUES "
		for r in vcf_reader: 
			bar.next()
			for i in r.samples:
				if i.gt_bases is None:
					continue
				alt = get_alt(i.gt_bases)
				chrm = normalize_chr(str(r.CHROM))

				if alt[0] != str(r.REF) :
					sql_query1 += "('%s', %s, '%s', '%s', %s)," % (chrm, str(r.POS), str(r.REF), str(alt[0]), r.is_transition)
					sql_query2 += "(%s, '%s', %s, '%s', '%s')," % (str(samples[i.sample].id), chrm, str(r.POS), str(r.REF), str(alt[0]))
				if alt[1] != str(r.REF) :
					sql_query1 += "('%s', %s, '%s', '%s', %s)," % (chrm, str(r.POS), str(r.REF), str(alt[1]), r.is_transition)
					sql_query2 += "(%s, '%s', %s, '%s', '%s')," % (str(samples[i.sample].id), chrm, str(r.POS), str(r.REF), str(alt[1]))

		bar.finish()
		end = datetime.datetime.now()
		print("\tparsing done   : " , end, " => " , (end - start).seconds, "s")
		sql_query1 = sql_query1[:-1] + " ON CONFLICT DO NOTHING"
		sql_query2 = sql_query2[:-1] + " ON CONFLICT DO NOTHING"
		connection.execute(sql_query1)
		connection.execute(sql_query2)
		end = datetime.datetime.now()
		print("\tdb import done : " , end, " => " , (end - start).seconds, "s")
		print("")



end = datetime.datetime.now()

print("IMPORT ALL VCF FILES DONE in ", (end - start_0).seconds), "s"
print("")
print("TEST SOME REQUESTS")



# count sample
with Timer() as t:
	result = session.query(Sample).count()
print("\nSample total : " , result, " (", t, ")")

#count sample_variant
with Timer() as t:
	result = session.query(SampleVariant).count()
print("SampleVariant total : " , result, " (", t, ")")

#count variant
with Timer() as t:
	result = session.query(Variant).count()
print("Variant total : " , result, " (", t, ")")


#count variant / sample
with Timer() as t:
	result = session.query(SampleVariant.sample_id, func.count(SampleVariant.sample_id)).group_by(SampleVariant.sample_id).all()
print("\nCount variant by sample (", t, ")")
for r in result:
	print ("\tSample n°", r[0], " : ", r[1], " variants")

# Get all variant with REF=A on chr5 for the sample 1
with Timer() as t:
	result = session.query(SampleVariant.pos, SampleVariant.alt).filter(SampleVariant.sample_id == 1).filter(SampleVariant.chr == '5').filter(SampleVariant.ref == 'A').all()
print("\nList variant of sample n°1, on chr5, with ref A : " , len(result), " results (", t, ")")
print ("\t", reprlib.repr((result)))


# Test group by same table : 
with Timer() as t:
	usedColumn = func.count(SampleVariant.pos)
	result = session.query(SampleVariant.pos, SampleVariant.ref, SampleVariant.alt, usedColumn).group_by(SampleVariant.pos, SampleVariant.ref, SampleVariant.alt).order_by(usedColumn.desc()).all()
print("\nCount how many variant are common by sample : " , len(result), " results (", t, ")")
t = 0
c = 0
print("    sample : variant count")
for r in result:
	if t > r[3]:
		print("\t", t, " : ", c)
		c = 0
	t = r[3]
	c += 1

# Test join right 2 tables on big request
with Timer() as t:
	usedColumn = func.count(SampleVariant.pos)
	result = session.query(SampleVariant.sample_id, Variant.is_transition, func.count(SampleVariant.pos)).join(SampleVariant.pos == Variant.pos).group_by(SampleVariant.sample_id, Variant.is_transition).order_by(SampleVariant.sample_id.desc()).all()
print("\nCount how many variant are common by sample : " , len(result), " results (", t, ")")