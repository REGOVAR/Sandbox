
-- 
-- DROP ALL
--
DROP TABLE IF EXISTS public."sample_variant_hg19";
DROP TABLE IF EXISTS public."regmut_hg19";
DROP TABLE IF EXISTS public."variant_hg19";
DROP TABLE IF EXISTS public."project_sample";
DROP TABLE IF EXISTS public."sample";
DROP TABLE IF EXISTS public."file";
DROP TABLE IF EXISTS public."reference";
DROP TABLE IF EXISTS public."subject_patient";
DROP TABLE IF EXISTS public."subject";
DROP TABLE IF EXISTS public."analyze_selection";
DROP TABLE IF EXISTS public."selection";
DROP TABLE IF EXISTS public."analyze";
DROP TABLE IF EXISTS public."template";
DROP TABLE IF EXISTS public."project";
DROP TABLE IF EXISTS public."user";


DROP SEQUENCE IF EXISTS public."variant_hg19_id_seq";
DROP SEQUENCE IF EXISTS public."sample_id_seq";
DROP SEQUENCE IF EXISTS public."file_id_seq";
DROP SEQUENCE IF EXISTS public."reference_id_seq";
DROP SEQUENCE IF EXISTS public."subject_id_seq";
DROP SEQUENCE IF EXISTS public."selection_id_seq";
DROP SEQUENCE IF EXISTS public."analyze_id_seq";
DROP SEQUENCE IF EXISTS public."template_id_seq";
DROP SEQUENCE IF EXISTS public."project_id_seq";
DROP SEQUENCE IF EXISTS public."user_id_seq";


DROP TYPE IF EXISTS tpl_status;
