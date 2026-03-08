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
from .dbclass import VaultDatabasePool
from .db import VaultDB

log = logging.getLogger("red.vault")


class CompositeClass(commands.CogMeta, ABCMeta):
    """Metaclass combining CogMeta and ABCMeta."""
    __slots__: tuple = ()


class Vault(
    EventMixin,
    CommandsMixin,
    AdminMixin,
    commands.Cog,
    metaclass=CompositeClass,
):
    """The Vault — collectible card game powered by ChodeCoin."""

    def __init__(self, bot: Red):
        self.bot: Red = bot

    async def initialize(self) -> None:
        """Called from __init__.py after construction."""
        VaultDatabasePool.initialize()
        await asyncio.to_thread(VaultDB.create_tables)
        log.info("Vault tables ready.")

    def cog_unload(self):
        """Cleanup when cog is unloaded."""
        VaultDatabasePool.close()
