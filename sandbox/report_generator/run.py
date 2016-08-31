#!env/python3
# coding: utf-8
import os
import sys
import csv
import urllib.request
import json

# Conversion pdf to img
from wand.image import Image
from wand.color import Color



INPUT_FILE    = 'input.csv'
RVIS_FILE     = 'GenicIntolerance_v3_12Mar16.csv'
OUTPUT_FOLDER = './reports/'
HTML_HEAD     = ''
HTML_FOOT     = ''


# Prepare Reports html
with open('template_header.tpl') as f: HTML_HEAD = f.read()
with open('template_footer.tpl') as f: HTML_FOOT = f.read()



# Get intellectual disability list
urllib.request.urlretrieve('https://raw.githubusercontent.com/REGOVAR/GenesPanel/master/intellectual_disability.lst', 'genes.lst')
disability_list = []
with open('genes.lst') as f: disability_list.append(f.read().splitlines())



print ("Creating Report : ")
with open(INPUT_FILE, newline='') as input_file:
	reader = csv.reader(input_file, delimiter=',')
	for row in reader:

		# Init report
		subject_id    = row[0]
		wannovar_url  = row[1]
		wannovar_csv  = wannovar_url.replace('index.html', 'query.output.exome_summary.csv')
		report_folder = OUTPUT_FOLDER + subject_id

		print (" - " + subject_id)

		if not os.path.exists(report_folder):
			os.makedirs(report_folder)
			os.makedirs(report_folder + '/src')



		# Download wAnnovar csv
		# ---------------------
		urllib.request.urlretrieve(wannovar_csv, report_folder + "/src/wannovar.csv")


		# Parsing wAnnovar CSV -> dic
		# ---------------------------
		wdata = {}

		with open(report_folder + "/src/wannovar.csv", newline='') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
			next(spamreader, None)  # skip the headers
			for row in spamreader:
				gene_name = row[6]
				if gene_name not in wdata.keys():
					wdata[gene_name] = []
				
				wdata[gene_name].append({
					'chr' : row[0],
					'start' : row[1], 
					'end' :row[2], 
					'ref' : row[3], 
					'alt' : row[4], 
					'func' : row[5], 
					'xfunc' : row[7], # exonicFunc
					'aachange' : row[9], 
					'1000g' : row[10], 
					'exac' : row[16], 
					'evs' : row[24], # ESP6500si
					'dbsnp' : row[29],
					'sift' : row[45], 
					'polyphen' : row[49],
					'muttaster' : row[53],
					'cadd' : row[64],
					'gerp' : row[65]
					})


		# Parsing RVIS CSV
		# ----------------
		rdata = {}
		with open(RVIS_FILE, newline='') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
			next(spamreader, None)  # skip the headers
			for row in spamreader:
				rdata[row[0]] = row[2]





		# Create one report by each gene
		# ------------------------------
		for gene_name in wdata.keys():
			print ("   - " + gene_name)
			gene_names = [gene_name]

			# Generate HMLT
			report_html = HTML_HEAD

			# 1 - Header of the report
			# ------------------------
			report_html += "<h1>%s</h1>\n" % subject_id
			report_html += "<h2>Phenotype</h2>\n<p class=\"note\">[... patient's phenotype ...]</p>\n"
			report_html += "<h2>%s</h2>\n<ol>" % gene_name

			for vdata in wdata[gene_name]:
				report_html += "\n\t<li><span class=\"variant\">%s  %s  %s : %s > %s</span></br>%s</li>" % (vdata['chr'], vdata['start'], vdata['end'], vdata['ref'], vdata['alt'], vdata['aachange'])
			report_html += "\n</ol>\n"


			# 2 - OMIM data
			# -------------
			json_req = "http://api.omim.org/api/search/geneMap?search=%s&start=0&limit=20&format=json&apiKey=vkxy009WSyaPNeGKGsWnAQ" % gene_name
			json_res = urllib.request.urlopen(json_req)

			json_res = json_res.read()
			json_res = json_res.decode('UTF-8')
			omim_data = json.loads(json_res)

			report_html += "<h2>OMIM</h2>"
			for odata in omim_data['omim']['searchResponse']['geneMapList']:
				if gene_name in odata['geneMap']['geneSymbols']:
					report_html += "\n<ul><li><span>Alternatives symboles</span> : %s</li>" % odata['geneMap']['geneSymbols']
					report_html += "\n<li><span>OMIM page</span> : <a href=\"http://omim.org/entry/%s\">%s</a></li>" % (odata['geneMap']['mimNumber'], odata['geneMap']['mimNumber'])
					report_html += "\n<li><span>Gene</span> : %s</li></ul>\n" % odata['geneMap']['geneName']
					gene_names.append(odata['geneMap']['geneSymbols'].split(','))

			# 3 - IGV Analysis
			# ----------------

			# TODO
			report_html += "<h2>IGV Analysis</h2>\n<p class=\"note\">[... Copy snapshot + doctor's analysis report ...]</p>\n"


			# 4 - Public Databases
			# --------------------
			report_html += "<h2>Public Databases</h2>\n<ul>\n"
			report_html += "<li><span>1000G</span> : %s</li><li><span>EVS</span> : %s</li><li><span>dbSNP</span> : %s</li><li><span>ExAC</span> : %s</li>" % (vdata['1000g'], vdata['evs'], vdata['dbsnp'], vdata['exac'])
			report_html += "\n</ul><h2>In silico predictions</h2>\n<ul>\n"
			report_html += "<li><span>SIFT</span> : %s</li><li><span>Polyphen HVAR</span> : %s</li><li><span>MutationTaster</span> : %s</li>" % (vdata['sift'], vdata['polyphen'], vdata['muttaster'])
			report_html += "<li><span>CADD phred</span> : %s</li><li><span>GERP</span> : %s</li>" % (vdata['cadd'], vdata['gerp'])


			# 5 - RVIS
			# --------
			rvis_web = "http://genic-intolerance.org/Search?query=%s" % gene_name
			rvis_sc  = "Not found"
			if gene_name in rdata.keys():
				rvis_sc = rdata[gene_name]
			report_html += "<li><span><a href=\"%s\">RVIS</a></span> : %s</li>\n</ul>\n" % (rvis_web, rvis_sc)
			

			# 6 - ASDP gene list
			# ------------------
			report_html += "<h2>Present in the ID genes list</h2>\n<ul>\n"
			for name in gene_names:
				asdp_check = 'NO'
				if name in disability_list : 
					asdp_check = 'YES'
				report_html += "<li>%s : %s</li>" % (name, asdp_check)

			report_html += "</ul>\n"




			# ===============================================
			report_html += "\n<h1>Cerebral Expression</h1>\n"
			# ===============================================




			# 7 - Tissue Atlas 
			# ----------------
			atlas_web = "http://www.proteinatlas.org/search/%s" % gene_name
			report_html += "<h2>Tissue Atlas </h2>\n"
			report_html += "<a href=\"%s\">Web site</a>\n" % atlas_web





			# 8 - Human brain transcriptome
			# -----------------------------
			# http://hbatlas.org/pages/hbtd
			hbt_file = report_folder + "/src/hbt_" + gene_name 
			hbt_url  = "http://hbatlas.org/hbtd/images/wholeBrain/%s.pdf" % gene_name
			hbt_src  = "./src/hbt_%s.png" % gene_name
			try:
				urllib.request.urlretrieve(hbt_url, hbt_file + ".pdf")

				with Image(filename=hbt_file+".pdf", resolution=300) as img:
					with Image(width=img.width, height=img.height, background=Color("white")) as bg:
						bg.composite(img,0,0)
						bg.save(filename=hbt_file + ".png")
						os.remove(hbt_file+".pdf")
						report_html += "<h2>Human brain transcriptome</h2>\nURL : <a href=\"%s\">%s</a>\n<br/>\n<img src=\"%s\" width=\"400px\"/>\n" % (hbt_url, gene_name, hbt_src)
			except:
				report_html += "<h2>Human brain transcriptome</h2>\nURL : <a href=\"%s\">%s</a>\n<br/>\nNot found\n" % (hbt_url, gene_name)


			# 9 - Sfari
			# ---------
			# https://gene.sfari.org/autdb/search





			# 10 - DECIPHER
			# -------------
			url 	 = "https://decipher.sanger.ac.uk/search?q=%s#consented-patients/results" % gene_name
			snapshot = ""
			report_html += "<h2>Decipher</h2>\nURL : <a href=\"%s\">%s</a>\n<br/>\n<img src=\"%s\"/>\n" % (url, gene_name, snapshot)




			# 11 - String pathway
			# -------------------
			# http://[database]/[access]/[format]/[request]?[parameter]=[value]
			stp_file = report_folder + "/src/stp_" + gene_name  + ".png"
			stp_url  = "http://string-db.org/api/image/network?identifier=%s_HUMAN" % gene_name
			stp_src  ="./src/stp_%s.png" % gene_name
			try:
				urllib.request.urlretrieve(stp_url, stp_file)
				report_html += "<h2>String pathway</h2>\n<img src=\"%s\" width=\"500px\"/>\n" %  stp_src
			except:
				report_html += "<h2>String pathway</h2>\nNot found\n"




			# 12 - Pubmed
			# -----------
			# http://www.ncbi.nlm.nih.gov/pubmed




			# Write report in HTML
			# --------------------
			with open(report_folder + '/' + gene_name + '.html', 'w') as f:
				read_data = f.write(report_html)
				f.closed



			# Convert HTML -> ODS







