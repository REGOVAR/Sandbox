#!env/python3
# coding: utf-8

import os
import sys
import datetime
import subprocess
import argparse
import reprlib
import time
import logging


from config import *
from common import *
from scripts import *




logging.basicConfig(filename=CONFIG["LOG_FILE"],level=logging.INFO)


# Import all bench

BENCHES = {}
BENCHES["B007"] = poc_007.Bench(CONFIG)


for key, bench in BENCHES.items():


	if (True): #args.script == key):
		start_0 = datetime.datetime.now()

		log(bench.description)

		log("Init DB :")
		start_1 = datetime.datetime.now()
		bench.init_db()
		end = datetime.datetime.now()
		log("Init DB done : " + str((end - start_1).seconds) + "s")


		log("File(s) import start : " )
		for file in CONFIG["VCF_FILES"]:

			file = CONFIG["INPUT_ROOT"] + file

			# console verbose
			bashCommand = 'grep -v "^#" ' + str(file) +' | wc -l'
			if file.endswith(".vcf.gz"):
				bashCommand = "z" + bashCommand
			
			# process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
			process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			cmd_out = process.communicate()[0]
			records_count = int(cmd_out.decode('utf8'))		


			log(" - Start import file : " + file + " (" + str(records_count) + " lines) ("+humansize(file) +")")
			start_1 = datetime.datetime.now()
			bench.import_vcf(file, records_count, CONFIG["LOG_FILE"], CONFIG["STATS_FILE"])
			end = datetime.datetime.now()
			log(" - File import done : " + str((end - start_1).seconds) + "s")


		end = datetime.datetime.now()
		log("All import(s) done : " + str((end - start_0).seconds) + "s")

		# run tests