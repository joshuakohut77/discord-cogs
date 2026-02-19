from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands
from redbot.core.commands.context import Context

from services.dbclass import db as dbconn

from .abcd import MixinMeta


DiscordUser = Union[discord.Member, discord.User]


class HofState:
    """Tracks Hall of Fame viewer state per user"""
    def __init__(self, discordId: str, targetId: str, messageId: int, channelId: int, run_index: int, total_runs: int):
        self.discordId = discordId      # The user viewing
        self.targetId = targetId        # The trainer being viewed
        self.messageId = messageId
        self.channelId = channelId
        self.run_index = run_index      # Current run being viewed (0-based)
        self.total_runs = total_runs


class HallOfFameMixin(MixinMeta):
    """Hall of Fame - Elite Four victory history"""

    __hof_states: dict[str, HofState] = {}

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user)."""
        pass

    @_trainer.command(name="hof", aliases=["halloffame"])
    async def hall_of_fame(self, ctx: commands.Context, user: DiscordUser = None):
        """
        View the Hall of Fame - your Elite Four victory history.
        Optionally mention a user to view their history.
        """
        author = ctx.author
        target = user if user else author

        # Get all distinct run_ids for this trainer, ordered newest first
        runs = self.__get_runs(str(target.id))

        if not runs or len(runs) == 0:
            await ctx.send(f"{'You have' if target.id == author.id else f'{target.display_name} has'} not defeated the Elite Four yet.")
            return

        total_runs = len(runs)
        run_index = 0  # Start at most recent

        embed = self.__build_hof_embed(target, runs, run_index, total_runs)
        view = self.__build_hof_view(run_index, total_runs)
        message = await ctx.send(embed=embed, view=view)

        self.__hof_states[str(author.id)] = HofState(
            str(author.id), str(target.id), message.id, message.channel.id, run_index, total_runs
        )

    def __get_runs(self, discord_id: str) -> list:
        """Get all victory runs for a trainer, newest first. Returns list of (run_id, victory_at, [(name, level), ...])"""
        try:
            db = dbconn()
            query = """
                SELECT run_id, pokemon_name, pokemon_level, victory_at
                FROM elite_four_victories
                WHERE discord_id = %(discordId)s
                ORDER BY run_id DESC, id ASC
            """
            results = db.queryAll(query, {'discordId': discord_id})
            if not results:
                return []

            # Group by run_id
            runs = {}
            for row in results:
                run_id = row[0]
                pokemon_name = row[1]
                pokemon_level = row[2]
                victory_at = row[3]

                if run_id not in runs:
                    runs[run_id] = {
                        'run_id': run_id,
                        'victory_at': victory_at,
                        'pokemon': []
                    }
                runs[run_id]['pokemon'].append((pokemon_name, pokemon_level))

            return list(runs.values())
        except Exception as e:
            print(f"Error fetching HoF runs: {e}")
            return []
        finally:
            del db

    def __build_hof_embed(self, target: DiscordUser, runs: list, run_index: int, total_runs: int) -> discord.Embed:
        """Build the Hall of Fame embed for a specific run"""
        run = runs[run_index]
        run_number = total_runs - run_index  # Display as 1-based, oldest = #1

        victory_time = run['victory_at']
        if victory_time:
            timestamp_str = f"<t:{int(victory_time.timestamp())}:F>"
        else:
            timestamp_str = "Unknown"

        embed = discord.Embed(
            title="🏆 Hall of Fame",
            description=f"Victory #{run_number} — {timestamp_str}",
            color=discord.Color.gold()
        )
        embed.set_author(name=target.display_name, icon_url=str(target.display_avatar.url))

        # Build party display
        party_lines = []
        for pokemon_name, pokemon_level in run['pokemon']:
            display_name = pokemon_name.capitalize() if pokemon_name else "???"
            # Try to get the Pokemon emoji from constant
            try:
                import constant
                emoji = constant.POKEMON_EMOJIS.get(pokemon_name.upper(), '') if pokemon_name else ''
            except Exception:
                emoji = ''

            party_lines.append(f"{emoji} **{display_name}** — Lv. {pokemon_level}")

        embed.add_field(
            name="🎖️ Champion Team",
            value="\n".join(party_lines) if party_lines else "No data",
            inline=False
        )

        embed.set_footer(text=f"Run {run_number} of {total_runs}")

        return embed

    def __build_hof_view(self, run_index: int, total_runs: int) -> View:
        """Build prev/next navigation buttons"""
        view = View()

        prev_btn = Button(
            style=ButtonStyle.gray,
            label="◀ Previous",
            custom_id="hof_prev",
            disabled=(run_index >= total_runs - 1)
        )
        prev_btn.callback = self.on_hof_prev
        view.add_item(prev_btn)

        next_btn = Button(
            style=ButtonStyle.gray,
            label="Next ▶",
            custom_id="hof_next",
            disabled=(run_index <= 0)
        )
        next_btn.callback = self.on_hof_next
        view.add_item(next_btn)

        return view

    async def on_hof_prev(self, interaction: Interaction):
        """Navigate to an older run"""
        user = interaction.user
        await interaction.response.defer()

        state = self.__hof_states.get(str(user.id))
        if not state or state.messageId != interaction.message.id:
            await interaction.followup.send("This is not for you.", ephemeral=True)
            return

        target = await interaction.guild.fetch_member(int(state.targetId))
        runs = self.__get_runs(state.targetId)
        if not runs:
            return

        state.run_index = min(state.run_index + 1, len(runs) - 1)
        state.total_runs = len(runs)

        embed = self.__build_hof_embed(target, runs, state.run_index, state.total_runs)
        view = self.__build_hof_view(state.run_index, state.total_runs)
        await interaction.message.edit(embed=embed, view=view)

    async def on_hof_next(self, interaction: Interaction):
        """Navigate to a newer run"""
        user = interaction.user
        await interaction.response.defer()

        state = self.__hof_states.get(str(user.id))
        if not state or state.messageId != interaction.message.id:
            await interaction.followup.send("This is not for you.", ephemeral=True)
            return

        target = await interaction.guild.fetch_member(int(state.targetId))
        runs = self.__get_runs(state.targetId)
        if not runs:
            return

        state.run_index = max(state.run_index - 1, 0)
        state.total_runs = len(runs)

        embed = self.__build_hof_embed(target, runs, state.run_index, state.total_runs)
        view = self.__build_hof_view(state.run_index, state.total_runs)
        await interaction.message.edit(embed=embed, view=view)