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

from .packopener import CardPool
from .dbclass import db

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

RIP_MESSAGES = [
    "You tear open the pack...",
    "You rip into the foil...",
    "The wrapper crinkles as you tear it open...",
    "You carefully peel the pack open...",
    "The foil glints as you rip it apart...",
]


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


# ═══════════════════════════════════════════════════════════
#  Embed builders
# ═══════════════════════════════════════════════════════════

def build_welcome_embed() -> discord.Embed:
    embed = discord.Embed(
        title="<:pokemon_trading_card:1481844443127611444> Pokémon TCG Card Collector",
        description=(
            "Collect cards from the original Gen 1 Pokémon TCG sets!\n\n"
            "**Select a booster pack** from the menu below to get started."
        ),
        color=0xFFD700,
    )
    embed.set_footer(text="Wizards of the Coast Era • 1999–2002")
    return embed


def build_set_preview_embed(set_id: str, config: dict) -> discord.Embed:
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


def build_pack_summary_embed(cards: list[dict], set_name: str, set_id: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎴 {set_name} — Pack Summary",
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
    embed.set_footer(text="Open another pack or check your stats!")
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
                "Use `!tcg` to open your own pack selector!",
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

        embed = build_set_preview_embed(self.selected_set_id, config)
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

        # Generate the pack
        cards = self.cog.card_pool.open_pack(set_id)
        if not cards:
            await interaction.response.send_message("❌ Failed to generate pack.", ephemeral=True)
            return

        # Save to database
        guild_id = interaction.guild.id if interaction.guild else 0
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


# ═══════════════════════════════════════════════════════════
#  Pack Viewer UI (navigate cards, summary at end)
# ═══════════════════════════════════════════════════════════

class PackViewer(discord.ui.View):
    """
    Card-by-card viewer for an opened pack.

    Index 0 through len(cards)-1 = individual cards
    Index len(cards) = summary page (last)
    """

    def __init__(self, cog: "PokemonTCG", cards: list[dict], set_name: str, set_id: str, author_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.cards = cards
        self.set_name = set_name
        self.set_id = set_id
        self.author_id = author_id
        self.index = 0  # Start at first card
        self.message: discord.Message | None = None

    @property
    def max_index(self) -> int:
        """Last index = summary page."""
        return len(self.cards)

    def get_embed(self) -> discord.Embed:
        if self.index >= len(self.cards):
            return build_pack_summary_embed(self.cards, self.set_name, self.set_id)
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
                "This isn't your pack! Use `!tcg` to open your own.",
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
        embed = build_welcome_embed()
        await interaction.response.edit_message(embed=embed, view=selector)
        selector.message = self.message


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
            !tcgset warmcache                — All sets, once
            !tcgset warmcache base1          — Just Base Set, once
            !tcgset warmcache base1 5        — Base Set, repeat 5 times
            !tcgset warmcache all 3          — All sets, repeat 3 times
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

        est_min = (len(cards) * 4 * repeats) // 60
        status = await ctx.send(
            f"🔥 Warming cache for **{len(cards)}** images × **{repeats}** pass{'es' if repeats > 1 else ''}... ~{est_min} min"
        )

        total_warmed = 0
        total_failed = 0
        batch_size = 4

        for run in range(1, repeats + 1):
            warmed = 0
            failed = 0

            for i in range(0, len(cards), batch_size):
                batch = cards[i:i + batch_size]

                try:
                    embeds = [discord.Embed().set_image(url=url) for url in batch]
                    msg = await ctx.send(embeds=embeds)
                    await asyncio.sleep(3.5)
                    await msg.delete()
                    warmed += len(batch)
                except Exception as e:
                    log.warning(f"Cache warm batch failed: {e}")
                    failed += len(batch)

                if warmed % 20 < batch_size:
                    try:
                        await status.edit(
                            content=f"🔥 Pass {run}/{repeats} — **{warmed}**/{len(cards)} ({failed} failed)"
                        )
                    except discord.HTTPException:
                        pass

                await asyncio.sleep(1.0)

            total_warmed += warmed
            total_failed += failed

            if run < repeats:
                await status.edit(
                    content=f"✅ Pass {run}/{repeats} done. Pausing 10s before next pass..."
                )
                await asyncio.sleep(10)

        await status.edit(
            content=f"✅ Cache warming complete: **{repeats}** pass{'es' if repeats > 1 else ''}, **{total_warmed}** sent, **{total_failed}** failed."
        )

    # ─── User commands ─────────────────────────────────────

    @commands.group(name="tcg", invoke_without_command=True)
    async def tcg(self, ctx: commands.Context):
        """Open Pokémon TCG booster packs and collect cards!"""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded. Try `!tcgset reload`.")
            return

        selector = PackSelector(cog=self, author_id=ctx.author.id)
        embed = build_welcome_embed()
        message = await ctx.send(embed=embed, view=selector)
        selector.message = message

    @tcg.command(name="open")
    async def tcg_open(self, ctx: commands.Context, set_id: str):
        """Quick-open a booster pack: !tcg open base1"""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded. Try `!tcgset reload`.")
            return

        set_id = set_id.lower().strip()
        config = self.card_pool.pack_config.get(set_id)
        if not config or set_id not in self.card_pool.sets:
            available = ", ".join(f"`{s['set_id']}`" for s in self.card_pool.get_available_sets())
            await ctx.send(f"❌ Unknown set `{set_id}`. Available: {available}")
            return

        cards = self.card_pool.open_pack(set_id)
        if not cards:
            await ctx.send("❌ Failed to generate pack.")
            return

        set_name = config.get("name", set_id)
        await self._save_pack_to_db(ctx.author.id, ctx.guild.id, set_id, cards)

        # Show foil wrapper rip
        rip_embed = build_rip_embed(set_id, config)
        message = await ctx.send(embed=rip_embed)

        await asyncio.sleep(2.5)

        # Transition to card viewer
        viewer = PackViewer(
            cog=self, cards=cards, set_name=set_name,
            set_id=set_id, author_id=ctx.author.id,
        )
        viewer._update_buttons()
        await message.edit(embed=viewer.get_embed(), view=viewer)
        viewer.message = message

    @tcg.command(name="packs")
    async def tcg_packs(self, ctx: commands.Context):
        """Show available booster packs."""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded. Try `!tcgset reload`.")
            return

        sets = self.card_pool.get_available_sets()
        embed = discord.Embed(
            title="📦 Available Booster Packs",
            description="Use `!tcg` for the interactive selector, or `!tcg open <set_id>` to quick-open.",
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

    # ─── Helpers ───────────────────────────────────────────

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
                description="No cards collected yet! Use `!tcg` to open your first pack.",
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