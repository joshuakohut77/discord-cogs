from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import owenWilson as wow

async def setup(bot: Red):
    await bot.add_cog(wow(bot))
