from __future__ import annotations
from typing import TYPE_CHECKING

from redbot.core.commands.commands import command

if TYPE_CHECKING:
    from redbot.core import Config
    from redbot.core.bot import Red

from redbot.core import commands

from abc import ABC, abstractmethod
from discord_components.client import DiscordComponents

class MixinMeta(ABC):
    def __init__(self, *args):
        self.bot: Red
        self.config: Config
        self.client: DiscordComponents

    @abstractmethod
    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context):
        raise NotImplementedError
