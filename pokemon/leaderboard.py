from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Button, View, Select

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands
from redbot.core.commands.context import Context

from services.trainerclass import trainer as TrainerClass
from services.leaderboardclass import leaderboard as LeaderBoardClass
from services.dbclass import db as dbconn

from .abcd import MixinMeta


DiscordUser = Union[discord.Member, discord.User]


class LeaderboardMixin(MixinMeta):
    """Leaderboard commands"""

    __leaderboard_states: dict[str, str] = {}  # Maps user_id -> selected_discord_id

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user)."""
        pass

    @_trainer.command(name="stats", aliases=['lb'])
    async def stats(self, ctx: commands.Context, user: DiscordUser = None):
        """
        View leaderboard stats for a specific player.
        Use the dropdown to switch between different trainers.
        """
        author: DiscordUser = ctx.author
        
        # Get all trainers from database
        db = dbconn()
        query = """
            SELECT DISTINCT t.discord_id, t.startdate 
            FROM trainer t
            JOIN leaderboard l ON t.discord_id = l.discord_id
            WHERE l.total_battles > 0 OR l.total_catch > 0
            ORDER BY t.startdate DESC
            LIMIT 25
        """
        results = db.queryAll(query, {})
        
        if not results or len(results) == 0:
            await ctx.send("No trainers found with stats.")
            return
        
        # If user specified, use that, otherwise use author
        if user is None:
            selected_discord_id = str(ctx.author.id)
        else:
            selected_discord_id = str(user.id)
        
        # Store selection state
        self.__leaderboard_states[str(author.id)] = selected_discord_id
        
        # Create embed and view
        embed = await self.__create_player_stats_embed(ctx, selected_discord_id)
        view = await self.__create_player_stats_view(ctx, results, selected_discord_id)
        
        await ctx.send(embed=embed, view=view)

    async def __create_player_stats_embed(self, ctx: Context, discord_id: str) -> discord.Embed:
        """Create the stats embed for a specific player"""
        try:
            # Get the Discord user
            user = await ctx.guild.fetch_member(int(discord_id))

            # Load leaderboard stats
            stats = LeaderBoardClass(discord_id)
            stats.load()

            # Load additional stats from DB
            db = dbconn()

            # Pokémon owned (not deleted)
            pokemon_count_result = db.querySingle(
                "SELECT COUNT(*) FROM pokemon WHERE discord_id = %(did)s AND (is_deleted = FALSE OR is_deleted IS NULL)",
                {'did': discord_id}
            )
            pokemon_owned = pokemon_count_result[0] if pokemon_count_result else 0

            # Shiny owned (not deleted)
            shiny_count_result = db.querySingle(
                "SELECT COUNT(*) FROM pokemon WHERE discord_id = %(did)s AND is_shiny = TRUE AND (is_deleted = FALSE OR is_deleted IS NULL)",
                {'did': discord_id}
            )
            shiny_owned = shiny_count_result[0] if shiny_count_result else 0

            # Pokédex entries
            pokedex_result = db.querySingle(
                "SELECT COUNT(*) FROM pokedex WHERE discord_id = %(did)s",
                {'did': discord_id}
            )
            pokedex_seen = pokedex_result[0] if pokedex_result else 0

            # Trainers defeated
            trainers_defeated_result = db.querySingle(
                "SELECT COUNT(*) FROM trainer_battles WHERE discord_id = %(did)s",
                {'did': discord_id}
            )
            trainers_defeated = trainers_defeated_result[0] if trainers_defeated_result else 0

            # Badges owned — count True badge columns in keyitems
            badges_result = db.querySingle(
                """
                SELECT (
                    (badge_boulder::int) + (badge_cascade::int) + (badge_thunder::int) +
                    (badge_rainbow::int) + (badge_soul::int) + (badge_marsh::int) +
                    (badge_volcano::int) + (badge_earth::int)
                ) FROM keyitems WHERE discord_id = %(did)s
                """,
                {'did': discord_id}
            )
            badges_owned = badges_result[0] if badges_result else 0

            # Create embed
            embed = discord.Embed(
                title=f"📊 Trainer Stats",
                color=discord.Color.blue()
            )
            embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))

            # --- Progress ---
            embed.add_field(name='🏅 Badges', value=f'{badges_owned}/8', inline=True)
            embed.add_field(name='📖 Pokédex', value=f'{pokedex_seen} seen', inline=True)
            embed.add_field(name='🎒 Pokémon Owned', value=f'{pokemon_owned}', inline=True)
            embed.add_field(name='✨ Shinies Owned', value=f'{shiny_owned}', inline=True)
            embed.add_field(name='🥚 Easter Eggs', value=f'{stats.total_easter_eggs or 0}', inline=True)
            embed.add_field(name='⚡ Pokémon Evolved', value=f'{stats.total_evolved or 0}', inline=True)

            # --- Battle Stats ---
            embed.add_field(name='⚔️ Total Battles', value=f'{stats.total_battles or 0}', inline=True)
            embed.add_field(name='🏆 Victories', value=f'{stats.total_victory or 0}', inline=True)
            embed.add_field(name='💀 Defeats', value=f'{stats.total_defeat or 0}', inline=True)

            if stats.total_battles and stats.total_battles > 0:
                win_rate = (stats.total_victory or 0) / stats.total_battles * 100
                embed.add_field(name='📈 Win Rate', value=f'{win_rate:.1f}%', inline=True)
            else:
                embed.add_field(name='📈 Win Rate', value='N/A', inline=True)

            embed.add_field(name='🧑‍🏫 Trainers Defeated', value=f'{trainers_defeated}', inline=True)
            embed.add_field(name='🎮 Actions', value=f'{stats.total_actions or 0}', inline=True)

            # --- Catching Stats ---
            embed.add_field(name='🎯 Pokéballs Thrown', value=f'{stats.total_balls_thrown or 0}', inline=True)
            embed.add_field(name='✅ Pokémon Caught', value=f'{stats.total_catch or 0}', inline=True)
            embed.add_field(name='🏃 Run Aways', value=f'{stats.total_run_away or 0}', inline=True)
            embed.add_field(name='🗑️ Released', value=f'{stats.total_released or 0}', inline=True)
            embed.add_field(name='🔄 Trades', value=f'{stats.total_trades or 0}', inline=True)
            embed.add_field(name='✔️ Completions', value=f'{stats.total_completions or 0}', inline=True)

            return embed

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Could not load stats for this trainer.",
                color=discord.Color.red()
            )
            return embed

    async def __create_player_stats_view(self, ctx: Context, trainers: List, selected_discord_id: str) -> View:
        """Create view with trainer dropdown"""
        view = View()
        
        # Create dropdown with all trainers
        select = Select(
            placeholder="Select a trainer to view stats...",
            custom_id='trainer_select',
            row=0
        )
        
        for trainer_data in trainers:
            discord_id = str(trainer_data[0])
            try:
                user = await ctx.guild.fetch_member(int(discord_id))
                select.add_option(
                    label=f"{user.display_name}",
                    value=discord_id,
                    description=f"Started: {trainer_data[1]}",
                    default=(discord_id == selected_discord_id)
                )
            except:
                # Skip if user not in guild
                continue
        
        select.callback = self.on_trainer_stats_select
        view.add_item(select)
        
        return view

    async def on_trainer_stats_select(self, interaction: discord.Interaction):
        """Handle trainer selection from dropdown"""
        await interaction.response.defer()
        
        selected_discord_id = interaction.data['values'][0]
        user = interaction.user
        
        # Update state
        self.__leaderboard_states[str(user.id)] = selected_discord_id
        
        # Get trainers list again
        db = dbconn()
        query = """
            SELECT DISTINCT t.discord_id, t.startdate 
            FROM trainer t
            JOIN leaderboard l ON t.discord_id = l.discord_id
            WHERE l.total_battles > 0 OR l.total_catch > 0
            ORDER BY t.startdate DESC
            LIMIT 25
        """
        results = db.queryAll(query, {})
        
        # Recreate embed and view
        ctx = await self.bot.get_context(interaction.message)
        embed = await self.__create_player_stats_embed(ctx, selected_discord_id)
        view = await self.__create_player_stats_view(ctx, results, selected_discord_id)
        
        await interaction.message.edit(embed=embed, view=view)

    @_trainer.command(name="leaderboard", aliases=['rankings', 'top'])
    async def leaderboard(self, ctx: commands.Context):
        """
        View the global leaderboard rankings.
        Shows top trainers by key stats.
        """
        db = dbconn()
        
        # Get top trainers by different metrics
        query = """
            SELECT 
                t.discord_id,
                l.total_battles,
                l.total_victory,
                l.total_catch,
                l.total_evolved,
                CASE 
                    WHEN l.total_battles > 0 THEN ROUND((l.total_victory::numeric / l.total_battles * 100)::numeric, 1)
                    ELSE 0
                END as win_rate
            FROM trainer t
            JOIN leaderboard l ON t.discord_id = l.discord_id
            WHERE l.total_battles > 0
            ORDER BY l.total_battles DESC, l.total_victory DESC
            LIMIT 10
        """
        
        results = db.queryAll(query, {})
        
        if not results or len(results) == 0:
            await ctx.send("No trainers on the leaderboard yet!")
            return
        
        # Create leaderboard embed
        embed = discord.Embed(
            title="🏆 Global Trainer Leaderboard",
            description="Top trainers by battle experience",
            color=discord.Color.gold()
        )
        
        # Build leaderboard text
        leaderboard_text = []
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, trainer_data in enumerate(results):
            discord_id = str(trainer_data[0])
            total_battles = trainer_data[1] or 0
            total_victory = trainer_data[2] or 0
            total_catch = trainer_data[3] or 0
            total_evolved = trainer_data[4] or 0
            win_rate = trainer_data[5] or 0
            
            try:
                user = await ctx.guild.fetch_member(int(discord_id))
                
                # Medal for top 3
                rank_symbol = medals[idx] if idx < 3 else f"`#{idx + 1}`"
                
                leaderboard_text.append(
                    f"{rank_symbol} **{user.display_name}**\n"
                    f"   ⚔️ {total_battles} battles | 🏆 {total_victory} wins ({win_rate}%)\n"
                    f"   ✨ {total_catch} caught | ⚡ {total_evolved} evolved\n"
                )
            except:
                # Skip if user not in guild
                continue
        
        embed.description = "\n".join(leaderboard_text) if leaderboard_text else "No trainers found."
        
        # Add footer
        embed.set_footer(text="Use ,trainer stats to see detailed stats for any trainer")
        
        await ctx.send(embed=embed)