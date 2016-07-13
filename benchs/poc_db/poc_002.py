#!env/python3
# coding: utf-8
import os
import sys
import datetime
import sqlalchemy
import subprocess

from progress.bar import Bar

from sqlalchemy import Table, Column, Integer, String, ForeignKey, Sequence
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


class Sample(Base):
	__tablename__ = '_2_sample'
	id = Column(Integer, Sequence('_2_sample_1_seq'), primary_key=True, nullable=False)
	name = Column(String)
	def __str__(self):
		return "<Sample(name='%s')>" % (self.name)


class Variant(Base):
	__tablename__ = '_2_variant'
	chr = Column(String, primary_key=True)
	pos = Column(Integer, primary_key=True)
	ref = Column(String, primary_key=True)
	alt = Column(String, primary_key=True)
	sample_id = Column (Integer, ForeignKey('_2_sample.id'), primary_key=True)
	def __str__(self):
		return "<Variant(chr='%s', pos='%s', ref='%s', alt='%s', sample='%s'>" % (self.chr, self.pos, self.ref, self.alt, self.sample_id)





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

# retrieve all vcf in the current directory
#directory = os.path.dirname(os.path.realpath(__file__))



print("IMPORT VCF FILES")


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
		print("Start parsing file : \n\r\tname     : ", file, "\n\r\trecords  : ", records_count, "\n\r\tsamples  : ", [s for s in samples.keys()], "\n\r\tstart    : ", start)
		#bar = Bar('\tprogress : ', max=records_count, suffix='%(percent).1f%% - %(elapsed_td)s')
		for r in vcf_reader: 
			#bar.next()
			for i in r.samples:
				v  = Variant(chr=str(r.CHROM), pos=str(r.POS), ref=str(r.REF), alt=str(r.ALT[0]), sample_id=samples[i.sample].id)
				try:
					session.add(v)
					session.commit()
				except IntegrityError as e:
					session.rollback()
		#bar.finish()
		end = datetime.datetime.now()
		print("\n\r\tdone     : " , end, " => " , (end - start).seconds, "s")
		print("")








