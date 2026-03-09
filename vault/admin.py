from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import asyncio
import io
import logging

import discord
from redbot.core import commands
from .abc import MixinMeta
from .db import VaultDB
from .renderer import render_card, resolve_art_path, save_art_file
from .constants import (
    EMBED_COLOR, STORE_EMBED_COLOR, COIN_EMOJI, ALL_CATEGORIES,
    RARITY_COLORS, RARITY_ORDER,
)

if TYPE_CHECKING:
    pass

log = logging.getLogger("red.vault.admin")

# Display helpers for the browse UI
CATEGORY_LABEL = {
    "superpower": "Superpowers",
    "ally": "Allies",
    "companion": "Companions",
    "item": "Items",
    "weapon": "Weapons",
    "armor": "Armor",
}

RARITY_DISPLAY = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "\u2728 Rare",
    "legendary": "\U0001f525 Legendary",
}


# ==================================================================
# BROWSE UI VIEWS
# ==================================================================

class BrowseView(discord.ui.View):
    """Interactive card browser with category dropdown and prev/next buttons."""

    def __init__(
        self,
        cog,
        ctx: commands.Context,
        cards: list[dict],
        category: str,
        index: int = 0,
    ):
        super().__init__(timeout=300)
        self.cog = cog
        self.ctx = ctx
        self.cards = cards         # all cards for current category
        self.category = category
        self.index = index
        self.message: Optional[discord.Message] = None

        self._update_buttons()
        self.add_item(BrowseCategorySelect(self, category))

    def _update_buttons(self):
        """Enable/disable prev/next based on current index."""
        self.prev_button.disabled = self.index <= 0
        self.next_button.disabled = self.index >= len(self.cards) - 1
        if self.cards:
            self.counter_button.label = f"{self.index + 1} / {len(self.cards)}"
        else:
            self.counter_button.label = "0 / 0"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your browse session.", ephemeral=True,
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
        """Render the current card and build the embed + file attachment."""
        if not self.cards:
            embed = discord.Embed(
                title="No Cards Found",
                description=f"No cards in the **{CATEGORY_LABEL.get(self.category, self.category)}** category.",
                color=EMBED_COLOR,
            )
            return embed, None

        card = self.cards[self.index]
        rarity_color = RARITY_COLORS.get(card["rarity"], EMBED_COLOR)

        embed = discord.Embed(
            title=f"{card['name']}",
            color=rarity_color,
        )
        embed.add_field(
            name="Category",
            value=CATEGORY_LABEL.get(card["category"], card["category"].title()),
            inline=True,
        )
        embed.add_field(
            name="Rarity",
            value=RARITY_DISPLAY.get(card["rarity"], card["rarity"].title()),
            inline=True,
        )
        embed.add_field(
            name="Card ID",
            value=f"#{card['id']}",
            inline=True,
        )
        store_status = "\u2705 In Store" if card.get("is_in_store") else "\u274c Not In Store"
        active_status = "\u2705 Active" if card.get("is_active") else "\u274c Inactive"
        embed.add_field(name="Status", value=f"{store_status} | {active_status}", inline=True)

        # Resolve art path: uses ArtFile if set, otherwise auto-derives from card name
        art_path = resolve_art_path(card["category"], card["name"], card.get("art_file"))

        # Show art status in embed
        art_status = "\u2705 Has Art" if art_path else "\u274c No Art"
        embed.add_field(name="Art", value=art_status, inline=True)

        try:
            png_bytes = await asyncio.to_thread(
                render_card,
                category=card["category"],
                name=card["name"],
                explanation=card["explanation"],
                blurb=card["blurb"],
                art_path=art_path,
            )
            file = discord.File(io.BytesIO(png_bytes), filename="card.png")
            embed.set_image(url="attachment://card.png")
        except Exception as e:
            log.error(f"Failed to render card {card['name']}: {e}")
            file = None
            embed.add_field(name="Description", value=card["explanation"], inline=False)
            embed.add_field(name="Details", value=card["blurb"], inline=False)

        embed.set_footer(
            text=f"Card {self.index + 1} of {len(self.cards)} in {CATEGORY_LABEL.get(self.category, self.category)}"
        )
        return embed, file

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

    # -- Navigation buttons --

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
        if self.index < len(self.cards) - 1:
            self.index += 1
        await self.update_message(interaction)

    @discord.ui.button(label="Update PNG", style=discord.ButtonStyle.primary, emoji="\U0001f5bc\ufe0f", row=0)
    async def upload_art_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Prompt the admin to upload a PNG for the current card."""
        if not self.cards:
            return await interaction.response.send_message(
                "No card selected to update.", ephemeral=True,
            )

        card = self.cards[self.index]
        await interaction.response.send_message(
            f"Upload a **.png** file for **{card['name']}** in your next message.\n"
            f"You have 60 seconds.",
            ephemeral=True,
        )

        def check(m: discord.Message) -> bool:
            return (
                m.author.id == interaction.user.id
                and m.channel.id == interaction.channel.id
                and len(m.attachments) > 0
            )

        try:
            msg = await self.cog.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            return await interaction.followup.send(
                "Timed out waiting for an image.", ephemeral=True,
            )

        # Validate the attachment
        attachment = msg.attachments[0]
        if not attachment.filename.lower().endswith(".png"):
            return await interaction.followup.send(
                "That's not a `.png` file. Upload cancelled.", ephemeral=True,
            )

        if attachment.size > 5 * 1024 * 1024:  # 5MB limit
            return await interaction.followup.send(
                "File is too large (max 5MB). Upload cancelled.", ephemeral=True,
            )

        # Download the image bytes
        try:
            img_bytes = await attachment.read()
        except discord.HTTPException:
            return await interaction.followup.send(
                "Failed to download the image. Try again.", ephemeral=True,
            )

        # Save to the correct directory with the correct name
        try:
            saved_path = await asyncio.to_thread(
                save_art_file,
                category=card["category"],
                card_name=card["name"],
                image_bytes=img_bytes,
            )
        except Exception as e:
            log.error(f"Failed to save art for {card['name']}: {e}")
            return await interaction.followup.send(
                f"Failed to save the image: {e}", ephemeral=True,
            )

        # Invalidate the rendered cache by nulling RenderedFile
        try:
            await asyncio.to_thread(
                VaultDB.update_card, card["id"], ArtFile=os.path.basename(saved_path),
            )
        except Exception as e:
            log.warning(f"Failed to update ArtFile on card {card['id']}: {e}")

        # Clean up the user's upload message if possible
        try:
            await msg.delete()
        except (discord.HTTPException, discord.Forbidden):
            pass

        await interaction.followup.send(
            f"\u2705 Art saved for **{card['name']}**! Refreshing preview...",
            ephemeral=True,
        )

        # Refresh the card data and re-render
        updated_cards = await asyncio.to_thread(
            VaultDB.browse_store_all, self.category
        )
        self.cards = updated_cards

        # Find the same card by ID in the refreshed list
        for i, c in enumerate(self.cards):
            if c["id"] == card["id"]:
                self.index = i
                break

        self._update_buttons()
        embed, file = await self._render_current()
        if file:
            await self.message.edit(embed=embed, view=self, attachments=[file])
        else:
            await self.message.edit(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="Done", style=discord.ButtonStyle.danger, emoji="\u2716\ufe0f", row=0)
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)
        self.stop()


class BrowseCategorySelect(discord.ui.Select):
    """Dropdown to switch between card categories in the browser."""

    def __init__(self, browse_view: BrowseView, current_category: str):
        self.browse_view = browse_view

        options = []
        for cat in ALL_CATEGORIES:
            label = CATEGORY_LABEL.get(cat, cat.title())
            is_default = cat == current_category
            options.append(
                discord.SelectOption(label=label, value=cat, default=is_default)
            )

        super().__init__(
            placeholder="Switch category...",
            options=options,
            min_values=1,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        new_category = self.values[0]

        cards = await asyncio.to_thread(
            VaultDB.browse_store_all, new_category
        )

        view = self.browse_view
        view.cards = cards
        view.category = new_category
        view.index = 0

        for item in view.children:
            if isinstance(item, BrowseCategorySelect):
                view.remove_item(item)
                break
        view.add_item(BrowseCategorySelect(view, new_category))

        await view.update_message(interaction)


# ==================================================================
# ADMIN MIXIN
# ==================================================================

# Need os import for the upload handler
import os


class AdminMixin(MixinMeta):
    """Admin commands for Vault card and store management."""

    __slots__: tuple = ()

    @commands.group(name="vaultadmin", aliases=["va"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def vaultadmin(self, ctx: commands.Context):
        """Admin commands for managing The Vault."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # ------------------------------------------------------------------
    # Browse cards (with rendered images)
    # ------------------------------------------------------------------

    @vaultadmin.command(name="browse")
    async def browse(self, ctx: commands.Context, category: str = "superpower"):
        """Browse all cards in the catalog with rendered card images.

        Use the dropdown to switch categories, arrows to cycle through cards.
        Use the Update PNG button to upload art for the current card.

        Example: `[p]va browse` or `[p]va browse weapon`
        """
        category = category.lower()
        if category not in ALL_CATEGORIES:
            categories = ", ".join(f"`{c}`" for c in ALL_CATEGORIES)
            return await ctx.send(f"Invalid category. Options: {categories}")

        cards = await asyncio.to_thread(VaultDB.browse_store_all, category)

        view = BrowseView(self, ctx, cards, category)
        embed, file = await view._render_current()

        kwargs = {"embed": embed, "view": view}
        if file:
            kwargs["file"] = file

        message = await ctx.send(**kwargs)
        view.message = message

    # ------------------------------------------------------------------
    # Store config
    # ------------------------------------------------------------------

    @vaultadmin.command(name="setprice")
    async def set_price(self, ctx: commands.Context, category: str, price: int):
        """Set the pull price for a category.

        Example: `[p]va setprice item 2`
        """
        category = category.lower()
        if category not in ALL_CATEGORIES:
            categories = ", ".join(f"`{c}`" for c in ALL_CATEGORIES)
            return await ctx.send(f"Invalid category. Options: {categories}")
        if price < 0:
            return await ctx.send("Price can't be negative.")

        await asyncio.to_thread(VaultDB.set_store_price, ctx.guild.id, category, price)
        await ctx.send(f"Pull price for **{category}** set to **{price}** {COIN_EMOJI}.")

    @vaultadmin.command(name="opencat")
    async def open_category(self, ctx: commands.Context, category: str):
        """Open a category in the store.

        Example: `[p]va opencat weapon`
        """
        category = category.lower()
        if category not in ALL_CATEGORIES:
            return await ctx.send(f"Invalid category.")

        await asyncio.to_thread(VaultDB.set_store_open, ctx.guild.id, category, True)
        await ctx.send(f"**{category.title()}** is now open in the store.")

    @vaultadmin.command(name="closecat")
    async def close_category(self, ctx: commands.Context, category: str):
        """Close a category in the store (players can't buy from it).

        Example: `[p]va closecat weapon`
        """
        category = category.lower()
        if category not in ALL_CATEGORIES:
            return await ctx.send(f"Invalid category.")

        await asyncio.to_thread(VaultDB.set_store_open, ctx.guild.id, category, False)
        await ctx.send(f"**{category.title()}** is now closed in the store.")

    @vaultadmin.command(name="storeconfig")
    async def store_config(self, ctx: commands.Context):
        """View current store configuration for this server."""
        config = await asyncio.to_thread(VaultDB.get_all_store_config, ctx.guild.id)

        embed = discord.Embed(
            title="Store Configuration",
            color=STORE_EMBED_COLOR,
        )

        for cat in ALL_CATEGORIES:
            cfg = config.get(cat, {"pull_price": 5, "is_open": True})
            status = "\u2705 Open" if cfg["is_open"] else "\u274c Closed"
            embed.add_field(
                name=cat.title(),
                value=f"Price: **{cfg['pull_price']}** {COIN_EMOJI}\nStatus: {status}",
                inline=True,
            )

        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Card management
    # ------------------------------------------------------------------

    @vaultadmin.command(name="addcard")
    async def add_card(self, ctx: commands.Context, category: str, rarity: str, *, text: str):
        """Add a card to the catalog.

        Use `|` to separate the name, explanation, and blurb.

        Example:
            `[p]va addcard item common Healing Potion | Restores a small amount of health. | A simple glass vial filled with a glowing red liquid. One sip mends minor wounds, but don't expect miracles.`
        """
        category = category.lower()
        rarity = rarity.lower()

        if category not in ALL_CATEGORIES:
            categories = ", ".join(f"`{c}`" for c in ALL_CATEGORIES)
            return await ctx.send(f"Invalid category. Options: {categories}")

        valid_rarities = ["common", "uncommon", "rare", "legendary"]
        if rarity not in valid_rarities:
            return await ctx.send(f"Invalid rarity. Options: {', '.join(valid_rarities)}")

        parts = text.split("|")
        if len(parts) != 3:
            return await ctx.send(
                "Use `|` to separate the three fields:\n"
                "`[p]va addcard <category> <rarity> <name> | <explanation> | <blurb>`\n\n"
                "Example:\n"
                "`[p]va addcard item common Healing Potion | Restores a small amount of health. | A simple glass vial filled with a glowing red liquid.`"
            )

        name = parts[0].strip()
        explanation = parts[1].strip()
        blurb = parts[2].strip()

        if not name:
            return await ctx.send("Card name can't be empty.")
        if not explanation:
            return await ctx.send("Explanation can't be empty.")
        if not blurb:
            return await ctx.send("Blurb can't be empty.")

        card_id = await asyncio.to_thread(
            VaultDB.add_card, name, category, rarity, explanation, blurb
        )

        embed = discord.Embed(
            title=f"Card Added — #{card_id}",
            description=f"**{name}**\n{category.title()} / {rarity.title()}",
            color=EMBED_COLOR,
        )
        embed.add_field(name="Explanation", value=explanation, inline=False)
        embed.add_field(name="Blurb", value=blurb, inline=False)
        embed.set_footer(text=f"Use `{ctx.prefix}va setprop {card_id} <key> <value>` to add properties")
        await ctx.send(embed=embed)

    @vaultadmin.command(name="setprop")
    async def set_prop(self, ctx: commands.Context, card_id: int, key: str, *, value: str):
        """Set a property on a card.

        Example: `[p]va setprop 1 consumable true`
        Example: `[p]va setprop 1 max_uses 3`
        """
        card = await asyncio.to_thread(VaultDB.get_card, card_id)
        if not card:
            return await ctx.send(f"No card found with ID **{card_id}**.")

        await asyncio.to_thread(VaultDB.set_card_property, card_id, key, value)
        await ctx.send(f"Set `{key}` = `{value}` on **{card['name']}** (#{card_id}).")

    @vaultadmin.command(name="delprop")
    async def del_prop(self, ctx: commands.Context, card_id: int, key: str):
        """Remove a property from a card.

        Example: `[p]va delprop 1 seasonal`
        """
        card = await asyncio.to_thread(VaultDB.get_card, card_id)
        if not card:
            return await ctx.send(f"No card found with ID **{card_id}**.")

        await asyncio.to_thread(VaultDB.remove_card_property, card_id, key)
        await ctx.send(f"Removed `{key}` from **{card['name']}** (#{card_id}).")

    @vaultadmin.command(name="listcards")
    async def list_cards(self, ctx: commands.Context, category: str = None, rarity: str = None):
        """List cards in the catalog.

        Example: `[p]va listcards` or `[p]va listcards weapon rare`
        """
        if category:
            category = category.lower()
        if rarity:
            rarity = rarity.lower()

        cards = await asyncio.to_thread(VaultDB.browse_store, category, rarity, limit=50)

        if not cards:
            return await ctx.send("No cards found matching those filters.")

        lines = []
        for card in cards:
            lines.append(
                f"`#{card['id']}` **{card['name']}** — {card['category'].title()} / {card['rarity'].title()}"
            )

        embed = discord.Embed(
            title="Card Catalog",
            description="\n".join(lines),
            color=EMBED_COLOR,
        )
        embed.set_footer(text=f"{len(cards)} cards shown")
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Grant / Revoke
    # ------------------------------------------------------------------

    @vaultadmin.command(name="grant")
    async def grant(self, ctx: commands.Context, member: discord.Member, card_id: int):
        """Grant a card to a player (no CC cost).

        Example: `[p]va grant @User 5`
        """
        card = await asyncio.to_thread(VaultDB.get_card, card_id)
        if not card:
            return await ctx.send(f"No card found with ID **{card_id}**.")

        inv_id = await asyncio.to_thread(
            VaultDB.grant_card, ctx.guild.id, member.id, card_id, "admin"
        )
        await ctx.send(
            f"Granted **{card['name']}** to {member.mention}. (Inventory ID: {inv_id})"
        )

    @vaultadmin.command(name="revoke")
    async def revoke(self, ctx: commands.Context, inv_id: int):
        """Revoke (retire) a card from a player's inventory by inventory ID.

        Example: `[p]va revoke 42`
        """
        item = await asyncio.to_thread(VaultDB.get_inventory_item, inv_id)
        if not item:
            return await ctx.send(f"No inventory item found with ID **{inv_id}**.")

        await asyncio.to_thread(VaultDB.retire_item, inv_id)
        await ctx.send(f"Revoked **{item['name']}** (inv #{inv_id}) from <@{item['user_id']}>.")