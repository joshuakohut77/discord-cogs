from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime
import asyncio
import logging

import discord
from redbot.core import commands
from .abc import MixinMeta
from .db import VaultDB
from .constants import (
    COIN_EMOJI, COIN_EMOJI_URL, EMBED_COLOR, STORE_EMBED_COLOR,
    RARITY_COLORS, ALL_CATEGORIES, RARITY_ORDER, CATEGORY_ITEM,
)

if TYPE_CHECKING:
    pass

log = logging.getLogger("red.vault.commands")

# Display names for categories
CATEGORY_DISPLAY = {
    "superpower": "\u2728 Superpowers",
    "ally": "\U0001f9d9 Allies",
    "companion": "\U0001f43e Companions",
    "item": "\U0001f9ea Items",
    "weapon": "\u2694\ufe0f Weapons",
    "armor": "\U0001f6e1\ufe0f Armor",
}

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
            label = CATEGORY_DISPLAY.get(cat, cat.title())
            price = config["pull_price"]
            options.append(
                discord.SelectOption(
                    label=label,
                    value=cat,
                    description=f"{price} ChodeCoin per pull",
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

        # Build confirmation embed
        embed = discord.Embed(
            title=f"{CATEGORY_DISPLAY.get(category, category.title())}",
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

        # Switch to pull view
        pull_view = PullView(view.cog, view.ctx, category, price, balance, view.store_config)
        pull_view.message = view.message

        await interaction.response.edit_message(embed=embed, view=pull_view)


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
            description=f"*Drawing from the {CATEGORY_DISPLAY.get(self.category, self.category)} vault...*",
            color=EMBED_COLOR,
        )
        await interaction.edit_original_response(embed=opening_embed, view=None)

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

        # Build reveal embed
        card = result["card"]
        rarity = result["rarity_rolled"]
        reveal_embed = _build_card_reveal_embed(card, rarity, result, interaction.user)

        # Offer to pull again or go back
        after_view = AfterPullView(
            self.cog, self.ctx, self.category, result["new_balance"],
            self.store_config,
        )
        after_view.message = self.message
        await interaction.edit_original_response(embed=reveal_embed, view=after_view)

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

    @discord.ui.button(label="Back to Store", style=discord.ButtonStyle.secondary, emoji="\U0001f3ea")
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

    @discord.ui.button(label="Back to Store", style=discord.ButtonStyle.secondary, emoji="\U0001f3ea")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = _build_store_front_embed(interaction.guild.name, self.store_config)
        store_view = StoreView(self.cog, self.ctx, self.store_config)
        store_view.message = self.message
        await interaction.response.edit_message(embed=embed, view=store_view)


# ==================================================================
# EMBED BUILDERS
# ==================================================================

def _build_store_front_embed(guild_name: str, store_config: dict) -> discord.Embed:
    """Build the main store landing page embed."""
    embed = discord.Embed(
        title="\U0001f3ea The Vault — Card Store",
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
            display = CATEGORY_DISPLAY.get(cat, cat.title())
            embed.description += f"> {display} — **{config['pull_price']}** {COIN_EMOJI} per pull\n"

    embed.set_footer(text=f"Select a category below to see available cards | {guild_name}")
    return embed


def _build_card_reveal_embed(
    card: dict,
    rarity: str,
    result: dict,
    user: discord.User | discord.Member,
) -> discord.Embed:
    """Build the card reveal embed after a successful pull."""
    rarity_color = RARITY_COLORS.get(rarity, EMBED_COLOR)

    embed = discord.Embed(
        title=f"{RARITY_DISPLAY.get(rarity, rarity)} — {card['name']}",
        color=rarity_color,
    )
    embed.add_field(
        name="Category",
        value=CATEGORY_DISPLAY.get(card["category"], card["category"].title()),
        inline=True,
    )
    embed.add_field(
        name="Rarity",
        value=RARITY_DISPLAY.get(rarity, rarity),
        inline=True,
    )
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Description", value=card["explanation"], inline=False)
    embed.add_field(name="Details", value=card["blurb"], inline=False)
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

    # TODO: Once PIL card renderer is built, attach the rendered card image
    # if card.get("rendered_file"):
    #     embed.set_image(url=f"attachment://card.png")

    return embed


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
        embed = _build_card_reveal_embed(card, rarity, result, ctx.author)
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    @vault.command(name="inventory", aliases=["inv", "cards"])
    @commands.guild_only()
    async def inventory(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """View your card inventory (or another player's).

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

        # Group by category
        by_category: dict[str, list] = {}
        for item in items:
            cat = item["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)

        embed = discord.Embed(
            title=f"\U0001f5c3\ufe0f {target.display_name}'s Vault",
            description=f"**{len(items)}** cards collected",
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        for cat in ALL_CATEGORIES:
            cat_items = by_category.get(cat, [])
            if not cat_items:
                continue

            lines = []
            for item in cat_items:
                rarity_icon = {
                    "common": "\u25cb",
                    "uncommon": "\u25cf",
                    "rare": "\U0001f535",
                    "legendary": "\u2b50",
                }.get(item["rarity"], "\u25cb")
                equipped = " \u2694\ufe0f" if item["is_equipped"] else ""
                fled = ""
                if item["state"].get("fled_until"):
                    fled = " \U0001f4a8"
                lines.append(f"{rarity_icon} {item['name']}{equipped}{fled}")

            display = CATEGORY_DISPLAY.get(cat, cat.title())
            embed.add_field(
                name=f"{display} ({len(cat_items)})",
                value="\n".join(lines),
                inline=True,
            )

        embed.set_footer(text="\u2694\ufe0f = equipped | \U0001f4a8 = fled | Use [p]v inspect <name> for details")
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Inspect
    # ------------------------------------------------------------------

    @vault.command(name="inspect", aliases=["info", "card"])
    @commands.guild_only()
    async def inspect(self, ctx: commands.Context, *, card_name: str):
        """Inspect a card from your inventory in detail.

        Example: `[p]v inspect Shadow Wolf`
        """
        items = await asyncio.to_thread(
            VaultDB.get_inventory, ctx.guild.id, ctx.author.id
        )

        # Find by name (case-insensitive)
        match = None
        for item in items:
            if item["name"].lower() == card_name.lower():
                match = item
                break

        if not match:
            return await ctx.send(f"You don't have a card called **{card_name}**.")

        rarity_color = RARITY_COLORS.get(match["rarity"], EMBED_COLOR)
        embed = discord.Embed(title=match["name"], color=rarity_color)

        embed.add_field(
            name="Category",
            value=CATEGORY_DISPLAY.get(match["category"], match["category"].title()),
            inline=True,
        )
        embed.add_field(
            name="Rarity",
            value=RARITY_DISPLAY.get(match["rarity"], match["rarity"]),
            inline=True,
        )
        equipped_str = "Yes \u2694\ufe0f" if match["is_equipped"] else "No"
        embed.add_field(name="Equipped", value=equipped_str, inline=True)

        embed.add_field(name="Description", value=match["explanation"], inline=False)
        embed.add_field(name="Details", value=match["blurb"], inline=False)

        # Show relevant state
        state = match["state"]
        props = match["properties"]
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
                state_lines.append("\U0001f4a8 Fled")
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

        embed.set_footer(text=f"Acquired via {match['acquired_via']} | ID: {match['inv_id']}")
        await ctx.send(embed=embed)