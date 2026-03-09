-- Table: public.vault_inventory_state

-- DROP TABLE IF EXISTS public.vault_inventory_state;

CREATE TABLE IF NOT EXISTS public.vault_inventory_state
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_inventory_state_Id_seq"'::regclass),
    "InventoryId" integer NOT NULL,
    "Key" character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "Value" text COLLATE pg_catalog."default" NOT NULL,
    "UpdatedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chodecoin_inventory_state_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "chodecoin_inventory_state_InventoryId_Key_key" UNIQUE ("InventoryId", "Key"),
    CONSTRAINT "chodecoin_inventory_state_InventoryId_fkey" FOREIGN KEY ("InventoryId")
        REFERENCES public.vault_inventory ("Id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_inventory_state
    OWNER to redbot;
-- Index: idx_vault_inv_state_inv

-- DROP INDEX IF EXISTS public.idx_vault_inv_state_inv;

CREATE INDEX IF NOT EXISTS idx_vault_inv_state_inv
    ON public.vault_inventory_state USING btree
    ("InventoryId" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;