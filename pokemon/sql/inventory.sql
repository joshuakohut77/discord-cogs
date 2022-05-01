-- Table: public.inventory

-- DROP TABLE IF EXISTS public.inventory;

CREATE TABLE IF NOT EXISTS public.inventory
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    money integer DEFAULT 0,
    "poke-ball" integer DEFAULT 0,
    "great-ball" integer DEFAULT 0,
    "ultra-ball" integer DEFAULT 0,
    "master-ball" integer DEFAULT 0,
    potion integer DEFAULT 0,
    "super-potion" integer DEFAULT 0,
    "hyper-potion" integer DEFAULT 0,
    "max-potion" integer DEFAULT 0,
    revive integer DEFAULT 0,
    "full-restore" integer DEFAULT 0,
    repel integer DEFAULT 0,
    "max-repel" integer DEFAULT 0,
    awakening integer DEFAULT 0,
    "escape-rope" integer DEFAULT 0,
    "full-heal" integer DEFAULT 0,
    "ice-heal" integer DEFAULT 0,
    "burn-heal" integer DEFAULT 0,
    "paralyze-heal" integer DEFAULT 0,
    antidote integer DEFAULT 0,
    CONSTRAINT inventory_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.inventory
    OWNER to redbot;