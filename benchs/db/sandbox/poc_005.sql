DROP SCHEMA IF EXISTS regovar cascade;
CREATE SCHEMA regovar;


CREATE TABLE regovar.files
(
    id		serial primary key,
    path	text not null
);

CREATE TABLE regovar.samples
(
    id			serial primary key,
    name		varchar(20) not null,
    description	varchar(255),
    file_id		int references regovar.files(id)
);

CREATE TABLE regovar.variants
(
    id			serial primary key,
    bin			bigint CHECK (pos >= 0),
    chr			varchar(20) not null,
    pos			bigint not null CHECK (pos >= 0),
    ref 		text,
    alt			text,
    UNIQUE(chr,pos,ref,alt)
);

CREATE TABLE regovar.sample_has_variants
(
    id			serial primary key,
   	sample_id 	int references regovar.samples(id),
   	variant_id  int references regovar.variants(id),
   	genotype 	int,
   	infos  		text[][]	     

);

