-- Table: public.leaderboard

-- DROP TABLE IF EXISTS public.leaderboard;

CREATE TABLE IF NOT EXISTS public.leaderboard
(
    discord_id character varying COLLATE pg_catalog."default" NOT NULL,
    total_battles integer DEFAULT 0,
    total_victory integer DEFAULT 0,
    total_defeat integer DEFAULT 0,
    total_actions integer DEFAULT 0,
    total_balls_thrown integer DEFAULT 0,
    total_catch integer DEFAULT 0,
    total_run_away integer DEFAULT 0,
    total_released integer DEFAULT 0,
    total_evolved integer DEFAULT 0,
    total_easter_eggs integer DEFAULT 0,
    total_completions integer DEFAULT 0,
    total_trades integer DEFAULT 0,
    CONSTRAINT stats_pkey PRIMARY KEY (discord_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.leaderboard
    OWNER to redbot;