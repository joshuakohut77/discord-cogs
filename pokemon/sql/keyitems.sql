-- Table: public.keyitems

-- DROP TABLE IF EXISTS public.keyitems;

CREATE TABLE IF NOT EXISTS public.keyitems
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    "HM01" boolean DEFAULT false,
    "HM02" boolean DEFAULT false,
    "HM03" boolean DEFAULT false,
    "HM04" boolean DEFAULT false,
    "HM05" boolean DEFAULT false,
    badge_boulder boolean DEFAULT false,
    badge_cascade boolean DEFAULT false,
    badge_thunder boolean DEFAULT false,
    badge_rainbow boolean DEFAULT false,
    badge_soul boolean DEFAULT false,
    badge_marsh boolean DEFAULT false,
    badge_volcano boolean DEFAULT false,
    badge_earth boolean DEFAULT false,
    pokeflute boolean DEFAULT false,
    silph_scope boolean DEFAULT false,
    oaks_parcel boolean DEFAULT false,
    ss_ticket boolean DEFAULT false,
    bicycle boolean DEFAULT false,
    old_rod boolean DEFAULT false,
    good_rod boolean DEFAULT false,
    super_rod boolean DEFAULT false,
    item_finder boolean DEFAULT false,
    CONSTRAINT keyitems_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.keyitems
    OWNER to redbot;