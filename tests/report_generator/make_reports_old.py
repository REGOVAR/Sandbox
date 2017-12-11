#! /usr/bin/env python3

import collections
import glob
import gzip
import jinja2
import json
import logging
import os
import pprint
import requests
import shutil

# Conversion pdf to img
from wand.image import Image
from wand.color import Color

__version__ = '0.1.0'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

root = '/commun/data/users/asdp/Hugodims/VCFscripts'
rvis_file = 'rvis_v3_20160312.csv'

cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
os.makedirs(cache, exist_ok=True)

modes = collections.OrderedDict([
    ('de novo', (
        '20160417_run15',
        'hapcal.*.parents_genotype.vcf.gz',
        1
    )),
    ('compound heterozygous', (
        'AR/20160827_alltogether_fixed',
        'hapcal.*.heterozygous_rec.vcf.gz',
        2
    )),
    ('homozygous', (
        'AR/20160827_alltogether_fixed',
        'hapcal.*.homozygous_rec.vcf.gz',
        1
    )),
    ('X linked', (
        'AR/20160827_alltogether_fixed',
        'hapcal.*.xlinked.vcf.gz',
        1
    )),
])

templates = jinja2.Environment(
    loader = jinja2.FileSystemLoader(
        os.path.dirname(os.path.abspath(__file__))
    ),
    trim_blocks = True
)

genemap_api = 'http://api.omim.org/api/search/geneMap'
omim_api = 'http://api.omim.org/api/entry'
omim_api_key_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.genemap_api_key')

with open(omim_api_key_filename, 'rt') as omim_api_key_file:
    omim_api_key = omim_api_key_file.read()

id_genes_list = 'https://raw.githubusercontent.com/REGOVAR/GenesPanel/master/intellectual_disability.lst'
r = requests.get(id_genes_list)
if r.status_code == requests.codes.ok:
    id_genes = set(r.text.splitlines())
else:
    logger.warning('Unable to access the list of ID genes')
    id_genes = set()

rdata = {}
with open(rvis_file, newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(spamreader, None)  # skip the headers
    for row in spamreader:
        rdata[row[0]] = row[2]


class ModeData:
    def __init__(self, vcf_filename, min_variant_count):
        self.vcf_filename = vcf_filename
        self.min_variant_count = min_variant_count

class GeneData:
    def __init__(self, name):
        self.mim_number = None
        self.name = None
        self.text = []
        self.id_gene = (name in id_genes)
#       if name not in ['CCDC40', 'CTD-3018O17.3', 'FBXL14', 'HLA-DRB5', 'KRTAP5-5', 'MUC5B', 'MUC6', 'RP11-532E4.2', 'RP1L1', 'WNT5B', 'ZNF880']: # TODO FIXME testing, remove this
        if name not in ['ABCC9', 'AK2', 'APLP2', 'CCHCR1', 'COL11A1', 'CTB-51A17.1', 'DNAH5', 'DYNC1LI1', 'DYSF', 'EFHC2', 'EPS8', 'EPYC', 'FLNB', 'GPC3', 'GSAP', 'IGFN1', 'IL1RAPL2', 'KRTAP4-16P', 'KRTAP4-8', 'LINC00842', 'MALRD1', 'MCC', 'MEGF9', 'MUC3A', 'NPY4R', 'NUDT12', 'PCNT', 'POLR2LP', 'PSMD5', 'PSMD5-AS1', 'PSORS1C1', 'PSORS1C2', 'PTPN22', 'RAB3GAP2', 'RP1-117O3.2', 'RP11-415I12.3', 'RP11-6N17.9', 'RP13-43E11.1', 'RP5-1073O3.2', 'RPL18AP2', 'RRM2P3', 'SCML2', 'SHROOM2', 'SLC9A6', 'SNORA36B', 'SRPX', 'TEX13A', 'TJP1', 'TM4SF2', 'TRPC5', 'TTN', 'TTN-AS1', 'USP32', 'Y_RNA', 'ZBTB11', 'snoU13']: # TODO FIXME testing 08-04-VO), remove this
            self.mim_number = 'MIM_NUMBER'
            self.name = 'NAME'
            self.text = []
            return # TODO FIXME testing, remove this
        info_filename = os.path.join(cache, 'omim_info_{}'.format(name))
        if os.path.exists(info_filename):
            with open(info_filename, 'rt') as info_file:
                info = json.load(info_file)
                self.mim_number = info['mim_number']
                self.name = info['name']
                self.text = info['text']
            return
        r = requests.get(genemap_api, params = {
            'search': name,
            'format': 'json',
            'apiKey': omim_api_key,
        })
        if r.status_code == requests.codes.ok:
            data = r.json()
            gene_map_list = data['omim']['searchResponse']['geneMapList']

            # OGD : ne pas prendre le premier result, trouver celui qui match vraiment
            # OGD : remplace la full description du gene par la liste des synonymes

            if len(gene_map_list) == 1 :
                self.mim_number = gene_map_list[0]['geneMap']['mimNumber']
                self.name = gdata['geneMap']['geneName']
                self.text = gdata['geneMap']['geneSymbols']
            else:
                for gdata in gene_map_list:
                    if name in gdata['geneMap']['geneSymbols']:
                        self.mim_number = gdata['geneMap']['mimNumber']
                        self.name = gdata['geneMap']['geneName']
                        self.text = gdata['geneMap']['geneSymbols']
                        # OGD : TODO : garder de côté cette liste des synonymes pour les recherches ds la liste d'ASDP, HBT, etc ?
        else:
            logger.warning('Unable to find the OMIM gene map for gene {}'.format(name))
        info = {
            'mim_number': self.mim_number,
            'name': self.name,
            'text': self.text,
        }
        with open(info_filename, 'wt') as info_file:
            json.dump(info, info_file)


class Gene:
    __cache = {}
    def __init__(self, name, variants):
        self.name = name
        self.variants = variants
        self.data = Gene.__cache.setdefault(name, GeneData(name))
        # TODO FIXME serialize the cache to avoid expensive calls at each run

class PubmedEntry:
    def __init__(self, data):
        self.uid = data['uid']
        self.fulljournalname = data['fulljournalname']
        self.firstauthor = ''
        self.lastauthor = data['lastauthor']
        self.title = data['title']
        self.elocationid = data['elocationid']
        if len(data['authors']) > 0 : 
            self.firstauthor  = data['authors'][0]['name']


def get_vcf_filenames(directory, pattern):
    return glob.glob(os.path.join(root, directory, pattern), recursive = True)

def extract_index(filename):
    return filename.split('.')[1][:-2]

def get_indexes_filenames():
    result = {}
    for mode, (directory, pattern, min_variant_count) in modes.items():
        filenames = get_vcf_filenames(directory, pattern)
        for filename in filenames:
            index = extract_index(filename)
            result.setdefault(index, collections.OrderedDict())[mode] = ModeData(filename, min_variant_count)
    return collections.OrderedDict(sorted(result.items(), key = lambda index: index[3:5] + index[0:2] + index[6:9]))

def extract_genes(vcf, min_variant_count):
    all_genes = {}
    for line in vcf:
        if not line.startswith('#'):
            columns = line.rstrip().split('\t')
            info = columns[7]
            annotation = info.split('EFF=' in info and 'EFF=' or 'ANN=')[1].split(';')[0]
            variant_genes = {}
            for effect in annotation.split(','):
                gene = effect.split('|')[3]
                if gene:
                    variant_genes.setdefault(gene, set()).add(tuple(columns[0:5]))
            for gene, variants in variant_genes.items():
                all_genes.setdefault(gene, set()).update(variants)
    return sorted([Gene(gene, variants) for gene, variants in all_genes.items() if len(variants) >= min_variant_count], key = lambda gene: gene.name)

def render_report(data, template_name):
    template = templates.get_template('{}.tpl'.format(template_name))
    return template.render(
        data = data,
        enumerate = enumerate
    )

def get_hbt_image(gene_name, output_folder):
    hbt_file = output_folder + "/hbt_" + gene_name
    hbt_url  = "http://hbatlas.org/hbtd/images/wholeBrain/%s.pdf" % gene_name

    # first we check if image already exist
    if os.path.isfile(hbt_file + ".png") :
        return hbt_file + ".png"

    try:
        # Retrieve pdf from hbt
        r = requests.get(hbt_url, stream=True)
        if r.status_code == 200:
            with open(hbt_file + ".pdf", 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f) 
            # Convert pdf into png
            with Image(filename=hbt_file+".pdf", resolution=200) as img:
                with Image(width=img.width, height=img.height, background=Color("white")) as bg:
                    bg.composite(img,0,0)
                    bg.save(filename=hbt_file + ".png")
                    os.remove(hbt_file+".pdf")
                    return hbt_file + ".png"
        else:
            logger.warning('Unable to find the HBT diagram for {}'.format(gene_name))
    except:
        logger.error('Error occure when trying to converting pdf from HBT to png for the gene {}'.format(gene_name))
    return output_folder + "/error.png"


def get_stp_image(gene_name, output_folder):
    stp_file = output_folder + "/stp_" + gene_name  + ".png"
    stp_url  = "http://string-db.org/api/image/network?identifier=%s_HUMAN" % gene_name

    if os.path.isfile(stp_file) :
        return hbt_file

    try:
        r = requests.get(stp_url, stream=True)
        if r.status_code == 200:
            with open(stp_file, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f) 
        return stp_file
    except:
        logger.error('Error occure when trying to retrieve image from String-Pathway for the gene {}'.format(gene_name))
    return output_folder + "/error.png"


def get_rvis_score(gene_name):
    rvis_sc  = "Not found"
    if gene_name in rdata.keys():
        rvis_sc = rdata[gene_name]
    return rvis_sc


def get_decipher_img(gene_name, output_folder):
    dec_file = output_folder + "/decipher_" + gene_name  + ".png"
    dec_url  = "https://decipher.sanger.ac.uk/search?q=%s#consented-patients/results" % gene_name

    if os.path.isfile(dec_file) :
        return dec_file

    # 1- retrieve image
    os.system ("cutycapt --url=\""+dec_url+"\" --out=\"" + dec_file + "_source.png\" --delay=500")

    # 2- crop image
    if os.path.isfile(dec_file + "_source.png"):
        f = open(dec_file + "_source.png", 'rb')
        with Image(file=f) as img:
            w = img.width - 10
            h = img.height - 315 - 360
            img.crop(5, 315, width=w, height=h)
            img.save(filename=dec_file)
            os.remove(dec_file + "_source.png")
            return dec_file
    else:
        logger.error('Error occure when trying to retrieve image from Decipher for the gene {}'.format(gene_name))
    return output_folder + "/error.png" 



def get_ta_img(gene_name, output_folder):
    ta_file = output_folder + "/ta_" + gene_name
    ta_url  = "http://www.proteinatlas.org/search/%s" % gene_name

    if os.path.isfile(ta_file + ".png") :
        return ta_file + ".png" 

    # 1- Retrieve "true url" from TA "user website url"
    r = requests.get(ta_url)
    if r.status_code == requests.codes.ok:
        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.find_all('a'):
            if (link.text==gene_name): 
                ta_url = "http://www.proteinatlas.org" + link.get('href')

    # 2- Retrieve html page with graphs
    r = requests.get(ta_url)
    if r.status_code == requests.codes.ok:
        soup = BeautifulSoup(r.text, 'html.parser')

        html = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
    <head>
        <title>Tissue expression of DRD4 - Summary - The Human Protein Atlas</title>
        <meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
        <meta name="description" content="Summary of DRD4 expression in human tissue. ">
        <link rel="icon" type="image/png" href="http://www.proteinatlas.org/images_static/favicon_anim.gif">
        <link rel="stylesheet" type="text/css" href="http://www.proteinatlas.org/common.css?version=15.0.0">
        <link rel="stylesheet" type="text/css" href="http://www.proteinatlas.org/search.css?version=15.0.0">
        <link rel="stylesheet" type="text/css" href="http://www.proteinatlas.org/image.css?version=15.0.0">
        <link rel="stylesheet" type="text/css" href="http://www.proteinatlas.org/image_stack.css?version=15.0.0">     
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/utils/jquery.min.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/common.js?version=15.0.0"></script>
        <script>
        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

        ga('create', 'UA-47932142-1', 'auto');
        </script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/search.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/image.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/image_stack.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/utils/d3.min.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/utils/box.min.js?version=15.0.0"></script> 
    </head>
    <body>
"""
        p = soup.find('p', text="RNA EXPRESSION OVERVIEW")
        html += p.findParent('table').prettify()
        html += "\n</body></html>"

    # 3- save into file
    with open(ta_file + ".html", 'wt') as html_file:
        html_file.write(html)

    # 4- convert html into png
    os.system ("cutycapt --url=\"file://"+ta_file+".html\" --out=\"" + ta_file + ".png\"")
    os.remove(ta_file+".html")
    return ta_file + ".png"


def get_SFARI_result(gene_name):
    sfari_url = "https://gene.sfari.org/autdb/submitsearch?selfld_0=GENES_GENE_SYMBOL&selfldv_0=%s&numOfFields=1&userAction=search&tableName=AUT_HG&submit=Submit+Query" % gene_name
    sfari_scr = False
    r = requests.get(sfari_url)
    if r.status_code == requests.codes.ok:
        if gene_name in r.text:
            sfari_scr = True
    return sfari_scr


def get_pubmed(gene_name):
    info_filename = os.path.join('/home/olivier/', 'pubmed_info_{}'.format(gene_name))
    if os.path.exists(info_filename):
        with open(info_filename, 'rt') as info_file:
            data = json.load(info_file)
            return data['count'], [PubmedEntry(a) for a in data['articles']]

    pm_lst_url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=20&term=%s" % gene_name
    pm_id_lst = []
    pm_total = 0
    r = requests.get(pm_lst_url)
    if r.status_code == requests.codes.ok:
        data = r.json()
        pm_id_lst = data['esearchresult']['idlist']
        pm_total = data['esearchresult']['count']

    articles = []
    pm_details_url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&amp;retmode=json&amp;id=%s" % ','.join(pm_id_lst)
    r = requests.get(pm_details_url)
    if r.status_code == requests.codes.ok:
        data = r.json()
        for pmid in pm_id_lst:
            articles.append(PubmedEntry(data['result'][pmid]))

    info = {
        'count': pm_total,
        'articles': [{'uid':a.uid, 'fulljournalname':a.fulljournalname, 'authors':[{'name':a.firstauthor}], 'lastauthor':a.lastauthor, 'title':a.title, 'elocationid':a.elocationid} for a in articles]
    }
    with open(info_filename, 'wt') as info_file:
        json.dump(info, info_file)

    return pm_total, articles




def get_data():
    logger.info('Listing VCF files and indexes...')
    data = get_indexes_filenames()
    logger.info('Extracting gene information...')
    for index, index_data in data.items():
        for mode, mode_data in index_data.items():
            with gzip.open(mode_data.vcf_filename, 'rt') as vcf:
                mode_data.genes = extract_genes(vcf, mode_data.min_variant_count)
    _data = {} # TODO FIXME testing, remove this
#    _data['02-03-SJ'] = data['02-03-SJ'] # TODO FIXME testing, remove this
    _data['08-04-VO'] = data['08-04-VO'] # TODO FIXME testing, remove this
    data = _data # TODO FIXME testing, remove this
    return data

if __name__ == '__main__':
    with open('report.md', 'wt') as report:
        report.write(render_report(get_data(), 'markdown'))
    logger.info('Converting Markdown to OpenDocument')
    import subprocess
    subprocess.run(['pandoc', '-s', '-o', 'report.doc', 'report.md'])
