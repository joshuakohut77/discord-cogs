from __future__ import annotations
from typing import TYPE_CHECKING
from discord import embeds
import discord
# import requests
# import shutil
import urllib2
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
            # embed = discord.Embed()
            # response = requests.get(videoLink)
            file_name = '/tempfiles/wowclip.mp4' 
            rsp = urllib2.urlopen(videoLink)
            with open(file_name,'wb') as f:
                f.write(rsp.read())

            file = discord.File('/tempfiles/wowclip.mp4')
            # embed.set_image(url="https://imgur.com/gallery/lxig9RX")
            await message.reply(file=file)

		