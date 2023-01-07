from __future__ import annotations
from typing import TYPE_CHECKING
from redbot.core import commands
from ChodeCoin.core.abcd import MixinMeta
from ChodeCoinBackend.ChodeCoinBackend import WorkFlow

if TYPE_CHECKING:
    import discord


class EventMixin(MixinMeta):
    __slots__: tuple = ()

    def __init__(self, work_flow=WorkFlow(), *args):
        super().__init__(*args)
        self.work_flow = work_flow

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        msg: str = message.content
        author = message.author.id

        reply, embed = self.work_flow.process_message(msg, author)
        if reply is not None:
            await message.reply(reply, embed=embed)
