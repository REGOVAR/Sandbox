#!/env/python3 
import psycopg2 
import argparse 
from progress.bar import Bar
from pysam import VariantFile
from mongoengine import *
import random

# ================= MONGOENGINE SCHEMA =============================
# On défini la collection Variant ! Je pense que unique et meta font la meme choses.. 
# Mais on ne sais jamais .. 
class Variant(Document):
	bin 	= IntField(required = True, default = -1)
	chrom 	= StringField(max_length = 50, unique_with =('pos','ref','alt'))
	pos 	= IntField(required = True, unique_with =('chrom','ref','alt'))
	ref 	= StringField(max_length = 1000,unique_with =('pos','chrom','alt'))
	alt 	= StringField(max_length = 1000, unique_with =('pos','ref','chrom'))

	meta = {
	'indexes': ['chrom','pos','ref','alt']
	}


# Ce n'est pas une collections , mais un sous documents qu'on retrouve dans Samples ! 
class Genotype(EmbeddedDocument):
	variant  = ReferenceField(Variant)
	infos    = DictField()

# Chaques samples contients la listes de ses variants associées à des infos 
class Sample(Document):
	name      = StringField(max_length=255)
	genotypes =  ListField(EmbeddedDocumentField(Genotype))


# ================= SCRIPTS =============================
def import_vcf(filename):

	print("import vcf ...")
	# on Compte le nombre de lignes .. 
	print("count records ...")
	count = sum([1 for i in VariantFile(filename)]) 
	print(count,"records found")

	bar     = Bar('Importing in cache... ', max = count, suffix='%(percent)d%%')
	bcf_in  = VariantFile(filename) 

	# Permet de garder en cache que les variants uniques 
	uniques = set()


	# On loop sur les variants et on met tout en mémoire
	for rec in bcf_in.fetch(): 
		chrom = str(rec.chrom)
		pos   = int(rec.pos) 
		ref   = str(rec.ref)
		alt   = str(rec.alts[0])

		key = (chrom,pos,ref,alt) 
		uniques.add(key)
		bar.next()

	bar.finish()
	

	bar     = Bar('Create objects... ', max = len(uniques), suffix='%(percent)d%%')
	
	# On va créer les objects de l'ORM de mongo et les mettres dans bulks
	bulks = []
	for key in uniques:
		bulks.append(Variant(chrom = key[0], pos = key[1], ref = key[2], alt = key[3]))
		bar.next()
	bar.finish()

	# On injecte les datas dans mongo
	print("Save objects")
	out = Variant.objects.insert(bulks)
	

	# Exemple pour sauvegarder les samples ! Je n'ai pas fini ... donc j'ai mis des variants au hasard
	for name in rec.samples:

		sample = Sample(name = name)
		sample.genotypes.append(Genotype(variant = random.choice(out), infos = {"DP":45, "geno":-1}))
		sample.genotypes.append(Genotype(variant = random.choice(out), infos = {"DP":42, "geno":1}))
		sample.genotypes.append(Genotype(variant = random.choice(out), infos = {"DP":5, "geno":-1}))
		sample.genotypes.append(Genotype(variant = random.choice(out), infos = {"DP":4, "geno":1}))
		sample.genotypes.append(Genotype(variant = random.choice(out), infos = {"DP":425, "geno":1}))
		sample.genotypes.append(Genotype(variant = random.choice(out), infos = {"DP":452, "geno":-1}))

		sample.save()





#=========== MAIN =======================


parser = argparse.ArgumentParser()
parser.add_argument('filename',help='import vcf file', default = None)
args = parser.parse_args()

if args.filename is not None:
	db = connect("regovar")
	db.drop_database("regovar")

	import_vcf(args.filename)



