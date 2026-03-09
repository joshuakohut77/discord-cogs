-- Table: public.vault_campaign_players

-- DROP TABLE IF EXISTS public.vault_campaign_players;

CREATE TABLE IF NOT EXISTS public.vault_campaign_players
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_campaign_players_Id_seq"'::regclass),
    "CampaignId" integer NOT NULL,
    "UserId" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    "DisplayName" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    "QuestionsUsedThisTurn" integer NOT NULL DEFAULT 0,
    "JoinedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT vault_campaign_players_pkey PRIMARY KEY ("Id"),
    CONSTRAINT "vault_campaign_players_CampaignId_UserId_key" UNIQUE ("CampaignId", "UserId"),
    CONSTRAINT "vault_campaign_players_CampaignId_fkey" FOREIGN KEY ("CampaignId")
        REFERENCES public.vault_campaigns ("Id") MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_campaign_players
    OWNER to redbot;
-- Index: idx_vault_campaign_players_campaign

-- DROP INDEX IF EXISTS public.idx_vault_campaign_players_campaign;

CREATE INDEX IF NOT EXISTS idx_vault_campaign_players_campaign
    ON public.vault_campaign_players USING btree
    ("CampaignId" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;