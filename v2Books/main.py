from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from discord import embeds

from discord_components import DiscordComponents, Select, SelectOption, Button,ButtonStyle


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
        # DiscordComponents(bot, change_discord_methods=True)

    bot = commands.Bot(command_prefix='.')

    @commands.group()
    async def v2(self, ctx: commands.Context) -> None:
        # """Gets the admin commands for react emojis cog."""
        # await ctx.send("Received map %s" %map)
        pass

    @v2.command()
    async def button(self, ctx):
        embed = discord.Embed(title='Test',description='Test text')

        await ctx.send(embed=embed, components=[Button(label='Test', custom_id="test-id", style=ButtonStyle.red)])
        interaction = await self.bot.wait_for(
        "button_click", check=lambda inter: inter.custom_id == "test-id")

    @bot.event
    async def button_click(self, interaction):
        await interaction.respond(type=6)
        await interaction.author.send("Click")
    

    @v2.command()
    async def books(self, ctx: commands.Context) -> None:
        """Takes a map name and returns books."""
     
        await ctx.send("message = it kinda worked?")
        return

        # await self.config.channel(ctx.channel).set_raw("frequency", value=frequency)
        # await ctx.tick()

    # @v2Books.group()
    # async def v2Book(self, ctx: commands.Context) -> None:
    #     """Add / Remove a website from the checking list."""
    #     await ctx.send("Received your v2Book command!")
    #     return
