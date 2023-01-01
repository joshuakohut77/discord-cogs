from __future__ import annotations
from typing import TYPE_CHECKING
from redbot.core import commands
from ChodeCoin.core.abcd import MixinMeta
from ..utilities.coin_manager import CoinManager
from ..utilities.message_manager import MessageManager

if TYPE_CHECKING:
    import discord


class EventMixin(MixinMeta):
    __slots__: tuple = ()

    def __init__(self, message_manager=MessageManager(), coin_manager=CoinManager(), *args):
        super().__init__(*args)
        self.message_manager = message_manager
        self.coin_manager = coin_manager

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        msg: str = message.content
        result, reply = self.message_manager.process_message(msg)
        if result:
            await message.reply(reply)
