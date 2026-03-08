-- Table: public.vault_store_config

-- DROP TABLE IF EXISTS public.vault_store_config;

CREATE TABLE IF NOT EXISTS public.vault_store_config
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_store_config_Id_seq"'::regclass),
    "GuildId" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    "Category" character varying(50) COLLATE pg_catalog."default" NOT NULL,
    "PullPrice" integer NOT NULL DEFAULT 5,
    "IsOpen" boolean NOT NULL DEFAULT true,
    "UpdatedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT vault_store_config_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "vault_store_config_GuildId_Category_key" UNIQUE ("GuildId", "Category")
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_store_config
    OWNER to redbot;
-- Index: idx_vault_store_cfg

-- DROP INDEX IF EXISTS public.idx_vault_store_cfg;

CREATE INDEX IF NOT EXISTS idx_vault_store_cfg
    ON public.vault_store_config USING btree
    ("GuildId" COLLATE pg_catalog."default" ASC NULLS LAST, "Category" COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;