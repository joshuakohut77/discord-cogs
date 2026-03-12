from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import asyncio
import io
import os
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

import random
from .campaign_db import CampaignDB
from .dm_engine import DMEngine
from .campaign import _start_turn, CAMPAIGN_COLOR

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

VALID_RARITIES = ["common", "uncommon", "rare", "legendary"]


# ==================================================================
# HELPER: wait for a text message from the user
# ==================================================================

async def _wait_for_text(bot, user_id: int, channel_id: int, timeout: float = 60) -> Optional[discord.Message]:
    """Wait for the next text message from a user in a channel.

    Returns the Message, or None on timeout.
    """
    def check(m: discord.Message) -> bool:
        return m.author.id == user_id and m.channel.id == channel_id

    try:
        return await bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        return None


# ==================================================================
# BROWSE UI VIEWS
# ==================================================================

class BrowseView(discord.ui.View):
    """Interactive card browser with category dropdown and prev/next buttons.

    Layout:
      Row 0 — ◀  counter  ▶  Done
      Row 1 — BrowseCategorySelect (dropdown)
      Row 2 — Update PNG | Update Text | Add Card | Delete
      Row 3 — RaritySelect (dropdown)
      Row 4 — Toggle In Store | Toggle Active
    """

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
        self.add_item(RaritySelect(self))

    def _update_buttons(self):
        """Enable/disable prev/next and card-action buttons based on current state."""
        self.prev_button.disabled = self.index <= 0
        self.next_button.disabled = self.index >= len(self.cards) - 1
        if self.cards:
            self.counter_button.label = f"{self.index + 1} / {len(self.cards)}"
        else:
            self.counter_button.label = "0 / 0"

        has_cards = len(self.cards) > 0
        self.upload_art_button.disabled = not has_cards
        self.update_text_button.disabled = not has_cards
        self.delete_card_button.disabled = not has_cards

        # Toggle button labels and state
        self._refresh_toggle_buttons()

    def _refresh_toggle_buttons(self):
        """Update toggle button labels and disabled state to match the current card."""
        if not self.cards:
            self.toggle_store_button.label = "\U0001f6d2 In Store: —"
            self.toggle_store_button.style = discord.ButtonStyle.secondary
            self.toggle_store_button.disabled = True
            self.toggle_active_button.label = "\u2705 Active: —"
            self.toggle_active_button.style = discord.ButtonStyle.secondary
            self.toggle_active_button.disabled = True
            return

        card = self.cards[self.index]

        if card.get("is_in_store"):
            self.toggle_store_button.label = "\U0001f6d2 In Store: ON"
            self.toggle_store_button.style = discord.ButtonStyle.success
        else:
            self.toggle_store_button.label = "\U0001f6d2 In Store: OFF"
            self.toggle_store_button.style = discord.ButtonStyle.secondary
        self.toggle_store_button.disabled = False

        if card.get("is_active"):
            self.toggle_active_button.label = "\u2705 Active: ON"
            self.toggle_active_button.style = discord.ButtonStyle.success
        else:
            self.toggle_active_button.label = "\u274c Active: OFF"
            self.toggle_active_button.style = discord.ButtonStyle.danger
        self.toggle_active_button.disabled = False

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

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    async def _refresh_cards(self, focus_card_id: int):
        """Reload card data from DB and re-focus on a specific card by ID."""
        self.cards = await asyncio.to_thread(
            VaultDB.browse_store_all, self.category
        )
        for i, c in enumerate(self.cards):
            if c["id"] == focus_card_id:
                self.index = i
                return
        # If the card was deleted or not found, clamp index
        if self.index >= len(self.cards):
            self.index = max(0, len(self.cards) - 1)

    async def _restore_browse(self):
        """Re-render the browse view and edit it back onto the message."""
        # Rebuild dropdowns
        for item in list(self.children):
            if isinstance(item, (BrowseCategorySelect, RaritySelect)):
                self.remove_item(item)
        self.add_item(BrowseCategorySelect(self, self.category))
        self.add_item(RaritySelect(self))

        self._update_buttons()
        embed, file = await self._render_current()
        attachments = [file] if file else []
        await self.message.edit(embed=embed, view=self, attachments=attachments)

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
        if self.index < len(self.cards) - 1:
            self.index += 1
        await self.update_message(interaction)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.danger, emoji="\u2716\ufe0f", row=0)
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)
        self.stop()

    # ------------------------------------------------------------------
    # Row 2: Card actions  (row 1 = BrowseCategorySelect)
    # ------------------------------------------------------------------

    @discord.ui.button(label="Update PNG", style=discord.ButtonStyle.primary, emoji="\U0001f5bc\ufe0f", row=2)
    async def upload_art_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Prompt the admin to upload a PNG for the current card."""
        card = self.cards[self.index]
        cat_label = CATEGORY_LABEL.get(card["category"], card["category"].title())

        # Replace the browse embed with an upload prompt
        prompt_embed = discord.Embed(
            title="\U0001f5bc\ufe0f Upload Art",
            description=(
                f"Upload a **.png** file for **{cat_label} — {card['name']}**.\n\n"
                f"Send the image as an attachment in your next message.\n"
                f"You have 60 seconds."
            ),
            color=EMBED_COLOR,
        )
        await interaction.response.edit_message(embed=prompt_embed, view=None, attachments=[])

        def check(m: discord.Message) -> bool:
            return (
                m.author.id == interaction.user.id
                and m.channel.id == interaction.channel.id
                and len(m.attachments) > 0
            )

        try:
            msg = await self.cog.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            await self._restore_browse()
            return

        # Validate the attachment
        attachment = msg.attachments[0]
        if not attachment.filename.lower().endswith(".png"):
            await interaction.followup.send(
                "That's not a `.png` file. Upload cancelled.", ephemeral=True,
            )
            await self._restore_browse()
            return

        if attachment.size > 5 * 1024 * 1024:
            await interaction.followup.send(
                "File is too large (max 5MB). Upload cancelled.", ephemeral=True,
            )
            await self._restore_browse()
            return

        try:
            img_bytes = await attachment.read()
        except discord.HTTPException:
            await interaction.followup.send(
                "Failed to download the image. Try again.", ephemeral=True,
            )
            await self._restore_browse()
            return

        try:
            saved_path = await asyncio.to_thread(
                save_art_file,
                category=card["category"],
                card_name=card["name"],
                image_bytes=img_bytes,
            )
        except Exception as e:
            log.error(f"Failed to save art for {card['name']}: {e}")
            await interaction.followup.send(
                f"Failed to save the image: {e}", ephemeral=True,
            )
            await self._restore_browse()
            return

        # Update ArtFile column and invalidate render cache
        try:
            await asyncio.to_thread(
                VaultDB.update_card, card["id"], ArtFile=os.path.basename(saved_path),
            )
        except Exception as e:
            log.warning(f"Failed to update ArtFile on card {card['id']}: {e}")

        # Clean up upload message
        try:
            await msg.delete()
        except (discord.HTTPException, discord.Forbidden):
            pass

        await self._refresh_cards(card["id"])
        await self._restore_browse()

    @discord.ui.button(label="Update Text", style=discord.ButtonStyle.primary, emoji="\u270f\ufe0f", row=2)
    async def update_text_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Prompt the admin to update the name, explanation, and blurb of the current card."""
        card = self.cards[self.index]
        cat_label = CATEGORY_LABEL.get(card["category"], card["category"].title())
        rarity_label = RARITY_DISPLAY.get(card["rarity"], card["rarity"].title())

        prompt_embed = discord.Embed(
            title="\u270f\ufe0f Update Card Text",
            description=(
                f"Editing **{cat_label} — {card['name']}** (#{card['id']})\n\n"
                f"Send the updated text in this format:\n"
                f"`Name | Explanation | Blurb`\n\n"
                f"**Current values:**\n"
                f"> **Rarity:** {rarity_label}\n"
                f"> **Name:** {card['name']}\n"
                f"> **Explanation:** {card['explanation']}\n"
                f"> **Blurb:** {card['blurb']}\n\n"
                f"*(To change rarity, use the **Change Rarity** dropdown below.)*\n\n"
                f"You have 60 seconds."
            ),
            color=EMBED_COLOR,
        )
        await interaction.response.edit_message(embed=prompt_embed, view=None, attachments=[])

        msg = await _wait_for_text(self.cog.bot, interaction.user.id, interaction.channel.id)
        if msg is None:
            await self._restore_browse()
            return

        # Parse the input
        parts = msg.content.split("|")
        if len(parts) != 3:
            await interaction.followup.send(
                "Invalid format. Use: `Name | Explanation | Blurb`", ephemeral=True,
            )
            await self._restore_browse()
            return

        new_name = parts[0].strip()
        new_explanation = parts[1].strip()
        new_blurb = parts[2].strip()

        if not new_name or not new_explanation or not new_blurb:
            await interaction.followup.send(
                "Name, explanation, and blurb can't be empty.", ephemeral=True,
            )
            await self._restore_browse()
            return

        # Update the card in the database
        try:
            await asyncio.to_thread(
                VaultDB.update_card, card["id"],
                Name=new_name, Explanation=new_explanation, Blurb=new_blurb,
            )
        except Exception as e:
            log.error(f"Failed to update card text for {card['name']}: {e}")
            await interaction.followup.send(
                f"Failed to update card: {e}", ephemeral=True,
            )
            await self._restore_browse()
            return

        # Clean up input message
        try:
            await msg.delete()
        except (discord.HTTPException, discord.Forbidden):
            pass

        await self._refresh_cards(card["id"])
        await self._restore_browse()

    @discord.ui.button(label="Add Card", style=discord.ButtonStyle.success, emoji="\u2795", row=2)
    async def add_card_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Prompt the admin to add a new card to the current category."""
        cat_label = CATEGORY_LABEL.get(self.category, self.category.title())
        rarities_str = ", ".join(f"`{r}`" for r in VALID_RARITIES)

        prompt_embed = discord.Embed(
            title=f"\u2795 Add New {cat_label} Card",
            description=(
                f"Adding to **{cat_label}** category.\n\n"
                f"Send the new card in this format:\n"
                f"`Rarity | Name | Explanation | Blurb`\n\n"
                f"Valid rarities: {rarities_str}\n\n"
                f"**Example:**\n"
                f"> `rare | Deity of Sand | Commands the desert sands. | "
                f"An ancient being bound to the dunes. Its power shapes "
                f"sandstorms but each use erodes its physical form.`\n\n"
                f"You have 60 seconds."
            ),
            color=EMBED_COLOR,
        )
        await interaction.response.edit_message(embed=prompt_embed, view=None, attachments=[])

        msg = await _wait_for_text(self.cog.bot, interaction.user.id, interaction.channel.id)
        if msg is None:
            await self._restore_browse()
            return

        # Parse the input
        parts = msg.content.split("|")
        if len(parts) != 4:
            await interaction.followup.send(
                "Invalid format. Use: `Rarity | Name | Explanation | Blurb`", ephemeral=True,
            )
            await self._restore_browse()
            return

        rarity = parts[0].strip().lower()
        new_name = parts[1].strip()
        new_explanation = parts[2].strip()
        new_blurb = parts[3].strip()

        if rarity not in VALID_RARITIES:
            await interaction.followup.send(
                f"Invalid rarity `{rarity}`. Options: {', '.join(VALID_RARITIES)}", ephemeral=True,
            )
            await self._restore_browse()
            return

        if not new_name or not new_explanation or not new_blurb:
            await interaction.followup.send(
                "Name, explanation, and blurb can't be empty.", ephemeral=True,
            )
            await self._restore_browse()
            return

        # Insert into the database
        try:
            card_id = await asyncio.to_thread(
                VaultDB.add_card, new_name, self.category, rarity, new_explanation, new_blurb,
            )
        except Exception as e:
            log.error(f"Failed to add card '{new_name}': {e}")
            await interaction.followup.send(
                f"Failed to add card: {e}", ephemeral=True,
            )
            await self._restore_browse()
            return

        # Clean up input message
        try:
            await msg.delete()
        except (discord.HTTPException, discord.Forbidden):
            pass

        # Refresh and focus on the newly added card
        await self._refresh_cards(card_id)
        await self._restore_browse()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="\U0001f5d1\ufe0f", row=2)
    async def delete_card_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the current card from the database after confirmation."""
        card = self.cards[self.index]
        cat_label = CATEGORY_LABEL.get(card["category"], card["category"].title())
        rarity_label = RARITY_DISPLAY.get(card["rarity"], card["rarity"].title())

        # Show confirmation embed with confirm/cancel buttons
        confirm_embed = discord.Embed(
            title="\U0001f5d1\ufe0f Delete Card?",
            description=(
                f"Are you sure you want to **permanently delete** this card?\n\n"
                f"> **{card['name']}** (#{card['id']})\n"
                f"> {cat_label} / {rarity_label}\n"
                f"> {card['explanation']}\n\n"
                f"This will also remove it from all player inventories.\n"
                f"**This cannot be undone.**"
            ),
            color=0xff0000,
        )
        confirm_view = DeleteConfirmView(self, card)
        await interaction.response.edit_message(embed=confirm_embed, view=confirm_view, attachments=[])

    # ------------------------------------------------------------------
    # Row 3: RaritySelect dropdown  (added dynamically in __init__)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Row 4: Toggle In Store | Toggle Active
    # ------------------------------------------------------------------

    @discord.ui.button(label="\U0001f6d2 In Store: —", style=discord.ButtonStyle.secondary, row=4)
    async def toggle_store_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle the IsInStore flag on the current card."""
        card = self.cards[self.index]
        new_value = not card.get("is_in_store", True)

        try:
            await asyncio.to_thread(VaultDB.update_card, card["id"], IsInStore=new_value)
        except Exception as e:
            log.error(f"Failed to toggle IsInStore on card {card['id']}: {e}")
            return await interaction.response.send_message(
                f"Failed to update card: {e}", ephemeral=True,
            )

        await self._refresh_cards(card["id"])
        await self.update_message(interaction)

    @discord.ui.button(label="\u2705 Active: —", style=discord.ButtonStyle.secondary, row=4)
    async def toggle_active_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle the IsActive flag on the current card."""
        card = self.cards[self.index]
        new_value = not card.get("is_active", True)

        try:
            await asyncio.to_thread(VaultDB.update_card, card["id"], IsActive=new_value)
        except Exception as e:
            log.error(f"Failed to toggle IsActive on card {card['id']}: {e}")
            return await interaction.response.send_message(
                f"Failed to update card: {e}", ephemeral=True,
            )

        await self._refresh_cards(card["id"])
        await self.update_message(interaction)


class RaritySelect(discord.ui.Select):
    """Dropdown to change the rarity of the currently displayed card."""

    def __init__(self, browse_view: BrowseView):
        self.browse_view = browse_view

        current_rarity = None
        if browse_view.cards:
            current_rarity = browse_view.cards[browse_view.index].get("rarity")

        rarity_emojis = {
            "common": "\u26aa",      # grey circle
            "uncommon": "\U0001f7e2", # green circle
            "rare": "\U0001f535",     # blue circle
            "legendary": "\U0001f7e1",# yellow circle
        }

        options = [
            discord.SelectOption(
                label=RARITY_DISPLAY.get(r, r.title()),
                value=r,
                emoji=rarity_emojis.get(r),
                default=(r == current_rarity),
            )
            for r in VALID_RARITIES
        ]

        super().__init__(
            placeholder="Change rarity...",
            options=options,
            min_values=1,
            max_values=1,
            disabled=not browse_view.cards,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.browse_view
        if not view.cards:
            return await interaction.response.defer()

        card = view.cards[view.index]
        new_rarity = self.values[0]

        if new_rarity == card.get("rarity"):
            # No change — just defer silently
            return await interaction.response.defer()

        try:
            await asyncio.to_thread(VaultDB.update_card, card["id"], Rarity=new_rarity)
        except Exception as e:
            log.error(f"Failed to update rarity for card {card['id']}: {e}")
            return await interaction.response.send_message(
                f"Failed to update rarity: {e}", ephemeral=True,
            )

        await view._refresh_cards(card["id"])
        await view.update_message(interaction)


class DeleteConfirmView(discord.ui.View):
    """Confirmation step for card deletion."""

    def __init__(self, browse_view: BrowseView, card: dict):
        super().__init__(timeout=30)
        self.browse_view = browse_view
        self.card = card

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.browse_view.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your browse session.", ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        # Timed out waiting for confirmation — restore browse
        await self.browse_view._restore_browse()

    @discord.ui.button(label="Yes, Delete", style=discord.ButtonStyle.danger, emoji="\U0001f5d1\ufe0f")
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        card = self.card

        try:
            await asyncio.to_thread(VaultDB.delete_card, card["id"])
        except Exception as e:
            log.error(f"Failed to delete card {card['name']} (#{card['id']}): {e}")
            await interaction.response.send_message(
                f"Failed to delete card: {e}", ephemeral=True,
            )
            await self.browse_view._restore_browse()
            return

        # Disable buttons immediately
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        # Refresh card list (the deleted card will be gone)
        bv = self.browse_view
        bv.cards = await asyncio.to_thread(
            VaultDB.browse_store_all, bv.category
        )
        if bv.index >= len(bv.cards):
            bv.index = max(0, len(bv.cards) - 1)

        await bv._restore_browse()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Just restore the browse view
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await self.browse_view._restore_browse()


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

        # Rebuild both dropdowns
        for item in list(view.children):
            if isinstance(item, (BrowseCategorySelect, RaritySelect)):
                view.remove_item(item)
        view.add_item(BrowseCategorySelect(view, new_category))
        view.add_item(RaritySelect(view))

        await view.update_message(interaction)


# ==================================================================
# ADMIN MIXIN
# ==================================================================

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

        **Action buttons:**
        \u2022 **Update PNG** — upload new art for the current card
        \u2022 **Update Text** — edit name, explanation, and blurb
        \u2022 **Add Card** — add a new card to the current category
        \u2022 **Delete** — permanently remove the current card
        \u2022 **Change Rarity** — change rarity via dropdown
        \u2022 **Toggle In Store** — toggle whether the card appears in the store
        \u2022 **Toggle Active** — toggle whether the card is active

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

        if rarity not in VALID_RARITIES:
            return await ctx.send(f"Invalid rarity. Options: {', '.join(VALID_RARITIES)}")

        parts = text.split("|")
        if len(parts) != 3:
            return await ctx.send(
                "Use `|` to separate the three fields:\n"
                "`[p]va addcard <category> <rarity> <n> | <explanation> | <blurb>`\n\n"
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

    # ------------------------------------------------------------------
    # Campaign management
    # ------------------------------------------------------------------

    @vaultadmin.command(name="startcampaign", aliases=["sc"])
    async def start_campaign(self, ctx: commands.Context, *members: discord.Member):
        """Start a new campaign with the specified players.

        This registers all players, generates a random turn order,
        builds the campaign narrative, and begins the first turn.

        Example: `[p]va startcampaign @User1 @User2 @User3`
        """
        if len(members) < 1:
            return await ctx.send("You need at least 1 player to start a campaign.")

        # Check for duplicates
        unique_members = list({m.id: m for m in members}.values())
        if len(unique_members) != len(members):
            return await ctx.send("Duplicate players detected. Each player can only be listed once.")

        # Check for bots
        if any(m.bot for m in unique_members):
            return await ctx.send("Bots can't participate in campaigns.")

        # Create campaign
        try:
            campaign_id = await asyncio.to_thread(
                CampaignDB.create_campaign, ctx.guild.id, ctx.channel.id,
            )
        except ValueError as e:
            return await ctx.send(str(e))

        # Register players
        for member in unique_members:
            await asyncio.to_thread(
                CampaignDB.add_player, campaign_id, member.id, member.display_name,
            )

        # Generate random turn order
        user_ids = [m.id for m in unique_members]
        random.shuffle(user_ids)
        await asyncio.to_thread(CampaignDB.set_turn_order, campaign_id, user_ids)

        # Get players for DM engine
        players = await asyncio.to_thread(CampaignDB.get_players, campaign_id)

        # Build turn order display
        turn_order_display = "\n".join(
            f"**{i+1}.** <@{uid}>" for i, uid in enumerate(user_ids)
        )

        # Starting embed
        setup_embed = discord.Embed(
            title="\U0001f3ad The Vault — Campaign Begins",
            description=(
                f"**Players ({len(unique_members)}):**\n"
                f"{turn_order_display}\n\n"
                f"Generating the campaign..."
            ),
            color=CAMPAIGN_COLOR,
        )
        await ctx.send(embed=setup_embed)

        # Generate campaign opening
        await DMEngine.generate_campaign_start(
            campaign_id=campaign_id,
            guild_id=str(ctx.guild.id),
            players=players,
        )

        # Activate the campaign
        await asyncio.to_thread(
            CampaignDB.set_campaign_status, campaign_id, "active",
        )

        # Get the fresh campaign state
        campaign = await asyncio.to_thread(
            CampaignDB.get_active_campaign, ctx.guild.id,
        )

        # Start the first turn
        await _start_turn(self, ctx.channel, campaign)

    @vaultadmin.command(name="endcampaign", aliases=["ec"])
    async def end_campaign(self, ctx: commands.Context):
        """Force-end the current campaign.

        Example: `[p]va endcampaign`
        """
        campaign = await asyncio.to_thread(
            CampaignDB.get_active_campaign, ctx.guild.id,
        )
        if not campaign:
            return await ctx.send("No active campaign in this server.")

        # Generate ending narrative
        ending = await DMEngine.generate_campaign_ending(
            campaign["id"], reason="admin_ended",
        )

        # End the campaign
        await asyncio.to_thread(
            CampaignDB.set_campaign_status, campaign["id"], "ended",
        )

        embed = discord.Embed(
            title="\U0001f3c1 Campaign Ended",
            description=ending,
            color=CAMPAIGN_COLOR,
        )
        turns = await asyncio.to_thread(CampaignDB.get_turn_count, campaign["id"])
        embed.set_footer(text=f"Campaign #{campaign['id']} \u2022 {campaign['current_round']} rounds \u2022 {turns} turns taken")
        await ctx.send(embed=embed)

    @vaultadmin.command(name="resume")
    async def resume_campaign(self, ctx: commands.Context):
        """Resume a campaign after a timeout or bot restart.

        Re-renders the current DM prompt and active player's inventory
        with fresh buttons.

        Example: `[p]va resume`
        """
        campaign = await asyncio.to_thread(
            CampaignDB.get_active_campaign, ctx.guild.id,
        )
        if not campaign:
            return await ctx.send("No active campaign to resume.")

        if campaign["status"] not in ("active", "paused"):
            return await ctx.send("Campaign isn't in a resumable state.")

        # If paused, reactivate
        if campaign["status"] == "paused":
            await asyncio.to_thread(
                CampaignDB.set_campaign_status, campaign["id"], "active",
            )

        await ctx.send("\U0001f504 **Resuming campaign...**")

        # Re-start the current turn
        await _start_turn(self, ctx.channel, campaign)

    @vaultadmin.command(name="pausecampaign", aliases=["pc"])
    async def pause_campaign(self, ctx: commands.Context):
        """Pause the current campaign. Use `[p]va resume` to continue.

        Example: `[p]va pausecampaign`
        """
        campaign = await asyncio.to_thread(
            CampaignDB.get_active_campaign, ctx.guild.id,
        )
        if not campaign:
            return await ctx.send("No active campaign.")
        if campaign["status"] != "active":
            return await ctx.send("Campaign isn't active.")

        await asyncio.to_thread(
            CampaignDB.set_campaign_status, campaign["id"], "paused",
        )
        await ctx.send("\u23f8\ufe0f **Campaign paused.** Use `[p]va resume` to continue.")