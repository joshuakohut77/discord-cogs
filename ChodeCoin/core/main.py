from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABCMeta

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from ChodeCoin.core.event import EventMixin

class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass

class ChodeCoin(EventMixin, commands.Cog, metaclass=CompositeClass):
    """chodecoin"""

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot