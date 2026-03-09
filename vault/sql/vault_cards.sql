-- Table: public.vault_cards

-- DROP TABLE IF EXISTS public.vault_cards;

CREATE TABLE IF NOT EXISTS public.vault_cards
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_cards_Id_seq"'::regclass),
    "Name" character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "Category" character varying(50) COLLATE pg_catalog."default" NOT NULL,
    "Rarity" character varying(20) COLLATE pg_catalog."default" NOT NULL,
    "Explanation" text COLLATE pg_catalog."default" NOT NULL,
    "Blurb" text COLLATE pg_catalog."default" NOT NULL,
    "ArtFile" character varying(255) COLLATE pg_catalog."default",
    "RenderedFile" character varying(255) COLLATE pg_catalog."default",
    "IsInStore" boolean NOT NULL DEFAULT true,
    "IsActive" boolean NOT NULL DEFAULT true,
    "CreatedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    "UpdatedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chodecoin_cards_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "chodecoin_cards_Name_Category_key" UNIQUE ("Name", "Category")
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_cards
    OWNER to redbot;
-- Index: idx_vault_cards_category

-- DROP INDEX IF EXISTS public.idx_vault_cards_category;

CREATE INDEX IF NOT EXISTS idx_vault_cards_category
    ON public.vault_cards USING btree
    ("Category" COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;
-- Index: idx_vault_cards_rarity

-- DROP INDEX IF EXISTS public.idx_vault_cards_rarity;

CREATE INDEX IF NOT EXISTS idx_vault_cards_rarity
    ON public.vault_cards USING btree
    ("Rarity" COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;
-- Index: idx_vault_cards_store

-- DROP INDEX IF EXISTS public.idx_vault_cards_store;

CREATE INDEX IF NOT EXISTS idx_vault_cards_store
    ON public.vault_cards USING btree
    ("IsInStore" ASC NULLS LAST, "IsActive" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;