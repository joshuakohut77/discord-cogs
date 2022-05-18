-- Table: public.itempricing

-- DROP TABLE IF EXISTS public.itempricing;

CREATE TABLE IF NOT EXISTS public.itempricing
(
    item character varying(20) COLLATE pg_catalog."default" NOT NULL,
    price integer,
    CONSTRAINT itempricing_pkey PRIMARY KEY (item)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.itempricing
    OWNER to redbot;