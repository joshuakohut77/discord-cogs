from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import PokemonTCG


async def setup(bot: Red):
    cog = PokemonTCG(bot)
    await bot.add_cog(cog)