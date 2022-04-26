from __future__ import annotations
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Pokemon


def setup(bot: Red):
    bot.add_cog(Pokemon(bot))
