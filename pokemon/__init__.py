from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Pokemon
from discord_components import DiscordComponents


def setup(bot: Red):
    DiscordComponents(bot)
    bot.add_cog(Pokemon(bot))
