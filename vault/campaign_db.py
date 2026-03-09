from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .dbclass import db as dbconn

log = logging.getLogger("red.vault.campaign_db")


class CampaignDB:
    """Database operations for the campaign system.

    All public methods are synchronous — the cog wraps them in
    asyncio.to_thread() so the bot loop is never blocked.
    """

    # ==================================================================
    # SCHEMA BOOTSTRAP
    # ==================================================================

    @staticmethod
    def create_tables() -> None:
        """Create all campaign tables and indexes if they don't exist."""
        database = dbconn()

        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_campaigns (
                "Id"                    SERIAL PRIMARY KEY,
                "GuildId"               VARCHAR(255) NOT NULL,
                "ChannelId"             VARCHAR(255) NOT NULL,
                "Status"                VARCHAR(20)  NOT NULL DEFAULT 'setup',
                "TurnOrder"             TEXT         NOT NULL DEFAULT '[]',
                "CurrentTurnIndex"      INTEGER      NOT NULL DEFAULT 0,
                "CurrentRound"          INTEGER      NOT NULL DEFAULT 1,
                "LastMessageId"         VARCHAR(255),
                "LastInventoryMessageId" VARCHAR(255),
                "CreatedAt"             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                "EndedAt"               TIMESTAMP
            );
        """)

        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_campaign_players (
                "Id"                    SERIAL PRIMARY KEY,
                "CampaignId"            INTEGER      NOT NULL REFERENCES vault_campaigns("Id") ON DELETE CASCADE,
                "UserId"                VARCHAR(255) NOT NULL,
                "DisplayName"           VARCHAR(255) NOT NULL,
                "QuestionsUsedThisTurn" INTEGER      NOT NULL DEFAULT 0,
                "JoinedAt"              TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE ("CampaignId", "UserId")
            );
        """)

        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_campaign_messages (
                "Id"                    SERIAL PRIMARY KEY,
                "CampaignId"            INTEGER      NOT NULL REFERENCES vault_campaigns("Id") ON DELETE CASCADE,
                "Role"                  VARCHAR(20)  NOT NULL,
                "Content"               TEXT         NOT NULL,
                "TurnNumber"            INTEGER,
                "MessageType"           VARCHAR(30)  NOT NULL DEFAULT 'turn',
                "CreatedAt"             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        database.execute("""
            CREATE TABLE IF NOT EXISTS vault_campaign_turns (
                "Id"                    SERIAL PRIMARY KEY,
                "CampaignId"            INTEGER      NOT NULL REFERENCES vault_campaigns("Id") ON DELETE CASCADE,
                "UserId"                VARCHAR(255) NOT NULL,
                "TurnNumber"            INTEGER      NOT NULL,
                "RoundNumber"           INTEGER      NOT NULL DEFAULT 1,
                "ActionType"            VARCHAR(20)  NOT NULL,
                "CardInvId"             INTEGER,
                "CardName"              VARCHAR(100),
                "ActionText"            TEXT,
                "DmResponse"            TEXT,
                "CardConsumed"          BOOLEAN      NOT NULL DEFAULT FALSE,
                "CreatedAt"             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Indexes
        for idx in [
            """CREATE INDEX IF NOT EXISTS idx_vault_campaigns_guild
               ON vault_campaigns("GuildId", "Status");""",
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_vault_campaigns_active_guild
               ON vault_campaigns("GuildId")
               WHERE "Status" IN ('setup', 'active', 'paused');""",
            """CREATE INDEX IF NOT EXISTS idx_vault_campaign_players_campaign
               ON vault_campaign_players("CampaignId");""",
            """CREATE INDEX IF NOT EXISTS idx_vault_campaign_messages_chain
               ON vault_campaign_messages("CampaignId", "Id");""",
            """CREATE INDEX IF NOT EXISTS idx_vault_campaign_turns_campaign
               ON vault_campaign_turns("CampaignId", "TurnNumber");""",
        ]:
            database.execute(idx)

    # ==================================================================
    # CAMPAIGN LIFECYCLE
    # ==================================================================

    @staticmethod
    def create_campaign(guild_id: int, channel_id: int) -> int:
        """Create a new campaign. Returns the campaign ID.

        Raises if there's already an active campaign in this guild.
        """
        database = dbconn()

        # Check for existing active campaign
        existing = database.querySingle(
            """SELECT "Id" FROM vault_campaigns
               WHERE "GuildId" = %(gid)s AND "Status" IN ('setup', 'active', 'paused')
            """,
            {"gid": str(guild_id)},
        )
        if existing:
            raise ValueError(f"Guild already has an active campaign (ID #{existing[0]}). End it first.")

        row = database.executeAndReturn(
            """INSERT INTO vault_campaigns ("GuildId", "ChannelId")
               VALUES (%(gid)s, %(cid)s)
               RETURNING "Id"
            """,
            {"gid": str(guild_id), "cid": str(channel_id)},
        )
        return row[0]

    @staticmethod
    def get_active_campaign(guild_id: int) -> Optional[dict]:
        """Get the active campaign for a guild, or None."""
        database = dbconn()
        row = database.querySingle(
            """SELECT "Id", "GuildId", "ChannelId", "Status", "TurnOrder",
                      "CurrentTurnIndex", "CurrentRound",
                      "LastMessageId", "LastInventoryMessageId",
                      "CreatedAt", "EndedAt"
               FROM vault_campaigns
               WHERE "GuildId" = %(gid)s AND "Status" IN ('setup', 'active', 'paused')
            """,
            {"gid": str(guild_id)},
        )
        if not row:
            return None
        return CampaignDB._row_to_campaign_dict(row)

    @staticmethod
    def set_campaign_status(campaign_id: int, status: str) -> None:
        """Update campaign status. Valid: setup, active, paused, ended."""
        database = dbconn()
        params = {"id": campaign_id, "status": status}
        extra = ""
        if status == "ended":
            extra = ', "EndedAt" = CURRENT_TIMESTAMP'
        database.execute(
            f'UPDATE vault_campaigns SET "Status" = %(status)s{extra} WHERE "Id" = %(id)s',
            params,
        )

    @staticmethod
    def set_turn_order(campaign_id: int, user_ids: list[int]) -> None:
        """Set the turn order as a JSON array of user ID strings."""
        database = dbconn()
        order_json = json.dumps([str(uid) for uid in user_ids])
        database.execute(
            'UPDATE vault_campaigns SET "TurnOrder" = %(order)s WHERE "Id" = %(id)s',
            {"id": campaign_id, "order": order_json},
        )

    @staticmethod
    def advance_turn(campaign_id: int) -> dict:
        """Advance to the next player's turn. Wraps around and increments round.

        Returns the updated campaign dict.
        """
        database = dbconn()
        campaign = CampaignDB._get_campaign_by_id(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found.")

        turn_order = campaign["turn_order"]
        if not turn_order:
            raise ValueError("No turn order set.")

        new_index = campaign["current_turn_index"] + 1
        new_round = campaign["current_round"]

        if new_index >= len(turn_order):
            new_index = 0
            new_round += 1

        database.execute(
            """UPDATE vault_campaigns
               SET "CurrentTurnIndex" = %(idx)s, "CurrentRound" = %(rnd)s
               WHERE "Id" = %(id)s
            """,
            {"id": campaign_id, "idx": new_index, "rnd": new_round},
        )

        # Reset question counts for all players on new turn
        database.execute(
            'UPDATE vault_campaign_players SET "QuestionsUsedThisTurn" = 0 WHERE "CampaignId" = %(id)s',
            {"id": campaign_id},
        )

        return CampaignDB._get_campaign_by_id(campaign_id)

    @staticmethod
    def update_message_ids(
        campaign_id: int,
        last_message_id: Optional[str] = None,
        last_inventory_message_id: Optional[str] = None,
    ) -> None:
        """Track Discord message IDs for resume functionality."""
        database = dbconn()
        sets = []
        params = {"id": campaign_id}
        if last_message_id is not None:
            sets.append('"LastMessageId" = %(mid)s')
            params["mid"] = last_message_id
        if last_inventory_message_id is not None:
            sets.append('"LastInventoryMessageId" = %(imid)s')
            params["imid"] = last_inventory_message_id
        if sets:
            database.execute(
                f'UPDATE vault_campaigns SET {", ".join(sets)} WHERE "Id" = %(id)s',
                params,
            )

    # ==================================================================
    # PLAYERS
    # ==================================================================

    @staticmethod
    def add_player(campaign_id: int, user_id: int, display_name: str) -> int:
        """Add a player to the campaign. Returns the player row ID."""
        database = dbconn()
        row = database.executeAndReturn(
            """INSERT INTO vault_campaign_players ("CampaignId", "UserId", "DisplayName")
               VALUES (%(cid)s, %(uid)s, %(name)s)
               RETURNING "Id"
            """,
            {"cid": campaign_id, "uid": str(user_id), "name": display_name},
        )
        return row[0]

    @staticmethod
    def get_players(campaign_id: int) -> list[dict]:
        """Get all players in a campaign."""
        database = dbconn()
        rows = database.queryAll(
            """SELECT "Id", "CampaignId", "UserId", "DisplayName",
                      "QuestionsUsedThisTurn", "JoinedAt"
               FROM vault_campaign_players
               WHERE "CampaignId" = %(cid)s
               ORDER BY "JoinedAt"
            """,
            {"cid": campaign_id},
        )
        return [
            {
                "id": r[0], "campaign_id": r[1], "user_id": r[2],
                "display_name": r[3], "questions_used": r[4], "joined_at": r[5],
            }
            for r in rows
        ]

    @staticmethod
    def is_player_in_campaign(campaign_id: int, user_id: int) -> bool:
        """Check if a user is registered in the campaign."""
        database = dbconn()
        row = database.querySingle(
            """SELECT 1 FROM vault_campaign_players
               WHERE "CampaignId" = %(cid)s AND "UserId" = %(uid)s
            """,
            {"cid": campaign_id, "uid": str(user_id)},
        )
        return row is not None

    @staticmethod
    def use_question(campaign_id: int, user_id: int) -> bool:
        """Increment question counter for a player this turn.

        Returns True if they had a question available, False if already used.
        """
        database = dbconn()
        row = database.querySingle(
            """SELECT "QuestionsUsedThisTurn" FROM vault_campaign_players
               WHERE "CampaignId" = %(cid)s AND "UserId" = %(uid)s
            """,
            {"cid": campaign_id, "uid": str(user_id)},
        )
        if not row or row[0] >= 1:
            return False

        database.execute(
            """UPDATE vault_campaign_players
               SET "QuestionsUsedThisTurn" = "QuestionsUsedThisTurn" + 1
               WHERE "CampaignId" = %(cid)s AND "UserId" = %(uid)s
            """,
            {"cid": campaign_id, "uid": str(user_id)},
        )
        return True

    @staticmethod
    def get_questions_used(campaign_id: int, user_id: int) -> int:
        """Get how many questions a player has used this turn."""
        database = dbconn()
        row = database.querySingle(
            """SELECT "QuestionsUsedThisTurn" FROM vault_campaign_players
               WHERE "CampaignId" = %(cid)s AND "UserId" = %(uid)s
            """,
            {"cid": campaign_id, "uid": str(user_id)},
        )
        return row[0] if row else 0

    # ==================================================================
    # MESSAGE CHAIN (for Claude API reconstruction)
    # ==================================================================

    @staticmethod
    def add_message(
        campaign_id: int,
        role: str,
        content: str,
        turn_number: Optional[int] = None,
        message_type: str = "turn",
    ) -> int:
        """Append a message to the Claude conversation chain."""
        database = dbconn()
        row = database.executeAndReturn(
            """INSERT INTO vault_campaign_messages
                ("CampaignId", "Role", "Content", "TurnNumber", "MessageType")
               VALUES (%(cid)s, %(role)s, %(content)s, %(turn)s, %(type)s)
               RETURNING "Id"
            """,
            {
                "cid": campaign_id, "role": role, "content": content,
                "turn": turn_number, "type": message_type,
            },
        )
        return row[0]

    @staticmethod
    def get_message_chain(campaign_id: int) -> list[dict]:
        """Get the full message chain for a campaign, ordered by creation.

        Returns list of {role, content} dicts ready for the Claude API.
        """
        database = dbconn()
        rows = database.queryAll(
            """SELECT "Role", "Content", "TurnNumber", "MessageType"
               FROM vault_campaign_messages
               WHERE "CampaignId" = %(cid)s
               ORDER BY "Id"
            """,
            {"cid": campaign_id},
        )
        return [
            {"role": r[0], "content": r[1], "turn_number": r[2], "message_type": r[3]}
            for r in rows
        ]

    @staticmethod
    def get_last_dm_response(campaign_id: int) -> Optional[str]:
        """Get the most recent assistant (DM) response."""
        database = dbconn()
        row = database.querySingle(
            """SELECT "Content" FROM vault_campaign_messages
               WHERE "CampaignId" = %(cid)s AND "Role" = 'assistant'
               ORDER BY "Id" DESC LIMIT 1
            """,
            {"cid": campaign_id},
        )
        return row[0] if row else None

    # ==================================================================
    # TURN LOG
    # ==================================================================

    @staticmethod
    def log_turn(
        campaign_id: int,
        user_id: int,
        turn_number: int,
        round_number: int,
        action_type: str,
        dm_response: str,
        card_inv_id: Optional[int] = None,
        card_name: Optional[str] = None,
        action_text: Optional[str] = None,
        card_consumed: bool = False,
    ) -> int:
        """Log a completed turn action."""
        database = dbconn()
        row = database.executeAndReturn(
            """INSERT INTO vault_campaign_turns
                ("CampaignId", "UserId", "TurnNumber", "RoundNumber",
                 "ActionType", "CardInvId", "CardName", "ActionText",
                 "DmResponse", "CardConsumed")
               VALUES (%(cid)s, %(uid)s, %(turn)s, %(rnd)s,
                       %(atype)s, %(cinv)s, %(cname)s, %(atext)s,
                       %(dmr)s, %(consumed)s)
               RETURNING "Id"
            """,
            {
                "cid": campaign_id, "uid": str(user_id),
                "turn": turn_number, "rnd": round_number,
                "atype": action_type, "cinv": card_inv_id,
                "cname": card_name, "atext": action_text,
                "dmr": dm_response, "consumed": card_consumed,
            },
        )
        return row[0]

    @staticmethod
    def get_turn_count(campaign_id: int) -> int:
        """Get total number of turns taken in the campaign."""
        database = dbconn()
        row = database.querySingle(
            'SELECT COUNT(*) FROM vault_campaign_turns WHERE "CampaignId" = %(cid)s',
            {"cid": campaign_id},
        )
        return row[0] if row else 0

    # ==================================================================
    # INTERNAL HELPERS
    # ==================================================================

    @staticmethod
    def _get_campaign_by_id(campaign_id: int) -> Optional[dict]:
        """Fetch a campaign by its ID."""
        database = dbconn()
        row = database.querySingle(
            """SELECT "Id", "GuildId", "ChannelId", "Status", "TurnOrder",
                      "CurrentTurnIndex", "CurrentRound",
                      "LastMessageId", "LastInventoryMessageId",
                      "CreatedAt", "EndedAt"
               FROM vault_campaigns WHERE "Id" = %(id)s
            """,
            {"id": campaign_id},
        )
        if not row:
            return None
        return CampaignDB._row_to_campaign_dict(row)

    @staticmethod
    def _row_to_campaign_dict(row) -> dict:
        """Convert a vault_campaigns row to a dict."""
        turn_order_raw = row[4]
        try:
            turn_order = json.loads(turn_order_raw) if turn_order_raw else []
        except (json.JSONDecodeError, TypeError):
            turn_order = []

        return {
            "id": row[0],
            "guild_id": row[1],
            "channel_id": row[2],
            "status": row[3],
            "turn_order": turn_order,
            "current_turn_index": row[5],
            "current_round": row[6],
            "last_message_id": row[7],
            "last_inventory_message_id": row[8],
            "created_at": row[9],
            "ended_at": row[10],
        }