"""
Pokemon TCG — Card Trading System

Trade flow:
    1. Player1 browses collection → clicks "Trade" on a card with count ≥ 1
    2. Player1 picks a recipient from a dropdown of other players → confirms
    3. Player2 receives a DM: "<Player1> wants to trade you <card>! Use !tcg trade in the server."
    4. Player2 uses !tcg trade → sees the offer → browses their own collection to pick a counter-card
    5. Player1 receives a DM: "<Player2> offers <card> for your <card>! Use !tcg trade in the server."
    6. Player1 uses !tcg trade → sees both cards → Accept / Decline
    7. On accept: cards swap in DB. On decline/cancel: trade cancelled.

Constraints:
    - One pending trade per player at a time (as initiator OR recipient).
    - Either player can cancel at any point.
    - Cross-set trades allowed.
    - Players can trade their last copy of a card.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from .main import PokemonTCG

log = logging.getLogger("red.pokemontcg.trade")


# ═══════════════════════════════════════════════════════════
#  URL helpers (mirror main.py conventions)
# ═══════════════════════════════════════════════════════════

ASSET_BASE_URL = "https://pokesprites.joshkohut.com/pokemon_tcgd"


def card_image_url(card_data: dict) -> str | None:
    """Return the CDN image URL for a card — must match main.py exactly."""
    image_file = card_data.get("image_file")
    if image_file:
        return f"{ASSET_BASE_URL}/{image_file}"
    return None


# ═══════════════════════════════════════════════════════════
#  Database helpers
# ═══════════════════════════════════════════════════════════

def get_pending_trade(database, user_id: int, guild_id: int) -> dict | None:
    """
    Return the user's active pending trade (as initiator or recipient), or None.
    Returns a dict with all trade columns.
    """
    row = database.querySingle(
        """
        SELECT id, guild_id, initiator_id, offered_card_id, offered_set_id,
               offered_card_name, offered_rarity, offered_is_holo,
               recipient_id, counter_card_id, counter_set_id,
               counter_card_name, counter_rarity, counter_is_holo,
               status, created_at, updated_at
        FROM tcg_trades
        WHERE guild_id = %(guild_id)s
          AND status IN ('pending_recipient', 'pending_initiator')
          AND (initiator_id = %(user_id)s OR recipient_id = %(user_id)s)
        ORDER BY created_at DESC
        LIMIT 1
        """,
        {"user_id": user_id, "guild_id": guild_id},
    )
    if not row:
        return None

    return {
        "id": row[0], "guild_id": row[1],
        "initiator_id": row[2], "offered_card_id": row[3], "offered_set_id": row[4],
        "offered_card_name": row[5], "offered_rarity": row[6], "offered_is_holo": row[7],
        "recipient_id": row[8], "counter_card_id": row[9], "counter_set_id": row[10],
        "counter_card_name": row[11], "counter_rarity": row[12], "counter_is_holo": row[13],
        "status": row[14], "created_at": row[15], "updated_at": row[16],
    }


def create_trade(
    database,
    guild_id: int,
    initiator_id: int,
    recipient_id: int,
    card_data: dict,
) -> int | None:
    """
    Insert a new trade in 'pending_recipient' status.
    Returns the trade ID.
    """
    result = database.executeAndReturn(
        """
        INSERT INTO tcg_trades
            (guild_id, initiator_id, recipient_id,
             offered_card_id, offered_set_id, offered_card_name,
             offered_rarity, offered_is_holo)
        VALUES
            (%(guild_id)s, %(initiator_id)s, %(recipient_id)s,
             %(card_id)s, %(set_id)s, %(card_name)s,
             %(rarity)s, %(is_holo)s)
        RETURNING id
        """,
        {
            "guild_id": guild_id,
            "initiator_id": initiator_id,
            "recipient_id": recipient_id,
            "card_id": card_data.get("id"),
            "set_id": card_data.get("set_id"),
            "card_name": card_data.get("name", "Unknown"),
            "rarity": card_data.get("rarity"),
            "is_holo": card_data.get("is_holo", False),
        },
    )
    return result[0] if result else None


def set_counter_offer(database, trade_id: int, card_data: dict):
    """Player2 picks their counter-card → status becomes 'pending_initiator'."""
    database.execute(
        """
        UPDATE tcg_trades
        SET counter_card_id = %(card_id)s,
            counter_set_id  = %(set_id)s,
            counter_card_name = %(card_name)s,
            counter_rarity  = %(rarity)s,
            counter_is_holo = %(is_holo)s,
            status = 'pending_initiator',
            updated_at = NOW()
        WHERE id = %(trade_id)s
        """,
        {
            "trade_id": trade_id,
            "card_id": card_data.get("id"),
            "set_id": card_data.get("set_id"),
            "card_name": card_data.get("name", "Unknown"),
            "rarity": card_data.get("rarity"),
            "is_holo": card_data.get("is_holo", False),
        },
    )


def cancel_trade(database, trade_id: int):
    """Cancel a trade (either player can do this)."""
    database.execute(
        """
        UPDATE tcg_trades
        SET status = 'cancelled', updated_at = NOW()
        WHERE id = %(trade_id)s
          AND status IN ('pending_recipient', 'pending_initiator')
        """,
        {"trade_id": trade_id},
    )


def complete_trade(database, trade: dict) -> bool:
    """
    Execute the card swap atomically:
    1. Transfer one copy of offered_card from initiator → recipient
    2. Transfer one copy of counter_card from recipient → initiator
    3. Mark trade as completed

    We swap by deleting ONE row from each player and inserting a new row
    for the other player. This preserves pack_open_id history on the original
    row and creates a clean new row for the new owner.

    Returns True on success, False on failure.
    """
    try:
        # Step 1: Find one row of the offered card from the initiator
        offered_row = database.querySingle(
            """
            SELECT id, card_id, set_id, card_name, rarity, category, is_holo, pack_open_id
            FROM tcg_user_cards
            WHERE user_id = %(user_id)s
              AND guild_id = %(guild_id)s
              AND card_id = %(card_id)s
            LIMIT 1
            """,
            {
                "user_id": trade["initiator_id"],
                "guild_id": trade["guild_id"],
                "card_id": trade["offered_card_id"],
            },
        )
        if not offered_row:
            log.error(f"Trade {trade['id']}: initiator no longer has offered card {trade['offered_card_id']}")
            return False

        # Step 2: Find one row of the counter card from the recipient
        counter_row = database.querySingle(
            """
            SELECT id, card_id, set_id, card_name, rarity, category, is_holo, pack_open_id
            FROM tcg_user_cards
            WHERE user_id = %(user_id)s
              AND guild_id = %(guild_id)s
              AND card_id = %(card_id)s
            LIMIT 1
            """,
            {
                "user_id": trade["recipient_id"],
                "guild_id": trade["guild_id"],
                "card_id": trade["counter_card_id"],
            },
        )
        if not counter_row:
            log.error(f"Trade {trade['id']}: recipient no longer has counter card {trade['counter_card_id']}")
            return False

        offered_row_id = offered_row[0]
        counter_row_id = counter_row[0]

        # Step 3: Swap ownership by updating user_id on each row
        database.execute(
            """
            UPDATE tcg_user_cards SET user_id = %(new_owner)s WHERE id = %(row_id)s
            """,
            {"new_owner": trade["recipient_id"], "row_id": offered_row_id},
        )
        database.execute(
            """
            UPDATE tcg_user_cards SET user_id = %(new_owner)s WHERE id = %(row_id)s
            """,
            {"new_owner": trade["initiator_id"], "row_id": counter_row_id},
        )

        # Step 4: Mark trade completed
        database.execute(
            """
            UPDATE tcg_trades SET status = 'completed', updated_at = NOW()
            WHERE id = %(trade_id)s
            """,
            {"trade_id": trade["id"]},
        )

        return True

    except Exception as e:
        log.error(f"Trade {trade['id']} execution failed: {e}")
        return False


def get_completed_trade_counts(database, guild_id: int) -> dict[int, int]:
    """
    Return {user_id: trade_count} for all users in the guild.
    Counts both initiator and recipient sides.
    """
    rows = database.queryAll(
        """
        SELECT user_id, COUNT(*) as cnt FROM (
            SELECT initiator_id AS user_id FROM tcg_trades
            WHERE guild_id = %(guild_id)s AND status = 'completed'
            UNION ALL
            SELECT recipient_id AS user_id FROM tcg_trades
            WHERE guild_id = %(guild_id)s AND status = 'completed'
        ) t
        GROUP BY user_id
        """,
        {"guild_id": guild_id},
    )
    return {row[0]: row[1] for row in rows}


def get_other_players(database, user_id: int, guild_id: int) -> list[int]:
    """Return user_ids of other players who have cards in this guild."""
    rows = database.queryAll(
        """
        SELECT DISTINCT user_id
        FROM tcg_user_cards
        WHERE guild_id = %(guild_id)s
          AND user_id != %(user_id)s
        ORDER BY user_id
        """,
        {"user_id": user_id, "guild_id": guild_id},
    )
    return [row[0] for row in rows]


def user_has_card(database, user_id: int, guild_id: int, card_id: str) -> bool:
    """Check if a user still owns at least one copy of a card."""
    row = database.querySingle(
        """
        SELECT COUNT(*) FROM tcg_user_cards
        WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s AND card_id = %(card_id)s
        """,
        {"user_id": user_id, "guild_id": guild_id, "card_id": card_id},
    )
    return row and row[0] > 0


# ═══════════════════════════════════════════════════════════
#  Embed builders
# ═══════════════════════════════════════════════════════════

RARITY_COLORS = {
    "rare holo": 0xFFD700,
    "rare": 0xF59E0B,
    "uncommon": 0x3B82F6,
    "common": 0x8B8B8B,
    "energy": 0x10B981,
}


def _card_color(rarity: str | None, is_holo: bool) -> int:
    if is_holo:
        return RARITY_COLORS["rare holo"]
    key = (rarity or "common").lower()
    return RARITY_COLORS.get(key, 0x8B8B8B)


def build_trade_offer_dm_embed(
    initiator_name: str,
    card_data: dict,
    guild_name: str,
) -> discord.Embed:
    """DM embed sent to Player2 when Player1 initiates a trade."""
    name = card_data.get("name", "Unknown")
    rarity = card_data.get("rarity") or "Unknown"
    is_holo = card_data.get("is_holo", False)
    holo_tag = " ✨ HOLO" if is_holo else ""
    set_name = card_data.get("set_name") or card_data.get("set_id", "Unknown")

    embed = discord.Embed(
        title="🔄 Incoming Trade Offer!",
        description=(
            f"**{initiator_name}** wants to trade you this card:\n\n"
            f"**{name}{holo_tag}**\n"
            f"{set_name} • {rarity}\n\n"
            f"Head to **{guild_name}** and use `!tcg trade` to pick a card to offer back, "
            f"or cancel the trade."
        ),
        color=_card_color(rarity, is_holo),
    )

    image = card_image_url(card_data)
    if image:
        embed.set_image(url=image)

    embed.set_footer(text="You can also cancel with !tcg trade → Cancel")
    return embed


def build_counter_offer_dm_embed(
    recipient_name: str,
    offered_card: dict,
    counter_card: dict,
    guild_name: str,
) -> discord.Embed:
    """DM embed sent to Player1 when Player2 picks a counter-card."""
    o_name = offered_card.get("name", "Unknown")
    o_holo = " ✨" if offered_card.get("is_holo") else ""
    c_name = counter_card.get("name", "Unknown")
    c_holo = " ✨" if counter_card.get("is_holo") else ""
    c_rarity = counter_card.get("rarity") or "Unknown"
    c_set = counter_card.get("set_name") or counter_card.get("set_id", "Unknown")

    embed = discord.Embed(
        title="🔄 Trade Counter-Offer!",
        description=(
            f"**{recipient_name}** wants to trade you:\n\n"
            f"**{c_name}{c_holo}**\n"
            f"{c_set} • {c_rarity}\n\n"
            f"In exchange for your **{o_name}{o_holo}**\n\n"
            f"Head to **{guild_name}** and use `!tcg trade` to accept or decline."
        ),
        color=_card_color(c_rarity, counter_card.get("is_holo", False)),
    )

    image = card_image_url(counter_card)
    if image:
        embed.set_image(url=image)

    # Show the offered card (what you'd give up) as thumbnail
    offered_img = card_image_url(offered_card)
    if offered_img:
        embed.set_thumbnail(url=offered_img)

    embed.set_footer(text="🖼️ Large = what you'd receive • Thumbnail = what you'd give up")
    return embed


def build_trade_review_embed(trade: dict, card_pool, viewer_id: int) -> discord.Embed:
    """
    Build the embed shown when a player uses !tcg trade and has an active trade.
    Shows different info depending on trade status and who is viewing.
    """
    status = trade["status"]
    is_initiator = (viewer_id == trade["initiator_id"])

    if status == "pending_recipient" and is_initiator:
        # Initiator waiting for recipient to pick a card
        embed = discord.Embed(
            title="🔄 Trade — Waiting for Response",
            description=(
                f"You offered **{trade['offered_card_name']}**"
                f"{'  ✨' if trade['offered_is_holo'] else ''}\n"
                f"to <@{trade['recipient_id']}>\n\n"
                f"Waiting for them to pick a card to trade back..."
            ),
            color=0xF59E0B,
        )
        # Show offered card image
        offered_data = card_pool.cards_by_id.get(trade["offered_card_id"]) if card_pool else None
        if offered_data:
            img = card_image_url(offered_data)
            if img:
                embed.set_image(url=img)
        embed.set_footer(text="You can cancel this trade at any time")
        return embed

    elif status == "pending_recipient" and not is_initiator:
        # Recipient needs to pick a counter-card
        embed = discord.Embed(
            title="🔄 Trade — Pick Your Offer",
            description=(
                f"<@{trade['initiator_id']}> wants to trade you:\n\n"
                f"**{trade['offered_card_name']}**"
                f"{'  ✨' if trade['offered_is_holo'] else ''}\n\n"
                f"Browse your collection below and click **Offer This Card** "
                f"to send a counter-offer, or cancel."
            ),
            color=0x3B82F6,
        )
        offered_data = card_pool.cards_by_id.get(trade["offered_card_id"]) if card_pool else None
        if offered_data:
            img = card_image_url(offered_data)
            if img:
                embed.set_image(url=img)
        embed.set_footer(text="Navigate your collection and offer a card back")
        return embed

    elif status == "pending_initiator" and is_initiator:
        # Initiator reviews the counter-offer — show BOTH cards
        embed = discord.Embed(
            title="🔄 Trade — Review Counter-Offer",
            description=(
                f"<@{trade['recipient_id']}> offers:\n\n"
                f"**{trade['counter_card_name']}**"
                f"{'  ✨' if trade['counter_is_holo'] else ''}\n\n"
                f"In exchange for your:\n\n"
                f"**{trade['offered_card_name']}**"
                f"{'  ✨' if trade['offered_is_holo'] else ''}\n\n"
                f"Accept or decline this trade?"
            ),
            color=0x10B981,
        )
        # Counter-offer card = large image (what you'd receive)
        counter_data = card_pool.cards_by_id.get(trade["counter_card_id"]) if card_pool else None
        if counter_data:
            img = card_image_url(counter_data)
            if img:
                embed.set_image(url=img)
        # Your offered card = thumbnail (what you'd give up)
        offered_data = card_pool.cards_by_id.get(trade["offered_card_id"]) if card_pool else None
        if offered_data:
            img = card_image_url(offered_data)
            if img:
                embed.set_thumbnail(url=img)
        embed.set_footer(text="🖼️ Large = what you'd receive • Thumbnail = what you'd give up")
        return embed

    elif status == "pending_initiator" and not is_initiator:
        # Recipient waiting for initiator to accept/decline — show BOTH cards
        embed = discord.Embed(
            title="🔄 Trade — Waiting for Response",
            description=(
                f"You offered **{trade['counter_card_name']}**"
                f"{'  ✨' if trade['counter_is_holo'] else ''}\n"
                f"for <@{trade['initiator_id']}>'s "
                f"**{trade['offered_card_name']}**"
                f"{'  ✨' if trade['offered_is_holo'] else ''}\n\n"
                f"Waiting for them to accept or decline..."
            ),
            color=0xF59E0B,
        )
        # What you'd receive = large image (the offered card)
        offered_data = card_pool.cards_by_id.get(trade["offered_card_id"]) if card_pool else None
        if offered_data:
            img = card_image_url(offered_data)
            if img:
                embed.set_image(url=img)
        # What you offered = thumbnail (your counter card)
        counter_data = card_pool.cards_by_id.get(trade["counter_card_id"]) if card_pool else None
        if counter_data:
            img = card_image_url(counter_data)
            if img:
                embed.set_thumbnail(url=img)
        embed.set_footer(text="🖼️ Large = what you'd receive • Thumbnail = what you'd give up")
        return embed

    # Fallback
    return discord.Embed(
        title="🔄 Trade",
        description="No active trade found.",
        color=0x8B8B8B,
    )


def build_trade_complete_embed(trade: dict, accepted: bool, card_pool=None) -> discord.Embed:
    """Embed shown after a trade is accepted or declined."""
    if accepted:
        embed = discord.Embed(
            title="✅ Trade Complete!",
            description=(
                f"**{trade['offered_card_name']}**"
                f"{'  ✨' if trade['offered_is_holo'] else ''}"
                f" ⇄ "
                f"**{trade['counter_card_name']}**"
                f"{'  ✨' if trade['counter_is_holo'] else ''}\n\n"
                f"<@{trade['initiator_id']}> received **{trade['counter_card_name']}**\n"
                f"<@{trade['recipient_id']}> received **{trade['offered_card_name']}**"
            ),
            color=0x10B981,
        )
        # Show both cards: counter as main image, offered as thumbnail
        if card_pool:
            counter_data = card_pool.cards_by_id.get(trade.get("counter_card_id"))
            if counter_data:
                img = card_image_url(counter_data)
                if img:
                    embed.set_image(url=img)
            offered_data = card_pool.cards_by_id.get(trade.get("offered_card_id"))
            if offered_data:
                img = card_image_url(offered_data)
                if img:
                    embed.set_thumbnail(url=img)
    else:
        embed = discord.Embed(
            title="❌ Trade Cancelled",
            description=(
                f"The trade between <@{trade['initiator_id']}> and "
                f"<@{trade['recipient_id']}> has been cancelled.\n"
                f"All cards remain with their original owners."
            ),
            color=0xEF4444,
        )
    return embed


# ═══════════════════════════════════════════════════════════
#  Views (UI components)
# ═══════════════════════════════════════════════════════════

class RecipientSelectView(discord.ui.View):
    """
    Dropdown to pick which player to trade with, then confirm/cancel.
    Shown after Player1 clicks "Trade" on a card in their collection.

    Row 0: Player dropdown
    Row 1: Confirm / Cancel buttons
    """

    def __init__(
        self,
        cog: "PokemonTCG",
        author_id: int,
        guild_id: int,
        guild_name: str,
        card_data: dict,
        card_count: int,
        player_ids: list[int],
        timeout: float = 120,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.author_id = author_id
        self.guild_id = guild_id
        self.guild_name = guild_name
        self.card_data = card_data
        self.card_count = card_count
        self.selected_recipient: int | None = None
        self.message: discord.Message | None = None

        # Build player options — we'll resolve names in initialize()
        self.player_ids = player_ids

    async def initialize(self, guild: discord.Guild):
        """Resolve player IDs to display names and populate the dropdown."""
        options = []
        for uid in self.player_ids[:25]:  # Discord max 25 options
            member = guild.get_member(uid)
            if member:
                name = member.display_name
            else:
                try:
                    member = await guild.fetch_member(uid)
                    name = member.display_name
                except Exception:
                    name = f"User {uid}"
            options.append(discord.SelectOption(
                label=name[:100],
                value=str(uid),
            ))

        if not options:
            options = [discord.SelectOption(label="No players found", value="none")]

        self.player_select.options = options

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isn't your trade!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.select(placeholder="Choose a player to trade with...", row=0)
    async def player_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0]
        if val == "none":
            await interaction.response.send_message("No players available to trade with.", ephemeral=True)
            return
        self.selected_recipient = int(val)
        for opt in self.player_select.options:
            opt.default = (opt.value == val)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Confirm Trade", style=discord.ButtonStyle.success, emoji="✅", row=1)
    async def btn_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_recipient:
            await interaction.response.send_message("Pick a player first!", ephemeral=True)
            return

        if self.selected_recipient == self.author_id:
            await interaction.response.send_message("You can't trade with yourself!", ephemeral=True)
            return

        # Check neither player has a pending trade
        try:
            existing = get_pending_trade(self.cog.database, self.author_id, self.guild_id)
            if existing:
                await interaction.response.send_message(
                    "❌ You already have a pending trade! Cancel it first with `!tcg trade`.",
                    ephemeral=True,
                )
                return

            existing_recip = get_pending_trade(self.cog.database, self.selected_recipient, self.guild_id)
            if existing_recip:
                await interaction.response.send_message(
                    "❌ That player already has a pending trade. Try again later.",
                    ephemeral=True,
                )
                return

            # Verify initiator still has the card
            if not user_has_card(self.cog.database, self.author_id, self.guild_id, self.card_data.get("id")):
                await interaction.response.send_message(
                    "❌ You no longer have this card!",
                    ephemeral=True,
                )
                return

            # Create the trade
            trade_id = create_trade(
                self.cog.database,
                guild_id=self.guild_id,
                initiator_id=self.author_id,
                recipient_id=self.selected_recipient,
                card_data=self.card_data,
            )

            if not trade_id:
                await interaction.response.send_message("❌ Failed to create trade.", ephemeral=True)
                return

        except Exception as e:
            log.error(f"Trade creation failed: {e}")
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
            return

        # Disable this view
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
        self.stop()

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Trade Offer Sent!",
                description=(
                    f"Sent trade offer to <@{self.selected_recipient}>.\n"
                    f"They'll receive a DM and can use `!tcg trade` to respond."
                ),
                color=0x10B981,
            ),
            view=self,
        )

        # Send DM to recipient
        try:
            guild = interaction.guild
            recipient_member = guild.get_member(self.selected_recipient) if guild else None
            if not recipient_member and guild:
                recipient_member = await guild.fetch_member(self.selected_recipient)

            if recipient_member:
                initiator_name = interaction.user.display_name
                dm_embed = build_trade_offer_dm_embed(
                    initiator_name=initiator_name,
                    card_data=self.card_data,
                    guild_name=self.guild_name,
                )
                try:
                    await recipient_member.send(embed=dm_embed)
                except discord.Forbidden:
                    # Can't DM the user, they'll have to check !tcg trade
                    log.warning(f"Cannot DM user {self.selected_recipient} for trade {trade_id}")
        except Exception as e:
            log.error(f"Failed to send trade DM: {e}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌", row=1)
    async def btn_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(title="Trade Cancelled", color=0x8B8B8B),
            view=self,
        )


class TradeStatusView(discord.ui.View):
    """
    Shown when a player uses !tcg trade and has an active trade.
    Adapts buttons based on trade status and the viewer's role.

    - pending_recipient + viewer is recipient → "Browse Collection" + "Cancel"
    - pending_recipient + viewer is initiator → "Cancel" only (waiting)
    - pending_initiator + viewer is initiator → "Accept" + "Decline"
    - pending_initiator + viewer is recipient → "Cancel" only (waiting)
    """

    def __init__(
        self,
        cog: "PokemonTCG",
        trade: dict,
        viewer_id: int,
        guild_id: int,
        timeout: float = 300,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.trade = trade
        self.viewer_id = viewer_id
        self.guild_id = guild_id
        self.message: discord.Message | None = None

        is_initiator = (viewer_id == trade["initiator_id"])
        status = trade["status"]

        # Dynamically add buttons based on state
        if status == "pending_recipient" and not is_initiator:
            # Recipient can browse and pick a card, or cancel
            self.add_item(TradePickCardButton(cog, trade, viewer_id, guild_id))
            self.add_item(TradeCancelButton(cog, trade))
        elif status == "pending_initiator" and is_initiator:
            # Initiator can accept or decline
            self.add_item(TradeAcceptButton(cog, trade, guild_id))
            self.add_item(TradeDeclineButton(cog, trade))
        else:
            # Waiting state — can only cancel
            self.add_item(TradeCancelButton(cog, trade))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.viewer_id:
            await interaction.response.send_message("This isn't your trade!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class TradePickCardButton(discord.ui.Button):
    """Button for the recipient to browse their collection and pick a counter card."""

    def __init__(self, cog, trade, viewer_id, guild_id):
        super().__init__(
            label="Browse Collection & Pick Card",
            style=discord.ButtonStyle.primary,
            emoji="📂",
        )
        self.cog = cog
        self.trade = trade
        self.viewer_id = viewer_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        """Open a trade-specific collection viewer for the recipient."""
        viewer = TradeCollectionViewer(
            cog=self.cog,
            trade=self.trade,
            author_id=self.viewer_id,
            guild_id=self.guild_id,
            display_name=interaction.user.display_name,
        )
        await viewer.initialize()
        embed = viewer.get_embed()

        # Disable the parent view
        for item in self.view.children:
            if hasattr(item, "disabled"):
                item.disabled = True
        self.view.stop()

        await interaction.response.edit_message(embed=embed, view=viewer)
        viewer.message = self.view.message


class TradeAcceptButton(discord.ui.Button):
    """Button for the initiator to accept the counter-offer."""

    def __init__(self, cog, trade, guild_id):
        super().__init__(
            label="Accept Trade",
            style=discord.ButtonStyle.success,
            emoji="✅",
        )
        self.cog = cog
        self.trade = trade
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        # Verify both players still have their cards
        if not user_has_card(self.cog.database, self.trade["initiator_id"], self.guild_id, self.trade["offered_card_id"]):
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="❌ Trade Failed",
                    description="You no longer have the offered card!",
                    color=0xEF4444,
                ),
                view=None,
            )
            cancel_trade(self.cog.database, self.trade["id"])
            return

        if not user_has_card(self.cog.database, self.trade["recipient_id"], self.guild_id, self.trade["counter_card_id"]):
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="❌ Trade Failed",
                    description="The other player no longer has their offered card!",
                    color=0xEF4444,
                ),
                view=None,
            )
            cancel_trade(self.cog.database, self.trade["id"])
            return

        # Execute the swap
        success = complete_trade(self.cog.database, self.trade)
        if success:
            embed = build_trade_complete_embed(self.trade, accepted=True, card_pool=self.cog.card_pool)
            await interaction.response.edit_message(embed=embed, view=None)

            # Notify the recipient via DM
            try:
                guild = interaction.guild
                recipient = guild.get_member(self.trade["recipient_id"]) if guild else None
                if not recipient and guild:
                    recipient = await guild.fetch_member(self.trade["recipient_id"])
                if recipient:
                    try:
                        await recipient.send(embed=embed)
                    except discord.Forbidden:
                        pass
            except Exception as e:
                log.error(f"Failed to send trade completion DM: {e}")
        else:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="❌ Trade Failed",
                    description="Something went wrong executing the trade. Cards were not swapped.",
                    color=0xEF4444,
                ),
                view=None,
            )
            cancel_trade(self.cog.database, self.trade["id"])


class TradeDeclineButton(discord.ui.Button):
    """Button for the initiator to decline the counter-offer."""

    def __init__(self, cog, trade):
        super().__init__(
            label="Decline",
            style=discord.ButtonStyle.danger,
            emoji="❌",
        )
        self.cog = cog
        self.trade = trade

    async def callback(self, interaction: discord.Interaction):
        cancel_trade(self.cog.database, self.trade["id"])
        embed = build_trade_complete_embed(self.trade, accepted=False)
        await interaction.response.edit_message(embed=embed, view=None)

        # Notify the other player
        other_id = (
            self.trade["recipient_id"]
            if interaction.user.id == self.trade["initiator_id"]
            else self.trade["initiator_id"]
        )
        try:
            guild = interaction.guild
            other = guild.get_member(other_id) if guild else None
            if not other and guild:
                other = await guild.fetch_member(other_id)
            if other:
                try:
                    await other.send(embed=embed)
                except discord.Forbidden:
                    pass
        except Exception:
            pass


class TradeCancelButton(discord.ui.Button):
    """Generic cancel button — either player can use this."""

    def __init__(self, cog, trade):
        super().__init__(
            label="Cancel Trade",
            style=discord.ButtonStyle.danger,
            emoji="🚫",
        )
        self.cog = cog
        self.trade = trade

    async def callback(self, interaction: discord.Interaction):
        cancel_trade(self.cog.database, self.trade["id"])
        embed = build_trade_complete_embed(self.trade, accepted=False)
        await interaction.response.edit_message(embed=embed, view=None)

        # Notify the other player
        other_id = (
            self.trade["recipient_id"]
            if interaction.user.id == self.trade["initiator_id"]
            else self.trade["initiator_id"]
        )
        try:
            guild = interaction.guild
            other = guild.get_member(other_id) if guild else None
            if not other and guild:
                other = await guild.fetch_member(other_id)
            if other:
                try:
                    await other.send(embed=embed)
                except discord.Forbidden:
                    pass
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  Trade Collection Viewer
#  (Similar to the normal CollectionViewer but with an
#   "Offer This Card" button instead of "Show Summary")
# ═══════════════════════════════════════════════════════════

# We need these helpers from main — import at runtime to avoid circular imports
def _classify_rarity(rarity, is_holo, category):
    cat = (category or "").lower()
    if cat == "energy":
        return "Energy"
    r = (rarity or "").lower()
    if is_holo or r == "rare holo":
        return "Rare Holo"
    if "rare" in r:
        return "Rare"
    if r == "uncommon":
        return "Uncommon"
    return "Common"


def _natural_sort_key(card_id: str) -> tuple:
    parts = card_id.rsplit("-", 1)
    if len(parts) == 2:
        try:
            return (parts[0], int(parts[1]))
        except ValueError:
            return (parts[0], 0)
    return (card_id, 0)


RARITY_ORDER = ["Rare Holo", "Rare", "Uncommon", "Common", "Energy"]
RARITY_EMOJI = {
    "rare holo": "✨",
    "rare": "⭐",
    "uncommon": "🔷",
    "common": "⚪",
    "energy": "🔋",
}


def _build_trade_card_embed(
    card_data: dict, count: int, index: int, total: int,
    set_name: str, trade: dict,
) -> discord.Embed:
    """Build an embed for a card in the trade collection viewer."""
    name = card_data.get("name", "Unknown")
    rarity = card_data.get("rarity") or "Unknown"
    category = card_data.get("category") or "Unknown"
    is_holo = card_data.get("is_holo", False)
    local_id = card_data.get("local_id", "?")

    display_rarity = _classify_rarity(rarity, is_holo, category)
    emoji = RARITY_EMOJI.get(display_rarity.lower(), "")

    color = _card_color(rarity, is_holo)

    title = f"{emoji} {name}"
    if count > 1:
        title += f"  (×{count})"

    embed = discord.Embed(title=title, color=color)

    image = card_image_url(card_data)
    if image:
        embed.set_image(url=image)

    embed.set_footer(
        text=(
            f"#{local_id} • {set_name} • {category} • {display_rarity} • "
            f"Card {index + 1}/{total} • "
            f"Trading for: {trade['offered_card_name']}"
        )
    )
    return embed


class TradeCollectionViewer(discord.ui.View):
    """
    Browse collected cards to pick one to offer in a trade.

    Row 0: Set dropdown
    Row 1: Rarity dropdown
    Row 2: ◀  (position)  ▶
    Row 3: "Offer This Card" + "Cancel Trade"
    """

    def __init__(
        self,
        cog: "PokemonTCG",
        trade: dict,
        author_id: int,
        guild_id: int,
        display_name: str,
        timeout: float = 300,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.trade = trade
        self.author_id = author_id
        self.guild_id = guild_id
        self.display_name = display_name
        self.message: discord.Message | None = None

        self.selected_set_id: str | None = None
        self.selected_rarity: str = "All"
        self.filtered_cards: list[tuple[dict, int]] = []
        self.index: int = 0

    async def initialize(self):
        """Populate set dropdown and load first set's cards."""
        sets = self.cog.card_pool.get_available_sets()
        if not sets:
            return

        options = []
        for s in sets:
            options.append(discord.SelectOption(
                label=s["name"],
                value=s["set_id"],
                description=f"{s['total_in_set']} cards • {s['year']}",
                emoji=self._parse_emoji(s.get("emoji", "📦")),
            ))
        self.set_filter.options = options

        # Default to first set
        self.selected_set_id = sets[0]["set_id"]
        for opt in self.set_filter.options:
            opt.default = (opt.value == self.selected_set_id)
        await self._reload_cards()
        self._rebuild_rarity_options()
        self._update_nav_buttons()

    @staticmethod
    def _parse_emoji(emoji_str):
        """Parse custom emoji or return string."""
        import re
        match = re.fullmatch(r"<(a?):(\w+):(\d+)>", emoji_str)
        if match:
            return discord.PartialEmoji(
                name=match.group(2),
                id=int(match.group(3)),
                animated=bool(match.group(1)),
            )
        return emoji_str

    async def _reload_cards(self):
        if not self.selected_set_id:
            self.filtered_cards = []
            return

        try:
            rows = self.cog.database.queryAll(
                """
                SELECT card_id, card_name, rarity, category, is_holo, COUNT(*) as cnt
                FROM tcg_user_cards
                WHERE user_id = %(user_id)s
                  AND guild_id = %(guild_id)s
                  AND set_id = %(set_id)s
                GROUP BY card_id, card_name, rarity, category, is_holo
                ORDER BY card_id
                """,
                {
                    "user_id": self.author_id,
                    "guild_id": self.guild_id,
                    "set_id": self.selected_set_id,
                },
            )
        except Exception as e:
            log.error(f"Trade collection query failed: {e}")
            self.filtered_cards = []
            return

        all_cards = []
        for row in rows:
            card_id, card_name, rarity, category, is_holo, count = row
            card_data = self.cog.card_pool.cards_by_id.get(card_id)
            if not card_data:
                card_data = {
                    "id": card_id,
                    "local_id": card_id.rsplit("-", 1)[-1] if "-" in card_id else "0",
                    "name": card_name,
                    "set_id": self.selected_set_id,
                    "rarity": rarity,
                    "category": category,
                    "is_holo": is_holo,
                }
            display_rarity = _classify_rarity(rarity, is_holo, category)
            all_cards.append((card_data, count, display_rarity))

        if self.selected_rarity and self.selected_rarity != "All":
            all_cards = [
                (cd, cnt, dr) for cd, cnt, dr in all_cards
                if dr == self.selected_rarity
            ]

        all_cards.sort(key=lambda x: _natural_sort_key(x[0].get("id", "")))
        self.filtered_cards = [(cd, cnt) for cd, cnt, _ in all_cards]
        self.index = 0

    def _rebuild_rarity_options(self):
        options = [discord.SelectOption(
            label="All Rarities", value="All", emoji="📋",
            default=(self.selected_rarity == "All"),
        )]
        if self.selected_set_id:
            pool = self.cog.card_pool.sets.get(self.selected_set_id, {})
            available = set()
            if pool.get("rares_holo"):
                available.add("Rare Holo")
            if pool.get("rares_normal"):
                available.add("Rare")
            if pool.get("uncommons"):
                available.add("Uncommon")
            if pool.get("commons"):
                available.add("Common")
            if pool.get("energy"):
                available.add("Energy")
            for rn in RARITY_ORDER:
                if rn in available:
                    emoji = RARITY_EMOJI.get(rn.lower(), "•")
                    options.append(discord.SelectOption(
                        label=rn, value=rn, emoji=emoji,
                        default=(self.selected_rarity == rn),
                    ))
        self.rarity_filter.options = options

    def _update_nav_buttons(self):
        total = len(self.filtered_cards)
        if total == 0:
            self.btn_prev.disabled = True
            self.btn_next.disabled = True
            self.btn_pos.label = "0/0"
            self.btn_offer.disabled = True
        else:
            self.btn_prev.disabled = (self.index <= 0)
            self.btn_next.disabled = (self.index >= total - 1)
            self.btn_pos.label = f"{self.index + 1}/{total}"
            self.btn_offer.disabled = False

    def get_embed(self) -> discord.Embed:
        if not self.filtered_cards:
            config = self.cog.card_pool.pack_config.get(self.selected_set_id or "", {})
            set_name = config.get("name", self.selected_set_id or "Unknown")
            filter_text = f" ({self.selected_rarity})" if self.selected_rarity != "All" else ""
            return discord.Embed(
                title=f"🔄 Pick a Card to Trade",
                description=(
                    f"No cards in **{set_name}**{filter_text}.\n"
                    f"Try a different set or rarity filter."
                ),
                color=0x3B82F6,
            )

        card_data, count = self.filtered_cards[self.index]
        config = self.cog.card_pool.pack_config.get(self.selected_set_id or "", {})
        set_name = config.get("name", self.selected_set_id or "Unknown")

        return _build_trade_card_embed(
            card_data=card_data,
            count=count,
            index=self.index,
            total=len(self.filtered_cards),
            set_name=set_name,
            trade=self.trade,
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isn't your trade!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    # ── Row 0: Set filter ──
    @discord.ui.select(placeholder="Choose a set...", min_values=1, max_values=1, row=0)
    async def set_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_set_id = select.values[0]
        self.selected_rarity = "All"
        for opt in self.set_filter.options:
            opt.default = (opt.value == self.selected_set_id)
        await self._reload_cards()
        self._rebuild_rarity_options()
        self._update_nav_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    # ── Row 1: Rarity filter ──
    @discord.ui.select(placeholder="Filter by rarity...", min_values=1, max_values=1, row=1)
    async def rarity_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_rarity = select.values[0]
        for opt in self.rarity_filter.options:
            opt.default = (opt.value == self.selected_rarity)
        await self._reload_cards()
        self._update_nav_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    # ── Row 2: Navigation ──
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=2)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.filtered_cards:
            self.index = max(0, self.index - 1)
        self._update_nav_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="0/0", style=discord.ButtonStyle.primary, disabled=True, row=2)
    async def btn_pos(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=2)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.filtered_cards:
            self.index = min(len(self.filtered_cards) - 1, self.index + 1)
        self._update_nav_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    # ── Row 3: Offer + Cancel ──
    @discord.ui.button(label="Offer This Card", style=discord.ButtonStyle.success, emoji="🔄", row=3)
    async def btn_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.filtered_cards:
            await interaction.response.send_message("No card selected!", ephemeral=True)
            return

        card_data, count = self.filtered_cards[self.index]
        card_id = card_data.get("id")

        # Can't offer the same card they're getting
        if card_id == self.trade["offered_card_id"]:
            await interaction.response.send_message(
                "❌ You can't offer the same card they're trading to you!",
                ephemeral=True,
            )
            return

        # Verify still have it
        if not user_has_card(self.cog.database, self.author_id, self.guild_id, card_id):
            await interaction.response.send_message("❌ You no longer have this card!", ephemeral=True)
            return

        # Re-check the trade is still pending_recipient
        current_trade = get_pending_trade(self.cog.database, self.author_id, self.guild_id)
        if not current_trade or current_trade["id"] != self.trade["id"] or current_trade["status"] != "pending_recipient":
            await interaction.response.send_message("❌ This trade is no longer active.", ephemeral=True)
            return

        try:
            set_counter_offer(self.cog.database, self.trade["id"], card_data)
        except Exception as e:
            log.error(f"Setting counter-offer failed: {e}")
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
            return

        # Disable view
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
        self.stop()

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Counter-Offer Sent!",
                description=(
                    f"You offered **{card_data.get('name', 'Unknown')}** "
                    f"for <@{self.trade['initiator_id']}>'s "
                    f"**{self.trade['offered_card_name']}**.\n\n"
                    f"Waiting for them to accept or decline..."
                ),
                color=0x10B981,
            ),
            view=self,
        )

        # DM the initiator
        try:
            guild = interaction.guild
            initiator = guild.get_member(self.trade["initiator_id"]) if guild else None
            if not initiator and guild:
                initiator = await guild.fetch_member(self.trade["initiator_id"])

            if initiator:
                # Enrich card data with set_name for the embed
                enriched = dict(card_data)
                config = self.cog.card_pool.pack_config.get(card_data.get("set_id", ""), {})
                enriched["set_name"] = config.get("name", card_data.get("set_id", "Unknown"))

                offered_data = self.cog.card_pool.cards_by_id.get(self.trade["offered_card_id"], {})
                dm_embed = build_counter_offer_dm_embed(
                    recipient_name=interaction.user.display_name,
                    offered_card=offered_data,
                    counter_card=enriched,
                    guild_name=guild.name if guild else "the server",
                )
                try:
                    await initiator.send(embed=dm_embed)
                except discord.Forbidden:
                    pass
        except Exception as e:
            log.error(f"Failed to send counter-offer DM: {e}")

    @discord.ui.button(label="Cancel Trade", style=discord.ButtonStyle.danger, emoji="🚫", row=3)
    async def btn_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        cancel_trade(self.cog.database, self.trade["id"])

        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
        self.stop()

        embed = build_trade_complete_embed(self.trade, accepted=False)
        await interaction.response.edit_message(embed=embed, view=self)

        # Notify initiator
        try:
            guild = interaction.guild
            initiator = guild.get_member(self.trade["initiator_id"]) if guild else None
            if not initiator and guild:
                initiator = await guild.fetch_member(self.trade["initiator_id"])
            if initiator:
                try:
                    await initiator.send(embed=embed)
                except discord.Forbidden:
                    pass
        except Exception:
            pass