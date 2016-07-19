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

from progress.bar import Bar
from progress.spinner import Spinner
from multiprocessing import Pool

from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, Sequence, UniqueConstraint, Index, func, distinct
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.ext.declarative import declarative_base

from pysam import VariantFile


print("Benchmark SQLAlchemy - Model schema n°4")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# TOOLS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class Timer(object):
	def __init__(self, verbose=False):
		self.verbose = verbose

	def __enter__(self):
		self.start = time.time()
		return self

	def __exit__(self, *args):
		self.end = time.time()
		self.secs = self.end - self.start
		self.msecs = self.secs * 1000  # millisecs
		if self.verbose:
			print (self.msecs, ' ms')
	def __str__(self):
		return str(self.msecs) + ' ms'

def connect(user, password, db, host='localhost', port=5433):
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
	__tablename__ = '_4_sample'
	id = Column(Integer, Sequence('_4_sample_1_seq'), primary_key=True, nullable=False)
	name = Column(String)
	def __str__(self):
		return "<Sample(name='%s')>" % (self.name)


class Variant(Base):
	__tablename__ = '_4_variant'
	bin = Column(Integer)
	chr = Column(String,  primary_key=True, nullable=False)
	pos = Column(Integer, primary_key=True, nullable=False)
	ref = Column(String,  primary_key=True, nullable=False)
	alt = Column(String,  primary_key=True, nullable=False)
	sample_id = Column (Integer, ForeignKey('_4_sample.id'), primary_key=True)
	is_transition = Column(Boolean)
	__table_args__ = (Index('_4_variant_idx', 'chr', 'pos', 'ref', 'alt', 'sample_id', unique=True), UniqueConstraint('chr', 'pos', 'ref', 'alt', 'sample_id', name='_4_variant_uc'), )
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

def normalize_chr(chrm):
	chrm = chrm.upper()
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


def is_transition(ref, alt):
	tr = ref+alt
	if tr in ('AG', 'GA', 'CT', 'TC'):
		return True
	return False

# retrieve all vcf in the current directory
#directory = os.path.dirname(os.path.realpath(__file__))



print("IMPORT VCF FILES")
# Start a worker processes.


start_0 = datetime.datetime.now()

session = Session(connection)


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
		bar = Bar('\tparsing  : ', max=records_count, suffix='%(percent).1f%% - %(elapsed_td)s')
		sql_query = ""
		sql_head = "INSERT INTO _4_variant (sample_id, chr, pos, ref, alt, is_transition) VALUES "
		sql_tail = " ON CONFLICT DO NOTHING"
		count = 0
		for r in vcf_reader.fetch(): 
			bar.next()

			chrm = normalize_chr(str(r.chrom))
			
			for sn in r.samples:
				s = r.samples.get(sn)

				alt = s.alleles

				if alt[0] != str(r.ref) :
					sql_query += "(%s, '%s', %s, '%s', '%s', %s)," % (str(samples[sn].id), chrm, str(r.pos), str(r.ref), str(alt[0]), is_transition(r.ref, str(alt[0])))
					count += 1
				if alt[1] != str(r.ref) :
					sql_query += "(%s, '%s', %s, '%s', '%s', %s)," % (str(samples[sn].id), chrm, str(r.pos), str(r.ref), str(alt[1]), is_transition(r.ref, str(alt[1])))
					count += 1

				# manage split big request to avoid sql out of memory transaction
				if count >= 1000000:
					count = 0
					transaction = sql_head + sql_query[:-1] + sql_tail
					connection.execute(transaction)
					sql_query = ""



		bar.finish()
		end = datetime.datetime.now()
		print("\tparsing done   : " , end, " => " , (end - start).seconds, "s")
		transaction = sql_head + sql_query[:-1] + sql_tail
		connection.execute(transaction)
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
print("\nSample total (via ORM -> POO) : " , result, " (", t, ")")

with Timer() as t:
	result = connection.execute("SELECT COUNT(*) FROM _4_sample")
print("Sample total (via ORM -> raw query): " , result.first()[0], " (", t, ")")





#count variant
with Timer() as t:
	result = session.query(Variant).count()
print("\nVariant total : " , result, " (", t, ")")

with Timer() as t:
	result = connection.execute("SELECT COUNT(DISTINCT(chr, pos, ref, alt)) FROM _4_variant")
print("Distinct Variant total : " , result.first()[0], " (", t, ")")
result.close()


#count variant / sample
with Timer() as t:
	result = session.query(Variant.sample_id, func.count(Variant.sample_id)).group_by(Variant.sample_id).all()
print("\nCount variant by sample (", t, ")")
for r in result:
	print ("\tSample n°", r[0], " : ", r[1], " variants")

# Get all variant with REF=A on chr5 for the sample 1
with Timer() as t:
	result = session.query(Variant.pos, Variant.alt).filter(Variant.sample_id == 1).filter(Variant.chr == '5').filter(Variant.ref == 'A').all()
print("\nList variant of sample n°1, on chr5, with ref A : " , len(result), " results (", t, ")")
print ("\t", reprlib.repr((result)))


# Test group by same table : 
with Timer() as t:
	usedColumn = func.count(Variant.pos)
	result = session.query(Variant.pos, Variant.ref, Variant.alt, usedColumn).group_by(Variant.pos, Variant.ref, Variant.alt).order_by(usedColumn.desc()).all()
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


with Timer() as t:
	result = connection.execute("SELECT sample_id, is_transition, count(*) FROM _4_variant GROUP BY is_transition, sample_id ORDER BY sample_id, is_transition")
print("\nCheck Sequencing integrity (", t, ")")
print("    sample : transition / transversion")
s = 0
tv = 0
for r in result:
	if r[0] > s :
		print("\tSample n°", s, " : ", r[2], "/", tv, " ", round(tv / r[2],2))
		c = 0
	s = r[0]
	tv = r[2]





