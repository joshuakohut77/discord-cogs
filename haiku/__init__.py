from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Haiku

async def setup(bot: Red):
    cog = Haiku(bot)
    await bot.add_cog(cog)
    await cog.initialize()