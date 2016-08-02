#!env/python3
# coding: utf-8

import os
import sys
import datetime
import sqlalchemy
import subprocess
import reprlib
import time


from common import *



from progress.bar import Bar
from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, Sequence, UniqueConstraint, Index, func, distinct
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.ext.declarative import declarative_base

from pysam import VariantFile



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODEL
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Sample(SQLBase):
	__tablename__ = '_6_sample'
	id = Column(Integer, Sequence('_6_sample_1_seq'), primary_key=True, nullable=False)
	name = Column(String)
	def __str__(self):
		return "<Sample(name='%s')>" % (self.name)


class Variant(SQLBase):
	__tablename__ = '_6_variant'
	bin = Column(Integer)
	chr = Column(String,  primary_key=True, nullable=False)
	pos = Column(Integer, primary_key=True, nullable=False)
	ref = Column(String,  primary_key=True, nullable=False)
	alt = Column(String,  primary_key=True, nullable=False)
	sample_id = Column (Integer, ForeignKey('_6_sample.id'), primary_key=True)
	is_transition = Column(Boolean)
	__table_args__ = (Index('_6_variant_idx', 'chr', 'pos', 'ref', 'alt', 'sample_id', unique=True), UniqueConstraint('chr', 'pos', 'ref', 'alt', 'sample_id', name='_6_variant_uc'), )
	def __str__(self):
		return "<Variant(chr='%s', pos='%s', ref='%s', alt='%s', sample='%s'>" % (self.chr, self.pos, self.ref, self.alt, self.sample_id)










class Bench(PostgreBench):

	def __init__(self, config):
		super(Bench, self).__init__(config)

		self.description = "Benchmark n°6\n - PySam\n - Model : Sample & Variant\n - SQLAlchemy using raw sql query\n - Parsing on main thread - SQL query exec on multithread"




	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# IMPORT VCF Data
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	def import_vcf(self, file, records_count:int, out_log:str, out_stat:str):
		vcf_reader = VariantFile(file)

		# get samples in the VCF 
		samples = {i : get_or_create(self.session, Sample, name=i)[0] for i in list((vcf_reader.header.samples))}
		self.session.commit()


		# parsing vcf file
		log("\n\r\tsamples  :  (" + str(len(samples.keys())) + ") " + str(reprlib.repr([s for s in samples.keys()])))
		bar = Bar('\tparsing  : ', max=records_count, suffix='%(percent).1f%% - %(elapsed_td)s')
		sql_query = ""
		sql_head = "INSERT INTO _6_variant (sample_id, chr, pos, ref, alt, is_transition) VALUES "
		sql_tail = " ON CONFLICT DO NOTHING"
		count = 0
		for r in vcf_reader.fetch(): 
			bar.next()
			chrm = normalize_chr(str(r.chrom))
			
			for sn in r.samples:
				s = r.samples.get(sn)

				pos, ref, alt = normalize(r.pos, r.ref, s.alleles[0])

				if alt != ref :
					sql_query = sql_query.join("(%s, '%s', %s, '%s', '%s', %s)," % (str(samples[sn].id), chrm, str(pos), ref, alt, is_transition(ref, alt)))
					count += 1

				pos, ref, alt = normalize(r.pos, r.ref, s.alleles[1])
				if alt != ref :
					sql_query = sql_query.join("(%s, '%s', %s, '%s', '%s', %s)," % (str(samples[sn].id), chrm, str(pos), ref, alt, is_transition(ref, alt)))
					count += 1

				# manage split big request to avoid sql out of memory transaction
				if count >= 1000000:
					count = 0
					transaction = sql_head + sql_query[:-1] + sql_tail
					threading.Thread(target=self.exec_sql_query, args=(transaction,)).start()
					sql_query = ""



		bar.finish()
		transaction = sql_head + sql_query[:-1] + sql_tail
		self.connection.execute(transaction)	

		while self.job_in_progress > 0:
			pass






	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# TEST Requests
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	def test_req(self, out_log:str, out_stat:str):

		# count sample
		with Timer() as t:
			result = self.session.query(Sample).count()
		print("\nSample total (via ORM -> POO) : " , result, " (", t, ")")

		with Timer() as t:
			result = self.connection.execute("SELECT COUNT(*) FROM _6_sample")
		print("Sample total (via ORM -> raw query): " , result.first()[0], " (", t, ")")





		#count variant
		with Timer() as t:
			result = self.connection.execute("SELECT COUNT(*) FROM _6_variant")
		print("\nVariant total : " , result.first()[0], " (", t, ")")

		with Timer() as t:
			result = self.connection.execute("SELECT COUNT(DISTINCT(chr, pos, ref, alt)) FROM _6_variant")
		print("Distinct Variant total : " , result.first()[0], " (", t, ")")
		result.close()


		#count variant / sample
		with Timer() as t:
			result = self.connection.execute("SELECT sample_id, COUNT(*) FROM _6_variant GROUP BY sample_id")
		print("\nCount variant by sample (", t, ")")
		for r in result:
			print ("\tSample n°", r[0], " : ", r[1], " variants")

		# Get all variant with REF=A on chr5 for the sample 1
		with Timer() as t:
			result = self.connection.execute("SELECT pos, alt FROM _6_variant WHERE sample_id = 1 AND chr = '5' AND ref = 'A'")
		print("\nList variant of sample n°1, on chr5, with ref A : " , result.rowcount, " results (", t, ")")
		print ("\t", reprlib.repr((result)))


		# Test group by same table : 
		with Timer() as t:
			result = self.connection.execute("SELECT chr, pos, ref, alt, count(sample_id ) as \"used\" FROM _6_variant GROUP BY chr, pos, ref, alt ORDER BY \"used\" DESC")

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
			result = self.connection.execute("SELECT sample_id, is_transition, count(*) FROM _6_variant GROUP BY is_transition, sample_id ORDER BY sample_id, is_transition")
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





