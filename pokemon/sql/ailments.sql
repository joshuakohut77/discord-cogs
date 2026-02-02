-- Table: public.ailments

-- DROP TABLE IF EXISTS public.ailments;

CREATE TABLE IF NOT EXISTS public.ailments
(
    "pokemonId" integer NOT NULL,
    "mostRecent" date,
    sleep boolean,
    poison boolean,
    burn boolean,
    "freeze" boolean,
    paralysis boolean,
    trap boolean,
    confusion boolean,
    disable boolean,
    CONSTRAINT ailments_pkey PRIMARY KEY ("pokemonId")
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.ailments
    OWNER to redbot;