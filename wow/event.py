from __future__ import annotations
from typing import TYPE_CHECKING
from discord import embeds
import discord
from .abc import MixinMeta

if TYPE_CHECKING:
    import discord

from redbot.core import commands
from .wowclass import Wow
import re

class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
		
        msg: str = message.content.lower()
        if re.search("w+o+w+", msg):
            owenWilson = Wow()
            newMsg, videoLink = owenWilson.getWow()
            await message.reply(newMsg)
            embed = discord.Embed()
            file = discord.File(videoLink)
            embed.set_image(url="attachment://%s" %videoLink)
            await ctx.send(embed=embed, file=file)

		