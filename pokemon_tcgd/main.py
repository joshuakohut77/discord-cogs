"""
Pokemon TCG Collector - Red Discord Bot Cog

Open booster packs from original Gen 1 era sets, collect cards,
and track your collection in PostgreSQL.
"""

import discord
from redbot.core import commands
from redbot.core.bot import Red
import asyncio
import logging
import os
import random
import urllib.parse
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from discord.ext import tasks
from .packopener import CardPool
from .dbclass import db

from .trade import (
    get_pending_trade,
    get_other_players,
    get_completed_trade_counts,
    build_trade_review_embed,
    RecipientSelectView,
    TradeStatusView,
)

from .showcase import (
      get_players_with_cards,
      ShowcasePlayerSelector,
  )

log = logging.getLogger("red.pokemontcg")


# ═══════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════

ASSET_BASE_URL = "https://pokesprites.joshkohut.com/pokemon_tcgd"

RARITY_COLORS = {
    "common":    0x8B8B8B,
    "uncommon":  0x3B82F6,
    "rare":      0xF59E0B,
    "rare holo": 0xEF4444,
    "energy":    0x10B981,
}

# Display order for rarity filter dropdown (top = most prestigious)
RARITY_ORDER = ["Rare Holo", "Rare", "Uncommon", "Common", "Energy"]

RARITY_EMOJI = {
    "rare holo": "✨",
    "rare":      "⭐",
    "uncommon":  "🔷",
    "common":    "⚪",
    "energy":    "🔋",
}

RIP_MESSAGES = [
    "You tear open the pack...",
    "You rip into the foil...",
    "The wrapper crinkles as you tear it open...",
    "You carefully peel the pack open...",
    "The foil glints as you rip it apart...",
]

# ── Pack allowance settings ──
PACKS_PER_DAY = 5           # Packs earned each day at midnight
MAX_PACK_BALANCE = 20       # Max banked packs (5 days × 2/day)
STARTING_BALANCE = 5        # Packs a brand new user starts with
RESET_TIMEZONE = ZoneInfo("America/New_York")  # Midnight Eastern


# ═══════════════════════════════════════════════════════════
#  URL helpers
# ═══════════════════════════════════════════════════════════

def card_image_url(card: dict) -> str | None:
    image_file = card.get("image_file")
    if image_file:
        return f"{ASSET_BASE_URL}/{image_file}"
    return None


def pack_art_url(set_id: str) -> str:
    return f"{ASSET_BASE_URL}/packart/{set_id}/display.png"


def set_logo_url(set_id: str) -> str:
    return f"{ASSET_BASE_URL}/packart/{set_id}/logo.png"


def wrapper_url(set_id: str, filename: str) -> str:
    encoded = urllib.parse.quote(filename)
    return f"{ASSET_BASE_URL}/packart/{set_id}/packs/{encoded}"


_CUSTOM_EMOJI_RE = re.compile(r"<(a?):(\w+):(\d+)>")


def parse_emoji(emoji_str: str) -> discord.PartialEmoji | str:
    """Convert a custom emoji string like <:base1:123456> into a
    discord.PartialEmoji, or return the original string if it's
    a standard Unicode emoji."""
    match = _CUSTOM_EMOJI_RE.fullmatch(emoji_str)
    if match:
        return discord.PartialEmoji(
            name=match.group(2),
            id=int(match.group(3)),
            animated=bool(match.group(1)),
        )
    return emoji_str


def _natural_sort_key(card_id: str) -> tuple:
    """Sort card IDs naturally: base1-1, base1-2, ... base1-10, base1-11.
    Extract the local_id numeric portion for proper ordering."""
    # card_id format is like "base1-77"
    parts = card_id.rsplit("-", 1)
    if len(parts) == 2:
        try:
            return (parts[0], int(parts[1]))
        except ValueError:
            return (parts[0], 0)
    return (card_id, 0)


def _classify_rarity(rarity: str | None, is_holo: bool, category: str | None) -> str:
    """Normalize a card's rarity into one of the standard display buckets."""
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


# ═══════════════════════════════════════════════════════════
#  Embed builders
# ═══════════════════════════════════════════════════════════

def build_welcome_embed(packs_remaining: int | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="<:pokemon_trading_card:1481844443127611444> Pokémon TCG Card Collector",
        description=(
            "Collect cards from the original Gen 1 Pokémon TCG sets!\n\n"
            "**Select a booster pack** from the menu below to get started."
        ),
        color=0xFFD700,
    )
    if packs_remaining is not None:
        embed.set_footer(text=f"📦 {packs_remaining} pack{'s' if packs_remaining != 1 else ''} remaining • Wizards of the Coast Era • 1999–2002")
    else:
        embed.set_footer(text="Wizards of the Coast Era • 1999–2002")
    return embed


def build_set_preview_embed(set_id: str, config: dict, packs_remaining: int | None = None) -> discord.Embed:
    name = config.get("name", set_id)
    emoji = config.get("emoji", "📦")
    desc = config.get("description", "")
    year = config.get("year", "")
    total = config.get("total_cards_in_set", "?")
    per_pack = config.get("cards_per_pack", 11)

    embed = discord.Embed(
        title=f"{emoji} {name}",
        description=desc,
        color=0xFFD700,
    )
    embed.set_image(url=pack_art_url(set_id))
    embed.set_thumbnail(url=set_logo_url(set_id))
    embed.add_field(name="Cards in Set", value=str(total), inline=True)
    embed.add_field(name="Per Pack", value=str(per_pack), inline=True)
    embed.add_field(name="Released", value=str(year), inline=True)
    if packs_remaining is not None:
        embed.set_footer(text=f"📦 {packs_remaining} pack{'s' if packs_remaining != 1 else ''} remaining • Hit Open Pack to rip it! 🔥")
    else:
        embed.set_footer(text="Hit Open Pack to rip it! 🔥")
    return embed


def build_rip_embed(set_id: str, config: dict) -> discord.Embed:
    """Build the pack-ripping animation embed with random foil wrapper."""
    wrappers = config.get("wrappers", [])
    wrapper_file = random.choice(wrappers) if wrappers else None

    embed = discord.Embed(
        title=random.choice(RIP_MESSAGES),
        color=0xFFD700,
    )

    if wrapper_file:
        embed.set_image(url=wrapper_url(set_id, wrapper_file))

    embed.set_footer(text="✨ What's inside...?")
    return embed


def build_card_embed(card: dict, index: int, total: int, set_name: str) -> discord.Embed:
    name = card.get("name", "Unknown")
    rarity = card.get("rarity") or "Unknown"
    category = card.get("category") or "Unknown"
    pulled_holo = card.get("pulled_as_holo", False)

    holo_tag = " ✨ HOLO" if pulled_holo else ""
    title = f"{name}{holo_tag}"

    color_key = "rare holo" if pulled_holo else rarity.lower()
    color = RARITY_COLORS.get(color_key, RARITY_COLORS.get("common", 0x8B8B8B))

    embed = discord.Embed(title=title, color=color)

    image = card_image_url(card)
    if image:
        embed.set_image(url=image)

    rarity_display = f"{'✨ ' if pulled_holo else ''}{rarity}"
    embed.set_footer(text=f"Card {index + 1}/{total} • {set_name} • {category} • {rarity_display}")
    return embed


def build_pack_summary_embed(cards: list[dict], set_name: str, set_id: str, packs_remaining: int | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"<:pokemon_trading_card:1481844443127611444> {set_name} — Pack Summary",
        description="Here's everything you pulled!",
        color=0xFFD700,
    )
    embed.set_thumbnail(url=set_logo_url(set_id))

    lines = []
    for card in cards:
        name = card.get("name", "?")
        rarity = card.get("rarity") or "?"
        holo = card.get("pulled_as_holo", False)
        category = card.get("category", "")

        if holo:
            lines.append(f"✨ **{name}** — Rare Holo")
        elif "rare" in (rarity or "").lower():
            lines.append(f"⭐ **{name}** — Rare")
        elif category and category.lower() == "energy":
            lines.append(f"🔋 {name}")
        else:
            lines.append(f"• {name} — {rarity}")

    embed.add_field(name="Cards", value="\n".join(lines), inline=False)
    if packs_remaining is not None:
        embed.set_footer(text=f"📦 {packs_remaining} pack{'s' if packs_remaining != 1 else ''} remaining • Open another pack or check your stats!")
    else:
        embed.set_footer(text="Open another pack or check your stats!")
    return embed


def build_collection_card_embed(
    card_data: dict, count: int, index: int, total: int,
    set_name: str, rarity_filter: str | None,
) -> discord.Embed:
    """Build an embed for a single card in the collection viewer."""
    name = card_data.get("name", "Unknown")
    rarity = card_data.get("rarity") or "Unknown"
    category = card_data.get("category") or "Unknown"
    is_holo = card_data.get("is_holo", False)
    local_id = card_data.get("local_id", "?")

    display_rarity = _classify_rarity(rarity, is_holo, category)
    emoji = RARITY_EMOJI.get(display_rarity.lower(), "")

    color_key = display_rarity.lower()
    color = RARITY_COLORS.get(color_key, 0x8B8B8B)

    title = f"{emoji} {name}"
    if count > 1:
        title += f"  (×{count})"

    embed = discord.Embed(title=title, color=color)

    image = card_image_url(card_data)
    if image:
        embed.set_image(url=image)

    filter_label = f" • {rarity_filter}" if rarity_filter and rarity_filter != "All" else ""
    embed.set_footer(
        text=f"#{local_id} • {set_name}{filter_label} • {category} • {display_rarity} • Card {index + 1}/{total}"
    )
    return embed


def build_collection_summary_embed(
    display_name: str,
    set_id: str,
    set_name: str,
    set_emoji: str,
    rarity_counts: dict,
    pool_counts: dict,
    total_unique: int,
    total_in_set: int,
    total_pulled: int,
    holo_unique: int,
    holo_total_in_set: int,
) -> discord.Embed:
    """Build the per-set summary embed with rarity breakdown and progress bars."""
    bar_length = 12

    # Overall progress
    if total_in_set and total_in_set > 0:
        overall_filled = round(total_unique / total_in_set * bar_length)
    else:
        overall_filled = 0
    overall_filled = min(overall_filled, bar_length)
    overall_bar = "▓" * overall_filled + "░" * (bar_length - overall_filled)
    pct = round(total_unique / total_in_set * 100) if total_in_set else 0

    header = (
        f"{set_emoji} **{set_name}**\n"
        f"`{overall_bar}` **{total_unique}**/{total_in_set} unique ({pct}%)\n"
        f"**{total_pulled}** total cards pulled\n"
        f"─────────────────────────"
    )

    # Per-rarity breakdown
    rarity_lines = []
    for rarity_name in RARITY_ORDER:
        collected = rarity_counts.get(rarity_name, 0)
        in_pool = pool_counts.get(rarity_name, 0)
        emoji = RARITY_EMOJI.get(rarity_name.lower(), "•")

        if in_pool == 0 and collected == 0:
            continue  # Skip rarities that don't exist in this set

        if in_pool > 0:
            filled = round(collected / in_pool * bar_length)
        else:
            filled = 0
        filled = min(filled, bar_length)
        bar = "▓" * filled + "░" * (bar_length - filled)
        r_pct = round(collected / in_pool * 100) if in_pool else 0

        rarity_lines.append(
            f"{emoji} **{rarity_name}**\n"
            f"`{bar}` **{collected}**/{in_pool} ({r_pct}%)"
        )

    description = header + "\n\n" + "\n\n".join(rarity_lines)

    embed = discord.Embed(
        title=f"📊 {display_name}'s {set_name} Collection",
        description=description,
        color=0x3B82F6,
    )
    embed.set_thumbnail(url=set_logo_url(set_id))
    embed.set_footer(text="Keep opening packs to complete the set!")
    return embed


# ═══════════════════════════════════════════════════════════
#  Pack Selector UI (dropdown + open button)
# ═══════════════════════════════════════════════════════════

class PackSelector(discord.ui.View):
    """Interactive pack selection: dropdown to pick a set, button to open."""

    def __init__(self, cog: "PokemonTCG", author_id: int, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.author_id = author_id
        self.selected_set_id: str | None = None
        self.message: discord.Message | None = None

        sets = cog.card_pool.get_available_sets()
        options = []
        for s in sets:
            options.append(discord.SelectOption(
                label=s["name"],
                value=s["set_id"],
                description=f"{s['total_in_set']} cards • {s['year']}",
                emoji=parse_emoji(s["emoji"]),
            ))
        self.set_select.options = options

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Use `,tcg` to open your own pack selector!",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.select(
        placeholder="Choose a booster pack...",
        min_values=1, max_values=1,
    )
    async def set_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_set_id = select.values[0]
        config = self.cog.card_pool.pack_config.get(self.selected_set_id, {})

        self.btn_open.disabled = False
        self.btn_open.label = f"Open {config.get('name', 'Pack')}"

        guild_id = interaction.guild.id if interaction.guild else 0
        balance = await self.cog._get_pack_balance(interaction.user.id, guild_id)

        embed = build_set_preview_embed(self.selected_set_id, config, packs_remaining=balance)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Open Pack", style=discord.ButtonStyle.success,
        emoji="📦", disabled=True, row=1,
    )
    async def btn_open(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_set_id:
            return

        set_id = self.selected_set_id
        config = self.cog.card_pool.pack_config.get(set_id, {})
        set_name = config.get("name", set_id)

        # Check pack balance
        guild_id = interaction.guild.id if interaction.guild else 0
        balance = await self.cog._get_pack_balance(interaction.user.id, guild_id)
        if balance <= 0:
            now_et = datetime.now(RESET_TIMEZONE)
            midnight = (now_et + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            minutes_left = int((midnight - now_et).total_seconds() / 60)
            hours = minutes_left // 60
            mins = minutes_left % 60
            await interaction.response.send_message(
                f"📦 You're out of packs! You'll get **{PACKS_PER_DAY}** more at midnight ET "
                f"(in about **{hours}h {mins}m**).",
                ephemeral=True,
            )
            return

        # Generate the pack
        cards = self.cog.card_pool.open_pack(set_id)
        if not cards:
            await interaction.response.send_message("❌ Failed to generate pack.", ephemeral=True)
            return

        # Deduct a pack and save
        new_balance = await self.cog._spend_pack(interaction.user.id, guild_id)
        await self.cog._save_pack_to_db(interaction.user.id, guild_id, set_id, cards)

        # Stop the selector
        self.stop()

        # Show the foil wrapper rip animation
        rip_embed = build_rip_embed(set_id, config)
        await interaction.response.edit_message(embed=rip_embed, view=None)

        # Wait for the dramatic reveal
        await asyncio.sleep(3.5)

        # Transition to the card viewer starting at card 1
        viewer = PackViewer(
            cog=self.cog,
            cards=cards,
            set_name=set_name,
            set_id=set_id,
            author_id=interaction.user.id,
            packs_remaining=new_balance,
        )
        viewer._update_buttons()

        await self.message.edit(embed=viewer.get_embed(), view=viewer)
        viewer.message = self.message

    @discord.ui.button(
        label="Stats", style=discord.ButtonStyle.secondary,
        emoji="📊", row=1,
    )
    async def btn_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id if interaction.guild else 0
        embed = await self.cog._build_stats_embed(
            interaction.user.id, guild_id, interaction.user.display_name
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Collection", style=discord.ButtonStyle.secondary,
        emoji="📂", row=1,
    )
    async def btn_collection(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open the collection viewer."""
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id if interaction.guild else 0
        viewer = CollectionViewer(
            cog=self.cog,
            author_id=interaction.user.id,
            guild_id=guild_id,
            display_name=interaction.user.display_name,
        )
        await viewer.initialize()
        embed = viewer.get_embed()
        await interaction.followup.send(embed=embed, view=viewer, ephemeral=True)


# ═══════════════════════════════════════════════════════════
#  Pack Viewer UI (navigate cards, summary at end)
# ═══════════════════════════════════════════════════════════

class PackViewer(discord.ui.View):
    """
    Card-by-card viewer for an opened pack.

    Index 0 through len(cards)-1 = individual cards
    Index len(cards) = summary page (last)
    """

    def __init__(self, cog: "PokemonTCG", cards: list[dict], set_name: str, set_id: str, author_id: int, packs_remaining: int | None = None, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.cards = cards
        self.set_name = set_name
        self.set_id = set_id
        self.author_id = author_id
        self.packs_remaining = packs_remaining
        self.index = 0  # Start at first card
        self.message: discord.Message | None = None

    @property
    def max_index(self) -> int:
        """Last index = summary page."""
        return len(self.cards)

    def get_embed(self) -> discord.Embed:
        if self.index >= len(self.cards):
            return build_pack_summary_embed(self.cards, self.set_name, self.set_id, packs_remaining=self.packs_remaining)
        return build_card_embed(self.cards[self.index], self.index, len(self.cards), self.set_name)

    def _update_buttons(self):
        self.btn_prev.disabled = (self.index <= 0)
        self.btn_next.disabled = (self.index >= self.max_index)

        if self.index >= len(self.cards):
            self.btn_pos.label = "Summary"
        else:
            self.btn_pos.label = f"{self.index + 1}/{len(self.cards)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This isn't your pack! Use `,tcg` to open your own.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = max(0, self.index - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="1/11", style=discord.ButtonStyle.primary, disabled=True)
    async def btn_pos(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Jump to summary
        self.index = self.max_index
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = min(self.max_index, self.index + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Open Another", style=discord.ButtonStyle.success, emoji="📦", row=1)
    async def btn_another(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        selector = PackSelector(cog=self.cog, author_id=self.author_id)
        guild_id = interaction.guild.id if interaction.guild else 0
        balance = await self.cog._get_pack_balance(interaction.user.id, guild_id)
        embed = build_welcome_embed(packs_remaining=balance)
        await interaction.response.edit_message(embed=embed, view=selector)
        selector.message = self.message


# ═══════════════════════════════════════════════════════════
#  Collection Viewer UI
# ═══════════════════════════════════════════════════════════

class CollectionViewer(discord.ui.View):
    """
    Browse collected cards with set/rarity filters and arrow navigation.

    Row 0: Set dropdown
    Row 1: Rarity dropdown
    Row 2: ◀  (position label)  ▶
    Row 3: Show Summary button
    """

    def __init__(
        self,
        cog: "PokemonTCG",
        author_id: int,
        guild_id: int,
        display_name: str,
        timeout: float = 300,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.author_id = author_id
        self.guild_id = guild_id
        self.display_name = display_name
        self.message: discord.Message | None = None

        # State
        self.selected_set_id: str | None = None
        self.selected_rarity: str = "All"  # "All", "Rare Holo", "Rare", etc.
        self.filtered_cards: list[tuple[dict, int]] = []  # (card_data, count)
        self.index: int = 0

        # Build set dropdown options
        sets = cog.card_pool.get_available_sets()
        options = []
        for s in sets:
            options.append(discord.SelectOption(
                label=s["name"],
                value=s["set_id"],
                description=f"{s['total_in_set']} cards • {s['year']}",
                emoji=parse_emoji(s["emoji"]),
            ))
        self.set_filter.options = options

    async def initialize(self):
        """Load the user's collection for the first set."""
        sets = self.cog.card_pool.get_available_sets()
        if sets:
            self.selected_set_id = sets[0]["set_id"]
            # Set the default on the dropdown
            for opt in self.set_filter.options:
                opt.default = (opt.value == self.selected_set_id)
            await self._reload_cards()
            self._rebuild_rarity_options()
        self._update_nav_buttons()

    async def _reload_cards(self):
        """Query DB for the user's collected cards in the selected set, grouped by card_id."""
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
            log.error(f"Collection query failed: {e}")
            self.filtered_cards = []
            return

        # Enrich with full card data from the card pool and apply rarity filter
        all_cards = []
        for row in rows:
            card_id, card_name, rarity, category, is_holo, count = row
            card_data = self.cog.card_pool.cards_by_id.get(card_id)
            if not card_data:
                # Fallback: build minimal card data from DB row
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

        # Apply rarity filter
        if self.selected_rarity and self.selected_rarity != "All":
            all_cards = [
                (cd, cnt, dr) for cd, cnt, dr in all_cards
                if dr == self.selected_rarity
            ]

        # Sort by local_id numerically (groups pokemon, trainers, energy naturally)
        all_cards.sort(key=lambda x: _natural_sort_key(x[0].get("id", "")))

        self.filtered_cards = [(cd, cnt) for cd, cnt, _ in all_cards]
        self.index = 0

    def _rebuild_rarity_options(self):
        """Rebuild the rarity dropdown based on what rarities exist in the user's collection for this set."""
        # Always include "All" option
        options = [discord.SelectOption(
            label="All Rarities",
            value="All",
            emoji="📋",
            default=(self.selected_rarity == "All"),
        )]

        # Check which rarities exist in the current set's card pool
        if self.selected_set_id:
            pool = self.cog.card_pool.sets.get(self.selected_set_id, {})
            available_rarities = set()
            if pool.get("rares_holo"):
                available_rarities.add("Rare Holo")
            if pool.get("rares_normal"):
                available_rarities.add("Rare")
            if pool.get("uncommons"):
                available_rarities.add("Uncommon")
            if pool.get("commons"):
                available_rarities.add("Common")
            if pool.get("energy"):
                available_rarities.add("Energy")

            for rarity_name in RARITY_ORDER:
                if rarity_name in available_rarities:
                    emoji = RARITY_EMOJI.get(rarity_name.lower(), "•")
                    options.append(discord.SelectOption(
                        label=rarity_name,
                        value=rarity_name,
                        emoji=emoji,
                        default=(self.selected_rarity == rarity_name),
                    ))

        self.rarity_filter.options = options

    def _update_nav_buttons(self):
        total = len(self.filtered_cards)
        if total == 0:
            self.btn_prev.disabled = True
            self.btn_next.disabled = True
            self.btn_pos.label = "0/0"
        else:
            self.btn_prev.disabled = (self.index <= 0)
            self.btn_next.disabled = (self.index >= total - 1)
            self.btn_pos.label = f"{self.index + 1}/{total}"

    def get_embed(self) -> discord.Embed:
        if not self.filtered_cards:
            config = self.cog.card_pool.pack_config.get(self.selected_set_id or "", {})
            set_name = config.get("name", self.selected_set_id or "Unknown")
            filter_text = f" ({self.selected_rarity})" if self.selected_rarity != "All" else ""
            embed = discord.Embed(
                title=f"📂 {self.display_name}'s Collection",
                description=f"No cards collected yet for **{set_name}**{filter_text}.\n\nOpen some packs with `,tcg` to start collecting!",
                color=0x3B82F6,
            )
            if self.selected_set_id:
                embed.set_thumbnail(url=set_logo_url(self.selected_set_id))
            return embed

        card_data, count = self.filtered_cards[self.index]
        config = self.cog.card_pool.pack_config.get(self.selected_set_id or "", {})
        set_name = config.get("name", self.selected_set_id or "Unknown")

        return build_collection_card_embed(
            card_data=card_data,
            count=count,
            index=self.index,
            total=len(self.filtered_cards),
            set_name=set_name,
            rarity_filter=self.selected_rarity,
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This isn't your collection! Use `,tcg collection` to view your own.",
                ephemeral=True,
            )
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

    @discord.ui.select(
        placeholder="Choose a set...",
        min_values=1, max_values=1,
        row=0,
    )
    async def set_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_set_id = select.values[0]
        self.selected_rarity = "All"
        # Update default selections on the set dropdown
        for opt in self.set_filter.options:
            opt.default = (opt.value == self.selected_set_id)
        await self._reload_cards()
        self._rebuild_rarity_options()
        self._update_nav_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    # ── Row 1: Rarity filter ──

    @discord.ui.select(
        placeholder="Filter by rarity...",
        min_values=1, max_values=1,
        row=1,
    )
    async def rarity_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_rarity = select.values[0]
        # Update default selections on the rarity dropdown
        for opt in self.rarity_filter.options:
            opt.default = (opt.value == self.selected_rarity)
        await self._reload_cards()
        self._update_nav_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    # ── Row 2: Navigation arrows ──

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=2)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.filtered_cards:
            self.index = max(0, self.index - 1)
        self._update_nav_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="0/0", style=discord.ButtonStyle.primary, disabled=True, row=2)
    async def btn_pos(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass  # Position indicator only

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=2)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.filtered_cards:
            self.index = min(len(self.filtered_cards) - 1, self.index + 1)
        self._update_nav_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    # ── Row 3: Summary button ──

    @discord.ui.button(label="Show Summary", style=discord.ButtonStyle.success, emoji="📊", row=3)
    async def btn_summary(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show a detailed rarity breakdown for the selected set."""
        if not self.selected_set_id:
            await interaction.response.send_message("Select a set first!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        embed = await self.cog._build_set_summary_embed(
            user_id=self.author_id,
            guild_id=self.guild_id,
            set_id=self.selected_set_id,
            display_name=self.display_name,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


    @discord.ui.button(label="Trade", style=discord.ButtonStyle.primary, emoji="🔄", row=3)
    async def btn_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Initiate a trade with the currently viewed card."""
        if not self.filtered_cards:
            await interaction.response.send_message("No card selected to trade!", ephemeral=True)
            return
 
        card_data, count = self.filtered_cards[self.index]
        guild_id = self.guild_id
 
        # Check if user already has a pending trade
        try:
            existing = get_pending_trade(self.cog.database, self.author_id, guild_id)
            if existing:
                await interaction.response.send_message(
                    "❌ You already have a pending trade! Use `,tcg trade` to view or cancel it.",
                    ephemeral=True,
                )
                return
        except Exception as e:
            log.error(f"Trade check failed: {e}")
            await interaction.response.send_message(f"❌ Error checking trades: {e}", ephemeral=True)
            return
 
        # Get other players
        try:
            player_ids = get_other_players(self.cog.database, self.author_id, guild_id)
        except Exception as e:
            log.error(f"Get other players failed: {e}")
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
            return
 
        if not player_ids:
            await interaction.response.send_message(
                "❌ No other players have collected cards yet!",
                ephemeral=True,
            )
            return
 
        guild = interaction.guild
        guild_name = guild.name if guild else "the server"
 
        # Show recipient selector
        selector = RecipientSelectView(
            cog=self.cog,
            author_id=self.author_id,
            guild_id=guild_id,
            guild_name=guild_name,
            card_data=card_data,
            card_count=count,
            player_ids=player_ids,
        )
        await selector.initialize(guild)
 
        card_name = card_data.get("name", "Unknown")
        is_holo = card_data.get("is_holo", False)
        holo_tag = " ✨" if is_holo else ""
 
        embed = discord.Embed(
            title=f"🔄 Trade — {card_name}{holo_tag}",
            description="Choose a player to send this trade offer to:",
            color=0xF59E0B,
        )
        img = card_image_url(card_data)
        if img:
            embed.set_thumbnail(url=img)
 
        await interaction.response.send_message(embed=embed, view=selector, ephemeral=True)
        selector.message = await interaction.original_response()
# ═══════════════════════════════════════════════════════════
#  Main cog
# ═══════════════════════════════════════════════════════════

class PokemonTCG(commands.Cog):
    """Collect original Gen 1 Pokemon TCG cards by opening booster packs."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.data_dir = os.path.join(os.path.dirname(__file__), "pokemon_cards")
        self.card_pool = CardPool()
        self.database = db()

    async def cog_load(self):
        try:
            self.card_pool.load(self.data_dir)
            log.info(f"Pokemon TCG: Loaded card data from {self.data_dir}")
        except FileNotFoundError as e:
            log.error(f"Pokemon TCG: {e}")
        except Exception as e:
            log.error(f"Pokemon TCG: Failed to load card data: {e}")
 
        # Start the pack-full reminder loop
        self._pack_reminder_loop.start()
 
    async def cog_unload(self):
        self._pack_reminder_loop.cancel()

    @tasks.loop(hours=1)
    async def _pack_reminder_loop(self):
        """
        Runs every hour. For every user who:
          1. Has opted in (remind_dm = TRUE)
          2. Has a balance at or above the cap
          3. Hasn't already been reminded this cap cycle
        … send them a DM telling them their packs are full.
        """
        try:
            rows = self.database.queryAll(
                """
                SELECT user_id, guild_id, balance
                FROM tcg_pack_allowance
                WHERE remind_dm = TRUE
                  AND balance >= %(cap)s
                  AND (last_reminded_at IS NULL
                       OR last_reminded_at < last_updated)
                """,
                {"cap": MAX_PACK_BALANCE},
            )
        except Exception as e:
            log.error(f"Pack reminder query failed: {e}")
            return
 
        if not rows:
            return
 
        for user_id, guild_id, balance in rows:
            try:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
 
                member = guild.get_member(user_id)
                if not member:
                    try:
                        member = await guild.fetch_member(user_id)
                    except discord.NotFound:
                        continue
                    except discord.HTTPException:
                        continue
 
                embed = discord.Embed(
                    title="📦 Your packs are full!",
                    description=(
                        f"You have **{balance}/{MAX_PACK_BALANCE}** packs banked in "
                        f"**{guild.name}**.\n\n"
                        f"New packs won't accumulate past the cap, so "
                        f"head over and open some with `,tcg`!\n\n"
                        f"*To stop these reminders, use `,tcg remind` in the server.*"
                    ),
                    color=0xFFD700,
                )
 
                await member.send(embed=embed)
 
                # Mark as reminded
                self.database.execute(
                    """
                    UPDATE tcg_pack_allowance
                    SET balance = %(balance)s,
                        last_reminded_at = NULL
                    WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                    """,
                    {"user_id": user_id, "guild_id": guild_id},
                )
 
            except discord.Forbidden:
                # User has DMs disabled — skip silently
                log.debug(f"Cannot DM user {user_id} for pack reminder (DMs disabled)")
            except Exception as e:
                log.error(f"Pack reminder failed for user {user_id}: {e}")
 
    @_pack_reminder_loop.before_loop
    async def _before_pack_reminder(self):
        await self.bot.wait_until_ready()

    # ─── Admin ─────────────────────────────────────────────

    @commands.group(name="tcgset", invoke_without_command=True)
    @commands.admin_or_permissions(administrator=True)
    async def tcgset(self, ctx: commands.Context):
        """Admin settings for Pokemon TCG collector."""
        await ctx.send_help(ctx.command)

    @tcgset.command(name="reload")
    @commands.admin_or_permissions(administrator=True)
    async def tcgset_reload(self, ctx: commands.Context):
        """Reload card data from disk."""
        try:
            self.card_pool = CardPool()
            self.card_pool.load(self.data_dir)
            total = len(self.card_pool.cards_by_id)
            sets = len(self.card_pool.get_available_sets())
            await ctx.send(f"✅ Reloaded: **{total}** cards across **{sets}** sets")
        except Exception as e:
            await ctx.send(f"❌ Failed to reload: {e}")

    @tcgset.command(name="warmcache")
    @commands.admin_or_permissions(administrator=True)
    async def tcgset_warmcache(self, ctx: commands.Context, set_id: str = None, repeats: int = 1):
        """
        Warm Discord's image proxy cache.

        Usage:
            ,tcgset warmcache                — All sets, once
            ,tcgset warmcache base1          — Just Base Set, once
            ,tcgset warmcache base1 5        — Base Set, repeat 5 times
            ,tcgset warmcache all 3          — All sets, repeat 3 times
        """
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded.")
            return

        if set_id and set_id.lower() == "all":
            set_id = None

        repeats = max(1, min(repeats, 20))

        cards = []
        for card in self.card_pool.cards_by_id.values():
            if set_id and card.get("set_id") != set_id.lower():
                continue
            url = card_image_url(card)
            if url:
                cards.append(url)

        if not cards:
            await ctx.send(f"❌ No cards found{' for set ' + set_id if set_id else ''}.")
            return

        total = len(cards) * repeats
        msg = await ctx.send(f"🔄 Warming cache for **{len(cards)}** cards × {repeats} pass(es) = **{total}** requests...")

        count = 0
        for _ in range(repeats):
            for url in cards:
                # Just reference the URL - Discord caches on first embed display
                count += 1

        await msg.edit(content=f"✅ Cache warm complete! Touched **{count}** URLs.")

    @tcgset.command(name="givepack")
    @commands.admin_or_permissions(administrator=True)
    async def tcgset_givepack(self, ctx: commands.Context, member: discord.Member, amount: int = 1):
        """Give a user extra pack opens. Can exceed the normal cap.

        Usage:
            ,tcgset givepack @user         — Give 1 extra pack
            ,tcgset givepack @user 5       — Give 5 extra packs
        """
        guild_id = ctx.guild.id if ctx.guild else 0
        amount = max(1, min(amount, 50))  # Sanity cap at 50

        # Ensure user has an allowance row (triggers creation if new)
        current = await self._get_pack_balance(member.id, guild_id)
        new_balance = current + amount

        try:
            self.database.execute(
                """
                UPDATE tcg_pack_allowance
                SET balance = %(balance)s
                WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                """,
                {"balance": new_balance, "user_id": member.id, "guild_id": guild_id},
            )
            await ctx.send(f"✅ Gave **{amount}** pack{'s' if amount != 1 else ''} to {member.mention}. They now have **{new_balance}** packs.")
        except Exception as e:
            log.error(f"Givepack failed: {e}")
            await ctx.send(f"❌ Failed to give packs: {e}")

    # ─── User commands ─────────────────────────────────────

    @commands.group(name="tcg", aliases=["t"], invoke_without_command=True)
    async def tcg(self, ctx: commands.Context):
        """Open Pokémon TCG booster packs and collect cards!"""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded. Try `,tcgset reload`.")
            return

        selector = PackSelector(cog=self, author_id=ctx.author.id)
        guild_id = ctx.guild.id if ctx.guild else 0
        balance = await self._get_pack_balance(ctx.author.id, guild_id)
        embed = build_welcome_embed(packs_remaining=balance)
        message = await ctx.send(embed=embed, view=selector)
        selector.message = message

    @tcg.command(name="open")
    async def tcg_open(self, ctx: commands.Context, set_id: str):
        """Quick-open a booster pack: ,tcg open base1"""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded. Try `,tcgset reload`.")
            return

        set_id = set_id.lower().strip()
        config = self.card_pool.pack_config.get(set_id)
        if not config or set_id not in self.card_pool.sets:
            available = ", ".join(f"`{s['set_id']}`" for s in self.card_pool.get_available_sets())
            await ctx.send(f"❌ Unknown set `{set_id}`. Available: {available}")
            return

        # Check pack balance
        guild_id = ctx.guild.id if ctx.guild else 0
        balance = await self._get_pack_balance(ctx.author.id, guild_id)
        if balance <= 0:
            now_et = datetime.now(RESET_TIMEZONE)
            midnight = (now_et + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            minutes_left = int((midnight - now_et).total_seconds() / 60)
            hours = minutes_left // 60
            mins = minutes_left % 60
            await ctx.send(
                f"📦 You're out of packs! You'll get **{PACKS_PER_DAY}** more at midnight ET "
                f"(in about **{hours}h {mins}m**)."
            )
            return

        cards = self.card_pool.open_pack(set_id)
        if not cards:
            await ctx.send("❌ Failed to generate pack.")
            return

        set_name = config.get("name", set_id)
        new_balance = await self._spend_pack(ctx.author.id, guild_id)
        await self._save_pack_to_db(ctx.author.id, guild_id, set_id, cards)

        # Show foil wrapper rip
        rip_embed = build_rip_embed(set_id, config)
        message = await ctx.send(embed=rip_embed)

        await asyncio.sleep(2.5)

        # Transition to card viewer
        viewer = PackViewer(
            cog=self, cards=cards, set_name=set_name,
            set_id=set_id, author_id=ctx.author.id,
            packs_remaining=new_balance,
        )
        viewer._update_buttons()
        await message.edit(embed=viewer.get_embed(), view=viewer)
        viewer.message = message

    @tcg.command(name="packs")
    async def tcg_packs(self, ctx: commands.Context):
        """Show available booster packs."""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded. Try `,tcgset reload`.")
            return

        sets = self.card_pool.get_available_sets()
        embed = discord.Embed(
            title="📦 Available Booster Packs",
            description="Use `,tcg` for the interactive selector, or `,tcg open <set_id>` to quick-open.",
            color=0xFFD700,
        )
        for s in sets:
            embed.add_field(
                name=f"{s['emoji']} {s['name']} (`{s['set_id']}`)",
                value=f"{s['description']}\n{s['total_in_set']} cards • {s['year']}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @tcg.command(name="stats")
    async def tcg_stats(self, ctx: commands.Context, member: discord.Member = None):
        """View your (or another user's) collection stats."""
        target = member or ctx.author
        guild_id = ctx.guild.id if ctx.guild else 0
        embed = await self._build_stats_embed(target.id, guild_id, target.display_name)
        await ctx.send(embed=embed)

    @tcg.command(name="collection")
    async def tcg_collection(self, ctx: commands.Context):
        """Browse your collected cards with filters."""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded. Try `,tcgset reload`.")
            return

        guild_id = ctx.guild.id if ctx.guild else 0
        viewer = CollectionViewer(
            cog=self,
            author_id=ctx.author.id,
            guild_id=guild_id,
            display_name=ctx.author.display_name,
        )
        await viewer.initialize()
        embed = viewer.get_embed()
        message = await ctx.send(embed=embed, view=viewer)
        viewer.message = message

    @tcg.command(name="showcase")
    async def tcg_showcase(self, ctx: commands.Context):
        """Browse another player's Holo and Rare cards."""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded. Try `,tcgset reload`.")
            return

        guild_id = ctx.guild.id if ctx.guild else 0

        try:
            player_ids = get_players_with_cards(self.database, guild_id)
        except Exception as e:
            log.error(f"Showcase player query failed: {e}")
            await ctx.send(f"❌ Error: {e}")
            return

        if not player_ids:
            await ctx.send(
                embed=discord.Embed(
                    title="🏆 Showcase",
                    description="No players have collected cards yet!",
                    color=0x8B8B8B,
                )
            )
            return

        selector = ShowcasePlayerSelector(
            cog=self,
            author_id=ctx.author.id,
            guild_id=guild_id,
            player_ids=player_ids,
        )
        await selector.initialize(ctx.guild)

        embed = discord.Embed(
            title="🏆 Showcase — Browse Collections",
            description=(
                "Pick a player from the dropdown to browse their\n"
                "**Rare Holo** and **Rare** cards!"
            ),
            color=0xFFD700,
        )

        message = await ctx.send(embed=embed, view=selector)
        selector.message = message

    @tcg.command(name="leaderboard", aliases=["lb"])
    async def tcg_leaderboard(self, ctx: commands.Context):
        """Show the server-wide leaderboard for unique Holos and Rares collected."""
        guild_id = ctx.guild.id if ctx.guild else 0
        embed = await self._build_leaderboard_embed(guild_id)
        await ctx.send(embed=embed)

    @tcg.command(name="trade")
    async def tcg_trade(self, ctx: commands.Context):
        """View or manage your active trade."""
        guild_id = ctx.guild.id if ctx.guild else 0
 
        try:
            trade = get_pending_trade(self.database, ctx.author.id, guild_id)
        except Exception as e:
            log.error(f"Trade lookup failed: {e}")
            await ctx.send(f"❌ Error: {e}")
            return
 
        if not trade:
            await ctx.send(
                embed=discord.Embed(
                    title="🔄 No Active Trade",
                    description=(
                        "You don't have any pending trades.\n\n"
                        "To start a trade, browse your collection with `,tcg collection` "
                        "and click the **Trade** button on any card."
                    ),
                    color=0x8B8B8B,
                )
            )
            return
 
        embed = build_trade_review_embed(trade, self.card_pool, ctx.author.id)
        view = TradeStatusView(
            cog=self,
            trade=trade,
            viewer_id=ctx.author.id,
            guild_id=guild_id,
        )
 
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @tcg.command(name="remind")
    async def tcg_remind(self, ctx: commands.Context):
        """Toggle DM reminders for when your packs are full.
 
        When enabled, you'll receive a DM once your pack balance
        hits the maximum (15). The reminder only fires once per
        cap cycle — after you open a pack the timer resets.
        """
        guild_id = ctx.guild.id if ctx.guild else 0
        user_id = ctx.author.id
 
        # Make sure they have an allowance row
        await self._get_pack_balance(user_id, guild_id)
 
        try:
            row = self.database.querySingle(
                """
                SELECT remind_dm
                FROM tcg_pack_allowance
                WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                """,
                {"user_id": user_id, "guild_id": guild_id},
            )
        except Exception as e:
            log.error(f"Remind query failed: {e}")
            await ctx.send("❌ Something went wrong. Try again later.")
            return
 
        current = row[0] if row else False
        new_value = not current
 
        try:
            self.database.execute(
                """
                UPDATE tcg_pack_allowance
                SET remind_dm = %(remind)s
                WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                """,
                {"remind": new_value, "user_id": user_id, "guild_id": guild_id},
            )
        except Exception as e:
            log.error(f"Remind toggle failed: {e}")
            await ctx.send("❌ Something went wrong. Try again later.")
            return
 
        if new_value:
            await ctx.send(
                "🔔 **Pack reminders enabled!** I'll DM you when your packs hit "
                f"**{MAX_PACK_BALANCE}** so you don't waste any."
            )
        else:
            await ctx.send("🔕 **Pack reminders disabled.** You won't receive DMs about full packs anymore.")

    # ─── Helpers ───────────────────────────────────────────

    async def _build_leaderboard_embed(self, guild_id: int) -> discord.Embed:
        """Build a server-wide leaderboard showing unique Holos, Rares, and Trades per player."""
        try:
            rows = self.database.queryAll(
                """
                SELECT
                    user_id,
                    COUNT(DISTINCT card_id) FILTER (WHERE is_holo = true) AS unique_holos,
                    COUNT(DISTINCT card_id) FILTER (
                        WHERE is_holo = false
                          AND LOWER(rarity) LIKE '%%rare%%'
                          AND category != 'Energy'
                    ) AS unique_rares,
                    COUNT(DISTINCT card_id) AS total_unique
                FROM tcg_user_cards
                WHERE guild_id = %(guild_id)s
                GROUP BY user_id
                ORDER BY unique_holos DESC, unique_rares DESC, total_unique DESC
                """,
                {"guild_id": guild_id},
            )
        except Exception as e:
            log.error(f"Leaderboard query failed: {e}")
            return discord.Embed(title="❌ Error", description="Failed to fetch leaderboard.", color=0xFF0000)
 
        if not rows:
            return discord.Embed(
                title="🏆 TCG Leaderboard",
                description="Nobody has collected any cards yet!\nUse `,tcg` to open your first pack.",
                color=0xFFD700,
            )
 
        # Get trade counts
        try:
            trade_counts = get_completed_trade_counts(self.database, guild_id)
        except Exception:
            trade_counts = {}
 
        # Count total possible holos and rares across all sets
        total_holos_in_game = 0
        total_rares_in_game = 0
        for set_id, pool in self.card_pool.sets.items():
            total_holos_in_game += len(pool.get("rares_holo", []))
            total_rares_in_game += len(pool.get("rares_normal", []))
 
        # Build leaderboard lines
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, row in enumerate(rows[:15]):
            user_id, unique_holos, unique_rares, total_unique = row
            rank = medals[i] if i < 3 else f"**{i + 1}.**"
            trades = trade_counts.get(user_id, 0)
            trade_str = f"  •  🔄 **{trades}** trades" if trades > 0 else ""
            lines.append(
                f"{rank} <@{user_id}>  —  "
                f"✨ **{unique_holos}** holo  •  "
                f"⭐ **{unique_rares}** rare"
                f"{trade_str}"
            )
 
        description = "\n".join(lines)
        description += (
            f"\n\n─────────────────────────\n"
            f"**{total_holos_in_game}** holos and **{total_rares_in_game}** rares exist across all sets"
        )
 
        embed = discord.Embed(
            title="🏆 TCG Leaderboard — Holos & Rares",
            description=description,
            color=0xFFD700,
        )
        embed.set_footer(text="Ranked by unique holos, then unique rares • 🔄 = completed trades")
        return embed
    
    async def _build_stats_embed(self, user_id: int, guild_id: int, display_name: str) -> discord.Embed:
        try:
            rows = self.database.queryAll(
                """
                SELECT set_id, total_cards, unique_cards, holo_cards,
                       pokemon_cards, trainer_cards, energy_cards
                FROM tcg_collection_summary
                WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                ORDER BY set_id
                """,
                {"user_id": user_id, "guild_id": guild_id},
            )
        except Exception as e:
            log.error(f"Stats query failed: {e}")
            return discord.Embed(title="❌ Error", description="Failed to fetch stats.", color=0xFF0000)

        if not rows:
            return discord.Embed(
                title=f"📊 {display_name}'s Collection",
                description="No cards collected yet! Use `,tcg` to open your first pack.",
                color=0x3B82F6,
            )

        # ── Gather totals ──
        total_all = unique_all = holo_all = 0
        set_lines = []

        for row in rows:
            set_id, total, unique, holos, pokemon, trainers, energy = row
            config = self.card_pool.pack_config.get(set_id, {})
            set_name = config.get("name", set_id)
            set_emoji = config.get("emoji", "📦")
            set_total = config.get("total_cards_in_set", 0)

            total_all += total
            unique_all += unique
            holo_all += holos

            # Build a progress bar  ▓▓▓▓▓▓▓▓░░  8/10
            bar_length = 10
            if set_total and set_total != "?":
                filled = round(unique / int(set_total) * bar_length)
            else:
                filled = 0
                set_total = "?"
            filled = min(filled, bar_length)
            bar = "▓" * filled + "░" * (bar_length - filled)

            holo_str = f"  ✨ {holos}" if holos else ""
            set_lines.append(
                f"{set_emoji} **{set_name}**\n"
                f"`{bar}` **{unique}**/{set_total} unique • {total} pulled{holo_str}"
            )

        # ── Pack count ──
        try:
            pack_row = self.database.querySingle(
                "SELECT COUNT(*) FROM tcg_pack_opens WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s",
                {"user_id": user_id, "guild_id": guild_id},
            )
            pack_count = pack_row[0] if pack_row else 0
        except Exception:
            pack_count = "?"

        # ── Build embed ──
        summary = (
            f"**{pack_count}** packs opened • **{total_all}** cards\n"
            f"**{unique_all}** unique • **{holo_all}** ✨ holo\n"
            f"─────────────────────────"
        )

        embed = discord.Embed(
            title=f"📊 {display_name}'s Collection",
            description=summary + "\n\n" + "\n\n".join(set_lines),
            color=0x3B82F6,
        )
        embed.set_footer(text="Open more packs to complete your collection!")
        return embed

    async def _build_set_summary_embed(
        self, user_id: int, guild_id: int, set_id: str, display_name: str,
    ) -> discord.Embed:
        """Build a detailed per-set summary with rarity breakdown progress bars."""
        config = self.card_pool.pack_config.get(set_id, {})
        set_name = config.get("name", set_id)
        set_emoji = config.get("emoji", "📦")
        total_in_set = config.get("total_cards_in_set", 0)

        # Count how many unique cards exist in each rarity bucket in the card pool
        pool = self.card_pool.sets.get(set_id, {})
        pool_counts = {
            "Rare Holo": len(pool.get("rares_holo", [])),
            "Rare": len(pool.get("rares_normal", [])),
            "Uncommon": len(pool.get("uncommons", [])),
            "Common": len(pool.get("commons", [])),
            "Energy": len(pool.get("energy", [])),
        }

        # Query user's unique cards per rarity in this set
        try:
            rows = self.database.queryAll(
                """
                SELECT
                    CASE
                        WHEN category = 'Energy' THEN 'Energy'
                        WHEN is_holo = true THEN 'Rare Holo'
                        WHEN LOWER(rarity) LIKE '%%rare%%' THEN 'Rare'
                        WHEN LOWER(rarity) = 'uncommon' THEN 'Uncommon'
                        ELSE 'Common'
                    END as rarity_bucket,
                    COUNT(DISTINCT card_id) as unique_count
                FROM tcg_user_cards
                WHERE user_id = %(user_id)s
                  AND guild_id = %(guild_id)s
                  AND set_id = %(set_id)s
                GROUP BY rarity_bucket
                """,
                {"user_id": user_id, "guild_id": guild_id, "set_id": set_id},
            )
        except Exception as e:
            log.error(f"Set summary query failed: {e}")
            return discord.Embed(title="❌ Error", description="Failed to fetch set summary.", color=0xFF0000)

        rarity_counts = {}
        for row in rows:
            rarity_counts[row[0]] = row[1]

        # Total unique and pulled counts
        try:
            totals_row = self.database.querySingle(
                """
                SELECT COUNT(DISTINCT card_id), COUNT(*)
                FROM tcg_user_cards
                WHERE user_id = %(user_id)s
                  AND guild_id = %(guild_id)s
                  AND set_id = %(set_id)s
                """,
                {"user_id": user_id, "guild_id": guild_id, "set_id": set_id},
            )
            total_unique = totals_row[0] if totals_row else 0
            total_pulled = totals_row[1] if totals_row else 0
        except Exception:
            total_unique = sum(rarity_counts.values())
            total_pulled = 0

        holo_unique = rarity_counts.get("Rare Holo", 0)
        holo_total_in_set = pool_counts.get("Rare Holo", 0)

        return build_collection_summary_embed(
            display_name=display_name,
            set_id=set_id,
            set_name=set_name,
            set_emoji=set_emoji,
            rarity_counts=rarity_counts,
            pool_counts=pool_counts,
            total_unique=total_unique,
            total_in_set=total_in_set,
            total_pulled=total_pulled,
            holo_unique=holo_unique,
            holo_total_in_set=holo_total_in_set,
        )

    # ─── Pack allowance ──────────────────────────────────────

    async def _get_pack_balance(self, user_id: int, guild_id: int) -> int:
        """
        Get the user's current pack balance, crediting any days that have
        passed since their last update. Uses a token-bucket approach:
        earn PACKS_PER_DAY at each midnight ET, capped at MAX_PACK_BALANCE.
        """
        now_et = datetime.now(RESET_TIMEZONE)
        today_midnight = now_et.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            row = self.database.querySingle(
                """
                SELECT balance, last_updated
                FROM tcg_pack_allowance
                WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                """,
                {"user_id": user_id, "guild_id": guild_id},
            )
        except Exception as e:
            log.error(f"Pack balance query failed: {e}")
            return 0

        if not row:
            # New user — initialize with starting balance
            try:
                self.database.execute(
                    """
                    INSERT INTO tcg_pack_allowance (user_id, guild_id, balance, last_updated)
                    VALUES (%(user_id)s, %(guild_id)s, %(balance)s, %(now)s)
                    ON CONFLICT (user_id, guild_id) DO NOTHING
                    """,
                    {
                        "user_id": user_id,
                        "guild_id": guild_id,
                        "balance": STARTING_BALANCE,
                        "now": today_midnight,
                    },
                )
            except Exception as e:
                log.error(f"Pack balance init failed: {e}")
            return STARTING_BALANCE

        balance, last_updated = row

        # Calculate how many midnights have passed since last_updated
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=RESET_TIMEZONE)
        else:
            last_updated = last_updated.astimezone(RESET_TIMEZONE)

        last_midnight = last_updated.replace(hour=0, minute=0, second=0, microsecond=0)
        days_elapsed = (today_midnight - last_midnight).days

        if days_elapsed > 0:
            earned = days_elapsed * PACKS_PER_DAY
            new_balance = min(balance + earned, MAX_PACK_BALANCE)

            # Update the stored balance and timestamp
            try:
                self.database.execute(
                    """
                    UPDATE tcg_pack_allowance
                    SET balance = %(balance)s, last_updated = %(now)s
                    WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                    """,
                    {
                        "balance": new_balance,
                        "now": today_midnight,
                        "user_id": user_id,
                        "guild_id": guild_id,
                    },
                )
            except Exception as e:
                log.error(f"Pack balance update failed: {e}")
            return new_balance

        return balance

    async def _spend_pack(self, user_id: int, guild_id: int) -> int:
        """Deduct one pack from the user's balance. Returns the new balance."""
        # Ensure balance is up to date first
        balance = await self._get_pack_balance(user_id, guild_id)
        new_balance = max(0, balance - 1)

        try:
            self.database.execute(
                """
                UPDATE tcg_pack_allowance
                SET balance = %(balance)s
                WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                """,
                {
                    "balance": new_balance,
                    "user_id": user_id,
                    "guild_id": guild_id,
                },
            )
        except Exception as e:
            log.error(f"Pack spend failed: {e}")
        return new_balance

    # ─── Database ──────────────────────────────────────────

    async def _save_pack_to_db(self, user_id: int, guild_id: int, set_id: str, cards: list[dict]) -> int | None:
        try:
            result = self.database.executeAndReturn(
                """
                INSERT INTO tcg_pack_opens (user_id, guild_id, set_id)
                VALUES (%(user_id)s, %(guild_id)s, %(set_id)s)
                RETURNING id
                """,
                {"user_id": user_id, "guild_id": guild_id, "set_id": set_id},
            )
            pack_open_id = result[0] if result else None

            for card in cards:
                self.database.execute(
                    """
                    INSERT INTO tcg_user_cards
                        (user_id, guild_id, card_id, set_id, card_name, rarity, category, is_holo, pack_open_id)
                    VALUES
                        (%(user_id)s, %(guild_id)s, %(card_id)s, %(set_id)s, %(card_name)s,
                         %(rarity)s, %(category)s, %(is_holo)s, %(pack_open_id)s)
                    """,
                    {
                        "user_id": user_id,
                        "guild_id": guild_id,
                        "card_id": card.get("id"),
                        "set_id": card.get("set_id"),
                        "card_name": card.get("name", "Unknown"),
                        "rarity": card.get("rarity"),
                        "category": card.get("category"),
                        "is_holo": card.get("pulled_as_holo", False),
                        "pack_open_id": pack_open_id,
                    },
                )
            return pack_open_id

        except Exception as e:
            log.error(f"Failed to save pack to database: {e}")
            return None