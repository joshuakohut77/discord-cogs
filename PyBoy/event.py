from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from pyboy import PyBoy
from io import BytesIO
import asyncio
import os

from .abc import MixinMeta

# if TYPE_CHECKING:
#     import discord

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

        if len(msg.split()) < 5 or msg[0] == '.':
            return

        username = message.author

        if not Duplicates.has_extension(msg):
            msgHash = Duplicates.hash_string(msg)
            

            duplicateList = Duplicates.select_duplicates(msgHash)
            if len(duplicateList) > 0:
                eastern = pytz.timezone('US/Eastern')
                embed = discord.Embed()
                formattedDescription = ""
                for dupe in duplicateList:
                    formattedDescription += dupe["username"] + ' on: ' + str(dupe["timestamp"].astimezone(eastern).strftime('%m/%d/%y %H:%M %Z')) + '\n'
                embed=discord.Embed(title="Duplicate Message!", description=formattedDescription, color=0x0b1bf4)  

                await message.reply(embed=embed)
            
            Duplicates.insert_message(msgHash, username)
                

