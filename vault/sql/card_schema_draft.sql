-- ============================================================
-- ChodeCoin Card System — Schema Draft
-- ============================================================
-- Design philosophy:
--   - One universal card catalog (not per-category tables)
--   - Flexible key-value properties for card mechanics
--   - Separate inventory tracking with per-instance state
--   - Property definitions table so the DM (Claude) can query
--     what each mechanic means without hardcoding knowledge
-- ============================================================


-- ============================================================
-- 1. CARD CATALOG
-- The canonical definition of every card in the game.
-- Universal fields only — anything behavioral goes in properties.
-- ============================================================
CREATE TABLE IF NOT EXISTS vault_cards (
    "Id"            SERIAL PRIMARY KEY,
    "Name"          VARCHAR(100) NOT NULL,
    "Category"      VARCHAR(50)  NOT NULL,      -- superpower, ally, companion, item, weapon, armor, ...
    "Rarity"        VARCHAR(20)  NOT NULL,       -- common, uncommon, rare, legendary
    "Explanation"   TEXT         NOT NULL,        -- one-sentence summary (shown on card)
    "Blurb"         TEXT         NOT NULL,        -- detailed description/limitations (shown on card)
    "ArtFile"       VARCHAR(255),                 -- filename of pixel art source, e.g. "fire_breath.png"
    "RenderedFile"  VARCHAR(255),                 -- cached composed card image (null = needs render)
    "StorePrice"    INTEGER      NOT NULL DEFAULT 0,  -- cost in ChodeCoin to buy from store
    "IsInStore"     BOOLEAN      NOT NULL DEFAULT TRUE,  -- available for purchase?
    "IsActive"      BOOLEAN      NOT NULL DEFAULT TRUE,  -- exists in game at all?
    "CreatedAt"     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    "UpdatedAt"     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    UNIQUE ("Name", "Category")
);

CREATE INDEX IF NOT EXISTS idx_vault_cards_category ON vault_cards("Category");
CREATE INDEX IF NOT EXISTS idx_vault_cards_rarity ON vault_cards("Rarity");
CREATE INDEX IF NOT EXISTS idx_vault_cards_store ON vault_cards("IsInStore", "IsActive");


-- ============================================================
-- 2. PROPERTY DEFINITIONS
-- Documents every known property key, what it means, what
-- data type to expect, and how the DM should interpret it.
-- This is the "rulebook" the DM queries to understand mechanics.
-- ============================================================
CREATE TABLE IF NOT EXISTS vault_property_defs (
    "Id"            SERIAL PRIMARY KEY,
    "Key"           VARCHAR(100) NOT NULL UNIQUE,
    "DataType"      VARCHAR(20)  NOT NULL DEFAULT 'string',  -- string, int, float, bool, json
    "AppliesTo"     VARCHAR(255),           -- csv of categories this is relevant to, null = all
    "Description"   TEXT         NOT NULL,   -- human/DM-readable explanation of this mechanic
    "Example"       VARCHAR(255),            -- example value for reference
    "CreatedAt"     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 3. CARD PROPERTIES
-- Key-value pairs that define a card's mechanical behavior.
-- Any card can have any combination of properties.
-- ============================================================
CREATE TABLE IF NOT EXISTS vault_card_properties (
    "Id"            SERIAL PRIMARY KEY,
    "CardId"        INTEGER      NOT NULL REFERENCES vault_cards("Id") ON DELETE CASCADE,
    "Key"           VARCHAR(100) NOT NULL,   -- references a key from property_defs
    "Value"         TEXT         NOT NULL,    -- always stored as text, cast in code

    UNIQUE ("CardId", "Key")
);

CREATE INDEX IF NOT EXISTS idx_vault_card_props_card ON vault_card_properties("CardId");
CREATE INDEX IF NOT EXISTS idx_vault_card_props_key ON vault_card_properties("Key");


-- ============================================================
-- 4. PLAYER INVENTORY
-- Tracks which cards a player owns. Each row is one "instance"
-- of a card — if a player somehow gets two of the same card,
-- that's two inventory rows.
-- ============================================================
CREATE TABLE IF NOT EXISTS vault_inventory (
    "Id"            SERIAL PRIMARY KEY,
    "GuildId"       VARCHAR(255) NOT NULL,
    "UserId"        VARCHAR(255) NOT NULL,
    "CardId"        INTEGER      NOT NULL REFERENCES vault_cards("Id"),
    "AcquiredVia"   VARCHAR(50)  NOT NULL DEFAULT 'store',  -- store, gift, drop, admin, quest, ...
    "IsActive"      BOOLEAN      NOT NULL DEFAULT TRUE,      -- false = consumed/destroyed/removed
    "IsEquipped"    BOOLEAN      NOT NULL DEFAULT FALSE,      -- for weapons/armor/companions
    "AcquiredAt"    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    "RetiredAt"     TIMESTAMP                                 -- when consumed/destroyed, null if active
);

CREATE INDEX IF NOT EXISTS idx_vault_inv_guild_user ON vault_inventory("GuildId", "UserId");
CREATE INDEX IF NOT EXISTS idx_vault_inv_card ON vault_inventory("CardId");
CREATE INDEX IF NOT EXISTS idx_vault_inv_active ON vault_inventory("GuildId", "UserId", "IsActive");


-- ============================================================
-- 5. INVENTORY INSTANCE STATE
-- Per-instance key-value state for a player's copy of a card.
-- This is where runtime/mutable state lives:
--   - remaining uses on a consumable
--   - whether a companion has fled and when it returns
--   - cooldown timers
--   - accumulated damage on a weapon
--   - temporary buffs/debuffs
--
-- Distinct from card_properties (which define what a card IS)
-- this tracks what's HAPPENING with this specific instance.
-- ============================================================
CREATE TABLE IF NOT EXISTS vault_inventory_state (
    "Id"            SERIAL PRIMARY KEY,
    "InventoryId"   INTEGER      NOT NULL REFERENCES vault_inventory("Id") ON DELETE CASCADE,
    "Key"           VARCHAR(100) NOT NULL,
    "Value"         TEXT         NOT NULL,
    "UpdatedAt"     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    UNIQUE ("InventoryId", "Key")
);

CREATE INDEX IF NOT EXISTS idx_vault_inv_state_inv ON vault_inventory_state("InventoryId");


-- ============================================================
-- 6. SEED: PROPERTY DEFINITIONS
-- Initial set of known property keys with descriptions.
-- The DM queries this to understand game mechanics.
-- New mechanics = new rows here. No schema migration needed.
-- ============================================================
INSERT INTO vault_property_defs ("Key", "DataType", "AppliesTo", "Description", "Example")
VALUES
-- ---- UNIVERSAL PROPERTIES (any category) ----
('consumable',          'bool',   NULL,              'Whether this card is destroyed after use. When true, the inventory instance is retired after activation.',   'true'),
('max_uses',            'int',    NULL,              'Maximum number of times this card can be activated before it is consumed. Tracked per-instance in inventory state as "uses_remaining".',  '3'),
('cooldown_hours',      'float',  NULL,              'Hours that must pass between activations. Tracked per-instance as "last_used_at" timestamp.',   '24'),
('time_restriction',    'string', NULL,              'Time of day when this card can be used. Values: day, night, dawn, dusk. Null means always usable.',   'night'),
('weather_restriction', 'string', NULL,              'Weather conditions required or forbidden. Format: "requires:rain" or "forbids:rain". Null means no restriction.',   'requires:storm'),
('seasonal',            'string', NULL,              'Season when this card is active. Values: spring, summer, autumn, winter. Null means always.',   'winter'),
('equip_slot',          'string', 'weapon,armor,companion',  'The slot this card occupies when equipped. Only one card per slot. Values: main_hand, off_hand, head, chest, legs, feet, companion.',   'main_hand'),
('passive_bonus',       'string', NULL,              'Passive stat bonus while card is owned/equipped. Format: "stat+value" or "stat-value". Multiple bonuses comma-separated.',   'stealth+2,perception+1'),
('synergy_with',        'json',   NULL,              'JSON array of card IDs or category names this card has special interactions with. DM interprets narratively.',   '["fire_breath", "companion"]'),
('cursed',              'bool',   NULL,              'Whether this card has a hidden downside. The DM knows the curse; the player discovers it in play.',   'true'),
('curse_effect',        'string', NULL,              'Description of the curse effect for the DM. Never shown directly to players.',   'Drains 1 ChodeCoin per day from holder'),

-- ---- ALLY / COMPANION PROPERTIES ----
('loyalty',             'string', 'ally,companion',  'How reliably this entity follows orders. Values: fanatical, loyal, neutral, fickle, treacherous. Affects DM narrative.',   'fickle'),
('can_flee',            'bool',   'ally,companion',  'Whether this entity can temporarily disappear from inventory. Tracked per-instance as "fled_until" timestamp.',   'true'),
('flee_chance',         'float',  'ally,companion',  'Probability (0.0–1.0) of fleeing when triggered (combat, loud noise, etc). Rolled by DM.',   '0.15'),
('flee_duration_hours', 'float',  'ally,companion',  'How long the entity is gone when it flees. Tracked per-instance as "fled_until".',   '3'),
('has_own_agenda',      'bool',   'ally',            'Whether this ally may act independently or against player interests. DM uses this for narrative tension.',   'true'),
('agenda_description',  'string', 'ally',            'DM-only description of what this ally secretly wants. Never shown to player.',   'Secretly reports player movements to the Shadow Guild'),
('combat_capable',      'bool',   'ally,companion',  'Whether this entity can fight. False means utility/support only.',   'true'),
('combat_power',        'int',    'ally,companion',  'Relative combat strength rating 1-10. Used by DM to judge outcomes.',   '6'),

-- ---- WEAPON / ARMOR PROPERTIES ----
('damage',              'int',    'weapon',          'Base damage value for the weapon.',   '15'),
('damage_type',         'string', 'weapon',          'Type of damage dealt. Values: slash, pierce, blunt, fire, ice, lightning, dark, holy.',   'slash'),
('armor_value',         'int',    'armor',           'Damage reduction provided when equipped.',   '8'),
('durability',          'int',    'weapon,armor',    'Max durability before the item breaks. Tracked per-instance as "durability_remaining". Null means indestructible.',   '50'),

-- ---- ITEM-SPECIFIC PROPERTIES ----
('effect_type',         'string', 'item',            'What this item does when activated. Values: heal, damage, buff, debuff, teleport, reveal, summon, transform, utility.',   'heal'),
('effect_value',        'int',    'item',            'Numeric magnitude of the effect. Meaning depends on effect_type.',   '50'),
('effect_duration_hours','float', 'item',            'How long the effect lasts. Null means instant.',   '2'),
('aoe',                 'bool',   'item,weapon',     'Whether the effect hits multiple targets.',   'false'),
('self_damage',         'int',    'item,weapon,superpower',  'Damage dealt to the user when activating. Represents a cost/tradeoff.',   '10'),

-- ---- SUPERPOWER PROPERTIES ----
('activation_cost',     'string', 'superpower',      'What it costs to use this power beyond just having it. Format varies: "10hp", "1_use_per_day", "25cc". DM interprets.',   '10hp'),
('backfire_chance',     'float',  'superpower',      'Probability (0.0–1.0) that the power misfires with unintended consequences. DM narrates the backfire.',   '0.10'),
('backfire_effect',     'string', 'superpower',      'DM-only description of what happens on a backfire.',   'Power reflects back on the caster at double strength'),
('power_level',         'int',    'superpower',      'Relative strength rating 1-10. Legendaries tend toward 8-10 but with severe tradeoffs.',   '7'),
('requires_concentration', 'bool','superpower',      'Whether the user must focus to maintain this power, preventing other actions.',   'true')

ON CONFLICT ("Key") DO NOTHING;


-- ============================================================
-- COMMON INVENTORY STATE KEYS (documentation, not a table)
-- These are the keys your code would read/write on inventory
-- instances at runtime:
--
--   uses_remaining     — int, decremented on each use
--   last_used_at       — timestamp, for cooldown checks
--   fled_until         — timestamp, when companion/ally returns
--   durability_remaining — int, decremented on use/hit
--   is_cursed_known    — bool, whether player has discovered the curse
--   equipped_at        — timestamp, when item was equipped
--   buff_expires_at    — timestamp, when a temporary buff wears off
--   accumulated_kills  — int, for weapons that grow in power
--   bond_level         — int, for companions that strengthen over time
-- ============================================================