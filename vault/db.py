from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from .dbclass import db as dbconn
from .constants import PropKeys, StateKeys

log = logging.getLogger("red.vault.db")


class VaultDB:
    """High-level database operations for The Vault.

    All public methods are synchronous — the cog wraps them in
    asyncio.to_thread() so the bot loop is never blocked.
    """

    # ==================================================================
    # SCHEMA BOOTSTRAP
    # ==================================================================

    @staticmethod
    def create_tables() -> None:
        """Create all Vault tables and indexes if they don't exist."""
        database = dbconn()

        # -- Card catalog --
        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_cards (
                "Id"            SERIAL PRIMARY KEY,
                "Name"          VARCHAR(100) NOT NULL,
                "Category"      VARCHAR(50)  NOT NULL,
                "Rarity"        VARCHAR(20)  NOT NULL,
                "Explanation"   TEXT         NOT NULL,
                "Blurb"         TEXT         NOT NULL,
                "ArtFile"       VARCHAR(255),
                "RenderedFile"  VARCHAR(255),
                "StorePrice"    INTEGER      NOT NULL DEFAULT 0,
                "IsInStore"     BOOLEAN      NOT NULL DEFAULT TRUE,
                "IsActive"      BOOLEAN      NOT NULL DEFAULT TRUE,
                "CreatedAt"     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                "UpdatedAt"     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE ("Name", "Category")
            );
        """)

        # -- Property definitions (the rulebook) --
        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_property_defs (
                "Id"            SERIAL PRIMARY KEY,
                "Key"           VARCHAR(100) NOT NULL UNIQUE,
                "DataType"      VARCHAR(20)  NOT NULL DEFAULT 'string',
                "AppliesTo"     VARCHAR(255),
                "Description"   TEXT         NOT NULL,
                "Example"       VARCHAR(255),
                "CreatedAt"     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # -- Card properties (mechanics per card) --
        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_card_properties (
                "Id"            SERIAL PRIMARY KEY,
                "CardId"        INTEGER      NOT NULL REFERENCES vault_cards("Id") ON DELETE CASCADE,
                "Key"           VARCHAR(100) NOT NULL,
                "Value"         TEXT         NOT NULL,
                UNIQUE ("CardId", "Key")
            );
        """)

        # -- Player inventory --
        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_inventory (
                "Id"            SERIAL PRIMARY KEY,
                "GuildId"       VARCHAR(255) NOT NULL,
                "UserId"        VARCHAR(255) NOT NULL,
                "CardId"        INTEGER      NOT NULL REFERENCES vault_cards("Id"),
                "AcquiredVia"   VARCHAR(50)  NOT NULL DEFAULT 'store',
                "IsActive"      BOOLEAN      NOT NULL DEFAULT TRUE,
                "IsEquipped"    BOOLEAN      NOT NULL DEFAULT FALSE,
                "AcquiredAt"    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                "RetiredAt"     TIMESTAMP
            );
        """)

        # -- Inventory instance state --
        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_inventory_state (
                "Id"            SERIAL PRIMARY KEY,
                "InventoryId"   INTEGER      NOT NULL REFERENCES vault_inventory("Id") ON DELETE CASCADE,
                "Key"           VARCHAR(100) NOT NULL,
                "Value"         TEXT         NOT NULL,
                "UpdatedAt"     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE ("InventoryId", "Key")
            );
        """)

        # -- Indexes --
        for idx in [
            'CREATE INDEX IF NOT EXISTS idx_vault_cards_category ON vault_cards("Category");',
            'CREATE INDEX IF NOT EXISTS idx_vault_cards_rarity ON vault_cards("Rarity");',
            'CREATE INDEX IF NOT EXISTS idx_vault_cards_store ON vault_cards("IsInStore", "IsActive");',
            'CREATE INDEX IF NOT EXISTS idx_vault_card_props_card ON vault_card_properties("CardId");',
            'CREATE INDEX IF NOT EXISTS idx_vault_card_props_key ON vault_card_properties("Key");',
            'CREATE INDEX IF NOT EXISTS idx_vault_inv_guild_user ON vault_inventory("GuildId", "UserId");',
            'CREATE INDEX IF NOT EXISTS idx_vault_inv_card ON vault_inventory("CardId");',
            'CREATE INDEX IF NOT EXISTS idx_vault_inv_active ON vault_inventory("GuildId", "UserId", "IsActive");',
            'CREATE INDEX IF NOT EXISTS idx_vault_inv_state_inv ON vault_inventory_state("InventoryId");',
        ]:
            database.execute(idx)

    # ==================================================================
    # CARD CATALOG — READ
    # ==================================================================

    @staticmethod
    def get_card(card_id: int) -> Optional[dict]:
        """Fetch a single card by ID with all its properties."""
        database = dbconn()
        row = database.querySingle(
            'SELECT * FROM vault_cards WHERE "Id" = %(id)s',
            {"id": card_id},
        )
        if not row:
            return None

        card = VaultDB._row_to_card_dict(row)
        card["properties"] = VaultDB._get_card_properties(card_id)
        return card

    @staticmethod
    def get_card_by_name(name: str, category: Optional[str] = None) -> Optional[dict]:
        """Fetch a card by name (case-insensitive), optionally filtered by category."""
        database = dbconn()
        if category:
            row = database.querySingle(
                'SELECT * FROM vault_cards WHERE LOWER("Name") = LOWER(%(name)s) AND "Category" = %(cat)s',
                {"name": name, "cat": category},
            )
        else:
            row = database.querySingle(
                'SELECT * FROM vault_cards WHERE LOWER("Name") = LOWER(%(name)s)',
                {"name": name},
            )
        if not row:
            return None

        card = VaultDB._row_to_card_dict(row)
        card["properties"] = VaultDB._get_card_properties(card["id"])
        return card

    @staticmethod
    def browse_store(
        category: Optional[str] = None,
        rarity: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """Browse cards available in the store with optional filters."""
        database = dbconn()
        conditions = ['"IsInStore" = TRUE', '"IsActive" = TRUE']
        params: dict = {"limit": limit, "offset": offset}

        if category:
            conditions.append('"Category" = %(category)s')
            params["category"] = category
        if rarity:
            conditions.append('"Rarity" = %(rarity)s')
            params["rarity"] = rarity

        where = " AND ".join(conditions)
        rows = database.queryAll(
            f'SELECT * FROM vault_cards WHERE {where} ORDER BY "Category", "Rarity", "Name" LIMIT %(limit)s OFFSET %(offset)s',
            params,
        )
        return [VaultDB._row_to_card_dict(r) for r in rows]

    @staticmethod
    def count_store(category: Optional[str] = None, rarity: Optional[str] = None) -> int:
        """Count cards available in the store (for pagination)."""
        database = dbconn()
        conditions = ['"IsInStore" = TRUE', '"IsActive" = TRUE']
        params: dict = {}

        if category:
            conditions.append('"Category" = %(category)s')
            params["category"] = category
        if rarity:
            conditions.append('"Rarity" = %(rarity)s')
            params["rarity"] = rarity

        where = " AND ".join(conditions)
        row = database.querySingle(
            f"SELECT COUNT(*) FROM vault_cards WHERE {where}",
            params,
        )
        return row[0] if row else 0

    @staticmethod
    def get_random_card_by_rarity(rarity: str, category: Optional[str] = None) -> Optional[dict]:
        """Pick a random card of a given rarity from the store. Used for pack opening."""
        database = dbconn()
        params: dict = {"rarity": rarity}
        cat_filter = ""
        if category:
            cat_filter = ' AND "Category" = %(category)s'
            params["category"] = category

        row = database.querySingle(
            f"""SELECT * FROM vault_cards
                WHERE "IsInStore" = TRUE AND "IsActive" = TRUE
                AND "Rarity" = %(rarity)s{cat_filter}
                ORDER BY RANDOM() LIMIT 1""",
            params,
        )
        if not row:
            return None

        card = VaultDB._row_to_card_dict(row)
        card["properties"] = VaultDB._get_card_properties(card["id"])
        return card

    # ==================================================================
    # CARD CATALOG — WRITE (admin)
    # ==================================================================

    @staticmethod
    def add_card(
        name: str,
        category: str,
        rarity: str,
        explanation: str,
        blurb: str,
        store_price: int = 0,
        art_file: Optional[str] = None,
    ) -> int:
        """Insert a new card into the catalog. Returns the new card ID."""
        database = dbconn()
        row = database.executeAndReturn(
            """INSERT INTO vault_cards
                ("Name", "Category", "Rarity", "Explanation", "Blurb", "StorePrice", "ArtFile")
               VALUES (%(name)s, %(cat)s, %(rar)s, %(expl)s, %(blurb)s, %(price)s, %(art)s)
               RETURNING "Id"
            """,
            {
                "name": name, "cat": category, "rar": rarity,
                "expl": explanation, "blurb": blurb,
                "price": store_price, "art": art_file,
            },
        )
        return row[0]

    @staticmethod
    def update_card(card_id: int, **fields) -> None:
        """Update card catalog fields. Pass only the fields to change.

        Also nulls RenderedFile to invalidate the image cache.
        """
        allowed = {
            "Name", "Category", "Rarity", "Explanation", "Blurb",
            "ArtFile", "StorePrice", "IsInStore", "IsActive",
        }
        to_set = {k: v for k, v in fields.items() if k in allowed}
        if not to_set:
            return

        # Always invalidate rendered cache on update
        to_set["RenderedFile"] = None
        to_set["UpdatedAt"] = datetime.now(timezone.utc)

        set_clause = ", ".join(f'"{k}" = %({k})s' for k in to_set)
        to_set["id"] = card_id

        database = dbconn()
        database.execute(
            f'UPDATE vault_cards SET {set_clause} WHERE "Id" = %(id)s',
            to_set,
        )

    @staticmethod
    def set_card_property(card_id: int, key: str, value: str) -> None:
        """Set a property on a card (upsert)."""
        database = dbconn()
        database.execute(
            """INSERT INTO vault_card_properties ("CardId", "Key", "Value")
               VALUES (%(cid)s, %(key)s, %(val)s)
               ON CONFLICT ("CardId", "Key") DO UPDATE SET "Value" = %(val)s
            """,
            {"cid": card_id, "key": key, "val": str(value)},
        )

    @staticmethod
    def remove_card_property(card_id: int, key: str) -> None:
        """Remove a property from a card."""
        database = dbconn()
        database.execute(
            'DELETE FROM vault_card_properties WHERE "CardId" = %(cid)s AND "Key" = %(key)s',
            {"cid": card_id, "key": key},
        )

    # ==================================================================
    # INVENTORY — ACQUISITION
    # ==================================================================

    @staticmethod
    def grant_card(
        guild_id: int,
        user_id: int,
        card_id: int,
        acquired_via: str = "store",
    ) -> int:
        """Add a card to a player's inventory. Returns the inventory instance ID.

        Automatically initializes instance state from the card's properties
        (e.g. sets uses_remaining from max_uses, durability_remaining from durability).
        """
        database = dbconn()
        row = database.executeAndReturn(
            """INSERT INTO vault_inventory
                ("GuildId", "UserId", "CardId", "AcquiredVia")
               VALUES (%(gid)s, %(uid)s, %(cid)s, %(via)s)
               RETURNING "Id"
            """,
            {
                "gid": str(guild_id), "uid": str(user_id),
                "cid": card_id, "via": acquired_via,
            },
        )
        inv_id = row[0]

        # Initialize instance state from card properties
        props = VaultDB._get_card_properties(card_id)

        if PropKeys.MAX_USES in props:
            VaultDB._set_instance_state(inv_id, StateKeys.USES_REMAINING, props[PropKeys.MAX_USES])

        if PropKeys.DURABILITY in props:
            VaultDB._set_instance_state(inv_id, StateKeys.DURABILITY_REMAINING, props[PropKeys.DURABILITY])

        if PropKeys.CURSED in props and props[PropKeys.CURSED].lower() == "true":
            VaultDB._set_instance_state(inv_id, StateKeys.IS_CURSED_KNOWN, "false")

        return inv_id

    # ==================================================================
    # INVENTORY — READ
    # ==================================================================

    @staticmethod
    def get_inventory(
        guild_id: int,
        user_id: int,
        category: Optional[str] = None,
        active_only: bool = True,
    ) -> list[dict]:
        """Get a player's inventory with card details and instance state."""
        database = dbconn()
        conditions = ['"i"."GuildId" = %(gid)s', '"i"."UserId" = %(uid)s']
        params: dict = {"gid": str(guild_id), "uid": str(user_id)}

        if active_only:
            conditions.append('"i"."IsActive" = TRUE')
        if category:
            conditions.append('"c"."Category" = %(cat)s')
            params["category"] = category

        where = " AND ".join(conditions)
        rows = database.queryAll(
            f"""SELECT i."Id" as inv_id, i."IsEquipped", i."AcquiredVia", i."AcquiredAt",
                       c."Id" as card_id, c."Name", c."Category", c."Rarity",
                       c."Explanation", c."Blurb", c."ArtFile", c."RenderedFile"
                FROM vault_inventory i
                JOIN vault_cards c ON i."CardId" = c."Id"
                WHERE {where}
                ORDER BY c."Category", c."Rarity", c."Name"
            """,
            params,
        )

        inventory = []
        for row in rows:
            item = {
                "inv_id": row[0],
                "is_equipped": row[1],
                "acquired_via": row[2],
                "acquired_at": row[3],
                "card_id": row[4],
                "name": row[5],
                "category": row[6],
                "rarity": row[7],
                "explanation": row[8],
                "blurb": row[9],
                "art_file": row[10],
                "rendered_file": row[11],
                "properties": VaultDB._get_card_properties(row[4]),
                "state": VaultDB._get_instance_state(row[0]),
            }
            inventory.append(item)

        return inventory

    @staticmethod
    def get_inventory_item(inv_id: int) -> Optional[dict]:
        """Get a single inventory item with full card details and state."""
        database = dbconn()
        row = database.querySingle(
            """SELECT i."Id", i."GuildId", i."UserId", i."IsEquipped",
                      i."IsActive", i."AcquiredVia", i."AcquiredAt",
                      c."Id", c."Name", c."Category", c."Rarity",
                      c."Explanation", c."Blurb", c."ArtFile"
               FROM vault_inventory i
               JOIN vault_cards c ON i."CardId" = c."Id"
               WHERE i."Id" = %(id)s
            """,
            {"id": inv_id},
        )
        if not row:
            return None

        return {
            "inv_id": row[0],
            "guild_id": row[1],
            "user_id": row[2],
            "is_equipped": row[3],
            "is_active": row[4],
            "acquired_via": row[5],
            "acquired_at": row[6],
            "card_id": row[7],
            "name": row[8],
            "category": row[9],
            "rarity": row[10],
            "explanation": row[11],
            "blurb": row[12],
            "art_file": row[13],
            "properties": VaultDB._get_card_properties(row[7]),
            "state": VaultDB._get_instance_state(row[0]),
        }

    @staticmethod
    def count_inventory(guild_id: int, user_id: int, active_only: bool = True) -> int:
        """Count how many cards a player has."""
        database = dbconn()
        active_filter = ' AND "IsActive" = TRUE' if active_only else ""
        row = database.querySingle(
            f'SELECT COUNT(*) FROM vault_inventory WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s{active_filter}',
            {"gid": str(guild_id), "uid": str(user_id)},
        )
        return row[0] if row else 0

    @staticmethod
    def player_owns_card(guild_id: int, user_id: int, card_id: int) -> bool:
        """Check if a player owns an active copy of a specific card."""
        database = dbconn()
        row = database.querySingle(
            """SELECT COUNT(*) FROM vault_inventory
               WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s
               AND "CardId" = %(cid)s AND "IsActive" = TRUE
            """,
            {"gid": str(guild_id), "uid": str(user_id), "cid": card_id},
        )
        return (row[0] if row else 0) > 0

    # ==================================================================
    # INVENTORY — MUTATIONS
    # ==================================================================

    @staticmethod
    def retire_item(inv_id: int) -> None:
        """Retire an inventory item (consumed, destroyed, etc)."""
        database = dbconn()
        database.execute(
            """UPDATE vault_inventory
               SET "IsActive" = FALSE, "IsEquipped" = FALSE,
                   "RetiredAt" = CURRENT_TIMESTAMP
               WHERE "Id" = %(id)s
            """,
            {"id": inv_id},
        )

    @staticmethod
    def equip_item(guild_id: int, user_id: int, inv_id: int) -> Optional[str]:
        """Equip an inventory item. Unequips any item in the same slot.

        Returns None on success, or an error message string.
        """
        item = VaultDB.get_inventory_item(inv_id)
        if not item:
            return "Item not found."
        if not item["is_active"]:
            return "That item has been consumed or destroyed."
        if item["guild_id"] != str(guild_id) or item["user_id"] != str(user_id):
            return "That's not your item."

        slot = item["properties"].get(PropKeys.EQUIP_SLOT)
        if not slot:
            return "This card can't be equipped."

        # Check if item is temporarily unavailable (fled companion, etc)
        fled_until = item["state"].get(StateKeys.FLED_UNTIL)
        if fled_until:
            try:
                fled_dt = datetime.fromisoformat(fled_until)
                if datetime.now(timezone.utc) < fled_dt:
                    return "This companion has fled and isn't available right now."
            except (ValueError, TypeError):
                pass

        database = dbconn()

        # Unequip anything currently in that slot
        database.execute(
            """UPDATE vault_inventory
               SET "IsEquipped" = FALSE
               WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s
               AND "IsActive" = TRUE AND "IsEquipped" = TRUE
               AND "Id" IN (
                   SELECT i."Id" FROM vault_inventory i
                   JOIN vault_card_properties cp ON i."CardId" = cp."CardId"
                   WHERE cp."Key" = 'equip_slot' AND cp."Value" = %(slot)s
                   AND i."GuildId" = %(gid)s AND i."UserId" = %(uid)s
               )
            """,
            {"gid": str(guild_id), "uid": str(user_id), "slot": slot},
        )

        # Equip the new item
        database.execute(
            'UPDATE vault_inventory SET "IsEquipped" = TRUE WHERE "Id" = %(id)s',
            {"id": inv_id},
        )

        now = datetime.now(timezone.utc).isoformat()
        VaultDB._set_instance_state(inv_id, StateKeys.EQUIPPED_AT, now)
        return None

    @staticmethod
    def unequip_item(inv_id: int) -> None:
        """Unequip an inventory item."""
        database = dbconn()
        database.execute(
            'UPDATE vault_inventory SET "IsEquipped" = FALSE WHERE "Id" = %(id)s',
            {"id": inv_id},
        )

    # ==================================================================
    # ITEM USAGE — activation, cooldowns, consumables
    # ==================================================================

    @staticmethod
    def use_item(inv_id: int) -> dict:
        """Attempt to use/activate an inventory item.

        Returns a result dict with:
          success: bool
          error: optional error message
          consumed: bool — whether the item was destroyed by this use
          uses_remaining: optional int
          card: the full card+state dict
        """
        item = VaultDB.get_inventory_item(inv_id)
        if not item:
            return {"success": False, "error": "Item not found."}
        if not item["is_active"]:
            return {"success": False, "error": "That item has been consumed or destroyed."}

        props = item["properties"]
        state = item["state"]
        now = datetime.now(timezone.utc)

        # -- Check cooldown --
        cooldown_hours = props.get(PropKeys.COOLDOWN_HOURS)
        last_used = state.get(StateKeys.LAST_USED_AT)
        if cooldown_hours and last_used:
            try:
                last_dt = datetime.fromisoformat(last_used)
                elapsed = (now - last_dt).total_seconds() / 3600
                remaining = float(cooldown_hours) - elapsed
                if remaining > 0:
                    return {
                        "success": False,
                        "error": f"On cooldown. Available in {remaining:.1f} hours.",
                    }
            except (ValueError, TypeError):
                pass

        # -- Check flee status --
        fled_until = state.get(StateKeys.FLED_UNTIL)
        if fled_until:
            try:
                fled_dt = datetime.fromisoformat(fled_until)
                if now < fled_dt:
                    return {
                        "success": False,
                        "error": "This companion has fled and isn't available.",
                    }
                else:
                    # Fled period is over — clear the state
                    VaultDB._remove_instance_state(inv_id, StateKeys.FLED_UNTIL)
            except (ValueError, TypeError):
                pass

        # -- Check time restriction --
        time_restriction = props.get(PropKeys.TIME_RESTRICTION)
        # NOTE: actual time-of-day check would depend on game world time
        # or real time. Leaving as a hook — DM can also enforce narratively.

        # -- Decrement uses if applicable --
        consumed = False
        uses_remaining = None

        if PropKeys.MAX_USES in props:
            current_uses = int(state.get(StateKeys.USES_REMAINING, props[PropKeys.MAX_USES]))
            if current_uses <= 0:
                return {"success": False, "error": "No uses remaining."}
            current_uses -= 1
            VaultDB._set_instance_state(inv_id, StateKeys.USES_REMAINING, str(current_uses))
            uses_remaining = current_uses

            if current_uses <= 0 and props.get(PropKeys.CONSUMABLE, "").lower() == "true":
                VaultDB.retire_item(inv_id)
                consumed = True

        elif props.get(PropKeys.CONSUMABLE, "").lower() == "true":
            # Single-use consumable with no max_uses — destroy on first use
            VaultDB.retire_item(inv_id)
            consumed = True

        # -- Decrement durability if applicable --
        if PropKeys.DURABILITY in props and not consumed:
            current_dur = int(state.get(StateKeys.DURABILITY_REMAINING, props[PropKeys.DURABILITY]))
            current_dur -= 1
            VaultDB._set_instance_state(inv_id, StateKeys.DURABILITY_REMAINING, str(current_dur))
            if current_dur <= 0:
                VaultDB.retire_item(inv_id)
                consumed = True

        # -- Record last used --
        if not consumed:
            VaultDB._set_instance_state(inv_id, StateKeys.LAST_USED_AT, now.isoformat())

        # Refresh item state after mutations
        item = VaultDB.get_inventory_item(inv_id)

        return {
            "success": True,
            "error": None,
            "consumed": consumed,
            "uses_remaining": uses_remaining,
            "card": item,
        }

    @staticmethod
    def trigger_flee(inv_id: int) -> Optional[str]:
        """Force a companion/ally to flee. Returns the return timestamp, or None if can't flee."""
        item = VaultDB.get_inventory_item(inv_id)
        if not item or not item["is_active"]:
            return None

        props = item["properties"]
        if props.get(PropKeys.CAN_FLEE, "").lower() != "true":
            return None

        hours = float(props.get(PropKeys.FLEE_DURATION_HOURS, 1))
        now = datetime.now(timezone.utc)
        return_at = now.timestamp() + (hours * 3600)
        return_dt = datetime.fromtimestamp(return_at, tz=timezone.utc)

        VaultDB._set_instance_state(inv_id, StateKeys.FLED_UNTIL, return_dt.isoformat())

        # Unequip if equipped
        if item["is_equipped"]:
            VaultDB.unequip_item(inv_id)

        return return_dt.isoformat()

    @staticmethod
    def check_fled_return(inv_id: int) -> bool:
        """Check if a fled companion has returned. Clears state if so. Returns True if available."""
        state = VaultDB._get_instance_state(inv_id)
        fled_until = state.get(StateKeys.FLED_UNTIL)
        if not fled_until:
            return True

        try:
            fled_dt = datetime.fromisoformat(fled_until)
            if datetime.now(timezone.utc) >= fled_dt:
                VaultDB._remove_instance_state(inv_id, StateKeys.FLED_UNTIL)
                return True
            return False
        except (ValueError, TypeError):
            return True

    # ==================================================================
    # DM CONTEXT — feeds the dungeon master (Claude) game state
    # ==================================================================

    @staticmethod
    def get_dm_card_context(card_id: int) -> Optional[dict]:
        """Get full card info including DM-only fields (curse details, agendas, etc).

        This is what gets fed to the DM AI. Includes everything.
        """
        card = VaultDB.get_card(card_id)
        if not card:
            return None

        # Fetch property definitions for any properties this card has
        database = dbconn()
        prop_defs = {}
        for key in card["properties"]:
            defn = database.querySingle(
                'SELECT "Description" FROM vault_property_defs WHERE "Key" = %(key)s',
                {"key": key},
            )
            if defn:
                prop_defs[key] = defn[0]

        card["property_definitions"] = prop_defs
        return card

    @staticmethod
    def get_dm_player_context(guild_id: int, user_id: int) -> dict:
        """Get a full dump of a player's game state for the DM.

        Returns inventory with all card details, properties, instance state,
        and property definitions — everything the DM needs to run the game.
        """
        inventory = VaultDB.get_inventory(guild_id, user_id)

        # Enrich each item with property definitions
        database = dbconn()
        all_defs: dict = {}

        for item in inventory:
            for key in item["properties"]:
                if key not in all_defs:
                    defn = database.querySingle(
                        'SELECT "Description" FROM vault_property_defs WHERE "Key" = %(key)s',
                        {"key": key},
                    )
                    if defn:
                        all_defs[key] = defn[0]

        equipped = [i for i in inventory if i["is_equipped"]]
        available = [i for i in inventory if not i["is_equipped"]]

        return {
            "player_user_id": str(user_id),
            "total_cards": len(inventory),
            "equipped": equipped,
            "available": available,
            "property_definitions": all_defs,
        }

    @staticmethod
    def get_all_property_defs() -> list[dict]:
        """Get all property definitions. Useful for DM context loading."""
        database = dbconn()
        rows = database.queryAll(
            'SELECT "Key", "DataType", "AppliesTo", "Description", "Example" FROM vault_property_defs ORDER BY "Key"'
        )
        return [
            {
                "key": r[0], "data_type": r[1], "applies_to": r[2],
                "description": r[3], "example": r[4],
            }
            for r in rows
        ]

    # ==================================================================
    # INTERNAL HELPERS
    # ==================================================================

    @staticmethod
    def _row_to_card_dict(row) -> dict:
        """Convert a vault_cards row tuple to a dict."""
        return {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "rarity": row[3],
            "explanation": row[4],
            "blurb": row[5],
            "art_file": row[6],
            "rendered_file": row[7],
            "store_price": row[8],
            "is_in_store": row[9],
            "is_active": row[10],
            "created_at": row[11],
            "updated_at": row[12],
        }

    @staticmethod
    def _get_card_properties(card_id: int) -> dict:
        """Get all properties for a card as a key->value dict."""
        database = dbconn()
        rows = database.queryAll(
            'SELECT "Key", "Value" FROM vault_card_properties WHERE "CardId" = %(cid)s',
            {"cid": card_id},
        )
        return {k: v for k, v in rows}

    @staticmethod
    def _get_instance_state(inv_id: int) -> dict:
        """Get all state key-values for an inventory instance."""
        database = dbconn()
        rows = database.queryAll(
            'SELECT "Key", "Value" FROM vault_inventory_state WHERE "InventoryId" = %(id)s',
            {"id": inv_id},
        )
        return {k: v for k, v in rows}

    @staticmethod
    def _set_instance_state(inv_id: int, key: str, value: str) -> None:
        """Set or update a state value on an inventory instance."""
        database = dbconn()
        database.execute(
            """INSERT INTO vault_inventory_state ("InventoryId", "Key", "Value", "UpdatedAt")
               VALUES (%(id)s, %(key)s, %(val)s, CURRENT_TIMESTAMP)
               ON CONFLICT ("InventoryId", "Key")
               DO UPDATE SET "Value" = %(val)s, "UpdatedAt" = CURRENT_TIMESTAMP
            """,
            {"id": inv_id, "key": key, "val": str(value)},
        )

    @staticmethod
    def _remove_instance_state(inv_id: int, key: str) -> None:
        """Remove a state key from an inventory instance."""
        database = dbconn()
        database.execute(
            'DELETE FROM vault_inventory_state WHERE "InventoryId" = %(id)s AND "Key" = %(key)s',
            {"id": inv_id, "key": key},
        )