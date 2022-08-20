from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from discord import embeds
from discord_components import (DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)
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

    @commands.group()
    async def v2(self, ctx: commands.Context) -> None:
        # """Gets the admin commands for react emojis cog."""
        # await ctx.send("Received map %s" %map)
        pass
    
    @v2.command()
    async def books(self, ctx: commands.Context) -> None:
        """Takes a map name and returns books."""
        # if frequency <= 0:
        lib = require('lib')({token: process.env.STDLIB_SECRET_TOKEN});

        await lib.discord.channels['@0.3.0'].messages.create({
        "channel_id": `${context.params.event.channel_id}`,
        "content": `Warhammer Vermintide 2 - Books`,
        "tts": false,
        "components": [
            {
            "type": 1,
            "components": [
                {
                "custom_id": `row_0_select_0`,
                "options": [
                    {
                    "label": `location 1`,
                    "description": `location 1 description`,
                    "default": true
                    },
                    {
                    "label": `location 2`,
                    "description": `location 2 description`,
                    "default": false
                    }
                ],
                "min_values": 1,
                "max_values": 1,
                "type": 3
                }
            ]
            }
        ],
        "embeds": [
            {
            "type": "rich",
            "title": `Tomes and Grims`,
            "description": `Get data on grims and tomes`,
            "color": 0x00FFFF
            }
        ]
        });

        await ctx.send("Received your books command! %s" %map)
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
