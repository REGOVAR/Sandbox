{% for index, index_data in data.items() %}
# {{index}}

Phenotype: cf. ppt

{% for mode, mode_data in index_data.items() %}
## {{mode}}

Candidate genes highlighted with {{mode}} HUGODIMS’s pipeline:

{% for gene in mode_data.genes %}
* {{gene.name}}
{% endfor %}

{% for gene in mode_data.genes %}
### {{gene.name}}

{% for variantId, variant in enumerate(gene.variants) %}

* Variant {{variantId + 1}}: {{' '.join(variant)}} {# TODO FIXME substitution / protein #}

{% endfor %}

{% if gene.data.mim_number %}
OMIM: [{{gene.data.mim_number}}](http://www.omim.org/entry/{{gene.data.mim_number}})

Synonymes : {{gene.data.text}}

Description : {{gene.data.name}}


{% else %}
No information found on OMIM.

{% endif %}

{% for variant in gene.variants %}
![IGV snapshot](/commun/data/users/asdp/Hugodims/VCFscripts/AR/20160827_alltogether_fixed/Snapshots/{{index}}_chr{{variant[0]}}:{{variant[1]}}.png)


{% endfor %}


Present in public databases:
{# TODO FIXME public dbs from SnpEff / SnpSift / VEP #}

In silico prediction:
* [RVIS](http://genic-intolerance.org/Search?query={{gene.name}}) : {{get_rvis_score(gene.name)}}
{# TODO FIXME in silico predictions from SnpEff / SnpSift / VEP #}

Present in the ID genes list: {{gene.data.id_gene and 'yes' or 'no'}}

Morbid Map:
{# TODO FIXME modbid map #}

Cerebral expression:
* GTEX: [{{gene.name}}](http://www.gtexportal.org/home/gene/{{gene.name}})
* TA: [{{gene.name}}](http://www.proteinatlas.org/search/{{gene.name}})
![TA snapshot]({{get_ta_img(gene.name, '/commun/data/users/asdp/Hugodims/VCFscripts/AR/20160827_alltogether_fixed/Snapshots_TA')}})
* HBT: [{{gene.name}}](http://hbatlas.org/hbtd/images/wholeBrain/{{gene.name}}.pdf)
![HBT snapshot]({{get_hbt_image(gene.name, '/commun/data/users/asdp/Hugodims/VCFscripts/AR/20160827_alltogether_fixed/Snapshots_HBT')}})
* SFARI: [{{ if get_SFARI_result(gene.name) : print("OUI") else : print("NON")}}](https://gene.sfari.org/autdb/submitsearch?selfld_0=GENES_GENE_SYMBOL&amp;selfldv_0={{gene.name}}&amp;numOfFields=1&amp;userAction=search&amp;tableName=AUT_HG&amp;submit=Submit+Query)

Decipher: [{{gene.name}}](https://decipher.sanger.ac.uk/search?q={{gene.name}}#consented-patients/results)
![Decipher snapshot]({{get_decipher_img(gene.name, '/commun/data/users/asdp/Hugodims/VCFscripts/AR/20160827_alltogether_fixed/Snapshots_Decipher')}})

STRING pathway: [{{gene.name}}](http://string-db.org/api/image/network?identifier={{gene.name}})
![HBT snapshot]({{get_stp_image(gene.name, '/commun/data/users/asdp/Hugodims/VCFscripts/AR/20160827_alltogether_fixed/Snapshots_STP')}})


{% a_count, pm_lst = get_pubmed(gene.name)  %}
Pubmed (search on gene.name) - {{a_count}} result(s) :
{% for a in pm_lst %}
* [{{a.uid}}](http://www.ncbi.nlm.nih.gov/pubmed/{{a.uid}}) - {{a.title}} <br/>{{a.fulljournalname}} - {{a.pubdate}} by {{a.firstauthor}} ({{a.lastauthor}}) [{{a.elocationid}}]
{% endfor %}


{% a_count, pm_lst = get_pubmed({{gene.name.lower()}}+autism)  %}
Pubmed (search on gene.name + autism) - {{a_count}} result(s) :
{% for a in pm_lst %}
* [{{a.uid}}](http://www.ncbi.nlm.nih.gov/pubmed/{{a.uid}}) - {{a.title}} <br/>{{a.fulljournalname}} - {{a.pubdate}} by {{a.firstauthor}} ({{a.lastauthor}}) [{{a.elocationid}}]
{% endfor %}



{% endfor %}

{% endfor %}
{% endfor %}
