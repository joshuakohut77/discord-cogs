-- Table: public.store

-- DROP TABLE IF EXISTS public.store;

CREATE TABLE IF NOT EXISTS public.store
(
    id integer NOT NULL,
    item character varying COLLATE pg_catalog."default",
    price integer,
    "areaId" integer,
    CONSTRAINT store_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.store
    OWNER to redbot;