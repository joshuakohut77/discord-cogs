-- Table: public.vault_campaigns

-- DROP TABLE IF EXISTS public.vault_campaigns;

CREATE TABLE IF NOT EXISTS public.vault_campaigns
(
    "Id" integer NOT NULL DEFAULT nextval('"vault_campaigns_Id_seq"'::regclass),
    "GuildId" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    "ChannelId" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    "Status" character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT 'setup'::character varying,
    "TurnOrder" text COLLATE pg_catalog."default" NOT NULL DEFAULT '[]'::text,
    "CurrentTurnIndex" integer NOT NULL DEFAULT 0,
    "CurrentRound" integer NOT NULL DEFAULT 1,
    "LastMessageId" character varying(255) COLLATE pg_catalog."default",
    "LastInventoryMessageId" character varying(255) COLLATE pg_catalog."default",
    "CreatedAt" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    "EndedAt" timestamp without time zone,
    CONSTRAINT vault_campaigns_pkey PRIMARY KEY ("Id")
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vault_campaigns
    OWNER to redbot;
-- Index: idx_vault_campaigns_active_guild

-- DROP INDEX IF EXISTS public.idx_vault_campaigns_active_guild;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vault_campaigns_active_guild
    ON public.vault_campaigns USING btree
    ("GuildId" COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default
    WHERE "Status"::text = ANY (ARRAY['setup'::character varying, 'active'::character varying, 'paused'::character varying]::text[]);
-- Index: idx_vault_campaigns_guild

-- DROP INDEX IF EXISTS public.idx_vault_campaigns_guild;

CREATE INDEX IF NOT EXISTS idx_vault_campaigns_guild
    ON public.vault_campaigns USING btree
    ("GuildId" COLLATE pg_catalog."default" ASC NULLS LAST, "Status" COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;