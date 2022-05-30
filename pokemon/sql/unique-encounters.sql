-- Table: public.unique-encounters

-- DROP TABLE IF EXISTS public."unique-encounters";

CREATE TABLE IF NOT EXISTS public."unique-encounters"
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    articuno boolean DEFAULT false,
    zapdos boolean DEFAULT false,
    moltres boolean DEFAULT false,
    mewtwo boolean DEFAULT false,
    magikarp boolean DEFAULT false,
    charmander boolean DEFAULT true,
    squirtle boolean DEFAULT true,
    bulbasaur boolean DEFAULT true,
    lapras boolean DEFAULT false,
    hitmonchan boolean DEFAULT false,
    hitmonlee boolean DEFAULT false,
    eevee boolean DEFAULT false,
    snorlax boolean DEFAULT false,
    CONSTRAINT "unique-encounters_pkey" PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public."unique-encounters"
    OWNER to redbot;