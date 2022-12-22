from __future__ import annotations
import re
from typing import TYPE_CHECKING
import discord
from redbot.core import commands
from discord import embeds
from .abc import MixinMeta
from .coinModifier import CoinModifier

if TYPE_CHECKING:
    import discord

class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
		
        msg: str = message.content.lower()
        if re.search("@.*\+\+", msg):
            pointAdder = CoinModifier()
            embed, file = pointAdder.addCoin()
            await message.reply(file=file, embed=embed)

        if re.search("@.*\-\-", msg):
            pointSubtractor = CoinModifier()
            embed, file = pointSubtractor.subtractCoin()
            await message.reply(file=file, embed=embed)

