from __future__ import annotations
from typing import TYPE_CHECKING
from discord_components.client import DiscordComponents

if TYPE_CHECKING:
    from redbot.core import Config
    from redbot.core.bot import Red

from abc import ABC

class MixinMeta(ABC):
    def __init__(self, *args):
        self.bot: Red
        self.config: Config
        self.client: DiscordComponents
