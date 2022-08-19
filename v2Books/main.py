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

class v2Books(EventMixin, commands.Cog):
    """Warhammer Books."""

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, identifier=2091831, force_registration=True)

    @commands.group()
    
    @v2Books.command()
    async def books(self, ctx: commands.Context, map: str) -> None:
        """Change the reacting frequency for the current channel."""
        # if frequency <= 0:
        await ctx.send("Received your books command!")
        return

        # await self.config.channel(ctx.channel).set_raw("frequency", value=frequency)
        # await ctx.tick()

    # @emojiadmin.command()
    # async def enable(self, ctx: commands.Context, true_or_false: bool) -> None:
    #     """Enable / Disable the reaction system."""
    #     await self.config.channel(ctx.channel).set_raw("enabled", value=true_or_false)
    #     await ctx.tick()

    # @emojiadmin.command()
    # async def multiplier(self, ctx: commands.Context, number: int) -> None:
    #     """Change the multiplier to change the chance a message can be reacted to from the bot."""
    #     if number <= 0:
    #         await ctx.send("Please set a number higher than zero!")
    #         return
            
    #     await self.config.channel(ctx.channel).set_raw("multiplier", value=number)
    #     await ctx.tick()
    
    @v2Books.group()
    async def v2Book(self, ctx: commands.Context) -> None:
        """Add / Remove a website from the checking list."""
        await ctx.send("Received your v2Book command!")
        return

    # @site.command(name="add")
    # async def _add(self, ctx: commands.Context, website: str) -> None:
    #     """Add a website to the checking list."""
    #     website: str = website.lower()
    #     async with self.config.guild(ctx.guild).websites() as websites:
    #         if website in websites:
    #             await ctx.send("That website already exists in the checking list.")
    #             return
    #         websites.append(website)
    #     await ctx.tick()
    
    # @site.command(name="remove")
    # async def _remove(self, ctx: commands.Context, website: str) -> None:
    #     """Remove a website from the checking list."""
    #     website: str = website.lower()
    #     async with self.config.guild(ctx.guild).websites() as websites:
    #         if website not in websites:
    #             await ctx.send("That website doesn't exists in the checking list.")
    #             return
    #         websites.remove(website)
    #     await ctx.tick()

    # @emojiadmin.group()
    # async def extensions(self, ctx: commands.Context) -> None:
    #     """Add / Remove an extension from the checking list."""
    #     pass
    
    # @extensions.command(name="add")
    # async def _add_(self, ctx: commands.Context, extension: str) -> None:
    #     """Add an extension to the checking list."""
    #     extension: str = extension.lower()
    #     async with self.config.guild(ctx.guild).extensions() as extensions:
    #         if extension in extensions:
    #             await ctx.send("That extension already exists in the checking list.")
    #             return
    #         extensions.append(extension)
    #     await ctx.tick()

    # @extensions.command(name="remove")
    # async def _remove_(self, ctx: commands.Context, extension: str) -> None:
    #     """Remove an extension from the checking list."""
    #     extension: str = extension.lower()
    #     async with self.config.guild(ctx.guild).extensions() as extensions:
    #         if extension not in extensions:
    #             await ctx.send("That extension doesn't exists in the checking list.")
    #             return
    #         extensions.remove(extension)
    #     await ctx.tick()

    # @emojiadmin.group(name="emoji")
    # async def _emoji(self, ctx: commands.Context) -> None:
    #     """Add / Remove an emoji from the emojis list for the current channel."""
    #     pass

