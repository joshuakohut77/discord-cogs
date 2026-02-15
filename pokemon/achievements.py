from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import discord
from discord import Embed

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands
from redbot.core.commands.context import Context

from services.trainerclass import trainer as TrainerClass
from services.pokedexclass import pokedex as PokedexClass
from services.dbclass import db as dbconn
from .abcd import MixinMeta


class AchievementsMixin(MixinMeta):
    """Achievement system for tracking and announcing player milestones"""

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: Context) -> None:
        """Base command to manage the trainer (user)."""
        pass

    @_trainer.command(name="setachievements")
    @commands.admin_or_permissions(manage_guild=True)
    async def set_achievement_channel(self, ctx: Context, channel: discord.TextChannel = None) -> None:
        """
        Set the channel for achievement announcements.
        
        Usage: [p]trainer setachievements #channel-name
        or: [p]trainer setachievements (to use current channel)
        
        To disable: [p]trainer setachievements disable
        """
        if channel is None and len(ctx.message.content.split()) > 2:
            # Check if they typed "disable"
            if "disable" in ctx.message.content.lower():
                await self.config.guild(ctx.guild).achievement_channel.set(None)
                await ctx.send("✅ Achievement announcements have been disabled.")
                return
            else:
                channel = ctx.channel
        elif channel is None:
            channel = ctx.channel
        
        await self.config.guild(ctx.guild).achievement_channel.set(channel.id)
        await ctx.send(f"✅ Achievement announcements will be sent to {channel.mention}")

    async def send_achievement(
        self, 
        guild: discord.Guild, 
        user: discord.Member, 
        achievement_type: str,
        **kwargs
    ) -> None:
        """
        Send an achievement announcement to the configured channel.
        
        Args:
            guild: The guild where the achievement occurred
            user: The user who earned the achievement
            achievement_type: Type of achievement (badge, capture_milestone, elite_four, evolution, easter_egg)
            **kwargs: Additional data specific to the achievement type
        """
        # Get achievement channel from config
        channel_id = await self.config.guild(guild).achievement_channel()
        
        if channel_id is None:
            return  # Achievements disabled for this guild
        
        channel = guild.get_channel(channel_id)
        if channel is None:
            return  # Channel no longer exists
        
        # Create embed based on achievement type
        embed = None
        
        if achievement_type == "badge":
            badge_name = kwargs.get("badge_name", "Badge")
            gym_name = kwargs.get("gym_name", "Gym")
            embed = Embed(
                title="🏆 Badge Earned!",
                description=f"**{user.display_name}** has earned the **{badge_name}** by defeating the {gym_name}!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
        elif achievement_type == "capture_milestone":
            count = kwargs.get("count", 0)
            emoji_map = {50: "🌟", 100: "⭐", 150: "💫"}
            emoji = emoji_map.get(count, "✨")
            embed = Embed(
                title=f"{emoji} Capture Milestone!",
                description=f"**{user.display_name}** has captured **{count} different Pokémon species**!",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
        elif achievement_type == "elite_four":
            embed = Embed(
                title="👑 Champion Crowned!",
                description=f"**{user.display_name}** has defeated the Elite Four and become the Pokémon Champion!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text="A legendary achievement!")
            
        elif achievement_type == "first_evolution":
            pokemon_name = kwargs.get("pokemon_name", "Unknown")
            embed = Embed(
                title="🌊 First Evolution Discovery!",
                description=f"**{user.display_name}** is the first trainer to evolve a **{pokemon_name.capitalize()}**!",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text="A historic moment in Pokémon history!")
            
        elif achievement_type == "easter_egg":
            egg_id = kwargs.get("egg_id", "???")
            embed = Embed(
                title="🥚 Easter Egg Discovered!",
                description=f"**{user.display_name}** has discovered a secret easter egg!",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text="Keep exploring to find more secrets...")
        
        if embed:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass  # Bot doesn't have permission to send to that channel
            except Exception:
                pass  # Silently fail if something goes wrong

    async def check_capture_milestones(self, user_id: str, guild: discord.Guild) -> None:
        """
        Check if user has reached a capture milestone and send achievement if so.
        
        Args:
            user_id: Discord ID of the user
            guild: The guild to send the achievement to
        """
        try:
            # Get user's pokedex count
            db = dbconn()
            query = 'SELECT COUNT(*) FROM pokedex WHERE discord_id = %(discord_id)s'
            result = db.querySingle(query, {'discord_id': user_id})
            
            if not result:
                return
            
            count = result[0]
            milestones = [50, 100, 150]
            
            # Check if they just hit a milestone
            for milestone in milestones:
                if count == milestone:
                    user = guild.get_member(int(user_id))
                    if user:
                        await self.send_achievement(
                            guild=guild,
                            user=user,
                            achievement_type="capture_milestone",
                            count=milestone
                        )
                    break
        except Exception:
            pass  # Silently fail
        finally:
            if db:
                del db

    async def check_first_evolution(
        self, 
        user_id: str, 
        guild: discord.Guild, 
        pokemon_name: str
    ) -> None:
        """
        Check if this is the first time ANY user has evolved this pokemon.
        
        Args:
            user_id: Discord ID of the user who evolved the pokemon
            guild: The guild to send the achievement to
            pokemon_name: Name of the evolved pokemon (e.g., "vaporeon")
        """
        try:
            # Check if anyone has evolved this pokemon before
            db = dbconn()
            
            # Check if this evolution has been achieved before
            check_query = '''
                SELECT 1 FROM first_evolutions 
                WHERE guild_id = %(guild_id)s AND pokemon_name = %(pokemon_name)s
            '''
            result = db.querySingle(check_query, {
                'guild_id': str(guild.id),
                'pokemon_name': pokemon_name.lower()
            })
            
            if result:
                return  # Someone already evolved this pokemon first
            
            # Record this as the first evolution
            insert_query = '''
                INSERT INTO first_evolutions (guild_id, discord_id, pokemon_name, evolved_at)
                VALUES (%(guild_id)s, %(discord_id)s, %(pokemon_name)s, NOW())
            '''
            db.execute(insert_query, {
                'guild_id': str(guild.id),
                'discord_id': user_id,
                'pokemon_name': pokemon_name.lower()
            })
            
            # Send achievement
            user = guild.get_member(int(user_id))
            if user:
                await self.send_achievement(
                    guild=guild,
                    user=user,
                    achievement_type="first_evolution",
                    pokemon_name=pokemon_name
                )
        except Exception as e:
            pass  # Silently fail if table doesn't exist yet
        finally:
            if db:
                del db

    async def send_easter_egg_achievement(
        self, 
        user_id: str, 
        guild: discord.Guild, 
        egg_id: str
    ) -> None:
        """
        Send an easter egg discovery achievement (without spoiling the egg).
        
        Args:
            user_id: Discord ID of the user who found the egg
            guild: The guild to send the achievement to
            egg_id: Identifier for the easter egg (not shown to other users)
        """
        try:
            # Check if this user already found this egg
            db = dbconn()
            check_query = '''
                SELECT 1 FROM easter_eggs_found 
                WHERE guild_id = %(guild_id)s AND discord_id = %(discord_id)s AND egg_id = %(egg_id)s
            '''
            result = db.querySingle(check_query, {
                'guild_id': str(guild.id),
                'discord_id': user_id,
                'egg_id': egg_id
            })
            
            if result:
                return  # User already found this egg
            
            # Record the discovery
            insert_query = '''
                INSERT INTO easter_eggs_found (guild_id, discord_id, egg_id, found_at)
                VALUES (%(guild_id)s, %(discord_id)s, %(egg_id)s, NOW())
            '''
            db.execute(insert_query, {
                'guild_id': str(guild.id),
                'discord_id': user_id,
                'egg_id': egg_id
            })
            
            # Send achievement (without spoiling what the egg was)
            user = guild.get_member(int(user_id))
            if user:
                await self.send_achievement(
                    guild=guild,
                    user=user,
                    achievement_type="easter_egg",
                    egg_id=egg_id
                )
        except Exception:
            pass  # Silently fail
        finally:
            if db:
                del db