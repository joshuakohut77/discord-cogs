from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING
import asyncio

import discord
from discord import (Embed, Member)
from discord import message
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass


from .abcd import MixinMeta
from services.pokeclass import Pokemon as PokemonClass
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class MapMixin(MixinMeta):
    """Map"""


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """

    @_trainer.command()
    async def map(self, ctx: commands.Context, user: discord.User = None):
        if user is None:
            user = ctx.author

        
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()

        file = discord.File(f"{location.spritePath}", filename=f"{location.name}.png")

        btns = []
        if location.north is not None:
            btns.append(Button(style=ButtonStyle.gray, label=f"{location.north} ↑"))
        if location.south is not None:
            btns.append(Button(style=ButtonStyle.gray, label=f"{location.south} ↓"))
        if location.east is not None:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=':arrow_right:')
            btns.append(Button(style=ButtonStyle.gray, emoji=emote, label=f"{location.east}"))
        if location.west is not None:
            btns.append(Button(style=ButtonStyle.gray, emoji=emote, label=f"{location.west}"))

        await ctx.send(
            content=location.name,
            file=file,
            components=[btns]
        )
