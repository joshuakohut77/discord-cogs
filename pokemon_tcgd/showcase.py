"""
Showcase — Browse another player's Rare Holo and Rare cards.

New command:  !tcg showcase
Flow:
  1. Player dropdown (no @mention needed) → pick who to view
  2. Read-only collection viewer filtered to Rare Holo + Rare only
     with set filter, navigation arrows, and summary.
"""

import discord
import logging
import re

log = logging.getLogger("red.pokemontcg")


# ── Helpers (duplicated from main/trade to avoid circular imports) ──

RARITY_COLORS = {
    "common": 0x8B8B8B,
    "uncommon": 0x3B82F6,
    "rare": 0xF59E0B,
    "rare holo": 0xEF4444,
    "energy": 0x10B981,
}

RARITY_EMOJI = {
    "rare holo": "✨",
    "rare": "⭐",
    "uncommon": "🔷",
    "common": "⚪",
    "energy": "🔋",
}

SHOWCASE_RARITIES = {"Rare Holo", "Rare"}

ASSET_BASE_URL = "https://pokesprites.joshkohut.com/pokemon_tcgd"


def _card_image_url(card: dict) -> str | None:
    image_file = card.get("image_file")
    if image_file:
        return f"{ASSET_BASE_URL}/{image_file}"
    return None


def _set_logo_url(set_id: str) -> str:
    return f"{ASSET_BASE_URL}/packart/{set_id}/logo.png"


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


_CUSTOM_EMOJI_RE = re.compile(r"<(a?):(\w+):(\d+)>")


def _parse_emoji(emoji_str: str) -> discord.PartialEmoji | str:
    match = _CUSTOM_EMOJI_RE.fullmatch(emoji_str)
    if match:
        return discord.PartialEmoji(
            name=match.group(2),
            id=int(match.group(3)),
            animated=bool(match.group(1)),
        )
    return emoji_str


def get_players_with_cards(database, guild_id: int) -> list[int]:
    """Return user_ids of all players who have cards in this guild."""
    rows = database.queryAll(
        """
        SELECT DISTINCT user_id
        FROM tcg_user_cards
        WHERE guild_id = %(guild_id)s
        ORDER BY user_id
        """,
        {"guild_id": guild_id},
    )
    return [row[0] for row in rows]


# ═══════════════════════════════════════════════════════════
#  Embed builder
# ═══════════════════════════════════════════════════════════

def build_showcase_card_embed(
    card_data: dict,
    count: int,
    index: int,
    total: int,
    set_name: str,
    display_name: str,
    rarity_filter: str,
) -> discord.Embed:
    """Build an embed for a single card in the showcase viewer."""
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

    image = _card_image_url(card_data)
    if image:
        embed.set_image(url=image)

    filter_label = f" • {rarity_filter}" if rarity_filter and rarity_filter != "All" else ""
    embed.set_footer(
        text=(
            f"#{local_id} • {set_name}{filter_label} • {display_rarity} • "
            f"Card {index + 1}/{total} • "
            f"👤 {display_name}'s collection"
        )
    )
    return embed


# ═══════════════════════════════════════════════════════════
#  Player Selector View
# ═══════════════════════════════════════════════════════════

class ShowcasePlayerSelector(discord.ui.View):
    """
    Dropdown to pick which player's showcase to view.

    Row 0: Player dropdown
    Row 1: View Showcase button
    """

    def __init__(
        self,
        cog,
        author_id: int,
        guild_id: int,
        player_ids: list[int],
        timeout: float = 120,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.author_id = author_id
        self.guild_id = guild_id
        self.player_ids = player_ids
        self.selected_player: int | None = None
        self.selected_name: str | None = None
        self.message: discord.Message | None = None

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
                description=f"View {name[:80]}'s Holos & Rares",
            ))

        if not options:
            options = [discord.SelectOption(label="No players found", value="none")]

        self.player_select.options = options

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Use `!tcg showcase` to browse someone's collection!",
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

    @discord.ui.select(placeholder="Choose a player to view...", row=0)
    async def player_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0]
        if val == "none":
            await interaction.response.send_message(
                "No players available to view.", ephemeral=True,
            )
            return
        self.selected_player = int(val)
        # Store the display name from the selected option
        for opt in self.player_select.options:
            opt.default = (opt.value == val)
            if opt.value == val:
                self.selected_name = opt.label
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="View Showcase",
        style=discord.ButtonStyle.success,
        emoji="🏆",
        row=1,
    )
    async def btn_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_player:
            await interaction.response.send_message(
                "Pick a player first!", ephemeral=True,
            )
            return

        display_name = self.selected_name or f"User {self.selected_player}"

        # Transition to the showcase viewer
        viewer = ShowcaseViewer(
            cog=self.cog,
            author_id=self.author_id,
            target_id=self.selected_player,
            guild_id=self.guild_id,
            display_name=display_name,
        )
        await viewer.initialize()

        self.stop()
        embed = viewer.get_embed()
        await interaction.response.edit_message(embed=embed, view=viewer)
        viewer.message = self.message


# ═══════════════════════════════════════════════════════════
#  Showcase Viewer (read-only, Holo + Rare only)
# ═══════════════════════════════════════════════════════════

class ShowcaseViewer(discord.ui.View):
    """
    Read-only collection browser showing another player's
    Rare Holo and Rare cards.

    Row 0: Set dropdown
    Row 1: Rarity filter (Holo / Rare / both)
    Row 2: ◀  (position)  ▶
    Row 3: Back to Player Select
    """

    def __init__(
        self,
        cog,
        author_id: int,
        target_id: int,
        guild_id: int,
        display_name: str,
        timeout: float = 300,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.author_id = author_id       # Who is browsing (controls interactions)
        self.target_id = target_id        # Whose cards we're viewing
        self.guild_id = guild_id
        self.display_name = display_name  # Target's display name
        self.message: discord.Message | None = None

        # State
        self.selected_set_id: str | None = None
        self.selected_rarity: str = "All"  # "All" (= both Holo+Rare), "Rare Holo", "Rare"
        self.filtered_cards: list[tuple[dict, int]] = []
        self.index: int = 0

        # Build set dropdown options
        sets = cog.card_pool.get_available_sets()
        options = []
        for s in sets:
            options.append(discord.SelectOption(
                label=s["name"],
                value=s["set_id"],
                description=f"{s['total_in_set']} cards • {s['year']}",
                emoji=_parse_emoji(s["emoji"]),
            ))
        self.set_filter.options = options

    async def initialize(self):
        """Load the target's collection for the first set."""
        sets = self.cog.card_pool.get_available_sets()
        if sets:
            self.selected_set_id = sets[0]["set_id"]
            for opt in self.set_filter.options:
                opt.default = (opt.value == self.selected_set_id)
            await self._reload_cards()
            self._rebuild_rarity_options()
        self._update_nav_buttons()

    async def _reload_cards(self):
        """Query DB for the target's Holo + Rare cards in the selected set."""
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
                    "user_id": self.target_id,
                    "guild_id": self.guild_id,
                    "set_id": self.selected_set_id,
                },
            )
        except Exception as e:
            log.error(f"Showcase query failed: {e}")
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

            # Only include Rare Holo and Rare cards
            if display_rarity not in SHOWCASE_RARITIES:
                continue

            all_cards.append((card_data, count, display_rarity))

        # Apply sub-filter (Rare Holo only, Rare only, or both)
        if self.selected_rarity and self.selected_rarity != "All":
            all_cards = [
                (cd, cnt, dr) for cd, cnt, dr in all_cards
                if dr == self.selected_rarity
            ]

        all_cards.sort(key=lambda x: _natural_sort_key(x[0].get("id", "")))
        self.filtered_cards = [(cd, cnt) for cd, cnt, _ in all_cards]
        self.index = 0

    def _rebuild_rarity_options(self):
        """Rebuild rarity dropdown — only Rare Holo and Rare options."""
        options = [discord.SelectOption(
            label="Holos & Rares",
            value="All",
            emoji="🏆",
            default=(self.selected_rarity == "All"),
        )]

        if self.selected_set_id:
            pool = self.cog.card_pool.sets.get(self.selected_set_id, {})
            if pool.get("rares_holo"):
                options.append(discord.SelectOption(
                    label="Rare Holo",
                    value="Rare Holo",
                    emoji="✨",
                    default=(self.selected_rarity == "Rare Holo"),
                ))
            if pool.get("rares_normal"):
                options.append(discord.SelectOption(
                    label="Rare",
                    value="Rare",
                    emoji="⭐",
                    default=(self.selected_rarity == "Rare"),
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
                title=f"🏆 {self.display_name}'s Showcase",
                description=(
                    f"No Holos or Rares in **{set_name}**{filter_text} yet.\n"
                    f"Try a different set!"
                ),
                color=0x3B82F6,
            )
            if self.selected_set_id:
                embed.set_thumbnail(url=_set_logo_url(self.selected_set_id))
            return embed

        card_data, count = self.filtered_cards[self.index]
        config = self.cog.card_pool.pack_config.get(self.selected_set_id or "", {})
        set_name = config.get("name", self.selected_set_id or "Unknown")

        return build_showcase_card_embed(
            card_data=card_data,
            count=count,
            index=self.index,
            total=len(self.filtered_cards),
            set_name=set_name,
            display_name=self.display_name,
            rarity_filter=self.selected_rarity,
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Use `!tcg showcase` to browse someone's collection!",
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