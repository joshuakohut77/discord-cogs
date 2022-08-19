from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta

if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands

from .event import EventMixin

# class CompositeClass(commands.CogMeta, ABCMeta):
#     __slots__: tuple = ()
#     pass
# class v2Books(EventMixin, commands.Cog):
class v2Books(commands.Cog):
    """Warhammer Books."""

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, identifier=2091831, force_registration=True)

    @commands.group()
    async def v2Books(self, ctx: commands.Context, map: str) -> None:
        """Gets the admin commands for react emojis cog."""
        await ctx.send("Received map %s" %map)
        return
    
    # @v2Books.command()
    # async def books(self, ctx: commands.Context, map: str) -> None:
    #     """Change the reacting frequency for the current channel."""
    #     # if frequency <= 0:
    #     await ctx.send("Received your books command!")
    #     return

    #     # await self.config.channel(ctx.channel).set_raw("frequency", value=frequency)
    #     # await ctx.tick()

    # @v2Books.group()
    # async def v2Book(self, ctx: commands.Context) -> None:
    #     """Add / Remove a website from the checking list."""
    #     await ctx.send("Received your v2Book command!")
    #     return
