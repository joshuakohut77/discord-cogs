from __future__ import annotations

import logging
from typing import Optional

from .dbclass import db as dbconn

log = logging.getLogger("red.chodecoin.db")


class ChodeCoinDB:
    """High-level database operations for ChodeCoin.

    All public methods are synchronous — the cog wraps them in
    asyncio.to_thread() so the bot loop is never blocked.
    """

    # ------------------------------------------------------------------
    # Schema bootstrap
    # ------------------------------------------------------------------

    @staticmethod
    def create_tables() -> None:
        """Create tables and indexes if they don't exist."""
        database = dbconn()

        database.execute("""
            CREATE TABLE IF NOT EXISTS chodecoin_wallets (
                "Id"         SERIAL PRIMARY KEY,
                "GuildId"    VARCHAR(255) NOT NULL,
                "UserId"     VARCHAR(255) NOT NULL,
                "Balance"    INTEGER NOT NULL DEFAULT 0,
                "IsActive"   BOOLEAN NOT NULL DEFAULT TRUE,
                "CreatedAt"  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "UpdatedAt"  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE ("GuildId", "UserId")
            );
        """)

        database.execute("""
            CREATE TABLE IF NOT EXISTS chodecoin_transactions (
                "Id"           SERIAL PRIMARY KEY,
                "GuildId"      VARCHAR(255) NOT NULL,
                "UserId"       VARCHAR(255) NOT NULL,
                "ActorId"      VARCHAR(255) NOT NULL,
                "Type"         VARCHAR(50) NOT NULL,
                "Amount"       INTEGER NOT NULL,
                "BalanceAfter" INTEGER NOT NULL,
                "Note"         TEXT,
                "CreatedAt"    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        database.execute("""
            CREATE TABLE IF NOT EXISTS chodecoin_stats (
                "Id"               SERIAL PRIMARY KEY,
                "GuildId"          VARCHAR(255) NOT NULL,
                "UserId"           VARCHAR(255) NOT NULL,
                "IncrementsGiven"  INTEGER NOT NULL DEFAULT 0,
                "IncrementsRecv"   INTEGER NOT NULL DEFAULT 0,
                "DecrementsGiven"  INTEGER NOT NULL DEFAULT 0,
                "DecrementsRecv"   INTEGER NOT NULL DEFAULT 0,
                "GiftsSent"        INTEGER NOT NULL DEFAULT 0,
                "GiftsSentTotal"   INTEGER NOT NULL DEFAULT 0,
                "GiftsRecv"        INTEGER NOT NULL DEFAULT 0,
                "GiftsRecvTotal"   INTEGER NOT NULL DEFAULT 0,
                UNIQUE ("GuildId", "UserId")
            );
        """)

        for idx in [
            'CREATE INDEX IF NOT EXISTS idx_cc_wallets_guild_user ON chodecoin_wallets("GuildId", "UserId");',
            'CREATE INDEX IF NOT EXISTS idx_cc_tx_guild_user ON chodecoin_transactions("GuildId", "UserId");',
            'CREATE INDEX IF NOT EXISTS idx_cc_tx_guild_actor ON chodecoin_transactions("GuildId", "ActorId");',
            'CREATE INDEX IF NOT EXISTS idx_cc_stats_guild_user ON chodecoin_stats("GuildId", "UserId");',
        ]:
            database.execute(idx)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_wallet(guild_id: int, user_id: int) -> None:
        database = dbconn()
        database.execute(
            """
            INSERT INTO chodecoin_wallets ("GuildId", "UserId")
            VALUES (%(guild_id)s, %(user_id)s)
            ON CONFLICT ("GuildId", "UserId") DO NOTHING
            """,
            {"guild_id": str(guild_id), "user_id": str(user_id)},
        )

    @staticmethod
    def _ensure_stats(guild_id: int, user_id: int) -> None:
        database = dbconn()
        database.execute(
            """
            INSERT INTO chodecoin_stats ("GuildId", "UserId")
            VALUES (%(guild_id)s, %(user_id)s)
            ON CONFLICT ("GuildId", "UserId") DO NOTHING
            """,
            {"guild_id": str(guild_id), "user_id": str(user_id)},
        )

    @staticmethod
    def _update_balance(
        guild_id: int,
        user_id: int,
        delta: int,
        actor_id: int,
        tx_type: str,
        note: Optional[str] = None,
    ) -> int:
        """Update balance, log transaction, return new balance."""
        database = dbconn()
        ChodeCoinDB._ensure_wallet(guild_id, user_id)

        database.execute(
            """
            UPDATE chodecoin_wallets
            SET "Balance" = "Balance" + %(delta)s, "UpdatedAt" = CURRENT_TIMESTAMP
            WHERE "GuildId" = %(guild_id)s AND "UserId" = %(user_id)s AND "IsActive" = TRUE
            """,
            {"delta": delta, "guild_id": str(guild_id), "user_id": str(user_id)},
        )

        row = database.querySingle(
            'SELECT "Balance" FROM chodecoin_wallets WHERE "GuildId" = %(guild_id)s AND "UserId" = %(user_id)s',
            {"guild_id": str(guild_id), "user_id": str(user_id)},
        )
        new_balance = row[0] if row else 0

        database.execute(
            """
            INSERT INTO chodecoin_transactions
                ("GuildId", "UserId", "ActorId", "Type", "Amount", "BalanceAfter", "Note")
            VALUES (%(guild_id)s, %(user_id)s, %(actor_id)s, %(type)s, %(amount)s, %(balance_after)s, %(note)s)
            """,
            {
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "actor_id": str(actor_id),
                "type": tx_type,
                "amount": delta,
                "balance_after": new_balance,
                "note": note,
            },
        )

        return new_balance

    # ------------------------------------------------------------------
    # Public mutation methods
    # ------------------------------------------------------------------

    @staticmethod
    def increment(guild_id: int, target_id: int, actor_id: int) -> int:
        """Give +1 ChodeCoin via ++. Returns new balance."""
        ChodeCoinDB._ensure_stats(guild_id, actor_id)
        ChodeCoinDB._ensure_stats(guild_id, target_id)

        new_bal = ChodeCoinDB._update_balance(
            guild_id, target_id, 1, actor_id, "increment"
        )

        database = dbconn()
        database.execute(
            'UPDATE chodecoin_stats SET "IncrementsGiven" = "IncrementsGiven" + 1 WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s',
            {"gid": str(guild_id), "uid": str(actor_id)},
        )
        database.execute(
            'UPDATE chodecoin_stats SET "IncrementsRecv" = "IncrementsRecv" + 1 WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s',
            {"gid": str(guild_id), "uid": str(target_id)},
        )
        return new_bal

    @staticmethod
    def decrement(guild_id: int, target_id: int, actor_id: int) -> int:
        """Remove 1 ChodeCoin via --. Returns new balance."""
        ChodeCoinDB._ensure_stats(guild_id, actor_id)
        ChodeCoinDB._ensure_stats(guild_id, target_id)

        new_bal = ChodeCoinDB._update_balance(
            guild_id, target_id, -1, actor_id, "decrement"
        )

        database = dbconn()
        database.execute(
            'UPDATE chodecoin_stats SET "DecrementsGiven" = "DecrementsGiven" + 1 WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s',
            {"gid": str(guild_id), "uid": str(actor_id)},
        )
        database.execute(
            'UPDATE chodecoin_stats SET "DecrementsRecv" = "DecrementsRecv" + 1 WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s',
            {"gid": str(guild_id), "uid": str(target_id)},
        )
        return new_bal

    @staticmethod
    def gift(guild_id: int, sender_id: int, recipient_id: int, amount: int) -> tuple:
        """Transfer coins. Returns (sender_balance, recipient_balance)."""
        sender_bal = ChodeCoinDB.get_balance(guild_id, sender_id)
        if sender_bal < amount:
            raise ValueError(f"Insufficient funds: you have **{sender_bal}** CC but need **{amount}**.")

        ChodeCoinDB._ensure_stats(guild_id, sender_id)
        ChodeCoinDB._ensure_stats(guild_id, recipient_id)

        new_sender = ChodeCoinDB._update_balance(
            guild_id, sender_id, -amount, sender_id, "gift",
            note=f"gift to {recipient_id}",
        )
        new_recipient = ChodeCoinDB._update_balance(
            guild_id, recipient_id, amount, sender_id, "gift",
            note=f"gift from {sender_id}",
        )

        database = dbconn()
        database.execute(
            """UPDATE chodecoin_stats
               SET "GiftsSent" = "GiftsSent" + 1, "GiftsSentTotal" = "GiftsSentTotal" + %(amt)s
               WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s""",
            {"amt": amount, "gid": str(guild_id), "uid": str(sender_id)},
        )
        database.execute(
            """UPDATE chodecoin_stats
               SET "GiftsRecv" = "GiftsRecv" + 1, "GiftsRecvTotal" = "GiftsRecvTotal" + %(amt)s
               WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s""",
            {"amt": amount, "gid": str(guild_id), "uid": str(recipient_id)},
        )
        return new_sender, new_recipient

    @staticmethod
    def admin_set_balance(guild_id: int, user_id: int, amount: int, admin_id: int) -> int:
        """Set exact balance. Returns new balance."""
        current = ChodeCoinDB.get_balance(guild_id, user_id)
        delta = amount - current
        return ChodeCoinDB._update_balance(
            guild_id, user_id, delta, admin_id, "admin_set",
            note=f"set to {amount} by admin",
        )

    @staticmethod
    def soft_reset(guild_id: int, admin_id: int) -> int:
        """Soft-reset all wallets in a guild. Returns count affected."""
        database = dbconn()
        rows = database.queryAll(
            'SELECT "UserId", "Balance" FROM chodecoin_wallets WHERE "GuildId" = %(gid)s AND "IsActive" = TRUE AND "Balance" != 0',
            {"gid": str(guild_id)},
        )

        for user_id, balance in rows:
            database.execute(
                """INSERT INTO chodecoin_transactions
                    ("GuildId", "UserId", "ActorId", "Type", "Amount", "BalanceAfter", "Note")
                   VALUES (%(gid)s, %(uid)s, %(aid)s, 'admin_reset', %(amt)s, 0, 'guild reset')""",
                {"gid": str(guild_id), "uid": user_id, "aid": str(admin_id), "amt": -balance},
            )

        database.execute(
            """UPDATE chodecoin_wallets
               SET "Balance" = 0, "IsActive" = FALSE, "UpdatedAt" = CURRENT_TIMESTAMP
               WHERE "GuildId" = %(gid)s AND "IsActive" = TRUE""",
            {"gid": str(guild_id)},
        )
        return len(rows)

    @staticmethod
    def soft_reset_user(guild_id: int, user_id: int, admin_id: int) -> None:
        """Soft-reset a single user's wallet."""
        database = dbconn()
        current = ChodeCoinDB.get_balance(guild_id, user_id)

        if current != 0:
            database.execute(
                """INSERT INTO chodecoin_transactions
                    ("GuildId", "UserId", "ActorId", "Type", "Amount", "BalanceAfter", "Note")
                   VALUES (%(gid)s, %(uid)s, %(aid)s, 'admin_reset', %(amt)s, 0, 'user reset')""",
                {"gid": str(guild_id), "uid": str(user_id), "aid": str(admin_id), "amt": -current},
            )

        database.execute(
            """UPDATE chodecoin_wallets
               SET "Balance" = 0, "IsActive" = FALSE, "UpdatedAt" = CURRENT_TIMESTAMP
               WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s""",
            {"gid": str(guild_id), "uid": str(user_id)},
        )

    # ------------------------------------------------------------------
    # Read queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_balance(guild_id: int, user_id: int) -> int:
        ChodeCoinDB._ensure_wallet(guild_id, user_id)
        database = dbconn()
        row = database.querySingle(
            'SELECT "Balance" FROM chodecoin_wallets WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s AND "IsActive" = TRUE',
            {"gid": str(guild_id), "uid": str(user_id)},
        )
        return row[0] if row else 0

    @staticmethod
    def leaderboard(guild_id: int, limit: int = 10) -> list:
        database = dbconn()
        return database.queryAll(
            """SELECT "UserId", "Balance" FROM chodecoin_wallets
               WHERE "GuildId" = %(gid)s AND "IsActive" = TRUE
               ORDER BY "Balance" DESC LIMIT %(limit)s""",
            {"gid": str(guild_id), "limit": limit},
        )

    @staticmethod
    def get_stats(guild_id: int, user_id: int) -> dict:
        ChodeCoinDB._ensure_stats(guild_id, user_id)
        database = dbconn()
        row = database.querySingle(
            'SELECT * FROM chodecoin_stats WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s',
            {"gid": str(guild_id), "uid": str(user_id)},
        )
        if not row:
            return {}
        keys = [
            "id", "guild_id", "user_id",
            "increments_given", "increments_recv",
            "decrements_given", "decrements_recv",
            "gifts_sent", "gifts_sent_total",
            "gifts_recv", "gifts_recv_total",
        ]
        return dict(zip(keys, row))

    @staticmethod
    def get_rank(guild_id: int, user_id: int) -> Optional[int]:
        ChodeCoinDB._ensure_wallet(guild_id, user_id)
        database = dbconn()
        row = database.querySingle(
            """SELECT COUNT(*) + 1 FROM chodecoin_wallets
               WHERE "GuildId" = %(gid)s AND "IsActive" = TRUE AND "Balance" > (
                   SELECT COALESCE("Balance", 0) FROM chodecoin_wallets
                   WHERE "GuildId" = %(gid)s AND "UserId" = %(uid)s
               )""",
            {"gid": str(guild_id), "uid": str(user_id)},
        )
        return row[0] if row else None
