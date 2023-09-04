from __future__ import annotations
from typing import TYPE_CHECKING
from discord import embeds
import discord

from .abc import MixinMeta

if TYPE_CHECKING:
    import discord

from redbot.core import commands
from .whoaclass import Whoa
import re

class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
		
        msg: str = message.content.lower()
        if re.search("w+h+o+a+", msg) or re.search("w+o+a+h+", msg):
            keanuReeves = Whoa()
            embed, file = keanuReeves.getWhoa()
            await message.reply(file=file, embed=embed)
