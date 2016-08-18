-- 
-- CREATE ALL - V1.0.0
--

CREATE TYPE tpl_status AS ENUM ('draft', 'released', 'validated');
CREATE TYPE analysis_status AS ENUM ('created', 'queued', 'importing', 'filtering', 'done', 'closed', 'diagnostic');
CREATE TYPE subject_relation_type AS ENUM ('parent', 'unknow');
CREATE TYPE regmut_pathos AS ENUM ('class1', 'class2', 'class3', 'class4a', 'class4b', 'class5');
CREATE TYPE regmut_contrib AS ENUM ('none', 'uncertain', 'partial', 'full');




CREATE SEQUENCE public.user_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.user_id_seq
	OWNER TO regovar;

CREATE TABLE public."user"
(
	id integer NOT NULL DEFAULT nextval('user_id_seq'::regclass),
	lastname character varying(255) COLLATE pg_catalog."C.UTF-8",
	firstname character varying(255) COLLATE pg_catalog."C.UTF-8",
	email character varying(255) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	location character varying(255) COLLATE pg_catalog."C.UTF-8",
	function character varying(255) COLLATE pg_catalog."C.UTF-8",
	last_activity_date timestamp without time zone,
	settings text, 
	CONSTRAINT user_pkey PRIMARY KEY (id),
	CONSTRAINT user_email_key UNIQUE (email)
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public."user"
	OWNER TO postgres;





CREATE SEQUENCE public.project_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.project_id_seq
	OWNER TO regovar;
CREATE TABLE public.project
(
	id integer NOT NULL DEFAULT nextval('project_id_seq'::regclass),
	name character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	comments text COLLATE pg_catalog."C.UTF-8",
	parent_id integer,
	data text COLLATE pg_catalog."C.UTF-8",
	CONSTRAINT project_pkey PRIMARY KEY (id)
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.project
	OWNER TO postgres;





CREATE SEQUENCE public.template_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.template_id_seq
	OWNER TO regovar;
CREATE TABLE public.template
(
	id integer NOT NULL DEFAULT nextval('template_id_seq'::regclass),
	name character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	author_id integer NOT NULL,
	description text COLLATE pg_catalog."C.UTF-8",
	version character varying(20) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	creation_date timestamp without time zone NOT NULL,
	update_date timestamp without time zone,
	parent_id integer,
	configuration text COLLATE pg_catalog."C.UTF-8",
	status tpl_status NOT NULL DEFAULT 'draft'::tpl_status,
	CONSTRAINT template_pkey PRIMARY KEY (id),
	CONSTRAINT template_author_id_fkey FOREIGN KEY (author_id)
		REFERENCES public."user" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT template_author_id_name_version_key UNIQUE (author_id, name, version)
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.template
	OWNER TO regovar;





CREATE SEQUENCE public.analysis_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.analysis_id_seq
	OWNER TO regovar;
CREATE TABLE public.analysis
(
	id integer NOT NULL DEFAULT nextval('analysis_id_seq'::regclass),
	name character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	owner_id integer NOT NULL,
	project_id integer NOT NULL,
	comments text COLLATE pg_catalog."C.UTF-8",
	template_id integer NOT NULL,
	template_settings text COLLATE pg_catalog."C.UTF-8",
	creation_date timestamp without time zone NOT NULL,
	update_date timestamp without time zone NOT NULL,
	is_archived boolean NOT NULL DEFAULT false,
	status analysis_status NOT NULL DEFAULT 'created'::analysis_status,
	CONSTRAINT analysis_pkey PRIMARY KEY (id),
	CONSTRAINT analysis_project_id_fkey FOREIGN KEY (project_id)
		REFERENCES public."project" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT analysis_template_id_fkey FOREIGN KEY (template_id)
		REFERENCES public."template" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT analysis_project_id_name_key UNIQUE (project_id, name),
	CONSTRAINT analysis_owner_id_fkey FOREIGN KEY (owner_id)
		REFERENCES public."user" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.analysis
	OWNER TO regovar;



CREATE SEQUENCE public.selection_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.selection_id_seq
	OWNER TO regovar;
CREATE TABLE public.selection
(
	id integer NOT NULL DEFAULT nextval('selection_id_seq'::regclass),
	analysis_id integer NOT NULL,
	name character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	comments text COLLATE pg_catalog."C.UTF-8",
	"order" integer,
	query text COLLATE pg_catalog."C.UTF-8",
	CONSTRAINT selection_pkey PRIMARY KEY (id),
	CONSTRAINT selection_analysis_id_fkey FOREIGN KEY (analysis_id)
		REFERENCES public."analysis" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.selection
	OWNER TO regovar;









CREATE SEQUENCE public.subject_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.subject_id_seq
	OWNER TO regovar;
CREATE TABLE public.subject
(
	id integer NOT NULL DEFAULT nextval('subject_id_seq'::regclass),
	name character varying(255) COLLATE pg_catalog."C.UTF-8",
	contact character varying(255) COLLATE pg_catalog."C.UTF-8",
	comments text COLLATE pg_catalog."C.UTF-8",
	CONSTRAINT subject_pkey PRIMARY KEY (id)
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.subject
	OWNER TO regovar;




CREATE TABLE public.subject_relation
(
	subject1_id integer NOT NULL,
	subject2_id integer NOT NULL,
	relation subject_relation_type NOT NULL DEFAULT 'parent'::subject_relation_type,
	CONSTRAINT subject_relation_pkey PRIMARY KEY (subject1_id, subject2_id, relation),
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.subject_relation
	OWNER TO regovar;





CREATE TABLE public.subject_patient
(
	subject_id integer NOT NULL,
	firstname character varying(255) COLLATE pg_catalog."C.UTF-8",
	lastname character varying(255) COLLATE pg_catalog."C.UTF-8",
	birthdate timestamp without time zone,
	deathdate timestamp without time zone,
	contact character varying(255) COLLATE pg_catalog."C.UTF-8",
	CONSTRAINT subject_patient_pkey PRIMARY KEY (subject_id),
	CONSTRAINT subject_patient_id_fkey FOREIGN KEY (subject_id)
		REFERENCES public."subject" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.subject_patient
	OWNER TO regovar;




CREATE SEQUENCE public.reference_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.reference_id_seq
	OWNER TO regovar;
CREATE TABLE public.reference
(
	id integer NOT NULL DEFAULT nextval('reference_id_seq'::regclass),
	name character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	description character varying(255) COLLATE pg_catalog."C.UTF-8",
	url character varying(255) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	table_suffix character varying(10) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	CONSTRAINT reference_pkey PRIMARY KEY (id)
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.reference
	OWNER TO regovar;




CREATE SEQUENCE public.file_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.file_id_seq
	OWNER TO regovar;
CREATE TABLE public.file
(
	id integer NOT NULL DEFAULT nextval('file_id_seq'::regclass),
	filename character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	description character varying(255) COLLATE pg_catalog."C.UTF-8",
	type character varying(10) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	reference_id integer NOT NULL,
	CONSTRAINT file_pkey PRIMARY KEY (id),
	CONSTRAINT file_reference_id_fkey FOREIGN KEY (reference_id)
		REFERENCES public."reference" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.file
	OWNER TO regovar;








CREATE SEQUENCE public.sample_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.sample_id_seq
	OWNER TO regovar;
CREATE TABLE public.sample
(
	id integer NOT NULL DEFAULT nextval('sample_id_seq'::regclass),
	name character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	description character varying(255) COLLATE pg_catalog."C.UTF-8",
	subject_id integer NOT NULL,
	CONSTRAINT sample_pkey PRIMARY KEY (id),
	CONSTRAINT sample_subject_id_fkey FOREIGN KEY (subject_id)
		REFERENCES public."subject" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT sample_file_id_fkey FOREIGN KEY (file_id)
		REFERENCES public."file" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.sample
	OWNER TO regovar;



CREATE TABLE public.sample_file
(
	sample_id integer NOT NULL,
	file_id integer NOT NULL,
	CONSTRAINT sample_file_pkey PRIMARY KEY (sample_id, file_id),
	CONSTRAINT sample_file_sample_id_fkey FOREIGN KEY (sample_id)
		REFERENCES public."sample" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT sample_file_file_id_fkey FOREIGN KEY (file_id)
		REFERENCES public."file" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.sample_file
	OWNER TO regovar;



CREATE TABLE public.project_sample
(
	project_id integer NOT NULL,
	sample_id integer NOT NULL,
	CONSTRAINT project_sample_pkey PRIMARY KEY (project_id, sample_id),
	CONSTRAINT project_sample_project_id_fkey FOREIGN KEY (project_id)
		REFERENCES public."project" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT project_sample_sample_id_fkey FOREIGN KEY (sample_id)
		REFERENCES public."sample" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.project_sample
	OWNER TO regovar;







CREATE SEQUENCE public.variant_hg19_id_seq
	INCREMENT 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1;
ALTER TABLE public.variant_hg19_id_seq
	OWNER TO regovar;
CREATE TABLE public.variant_hg19
(
	id integer NOT NULL DEFAULT nextval('variant_hg19_id_seq'::regclass),
	bin integer,
	chr character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	pos integer NOT NULL,
	ref text NOT NULL,
	alt text NOT NULL,
	sample_list integer[],
	caller_list character varying(50)[] COLLATE pg_catalog."C.UTF-8",
	refgen_name2 character varying(50) COLLATE pg_catalog."C.UTF-8",
	refgen_transcript character varying(50)[] COLLATE pg_catalog."C.UTF-8",
	CONSTRAINT variant_hg19_pkey PRIMARY KEY (id),
	CONSTRAINT variant_hg19_ukey UNIQUE (chr, pos, ref, alt)
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.variant_hg19
	OWNER TO regovar;









CREATE TABLE public.regmut_hg19
(
	bin integer,
	chr character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	pos integer NOT NULL,
	ref text NOT NULL,
	alt text NOT NULL,
	variant_id integer,
	subject_list integer[],
	phenotype character varying(255) COLLATE pg_catalog."C.UTF-8",
	inheritance character varying(255) COLLATE pg_catalog."C.UTF-8",
	pathogenicity regmut_pathos,
	contribution regmut_contrib,
	sex character varying(50) COLLATE pg_catalog."C.UTF-8",
	CONSTRAINT regmut_hg19_pkey PRIMARY KEY (chr, pos, ref, alt)
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.regmut_hg19
	OWNER TO regovar;





CREATE TABLE public.sample_variant_hg19
(
	sample_id integer NOT NULL,
	bin integer,
	chr character varying(50) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	pos integer NOT NULL,
	ref text NOT NULL,
	alt text NOT NULL,
	variant_id integer,
	genotype character varying(1),
	info character varying(255)[][] COLLATE pg_catalog."C.UTF-8",
	CONSTRAINT sample_variant_hg19_pkey PRIMARY KEY (sample_id, chr, pos, ref, alt),
	CONSTRAINT sample_variant_hg19_variant_id_fkey FOREIGN KEY (variant_id)
		REFERENCES public."variant" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT sample_variant_hg19_sample_id_fkey FOREIGN KEY (sample_id)
		REFERENCES public."sample" (id) MATCH SIMPLE
		ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public.variant_hg19
	OWNER TO regovar;





CREATE TABLE public."parameter"
(
	key character varying(255) COLLATE pg_catalog."C.UTF-8" NOT NULL ,
	value character varying(255) COLLATE pg_catalog."C.UTF-8" NOT NULL,
	description character varying(255) COLLATE pg_catalog."C.UTF-8",
	CONSTRAINT parameter_pkey PRIMARY KEY (key)
)
WITH (
	OIDS=FALSE
);
ALTER TABLE public."parameter"
	OWNER TO postgres;


--
-- INIT DATA
--
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";



INSERT INTO public.reference (name, description, url, table_suffix) VALUES
	("Human Genom 19", "Human Genom version 19", "", "hg19");



INSERT INTO public."parameter" (key, description, value) VALUES
	("DatabaseVersion",        "The current version of the database",                                      "V1.0.0"),
	("HeavyClientLastVersion", "Last complient version of the heavy client",                               "V1.0.0"),
	("HeavyClient",            "Information for the Launcher to be able to download/update the client",    "{}"),
	("LastBackupDate",         "The date of the last database dump",                                       to_char(current_timestamp, 'YYYY-MM-DD')),
	("RegovarDatabaseUUID",    "Unique ID of the Regovar database", "The current version of the database", uuid_generate_v4());





