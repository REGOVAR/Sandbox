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
* Present in public databases:

  * REGOVAR GenePanel's ID genes list: {{gene.data.id_gene and 'yes' or 'no'}}{{gene.data.id_gene_as and '( as {})'.format(gene.data.id_gene_as) or ''}}
  * 1000 genomes:
  * ESP:
  * dbSNP:
  * ExAC:

* In silico prediction:

  * SIFT:
  * PolyPhen2 HVAR:
  * MutationTaster:
  * CADD phred:
  * GERP:
  * RVIS: `{{gene.data.rvis_score and (gene.data.rvis_score[0] == 'NA' and 'N/A' or '{} ({}%)'.format(*gene.data.rvis_score)) or 'unknown'}} <http://genic-intolerance.org/Search?query={{gene.name}}>`_{{gene.data.rvis_score_as and ' (as {})'.format(gene.data.rvis_score_as) or ''}}

* Morbid map:

* Cerebral expression

  * GTEX: {{gene.render_aliases('`{} <http://www.gtexportal.org/home/gene/{}>`_')}}
  * Protein Atlas: {{gene.render_aliases('`{} <http://www.proteinatlas.org/search/{}>`_')}}
  * Tissue Atlas: 
            {% if gene.data.hbt_image %}
  * Human Brain Transcriptome: `{{gene.data.hbt_image_as or gene.name}} <http://hbatlas.org/hbtd/images/wholeBrain/{{gene.data.hbt_image_as or gene.name}}.pdf>`_

    .. image:: {{gene.data.hbt_image}}
       :scale: 20%
       :align: center
            {% else %}
  * Human Brain Transcriptome: not found
            {% endif %}

* SFARI:
* Decipher: {{gene.render_aliases('`{} <https://decipher.sanger.ac.uk/search?q={}#consented-patients/results>`_')}}
            {% if gene.data.sp_image %}
* STRING pathway: `{{gene.data.sp_image_as or gene.name}} <http://string-db.org/api/image/network?identifier={{gene.data.sp_image_as or gene.name}}>`_

    .. image:: {{gene.data.sp_image}}
       :scale: 20%
       :align: center
            {% else %}
* STRING pathway: not found
            {% endif %}
* PubMed:
* {{len(gene.variants)}} variant{{len(gene.variants) > 1 and 's' or ''}} found:

            {% for variant in gene.variants %}
  * {{' '.join(variant)}} {# TODO FIXME substitution / protein #}

            {% endfor %}

	    {% for variant in gene.variants %}
.. image:: /commun/data/users/asdp/Hugodims/VCFscripts/AR/20160901_alltogether/Snapshots/{{index}}_chr{{variant[0]}}:{{variant[1]}}.png
   :scale: 20%
   :align: center
   :alt: Missing IGV snapshot for {{index}}_chr{{variant[0]}}:{{variant[1]}}

            {% endfor %}
        {% endfor %}

    {% endfor %}

{% endfor %}

