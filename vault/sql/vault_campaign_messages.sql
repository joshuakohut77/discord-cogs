-- Table: public.vault_campaign_messages

-- DROP TABLE IF EXISTS public.vault_campaign_messages;

CREATE TABLE IF NOT EXISTS public.vault_campaign_messages
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_campaign_messages_Id_seq"'::regclass),
    "CampaignId" integer NOT NULL,
    "Role" character varying(20) COLLATE pg_catalog."default" NOT NULL,
    "Content" text COLLATE pg_catalog."default" NOT NULL,
    "TurnNumber" integer,
    "MessageType" character varying(30) COLLATE pg_catalog."default" NOT NULL DEFAULT 'turn'::character varying,
    "CreatedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT vault_campaign_messages_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "vault_campaign_messages_CampaignId_fkey" FOREIGN KEY ("CampaignId")
        REFERENCES public.vault_campaigns ("Id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_campaign_messages
    OWNER to redbot;
-- Index: idx_vault_campaign_messages_chain

-- DROP INDEX IF EXISTS public.idx_vault_campaign_messages_chain;

CREATE INDEX IF NOT EXISTS idx_vault_campaign_messages_chain
    ON public.vault_campaign_messages USING btree
    ("CampaignId" ASC NULLS LAST, "Id" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;