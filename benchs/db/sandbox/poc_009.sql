-- 
-- TEST join avec comparaison "simple" txstart/txend
--

SELECT sv.variant_id 
FROM _8_sample_variant sv 
WHERE sv.sample_id=1
--=> 209 089 lignes en 5.3s


SELECT v.chr, v.pos 
FROM _8_sample_variant sv 
INNER JOIN _8_variant v ON v.id = sv.variant_id
WHERE sv.sample_id=1
--=> 209 089 lignes en 6.5s


SELECT v.chr, v.pos, rg.name
FROM _8_sample_variant sv 
INNER JOIN _8_variant v ON v.id = sv.variant_id
INNER JOIN refgene rg ON v.chr = rg.chrom AND v.pos >= rg.txstart AND v.pos <= rg.txend
WHERE sv.sample_id=1
--=> 258 608 lignes en 1min 7s
--=> index simple sur (chrom, txstart, txend)




-- 
-- TEST join avec comparaison utilisation des ranges
--

SELECT v.chr, v.pos, rg.name
FROM _8_sample_variant sv 
INNER JOIN _8_variant v ON v.id = sv.variant_id
INNER JOIN refgene rg ON v.chr = rg.chrom AND rg.txrange @> int8(v.pos)
WHERE sv.sample_id=1
--=> 258 605 lignes en 20.2s



--
-- CREATE poc_009 db
--

CREATE SEQUENCE public._9_variant_id_seq
  INCREMENT 1
  MINVALUE 1
  MAXVALUE 9223372036854775807
  START 1
  CACHE 1;
ALTER TABLE public._9_variant_id_seq
  OWNER TO regovar;
CREATE TABLE public._9_variant
(
  id integer NOT NULL DEFAULT nextval('_9_variant_id_seq'::regclass),
  bin integer,
  chr character varying NOT NULL,
  pos integer NOT NULL,
  ref character varying NOT NULL,
  alt character varying NOT NULL,
  is_transition boolean,
  refgene_ids integer[][],
  CONSTRAINT _9_variant_pkey PRIMARY KEY (id),
  CONSTRAINT _9_variant_uc UNIQUE (chr, pos, ref, alt)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public._9_variant
  OWNER TO regovar;

CREATE UNIQUE INDEX _9_variant_idx
  ON public._9_variant
  USING btree
  (chr COLLATE pg_catalog."default", pos, ref COLLATE pg_catalog."default", alt COLLATE pg_catalog."default");


CREATE SEQUENCE public.refgene_id_seq
  INCREMENT 1
  MINVALUE 1
  MAXVALUE 9223372036854775807
  START 1
  CACHE 1;
ALTER TABLE public.refgene_id_seq
  OWNER TO regovar;

ALTER TABLE refGene ADD id integer NOT NULL DEFAULT nextval('refgene_id_seq'::regclass)
ALTER TABLE refGene ADD variant_ids integer[][]



--
-- Populate poc_009 db
--

INSERT INTO _9_variant (bin, chr, pos, ref, alt, is_transition, refgene_ids)
SELECT v.bin, v.chr, v.pos, v.ref, v.alt, v.is_transition, array_agg(rg.id)
FROM _8_variant v
LEFT JOIN refgene rg ON rg.txrange @> int8(v.pos)
GROUP BY v.id


SELECT v.id, v.chr, v.pos
FROM _9_variant v
--=> 11s



UPDATE refgene SET variant_ids=array_agg(v.id)
FROM _8_variant v
LEFT JOIN refgene rg ON rg.txrange @> int8(v.pos)
GROUP BY v.id



SELECT v.chr, v.pos, rg.name
FROM _8_sample_variant sv 
INNER JOIN _9_variant v ON v.id = sv.variant_id
INNER JOIN refgene rg ON rg.id IN v.refgene_ids
WHERE sv.sample_id=1
--=> 258 605 lignes en 20.2s





SELECT v.id, v.chr, v.pos, rg.name
FROM _9_variant v
INNER JOIN refgene rg ON rg.id = ANY(v.refgene_ids)
WHERE v.id=1763588
-- ~41 ~51 ms

SELECT v.id, v.chr, v.pos, array_agg(rg.name)
FROM _9_variant v
INNER JOIN refgene rg ON rg.id = ANY(v.refgene_ids)
WHERE v.id=1763588
GROUP BY v.id
-- ~41 ~51 ms




SELECT v.id, v.chr, v.pos, rg.name
FROM _9_variant v
INNER JOIN refgene rg ON rg.txrange @> int8(v.pos)
WHERE v.id=1763588
-- ~12 ~13 ms

SELECT v.id, v.chr, v.pos, array_agg(rg.name)
FROM _9_variant v
INNER JOIN refgene rg ON rg.txrange @> int8(v.pos)
WHERE v.id>=1763588
GROUP BY v.id
-- ~12 ~13 ms


-- Join via array
SELECT v.id, v.chr, v.pos, array_agg(rg.name)
FROM _9_variant v
INNER JOIN refgene rg ON rg.id = ANY(v.refgene_ids)
WHERE v.id>=1763588 AND v.id <=1764588
GROUP BY v.id
-- 31.7 s

-- "normal" join
SELECT v.id, v.chr, v.pos, array_agg(rg.name)
FROM _9_variant v
INNER JOIN refgene rg ON rg.txrange @> int8(v.pos)
WHERE v.id>=1763588 AND v.id <=1764588
GROUP BY v.id
-- ~417 ms

-- No join
SELECT v.id, v.chr, v.pos
FROM _9_variant v
WHERE v.id>=1763588 AND v.id <=1764588
-- ~55 ms

-- => en fait les join sont 5 à 8 fois plus optimisé que les arrays... :/ même quand ont travaille sur un petit volume. ça doit venir de la meilleure gestion des index au niveau des tables