-- Table: public.type-effectiveness

-- DROP TABLE IF EXISTS public."type-effectiveness";

CREATE TABLE IF NOT EXISTS public."type-effectiveness"
(
    source character varying(10) COLLATE pg_catalog."default" DEFAULT 1,
    normal double precision DEFAULT 1,
    fighting double precision DEFAULT 1,
    flying double precision DEFAULT 1,
    poison double precision DEFAULT 1,
    ground double precision DEFAULT 1,
    rock double precision DEFAULT 1,
    bug double precision DEFAULT 1,
    ghost double precision DEFAULT 1,
    fire double precision DEFAULT 1,
    water double precision DEFAULT 1,
    grass double precision DEFAULT 1,
    electric double precision DEFAULT 1,
    psychic double precision DEFAULT 1,
    ice double precision DEFAULT 1,
    dragon double precision DEFAULT 1
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public."type-effectiveness"
    OWNER to redbot;