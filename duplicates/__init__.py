from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Duplicates

async def setup(bot: Red):
    cog = Duplicates(bot)
    await bot.add_cog(cog)
    await cog.initialize()