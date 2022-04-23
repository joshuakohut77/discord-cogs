from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta

if TYPE_CHECKING:
    from redbot.core.bot import Red

# import emojis
import discord
from redbot.core import Config, commands

from .event import EventMixin


class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class Pokemon(EventMixin, commands.Cog, metaclass=CompositeClass):
    """Pokemon"""

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, identifier=4206980085, force_registration=True)

        default_channel: Dict[str, Any] = {
            "enabled": True,
        }
        default_guild: Dict[str, Any] = {
            "enabled": True
        }
        self.config.register_channel(**default_channel)
        self.config.register_guild(**default_guild)


    async def guild_only_check():
        async def pred(self, ctx: commands.Context):
            if ctx.guild is not None and await self.config.guild(ctx.guild).enabled():
                return True
            else:
                return False

        return commands.check(pred)


    @guild_only_check()
    @commands.group(name="trainer")
    async def _trainer(self, ctx: commands.Context):
        """Base command to manage the trainer (user).
        """
        pass

    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: discord.Member = None):
        """Show the starter pokemon for the trainer.
        """
        if user is None:
            user = ctx.author

        await ctx.send("trainer command hit")

