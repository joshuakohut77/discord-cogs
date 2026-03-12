from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from datetime import timezone
from typing import TYPE_CHECKING, Dict, List, Optional

import discord
from discord.channel import TextChannel
from discord.enums import ButtonStyle

from .components.poll import PollView

if TYPE_CHECKING:
    from .buttonpoll import ButtonPoll

log = logging.getLogger("red.buttonpoll.poll")


def datetime_to_timestamp(dt: datetime.datetime, fmt: str = "f") -> str:
    """Generate a Discord timestamp string from a datetime object."""
    return f"<t:{int(dt.timestamp())}:{fmt}>"


@dataclass
class PollOption:
    """A poll option."""

    name: str
    style: ButtonStyle


class Poll:
    """A poll object."""

    def __init__(
        self,
        unique_poll_id: str,
        guild_id: int,
        channel_id: int,
        question: str,
        description: Optional[str],
        options: List[PollOption],
        allow_vote_change: bool,
        view_while_live: bool,
        send_msg_when_over: bool,
        poll_finish: datetime.datetime,
        cog: ButtonPoll,
        view: Optional[PollView],
        message_id: int = 0,
        multi: bool = False,
    ):
        self.unique_poll_id = unique_poll_id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.question = question
        self.description = description
        self.options = options
        self.allow_vote_change = allow_vote_change
        self.view_while_live = view_while_live
        self.multi = multi
        self.send_msg_when_over = send_msg_when_over
        self.poll_finish = poll_finish
        self.view = view
        self.cog = cog

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Poll):
            return self.unique_poll_id == other.unique_poll_id
        return False

    def set_msg_id(self, msg_id: int):
        """Set the message id of the poll, to be used once sent."""
        self.message_id = msg_id

    @classmethod
    def from_dict(cls, data: dict, cog: ButtonPoll) -> Poll:
        """Create a Poll object from a dict."""
        if isinstance(data["poll_finish"], (int, float)):
            finish = datetime.datetime.fromtimestamp(data["poll_finish"], tz=timezone.utc)
        else:
            finish = data["poll_finish"]

        poll = cls(
            unique_poll_id=data["unique_poll_id"],
            guild_id=int(data["guild_id"]),
            channel_id=int(data["channel_id"]),
            message_id=int(data["message_id"]),
            question=data["question"],
            description=data["description"],
            options=[PollOption(n, ButtonStyle(s)) for n, s in data["options"].items()],
            allow_vote_change=bool(data["allow_vote_change"]),
            view_while_live=bool(data["view_while_live"]),
            multi=bool(data.get("multi")),
            send_msg_when_over=bool(data["send_msg_when_over"]),
            poll_finish=finish,
            cog=cog,
            view=None,
        )
        poll.view = PollView(cog.config, poll)
        return poll

    def to_dict(self) -> dict:
        return {
            "unique_poll_id": self.unique_poll_id,
            "guild_id": str(self.guild_id),
            "channel_id": str(self.channel_id),
            "message_id": str(self.message_id),
            "question": self.question,
            "description": self.description,
            "options": {option.name: option.style.value for option in self.options},
            "allow_vote_change": self.allow_vote_change,
            "view_while_live": self.view_while_live,
            "send_msg_when_over": self.send_msg_when_over,
            "multi": self.multi,
            "poll_finish": self.poll_finish.timestamp(),
        }

    async def get_results(self) -> Dict[str, int]:
        """Get poll results as {option_name: vote_count}."""
        results: Dict[str, int] = {}
        for option in self.options:
            results[option.name] = 0

        all_poll_vote_data = await self.cog.config.guild_from_id(self.guild_id).poll_user_choices()
        raw_vote_data = all_poll_vote_data.get(self.unique_poll_id, {})

        for str_option in raw_vote_data.values():
            if isinstance(str_option, list):
                for opt in str_option:
                    if opt in results:
                        results[opt] += 1
            elif str_option in results:
                results[str_option] += 1

        return results

    def format_results(self, results: Dict[str, int], bar_length: int = 16) -> str:
        """Format results as a text-based bar chart."""
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1], reverse=True))
        total = sum(sorted_results.values())

        lines = []
        for option, count in sorted_results.items():
            if total > 0:
                pct = count / total * 100
                filled = round(count / total * bar_length)
            else:
                pct = 0.0
                filled = 0
            bar = "\u2588" * filled + "\u2591" * (bar_length - filled)
            lines.append(f"`{bar}` **{option}** — {count} vote{'s' if count != 1 else ''} ({pct:.0f}%)")

        if total == 0:
            lines.append("\n*No votes were cast.*")
        else:
            lines.append(f"\n**Total votes:** {total}")

        return "\n".join(lines)

    async def finish(self):
        """Finish this poll."""
        guild = self.cog.bot.get_guild(self.guild_id)
        if guild is None:
            log.warning(
                "Guild %s not found. Unable to finish poll %s — removing.",
                self.guild_id,
                self.unique_poll_id,
            )
            await self._cleanup_config_by_id(self.guild_id)
            return

        channel = guild.get_channel(self.channel_id) or guild.get_thread(self.channel_id)
        if not isinstance(channel, (TextChannel, discord.Thread)):
            log.warning(
                "Channel %s does not exist. Removing poll %s without finishing.",
                self.channel_id,
                self.unique_poll_id,
            )
            await self._cleanup_config(guild)
            return

        poll_msg = channel.get_partial_message(self.message_id)
        poll_results = await self.get_results()
        results_text = self.format_results(poll_results)

        if self.send_msg_when_over:
            embed = discord.Embed(
                title="Poll finished!",
                colour=await self.cog.bot.get_embed_color(channel),
                description=f"**{self.question}**\n\n{results_text}",
            )

            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Original message",
                    style=ButtonStyle.link,
                    url=poll_msg.jump_url,
                )
            )

            message = await channel.send(embed=embed, view=view)
            view.stop()

            # Edit original message to link to results
            view2 = discord.ui.View()
            view2.add_item(
                discord.ui.Button(
                    label="Poll finished. View results",
                    style=ButtonStyle.link,
                    url=message.jump_url,
                )
            )
            try:
                await poll_msg.edit(view=view2)
            except discord.NotFound:
                log.warning(
                    "Poll %s message not found, cannot edit. Removing.",
                    self.unique_poll_id,
                )
                await self._cleanup_config(guild)
                return

        else:
            # Edit in place
            embed = discord.Embed(
                colour=await self.cog.bot.get_embed_color(channel),
                title=self.question,
                description=(self.description or "") + f"\n\n{results_text}",
            )
            try:
                await poll_msg.edit(embed=embed, content="", view=None)
            except discord.NotFound:
                log.warning(
                    "Poll %s message not found, cannot edit. Removing.",
                    self.unique_poll_id,
                )
                await self._cleanup_config(guild)
                return

        # Archive poll data then clean up active data
        poll_user_choices = (await self.cog.config.guild(guild).poll_user_choices()).get(
            self.unique_poll_id, {}
        )
        await self.cog.config.guild(guild).historic_poll_settings.set_raw(
            self.unique_poll_id, value=self.to_dict()
        )
        await self.cog.config.guild(guild).historic_poll_user_choices.set_raw(
            self.unique_poll_id, value=poll_user_choices
        )

        await self._cleanup_config(guild)
        log.info("Finished poll %s", self.unique_poll_id)

    async def _cleanup_config(self, guild: discord.Guild):
        """Remove this poll from active config."""
        async with self.cog.config.guild(guild).poll_settings() as poll_settings:
            poll_settings.pop(self.unique_poll_id, None)
        async with self.cog.config.guild(guild).poll_user_choices() as poll_user_choices:
            poll_user_choices.pop(self.unique_poll_id, None)

    async def _cleanup_config_by_id(self, guild_id: int):
        """Remove this poll from active config using guild ID."""
        async with self.cog.config.guild_from_id(guild_id).poll_settings() as poll_settings:
            poll_settings.pop(self.unique_poll_id, None)
        async with self.cog.config.guild_from_id(guild_id).poll_user_choices() as poll_user_choices:
            poll_user_choices.pop(self.unique_poll_id, None)

    def __str__(self) -> str:
        return str(self.to_dict())