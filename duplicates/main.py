from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from .duplicatesclass import Duplicates as DupeCls
from .dbclass import DatabasePool

if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands
from discord.ext import tasks

from .event import EventMixin

class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass

class Duplicates(EventMixin, commands.Cog, metaclass=CompositeClass):
    """Duplicates"""
	
    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.db_pool = DatabasePool()

    async def initialize(self):
        """Initialize database pool and start cleanup task"""
        self.db_pool.initialize()
        self.cleanup_old_messages.start()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.cleanup_old_messages.cancel()
        self.db_pool.close()

    @tasks.loop(hours=168)  # Run once a week
    async def cleanup_old_messages(self):
        """Remove messages older than 180 days to keep database size manageable"""
        try:
            DupeCls.cleanup_old_messages(days=180)
        except Exception as e:
            print(f"Error during cleanup: {e}")

    @cleanup_old_messages.before_loop
    async def before_cleanup(self):
        """Wait for bot to be ready before starting cleanup task"""
        await self.bot.wait_until_ready()

    @commands.group()
    @commands.guild_only()
    async def duplicates(self, ctx: commands.Context) -> None:
        """Gets the admin commands for duplicates cog."""
        pass
    
    @duplicates.command()
    async def size(self, ctx: commands.Context) -> None:
        """Get the total size of the duplicate_message table"""
        size = DupeCls.get_table_size()
        await ctx.send("Table Size: %s" %(str(size)))
        return

    @duplicates.command()
    async def count(self, ctx: commands.Context) -> None:
        """Get the total count of messages in the database"""
        count = DupeCls.get_message_count()
        await ctx.send("Message Count: %s" %(str(count)))
        return
    
    @duplicates.command()
    async def time(self, ctx: commands.Context) -> None:
        """Get the query execution time for duplicate lookups"""
        time = DupeCls.get_query_time()
        await ctx.send("%s" %(str(time)))
        return

    @duplicates.command()
    @commands.is_owner()
    async def cleanup(self, ctx: commands.Context, days: int = 180) -> None:
        """Manually trigger cleanup of old messages (owner only)
        
        Args:
            days: Number of days to keep (default: 180)
        """
        try:
            deleted = DupeCls.cleanup_old_messages(days)
            await ctx.send(f"Cleaned up messages older than {days} days. Deleted {deleted} messages.")
        except Exception as e:
            await ctx.send(f"Error during cleanup: {e}")