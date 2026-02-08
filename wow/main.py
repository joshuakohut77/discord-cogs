from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABCMeta

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands
from .event import EventMixin


class CompositeClass(commands.CogMeta, ABCMeta):
    """Metaclass combining CogMeta and ABCMeta."""
    __slots__: tuple = ()


class OwenWilson(EventMixin, commands.Cog, metaclass=CompositeClass):
    """A cog that responds to 'wow' with Owen Wilson clips."""
    
    def __init__(self, bot: Red):
        self.bot: Red = bot
    
    def cog_unload(self):
        """Cleanup when cog is unloaded."""
        pass