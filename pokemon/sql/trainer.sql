-- Table: public.trainer

-- DROP TABLE IF EXISTS public.trainer;

CREATE TABLE IF NOT EXISTS public.trainer
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    "starterId" integer,
    "activePokemon" integer,
    "locationId" integer DEFAULT 86,
    "legacySprites" boolean DEFAULT false,
    startdate date DEFAULT CURRENT_DATE,
    "starterName" character varying COLLATE pg_catalog."default",
    "trainerName" character varying COLLATE pg_catalog."default",
    missingno_step integer DEFAULT 0,
    CONSTRAINT trainer_pkey PRIMARY KEY (discord_id),
    CONSTRAINT "trainer_activePokemon_pokemon_id" FOREIGN KEY ("activePokemon")
        REFERENCES public.pokemon (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT "trainer_starterId_pokemon_id" FOREIGN KEY ("starterId")
        REFERENCES public.pokemon (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trainer
    OWNER to redbot;