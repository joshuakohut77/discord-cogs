# ---------------------------------------------------------------
# The Vault — display constants & property key registry
# ---------------------------------------------------------------
import re

# -- Branding --
# Using the same ChodeCoin emoji since cards are bought with CC
COIN_EMOJI = "<:ChodeCoin:1479593199554269318>"

_emoji_id_match = re.search(r"(\d+)>$", COIN_EMOJI)
COIN_EMOJI_URL = (
    f"https://cdn.discordapp.com/emojis/{_emoji_id_match.group(1)}.png?size=128"
    if _emoji_id_match
    else None
)

EMBED_COLOR = 0x8B0000        # dark red — fits the dark fantasy tone
STORE_EMBED_COLOR = 0xffa72e  # gold — matches ChodeCoin for purchase context

# -- Card categories --
CATEGORY_SUPERPOWER = "superpower"
CATEGORY_ALLY = "ally"
CATEGORY_COMPANION = "companion"
CATEGORY_ITEM = "item"
CATEGORY_WEAPON = "weapon"
CATEGORY_ARMOR = "armor"

ALL_CATEGORIES = [
    CATEGORY_SUPERPOWER,
    CATEGORY_ALLY,
    CATEGORY_COMPANION,
    CATEGORY_ITEM,
    CATEGORY_WEAPON,
    CATEGORY_ARMOR,
]

# -- Rarity tiers & pull weights (per 10-card pack) --
RARITY_COMMON = "common"
RARITY_UNCOMMON = "uncommon"
RARITY_RARE = "rare"
RARITY_LEGENDARY = "legendary"

RARITY_ORDER = [RARITY_COMMON, RARITY_UNCOMMON, RARITY_RARE, RARITY_LEGENDARY]

# Distribution: 4/3/2/1 per 10 cards
RARITY_WEIGHTS = {
    RARITY_COMMON: 4,
    RARITY_UNCOMMON: 3,
    RARITY_RARE: 2,
    RARITY_LEGENDARY: 1,
}

# -- Equip slots --
SLOT_MAIN_HAND = "main_hand"
SLOT_OFF_HAND = "off_hand"
SLOT_HEAD = "head"
SLOT_CHEST = "chest"
SLOT_LEGS = "legs"
SLOT_FEET = "feet"
SLOT_COMPANION = "companion"

ALL_EQUIP_SLOTS = [
    SLOT_MAIN_HAND, SLOT_OFF_HAND,
    SLOT_HEAD, SLOT_CHEST, SLOT_LEGS, SLOT_FEET,
    SLOT_COMPANION,
]


# ---------------------------------------------------------------
# Property key constants
# Use these instead of raw strings to avoid typos.
# Definitions (descriptions, data types) live in the DB table
# chodecoin_property_defs — these are just the key references.
# ---------------------------------------------------------------
class PropKeys:
    """Known property keys for card_properties and inventory_state."""

    # -- Universal card properties --
    CONSUMABLE = "consumable"
    MAX_USES = "max_uses"
    COOLDOWN_HOURS = "cooldown_hours"
    TIME_RESTRICTION = "time_restriction"
    WEATHER_RESTRICTION = "weather_restriction"
    SEASONAL = "seasonal"
    EQUIP_SLOT = "equip_slot"
    PASSIVE_BONUS = "passive_bonus"
    SYNERGY_WITH = "synergy_with"
    CURSED = "cursed"
    CURSE_EFFECT = "curse_effect"

    # -- Ally / Companion --
    LOYALTY = "loyalty"
    CAN_FLEE = "can_flee"
    FLEE_CHANCE = "flee_chance"
    FLEE_DURATION_HOURS = "flee_duration_hours"
    HAS_OWN_AGENDA = "has_own_agenda"
    AGENDA_DESCRIPTION = "agenda_description"
    COMBAT_CAPABLE = "combat_capable"
    COMBAT_POWER = "combat_power"

    # -- Weapon / Armor --
    DAMAGE = "damage"
    DAMAGE_TYPE = "damage_type"
    ARMOR_VALUE = "armor_value"
    DURABILITY = "durability"

    # -- Item-specific --
    EFFECT_TYPE = "effect_type"
    EFFECT_VALUE = "effect_value"
    EFFECT_DURATION_HOURS = "effect_duration_hours"
    AOE = "aoe"
    SELF_DAMAGE = "self_damage"

    # -- Superpower --
    ACTIVATION_COST = "activation_cost"
    BACKFIRE_CHANCE = "backfire_chance"
    BACKFIRE_EFFECT = "backfire_effect"
    POWER_LEVEL = "power_level"
    REQUIRES_CONCENTRATION = "requires_concentration"


class StateKeys:
    """Known keys for per-instance inventory_state tracking."""

    USES_REMAINING = "uses_remaining"
    LAST_USED_AT = "last_used_at"
    FLED_UNTIL = "fled_until"
    DURABILITY_REMAINING = "durability_remaining"
    IS_CURSED_KNOWN = "is_cursed_known"
    EQUIPPED_AT = "equipped_at"
    BUFF_EXPIRES_AT = "buff_expires_at"
    ACCUMULATED_KILLS = "accumulated_kills"
    BOND_LEVEL = "bond_level"
