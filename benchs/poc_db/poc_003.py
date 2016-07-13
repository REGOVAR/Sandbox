#!env/python3
# coding: utf-8
import os
import sys
import datetime
import sqlalchemy
import subprocess

from progress.bar import Bar

from sqlalchemy import Table, Column, Integer, String, ForeignKey, Sequence, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.ext.declarative import declarative_base

import vcf

print("Benchmark SQLAlchemy - Model schema n°2")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# TOOLS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def connect(user, password, db, host='localhost', port=5432):
	'''Returns a connection and a metadata object'''
	url = 'postgresql://{}:{}@{}:{}/{}'
	url = url.format(user, password, host, port, db)
	con = sqlalchemy.create_engine(url, client_encoding='utf8')
	meta = sqlalchemy.MetaData(bind=con)
	return con, meta


def get_or_create(session, model, defaults=None, **kwargs):
	if defaults is None:
		defaults = {}
	try:
		query = session.query(model).filter_by(**kwargs)

		instance = query.first()

		if instance:
			return instance, False
		else:
			session.begin(nested=True)
			try:
				params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
				params.update(defaults)
				instance = model(**params)

				session.add(instance)
				session.commit()

				return instance, True
			except IntegrityError as e:
				session.rollback()
				instance = query.one()

				return instance, False
	except Exception as e:
		raise e




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
	#genotype = Column(JSONB, nullable=True)
	#infos = Column(ARRAY(String, dimensions=2))
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
	bin  = Column(Integer)
	chr = Column(String,  primary_key=True, nullable=False)
	pos = Column(Integer, primary_key=True, nullable=False)
	ref = Column(String,  primary_key=True, nullable=False)
	alt = Column(String,  primary_key=True, nullable=False)
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
	if (chrm.startswith("CHR")):
		chrm = chrm[3:]
	return chrm


# retrieve all vcf in the current directory
#directory = os.path.dirname(os.path.realpath(__file__))


print("IMPORT VCF FILES")
start_0 = datetime.datetime.now()



for file in os.listdir("."):
	if file.endswith(".vcf") or file.endswith(".vcf.gz"):
		vcf_reader = vcf.Reader(filename=file)

		# get samples in the VCF 
		session = Session(connection)
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
		start = datetime.datetime.now()
		print("Importing file ", file, "\n\r\trecords  : ", records_count, "\n\r\tsamples  : ", [s for s in samples.keys()], "\n\r\tstart    : ", start)
		bar = Bar('\tparsing  : ', max=records_count, suffix='%(percent).1f%% - %(elapsed_td)s')
		sql_query1 = "INSERT INTO _3_variant (chr, pos, ref, alt) VALUES "
		sql_query2 = "INSERT INTO _3_sample_variant (sample_id, chr, pos, ref, alt) VALUES "
		for r in vcf_reader: 
			bar.next()
			for i in r.samples:
				if i.gt_bases is None:
					continue
				alt = i.gt_bases.split('/')
				chrm = normalize_chr(str(r.CHRM))

				sql_query1 += "('%s', %s, '%s', '%s')," % (chrm, str(r.POS), str(r.REF), str(alt[0]))
				sql_query2 += "(%s, '%s', %s, '%s', '%s')," % (str(samples[i.sample].id), chrm, str(r.POS), str(r.REF), str(alt[0]))
				if i.is_het:
					sql_query1 += "('%s', %s, '%s', '%s')," % (chrm, str(r.POS), str(r.REF), str(alt[1]))
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




print("IMPORT VCF FILES DONE : ", (end - start_0).seconds)
print("")
print("TEST SOME REQUEST")




