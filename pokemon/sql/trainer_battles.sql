-- Table: public.trainer_battles

-- DROP TABLE IF EXISTS public.trainer_battles;

CREATE TABLE IF NOT EXISTS public.trainer_battles
(
    discord_id character varying(20) COLLATE pg_catalog."default" NOT NULL,
    "locationId" integer,
    enemy_uuid character varying COLLATE pg_catalog."default",
    CONSTRAINT trainer_battles_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trainer_battles
    OWNER to redbot;