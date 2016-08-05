Here is a state of the art of genetic data analysis. In the context of Regovar project, we will focus mainly on variant analysis, prediction tools and on databases available.
Once this state of the art done, we will decide which features and data that will be managed by Regovar.


Softwares
--
* [ ] Alamut visual (license fee)
* [ ] Alamut Batch (license fee)
* [ ] Annovar
* [ ] BAPT - [ext link](http://consortium-normand.baclesse.fr/index.php/Pr%C3%A9sentation_de_BAPT) (free)
* [ ] DNAstar (trial, license fee)
* [ ] ERIS
* [ ] EVA (old version free, web)
* [ ] [**ExAM**] (http://sourceforge.net/projects/exam-exome-analysis-and-mining/) (free)
* [x] [**Exomiser**](http://www.sanger.ac.uk/science/tools/exomiser)
  - **Resume :** software to finds potential disease-causing variants from whole-exome or whole-genome sequencing data.
     * INPUTS : VCF
     * OUTPUTS : TSV, VCF
  - **Pros :**
     * GNU AGPL (V3) - _ie. free to use, change, and share this software_
     * use of [phenotype onthology (HPO)](http://www.human-phenotype-ontology.org/) 
     * a simplified online interface to test the tool [here](http://www.sanger.ac.uk/resources/software/exomiser/submit/) 
  - **Cons :**
     * not user friendly - _no GUI, only command line and "bash script" file to work_
     * "one shot" - _no interactivity, run the command on the input file and basta_
     * user alone - _no simple way to share work with other users, or to reuse filters set in another project_
     * not for MacOS - _only available for Windows and Linux_
* [ ] Galaxy (libre, web)
* [ ] Gemini (libre, console)
* [ ] GenoDiag (payant), test gratuit dispo (mail 02/2016)
* [ ] [**Genouest**](http://www.genouest.org/) - [git](https://github.com/genouest) (libre)
* [ ] KNIME (libre)
* [ ] Polyweb
* [ ] Taverne (libre)
* [ ] UCSC genome browser (libre, web)
* [ ] [**VarAFT**](http://varaft.eu/) (free)
* [ ] [**VaRank**](http://www.lbgi.fr/VaRank/) (free, mail 12/2015)
* [ ] Variant Analysis
* [x] [**VariantTools**](http://varianttools.sourceforge.net/)
  - **Resume :** software for the manipulation, annotation, selection, simulation, and analysis of variants
     * INPUTS : [Multiple](http://varianttools.sourceforge.net/Format/HomePage)
     * OUTPUTS : can export data in same formats supported in INPUTS
  - **Pros :**
     * GNU Public License (V3) - _ie. free to use, change, and share this software_
     * lot of [features](http://varianttools.sourceforge.net/#features)
     * work by project - _ie. working several sample at the same time_
     * speed - _once variant/vcf are imported in the database_
     * possibility to save intermediate state while filtering processe
  - **Cons :**
     * not user friendly - _no GUI, only command line_
     * space consumming - _all db used for the analyse (like hg19) are imported on the user computer_
     * user alone - _no simple way to share work with other users, or to reuse filters set in another project_
     * not for Windows - _only available for MacOS and Linux_
* [ ] VarSeq (mail Sacha 22/07/2016)
* [ ] wAnnovar 


Prediction
--
* [ ] CADD
* [ ] FATHMM
* [ ] GERP
* [ ] Human Splicing Finder
* [ ] LRScore
* [ ] LRT
* [ ] Mutation Taster
* [ ] MutationAssessor
* [ ] PhastCons
* [ ] PhyloP
* [ ] Polyphen2 (HDIV HVAR)
* [ ] RadialSVM
* [ ] SIFT
* [ ] SiPhy
* [ ] UMD Predictor
* [ ] Vest3Score

Databases
--
_Variants_
* [ ] ?? Base de donnée cumulant les grandes cohortes d'exomes
* [ ] 1000 Genomes
* [ ] Cancer gene census
* [ ] CG46
* [ ] ClinVar
* [ ] Cosmic
* [ ] dbNSFP
* [ ] dbSNP
* [ ] Decipher et DDD
* [ ] EVS
* [ ] ExAC
* [ ] gEAR [ext link] (http://gear.igs.umaryland.edu)
* [ ] Geno2MP [ext link] (http://geno2mp.gs.washington.edu/Geno2MP/#/)
* [ ] GoNL
* [ ] GWAS
* [ ] HRC
* [ ] Kaviar
* [ ] MakeMatcher
* [ ] Matchmaker Exchange
* [ ] MyGene2
* [ ] NCI60
* [ ] Occular Tissue DB [ext link] (https://genome.uiowa.edu/otdb/)
* [ ] Phenome Central
* [ ] SHIELD [ext link] (https://shield.hms.harvard.edu/)
* [ ] Sisu [ext link] (http://www.sisuproject.fi)

_Misc_
* [ ] ENCODE
* [ ] HPO
* [ ] HGMD
* [ ] OMIM
* [ ] RefGene
  - **Resume :** list of know transcriptions
  - [Schema description](http://ucscbrowser.genap.ca/cgi-bin/hgTables?hgsid=7474_TguneC5qhYKxDwJ1WJ3XiiTSRbCd&hgta_doSchemaDb=hg19&hgta_doSchemaTable=refGene)
  - [SQL schema](http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/refGene.sql), [data (txt.gz)](http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/refGene.txt.gz)