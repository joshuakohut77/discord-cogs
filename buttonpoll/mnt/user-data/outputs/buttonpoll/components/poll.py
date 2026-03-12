from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Union

import discord
from discord.enums import ButtonStyle
from redbot.core.config import Config

if TYPE_CHECKING:
    from ..poll import Poll

log = logging.getLogger("red.buttonpoll.components.poll")


class OptionButton(discord.ui.Button):
    """A button representing a single poll option."""

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, PollView)
        poll = self.view.poll_settings

        if poll.multi:
            await self._handle_multi_vote(interaction)
        else:
            await self._handle_single_vote(interaction)

    async def _handle_single_vote(self, interaction: discord.Interaction):
        assert isinstance(self.view, PollView)
        poll = self.view.poll_settings

        current_choice = await self.view.get_user_vote(
            interaction.guild, interaction.user.id  # type: ignore
        )

        if not poll.allow_vote_change and current_choice is not None:
            msg = (
                f"You've already voted for `{current_choice}`, and you can't change "
                "your vote in this poll."
            )
        elif current_choice == self.label:
            msg = f"You're already voting for `{self.label}`!"
        elif current_choice is not None:
            msg = f"You've already voted, so I've **changed** your vote to `{self.label}`."
            await self._save_vote(interaction, self.label)
        else:
            msg = f"You've voted for `{self.label}`."
            await self._save_vote(interaction, self.label)

        await interaction.response.send_message(msg, ephemeral=True)

    async def _handle_multi_vote(self, interaction: discord.Interaction):
        assert isinstance(self.view, PollView)

        current_choices = await self.view.get_user_vote(
            interaction.guild, interaction.user.id  # type: ignore
        )

        if current_choices is None:
            current_choices = []

        if isinstance(current_choices, str):
            current_choices = [current_choices]

        if self.label in current_choices:
            current_choices.remove(self.label)
            if current_choices:
                msg = f"Removed your vote for `{self.label}`. Your current votes: {', '.join(f'`{c}`' for c in current_choices)}"
            else:
                msg = f"Removed your vote for `{self.label}`. You have no active votes."
            await self._save_vote(interaction, current_choices if current_choices else None)
        else:
            current_choices.append(self.label)
            msg = f"You've voted for `{self.label}`. Your current votes: {', '.join(f'`{c}`' for c in current_choices)}"
            await self._save_vote(interaction, current_choices)

        await interaction.response.send_message(msg, ephemeral=True)

    async def _save_vote(self, interaction: discord.Interaction, value):
        assert isinstance(self.view, PollView)
        if value is None:
            # Remove the vote entirely
            async with self.view.config.guild(
                interaction.guild  # type: ignore
            ).poll_user_choices() as choices:
                poll_choices = choices.get(self.view.poll_settings.unique_poll_id, {})
                poll_choices.pop(str(interaction.user.id), None)
                choices[self.view.poll_settings.unique_poll_id] = poll_choices
        else:
            await self.view.config.guild(
                interaction.guild  # type: ignore
            ).poll_user_choices.set_raw(
                self.view.poll_settings.unique_poll_id,
                str(interaction.user.id),
                value=value,
            )


class PollView(discord.ui.View):
    """View for an active poll. Persistent-compatible."""

    def __init__(self, config: Config, poll_settings: Poll):
        super().__init__(timeout=None)

        for option in poll_settings.options:
            if not option.name:
                continue
            self.add_item(
                OptionButton(
                    style=option.style,
                    label=option.name,
                    custom_id=poll_settings.unique_poll_id[:70] + "_" + option.name[:29],
                )
            )

        self.poll_settings = poll_settings
        self.config = config

        if not poll_settings.view_while_live:
            self.remove_item(self.view_results_btn)  # type: ignore

    async def get_user_vote(
        self, guild: discord.Guild, user_id: int
    ) -> Optional[Union[str, List[str]]]:
        """Get the vote(s) of a user in a poll."""
        return (
            (await self.config.guild(guild).poll_user_choices())
            .get(self.poll_settings.unique_poll_id, {})
            .get(str(user_id), None)
        )

    @discord.ui.button(
        label="View my vote", custom_id="view_vote", style=ButtonStyle.grey, row=2
    )
    async def view_my_vote_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show the user their current vote, if any."""
        choice = await self.get_user_vote(
            interaction.guild, interaction.user.id  # type: ignore
        )
        if choice is None:
            await interaction.response.send_message("You haven't voted yet!", ephemeral=True)
        elif isinstance(choice, list):
            formatted = ", ".join(f"`{c}`" for c in choice)
            change_msg = " Click a button to toggle your votes." if self.poll_settings.allow_vote_change else ""
            await interaction.response.send_message(
                f"You voted for: {formatted}.{change_msg}", ephemeral=True
            )
        else:
            change_msg = (
                " Change your vote by clicking a new button."
                if self.poll_settings.allow_vote_change
                else ""
            )
            await interaction.response.send_message(
                f"You voted for `{choice}`.{change_msg}", ephemeral=True
            )

    @discord.ui.button(
        label="View results so far",
        custom_id="view_results",
        style=ButtonStyle.grey,
        row=2,
    )
    async def view_results_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show the results of the poll (only if user has voted)."""
        choice = await self.get_user_vote(
            interaction.guild, interaction.user.id  # type: ignore
        )
        if choice is None:
            await interaction.response.send_message(
                "You need to vote first to be able to see results.", ephemeral=True
            )
            return

        results = await self.poll_settings.get_results()
        results_text = self.poll_settings.format_results(results)

        await interaction.response.send_message(
            f"**Results so far:**\n{results_text}", ephemeral=True
        )
