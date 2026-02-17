-- Table: public.pokemon

-- DROP TABLE IF EXISTS public.pokemon;

CREATE TABLE IF NOT EXISTS public.pokemon
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    "pokemonId" integer,
    "pokemonName" character varying COLLATE pg_catalog."default",
    type_1 character varying COLLATE pg_catalog."default",
    type_2 character varying COLLATE pg_catalog."default",
    "nickName" character varying COLLATE pg_catalog."default",
    "growthRate" character varying COLLATE pg_catalog."default",
    "currentLevel" integer,
    "currentExp" integer,
    base_hp integer,
    base_attack integer,
    base_defense integer,
    base_speed integer,
    base_special_attack integer,
    base_special_defense integer,
    "IV_hp" integer,
    "IV_attack" integer,
    "IV_defense" integer,
    "IV_speed" integer,
    "IV_special_attack" integer,
    "IV_special_defense" integer,
    "EV_hp" integer,
    "EV_attack" integer,
    "EV_defense" integer,
    "EV_speed" integer,
    "EV_special_attack" integer,
    "EV_special_defense" integer,
    move_1 character varying COLLATE pg_catalog."default",
    move_2 character varying COLLATE pg_catalog."default",
    move_3 character varying COLLATE pg_catalog."default",
    move_4 character varying COLLATE pg_catalog."default",
    traded boolean,
    "currentHP" integer,
    party boolean DEFAULT false,
    is_shiny boolean DEFAULT false,
    is_deleted boolean DEFAULT false,
    CONSTRAINT pokemon_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.pokemon
    OWNER to redbot;