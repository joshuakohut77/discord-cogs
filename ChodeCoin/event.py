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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        msg: str = message.content.lower()
        if re.search("@.{2,32}?[+]{2}", msg):
            message_formatter = MessageFormatter()
            point_adder = CoinManager()
            targeted_user = message_formatter.extract_targeted_user(msg, "PlusPlus")
            point_adder.process_plus_plus(targeted_user)

        if re.search("@.{2,32}?-{2}", msg):
            message_formatter = MessageFormatter()
            coin_modifier = CoinManager()
            targeted_user = message_formatter.extract_targeted_user(msg, "MinusMinus")
            coin_modifier.process_minus_minus(targeted_user)
