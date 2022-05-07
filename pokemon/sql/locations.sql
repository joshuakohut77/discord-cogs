-- Table: public.locations

-- DROP TABLE IF EXISTS public.locations;

CREATE TABLE IF NOT EXISTS public.locations
(
    "locationId" integer NOT NULL,
    name character varying(25) COLLATE pg_catalog."default",
    north character varying(25) COLLATE pg_catalog."default",
    east character varying(25) COLLATE pg_catalog."default",
    south character varying(25) COLLATE pg_catalog."default",
    west character varying(25) COLLATE pg_catalog."default",
    prerequisites character varying COLLATE pg_catalog."default",
    "spritePath" character varying COLLATE pg_catalog."default",
    CONSTRAINT locations_pkey PRIMARY KEY ("locationId")
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.locations
    OWNER to redbot;