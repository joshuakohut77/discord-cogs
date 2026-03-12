from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import os
from typing import TYPE_CHECKING, List, Literal, Optional

import discord
from discord.channel import TextChannel
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red
from redbot.core.commands import BadArgument, parse_timedelta
from redbot.core.utils.chat_formatting import humanize_list, pagify

from .components.poll import PollView
from .components.setup import SetupYesNoView, StartSetupView
from .poll import Poll, PollOption, datetime_to_timestamp

log = logging.getLogger("red.buttonpoll")


class NoExitParser(argparse.ArgumentParser):
    """ArgumentParser that raises BadArgument instead of calling sys.exit."""

    def error(self, message):
        raise BadArgument(message)


class ButtonPoll(commands.Cog):
    """Create polls with buttons and text-based results."""

    __author__ = "Josh (based on Vexed's ButtonPoll)"
    __version__ = "2.0.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(
            self, 418078199982063626, force_registration=True
        )
        self.config.register_guild(
            poll_settings={},
            poll_user_choices={},
            historic_poll_settings={},
            historic_poll_user_choices={},
        )

        self.polls: List[Poll] = []
        self._loop_task: Optional[asyncio.Task] = None

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal[
            "discord_deleted_user", "owner", "user", "user_strict"
        ],
        user_id: int,
    ):
        for g_id, g_polls in (await self.config.all_guilds()).items():
            for poll_id, poll in g_polls.get("poll_user_choices", {}).items():
                for user, vote in poll.items():
                    if user == str(user_id):
                        async with self.config.guild_from_id(
                            g_id
                        ).poll_user_choices() as user_choices:
                            del user_choices[poll_id][user]

    async def cog_load(self) -> None:
        """Re-initialise persistent views and start the background loop."""
        all_polls = await self.config.all_guilds()
        for guild_polls in all_polls.values():
            for poll in guild_polls.get("poll_settings", {}).values():
                obj_poll = Poll.from_dict(poll, self)
                self.polls.append(obj_poll)
                self.bot.add_view(obj_poll.view, message_id=obj_poll.message_id)
                log.debug("Re-initialised view for poll %s", obj_poll.unique_poll_id)

        self._loop_task = self.bot.loop.create_task(self._poll_loop())

    async def cog_unload(self) -> None:
        if self._loop_task:
            self._loop_task.cancel()
        for poll in self.polls:
            poll.view.stop()
        log.info("ButtonPoll unloaded.")

    # ──────────────────────────── Background Loop ────────────────────────────

    async def _poll_loop(self):
        """Background loop that checks for finished polls every 30 seconds."""
        await self.bot.wait_until_red_ready()
        while True:
            try:
                await self._check_finished_polls()
            except Exception:
                log.exception("Error in ButtonPoll loop.")
            await asyncio.sleep(30)

    async def _check_finished_polls(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        for poll in self.polls.copy():
            if poll.poll_finish < now:
                log.info("Poll %s has finished.", poll.unique_poll_id)
                poll.view.stop()
                await poll.finish()
                self.polls.remove(poll)

    # ──────────────────────────── Text Commands ──────────────────────────────

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command(aliases=["poll", "bpoll"])
    async def buttonpoll(
        self, ctx: commands.Context, chan: Optional[TextChannel] = None
    ):
        """
        Start a button-based poll.

        This is an interactive setup. By default the current channel will be used,
        but if you want to start a poll remotely you can send the channel name
        along with the buttonpoll command.

        **Examples:**
        - `[p]buttonpoll` - start a poll in the current channel
        - `[p]buttonpoll #polls` - start a poll somewhere else
        """
        channel = chan or ctx.channel
        if TYPE_CHECKING:
            assert isinstance(channel, (TextChannel, discord.Thread))
            assert isinstance(ctx.author, discord.Member)

        if not channel.permissions_for(ctx.author).send_messages:  # type: ignore
            return await ctx.send(
                f"You don't have permission to send messages in {channel.mention}, "
                "so I can't start a poll there."
            )
        if not channel.permissions_for(ctx.me).send_messages:  # type: ignore
            return await ctx.send(
                f"I don't have permission to send messages in {channel.mention}, "
                "so I can't start a poll there."
            )

        view = StartSetupView(author=ctx.author, channel=channel, cog=self)
        await ctx.send("Click below to start a poll!", view=view)

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def advstartpoll(self, ctx: commands.Context, *, arguments: str = ""):
        """
        Advanced: create a poll using command arguments.

        Run `[p]advstartpoll` with no arguments to see full usage.
        """
        if not arguments:
            return await ctx.send(
                "\N{WARNING SIGN}\N{VARIATION SELECTOR-16} **This command is for advanced "
                "users only.\nYou should use `[p]buttonpoll` or the slash command `/poll` "
                "for a more user-friendly experience.**\n\n"
                "**Required arguments:**\n"
                "- `--channel ID`: The channel ID to start the poll in\n"
                "- `--question string`: The question to ask\n"
                "- `--option string`: The options (repeat for each, 2-5)\n\n"
                "**You must also provide one of:**\n"
                "- `--duration integer`: Duration in seconds (min 60)\n"
                "- `--end string`: End time as `YYYY-MM-DD HH:MM:SS` (UTC) or Unix timestamp\n\n"
                "**Optional flags:**\n"
                "- `--description string`: A description (use \\n for newlines)\n"
                "- `--allow-vote-change`: Allow users to change their vote\n"
                "- `--view-while-live`: Allow viewing results while live\n"
                "- `--send-new-msg`: Send a new message when finished\n"
                "- `--multi`: Allow voting for multiple options\n"
                "- `--silent`: Suppress error messages"
            )

        parser = NoExitParser(description="Create a poll.", add_help=False)
        parser.add_argument("--channel", type=int, required=True)
        parser.add_argument("--question", type=str, required=True, nargs="+")
        parser.add_argument(
            "--option", type=str, action="append", required=True, nargs="+"
        )
        parser.add_argument("--duration", type=int)
        parser.add_argument("--end", type=str, nargs="+")
        parser.add_argument("--description", type=str, nargs="+", default="")
        parser.add_argument("--allow-vote-change", action="store_true")
        parser.add_argument("--view-while-live", action="store_true")
        parser.add_argument("--send-new-msg", action="store_true")
        parser.add_argument("--silent", action="store_true")
        parser.add_argument("--multi", action="store_true")

        try:
            args = parser.parse_args(arguments.split())
        except Exception as e:
            return await ctx.send(f"Error parsing arguments: {e}")

        if args.duration is None and args.end is None:
            if not args.silent:
                await ctx.send("You must provide either a duration or an end time.")
            return

        channel = self.bot.get_channel(args.channel)
        if not channel:
            if not args.silent:
                await ctx.send("That channel does not exist.")
            return

        unique_poll_id = (
            os.urandom(5).hex()
            + "_"
            + str(ctx.message.id)
            + "_"
            + "".join(
                " ".join(c) for c in args.option if " ".join(c).isalnum()
            )[:25]
        )

        if args.duration:
            poll_finish = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(seconds=args.duration)
        else:
            try:
                poll_finish = datetime.datetime.strptime(
                    " ".join(args.end), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                try:
                    poll_finish = datetime.datetime.fromtimestamp(
                        int(args.end[0]), tz=datetime.timezone.utc
                    )
                except ValueError:
                    if not args.silent:
                        await ctx.send(
                            "Invalid end time. Must be `YYYY-MM-DD HH:MM:SS` (UTC) "
                            "or a Unix timestamp."
                        )
                    return

        question = " ".join(args.question)
        description = " ".join(args.description) if args.description else ""

        poll = Poll(
            unique_poll_id=unique_poll_id,
            guild_id=channel.guild.id,
            channel_id=channel.id,
            question=question,
            description=description,
            options=[
                PollOption(" ".join(o), discord.ButtonStyle.primary)
                for o in args.option
            ],
            allow_vote_change=args.allow_vote_change,
            view_while_live=args.view_while_live,
            multi=args.multi,
            send_msg_when_over=args.send_new_msg,
            poll_finish=poll_finish,
            cog=self,
            view=None,
        )
        poll.view = PollView(self.config, poll)

        e = discord.Embed(
            colour=await self.bot.get_embed_colour(channel),
            title=poll.question,
            description=poll.description or None,
        )
        e.add_field(
            name=(
                f"Ends at {datetime_to_timestamp(poll.poll_finish)}, "
                f"{datetime_to_timestamp(poll.poll_finish, 'R')}"
            ),
            value=(
                "You have one vote, "
                + (
                    "and you can change it by clicking a new button."
                    if poll.allow_vote_change
                    else "and you can't change it."
                )
                + (
                    "\nYou can view the results while the poll is live, once you vote."
                    if poll.view_while_live
                    else "\nYou can view the results when the poll finishes."
                )
            ),
        )

        m = await channel.send(embed=e, view=poll.view)  # type: ignore

        poll.set_msg_id(m.id)
        async with self.config.guild(channel.guild).poll_settings() as poll_settings:
            poll_settings[poll.unique_poll_id] = poll.to_dict()
        self.polls.append(poll)

    # ──────────────────────────── Slash Command ──────────────────────────────

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        channel="Channel to start the poll in.",
        question="Question to ask.",
        description="An optional description.",
        duration="Duration of the poll. Examples: 1 day, 1 minute, 4 hours",
        choice1="First choice.",
        choice2="Second choice.",
        choice3="Optional third choice.",
        choice4="Optional fourth choice.",
        choice5="Optional fifth choice.",
    )
    @app_commands.command(name="poll", description="Start a button-based poll.")
    async def poll_slash(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel],
        question: app_commands.Range[str, 1, 256],
        description: Optional[app_commands.Range[str, 1, 4000]],
        duration: app_commands.Range[str, 1, 20],
        choice1: app_commands.Range[str, 1, 80],
        choice2: app_commands.Range[str, 1, 80],
        choice3: Optional[app_commands.Range[str, 1, 80]],
        choice4: Optional[app_commands.Range[str, 1, 80]],
        choice5: Optional[app_commands.Range[str, 1, 80]],
    ):
        try:
            parsed_duration = parse_timedelta(duration or "")
        except Exception:
            await interaction.response.send_message(
                "Invalid time format. Please use a valid time format, for example "
                "`1 day`, `1 minute`, `4 hours`.",
                ephemeral=True,
            )
            return
        if parsed_duration is None:
            await interaction.response.send_message(
                "Invalid time format. Please use a valid time format, for example "
                "`1 day`, `1 minute`, `4 hours`.",
                ephemeral=True,
            )
            return

        str_options: list[str | None] = [
            choice1, choice2, choice3, choice4, choice5
        ]
        while None in str_options:
            str_options.remove(None)

        if len(str_options) < 2:
            await interaction.response.send_message(
                "You must provide at least two unique choices.", ephemeral=True
            )
            return

        if len(str_options) != len(set(str_options)):
            await interaction.response.send_message(
                "You can't have duplicate choices.", ephemeral=True
            )
            return

        options: list[PollOption] = []
        for option in str_options:
            options.append(PollOption(option, discord.ButtonStyle.primary))

        await interaction.response.send_message(
            "Great! Just a few quick questions now.",
            view=SetupYesNoView(
                author=interaction.user,
                channel=channel or interaction.channel,
                cog=self,
                question=question,
                description=description or "",
                time=parsed_duration,
                options=options,
            ),
            ephemeral=True,
        )

    # ──────────────────────────── Utility Commands ───────────────────────────

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command(aliases=["voters"])
    async def getvoters(self, ctx: commands.Context, message_id: int):
        """
        Fetch the current voters for a running or finished poll.

        **Arguments**
        - `message_id`: (integer) The ID of the poll message
        """
        conf = await self.config.guild(ctx.guild).all()
        obj_poll = None
        votes = {}

        # Check active polls
        for poll in self.polls:
            if poll.message_id == message_id:
                obj_poll = poll
                votes = conf["poll_user_choices"].get(
                    obj_poll.unique_poll_id, {}
                )
                break

        # Check historic polls
        if obj_poll is None:
            for poll_data in conf.get("historic_poll_settings", {}).values():
                if int(poll_data["message_id"]) == message_id:
                    obj_poll = Poll.from_dict(poll_data, self)
                    votes = conf.get("historic_poll_user_choices", {}).get(
                        obj_poll.unique_poll_id, {}
                    )
                    break

        if obj_poll is None:
            return await ctx.send(
                "Could not find a poll associated with this message!"
            )

        if not votes:
            return await ctx.send("This poll has no votes yet!")

        options = {}
        for user_id, vote in votes.items():
            vote_list = vote if isinstance(vote, list) else [vote]
            for v in vote_list:
                if v not in options:
                    options[v] = []
                user = ctx.guild.get_member(int(user_id))
                mention = user.mention if user else f"<@{user_id}>"
                options[v].append(mention)

        sorted_votes = sorted(
            options.items(), key=lambda x: len(x[1]), reverse=True
        )

        text = ""
        for vote, voters in sorted_votes:
            count = len(voters)
            text += (
                f"**{vote}** has {count} "
                f"{'votes' if count != 1 else 'vote'} from "
                f"{humanize_list(voters)}\n"
            )

        for p in pagify(text):
            embed = discord.Embed(
                title=obj_poll.question,
                description=p,
                color=ctx.author.color,
            )
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command(aliases=["endp"])
    async def endpoll(self, ctx: commands.Context, message_id: int):
        """
        End a currently running poll.

        **Arguments**
        - `message_id`: (integer) The ID of the poll message
        """
        for poll in self.polls:
            if poll.message_id == message_id:
                obj_poll = poll
                break
        else:
            return await ctx.send(
                "Could not find a running poll associated with this message!"
            )

        async with ctx.typing():
            obj_poll.view.stop()
            await obj_poll.finish()
            self.polls.remove(obj_poll)
            await ctx.tick()

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def listpolls(self, ctx: commands.Context):
        """List all currently running polls."""
        guild_polls = [p for p in self.polls if p.guild_id == ctx.guild.id]

        if not guild_polls:
            return await ctx.send("There are no polls currently running!")

        text = ""
        for poll in guild_polls:
            text += (
                f"**{poll.question}**\nMessage ID `{poll.message_id}`\n"
                f"https://discord.com/channels/{poll.guild_id}/{poll.channel_id}/{poll.message_id}"
                "\n\n"
            )

        for p in pagify(text):
            embed = discord.Embed(
                title="Current Polls",
                description=p,
                color=ctx.author.color,
            )
            await ctx.send(embed=embed)
