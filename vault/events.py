from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from redbot.core import commands
from .abc import MixinMeta

if TYPE_CHECKING:
    import discord

log = logging.getLogger("red.vault.events")


class EventMixin(MixinMeta):
    """Passive event listeners for The Vault.

    Future home of:
    - Periodic fled-companion return checks
    - Curse trigger events
    - Passive bonus application
    - Bond level progression on activity
    """

    __slots__: tuple = ()
