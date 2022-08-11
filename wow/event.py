from __future__ import annotations
from typing import TYPE_CHECKING
from discord import embeds
import discord
import requests
# import shutil
# import urllib2
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
            
            # embed = discord.Embed()
            r = requests.get(videoLink)
            with open("/tempfiles/wowclip.mp4", 'wb') as f:
            #giving a name and saving it in any required format
            #opening the file in write mode
                f.write(r.content) 

            file = discord.File('/tempfiles/wowclip.mp4')
            # embed.set_image(url="https://imgur.com/gallery/lxig9RX")
            # await message.reply(file=file)

            await message.reply(newMsg, file=file)