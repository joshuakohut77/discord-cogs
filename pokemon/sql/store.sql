-- Table: public.store

-- DROP TABLE IF EXISTS public.store;

CREATE TABLE IF NOT EXISTS public.store
(
    item character varying COLLATE pg_catalog."default",
    price integer,
    "areaId" integer
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.store
    OWNER to redbot;