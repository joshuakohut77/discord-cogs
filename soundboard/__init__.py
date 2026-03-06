from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Soundboard


async def setup(bot: Red):
    cog = Soundboard(bot)
    await bot.add_cog(cog)
    await cog.start_api()
