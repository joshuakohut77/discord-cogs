from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import asyncio
import io
import logging
import random

import discord
from redbot.core import commands
from .db import VaultDB
from .campaign_db import CampaignDB
from .dm_engine import DMEngine
from .renderer import render_card, resolve_art_path
from .constants import (
    EMBED_COLOR, RARITY_COLORS, ALL_CATEGORIES, RARITY_ORDER, COIN_EMOJI,
)

if TYPE_CHECKING:
    from redbot.core.bot import Red

log = logging.getLogger("red.vault.campaign")

# ---------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------

CAMPAIGN_COLOR = 0x4B0082  # indigo — distinct from store/admin

CATEGORY_LABEL = {
    "superpower": "Superpowers",
    "ally": "Allies",
    "companion": "Companions",
    "item": "Items",
    "weapon": "Weapons",
    "armor": "Armor",
}

CATEGORY_EMOJI = {
    "superpower": "\u2728",
    "ally": "\U0001f9d9",
    "companion": "\U0001f43e",
    "item": "\U0001f9ea",
    "weapon": "\u2694\ufe0f",
    "armor": "\U0001f6e1\ufe0f",
}

RARITY_DISPLAY = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "\u2728 Rare",
    "legendary": "\U0001f525 Legendary",
}


# ==================================================================
# ACTION TEXT MODAL
# ==================================================================

class ActionTextModal(discord.ui.Modal, title="Describe Your Action"):
    """Modal for entering free-text action description."""

    action_input = discord.ui.TextInput(
        label="What do you do?",
        style=discord.TextStyle.paragraph,
        placeholder="Describe your action in detail...",
        required=True,
        max_length=1000,
    )

    def __init__(self, campaign_view: "CampaignTurnView", include_card: bool = False):
        super().__init__()
        self.campaign_view = campaign_view
        self.include_card = include_card

    async def on_submit(self, interaction: discord.Interaction):
        action_text = self.action_input.value.strip()
        if not action_text:
            return await interaction.response.send_message(
                "Action text can't be empty.", ephemeral=True,
            )

        card = None
        if self.include_card:
            card = self.campaign_view.get_selected_card()
            if not card:
                return await interaction.response.send_message(
                    "No card selected. Navigate to a card first, then use Play Both.",
                    ephemeral=True,
                )

        action_type = "both" if self.include_card and card else "action"
        await self.campaign_view.execute_turn(interaction, action_type, card=card, action_text=action_text)


class QuestionModal(discord.ui.Modal, title="Ask the Dungeon Master"):
    """Modal for asking a question that doesn't consume a turn."""

    question_input = discord.ui.TextInput(
        label="Your question",
        style=discord.TextStyle.paragraph,
        placeholder="Ask about your surroundings, an object, a sound...",
        required=True,
        max_length=500,
    )

    def __init__(self, campaign_view: "CampaignTurnView"):
        super().__init__()
        self.campaign_view = campaign_view

    async def on_submit(self, interaction: discord.Interaction):
        question = self.question_input.value.strip()
        if not question:
            return await interaction.response.send_message(
                "Question can't be empty.", ephemeral=True,
            )
        await self.campaign_view.handle_question(interaction, question)


# ==================================================================
# CAMPAIGN DM PROMPT VIEW (shown to all players)
# ==================================================================

class CampaignDMView(discord.ui.View):
    """The main campaign view shown after each DM prompt.

    Contains:
    - Show Cards button (ephemeral inventory for non-active players)
    - Ask Question button (1 per player per turn)
    """

    def __init__(self, cog, campaign: dict, dm_text: str):
        super().__init__(timeout=None)  # No timeout — campaign persists
        self.cog = cog
        self.campaign = campaign
        self.dm_text = dm_text
        self.message: Optional[discord.Message] = None

    def _get_active_user_id(self) -> Optional[str]:
        """Get the user ID of the current active player."""
        order = self.campaign["turn_order"]
        idx = self.campaign["current_turn_index"]
        if order and 0 <= idx < len(order):
            return order[idx]
        return None

    @discord.ui.button(label="Show My Cards", style=discord.ButtonStyle.secondary, emoji="\U0001f0cf", row=0)
    async def show_cards_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show the requesting player's inventory ephemerally."""
        # Check if player is in the campaign
        campaign = self.campaign
        if not await asyncio.to_thread(
            CampaignDB.is_player_in_campaign, campaign["id"], interaction.user.id
        ):
            return await interaction.response.send_message(
                "You're not part of this campaign.", ephemeral=True,
            )

        items = await asyncio.to_thread(
            VaultDB.get_inventory, int(campaign["guild_id"]), interaction.user.id
        )

        if not items:
            return await interaction.response.send_message(
                "You don't have any cards.", ephemeral=True,
            )

        # Build a simple text inventory (ephemeral, no rendered images for speed)
        cat_groups: dict[str, list] = {}
        for item in items:
            cat_groups.setdefault(item["category"], []).append(item)

        embed = discord.Embed(
            title=f"\U0001f0cf {interaction.user.display_name}'s Cards",
            color=EMBED_COLOR,
        )
        for cat in ALL_CATEGORIES:
            if cat not in cat_groups:
                continue
            cat_items = cat_groups[cat]
            lines = []
            for it in cat_items:
                equipped = " \u2694\ufe0f" if it["is_equipped"] else ""
                rarity = RARITY_DISPLAY.get(it["rarity"], it["rarity"])
                lines.append(f"**{it['name']}** ({rarity}){equipped}")
                lines.append(f"> {it['explanation']}")
            emoji = CATEGORY_EMOJI.get(cat, "")
            label = CATEGORY_LABEL.get(cat, cat.title())
            embed.add_field(
                name=f"{emoji} {label} ({len(cat_items)})",
                value="\n".join(lines),
                inline=False,
            )

        embed.set_footer(text=f"{len(items)} cards total")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Ask Question", style=discord.ButtonStyle.primary, emoji="\u2753", row=0)
    async def ask_question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Let any campaign player ask the DM a question (1 per turn)."""
        campaign = self.campaign
        if not await asyncio.to_thread(
            CampaignDB.is_player_in_campaign, campaign["id"], interaction.user.id
        ):
            return await interaction.response.send_message(
                "You're not part of this campaign.", ephemeral=True,
            )

        questions_used = await asyncio.to_thread(
            CampaignDB.get_questions_used, campaign["id"], interaction.user.id
        )
        if questions_used >= 1:
            return await interaction.response.send_message(
                "You've already asked your question this turn.", ephemeral=True,
            )

        # We need a reference to the active turn view to handle the question
        # The question modal will handle it through the DM engine directly
        modal = CampaignQuestionModalStandalone(self.cog, campaign, interaction.user)
        await interaction.response.send_modal(modal)


class CampaignQuestionModalStandalone(discord.ui.Modal, title="Ask the Dungeon Master"):
    """Standalone question modal triggered from the DM view."""

    question_input = discord.ui.TextInput(
        label="Your question",
        style=discord.TextStyle.paragraph,
        placeholder="Ask about your surroundings, an object, a sound...",
        required=True,
        max_length=500,
    )

    def __init__(self, cog, campaign: dict, user: discord.User | discord.Member):
        super().__init__()
        self.cog = cog
        self.campaign = campaign
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        question = self.question_input.value.strip()
        if not question:
            return await interaction.response.send_message(
                "Question can't be empty.", ephemeral=True,
            )

        # Check and consume the question allowance
        used = await asyncio.to_thread(
            CampaignDB.use_question, self.campaign["id"], interaction.user.id
        )
        if not used:
            return await interaction.response.send_message(
                "You've already asked your question this turn.", ephemeral=True,
            )

        await interaction.response.defer()

        # Get DM's answer
        answer = await DMEngine.answer_question(
            campaign_id=self.campaign["id"],
            guild_id=self.campaign["guild_id"],
            user_id=str(interaction.user.id),
            display_name=interaction.user.display_name,
            question=question,
        )

        # Post the Q&A publicly
        embed = discord.Embed(
            title=f"\u2753 {interaction.user.display_name} asks...",
            description=f"*\"{question}\"*",
            color=CAMPAIGN_COLOR,
        )
        embed.add_field(name="The Dungeon Master responds:", value=answer, inline=False)
        embed.set_footer(text="This did not consume a turn.")
        await interaction.followup.send(embed=embed)


# ==================================================================
# CAMPAIGN TURN VIEW (active player's inventory + action buttons)
# ==================================================================

class CampaignTurnView(discord.ui.View):
    """Active player's turn interface.

    Shows their inventory with prev/next navigation,
    plus action buttons: Play Card, Action, Play Both.
    """

    def __init__(
        self,
        cog,
        campaign: dict,
        player_user: discord.Member,
        items: list[dict],
        category: str,
        index: int = 0,
    ):
        super().__init__(timeout=None)  # No timeout — resume handles recovery
        self.cog = cog
        self.campaign = campaign
        self.player_user = player_user
        self.all_items = items
        self.category = category
        self.index = index
        self.message: Optional[discord.Message] = None
        self.turn_submitted = False

        # Filter for current category
        self.items = [i for i in items if i["category"] == category]

        self._update_buttons()
        if items:
            self.add_item(CampaignCategorySelect(self, items, category))

    def _update_buttons(self):
        self.prev_button.disabled = self.index <= 0
        self.next_button.disabled = self.index >= len(self.items) - 1
        if self.items:
            self.counter_button.label = f"{self.index + 1} / {len(self.items)}"
        else:
            self.counter_button.label = "0 / 0"

        # Disable action buttons if turn already submitted
        has_cards = len(self.items) > 0
        self.play_card_button.disabled = self.turn_submitted or not has_cards
        self.play_both_button.disabled = self.turn_submitted or not has_cards
        self.action_button.disabled = self.turn_submitted

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_user.id:
            await interaction.response.send_message(
                f"It's **{self.player_user.display_name}**'s turn right now.",
                ephemeral=True,
            )
            return False
        return True

    def get_selected_card(self) -> Optional[dict]:
        """Get the currently displayed card."""
        if not self.items or self.index >= len(self.items):
            return None
        return self.items[self.index]

    async def _render_current(self) -> tuple[discord.Embed, Optional[discord.File]]:
        """Render the current inventory card."""
        embed = discord.Embed(
            title=f"\u2694\ufe0f {self.player_user.display_name}'s Turn — Round {self.campaign['current_round']}",
            color=CAMPAIGN_COLOR,
        )

        if not self.items:
            embed.description = (
                f"No **{CATEGORY_LABEL.get(self.category, self.category)}** cards.\n\n"
                f"Use the dropdown to switch categories, or use **Action** to describe what you do."
            )
            return embed, None

        item = self.items[self.index]
        rarity_color = RARITY_COLORS.get(item["rarity"], EMBED_COLOR)
        embed.color = rarity_color

        embed.add_field(
            name="Card",
            value=f"**{item['name']}**",
            inline=True,
        )
        embed.add_field(
            name="Category",
            value=CATEGORY_LABEL.get(item["category"], item["category"].title()),
            inline=True,
        )
        embed.add_field(
            name="Rarity",
            value=RARITY_DISPLAY.get(item["rarity"], item["rarity"]),
            inline=True,
        )

        # Status from properties and state
        props = item.get("properties", {})
        state = item.get("state", {})
        status_lines = []
        if item.get("is_equipped"):
            status_lines.append("\u2694\ufe0f Equipped")
        if "uses_remaining" in state:
            status_lines.append(f"Uses: {state['uses_remaining']}/{props.get('max_uses', '?')}")
        if "durability_remaining" in state:
            status_lines.append(f"Durability: {state['durability_remaining']}/{props.get('durability', '?')}")
        if props.get("damage"):
            dtype = props.get("damage_type", "")
            status_lines.append(f"Damage: {props['damage']} {dtype}")
        if props.get("armor_value"):
            status_lines.append(f"Armor: {props['armor_value']}")
        if props.get("combat_power"):
            status_lines.append(f"Combat: {props['combat_power']}")
        if status_lines:
            embed.add_field(name="Status", value=" | ".join(status_lines), inline=False)

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
            log.error(f"Campaign card render failed for {item['name']}: {e}")
            embed.add_field(name="Description", value=item["explanation"], inline=False)
            embed.add_field(name="Details", value=item["blurb"], inline=False)

        total = len(self.all_items)
        cat_count = len(self.items)
        cat_label = CATEGORY_LABEL.get(self.category, self.category.title())
        embed.set_footer(
            text=f"Card {self.index + 1}/{cat_count} in {cat_label} \u2022 {total} cards total \u2022 Navigate then choose an action below",
            icon_url=self.player_user.display_avatar.url,
        )

        return embed, card_file

    async def update_message(self, interaction: discord.Interaction):
        self._update_buttons()
        embed, file = await self._render_current()
        if file:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    async def execute_turn(
        self,
        interaction: discord.Interaction,
        action_type: str,
        card: Optional[dict] = None,
        action_text: Optional[str] = None,
    ):
        """Execute the turn — send action to DM engine and advance."""
        if self.turn_submitted:
            return await interaction.response.send_message(
                "You've already submitted your action this turn.", ephemeral=True,
            )

        self.turn_submitted = True
        self._update_buttons()

        # Acknowledge immediately
        if not interaction.response.is_done():
            await interaction.response.defer()

        # Disable the turn view
        for child in self.children:
            child.disabled = True
        try:
            embed, _ = await self._render_current()
            embed.set_footer(text=f"Action submitted — waiting for the Dungeon Master...")
            await self.message.edit(embed=embed, view=self)
        except Exception:
            pass

        # Calculate turn number
        turn_number = await asyncio.to_thread(CampaignDB.get_turn_count, self.campaign["id"]) + 1

        # Process through DM engine
        result = await DMEngine.process_turn(
            campaign_id=self.campaign["id"],
            guild_id=self.campaign["guild_id"],
            user_id=str(self.player_user.id),
            display_name=self.player_user.display_name,
            action_type=action_type,
            card=card,
            action_text=action_text,
            turn_number=turn_number,
        )

        # Log the turn
        await asyncio.to_thread(
            CampaignDB.log_turn,
            campaign_id=self.campaign["id"],
            user_id=self.player_user.id,
            turn_number=turn_number,
            round_number=self.campaign["current_round"],
            action_type=action_type,
            dm_response=result["narrative"],
            card_inv_id=card["inv_id"] if card else None,
            card_name=card["name"] if card else None,
            action_text=action_text,
            card_consumed=result.get("card_consumed", False),
        )

        # Build action summary embed
        action_embed = discord.Embed(
            title=f"\u2694\ufe0f {self.player_user.display_name}'s Action",
            color=CAMPAIGN_COLOR,
        )
        if card:
            action_embed.add_field(name="Card Played", value=f"**{card['name']}** ({card['category']})", inline=True)
            if result.get("card_consumed"):
                action_embed.add_field(name="\u200b", value="*Card was consumed!*", inline=True)
        if action_text:
            action_embed.add_field(name="Action", value=action_text, inline=False)

        channel = interaction.channel
        await channel.send(embed=action_embed)

        # Check if campaign is ending
        if result.get("campaign_ending"):
            ending = result.get("ending_narrative", "The campaign has ended.")
            end_embed = discord.Embed(
                title="\U0001f3c1 Campaign Complete",
                description=ending,
                color=CAMPAIGN_COLOR,
            )
            await channel.send(embed=end_embed)
            await asyncio.to_thread(
                CampaignDB.set_campaign_status, self.campaign["id"], "ended"
            )
            return

        # Advance to next turn
        updated_campaign = await asyncio.to_thread(
            CampaignDB.advance_turn, self.campaign["id"]
        )

        # Start next player's turn
        await _start_turn(self.cog, channel, updated_campaign)

    async def handle_question(self, interaction: discord.Interaction, question: str):
        """Handle a question from the active player."""
        used = await asyncio.to_thread(
            CampaignDB.use_question, self.campaign["id"], interaction.user.id
        )
        if not used:
            return await interaction.response.send_message(
                "You've already asked your question this turn.", ephemeral=True,
            )

        await interaction.response.defer()

        answer = await DMEngine.answer_question(
            campaign_id=self.campaign["id"],
            guild_id=self.campaign["guild_id"],
            user_id=str(interaction.user.id),
            display_name=interaction.user.display_name,
            question=question,
        )

        embed = discord.Embed(
            title=f"\u2753 {interaction.user.display_name} asks...",
            description=f"*\"{question}\"*",
            color=CAMPAIGN_COLOR,
        )
        embed.add_field(name="The Dungeon Master responds:", value=answer, inline=False)
        embed.set_footer(text="This did not consume your turn. Choose an action when ready.")
        await interaction.followup.send(embed=embed)

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

    # Row 1 = category select dropdown

    # ------------------------------------------------------------------
    # Row 2: Action buttons
    # ------------------------------------------------------------------

    @discord.ui.button(label="Play Card", style=discord.ButtonStyle.success, emoji="\U0001f0cf", row=2)
    async def play_card_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Play the currently selected card."""
        card = self.get_selected_card()
        if not card:
            return await interaction.response.send_message(
                "No card selected. Navigate to a card first.", ephemeral=True,
            )
        await self.execute_turn(interaction, "card", card=card)

    @discord.ui.button(label="Action", style=discord.ButtonStyle.primary, emoji="\u270f\ufe0f", row=2)
    async def action_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Describe an action without playing a card."""
        modal = ActionTextModal(self, include_card=False)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Play Both", style=discord.ButtonStyle.success, emoji="\u2694\ufe0f", row=2)
    async def play_both_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Play the current card AND describe an accompanying action."""
        card = self.get_selected_card()
        if not card:
            return await interaction.response.send_message(
                "No card selected. Navigate to a card first, then use Play Both.", ephemeral=True,
            )
        modal = ActionTextModal(self, include_card=True)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Ask Question", style=discord.ButtonStyle.secondary, emoji="\u2753", row=2)
    async def ask_question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ask the DM a question without consuming your turn."""
        questions_used = await asyncio.to_thread(
            CampaignDB.get_questions_used, self.campaign["id"], interaction.user.id
        )
        if questions_used >= 1:
            return await interaction.response.send_message(
                "You've already asked your question this turn.", ephemeral=True,
            )
        modal = QuestionModal(self)
        await interaction.response.send_modal(modal)


class CampaignCategorySelect(discord.ui.Select):
    """Dropdown to switch card categories during a campaign turn."""

    def __init__(self, turn_view: CampaignTurnView, all_items: list[dict], current_category: str):
        self.turn_view = turn_view

        owned_cats = sorted(
            set(i["category"] for i in all_items),
            key=lambda c: ALL_CATEGORIES.index(c) if c in ALL_CATEGORIES else 99,
        )

        options = []
        for cat in owned_cats:
            label = CATEGORY_LABEL.get(cat, cat.title())
            emoji = CATEGORY_EMOJI.get(cat)
            count = sum(1 for i in all_items if i["category"] == cat)
            options.append(
                discord.SelectOption(
                    label=label, value=cat,
                    description=f"{count} card{'s' if count != 1 else ''}",
                    emoji=emoji,
                    default=(cat == current_category),
                )
            )

        if not options:
            options.append(discord.SelectOption(label="No cards", value="none"))

        super().__init__(
            placeholder="Switch category...",
            options=options, min_values=1, max_values=1, row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        new_cat = self.values[0]
        if new_cat == "none":
            return await interaction.response.defer()

        view = self.turn_view
        view.category = new_cat
        view.items = [i for i in view.all_items if i["category"] == new_cat]
        view.index = 0

        # Replace dropdown
        for item in view.children:
            if isinstance(item, CampaignCategorySelect):
                view.remove_item(item)
                break
        view.add_item(CampaignCategorySelect(view, view.all_items, new_cat))

        await view.update_message(interaction)


# ==================================================================
# TURN ORCHESTRATION
# ==================================================================

async def _start_turn(cog, channel: discord.TextChannel, campaign: dict):
    """Start a new turn: post DM prompt + active player's inventory."""
    turn_order = campaign["turn_order"]
    idx = campaign["current_turn_index"]

    if not turn_order or idx >= len(turn_order):
        return await channel.send("Error: No players in turn order.")

    active_user_id = int(turn_order[idx])
    guild = channel.guild

    # Fetch the active player member
    try:
        active_member = guild.get_member(active_user_id)
        if not active_member:
            active_member = await guild.fetch_member(active_user_id)
    except discord.HTTPException:
        return await channel.send(f"Could not find player <@{active_user_id}>. Use `[p]va resume` to retry.")

    # Get last DM response
    last_dm = await asyncio.to_thread(CampaignDB.get_last_dm_response, campaign["id"])
    if not last_dm:
        last_dm = "*The Dungeon Master is silent...*"

    # Post DM prompt embed with the shared view
    dm_embed = discord.Embed(
        title=f"\U0001f3ad The Dungeon Master — Round {campaign['current_round']}",
        description=last_dm,
        color=CAMPAIGN_COLOR,
    )
    dm_embed.set_footer(text=f"It's {active_member.display_name}'s turn \u2022 Others: use Show My Cards to view your inventory")

    dm_view = CampaignDMView(cog, campaign, last_dm)
    dm_message = await channel.send(embed=dm_embed, view=dm_view)
    dm_view.message = dm_message

    # Track the message ID for resume
    await asyncio.to_thread(
        CampaignDB.update_message_ids, campaign["id"],
        last_message_id=str(dm_message.id),
    )

    # Announce whose turn it is
    turn_announce = discord.Embed(
        title=f"\u2694\ufe0f {active_member.display_name}'s Turn",
        description=(
            f"{active_member.mention}, it's your move!\n\n"
            f"Browse your cards below, then choose:\n"
            f"\u2022 **Play Card** — use the currently shown card\n"
            f"\u2022 **Action** — describe what you do (no card)\n"
            f"\u2022 **Play Both** — play the card AND describe an action\n"
            f"\u2022 **Ask Question** — ask the DM without using your turn (1 per turn)"
        ),
        color=CAMPAIGN_COLOR,
    )
    await channel.send(embed=turn_announce)

    # Load active player's inventory and post it publicly
    items = await asyncio.to_thread(
        VaultDB.get_inventory, guild.id, active_user_id
    )

    if not items:
        # Player has no cards — they must use Action
        no_cards_embed = discord.Embed(
            title=f"{active_member.display_name}'s Inventory",
            description="You have no cards. Use **Action** to describe what you do.",
            color=EMBED_COLOR,
        )
        turn_view = CampaignTurnView(cog, campaign, active_member, [], "superpower")
        inv_message = await channel.send(embed=no_cards_embed, view=turn_view)
        turn_view.message = inv_message
    else:
        # Start on the first category that has cards
        owned_cats = set(i["category"] for i in items)
        start_cat = next(
            (c for c in ALL_CATEGORIES if c in owned_cats),
            items[0]["category"],
        )

        turn_view = CampaignTurnView(cog, campaign, active_member, items, start_cat)
        embed, file = await turn_view._render_current()

        kwargs: dict = {"embed": embed, "view": turn_view}
        if file:
            kwargs["file"] = file

        inv_message = await channel.send(**kwargs)
        turn_view.message = inv_message

    # Track inventory message ID
    await asyncio.to_thread(
        CampaignDB.update_message_ids, campaign["id"],
        last_inventory_message_id=str(inv_message.id),
    )

