from __future__ import annotations
from typing import TYPE_CHECKING
from redbot.core import commands
from ChodeCoin.core.abcd import MixinMeta
from ChodeCoin.Backend.workflows.main_work_flow import WorkFlow

if TYPE_CHECKING:
    import discord


class EventMixin(MixinMeta):
    __slots__: tuple = ()

    def __init__(self, work_flow=WorkFlow(), *args):
        super().__init__(*args)
        self.work_flow = work_flow

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        msg: str = message.content
        author = message.author.id
        channel = message.channel.__str__()
        embed = message.embeds

        reply, embed = self.work_flow.process_message(msg, author, channel, embed)
        await message.reply(channel.__str__())
        if reply is not None:
            await message.reply(reply, embed=embed)
