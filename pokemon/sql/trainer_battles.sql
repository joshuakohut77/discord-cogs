-- Table: public.trainer_battles

-- DROP TABLE IF EXISTS public.trainer_battles;

CREATE TABLE IF NOT EXISTS public.trainer_battles
(
    id bigint NOT NULL,
    discord_id character varying(20) COLLATE pg_catalog."default" NOT NULL,
    "locationId" integer NOT NULL,
    enemy_uuid character varying(10) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT trainer_battles_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trainer_battles
    OWNER to redbot;