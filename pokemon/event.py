from __future__ import annotations
from typing import TYPE_CHECKING
from .abc import MixinMeta

if TYPE_CHECKING:
    import discord

from redbot.core import commands

class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        pass
		