from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from .duplicatesclass import Duplicates as DupeCls
from .dbclass import DatabasePool

if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands

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
        """Initialize database pool"""
        self.db_pool.initialize()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.db_pool.close()

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