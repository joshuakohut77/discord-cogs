from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

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
    def __init__(self, discordId: str, targetId: Optional[str], messageId: int, channelId: int, guildId: int, run_index: int, total_runs: int):
        self.discordId = discordId      # The user viewing
        self.targetId = targetId        # None = all players, or a specific discord_id
        self.messageId = messageId
        self.channelId = channelId
        self.guildId = guildId
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
        View the Hall of Fame - Elite Four victory history.
        Use without mention to see all victories, or @mention to see a specific trainer.
        """
        author = ctx.author
        target_id = str(user.id) if user else None

        runs = self.__get_runs(target_id)

        if not runs or len(runs) == 0:
            if user:
                await ctx.send(f"{user.display_name} has not defeated the Elite Four yet.")
            else:
                await ctx.send("No one has defeated the Elite Four yet.")
            return

        total_runs = len(runs)
        run_index = 0  # Start at most recent

        embed = await self.__build_hof_embed(ctx.guild, runs, run_index, total_runs, target_id)
        view = self.__build_hof_view(run_index, total_runs)
        message = await ctx.send(embed=embed, view=view)

        self.__hof_states[str(author.id)] = HofState(
            str(author.id), target_id, message.id, message.channel.id, ctx.guild.id, run_index, total_runs
        )

    def __get_runs(self, discord_id: Optional[str] = None) -> list:
        """Get victory runs, newest first. If discord_id is None, gets all players."""
        try:
            db = dbconn()

            if discord_id:
                query = """
                    SELECT discord_id, run_id, pokemon_name, pokemon_level, victory_at
                    FROM elite_four_victories
                    WHERE discord_id = %(discordId)s
                    ORDER BY run_id DESC, id ASC
                """
                results = db.queryAll(query, {'discordId': discord_id})
            else:
                query = """
                    SELECT discord_id, run_id, pokemon_name, pokemon_level, victory_at
                    FROM elite_four_victories
                    ORDER BY victory_at DESC, run_id DESC, id ASC
                """
                results = db.queryAll(query, {})

            if not results:
                return []

            # Group by (discord_id, run_id)
            runs = {}
            run_order = []
            for row in results:
                d_id = row[0]
                run_id = row[1]
                pokemon_name = row[2]
                pokemon_level = row[3]
                victory_at = row[4]

                key = f"{d_id}_{run_id}"
                if key not in runs:
                    runs[key] = {
                        'discord_id': d_id,
                        'run_id': run_id,
                        'victory_at': victory_at,
                        'pokemon': []
                    }
                    run_order.append(key)
                runs[key]['pokemon'].append((pokemon_name, pokemon_level))

            return [runs[k] for k in run_order]
        except Exception as e:
            print(f"Error fetching HoF runs: {e}")
            return []
        finally:
            del db

    async def __build_hof_embed(self, guild: discord.Guild, runs: list, run_index: int, total_runs: int, target_id: Optional[str] = None) -> discord.Embed:
        """Build the Hall of Fame embed for a specific run"""
        run = runs[run_index]
        trainer_discord_id = run['discord_id']

        # Try to get the member from the guild
        display_name = f"Trainer ({trainer_discord_id})"
        avatar_url = None
        try:
            # Try cache first (no API call)
            member = guild.get_member(int(trainer_discord_id))
            if member is None:
                # Try fetching from guild
                member = await guild.fetch_member(int(trainer_discord_id))
            if member:
                display_name = member.display_name
                avatar_url = str(member.display_avatar.url)
        except Exception:
            try:
                # Fallback: fetch user directly (doesn't need Members intent)
                fetched_user = await self.bot.fetch_user(int(trainer_discord_id))
                if fetched_user:
                    display_name = fetched_user.display_name
                    avatar_url = str(fetched_user.display_avatar.url)
            except Exception:
                pass

        # Figure out the run number for this specific trainer
        # Count how many runs this trainer has, and which one this is
        trainer_run_number = self.__get_trainer_run_number(runs, run_index)

        victory_time = run['victory_at']
        if victory_time:
            timestamp_str = f"<t:{int(victory_time.timestamp())}:F>"
        else:
            timestamp_str = "Unknown"

        if target_id:
            title = "🏆 Hall of Fame"
        else:
            title = "🏆 Hall of Fame — All Champions"

        embed = discord.Embed(
            title=title,
            description=f"**{display_name}** — Victory #{trainer_run_number}\n{timestamp_str}",
            color=discord.Color.gold()
        )

        if avatar_url:
            embed.set_author(name=display_name, icon_url=avatar_url)

        # Build party display
        party_lines = []
        for pokemon_name, pokemon_level in run['pokemon']:
            display_poke = pokemon_name.capitalize() if pokemon_name else "???"
            try:
                import constant
                emoji = constant.POKEMON_EMOJIS.get(pokemon_name.upper(), '') if pokemon_name else ''
            except Exception:
                emoji = ''

            party_lines.append(f"{emoji} **{display_poke}** — Lv. {pokemon_level}")

        embed.add_field(
            name="🎖️ Champion Team",
            value="\n".join(party_lines) if party_lines else "No data",
            inline=False
        )

        embed.set_footer(text=f"{run_index + 1} of {total_runs}")

        return embed

    def __get_trainer_run_number(self, runs: list, current_index: int) -> int:
        """Calculate which victory number this is for the specific trainer (oldest = #1)"""
        current_run = runs[current_index]
        trainer_id = current_run['discord_id']
        current_run_id = current_run['run_id']

        # Get all run_ids for this trainer from the runs list, sorted ascending
        trainer_run_ids = sorted(set(
            r['run_id'] for r in runs if r['discord_id'] == trainer_id
        ))

        if current_run_id in trainer_run_ids:
            return trainer_run_ids.index(current_run_id) + 1
        return 1

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

        runs = self.__get_runs(state.targetId)
        if not runs:
            return

        state.run_index = min(state.run_index + 1, len(runs) - 1)
        state.total_runs = len(runs)

        guild = interaction.guild
        embed = await self.__build_hof_embed(guild, runs, state.run_index, state.total_runs, state.targetId)
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

        runs = self.__get_runs(state.targetId)
        if not runs:
            return

        state.run_index = max(state.run_index - 1, 0)
        state.total_runs = len(runs)

        guild = interaction.guild
        embed = await self.__build_hof_embed(guild, runs, state.run_index, state.total_runs, state.targetId)
        view = self.__build_hof_view(state.run_index, state.total_runs)
        await interaction.message.edit(embed=embed, view=view)