from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from discord import embeds
from discord_components import (DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)
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
    async def v2(self, ctx: commands.Context) -> None:
        # """Gets the admin commands for react emojis cog."""
        # await ctx.send("Received map %s" %map)
        pass
    
    @v2.command()
    async def books(self, ctx: commands.Context, interaction: Interaction, map: str) -> None:
        """Takes a map name and returns books."""
        # if frequency <= 0:
        firstRowBtns = []
        firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray,
                       label='Previous', custom_id='previous'),
                self.__on_prev_click
            ))
        embed = discord.Embed()
        embed=discord.Embed(title="Owen Wilson", url="https://www.tomorrowtides.com/owen-wilson-movies.html", color=0x0b1bf4)
        embed.add_field(name="Movie", value='Test Movie', inline=True)

        message = await interaction.edit_origin(embed=embed, components=firstRowBtns)
        
        await ctx.send("Received your books command! %s" %map)
        await ctx.send("message = %s" %message)
        return

        # await self.config.channel(ctx.channel).set_raw("frequency", value=frequency)
        # await ctx.tick()

    # @v2Books.group()
    # async def v2Book(self, ctx: commands.Context) -> None:
    #     """Add / Remove a website from the checking list."""
    #     await ctx.send("Received your v2Book command!")
    #     return
