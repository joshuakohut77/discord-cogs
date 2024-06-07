from __future__ import annotations
from typing import TYPE_CHECKING
from discord import embeds
import discord

from .abc import MixinMeta

if TYPE_CHECKING:
    import discord

from redbot.core import commands
from .duplicatesclass import Duplicates
import re

class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
		
        msg: str = message.content.lower()

        if len(msg.split()) < 5:
            return

        username = message.author

        if not Duplicates.has_extension(msg):
            msgHash = Duplicates.hash_string(msg)
            Duplicates.insert_message(msgHash, username)

            duplicateList = Duplicates.select_duplicates(msgHash)
            if len(duplicateList) > 0:
                embed = discord.Embed()
                formattedDescription = ""
                for dupe in duplicateList:
                    formattedDescription += dupe["username"] + ' on: ' + dupe["timestamp"]
                embed=discord.Embed(title="Duplicate Message!", description=formattedDescription, color=0x0b1bf4)  

                await message.reply(embed=embed)
                

