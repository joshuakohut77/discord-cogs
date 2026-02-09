from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from .haikuclass import HaikuDetector
from .dbclass import DatabasePool

if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands

from .event import EventMixin

class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass

class Haiku(EventMixin, commands.Cog, metaclass=CompositeClass):
    """Detects and logs accidental haikus in messages"""
    
    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.db_pool = DatabasePool()
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        
        # Default settings
        default_guild = {
            "enabled": True
        }
        self.config.register_guild(**default_guild)

    async def initialize(self):
        """Initialize database pool and create table if needed"""
        self.db_pool.initialize()
        await self._create_table()

    async def _create_table(self):
        """Create the haiku table if it doesn't exist"""
        from .dbclass import db
        database = db()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS haiku (
            "Id" SERIAL PRIMARY KEY,
            "UserId" VARCHAR(255) NOT NULL,
            "Username" VARCHAR(255) NOT NULL,
            "GuildId" VARCHAR(255),
            "ChannelId" VARCHAR(255) NOT NULL,
            "MessageId" VARCHAR(255) NOT NULL,
            "OriginalText" TEXT NOT NULL,
            "FormattedHaiku" TEXT NOT NULL,
            "Timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            database.execute(create_table_query)
            
            # Create indexes for better query performance
            index_queries = [
                'CREATE INDEX IF NOT EXISTS idx_haiku_user ON haiku("UserId");',
                'CREATE INDEX IF NOT EXISTS idx_haiku_guild ON haiku("GuildId");',
                'CREATE INDEX IF NOT EXISTS idx_haiku_timestamp ON haiku("Timestamp");'
            ]
            
            for index_query in index_queries:
                database.execute(index_query)
                
        except Exception as e:
            print(f"Error creating haiku table: {e}")

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.db_pool.close()

    @commands.group()
    @commands.guild_only()
    async def haiku(self, ctx: commands.Context) -> None:
        """Haiku detection commands"""
        pass
    
    @haiku.command()
    async def count(self, ctx: commands.Context) -> None:
        """Get the total count of haikus detected"""
        try:
            count = HaikuDetector.get_haiku_count()
            await ctx.send(f"Total haikus detected: **{count}**")
        except Exception as e:
            await ctx.send(f"Error getting haiku count: {e}")
    
    @haiku.command()
    async def mycount(self, ctx: commands.Context) -> None:
        """Get your personal haiku count"""
        try:
            count = HaikuDetector.get_user_haiku_count(ctx.author.id)
            await ctx.send(f"{ctx.author.mention}, you have created **{count}** accidental haikus!")
        except Exception as e:
            await ctx.send(f"Error getting your haiku count: {e}")
    
    @haiku.command()
    async def leaderboard(self, ctx: commands.Context, limit: int = 10) -> None:
        """Show the top haiku creators
        
        Args:
            limit: Number of users to show (default: 10, max: 25)
        """
        if limit > 25:
            limit = 25
        
        try:
            top_users = HaikuDetector.get_top_haiku_users(limit)
            
            if not top_users:
                await ctx.send("No haikus have been detected yet!")
                return
            
            embed = discord.Embed(
                title="🍃 Haiku Leaderboard 🍃",
                color=0x90EE90
            )
            
            description = ""
            for i, (username, count) in enumerate(top_users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                description += f"{medal} **{username}**: {count} haiku{'s' if count != 1 else ''}\n"
            
            embed.description = description
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error getting leaderboard: {e}")
    
    @haiku.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def toggle(self, ctx: commands.Context) -> None:
        """Toggle haiku detection for this server"""
        current = await self.config.guild(ctx.guild).enabled()
        await self.config.guild(ctx.guild).enabled.set(not current)
        
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Haiku detection has been **{status}** for this server.")