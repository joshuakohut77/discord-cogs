from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC

if TYPE_CHECKING:
    from redbot.core import Config
    from redbot.core.bot import Red
    from .database import DankDatabase


class MixinMeta(ABC):
    """
    Base class for mixins.
    
    Provides type hints for the bot, config, and database objects
    that will be available in all mixins.
    """
    
    def __init__(self, *args):
        self.bot: Red
        self.config: Config
        self.db: DankDatabase