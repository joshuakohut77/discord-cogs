-- Table: public.vault_property_defs

-- DROP TABLE IF EXISTS public.vault_property_defs;

CREATE TABLE IF NOT EXISTS public.vault_property_defs
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_property_defs_Id_seq"'::regclass),
    "Key" character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "DataType" character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT 'string'::character varying,
    "AppliesTo" character varying(255) COLLATE pg_catalog."default",
    "Description" text COLLATE pg_catalog."default" NOT NULL,
    "Example" character varying(255) COLLATE pg_catalog."default",
    "CreatedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chodecoin_property_defs_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "chodecoin_property_defs_Key_key" UNIQUE ("Key")
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_property_defs
    OWNER to redbot;