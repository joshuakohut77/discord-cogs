from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from .duplicatesclass import Duplicates as DupeCls

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
        self.bot: Red = bot


    @commands.group()
    @commands.guild_only()
    async def duplicates(self, ctx: commands.Context) -> None:
        """Gets the admin commands for react emojis cog."""
        pass
    
    @duplicates.command()
    async def size(self, ctx: commands.Context) -> None:
        size = DupeCls.get_table_size()
        await ctx.send("Table Size: %s" %(str(size)))
        return

    @duplicates.command()
    async def count(self, ctx: commands.Context) -> None:
        count = DupeCls.get_message_count()
        await ctx.send("Message Count: %s" %(str(count)))
        return