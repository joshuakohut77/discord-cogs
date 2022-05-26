-- Table: public.trainer_battles

-- DROP TABLE IF EXISTS public.trainer_battles;

CREATE TABLE IF NOT EXISTS public.trainer_battles
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    discord_id character varying(20) COLLATE pg_catalog."default" NOT NULL,
    "locationId" integer NOT NULL,
    enemy_uuid character varying(10) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT trainer_battles_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trainer_battles
    OWNER to redbot;