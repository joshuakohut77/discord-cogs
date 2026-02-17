-- Table: public.first_evolutions

-- DROP TABLE IF EXISTS public.first_evolutions;

CREATE TABLE IF NOT EXISTS public.first_evolutions
(
    guild_id character varying COLLATE pg_catalog."default" NOT NULL,
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    pokemon_name character varying COLLATE pg_catalog."default" NOT NULL,
    evolved_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT first_evolutions_pkey PRIMARY KEY (guild_id, pokemon_name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.first_evolutions
    OWNER to redbot;
-- Index: idx_first_evolutions_guild

-- DROP INDEX IF EXISTS public.idx_first_evolutions_guild;

CREATE INDEX IF NOT EXISTS idx_first_evolutions_guild
    ON public.first_evolutions USING btree
    (guild_id COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;