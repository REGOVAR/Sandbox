#!env/python3
# coding: utf-8
import random
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




print("Populate Database")
def connect(user, password, db, host, port):
	'''Returns a connection and a metadata object'''
	url = 'postgresql://{}:{}@{}:{}/{}'
	url = url.format(user, password, host, port, db)
	con = sqlalchemy.create_engine(url, client_encoding='utf8')
	meta = sqlalchemy.MetaData(bind=con)
	return con, meta

def is_transition(ref, alt):
	tr = ref+alt
	if len(ref) == 1 and tr in ('AG', 'GA', 'CT', 'TC'):
		return True
	return False



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODEL
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Init SQLAlchemy database engine thanks to a connection string
Base = declarative_base()


class SampleVariant(Base):
	__tablename__ = '_10_sample_variant'
	sample_id  = Column(Integer, ForeignKey('_10_sample.id'),   primary_key=True, nullable=False)
	chr        = Column(String,   primary_key=True, nullable=False)
	pos        = Column(Integer,  primary_key=True, nullable=False)
	ref        = Column(String,   primary_key=True, nullable=False)
	alt        = Column(String,   primary_key=True, nullable=False)
	variant_id = Column(Integer, ForeignKey('_10_variant.id'), nullable=False)

	__table_args__ = (
		Index('_10_sample_variant_idx1', 'sample_id', 'chr', 'pos', 'ref', 'alt', unique=True), 
		Index('_10_sample_variant_idx2', 'sample_id', 'variant_id', unique=True),
		UniqueConstraint('sample_id', 'chr', 'pos', 'ref', 'alt', name='_10_sample_variant_uc'), )


class Sample(Base):
	__tablename__ = '_10_sample'
	id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
	name = Column(String)
	description = Column(String)
	__table_args__ = (
		Index('_10_sample_idx', 'id', unique=True), 
		UniqueConstraint('id', name='_10_sample_uc'), )

class Variant(Base):
	__tablename__ = '_10_variant'
	id = Column(Integer, primary_key=True)
	bin = Column(Integer)
	chr = Column(String,  nullable=False)
	pos = Column(Integer, nullable=False)
	ref = Column(String,  nullable=False)
	alt = Column(String,  nullable=False)
	is_transition = Column(Boolean)
	regovar_stat = Column(Integer)

	__table_args__ = (
		Index('_10_variant_idx1', 'chr', 'pos', 'ref', 'alt', unique=True), 
		Index('_10_variant_idx2', 'id', unique=True), 
		UniqueConstraint('chr', 'pos', 'ref', 'alt', name='_10_variant_uc'), )






#Connect to database
connection, meta = connect('regovar', 'regovar', 'regovar', "localhost", 5432)
# Associate model with connected database
Base.metadata.create_all(connection)





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# IMPORT VCF Data
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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


# 2 milliards de sample
stotal = 20 #2000000000

# 75.6 milliards de variants = 300M²(pos) x 12(ref->alt) x 21(chr)
var = {"A": ["C", "G", "T"], "C": ["A", "G", "T"], "G": ["A", "C", "T"], "T": ["A", "C", "G"]}
ctotal = 22
ptotal = 300000000
vtotal = 75600000000


# Create Samples
print("Populate DB with Fakes Samples (2 000 000 000) - Press \"space\" to pause the loop)")
sql_head = "INSERT INTO _10_sample (name) VALUES "
sql_query = ""
count = 0

bar = Bar('\tCreate samples  : ', max=stotal, suffix='%(percent).1f%% - %(elapsed_td)s')
for sample_id in range(1,stotal + 1):
	sql_query += "('sample n°%s')," % sample_id
	count += 1
	bar.next()
	if count >= 500000:
		count = 0
		transaction = sql_head + sql_query[:-1]
		threading.Thread(target=exec_sql_query, args=(transaction, )).start()
		sql_query = ""

	# Allow user to pause
	try:
		key = win.getkey()
		if key == " ": # of we got a space then break
			raw_input("Press any Key to continue")
	except: # in no delay mode getkey raise and exeption if no key is press 
		key = None


transaction = sql_head + sql_query[:-1]
threading.Thread(target=exec_sql_query, args=(transaction, )).start()
while job_in_progress > 0:
	if current != job_in_progress:
		print ("\t - remaining sql job : ", job_in_progress)
		current = job_in_progress
	pass
bar.finish()
print ("\n")


# Create Variants
print("Populate DB with Fakes Variant (75 600 000 000) - Press \"space\" to pause the loop)")
sql_head1 = "; INSERT INTO _10_sample_variant (sample_id, chr, pos, ref, alt, variant_id) VALUES "
sql_head2 = "INSERT INTO _10_variant (id, chr, pos, ref, alt, is_transition, regovar_stat) VALUES "
sql_query1 = ""
sql_query2 = ""
variant_id = 1
count = 0
bar = Bar('\tCreate variants  : ', max=vtotal, suffix='%(percent).1f%% - %(elapsed_td)s')
for chrm in range(1,ctotal + 1):
	for pos in range(1, ptotal + 1):
		samples_count = random.randint(35, 60)
		samples = [random.randint(1, stotal) for i in range(samples_count)]


		for ref in var.keys():
			for alt in var[ref]:

				sql_query2 += "(%s, '%s', %s, '%s', '%s', %s, '%s')," % (variant_id, str(chrm), str(pos), ref, alt, is_transition(ref, alt), samples_count)
				for sample in samples:
					sql_query1 += "(%s, '%s', %s, '%s', '%s', %s)," % (sample, str(chrm), str(pos), ref, alt, variant_id)
					
				bar.next()
				variant_id += 1
				count += samples_count

				if count >= 200000:
					count = 0
					transaction1 = sql_head1 + sql_query1[:-1] + " ON CONFLICT DO NOTHING"
					transaction2 = sql_head2 + sql_query2[:-1] + " ON CONFLICT DO NOTHING"
					threading.Thread(target=exec_sql_query, args=(transaction2 + transaction1, )).start()
					sql_query1 = ""
					sql_query2 = ""

				# Allow user to pause
				try:
					key = win.getkey()
					if key == " ": # of we got a space then break
						raw_input("Press any Key to continue")
				except: # in no delay mode getkey raise and exeption if no key is press 
					key = None
		
transaction1 = sql_head1 + sql_query1[:-1] + " ON CONFLICT DO NOTHING"
transaction2 = sql_head2 + sql_query2[:-1] + " ON CONFLICT DO NOTHING"
threading.Thread(target=exec_sql_query, args=(transaction2 + transaction1, )).start()
while job_in_progress > 0:
	if current != job_in_progress:
		print ("\t - remaining sql job : ", job_in_progress)
		current = job_in_progress
	pass
bar.finish()
print ("\n")



