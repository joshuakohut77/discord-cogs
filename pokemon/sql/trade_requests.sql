-- Table: public.trade_requests

-- DROP TABLE IF EXISTS public.trade_requests;

CREATE TABLE IF NOT EXISTS public.trade_requests
(
    trade_id integer NOT NULL DEFAULT nextval('trade_requests_trade_id_seq'::regclass),
    sender_discord_id character varying(20) COLLATE pg_catalog."default" NOT NULL,
    receiver_discord_id character varying(20) COLLATE pg_catalog."default" NOT NULL,
    sender_pokemon_id bigint NOT NULL,
    receiver_pokemon_id bigint,
    status character varying(30) COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    notification_message_id character varying(20) COLLATE pg_catalog."default",
    CONSTRAINT trade_requests_pkey PRIMARY KEY (trade_id),
    CONSTRAINT fk_receiver_pokemon FOREIGN KEY (receiver_pokemon_id)
        REFERENCES public.pokemon (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_sender_pokemon FOREIGN KEY (sender_pokemon_id)
        REFERENCES public.pokemon (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trade_requests
    OWNER to redbot;
-- Index: idx_trade_created

-- DROP INDEX IF EXISTS public.idx_trade_created;

CREATE INDEX IF NOT EXISTS idx_trade_created
    ON public.trade_requests USING btree
    (created_at DESC NULLS FIRST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;
-- Index: idx_trade_receiver

-- DROP INDEX IF EXISTS public.idx_trade_receiver;

CREATE INDEX IF NOT EXISTS idx_trade_receiver
    ON public.trade_requests USING btree
    (receiver_discord_id COLLATE pg_catalog."default" ASC NULLS LAST, status COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;
-- Index: idx_trade_sender

-- DROP INDEX IF EXISTS public.idx_trade_sender;

CREATE INDEX IF NOT EXISTS idx_trade_sender
    ON public.trade_requests USING btree
    (sender_discord_id COLLATE pg_catalog."default" ASC NULLS LAST, status COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;
-- Index: idx_trade_status

-- DROP INDEX IF EXISTS public.idx_trade_status;

CREATE INDEX IF NOT EXISTS idx_trade_status
    ON public.trade_requests USING btree
    (status COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;