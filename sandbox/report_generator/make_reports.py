#! /usr/bin/env python3

import collections
import csv
import glob
import gzip
import itertools
import jinja2
import json
import logging
import multiprocessing
import os
import os.path
import pysam
import requests
import shutil
import subprocess
import tempfile
import wand.color
import wand.image

__version__ = '0.1.0'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

root = '/commun/data/users/asdp/Hugodims/VCFscripts'

cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
os.makedirs(cache, exist_ok=True)

modes = collections.OrderedDict([
    ('de novo', (
        '20160921_full_0.0001-0.01-0.005',
        'hapcal.*.parents_genotype.annot.cadd.vcf',
        1
    )),
    ('compound heterozygous', (
        '20160921_full_0.0001-0.01-0.005',
        'hapcal.*.heterozygous_rec.annot.cadd.vcf',
        2
    )),
    ('homozygous', (
        '20160921_full_0.0001-0.01-0.005',
        'hapcal.*.homozygous_rec.annot.cadd.vcf',
        1
    )),
    ('X linked', (
        '20160921_full_0.0001-0.01-0.005',
        'hapcal.*.xlinked.annot.cadd.vcf',
        1
    )),
])

templates = jinja2.Environment(
    loader = jinja2.FileSystemLoader(
        os.path.dirname(os.path.abspath(__file__))
    ),
    trim_blocks = True,
    lstrip_blocks = True,
)

genemap_api = 'http://api.omim.org/api/search/geneMap'
omim_api = 'http://api.omim.org/api/entry'
omim_api_key_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.omim_api_key')

entrez_api = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/{}.fcgi'

strasbourg_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strasbourg_di_panels.csv')
sfari_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sfari_20160914.csv')
rvis_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rvis_v3_20160312.csv')
morbid_map_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Morbid-COe-Eichler_20160914.csv')

with open(omim_api_key_filename, 'rt') as omim_api_key_file:
    omim_api_key = omim_api_key_file.read()

annotation_ids = {
    'SnpEff': ['Annotation', 'Annotation_Impact', 'Feature_Type', 'Rank', 'HGVS.c', 'HGVS.p'],
    'dbNSFP': ['dbNSFP_1000Gp1_AF', 'dbNSFP_ExAC_AF', 'dbNSFP_ESP6500_AA_AF', 'dbNSFP_ESP6500_EA_AF', 'dbNSFP_SIFT_pred', 'dbNSFP_Polyphen2_HDIV_pred', 'dbNSFP_Polyphen2_HVAR_pred', 'dbNSFP_MutationTaster_pred', 'dbNSFP_CADD_phred', 'dbNSFP_LRT_pred', 'dbNSFP_MetaSVM_pred', 'dbNSFP_MutationAssessor_pred', 'dbNSFP_PROVEAN_pred', 'dbNSFP_GERP___RS', 'dbNSFP_FATHMM_pred', 'dbNSFP_PhastCons100way_vertebrate'],
    'dbNSFP_1000Gp1': ['dbNSFP_1000Gp1_AFR_AF', 'dbNSFP_1000Gp1_AMR_AF', 'dbNSFP_1000Gp1_EUR_AF', 'dbNSFP_1000Gp1_ASN_AF'],
    'dbNSFP_ExAC': ['dbNSFP_ExAC_NFE_AF', 'dbNSFP_ExAC_SAS_AF', 'dbNSFP_ExAC_Adj_AF', 'dbNSFP_ExAC_AFR_AF', 'dbNSFP_ExAC_FIN_AF', 'dbNSFP_ExAC_AMR_AF', 'dbNSFP_ExAC_EAS_AF'],
}
blacklisted_feature_annotations = set(['upstream_gene_variant', 'downstream_gene_variant', 'intron_variant'])

publication_themes = ['autism', 'epilepsy', 'intellectual', 'mental', 'schizophrenia', 'seizures']

id_genes_list = 'https://raw.githubusercontent.com/REGOVAR/GenesPanel/master/intellectual_disability.lst'
r = requests.get(id_genes_list)
if r.status_code == requests.codes.ok:
    id_genes = set(r.text.splitlines())
else:
    logger.warning('Unable to access the list of ID genes')
    id_genes = set()

strasbourg_panels = {}
with open(strasbourg_filename, 'rt') as strasbourg_file:
    strasbourg_reader = csv.reader(strasbourg_file, delimiter=',', quotechar='"')
    next(strasbourg_reader, None)  # skip the headers
    for row in strasbourg_reader:
        strasbourg_panels[row[0]] = row[1]

sfari_genes = set()
with open(sfari_filename, 'rt') as sfari_file:
    sfari_reader = csv.reader(sfari_file, delimiter=',', quotechar='"')
    next(sfari_reader, None)  # skip the headers
    for row in sfari_reader:
        sfari_genes.add(row[0])

rvis_score = {}
with open(rvis_filename, 'rt', newline='') as rvis_file:
    rvis_reader = csv.reader(rvis_file, delimiter=',', quotechar='"')
    rvis_column_names = next(rvis_reader, None)  # headers
    for row in rvis_reader:
        rvis_score[row[0]] = { rvis_column_names[column_id]: column_value for column_id, column_value in enumerate(row) }

morbid_map_score = {}
with open(morbid_map_filename, 'rt') as morbid_map_file:
    morbid_map_reader = csv.reader(morbid_map_file, delimiter=',', quotechar='"')
    next(morbid_map_reader, None)  # skip the headers
    for row in morbid_map_reader:
        values = [int(row[column_id] or 0) if row[column_id] and row[column_id] != '#N/A' else 0 for column_id in [4, 5, 22, 23, 24]]
        values.append(sum(values[2:5]))
        morbid_map_score[row[3]] = values

class ModeData:
    def __init__(self, vcf_filename, min_variant_count):
        self.vcf_filename = vcf_filename
        self.min_variant_count = min_variant_count

def fill_omim_info(gene_data, gene_name):
    info_filename = os.path.join(cache, 'omim_info_{}'.format(gene_name))
    if os.path.exists(info_filename):
        with open(info_filename, 'rt') as info_file:
            info = json.load(info_file)
            gene_data.mim_number = info['mim_number']
            gene_data.name = info['name']
            gene_data.symbols = info['symbols']
            gene_data.text = info['text']
        return

    def get_gene_map_list(name):
        r = requests.get(genemap_api, params = {
            'search': name,
            'format': 'json',
            'apiKey': omim_api_key,
        })
        if r.status_code == requests.codes.ok:
            data = r.json()
            response = data['omim']['searchResponse']
            if response['totalResults'] == 0:
                if response['searchSpelling']:
                    return get_gene_map_list(response['searchSpelling'])
                return None
            return response['geneMapList']

    gene_map_list = get_gene_map_list(gene_name)
    if gene_map_list:
        for gene_map_list_entry in gene_map_list:
            gene_map = gene_map_list_entry['geneMap']
            gene_map['geneSymbols'] = [symbol.strip() for symbol in gene_map['geneSymbols'].split(',')]
            symbols = set([symbol.lower() for symbol in gene_map['geneSymbols']])
            if gene_name.lower() in symbols:
                gene_data.mim_number = gene_map['mimNumber']
                gene_data.name = gene_map['geneName']
                gene_data.symbols = gene_map['geneSymbols']
                gene_data.text = []
                r = requests.get(omim_api, params = {
                    'mimNumber': gene_data.mim_number,
                    'include': 'text',
                    'format': 'json',
                    'apiKey': omim_api_key,
                })
                if r.status_code == requests.codes.ok:
                    data = r.json()
                    gene_entry = data['omim']['entryList'][0]['entry']
                    for textSection in gene_entry['textSectionList']:
                        gene_data.text.append(textSection['textSection']['textSectionContent'])
                else:
                    logger.warning('Unable to get the OMIM entry for gene {}'.format(gene_name))
                break
        else:
            logger.warning('Unable to find the OMIM gene map for gene {}'.format(gene_name))
    else:
        logger.warning('Unable to find the OMIM gene map for gene {}'.format(gene_name))
    info = {
        'mim_number': gene_data.mim_number,
        'name': gene_data.name,
        'symbols': gene_data.symbols,
        'text': gene_data.text,
    }
    with open(info_filename, 'wt') as info_file:
        json.dump(info, info_file)

class GeneData:
    def __init__(self, name):
        self.mim_number = None
        self.name = None
        self.symbols = []
        self.text = []
        self.article_count = 0
        self.articles = []

        fill_omim_info(self, name)

        self.strasbourg_panel = strasbourg_panels.get(name, None)
        self.strasbourg_panel_as = None
        if not self.strasbourg_panel:
            for symbol in self.symbols:
                self.strasbourg_panel = strasbourg_panels.get(symbol, None)
                if self.strasbourg_panel:
                    self.strasbourg_panel_as = symbol
                    break

        self.id_gene = (name in id_genes)
        self.id_gene_as = None
        if not self.id_gene:
            for symbol in self.symbols:
                self.id_gene = (symbol in id_genes)
                if self.id_gene:
                    self.id_gene_as = symbol
                    break

        self.sfari_gene = (name in sfari_genes)
        self.sfari_gene_as = None
        if not self.sfari_gene:
            for symbol in self.symbols:
                self.sfari_gene = (symbol in sfari_genes)
                if self.sfari_gene:
                    self.sfari_gene_as = symbol
                    break

        self.rvis_score = rvis_score.get(name, None)
        self.rvis_score_as = None
        if not self.rvis_score:
            for symbol in self.symbols:
                self.rvis_score = rvis_score.get(symbol, None)
                if self.rvis_score:
                    self.rvis_score_as = symbol
                    break

        self.morbid_map_score = morbid_map_score.get(name, None)
        self.morbid_map_score_as = None
        if not self.morbid_map_score:
            for symbol in self.symbols:
                self.morbid_map_score = morbid_map_score.get(symbol, None)
                if self.morbid_map_score:
                    self.morbid_map_score_as = symbol
                    break

        self.hbt_image = get_hbt_image(name)
        self.hbt_image_as = None
        if not self.hbt_image:
            for symbol in self.symbols:
                self.hbt_image = get_hbt_image(symbol)
                if self.hbt_image:
                    self.hbt_image_as = symbol
                    break

        # TODO FIXME protein / tissue atlas snapshot

        self.sp_image = get_sp_image(name)
        self.sp_image_as = None
        if not self.sp_image:
            for symbol in self.symbols:
                self.sp_image = get_sp_image(symbol)
                if self.sp_image:
                    self.sp_image_as = symbol
                    break

        # TODO FIXME Decipher snapshot

        fill_pubmed_articles(self, name)
        self.articles_as = None
        if not self.article_count:
            for symbol in self.symbols:
                fill_pubmed_articles(self, symbol)
                if self.article_count:
                    self.article_as = symbol
                    break
        self.articles = collections.OrderedDict()
        for theme in publication_themes:
            pubmed_data = PubMedData()
            fill_pubmed_articles(pubmed_data, name, theme)
            if not pubmed_data.article_count:
                for symbol in self.symbols:
                    fill_pubmed_articles(pubmed_data, symbol, theme)
                    if pubmed_data.article_count:
                        pubmed_data.gene_name = symbol
                        break
            if pubmed_data.article_count:
                self.articles[theme] = pubmed_data

class Gene:
    __cache = {}
    def __init__(self, name, variants):
        self.name = name
        self.variants = variants
        self.data = Gene.__cache.setdefault(name, GeneData(name))
        self.aliases = list(itertools.chain([self.name], sorted(set(self.data.symbols) - set([self.name]))))

        # TODO aliases from genecards and NCBI as well

    def get_formated_aliases(self, template):
        return [template.format(alias, alias) for alias in self.aliases]

    def get_variant_annotations(self, *annotation_ids):
        if len(annotation_ids) > 1:
            return [', '.join(value) for value in zip(*tuple([self.get_variant_annotations(annotation_id) for annotation_id in annotation_ids]))]
        else:
            annotation_id = annotation_ids[0]

        def stringify(value):
            if type(value) is float:
                if value < .0010:
                    return '{:.2e}'.format(value)
                else:
                    return '{:.4f}'.format(value)
            return str(value)

        variant_annotations = []
        for variant in self.variants:
            annotations = variant.annotations.get(annotation_id, '')
            if type(annotations) is tuple:
                variant_annotations.append(', '.join([stringify(annotation) for annotation in annotations]))
            else:
                variant_annotations.append(stringify(annotations))
        return variant_annotations

    def get_formated_variant_ids(self, template):
        return [variant.get_formated_ids(template) for variant in self.variants]

    def get_clinical_significances(self):
        return [variant.get_clinical_significances() for variant in self.variants]

class VariantData:
    def __init__(self):
        self.genes = set()

class Variant:
    __cache = {}

    def __init__(self, chromosome, position, reference, alternatives, ids, clinical_significances, gene_name):
        self.chromosome = chromosome
        self.position = position
        self.reference = reference
        self.alternatives = alternatives
        self.ids = ids
        self.clinical_significances = clinical_significances
        self.gene_name = gene_name
        self.annotations = {}
        self.features = {}
        self.data = Variant.__cache.setdefault((chromosome, position, reference, alternatives), VariantData())
        self.data.genes.add(gene_name)

    def has_overlaps(self):
        return len(self.data.genes) > 1

    def overlaps(self):
        return sorted([gene for gene in self.data.genes if gene != self.gene_name])

    def get_formated_ids(self, template):
        return ', '.join([template.format(variant_id, variant_id) for variant_id in self.ids])

    def get_clinical_significances(self):
        return ', '.join([clinical_significance and '{}: {}'.format(*clinical_significance) or '' for clinical_significance in self.clinical_significances])

class Feature:
    def __init__(self, name):
        self.name = name
        self.annotations = {}

def upper_first_letter(string):
    return string[:1].upper() + string[1:]

def get_vcf_filenames(directory, pattern):
    return glob.glob(os.path.join(root, directory, pattern), recursive = True)

def extract_index(filename):
    return filename.split(os.sep)[-1].split('.')[1][:-2]

def get_indexes_filenames():
    result = {}
    for mode, (directory, pattern, min_variant_count) in modes.items():
        filenames = get_vcf_filenames(directory, pattern)
        for filename in filenames:
            index = extract_index(filename)
            result.setdefault(index, collections.OrderedDict())[mode] = ModeData(filename, min_variant_count)
    return collections.OrderedDict(sorted(result.items(), key = lambda index: index[3:5] + index[0:2] + index[6:9]))

def get_snpeff_annotation_id(info):
    if 'ANN' in info:
        snpeff_annotation_id = 'ANN'
        if 'EFF' in info:
            logger.warning('Found both ANN and EFF in header, using ANN')
    elif 'EFF' in info:
        snpeff_annotation_id = 'EFF'
    else:
        snpeff_annotation_id = None
        logger.warning('Neither EFF nor ANN found in header')
    return snpeff_annotation_id

def get_snpeff_annotation_columns(snpeff_metadata):
    #metadata: contenu de la ligne info qui contient un id en particulier
    annotations = [annotation.strip() for annotation in snpeff_metadata.description.split("'")[1].split('|')]
    snpeff_annotation_columns = {annotation: position for position, annotation in enumerate(annotations)}
    return snpeff_annotation_columns

def get_vep_annotation_columns(vep_metadata):
    annotations = [annotation.strip() for annotation in vep_metadata.description.split(':')[1].split('|')]
    vep_annotation_columns = {annotation: position for position, annotation in enumerate(annotations)}
    return vep_annotation_columns

def extract_genes(vcf_filename, min_variant_count):
    try:
        vcf_context = pysam.VariantFile(vcf_filename)
    except ValueError:
        logger.warning('Error while loading {}, probably bug #259 of pysam'.format(vcf_filename))
        return []
    with vcf_context as vcf_file:
        snpeff_annotation_id = get_snpeff_annotation_id(vcf_file.header.info)
        if snpeff_annotation_id is None:
            logger.warning('SnpEff annotation ID (ANN or EFF) not found in header for {}'.format(vcf_filename))
            return []
        snpeff_metadata = vcf_file.header.info[snpeff_annotation_id]
        snpeff_annotation_columns = get_snpeff_annotation_columns(snpeff_metadata)
        if 'Gene_Name' not in snpeff_annotation_columns:
            logger.warning('Gene_Name not found in SnpEff annotation description in header for {}'.format(vcf_filename))
            return []
        gene_name_column_number = snpeff_annotation_columns['Gene_Name']
        feature_id_column_number = snpeff_annotation_columns['Feature_ID']
        if 'CSQ' in vcf_file.header.info:
            vep_metadata = vcf_file.header.info['CSQ']
            vep_annotation_columns = get_vep_annotation_columns(vep_metadata)
        feature_annotation_column_number = snpeff_annotation_columns['Annotation']
        clinical_significance_levels = {level.strip(): label.strip().lower() for level, label in [level_info.split('-') for level_info in 'CLNSIG' in vcf_file.header.info and vcf_file.header.info['CLNSIG'].description.split(',')[1:] or []]}
        genes = {}
        for row in vcf_file:
            # TODO FIXME VEP (CSQ) annotations
            snpeff_annotations = row.info[snpeff_annotation_id]
            for snpeff_annotation in snpeff_annotations:
                feature_annotations = snpeff_annotation.split('|')
                gene_name = feature_annotations[gene_name_column_number]
                if gene_name:
                    variant_ids = row.id and row.id.split(';') or []
                    variant_clinical_significances = 'CLNSIG' in row.info and [(clinical_significance, clinical_significance_levels[clinical_significance]) for clinical_significance in itertools.chain.from_iterable([clinical_significances.split('|') for clinical_significances in row.info['CLNSIG']])] or []
                    variant = genes.setdefault(gene_name, {}).setdefault((row.chrom, row.pos, row.ref, row.alts), Variant(row.chrom, row.pos, row.ref, row.alts, variant_ids, variant_clinical_significances, gene_name))
                    for annotation_id in annotation_ids['dbNSFP']:
                        if annotation_id in row.info:
                            variant.annotations[annotation_id] = row.info[annotation_id]
                    dbNSFP_1000Gp1_values = [row.info[annotation_id] for annotation_id in annotation_ids['dbNSFP_1000Gp1'] if annotation_id in row.info]
                    variant.annotations['dbNSFP_1000Gp1_max'] = tuple(max(values) for values in zip(*tuple(dbNSFP_1000Gp1_values)))
                    dbNSFP_ExAC_values = [row.info[annotation_id] for annotation_id in annotation_ids['dbNSFP_ExAC'] if annotation_id in row.info]
                    variant.annotations['dbNSFP_ExAC_max'] = tuple(max(values) for values in zip(*tuple(dbNSFP_ExAC_values)))
                    #print(row, dbNSFP_ExAC_values, variant.annotations['dbNSFP_ExAC_max'])
                    feature_name = feature_annotations[feature_id_column_number]
                    feature_annotation = feature_annotations[feature_annotation_column_number]
                    if feature_name not in variant.features and \
                       feature_annotation not in blacklisted_feature_annotations:
                        feature = Feature(feature_name)
                        for annotation_id in annotation_ids['SnpEff']:
                            feature.annotations[annotation_id] = feature_annotations[snpeff_annotation_columns[annotation_id]]
                        variant.features[feature_name] = feature

    def filter_genes():
        for gene_name, variants in genes.items():
            variants = [variant for variant in variants.values() if variant.features]
            for variant in variants:
                variant.features = sorted(variant.features.values(), key = lambda feature: feature.name)
            if len(variants) >= min_variant_count:
                yield Gene(gene_name, sorted(variants, key=lambda variant: (variant.chromosome, variant.position, variant.reference)))

    return sorted(filter_genes(), key = lambda gene: gene.name)

def render_report(data, template_name):
    template = templates.get_template('{}.tpl'.format(template_name))
    return template.render(
        data=data,
        len=len,
        upper_first_letter=upper_first_letter,
    )

def convert_html(source, destination, delay=0):
    subprocess.run(['CutyCapt', '--url={}'.format(source), '--out={}'.format(destination), '--delay={}'.format(delay)])

def convert_doc(source, destination):
    subprocess.run(['pandoc', '-s', '-o', destination, source])

def get_hbt_image(gene_name):
    image_url  = 'http://hbatlas.org/hbtd/images/wholeBrain/{}.pdf'.format(gene_name)
    image_filename = os.path.join(cache, 'hbt_image_{}.png'.format(gene_name))
    missing_filename = os.path.join(cache, 'hbt_image_{}.missing'.format(gene_name))
    if os.path.exists(image_filename) :
        return image_filename
    elif os.path.exists(missing_filename):
        return None
    try:
        r = requests.get(image_url, stream=True)
        if r.status_code == requests.codes.ok:
            with tempfile.TemporaryFile() as image_file:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, image_file)
                image_file.seek(0)
                with wand.image.Image(file=image_file, resolution=200) as image:
                    with wand.image.Image(width=image.width, height=image.height, background=wand.color.Color('white')) as bg:
                        bg.composite(image, 0, 0)
                        bg.save(filename=image_filename)
            return image_filename
        else:
            logger.warning('Unable to retrieve PDF from HBT for {}'.format(gene_name))
    except:
        logger.warning('Unable to convert HBT PDF to PNG for the gene {}'.format(gene_name))
    with open(missing_filename, 'wb') as image:
        pass
    return None

def get_sp_image(gene_name):
    image_url  = 'http://string-db.org/api/image/network?identifier={}_HUMAN'.format(gene_name)
    image_filename = os.path.join(cache, 'sp_image_{}.png'.format(gene_name))
    missing_filename = os.path.join(cache, 'sp_image_{}.missing'.format(gene_name))
    if os.path.exists(image_filename):
        return image_filename
    elif os.path.exists(missing_filename):
        return None
    try:
        r = requests.get(image_url, stream=True)
        if r.status_code == requests.codes.ok:
            with open(image_filename, 'wb') as image_file:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, image_file)
            return image_filename
        else:
            logger.warning('Unable to retrieve image from String Pathway for {}'.format(gene_name))
    except:
        logger.warning('Unable to retrieve image from String Pathway for {}'.format(gene_name))
    with open(missing_filename, 'wb') as image:
        pass
    return None

def get_decipher_image(gene_name, output_folder):
    dec_filename = output_folder + '/' + gene_name  + '_decipher.png'
    dec_url  = 'https://decipher.sanger.ac.uk/search?q=%s#consented-patients/results' % gene_name

    if os.path.isfile(dec_filename) :
        return dec_filename

    # 1- retrieve image
    convert_html(dec_url, '{}_source.png'.format(dec_filename), 3000)

    # 2- crop image
    if os.path.isfile(dec_filename + '_source.png'):
        with open(dec_filename + '_source.png', 'rb') as f:
            with wand.image.Image(file=f) as image:
                w = image.width - 10
                h = image.height - 315 - 360
                image.crop(5, 315, width=w, height=h)
                image.save(filename=dec_filename)
                os.remove(dec_filename + '_source.png')
                return dec_filename
    else:
        logger.warning('Unable to retrieve image from Decipher for the gene {}'.format(gene_name))

    return output_folder + '/error.png'

def get_ta_image(gene_name, output_folder):
    ta_filename = output_folder + '/' + gene_name + '_ta'
    ta_url  = 'http://www.proteinatlas.org/search/%s' % gene_name

    if os.path.isfile(ta_filename + '.png') :
        return ta_filename + '.png'

    # 1- Retrieve "true url" from TA "user website url"
    r = requests.get(ta_url)
    if r.status_code == requests.codes.ok:
        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.find_all('a'):
            if (link.text==gene_name):
                ta_url = 'http://www.proteinatlas.org' + link.get('href')

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
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/search.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/image.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/image_stack.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/utils/d3.min.js?version=15.0.0"></script>
        <script language="javascript" type="text/javascript" src="http://www.proteinatlas.org/utils/box.min.js?version=15.0.0"></script>
    </head>
    <body>
"""
        p = soup.find('p', text='RNA EXPRESSION OVERVIEW')
        html += p.findParent('table').prettify()
        html += '\n</body></html>'

    # 3- save into file
    with open(ta_filename + '.html', 'wt') as ta_file:
        ta_file.write(html)

    # 4- convert html into png
    convert_html('file://{}.html'.format(ta_filename), '{}.png'.format(ta_filename), 500)
    os.remove(ta_filename+'.html')
    return ta_filename + '.png'

class PubMedData:
    def __init__(self):
        self.gene_name = None
        self.article_count = 0
        self.articles = []

def fill_pubmed_articles(pubmed_data, gene_name, theme=''):
    info_filename = os.path.join(cache, 'pubmed_info_{}_{}'.format(gene_name, theme))
    if os.path.exists(info_filename):
        with open(info_filename, 'rt') as info_file:
            info = json.load(info_file)
            pubmed_data.article_count = info['article_count']
            pubmed_data.articles = info['articles']
        return

    # TODO FIXME pubmed from all aliases as well (aggregate with OR)

    pubmed_ids = []
    r = requests.get(entrez_api.format('esearch'), params = {
        'term': '{} AND {}'.format(gene_name, theme),
        'db': 'pubmed',
        'retmode': 'json',
        'retmax': 10,
    })
    if r.status_code == requests.codes.ok:
        data = r.json()
        pubmed_ids = data['esearchresult']['idlist']
        pubmed_data.article_count = int(data['esearchresult']['count'])
    else:
        logger.warning('Unable to get the PubMed publications for gene {} and theme {}'.format(gene_name, theme))
        return
    r = requests.get(entrez_api.format('esummary'), params = {
        'id': ','.join(pubmed_ids),
        'db': 'pubmed',
        'retmode': 'json',
    })
    if r.status_code == requests.codes.ok:
        data = r.json()
        for pubmed_id in pubmed_ids:
            pubmed_data.articles.append(data['result'][pubmed_id])
    else:
        logger.warning('Unable to get the PubMed publication details for gene {} and theme {}'.format(gene_name, theme))
        return

    info = {
        'article_count': pubmed_data.article_count,
        'articles': pubmed_data.articles
    }
    with open(info_filename, 'wt') as info_file:
        json.dump(info, info_file)

def get_data():
    logger.info('Listing VCF files and indexes...')
    data = get_indexes_filenames()
    logger.info('Extracting gene information...')
    with multiprocessing.Pool() as pool:
        for index, index_data in data.items():
            for mode, mode_data in index_data.items():
                mode_data.async_job = pool.apply_async(extract_genes, (mode_data.vcf_filename, mode_data.min_variant_count))
        for index, index_data in data.items():
            for mode, mode_data in index_data.items():
                mode_data.genes = mode_data.async_job.get()
                del mode_data.async_job
    return data

if __name__ == '__main__':
    data = get_data()
    if data:
        os.makedirs('reports', exist_ok=True)
        logger.info('Rendering reports as reStructuredText...')
        for index, index_data in data.items():
            with open('reports/report_{}.rst'.format(index), 'wt') as report:
                report.write(render_report({index: index_data}, 'restructuredtext'))
        logger.info('Converting reports from reStructuredText to Microsoft Word...')
        pool = multiprocessing.Pool()
        for index in data:
            pool.apply_async(convert_doc, ('reports/report_{}.rst'.format(index), 'reports/report_{}.docx'.format(index)))
        pool.close()
        pool.join()
        logger.info('{} reports generated.'.format(len(data)))
