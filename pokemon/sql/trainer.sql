-- Table: public.trainer

-- DROP TABLE IF EXISTS public.trainer;

CREATE TABLE IF NOT EXISTS public.trainer
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    "starterId" integer,
    "activePokemon" integer,
    "areaId" integer DEFAULT 285,
    "locationId" integer DEFAULT 86,
    CONSTRAINT trainer_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trainer
    OWNER to redbot;



ALTER TABLE
  "public"."trainer"
ADD
  CONSTRAINT "trainer_starterId_pokemon_id" FOREIGN KEY ("starterId") REFERENCES "public"."pokemon" ("id") ON
UPDATE
  NO ACTION ON DELETE NO ACTION;


ALTER TABLE
  "public"."trainer"
ADD
  CONSTRAINT "trainer_activePokemon_pokemon_id" FOREIGN KEY ("activePokemon") REFERENCES "public"."pokemon" ("id") ON
UPDATE
  NO ACTION ON DELETE NO ACTION