#!/env/python3 
import psycopg2 
import argparse 
from progress.bar import Bar
from pysam import VariantFile

DBNAME   	= "regovar-dev"
USER     	= "regovar"
HOST     	= "localhost"
PASSWORD 	= "regovar" 
SHEMA_FILE  = "poc_005.sql"

#========================================================
def create_schema(conn):
	print("create schema ...")
	cursor =  conn.cursor()
	cursor.execute(str(open(SHEMA_FILE, "r").read()))
	conn.commit()
	cursor.close()
#========================================================
def connect_database():
	try:
		conn = psycopg2.connect("dbname={} user={} host={} password={}".format(DBNAME,USER,HOST,PASSWORD))
		print("connection success ...")
	except:
		print("Impossible de se connecter à postgreSQL")
	return conn 
#========================================================
def import_vcf(conn, filename):

	print("import vcf ...")
	# On crée le schema.. Si ca existe deja on supprime tout . Le schema est dans le namespace regovar. Donc tinquiete , ca va pas effacer tes tables. 
	create_schema(conn)

	print("count records ...")
	count = sum([1 for i in VariantFile(filename)]) 
	print(count,"records found")

	bar     = Bar('Importing variants... ', max = count, suffix='%(percent)d%%')
	bcf_in  = VariantFile(filename) 

	curr           = conn.cursor()
	variant_ids    = dict()
	samples_vars   = dict()

	# On loop sur les variants 
	for rec in bcf_in.fetch():
		chrom = str(rec.chrom)
		pos   = int(rec.pos) 
		ref   = str(rec.ref)
		alt   = str(rec.alts[0])


		try:
			curr.execute("INSERT INTO regovar.variants (bin,chr,pos,ref,alt) VALUES (%s,%s,%s,%s,%s) RETURNING id", (0,chrom,pos,ref,alt))   # it's a tupple ( x,)
			last_id = curr.fetchone()[0]
		except Exception as e : 
			last_id = None

		# Si bien inseré , alors on sauvegarde l'identifiant 
		if last_id is not None:
			variant_ids[(chrom,pos,ref,alt)] = last_id


		#Sauvegarde des samples en memoire 
		for name in rec.samples:
			if name not in samples_vars:
				samples_vars[name] = list()
			samples_vars[name].append(last_id)



		bar.next()

	bar.finish()
	conn.commit()

	# Insertion des filenames 
	curr.execute("INSERT INTO regovar.files (path) VALUES (%s) RETURNING id", (filename,))   # it's a tupple ( x,)
	file_id = curr.fetchone()[0]



	for name in samples_vars.keys():
		bar = Bar('Importing sample: {} '.format(name), max = len(samples_vars[name]), suffix='%(percent)d%%')

		curr.execute("INSERT INTO regovar.samples (name,description,file_id) VALUES (%s,%s,%s) RETURNING id", (name,"",file_id))   # it's a tupple ( x,)
		sample_id = curr.fetchone()[0]
		# Insert dans sample_variants

		for var_id in samples_vars[name]:
			curr.execute("INSERT INTO regovar.sample_has_variants (sample_id,variant_id,genotype) VALUES (%s,%s,%s) RETURNING id", (sample_id,var_id,-1))   # it's a tupple ( x,)
			bar.next()

		bar.finish()
		conn.commit()
	# On importe les samples 








#========================================================

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--create', help='create database schema', action='store_true')
parser.add_argument('-i', '--input',help='import vcf file', default = None)

args = parser.parse_args()
if args.create is True :
	conn = connect_database()
	create_schema(conn)
	conn.close()
else:
	if args.create is False and args.input is not None:
		conn = connect_database()
		import_vcf(conn, args.input)

	else:
		parser.print_help()
