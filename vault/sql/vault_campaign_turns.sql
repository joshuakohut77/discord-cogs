-- Table: public.vault_campaign_turns

-- DROP TABLE IF EXISTS public.vault_campaign_turns;

CREATE TABLE IF NOT EXISTS public.vault_campaign_turns
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_campaign_turns_Id_seq"'::regclass),
    "CampaignId" integer NOT NULL,
    "UserId" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    "TurnNumber" integer NOT NULL,
    "RoundNumber" integer NOT NULL DEFAULT 1,
    "ActionType" character varying(20) COLLATE pg_catalog."default" NOT NULL,
    "CardInvId" integer,
    "CardName" character varying(100) COLLATE pg_catalog."default",
    "ActionText" text COLLATE pg_catalog."default",
    "DmResponse" text COLLATE pg_catalog."default",
    "CardConsumed" boolean NOT NULL DEFAULT false,
    "CreatedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT vault_campaign_turns_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "vault_campaign_turns_CampaignId_fkey" FOREIGN KEY ("CampaignId")
        REFERENCES public.vault_campaigns ("Id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_campaign_turns
    OWNER to redbot;
-- Index: idx_vault_campaign_turns_campaign

-- DROP INDEX IF EXISTS public.idx_vault_campaign_turns_campaign;

CREATE INDEX IF NOT EXISTS idx_vault_campaign_turns_campaign
    ON public.vault_campaign_turns USING btree
    ("CampaignId" ASC NULLS LAST, "TurnNumber" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;