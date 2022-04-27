-- Table: public.pokedex

-- DROP TABLE IF EXISTS public.pokedex;

CREATE TABLE IF NOT EXISTS public.pokedex
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    discord_id character varying COLLATE pg_catalog."default",
    "pokemonId" integer,
    "pokemonName" character varying COLLATE pg_catalog."default",
    "mostRecent" date,
    CONSTRAINT pokedex_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.pokedex
    OWNER to redbot;