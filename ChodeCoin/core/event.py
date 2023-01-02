from __future__ import annotations
from typing import TYPE_CHECKING
from redbot.core import commands
from ChodeCoin.core.abcd import MixinMeta
from ..utilities.coin_manager import CoinManager
from ..utilities.message_reader import MessageManager
from ..workflows.main_work_flow import WorkFlow

if TYPE_CHECKING:
    import discord


class EventMixin(MixinMeta):
    __slots__: tuple = ()

    def __init__(self, message_manager=MessageManager(), coin_manager=CoinManager(), work_flow=WorkFlow(), *args):
        super().__init__(*args)
        self.message_manager = message_manager
        self.coin_manager = coin_manager
        self.work_flow = work_flow

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        msg: str = message.content
        author = message.author

        reply = self.work_flow.process_message(msg, author)
        if reply is not None:
            await message.reply(reply)
