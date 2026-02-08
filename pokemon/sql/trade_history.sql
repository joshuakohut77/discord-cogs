-- View: public.trade_history

-- DROP VIEW public.trade_history;

CREATE OR REPLACE VIEW public.trade_history
 AS
 SELECT t.trade_id,
    t.sender_discord_id,
    t.receiver_discord_id,
    t.sender_pokemon_id,
    t.receiver_pokemon_id,
    t.status,
    t.created_at,
    t.updated_at,
    t.completed_at,
    t.notification_message_id,
    sp."pokemonName" AS sender_pokemon_name,
    sp."currentLevel" AS sender_pokemon_level,
    sp."nickName" AS sender_pokemon_nickname,
    rp."pokemonName" AS receiver_pokemon_name,
    rp."currentLevel" AS receiver_pokemon_level,
    rp."nickName" AS receiver_pokemon_nickname
   FROM trade_requests t
     LEFT JOIN pokemon sp ON t.sender_pokemon_id = sp.id
     LEFT JOIN pokemon rp ON t.receiver_pokemon_id = rp.id
  WHERE t.status::text = ANY (ARRAY['COMPLETED'::character varying, 'CANCELLED_BY_SENDER'::character varying, 'CANCELLED_BY_RECEIVER'::character varying, 'EXPIRED'::character varying, 'INVALID'::character varying]::text[]);

ALTER TABLE public.trade_history
    OWNER TO redbot;

