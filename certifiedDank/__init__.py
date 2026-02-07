from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import DankHall


async def setup(bot: Red):
    cog = DankHall(bot)
    await cog.initialize()
    await bot.add_cog(cog)