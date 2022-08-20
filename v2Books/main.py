from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from discord import embeds
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType
if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands

# from .event import EventMixin

# class CompositeClass(commands.CogMeta, ABCMeta):
#     __slots__: tuple = ()
#     pass
# class v2Books(EventMixin, commands.Cog):
class v2Books(commands.Cog):
    """Warhammer Books."""

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, identifier=2091831, force_registration=True)
        DiscordComponents(bot, change_discord_methods=True)

    @commands.group()
    async def v2(self, ctx: commands.Context) -> None:
        # """Gets the admin commands for react emojis cog."""
        # await ctx.send("Received map %s" %map)
        pass
    
    @v2.command()
    async def books(self, ctx: commands.Context) -> None:
        """Takes a map name and returns books."""
        await ctx.send(type=InteractionType.ChannelMessageWithSource, content="Message Here", components=[Button(style=ButtonStyle.URL, label="Example Invite Button", url="https://google.com"), Button(style=ButtonStyle.blue, label="Default Button", custom_id="button")])
        
                
        
        # message = await interaction.edit_origin(embed=embed, components=firstRowBtns)
        

        
        # await ctx.send("message = %s" %message)
        return

        # await self.config.channel(ctx.channel).set_raw("frequency", value=frequency)
        # await ctx.tick()

    # @v2Books.group()
    # async def v2Book(self, ctx: commands.Context) -> None:
    #     """Add / Remove a website from the checking list."""
    #     await ctx.send("Received your v2Book command!")
    #     return
