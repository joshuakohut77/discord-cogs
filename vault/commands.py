from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime
import asyncio
import io
import logging

import discord
from redbot.core import commands
from .abc import MixinMeta
from .db import VaultDB
from .renderer import render_card, resolve_art_path
from .constants import (
    COIN_EMOJI, COIN_EMOJI_URL, EMBED_COLOR, STORE_EMBED_COLOR,
    RARITY_COLORS, ALL_CATEGORIES, RARITY_ORDER, CATEGORY_ITEM,
)

if TYPE_CHECKING:
    pass

log = logging.getLogger("red.vault.commands")

# Separate emoji and label so select menus render emojis properly
CATEGORY_EMOJI = {
    "superpower": "\u2728",
    "ally": "\U0001f9d9",
    "companion": "\U0001f43e",
    "item": "\U0001f9ea",
    "weapon": "\u2694\ufe0f",
    "armor": "\U0001f6e1\ufe0f",
}

CATEGORY_LABEL = {
    "superpower": "Superpowers",
    "ally": "Allies",
    "companion": "Companions",
    "item": "Items",
    "weapon": "Weapons",
    "armor": "Armor",
}


def cat_display(cat: str) -> str:
    """Combined emoji + label for use in embeds and text."""
    emoji = CATEGORY_EMOJI.get(cat, "")
    label = CATEGORY_LABEL.get(cat, cat.title())
    return f"{emoji} {label}" if emoji else label

RARITY_DISPLAY = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "\u2728 Rare",
    "legendary": "\U0001f525 LEGENDARY",
}


# ==================================================================
# DISCORD UI VIEWS
# ==================================================================

class StoreView(discord.ui.View):
    """Main store view — category selection."""

    def __init__(self, cog, ctx: commands.Context, store_config: dict):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.store_config = store_config
        self.message: Optional[discord.Message] = None

        self.add_item(CategorySelect(store_config))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your store session. Use `[p]v store` to open your own.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass


class CategorySelect(discord.ui.Select):
    """Dropdown to pick a card category."""

    def __init__(self, store_config: dict):
        options = []
        for cat in ALL_CATEGORIES:
            config = store_config.get(cat, {"pull_price": 5, "is_open": True})
            if not config["is_open"]:
                continue
            label = CATEGORY_LABEL.get(cat, cat.title())
            emoji = CATEGORY_EMOJI.get(cat)
            price = config["pull_price"]
            options.append(
                discord.SelectOption(
                    label=label,
                    value=cat,
                    description=f"{price} ChodeCoin per pull",
                    emoji=emoji,
                )
            )

        if not options:
            options.append(
                discord.SelectOption(label="Store is closed", value="closed")
            )

        super().__init__(
            placeholder="Choose a category to pull from...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        if category == "closed":
            return await interaction.response.send_message(
                "The store is currently closed.", ephemeral=True
            )

        view: StoreView = self.view
        config = view.store_config.get(category, {"pull_price": 5})
        price = config["pull_price"]

        # Get availability info
        availability = await asyncio.to_thread(
            VaultDB.count_available_cards, interaction.guild.id, category
        )
        total_available = sum(availability.values())

        if total_available == 0:
            return await interaction.response.send_message(
                f"No **{category}** cards are available — the pool is depleted!",
                ephemeral=True,
            )

        # Get player balance
        balance = await asyncio.to_thread(
            VaultDB._get_cc_balance, interaction.guild.id, interaction.user.id
        )

        # Build info embed
        embed = discord.Embed(
            title=f"{cat_display(category)}",
            description=(
                f"**Cost:** {price} {COIN_EMOJI} per pull\n"
                f"**Your balance:** {balance} {COIN_EMOJI}\n\n"
                f"**Cards available in pool:**\n"
            ),
            color=STORE_EMBED_COLOR,
        )

        for rarity in RARITY_ORDER:
            count = availability.get(rarity, 0)
            display = RARITY_DISPLAY.get(rarity, rarity)
            embed.description += f"> {display}: **{count}** remaining\n"

        if category != CATEGORY_ITEM:
            embed.set_footer(text="Non-item cards are unique — only one owner per server!")

        # Show confirm view (not pull view yet)
        confirm_view = ConfirmPullView(
            view.cog, view.ctx, category, price, balance, view.store_config
        )
        confirm_view.message = view.message

        await interaction.response.edit_message(embed=embed, view=confirm_view)


class ConfirmPullView(discord.ui.View):
    """Intermediate confirmation step — player sees category info and confirms before pulling."""

    def __init__(self, cog, ctx, category, price, balance, store_config):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.category = category
        self.price = price
        self.balance = balance
        self.store_config = store_config
        self.message: Optional[discord.Message] = None

        if balance < price:
            self.confirm_button.disabled = True
            self.confirm_button.label = f"Not enough CC ({price} needed)"
            self.confirm_button.style = discord.ButtonStyle.secondary

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your store session.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Confirm Pull", style=discord.ButtonStyle.success, emoji="\U0001f0cf")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Transition to the actual pull
        pull_view = PullView(
            self.cog, self.ctx, self.category, self.price, self.balance, self.store_config
        )
        pull_view.message = self.message
        await pull_view.pull_button.callback(interaction)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, emoji="\u25c0\ufe0f")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = _build_store_front_embed(interaction.guild.name, self.store_config)
        store_view = StoreView(self.cog, self.ctx, self.store_config)
        store_view.message = self.message
        await interaction.response.edit_message(embed=embed, view=store_view)


class PullView(discord.ui.View):
    """Confirmation view with Pull and Back buttons."""

    def __init__(self, cog, ctx, category, price, balance, store_config):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.category = category
        self.price = price
        self.balance = balance
        self.store_config = store_config
        self.message: Optional[discord.Message] = None

        if balance < price:
            self.pull_button.disabled = True
            self.pull_button.label = f"Not enough CC ({price} needed)"
            self.pull_button.style = discord.ButtonStyle.secondary

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your store session.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Pull Card", style=discord.ButtonStyle.success, emoji="\U0001f0cf")
    async def pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons immediately to prevent double-pulls
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        # Show opening animation
        opening_embed = discord.Embed(
            title="\U0001f0cf Opening...",
            description=f"*Drawing from the {cat_display(self.category)} vault...*",
            color=EMBED_COLOR,
        )
        await interaction.edit_original_response(embed=opening_embed, view=None, attachments=[])

        # Brief suspense delay
        await asyncio.sleep(1.5)

        # Execute the pull
        result = await asyncio.to_thread(
            VaultDB.pull_card,
            interaction.guild.id,
            interaction.user.id,
            self.category,
        )

        if not result["success"]:
            error_embed = discord.Embed(
                title="Pull Failed",
                description=result["error"],
                color=0xff0000,
            )
            back_view = BackToStoreView(self.cog, self.ctx, self.store_config)
            back_view.message = self.message
            await interaction.edit_original_response(embed=error_embed, view=back_view)
            return

        # Build reveal embed with rendered card image
        card = result["card"]
        rarity = result["rarity_rolled"]
        reveal_embed, card_file = await _build_card_reveal(card, rarity, result, interaction.user)

        # Offer to pull again or go back
        after_view = AfterPullView(
            self.cog, self.ctx, self.category, result["new_balance"],
            self.store_config,
        )
        after_view.message = self.message

        kwargs = {"embed": reveal_embed, "view": after_view}
        if card_file:
            kwargs["attachments"] = [card_file]

        await interaction.edit_original_response(**kwargs)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, emoji="\u25c0\ufe0f")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = _build_store_front_embed(interaction.guild.name, self.store_config)
        store_view = StoreView(self.cog, self.ctx, self.store_config)
        store_view.message = self.message
        await interaction.response.edit_message(embed=embed, view=store_view)


class AfterPullView(discord.ui.View):
    """Shown after a successful pull — pull again or back to store."""

    def __init__(self, cog, ctx, category, balance, store_config):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.category = category
        self.balance = balance
        self.store_config = store_config
        self.message: Optional[discord.Message] = None

        price = store_config.get(category, {}).get("pull_price", 5)
        if balance < price:
            self.pull_again_button.disabled = True
            self.pull_again_button.label = f"Not enough CC ({price} needed)"
            self.pull_again_button.style = discord.ButtonStyle.secondary

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your store session.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Pull Again", style=discord.ButtonStyle.success, emoji="\U0001f504")
    async def pull_again_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.store_config.get(self.category, {"pull_price": 5})
        price = config["pull_price"]

        pull_view = PullView(
            self.cog, self.ctx, self.category, price, self.balance, self.store_config
        )
        pull_view.message = self.message
        await pull_view.pull_button.callback(interaction)

    @discord.ui.button(label="Back to Store", style=discord.ButtonStyle.secondary)
    async def back_to_store_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = _build_store_front_embed(interaction.guild.name, self.store_config)
        store_view = StoreView(self.cog, self.ctx, self.store_config)
        store_view.message = self.message
        await interaction.response.edit_message(embed=embed, view=store_view)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.secondary, emoji="\u2716\ufe0f")
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)


class BackToStoreView(discord.ui.View):
    """Simple view with just a back button after an error."""

    def __init__(self, cog, ctx, store_config):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.store_config = store_config
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            return False
        return True

    @discord.ui.button(label="Back to Store", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = _build_store_front_embed(interaction.guild.name, self.store_config)
        store_view = StoreView(self.cog, self.ctx, self.store_config)
        store_view.message = self.message
        await interaction.response.edit_message(embed=embed, view=store_view)


# ==================================================================
# INVENTORY BROWSE UI
# ==================================================================

class InventoryBrowseView(discord.ui.View):
    """Interactive inventory browser with category dropdown, prev/next, and rendered cards."""

    def __init__(
        self,
        cog,
        ctx: commands.Context,
        target: discord.Member | discord.User,
        all_items: list[dict],
        category: str,
        index: int = 0,
    ):
        super().__init__(timeout=300)
        self.cog = cog
        self.ctx = ctx
        self.target = target
        self.all_items = all_items       # full inventory (all categories)
        self.category = category
        self.index = index
        self.message: Optional[discord.Message] = None

        # Filter items for the current category
        self.items = [i for i in all_items if i["category"] == category]

        self._update_buttons()
        self.add_item(InventoryCategorySelect(self, all_items, category))

    def _update_buttons(self):
        """Enable/disable prev/next based on current index."""
        self.prev_button.disabled = self.index <= 0
        self.next_button.disabled = self.index >= len(self.items) - 1
        if self.items:
            self.counter_button.label = f"{self.index + 1} / {len(self.items)}"
        else:
            self.counter_button.label = "0 / 0"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your inventory session. Use `[p]v inv` to open your own.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

    async def _render_current(self) -> tuple[discord.Embed, Optional[discord.File]]:
        """Render the current inventory card and build embed + file."""
        if not self.items:
            embed = discord.Embed(
                title=f"\U0001f5c3\ufe0f {self.target.display_name}'s Vault",
                description=f"No **{CATEGORY_LABEL.get(self.category, self.category)}** cards in this collection.",
                color=EMBED_COLOR,
            )
            embed.set_thumbnail(url=self.target.display_avatar.url)
            return embed, None

        item = self.items[self.index]
        rarity_color = RARITY_COLORS.get(item["rarity"], EMBED_COLOR)

        embed = discord.Embed(
            title=item["name"],
            color=rarity_color,
        )
        embed.add_field(
            name="Category",
            value=cat_display(item["category"]),
            inline=True,
        )
        embed.add_field(
            name="Rarity",
            value=RARITY_DISPLAY.get(item["rarity"], item["rarity"].title()),
            inline=True,
        )
        equipped_str = "Yes \u2694\ufe0f" if item["is_equipped"] else "No"
        embed.add_field(name="Equipped", value=equipped_str, inline=True)

        # Build status lines from instance state and properties
        state = item["state"]
        props = item["properties"]
        state_lines = []

        if "uses_remaining" in state:
            max_uses = props.get("max_uses", "?")
            state_lines.append(f"Uses: **{state['uses_remaining']}** / {max_uses}")
        if "durability_remaining" in state:
            max_dur = props.get("durability", "?")
            state_lines.append(f"Durability: **{state['durability_remaining']}** / {max_dur}")
        if "fled_until" in state:
            try:
                fled_ts = int(datetime.fromisoformat(state["fled_until"]).timestamp())
                state_lines.append(f"\U0001f4a8 Fled — returns <t:{fled_ts}:R>")
            except (ValueError, TypeError):
                state_lines.append(f"\U0001f4a8 Fled")
        if "bond_level" in state:
            state_lines.append(f"Bond level: **{state['bond_level']}**")
        if props.get("passive_bonus"):
            state_lines.append(f"Passive: {props['passive_bonus']}")
        if props.get("cooldown_hours"):
            state_lines.append(f"Cooldown: {props['cooldown_hours']}h")
        if props.get("damage"):
            dmg_type = props.get("damage_type", "")
            state_lines.append(f"Damage: **{props['damage']}** {dmg_type}")
        if props.get("armor_value"):
            state_lines.append(f"Armor: **{props['armor_value']}**")
        if props.get("combat_power"):
            state_lines.append(f"Combat power: **{props['combat_power']}**")

        if state_lines:
            embed.add_field(name="Status", value="\n".join(state_lines), inline=False)

        # Render card image
        art_path = resolve_art_path(item["category"], item["name"], item.get("art_file"))
        card_file = None

        try:
            png_bytes = await asyncio.to_thread(
                render_card,
                category=item["category"],
                name=item["name"],
                explanation=item["explanation"],
                blurb=item["blurb"],
                art_path=art_path,
            )
            card_file = discord.File(io.BytesIO(png_bytes), filename="card.png")
            embed.set_image(url="attachment://card.png")
        except Exception as e:
            log.error(f"Failed to render card {item['name']} in inventory browse: {e}")
            # Fallback to text if render fails
            embed.add_field(name="Description", value=item["explanation"], inline=False)
            embed.add_field(name="Details", value=item["blurb"], inline=False)

        # Category totals for footer
        total = len(self.all_items)
        cat_count = len(self.items)
        cat_label = CATEGORY_LABEL.get(self.category, self.category.title())
        embed.set_footer(
            text=(
                f"Card {self.index + 1} of {cat_count} in {cat_label} "
                f"\u2022 {total} cards total "
                f"\u2022 Acquired via {item['acquired_via']}"
            ),
            icon_url=self.target.display_avatar.url,
        )

        return embed, card_file

    async def update_message(self, interaction: discord.Interaction):
        """Re-render and update the message."""
        self._update_buttons()
        embed, file = await self._render_current()

        if file:
            await interaction.response.edit_message(
                embed=embed, view=self, attachments=[file],
            )
        else:
            await interaction.response.edit_message(
                embed=embed, view=self, attachments=[],
            )

    # ------------------------------------------------------------------
    # Row 0: Navigation
    # ------------------------------------------------------------------

    @discord.ui.button(label="\u25c0", style=discord.ButtonStyle.secondary, row=0)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True, row=0)
    async def counter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="\u25b6", style=discord.ButtonStyle.secondary, row=0)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.items) - 1:
            self.index += 1
        await self.update_message(interaction)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.danger, emoji="\u2716\ufe0f", row=0)
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)
        self.stop()


class InventoryCategorySelect(discord.ui.Select):
    """Dropdown to switch between card categories in the inventory browser.

    Only shows categories the player actually has cards in.
    """

    def __init__(self, browse_view: InventoryBrowseView, all_items: list[dict], current_category: str):
        self.browse_view = browse_view

        # Determine which categories the player has cards in
        owned_cats = sorted(set(i["category"] for i in all_items), key=lambda c: ALL_CATEGORIES.index(c) if c in ALL_CATEGORIES else 99)

        options = []
        for cat in owned_cats:
            label = CATEGORY_LABEL.get(cat, cat.title())
            emoji = CATEGORY_EMOJI.get(cat)
            count = sum(1 for i in all_items if i["category"] == cat)
            is_default = cat == current_category
            options.append(
                discord.SelectOption(
                    label=label,
                    value=cat,
                    description=f"{count} card{'s' if count != 1 else ''}",
                    emoji=emoji,
                    default=is_default,
                )
            )

        # Safety fallback — shouldn't happen since we check for empty inventory before creating
        if not options:
            options.append(discord.SelectOption(label="No cards", value="none"))

        super().__init__(
            placeholder="Switch category...",
            options=options,
            min_values=1,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        new_category = self.values[0]
        if new_category == "none":
            return await interaction.response.defer()

        view = self.browse_view
        view.category = new_category
        view.items = [i for i in view.all_items if i["category"] == new_category]
        view.index = 0

        # Replace the dropdown with an updated one
        for item in view.children:
            if isinstance(item, InventoryCategorySelect):
                view.remove_item(item)
                break
        view.add_item(InventoryCategorySelect(view, view.all_items, new_category))

        await view.update_message(interaction)


# ==================================================================
# EMBED BUILDERS
# ==================================================================

def _build_store_front_embed(guild_name: str, store_config: dict) -> discord.Embed:
    """Build the main store landing page embed."""
    embed = discord.Embed(
        title="The Vault — Card Store",
        description=(
            "Spend your ChodeCoin to pull cards from the vault.\n"
            "Each pull gives you a random card — rarity is the gamble!\n\n"
            "**Available Categories:**\n"
        ),
        color=STORE_EMBED_COLOR,
    )

    for cat in ALL_CATEGORIES:
        config = store_config.get(cat, {"pull_price": 5, "is_open": True})
        if config["is_open"]:
            display = cat_display(cat)
            embed.description += f"> {display} — **{config['pull_price']}** {COIN_EMOJI} per pull\n"

    embed.set_footer(text=f"Select a category below to see available cards | {guild_name}")
    return embed


async def _build_card_reveal(
    card: dict,
    rarity: str,
    result: dict,
    user: discord.User | discord.Member,
) -> tuple[discord.Embed, Optional[discord.File]]:
    """Build the card reveal embed with the rendered card image.

    Returns (embed, file) — file may be None if rendering fails,
    in which case the embed falls back to text fields.
    """
    rarity_color = RARITY_COLORS.get(rarity, EMBED_COLOR)

    embed = discord.Embed(
        title=f"{RARITY_DISPLAY.get(rarity, rarity)} — {card['name']}",
        color=rarity_color,
    )
    embed.add_field(
        name="Category",
        value=cat_display(card["category"]),
        inline=True,
    )
    embed.add_field(
        name="Rarity",
        value=RARITY_DISPLAY.get(rarity, rarity),
        inline=True,
    )
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(
        name="Cost",
        value=f"-{result['price']} {COIN_EMOJI}",
        inline=True,
    )
    embed.add_field(
        name="Remaining Balance",
        value=f"{result['new_balance']} {COIN_EMOJI}",
        inline=True,
    )

    embed.set_footer(
        text=f"Pulled by {user.display_name}",
        icon_url=user.display_avatar.url,
    )

    # Render the card image
    art_path = resolve_art_path(card["category"], card["name"], card.get("art_file"))
    card_file = None

    try:
        png_bytes = await asyncio.to_thread(
            render_card,
            category=card["category"],
            name=card["name"],
            explanation=card["explanation"],
            blurb=card["blurb"],
            art_path=art_path,
        )
        card_file = discord.File(io.BytesIO(png_bytes), filename="card.png")
        embed.set_image(url="attachment://card.png")
    except Exception as e:
        log.error(f"Failed to render card {card['name']} during pull reveal: {e}")
        # Fallback: show text fields if rendering fails
        embed.add_field(name="Description", value=card["explanation"], inline=False)
        embed.add_field(name="Details", value=card["blurb"], inline=False)

    return embed, card_file


# ==================================================================
# COMMANDS MIXIN
# ==================================================================

class CommandsMixin(MixinMeta):
    """User-facing Vault commands."""

    __slots__: tuple = ()

    # ------------------------------------------------------------------
    # Command group
    # ------------------------------------------------------------------

    @commands.group(name="vault", aliases=["v"], invoke_without_command=True)
    @commands.guild_only()
    async def vault(self, ctx: commands.Context):
        """The Vault — your collection of cards, artifacts, and allies."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # ------------------------------------------------------------------
    # Store
    # ------------------------------------------------------------------

    @vault.command(name="store", aliases=["shop"])
    @commands.guild_only()
    async def store(self, ctx: commands.Context):
        """Open The Vault card store. Browse categories and pull cards."""
        store_config = await asyncio.to_thread(
            VaultDB.get_all_store_config, ctx.guild.id
        )

        embed = _build_store_front_embed(ctx.guild.name, store_config)
        view = StoreView(self, ctx, store_config)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    # ------------------------------------------------------------------
    # Quick pull (skip the store UI)
    # ------------------------------------------------------------------

    @vault.command(name="pull", aliases=["buy"])
    @commands.guild_only()
    async def quick_pull(self, ctx: commands.Context, category: Optional[str] = None):
        """Quick-pull a card from a category.

        Example: `[p]v pull item` or `[p]v buy weapon`
        """
        if not category or category.lower() not in ALL_CATEGORIES:
            categories = ", ".join(f"`{c}`" for c in ALL_CATEGORIES)
            return await ctx.send(f"Pick a category: {categories}")

        category = category.lower()

        result = await asyncio.to_thread(
            VaultDB.pull_card, ctx.guild.id, ctx.author.id, category
        )

        if not result["success"]:
            return await ctx.send(result["error"])

        card = result["card"]
        rarity = result["rarity_rolled"]
        embed, card_file = await _build_card_reveal(card, rarity, result, ctx.author)

        kwargs = {"embed": embed}
        if card_file:
            kwargs["file"] = card_file

        await ctx.send(**kwargs)

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    @vault.command(name="inventory", aliases=["inv", "cards"])
    @commands.guild_only()
    async def inventory(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Browse your card inventory (or another player's).

        Use the dropdown to switch categories and arrows to flip through cards.
        Each card is shown as a rendered image with its stats.

        Example: `[p]v inv` or `[p]v cards @User`
        """
        target = member or ctx.author
        items = await asyncio.to_thread(
            VaultDB.get_inventory, ctx.guild.id, target.id
        )

        if not items:
            if target == ctx.author:
                return await ctx.send("You don't have any cards yet. Visit the store with `[p]v store`!")
            return await ctx.send(f"{target.display_name} doesn't have any cards yet.")

        # Start on the first category that has cards (following ALL_CATEGORIES order)
        owned_cats = set(i["category"] for i in items)
        start_category = next(
            (c for c in ALL_CATEGORIES if c in owned_cats),
            items[0]["category"],
        )

        view = InventoryBrowseView(self, ctx, target, items, start_category)
        embed, file = await view._render_current()

        kwargs: dict = {"embed": embed, "view": view}
        if file:
            kwargs["file"] = file

        message = await ctx.send(**kwargs)
        view.message = message

    # ------------------------------------------------------------------
    # Inspect (quick jump into the browse UI focused on a specific card)
    # ------------------------------------------------------------------

    @vault.command(name="inspect", aliases=["info", "card"])
    @commands.guild_only()
    async def inspect(self, ctx: commands.Context, *, card_name: str):
        """Inspect a card from your inventory — opens the browser focused on it.

        Example: `[p]v inspect Shadow Wolf`
        """
        items = await asyncio.to_thread(
            VaultDB.get_inventory, ctx.guild.id, ctx.author.id
        )

        if not items:
            return await ctx.send("You don't have any cards yet.")

        # Find by name (case-insensitive)
        match = None
        for item in items:
            if item["name"].lower() == card_name.lower():
                match = item
                break

        if not match:
            return await ctx.send(f"You don't have a card called **{card_name}**.")

        # Find the index of this card within its category
        category = match["category"]
        cat_items = [i for i in items if i["category"] == category]
        card_index = 0
        for i, ci in enumerate(cat_items):
            if ci["inv_id"] == match["inv_id"]:
                card_index = i
                break

        view = InventoryBrowseView(self, ctx, ctx.author, items, category, index=card_index)
        embed, file = await view._render_current()

        kwargs: dict = {"embed": embed, "view": view}
        if file:
            kwargs["file"] = file

        message = await ctx.send(**kwargs)
        view.message = message