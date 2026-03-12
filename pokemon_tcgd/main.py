"""
Pokemon TCG Collector - Red Discord Bot Cog

Open booster packs from original Gen 1 era sets, collect cards,
and track your collection in PostgreSQL.
"""

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import logging
import os

from .packopener import CardPool
from .dbclass import db

log = logging.getLogger("red.pokemontcg")


# ═══════════════════════════════════════════════════════════
#  Embed builder helpers
# ═══════════════════════════════════════════════════════════

# Rarity colors for embeds
RARITY_COLORS = {
    "common":    0x8B8B8B,   # Gray
    "uncommon":  0x3B82F6,   # Blue
    "rare":      0xF59E0B,   # Gold
    "rare holo": 0xEF4444,   # Red
    "energy":    0x10B981,   # Green
}

# Type emoji mapping
TYPE_EMOJI = {
    "Colorless": "⚪", "Fire": "🔥", "Water": "💧", "Grass": "🌿",
    "Lightning": "⚡", "Psychic": "🔮", "Fighting": "👊", "Darkness": "🌑",
    "Metal": "⚙️", "Dragon": "🐉", "Fairy": "🧚",
}


def build_card_embed(card: dict, index: int, total: int, set_name: str) -> discord.Embed:
    """Build a Discord embed for a single card in a pack."""

    name = card.get("name", "Unknown")
    rarity = card.get("rarity") or "Unknown"
    category = card.get("category") or "Unknown"
    pulled_holo = card.get("pulled_as_holo", False)

    # Title
    holo_tag = " ✨ HOLO" if pulled_holo else ""
    title = f"{name}{holo_tag}"

    # Color based on rarity
    color_key = "rare holo" if pulled_holo else rarity.lower()
    color = RARITY_COLORS.get(color_key, RARITY_COLORS.get("common", 0x8B8B8B))

    embed = discord.Embed(title=title, color=color)

    # Card image (use TCGdex hosted URL)
    image_url = card.get("image_high") or card.get("image_low")
    if image_url:
        embed.set_image(url=image_url)

    # Footer with position and set info
    rarity_display = f"{'✨ ' if pulled_holo else ''}{rarity}"
    embed.set_footer(text=f"Card {index + 1}/{total} • {set_name} • {category} • {rarity_display}")

    return embed


def build_pack_summary_embed(cards: list[dict], set_name: str, set_emoji: str) -> discord.Embed:
    """Build a summary embed showing all cards in an opened pack."""

    embed = discord.Embed(
        title=f"{set_emoji} {set_name} Booster Pack",
        description="Here's what you pulled!",
        color=0xFFD700,
    )

    # Group by rarity for display
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
    embed.set_footer(text="Use the arrows to view each card")

    return embed


# ═══════════════════════════════════════════════════════════
#  Pack viewer UI (discord.py View with buttons)
# ═══════════════════════════════════════════════════════════

class PackViewer(discord.ui.View):
    """Interactive card viewer for an opened pack with Previous/Next buttons."""

    def __init__(self, cards: list[dict], set_name: str, set_emoji: str, author_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.cards = cards
        self.set_name = set_name
        self.set_emoji = set_emoji
        self.author_id = author_id
        self.index = -1  # -1 = summary page
        self.message: discord.Message | None = None

    def get_embed(self) -> discord.Embed:
        """Get the embed for the current index."""
        if self.index == -1:
            return build_pack_summary_embed(self.cards, self.set_name, self.set_emoji)
        return build_card_embed(self.cards[self.index], self.index, len(self.cards), self.set_name)

    def _update_buttons(self):
        """Update button states based on current index."""
        self.btn_prev.disabled = (self.index <= -1)
        self.btn_next.disabled = (self.index >= len(self.cards) - 1)
        # Update label to show position
        if self.index == -1:
            self.btn_pos.label = "Summary"
        else:
            self.btn_pos.label = f"{self.index + 1}/{len(self.cards)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only the user who opened the pack can navigate."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This isn't your pack! Open your own with `!tcg open`.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        """Disable buttons when the view times out."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, custom_id="pack_prev")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = max(-1, self.index - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Summary", style=discord.ButtonStyle.primary, custom_id="pack_pos", disabled=True)
    async def btn_pos(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Clicking position indicator goes back to summary
        self.index = -1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, custom_id="pack_next")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = min(len(self.cards) - 1, self.index + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


# ═══════════════════════════════════════════════════════════
#  Main cog
# ═══════════════════════════════════════════════════════════

class PokemonTCG(commands.Cog):
    """Collect original Gen 1 Pokemon TCG cards by opening booster packs."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0x706B6D6E_74636700)
        self.config.register_global(
            data_dir="/srv/pokemontcg/data",  # Where cards.json + pack_config.json live
        )
        self.card_pool = CardPool()
        self.database = db()

    async def cog_load(self):
        """Load card data when cog is loaded."""
        data_dir = await self.config.data_dir()
        try:
            self.card_pool.load(data_dir)
            log.info(f"Pokemon TCG: Loaded card data from {data_dir}")
        except FileNotFoundError as e:
            log.error(f"Pokemon TCG: {e}")
            log.error(f"Pokemon TCG: Set data directory with: [p]tcgset datadir <path>")
        except Exception as e:
            log.error(f"Pokemon TCG: Failed to load card data: {e}")

    # ─── Admin commands ────────────────────────────────────

    @commands.group(name="tcgset", invoke_without_command=True)
    @commands.admin_or_permissions(administrator=True)
    async def tcgset(self, ctx: commands.Context):
        """Admin settings for Pokemon TCG collector."""
        await ctx.send_help(ctx.command)

    @tcgset.command(name="datadir")
    @commands.admin_or_permissions(administrator=True)
    async def tcgset_datadir(self, ctx: commands.Context, path: str):
        """Set the path to the card data directory (where cards.json and pack_config.json live)."""
        if not os.path.isdir(path):
            await ctx.send(f"❌ Directory not found: `{path}`")
            return

        cards_json = os.path.join(path, "cards.json")
        config_json = os.path.join(path, "pack_config.json")

        if not os.path.exists(cards_json):
            await ctx.send(f"❌ `cards.json` not found in `{path}`")
            return
        if not os.path.exists(config_json):
            await ctx.send(f"❌ `pack_config.json` not found in `{path}`")
            return

        await self.config.data_dir.set(path)

        try:
            self.card_pool.load(path)
            sets = self.card_pool.get_available_sets()
            total_cards = len(self.card_pool.cards_by_id)
            await ctx.send(
                f"✅ Card data loaded: **{total_cards}** cards across **{len(sets)}** sets from `{path}`"
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to load card data: {e}")

    @tcgset.command(name="reload")
    @commands.admin_or_permissions(administrator=True)
    async def tcgset_reload(self, ctx: commands.Context):
        """Reload card data from disk."""
        data_dir = await self.config.data_dir()
        try:
            self.card_pool = CardPool()  # Reset
            self.card_pool.load(data_dir)
            total = len(self.card_pool.cards_by_id)
            await ctx.send(f"✅ Reloaded: **{total}** cards")
        except Exception as e:
            await ctx.send(f"❌ Failed to reload: {e}")

    # ─── User commands ─────────────────────────────────────

    @commands.group(name="tcg", invoke_without_command=True)
    async def tcg(self, ctx: commands.Context):
        """Pokemon TCG Card Collector — open packs, collect cards!"""
        await ctx.send_help(ctx.command)

    @tcg.command(name="packs")
    async def tcg_packs(self, ctx: commands.Context):
        """Show available booster packs you can open."""
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded yet. An admin needs to run `!tcgset datadir <path>`.")
            return

        sets = self.card_pool.get_available_sets()
        if not sets:
            await ctx.send("❌ No sets available.")
            return

        embed = discord.Embed(
            title="📦 Available Booster Packs",
            description="Choose a set to open with `!tcg open <set_id>`",
            color=0xFFD700,
        )

        for s in sets:
            embed.add_field(
                name=f"{s['emoji']} {s['name']} (`{s['set_id']}`)",
                value=f"{s['description']}\n{s['total_in_set']} cards • {s['cards_per_pack']} per pack • {s['year']}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @tcg.command(name="open")
    async def tcg_open(self, ctx: commands.Context, set_id: str):
        """
        Open a booster pack from a specific set.

        Examples:
            !tcg open base1    — Open a Base Set pack
            !tcg open base5    — Open a Team Rocket pack
            !tcg open gym1     — Open a Gym Heroes pack
        """
        if not self.card_pool.loaded:
            await ctx.send("❌ Card data not loaded yet. An admin needs to run `!tcgset datadir <path>`.")
            return

        set_id = set_id.lower().strip()

        # Validate set
        config = self.card_pool.pack_config.get(set_id)
        if not config or set_id not in self.card_pool.sets:
            available = ", ".join(f"`{s['set_id']}`" for s in self.card_pool.get_available_sets())
            await ctx.send(f"❌ Unknown set `{set_id}`. Available: {available}")
            return

        # Open the pack
        cards = self.card_pool.open_pack(set_id)
        if not cards:
            await ctx.send("❌ Failed to generate pack. The set may not have enough card data.")
            return

        set_name = config.get("name", set_id)
        set_emoji = config.get("emoji", "📦")

        # Save to database
        pack_open_id = await self._save_pack_to_db(ctx.author.id, ctx.guild.id, set_id, cards)

        # Build the viewer
        view = PackViewer(
            cards=cards,
            set_name=set_name,
            set_emoji=set_emoji,
            author_id=ctx.author.id,
        )
        view._update_buttons()

        message = await ctx.send(embed=view.get_embed(), view=view)
        view.message = message

    @tcg.command(name="stats")
    async def tcg_stats(self, ctx: commands.Context, member: discord.Member = None):
        """View your (or another user's) collection stats."""
        target = member or ctx.author

        try:
            rows = self.database.queryAll(
                """
                SELECT set_id, total_cards, unique_cards, holo_cards,
                       pokemon_cards, trainer_cards, energy_cards
                FROM tcg_collection_summary
                WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                ORDER BY set_id
                """,
                {"user_id": target.id, "guild_id": ctx.guild.id},
            )
        except Exception as e:
            log.error(f"Stats query failed: {e}")
            await ctx.send("❌ Failed to fetch stats.")
            return

        if not rows:
            if target == ctx.author:
                await ctx.send("You haven't collected any cards yet! Try `!tcg open base1` to get started.")
            else:
                await ctx.send(f"{target.display_name} hasn't collected any cards yet.")
            return

        embed = discord.Embed(
            title=f"📊 {target.display_name}'s Collection",
            color=0x3B82F6,
        )

        total_all = 0
        unique_all = 0
        holo_all = 0

        for row in rows:
            set_id, total, unique, holos, pokemon, trainers, energy = row
            config = self.card_pool.pack_config.get(set_id, {})
            set_name = config.get("name", set_id)
            set_emoji = config.get("emoji", "📦")
            set_total = config.get("total_cards_in_set", "?")

            embed.add_field(
                name=f"{set_emoji} {set_name}",
                value=(
                    f"**{unique}**/{set_total} unique • {total} total\n"
                    f"✨ {holos} holo"
                ),
                inline=True,
            )

            total_all += total
            unique_all += unique
            holo_all += holos

        # Pack count
        try:
            pack_row = self.database.querySingle(
                """
                SELECT COUNT(*) FROM tcg_pack_opens
                WHERE user_id = %(user_id)s AND guild_id = %(guild_id)s
                """,
                {"user_id": target.id, "guild_id": ctx.guild.id},
            )
            pack_count = pack_row[0] if pack_row else 0
        except Exception:
            pack_count = "?"

        embed.description = f"**{total_all}** cards collected • **{unique_all}** unique • **{holo_all}** ✨ holo • **{pack_count}** packs opened"

        await ctx.send(embed=embed)

    # ─── Database operations ───────────────────────────────

    async def _save_pack_to_db(self, user_id: int, guild_id: int, set_id: str, cards: list[dict]) -> int | None:
        """Save a pack opening and its cards to the database."""
        try:
            # Insert pack open record
            result = self.database.executeAndReturn(
                """
                INSERT INTO tcg_pack_opens (user_id, guild_id, set_id)
                VALUES (%(user_id)s, %(guild_id)s, %(set_id)s)
                RETURNING id
                """,
                {"user_id": user_id, "guild_id": guild_id, "set_id": set_id},
            )
            pack_open_id = result[0] if result else None

            # Insert each card
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