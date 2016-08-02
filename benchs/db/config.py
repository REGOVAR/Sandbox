#!env/python3
# coding: utf-8

CONFIG = {
	"INPUT_ROOT" : "../../../INPUTS/VCF/",
	"VCF_FILES"  : ["B00H79M_HS37D5_BOTH.merged.annot.vcf.gz"],

	"DB_HOST"    : "localhost",
	"DB_PORT"    : 5432,
	"DB_USER"    : "regovar",
	"DB_PWD"     : "regovar",
	"DB_NAME"    : "regovar",
	"DB_RESET"   : True,

	"LOG_FILE"   : "bench.log",
	"STATS_FILE" : "bench.csv"
}

