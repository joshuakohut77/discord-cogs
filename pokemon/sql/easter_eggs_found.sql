-- Table: public.easter_eggs_found

-- DROP TABLE IF EXISTS public.easter_eggs_found;

CREATE TABLE IF NOT EXISTS public.easter_eggs_found
(
    id integer NOT NULL DEFAULT nextval('easter_eggs_found_id_seq'::regclass),
    guild_id character varying COLLATE pg_catalog."default" NOT NULL,
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    egg_id character varying COLLATE pg_catalog."default" NOT NULL,
    found_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT easter_eggs_found_pkey PRIMARY KEY (id),
    CONSTRAINT easter_eggs_unique UNIQUE (guild_id, discord_id, egg_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.easter_eggs_found
    OWNER to redbot;
-- Index: idx_easter_eggs_guild_user

-- DROP INDEX IF EXISTS public.idx_easter_eggs_guild_user;

CREATE INDEX IF NOT EXISTS idx_easter_eggs_guild_user
    ON public.easter_eggs_found USING btree
    (guild_id COLLATE pg_catalog."default" ASC NULLS LAST, discord_id COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;