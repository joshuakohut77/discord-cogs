from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABCMeta
import asyncio
import logging

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from .events import EventMixin
from .commands import CommandsMixin
from .admin import AdminMixin
from .dbclass import DatabasePool
from .db import ChodeCoinDB

log = logging.getLogger("red.chodecoin")


class CompositeClass(commands.CogMeta, ABCMeta):
    """Metaclass combining CogMeta and ABCMeta."""
    __slots__: tuple = ()


class ChodeCoin(
    EventMixin,
    CommandsMixin,
    AdminMixin,
    commands.Cog,
    metaclass=CompositeClass,
):
    """A coin economy cog. @user++ / @user-- to give or take ChodeCoin."""

    def __init__(self, bot: Red):
        self.bot: Red = bot

    async def initialize(self) -> None:
        """Called from __init__.py after construction."""
        DatabasePool.initialize()
        await asyncio.to_thread(ChodeCoinDB.create_tables)
        log.info("ChodeCoin tables ready.")

    def cog_unload(self):
        """Cleanup when cog is unloaded."""
        DatabasePool.close()