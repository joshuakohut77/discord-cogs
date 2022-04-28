-- Table: public.trainer

-- DROP TABLE IF EXISTS public.trainer;

CREATE TABLE IF NOT EXISTS public.trainer
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    "starterId" integer,
    "activePokemon" integer,
    "areaId" integer DEFAULT 1,
    "locationId" integer DEFAULT 1,
    CONSTRAINT trainer_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trainer
    OWNER to redbot;