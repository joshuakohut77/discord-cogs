from __future__ import annotations
import re
from typing import TYPE_CHECKING
import discord
from redbot.core import commands
from discord import embeds
from .abc import MixinMeta
from coin_manager import CoinManager
from message_formatter import MessageFormatter

if TYPE_CHECKING:
    import discord


class EventMixin(MixinMeta):
    __slots__: tuple = ()

    def __init__(self, message_formatter=MessageFormatter(), coin_manager=CoinManager()):
        self.message_formatter = message_formatter
        self.coin_manager = coin_manager

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        msg: str = message.content.lower()
        if re.search("@.{2,32}?[+]{2}", msg):
            targeted_user = self.message_formatter.extract_targeted_user(msg, "PlusPlus")
            self.coin_manager.process_plus_plus(targeted_user)

        if re.search("@.{2,32}?-{2}", msg):
            targeted_user = self.message_formatter.extract_targeted_user(msg, "MinusMinus")
            self.coin_manager.process_minus_minus(targeted_user)
