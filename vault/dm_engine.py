"""
vault/dm_engine.py — Dungeon Master AI engine

Phase 2 will replace the placeholder methods with real Claude API calls.
For now, returns mock responses so the full UI flow can be tested.

Architecture notes for Phase 2:
    - Uses aiohttp to call https://api.anthropic.com/v1/messages
    - API key from ANTHROPIC_API_KEY env var
    - System prompt built dynamically from player inventories + card properties
    - Full conversation history reconstructed from vault_campaign_messages
    - Claude responds with structured JSON so we can parse:
        - narrative: str (the DM's story text)
        - cards_consumed: list[int] (inventory IDs that were destroyed)
        - state_changes: dict (any card state updates)
        - campaign_ending: bool (whether the campaign should end)
        - ending_narrative: str (final wrap-up text if ending)
"""
from __future__ import annotations

import json
import logging
import random
from typing import Optional

from .campaign_db import CampaignDB
from .db import VaultDB

log = logging.getLogger("red.vault.dm_engine")


class DMEngine:
    """Interface to the Dungeon Master AI.

    All methods are async — they'll make HTTP calls in Phase 2.
    For now they return placeholder responses.
    """

    # ==================================================================
    # CAMPAIGN GENERATION
    # ==================================================================

    @staticmethod
    async def generate_campaign_start(
        campaign_id: int,
        guild_id: int,
        players: list[dict],
    ) -> str:
        """Generate the opening campaign narrative.

        In Phase 2, this will:
        1. Build a system prompt with all player inventories and game rules
        2. Send an initial prompt asking Claude to generate a campaign
        3. Store the system prompt and response in campaign_messages
        4. Return the narrative text

        For now, returns a placeholder opening.
        """
        player_names = [p["display_name"] for p in players]
        names_str = ", ".join(player_names[:-1]) + f" and {player_names[-1]}" if len(player_names) > 1 else player_names[0]

        # Build inventory summary for the placeholder
        inv_summaries = []
        for p in players:
            items = VaultDB.get_inventory(int(guild_id), int(p["user_id"]))
            card_count = len(items)
            equipped = [i for i in items if i["is_equipped"]]
            inv_summaries.append(
                f"**{p['display_name']}** — {card_count} cards ({len(equipped)} equipped)"
            )

        inv_block = "\n".join(inv_summaries)

        placeholder = (
            f"*[PLACEHOLDER DM — Phase 2 will use Claude API]*\n\n"
            f"**The Descent Begins**\n\n"
            f"The ancient iron doors groan open, revealing a darkness so thick it seems to breathe. "
            f"{names_str} stand at the threshold, the weight of their gathered artifacts "
            f"pressing against them like a premonition.\n\n"
            f"Before you stretches a corridor carved from obsidian, its walls etched with warnings "
            f"in a language that predates memory. Somewhere deep below, a heartbeat echoes — slow, "
            f"massive, patient.\n\n"
            f"**Party:**\n{inv_block}\n\n"
            f"The corridor branches ahead. Faint light flickers from the left passage. "
            f"The right passage exhales cold air that smells of iron and old blood.\n\n"
            f"*What do you do?*"
        )

        # Store in message chain
        CampaignDB.add_message(
            campaign_id, "assistant", placeholder,
            turn_number=0, message_type="campaign_start",
        )

        return placeholder

    # ==================================================================
    # TURN PROCESSING
    # ==================================================================

    @staticmethod
    async def process_turn(
        campaign_id: int,
        guild_id: int,
        user_id: int,
        display_name: str,
        action_type: str,
        card: Optional[dict] = None,
        action_text: Optional[str] = None,
        turn_number: int = 1,
    ) -> dict:
        """Process a player's turn action and get the DM's response.

        In Phase 2, this will:
        1. Reconstruct the message chain from campaign_messages
        2. Build the user message describing the action
        3. Send to Claude API
        4. Parse Claude's structured response
        5. Apply card state changes (consumed, durability, etc.)
        6. Store messages in the chain
        7. Return the parsed response

        Returns dict with:
            narrative: str — the DM's response text
            card_consumed: bool — whether the played card was consumed
            campaign_ending: bool — whether Claude wants to end the campaign
            ending_narrative: str — wrap-up text if ending
        """
        # Build the user message
        action_parts = []
        if card:
            action_parts.append(
                f"**{display_name}** plays **{card['name']}** "
                f"({card['category']}/{card['rarity']}): {card['explanation']}"
            )
        if action_text:
            action_parts.append(f"**{display_name}** declares: \"{action_text}\"")

        user_message = "\n".join(action_parts) if action_parts else f"**{display_name}** takes an action."

        # Store user message in chain
        CampaignDB.add_message(
            campaign_id, "user", user_message,
            turn_number=turn_number, message_type="turn",
        )

        # --- PLACEHOLDER RESPONSE ---
        card_consumed = False
        if card:
            # Use the existing use_item system for card consumption
            use_result = VaultDB.use_item(card["inv_id"])
            card_consumed = use_result.get("consumed", False)

        responses = [
            "The shadows shift in response to your actions. Something stirs deeper in the darkness.",
            "A low rumble echoes through the chamber. Dust falls from cracks in the ceiling you hadn't noticed before.",
            "The air grows colder. Your breath crystallizes. Something is watching.",
            "The ground beneath your feet vibrates with an ancient resonance. The walls seem to close in, then retreat.",
            "A distant scream — or was it laughter? — rings through the corridor. The torches flicker, then steady.",
        ]

        card_note = ""
        if card and card_consumed:
            card_note = f"\n\n*[{card['name']} was consumed by this action.]*"
        elif card:
            card_note = f"\n\n*[{card['name']} was used but remains in your inventory.]*"

        narrative = (
            f"*[PLACEHOLDER DM — Phase 2 will use Claude API]*\n\n"
            f"In response to {display_name}'s action:\n\n"
            f"{random.choice(responses)}{card_note}\n\n"
            f"*The next adventurer steps forward...*"
        )

        # Store DM response in chain
        CampaignDB.add_message(
            campaign_id, "assistant", narrative,
            turn_number=turn_number, message_type="turn",
        )

        return {
            "narrative": narrative,
            "card_consumed": card_consumed,
            "campaign_ending": False,
            "ending_narrative": "",
        }

    # ==================================================================
    # QUESTION HANDLING
    # ==================================================================

    @staticmethod
    async def answer_question(
        campaign_id: int,
        guild_id: int,
        user_id: int,
        display_name: str,
        question: str,
    ) -> str:
        """Answer a player's question without consuming a turn.

        In Phase 2, this appends the question and answer to the message
        chain so Claude stays consistent, but doesn't advance the turn.

        Returns the DM's answer text.
        """
        # Store question in chain
        user_msg = f"[QUESTION from {display_name}]: {question}"
        CampaignDB.add_message(
            campaign_id, "user", user_msg,
            message_type="question",
        )

        # Placeholder answer
        answers = [
            "The walls seem to whisper an answer, but the words dissolve before they reach you fully. You sense the answer lies ahead.",
            "Your instincts tell you to proceed with caution. The dungeon reveals its secrets to those who earn them.",
            "The flickering torchlight briefly illuminates runes on the wall — a partial answer, perhaps, to what you seek.",
            "A chill wind carries fragments of knowledge from deeper within. The full truth waits around the next corner.",
        ]

        answer = (
            f"*[PLACEHOLDER DM — Phase 2 will use Claude API]*\n\n"
            f"{random.choice(answers)}"
        )

        CampaignDB.add_message(
            campaign_id, "assistant", answer,
            message_type="question",
        )

        return answer

    # ==================================================================
    # CAMPAIGN END
    # ==================================================================

    @staticmethod
    async def generate_campaign_ending(
        campaign_id: int,
        reason: str = "admin_ended",
    ) -> str:
        """Generate a campaign ending narrative.

        In Phase 2, Claude will write a proper wrap-up based on the full
        story so far. For now, returns a placeholder.
        """
        endings = {
            "admin_ended": (
                "*[PLACEHOLDER DM]*\n\n"
                "**The Vision Fades**\n\n"
                "The dungeon shimmers and dissolves like mist at dawn. "
                "The adventure ends — not with a final blow, but with the "
                "quiet certainty that this chapter is closed.\n\n"
                "*Campaign ended by admin.*"
            ),
            "claude_ended": (
                "*[PLACEHOLDER DM]*\n\n"
                "**The Final Door Opens**\n\n"
                "Beyond the last threshold, light pours in — warm, golden, "
                "impossibly bright after the darkness below. The party emerges, "
                "forever changed by what they found in The Vault.\n\n"
                "*Campaign completed.*"
            ),
        }

        narrative = endings.get(reason, endings["admin_ended"])

        CampaignDB.add_message(
            campaign_id, "assistant", narrative,
            message_type="campaign_end",
        )

        return narrative

    # ==================================================================
    # CONTEXT BUILDERS (used by Phase 2)
    # ==================================================================

    @staticmethod
    def build_player_context(guild_id: int, players: list[dict]) -> str:
        """Build a text summary of all player inventories for the system prompt.

        This is used now for placeholder display and will feed into the
        Claude system prompt in Phase 2.
        """
        sections = []
        for p in players:
            items = VaultDB.get_inventory(int(guild_id), int(p["user_id"]))
            if not items:
                sections.append(f"### {p['display_name']}\nNo cards in inventory.")
                continue

            lines = [f"### {p['display_name']}"]
            for item in items:
                equipped = " [EQUIPPED]" if item["is_equipped"] else ""
                props_str = ", ".join(f"{k}={v}" for k, v in item["properties"].items()) if item["properties"] else "no special properties"
                state_str = ", ".join(f"{k}={v}" for k, v in item["state"].items()) if item["state"] else ""
                state_note = f" | State: {state_str}" if state_str else ""
                lines.append(
                    f"- **{item['name']}** ({item['category']}/{item['rarity']}){equipped}: "
                    f"{item['explanation']} [{props_str}{state_note}]"
                )
            sections.append("\n".join(lines))

        return "\n\n".join(sections)