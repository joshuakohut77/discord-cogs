from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import KeanuReeves


async def setup(bot: Red):
    """Load the KeanuReeves cog."""
    await bot.add_cog(KeanuReeves(bot))