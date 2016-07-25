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

	def total_ms():
		return self.msecs
	def total_s():
		return self.secs

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


def normalize(pos, ref, alt):
	if (ref == alt):
		return None,None,None
	if ref is None:
		ref = ''
	if alt is None:
		alt = ''

	while len(ref) > 0 and len(alt) > 0 and ref[0]==alt[0] :
		ref = ref[1:]
		alt = alt[1:]
		pos += 1
	if len(ref) == len(alt):
		while ref[-1:]==alt[-1:]:
			ref = ref[0:-1]
			alt = alt[0:-1]

	return pos, ref, alt


def is_transition(ref, alt):
	tr = ref+alt
	if len(ref) == 1 and tr in ('AG', 'GA', 'CT', 'TC'):
		return True
	return False





