-- Table: public.vault_inventory

-- DROP TABLE IF EXISTS public.vault_inventory;

CREATE TABLE IF NOT EXISTS public.vault_inventory
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_inventory_Id_seq"'::regclass),
    "GuildId" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    "UserId" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    "CardId" integer NOT NULL,
    "AcquiredVia" character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT 'store'::character varying,
    "IsActive" boolean NOT NULL DEFAULT true,
    "IsEquipped" boolean NOT NULL DEFAULT false,
    "AcquiredAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    "RetiredAt" timestamp without time zone,
    CONSTRAINT chodecoin_inventory_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "chodecoin_inventory_CardId_fkey" FOREIGN KEY ("CardId")
        REFERENCES public.vault_cards ("Id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_inventory
    OWNER to redbot;
-- Index: idx_vault_inv_active

-- DROP INDEX IF EXISTS public.idx_vault_inv_active;

CREATE INDEX IF NOT EXISTS idx_vault_inv_active
    ON public.vault_inventory USING btree
    ("GuildId" COLLATE pg_catalog."default" ASC NULLS LAST, "UserId" COLLATE pg_catalog."default" ASC NULLS LAST, "IsActive" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;
-- Index: idx_vault_inv_card

-- DROP INDEX IF EXISTS public.idx_vault_inv_card;

CREATE INDEX IF NOT EXISTS idx_vault_inv_card
    ON public.vault_inventory USING btree
    ("CardId" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;
-- Index: idx_vault_inv_guild_user

-- DROP INDEX IF EXISTS public.idx_vault_inv_guild_user;

CREATE INDEX IF NOT EXISTS idx_vault_inv_guild_user
    ON public.vault_inventory USING btree
    ("GuildId" COLLATE pg_catalog."default" ASC NULLS LAST, "UserId" COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;