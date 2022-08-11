from __future__ import annotations
from typing import TYPE_CHECKING
from discord import embeds
import discord
import requests
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
            embed, videoLink = owenWilson.getWow()
            
            
            r = requests.get(videoLink)
            with open("/tempfiles/wowclip.mp4", 'wb') as f:
            #giving a name and saving it in any required format
            #opening the file in write mode
                f.write(r.content) 
            file = discord.File('/tempfiles/wowclip.mp4')

            await ctx.send(embed=embed)

            # await message.reply(newMsg, file=file)
