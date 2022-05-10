-- Table: public.keyitems

-- DROP TABLE IF EXISTS public.keyitems;

CREATE TABLE IF NOT EXISTS public.keyitems
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    "HM01" boolean,
    "HM02" boolean,
    "HM03" boolean,
    "HM04" boolean,
    "HM05" boolean,
    badge_boulder boolean,
    badge_cascade boolean,
    badge_thunder boolean,
    badge_rainbow boolean,
    badge_soul boolean,
    badge_marsh boolean,
    badge_volcano boolean,
    badge_earth boolean,
    pokeflute boolean,
    silph_scope boolean,
    oaks_parcel boolean,
    ss_ticket boolean,
    bicycle boolean,
    "old-rod" boolean,
    "good-rod" boolean,
    "super-rod" boolean,
    item_finder boolean,
    CONSTRAINT keyitems_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.keyitems
    OWNER to redbot;