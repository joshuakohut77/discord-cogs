-- Table: public.inventory

-- DROP TABLE IF EXISTS public.inventory;

CREATE TABLE IF NOT EXISTS public.inventory
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    potion integer DEFAULT 0,
    "poke-ball" integer DEFAULT 0,
    money integer DEFAULT 0,
    CONSTRAINT inventory_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.inventory
    OWNER to redbot;