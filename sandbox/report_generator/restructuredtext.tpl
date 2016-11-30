{% for index, index_data in data.items() %}
{{index}}
{{'=' * len(index)}}

Phenotype: cf. ppt

    {% for mode, mode_data in index_data.items() %}
{{upper_first_letter(mode)}}
{{'-' * len(mode)}}

{{len(mode_data.genes)}} candidate gene{{len(mode_data.genes) > 1 and 's' or ''}} highlighted with HUGODIMS’s {{mode}} pipeline:

        {% for gene in mode_data.genes %}
* {{gene.name}}
        {% endfor %}

        {% for gene in mode_data.genes %}
{{gene.name}}
{{'`' * len(gene.name)}}

            {% if gene.data.mim_number %}
* Name: {{gene.data.name}}
* Also known as {{', '.join(gene.data.symbols)}}
* OMIM: `{{gene.data.mim_number}} <http://www.omim.org/entry/{{gene.data.mim_number}}>`_
            {% else %}
* No information found on OMIM: `search for {{gene.name}} <http://omim.org/search/?search={{gene.name}}>`_
            {% endif %}

* {{len(gene.variants)}} variant{{len(gene.variants) > 1 and 's' or ''}} found:

            {% for variant in gene.variants %}
  * {{'{}: chr{} {}: {} → {}'.format(variant.get_formated_ids('`{} <http://www.ncbi.nlm.nih.gov/SNP/snp_ref.cgi?searchType=adhoc_search&type=rs&rs={}>`_') or 'Unknown', variant.chromosome, variant.position, variant.reference, ', '.join(variant.alternatives))}}{% if variant.has_overlaps() %} (overlaps with {{', '.join(variant.overlaps())}}){% endif %}

                {% for feature in variant.features %}

    * {{feature.name}}: {{feature.annotations['Feature_Type']}}:{{feature.annotations['Rank']}}:{{feature.annotations['HGVS.c']}}:{{feature.annotations['HGVS.p']}} ({{', '.join(feature.annotations['Annotation'].split('&'))}}: {{feature.annotations['Annotation_Impact']}})  {{gene.name}}

                {% endfor %}

            {% endfor %}

	    {% for variant in gene.variants %}
.. image:: /commun/data/users/asdp/Hugodims/VCFscripts/AR/20160901_alltogether/Snapshots/{{index}}_chr{{variant.chromosome}}:{{variant.position}}.png
   :scale: 20%
   :align: center
   :alt: Missing IGV snapshot for {{index}}_chr{{variant[0]}}:{{variant[1]}}

            {% endfor %}

* Present in public databases:

  * Strasbourg's ID genes panel: {{gene.data.strasbourg_panel or 'N/A'}}{{gene.data.id_gene_as and ' (as {})'.format(gene.data.id_gene_as) or ''}} {{gene.name}}
  * REGOVAR GenePanel's ID genes list: {{gene.data.id_gene and 'yes' or 'no'}}{{gene.data.id_gene_as and ' (as {})'.format(gene.data.id_gene_as) or ''}} 
  * SFARI autism genes list: {{gene.data.sfari_gene and '`yes <https://gene.sfari.org/autdb/submitsearch?selfld_0=GENES_GENE_SYMBOL&selfldv_0={}&numOfFields=1&userAction=search&tableName=AUT_HG&submit=Submit+Query>`_'.format(gene.data.sfari_gene_as or gene.name) or 'no'}}{{gene.data.sfari_gene_as and ' (as {})'.format(gene.data.sfari_gene_as) or ''}}
  * 1000 genomes (all, max): {{' / '.join(gene.get_variant_annotations('dbNSFP_1000Gp1_AF', 'dbNSFP_1000Gp1_pred')) or 'Ø'}}
  * ESP (AA, EA): {{' / '.join(gene.get_variant_annotations('dbNSFP_ESP6500_AA_AF', 'dbNSFP_ESP6500_EA_AF')) or 'Ø'}}
  * dbSNP: {{' / '.join(gene.get_formated_variant_ids('`{} <http://www.ncbi.nlm.nih.gov/SNP/snp_ref.cgi?searchType=adhoc_search&type=rs&rs={}>`_'))}}
  * ClinVar: {{' / '.join(gene.get_clinical_significances())}} {{gene.name}}
  * ExAC (all, max): {{' / '.join(gene.get_variant_annotations('dbNSFP_ExAC_AF', 'dbNSFP_ExAC_max')) or 'Ø'}} 

* In silico prediction:

  * SIFT: {{' / '.join(gene.get_variant_annotations('dbNSFP_SIFT_pred')) or 'Ø'}}
  * PolyPhen2 (HDIV): {{' / '.join(gene.get_variant_annotations('dbNSFP_Polyphen2_HDIV_pred')) or 'Ø'}}
  * PolyPhen2 (HVAR): {{' / '.join(gene.get_variant_annotations('dbNSFP_Polyphen2_HVAR_pred')) or 'Ø'}}
  * MutationTaster: {{' / '.join(gene.get_variant_annotations('dbNSFP_MutationTaster_pred')) or 'Ø'}}
  * CADD phred: {{' / '.join(gene.get_variant_annotations('dbNSFP_CADD_phred')) or 'Ø'}}
  * LRT: {{' / '.join(gene.get_variant_annotations('dbNSFP_LRT_pred')) or 'Ø'}}
  * MetaSVM: {{' / '.join(gene.get_variant_annotations('dbNSFP_MetaSVM_pred')) or 'Ø'}}
  * MutationAssessor: {{' / '.join(gene.get_variant_annotations('dbNSFP_MutationAssessor_pred')) or 'Ø'}}
  * PROVEAN: {{' / '.join(gene.get_variant_annotations('dbNSFP_PROVEAN_pred')) or 'Ø'}}
  * GERP (RS): {{' / '.join(gene.get_variant_annotations('dbNSFP_GERP___RS')) or 'Ø'}}
  * FATHMM: {{' / '.join(gene.get_variant_annotations('dbNSFP_FATHMM_pred')) or 'Ø'}}
  * phastCons100way_vertebrate: {{' / '.join(gene.get_variant_annotations('dbNSFP_PhastCons100way_vertebrate')) or 'Ø'}}
  * RVIS ESP / OEratio ESP / RVIS ExAC: `{{gene.data.rvis_score and ((gene.data.rvis_score['ALL_0.1%'] == 'NA' and 'Ø' or '{} ({}%)'.format(gene.data.rvis_score['ALL_0.1%'], gene.data.rvis_score['%ALL_0.1%'])) + ' / ' + (gene.data.rvis_score['OEratio'] == 'NA' and 'Ø' or '{} ({}%)'.format(gene.data.rvis_score['OEratio'], gene.data.rvis_score['%OEratio'])) + ' / ' + (gene.data.rvis_score['%ExAC_0.05%popn'] == 'NA' and 'Ø' or '{} ({}%)'.format('', gene.data.rvis_score['%ExAC_0.05%popn']))) or 'unknown'}} <http://genic-intolerance.org/Search?query={{gene.name}}>`_{{gene.data.rvis_score_as and ' (as {})'.format(gene.data.rvis_score_as) or ''}}

* Morbid map: {% if gene.data.morbid_map_score %}deletion found in {{gene.data.morbid_map_score[0]}} patient{{gene.data.morbid_map_score[0] > 1 and 's' or ''}} vs {{gene.data.morbid_map_score[1]}} control{{gene.data.morbid_map_score[0] > 1 and 's' or ''}}. {{gene.data.morbid_map_score[5] > 0 and 'Published de novo ({} LoF, {} missense, {} de novo)'.format(*gene.data.morbid_map_score[2:5]) or 'Not published'}}{% else %}N/A{% endif %}.

* Cerebral expression:

  * GTEX: {{','.join(gene.get_formated_aliases('`{} <http://www.gtexportal.org/home/gene/{}>`_'))}}
  * Protein Atlas (tissue): {{','.join(gene.get_formated_aliases('`{} <http://www.proteinatlas.org/search/{}>`_'))}}
            {% if gene.data.hbt_image %}
  * Human Brain Transcriptome: `{{gene.data.hbt_image_as or gene.name}} <http://hbatlas.org/hbtd/images/wholeBrain/{{gene.data.hbt_image_as or gene.name}}.pdf>`_

    .. image:: {{gene.data.hbt_image}}
       :scale: 20%
       :align: center
            {% else %}
  * Human Brain Transcriptome: not found
            {% endif %}

* Decipher: {{','.join(gene.get_formated_aliases('`{} <https://decipher.sanger.ac.uk/search?q={}#consented-patients/results>`_'))}}
            {% if gene.data.sp_image %}
* STRING pathway: `{{gene.data.sp_image_as or gene.name}} <http://string-db.org/api/image/network?identifier={{gene.data.sp_image_as or gene.name}}>`_

    .. image:: {{gene.data.sp_image}}
       :scale: 20%
       :align: center
            {% else %}
* STRING pathway: not found
            {% endif %}

* PubMed: `{{gene.data.article_count}} article{{gene.data.article_count > 1 and 's' or ''}} found <http://www.ncbi.nlm.nih.gov/pubmed/?term={{gene.data.articles_as or gene.name}}>`_{{gene.data.articles_as and ' (as {})'.format(gene.data.articles_as) or ''}}:

	    {% for theme, article_info in gene.data.articles.items() %}

  * {{theme}}: `{{article_info.article_count}} article{{article_info.article_count > 1 and 's' or ''}} found <http://www.ncbi.nlm.nih.gov/pubmed/?term={{article_info.articles_as or '{}+{}'.format(article_info.gene_name or gene.name, theme)}}>`_{{article_info.gene_name and ' (as {})'.format(article_info.gene_name) or ''}}:

    	        {% for article in article_info.articles %}
    * {{article['authors'] and '{} et al., '.format(article['authors'][0]['name']) or ''}}**`{{article['title']}} <http://www.ncbi.nlm.nih.gov/pubmed/{{article['uid']}}>`_**, {{article['fulljournalname']}}, {{article['pubdate']}}{{article.elocationid and ' ({})'.format(article.elocationid) or ''}}

                {% endfor %}

            {% endfor %}

        {% endfor %}

    {% endfor %}

{% endfor %}
