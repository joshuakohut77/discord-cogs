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
        username = message.username

        if not Duplicates.has_extension(msg):
            msgHash = Duplicates.hash_string(msg)
            Duplicates.insert_message(msgHash, username)


