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
    calcium integer DEFAULT 0,
    carbos integer DEFAULT 0,
    "coin-case" integer DEFAULT 0,
    "dire-hit" integer DEFAULT 0,
    "dome-fossil" integer DEFAULT 0,
    "fresh-water" integer DEFAULT 0,
    "helix-fossil" integer DEFAULT 0,
    "hp-up" integer DEFAULT 0,
    lemonade integer DEFAULT 0,
    elixir integer DEFAULT 0,
    "max-elixir" integer DEFAULT 0,
    "max-ether" integer DEFAULT 0,
    ether integer DEFAULT 0,
    nugget integer DEFAULT 0,
    "old-amber" integer DEFAULT 0,
    "poke-doll" integer DEFAULT 0,
    "pp-up" integer DEFAULT 0,
    "soda-pop" integer DEFAULT 0,
    "town-map" integer DEFAULT 0,
    "x-accuracy" integer DEFAULT 0,
    "x-defense" integer DEFAULT 0,
    "x-sp-atk" integer DEFAULT 0,
    "x-speed" integer DEFAULT 0,
    "super-repel" integer DEFAULT 0,
    "fire-stone" integer DEFAULT 0,
    "water-stone" integer DEFAULT 0,
    "thunder-stone" integer DEFAULT 0,
    "leaf-stone" integer DEFAULT 0,
    "moon-stone" integer DEFAULT 0,
    "x-attack" integer DEFAULT 0,
    "x-sp-def" integer DEFAULT 0,
    "link-cable" integer DEFAULT 0,
    "game-shark" integer DEFAULT 0,
    iron integer DEFAULT 0,
    protein integer DEFAULT 0,
    CONSTRAINT inventory_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.inventory
    OWNER to redbot;