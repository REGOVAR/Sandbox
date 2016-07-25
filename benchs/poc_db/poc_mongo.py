#!/env/python3 
import psycopg2 
import argparse 
from progress.bar import Bar
from pysam import VariantFile
from mongoengine import *
import random

# ================= MONGOENGINE SCHEMA =============================


class Variant(Document):
	bin 	= IntField(required = True, default = -1)
	chrom 	= StringField(max_length = 50, unique_with =('pos','ref','alt'))
	pos 	= IntField(required = True, unique_with =('chrom','ref','alt'))
	ref 	= StringField(max_length = 1000,unique_with =('pos','chrom','alt'))
	alt 	= StringField(max_length = 1000, unique_with =('pos','ref','chrom'))

	meta = {
	'indexes': ['chrom','pos','ref','alt']
	}


class Genotype(EmbeddedDocument):
	variant  = ReferenceField(Variant)
	infos    = DictField()


class Sample(Document):
	name      = StringField(max_length=255)
	genotypes =  ListField(EmbeddedDocumentField(Genotype))


# ================= SCRIPTS =============================

DBNAME   	= "regovar-dev"
USER     	= "regovar"
HOST     	= "localhost"
PASSWORD 	= "regovar" 

#========================================================
def import_vcf(filename):

	print("import vcf ...")
	# On crée le schema.. Si ca existe deja on supprime tout . Le schema est dans le namespace regovar. Donc tinquiete , ca va pas effacer tes tables. 

	print("count records ...")
	count = sum([1 for i in VariantFile(filename)]) 
	print(count,"records found")

	bar     = Bar('Importing in cache... ', max = count, suffix='%(percent)d%%')
	bcf_in  = VariantFile(filename) 

	uniques = set()


	# On loop sur les variants 
	for rec in bcf_in.fetch():
		chrom = str(rec.chrom)
		pos   = int(rec.pos) 
		ref   = str(rec.ref)
		alt   = str(rec.alts[0])

		key = (chrom,pos,ref,alt) 

		uniques.add(key)
		bar.next()

	bar.finish()
	

	# Create objects 
	bar     = Bar('Create objects... ', max = len(uniques), suffix='%(percent)d%%')

	bulks = []
	for key in uniques:
		bulks.append(Variant(chrom = key[0], pos = key[1], ref = key[2], alt = key[3]))
		bar.next()

	bar.finish()

	print("Save objects")
	out = Variant.objects.insert(bulks)
	


	for name in rec.samples:

		sample = Sample(name = name)
		sample.genotypes.append(Genotype(variant = random.choice(out), infos = {"DP":45, "geno":-1}))
		sample.save()


		# bar = Bar('Importing sample: {} '.format(name), max = len(samples_vars[name]), suffix='%(percent)d%%')

		# curr.execute("INSERT INTO regovar.samples (name,description,file_id) VALUES (%s,%s,%s) RETURNING id", (name,"",file_id))   # it's a tupple ( x,)
		# sample_id = curr.fetchone()[0]
		# # Insert dans sample_variants

		# for var_id in samples_vars[name]:
		# 	curr.execute("INSERT INTO regovar.sample_has_variants (sample_id,variant_id,genotype) VALUES (%s,%s,%s) RETURNING id", (sample_id,var_id,-1))   # it's a tupple ( x,)
		# 	bar.next()

		# bar.finish()
		# conn.commit()
	# # On importe les samples 


#=========== MAIN =======================


parser = argparse.ArgumentParser()
parser.add_argument('filename',help='import vcf file', default = None)
args = parser.parse_args()

if args.filename is not None:
	db = connect("regovar")
	db.drop_database("regovar")

	import_vcf(args.filename)



