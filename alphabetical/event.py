from __future__ import annotations
from typing import TYPE_CHECKING
from discord import embeds
import discord

from .abc import MixinMeta

if TYPE_CHECKING:
    import discord

from redbot.core import commands
from .alphabeticalclass import Alphabetical
import re

class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
		
        msg: str = message.content.lower()
        if Alphabetical.are_words_alphabetical_order(msg):
            if Alphabetical.check_sentence(msg):

                embed = discord.Embed()
                embed=discord.Embed(title="Alphabet Soup!", description="All your words are in alphabetical order.", color=0x0b1bf4)            

                await message.reply(embed=embed)

