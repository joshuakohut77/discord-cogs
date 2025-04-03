from abc import ABCMeta
from redbot.core import commands
from ChodeCoin.core.event import EventMixin
from ChodeCoin.Backend.workflows.main_work_flow import process_leaderboard_request_command
import discord

class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass

class ChodeCoin(EventMixin, commands.Cog, metaclass=CompositeClass):
    """ChodeCoin"""

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot

    @commands.group()
    @commands.mod_or_permissions()
    @commands.guild_only()
    async def chodecoin(self, ctx: commands.Context, main) -> None:
        """Gets the admin commands for the ChodeCoin cog."""
        pass

    @chodecoin.command()
    async def leaderboard(self, ctx: commands.Context) -> None:
        """Displays the top 10 ChodeCoin owners in the server."""
        await ctx.process_leadership_request_command()
