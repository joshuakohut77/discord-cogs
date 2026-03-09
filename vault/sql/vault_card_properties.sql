-- Table: public.vault_card_properties

-- DROP TABLE IF EXISTS public.vault_card_properties;

CREATE TABLE IF NOT EXISTS public.vault_card_properties
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_card_properties_Id_seq"'::regclass),
    "CardId" integer NOT NULL,
    "Key" character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "Value" text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT chodecoin_card_properties_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "chodecoin_card_properties_CardId_Key_key" UNIQUE ("CardId", "Key"),
    CONSTRAINT "chodecoin_card_properties_CardId_fkey" FOREIGN KEY ("CardId")
        REFERENCES public.vault_cards ("Id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_card_properties
    OWNER to redbot;
-- Index: idx_vault_card_props_card

-- DROP INDEX IF EXISTS public.idx_vault_card_props_card;

CREATE INDEX IF NOT EXISTS idx_vault_card_props_card
    ON public.vault_card_properties USING btree
    ("CardId" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;
-- Index: idx_vault_card_props_key

-- DROP INDEX IF EXISTS public.idx_vault_card_props_key;

CREATE INDEX IF NOT EXISTS idx_vault_card_props_key
    ON public.vault_card_properties USING btree
    ("Key" COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;