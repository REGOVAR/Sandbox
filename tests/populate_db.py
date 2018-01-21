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



class Sample(Base):
	__tablename__ = '_10_sample'
	id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
	name = Column(String)
	description = Column(String)
	# __table_args__ = (
	# 	Index('_10_sample_idx', 'id', unique=True), 
	# 	UniqueConstraint('id', name='_10_sample_uc'), )

class SampleVariant(Base):
	__tablename__ = '_10_sample_variant'
	sample_id  = Column(Integer, primary_key=True, nullable=False)
	chr        = Column(String,  primary_key=True, nullable=False)
	pos        = Column(Integer, primary_key=True, nullable=False)
	ref        = Column(String,  primary_key=True, nullable=False)
	alt        = Column(String,  primary_key=True, nullable=False)
	variant_id = Column(Integer, nullable=False)

	# __table_args__ = (
	# 	Index('_10_sample_variant_idx1', 'sample_id', 'chr', 'pos', 'ref', 'alt', unique=True), 
	# 	Index('_10_sample_variant_idx2', 'sample_id', 'variant_id', unique=True),
	# 	UniqueConstraint('sample_id', 'chr', 'pos', 'ref', 'alt', name='_10_sample_variant_uc'), )


class Variant(Base):
	__tablename__ = '_10_variant'
	id = Column(Integer,  primary_key=True)
	bin = Column(Integer)
	chr = Column(String,  nullable=False)
	pos = Column(Integer, nullable=False)
	ref = Column(String,  nullable=False)
	alt = Column(String,  nullable=False)
	is_transition = Column(Boolean)
	regovar_stat = Column(Integer)

# 	__table_args__ = (
# 		Index('_10_variant_idx1', 'chr', 'pos', 'ref', 'alt', unique=True), 
# 		Index('_10_variant_idx2', 'id', unique=True), 
# 		UniqueConstraint('chr', 'pos', 'ref', 'alt', name='_10_variant_uc'), )






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
job_in_progress = 1
# Max process core that the script can use
proc_max   = 7
# Max python process
th_pyt_max = 2




def exec_sql_query(raw_sql):
	global job_in_progress
	job_in_progress += 1
	connection.execute(raw_sql)
	job_in_progress -= 1

# We need to wait that a core is free for us before running the query
def run_asynch_sql_query(transaction:str):
	global job_in_progress, proc_max
	while (job_in_progress >= proc_max):
		time.sleep(1)

	# Ok run the query in another thread and continue
	threading.Thread(target=exec_sql_query, args=(transaction, )).start()






# Total sample
stotal = 200000000 #2000000000



# 75.6 milliards de variants = 300M²(pos) x 12(ref->alt) x 21(chr)
var = {"A": ["C", "G", "T"], "C": ["A", "G", "T"], "G": ["A", "C", "T"], "T": ["A", "C", "G"]}
ctotal = 22
ptotal = 3000000


# Create Samples




def register_sample(start:int, end:int):
	global job_in_progress, th_pyt_max, global_count, sql_head
	job_in_progress += 1
	sql_query = ""
	count = 0
	for sample_id in range(start, end):
		sql_query += "('sample n°%s')," % sample_id
		count += 1
		global_count += 1
		if count >= 500000:
			count = 0
			if (sql_query != ""):
				transaction = sql_head + sql_query[:-1]
				sql_query = ""
				run_asynch_sql_query(transaction)

	if (sql_query != ""):
		transaction = sql_head + sql_query[:-1]
		run_asynch_sql_query(transaction)

	job_in_progress -= 1





def register_variant(chr_start:int, chr_end:int):
	global job_in_progress, th_pyt_max, global_variant_count, global_chr_count, sql_head1, sql_head2, var, ptotal, stotal, variant_id
	job_in_progress += 1
	sql_query1, sql_query2 = "", ""
	count = 0
	for chrm in range(chr_start, chr_end):
		for pos in range(1, ptotal + 1):
			samples_count = random.randint(20, 50)
			samples = [random.randint(1, stotal) for i in range(samples_count)]


			for ref in var.keys():
				for alt in var[ref]:

					sql_query2 += "(%s, '%s', %s, '%s', '%s', %s, '%s')," % (variant_id, str(chrm), str(pos), ref, alt, is_transition(ref, alt), samples_count)
					for sample in samples:
						sql_query1 += "(%s, '%s', %s, '%s', '%s', %s)," % (sample, str(chrm), str(pos), ref, alt, variant_id)
						
					variant_id += 1
					count += samples_count
					global_variant_count += 1

					if count >= 300000:
						count = 0
						transaction1, transaction2 = "", ""
						if (sql_query1 != ""):
							transaction1 = sql_head1 + sql_query1[:-1] + " ON CONFLICT DO NOTHING"
						if (sql_query2 != ""):
							transaction2 = sql_head2 + sql_query2[:-1] + " ON CONFLICT DO NOTHING"
						sql_query1 = ""
						sql_query2 = ""
						run_asynch_sql_query(transaction2 + transaction1)
		global_chr_count +=1

	transaction1, transaction2 = "", ""
	if (sql_query1 != ""):
		transaction1 = sql_head1 + sql_query1[:-1] + " ON CONFLICT DO NOTHING"
	if (sql_query2 != ""):
		transaction2 = sql_head2 + sql_query2[:-1] + " ON CONFLICT DO NOTHING"
	sql_query1, sql_query2 = "", ""

	job_in_progress -= 1








Main Sample loop (~30 minutes)
start_date = datetime.datetime.now()
print("Populate DB with Fakes Samples (%s).\nStart at : %s" % (stotal, start_date))
sql_head = "INSERT INTO _10_sample (name) VALUES "
global_count = 0
sample_step = int(round(stotal / th_pyt_max,0))
for p in range(0,th_pyt_max):
	threading.Thread(target=register_sample, args=(p * sample_step, (p+1)*sample_step, )).start()

while job_in_progress > 1:
	print('\rSample creation in progress : [Thread:' + str(job_in_progress) + '/' + str(proc_max) + ']\t\t' + str(global_count) + ' samples (' + str(round(global_count/stotal*100,1)) + '%)' , end='')

duration = datetime.datetime.now() - start_date 
print('\rSample creation done in ' + duration.hours + 'h ' + duration.minutes + 'm ' + duration.seconds + 's : [Max Thread:' + str(proc_max) + ']\t\t' + str(global_count) + ' samples (' + str(round(global_count/stotal*100,1)) + "%)\n")



# Main Variant loop
start_date = datetime.datetime.now()
print("Populate DB with Fakes Variant (%s chr - %s pos - %s var).\nStart at : %s" % (ctotal, ptotal, 12, start_date))
sql_head1 = "; INSERT INTO _10_sample_variant (sample_id, chr, pos, ref, alt, variant_id) VALUES "
sql_head2 = "INSERT INTO _10_variant (id, chr, pos, ref, alt, is_transition, regovar_stat) VALUES "
global_variant_count = 0
global_chr_count = 0
variant_id = 1
variant_step = int(round(ctotal / th_pyt_max,0))
for p in range(0,th_pyt_max):
	threading.Thread(target=register_variant, args=(p * variant_step, (p+1)*variant_step, )).start()

while job_in_progress > 1:
	print('\rVariant creation in progress : [Thread:' + str(job_in_progress) + '/' + str(proc_max) + ']\t\t' + str(global_variant_count) + ' s-variant (chr done : ' + str(global_chr_count) + ')' , end='')

duration = datetime.datetime.now() - start_date 
print('\rVariant creation done in ' + duration.hours + 'h ' + duration.minutes + 'm ' + duration.seconds + 's : [Max Thread:' + str(proc_max) + ']\t\t' + str(global_count) + ' s-variant (chr done : ' + str(global_chr_count) + ')')




