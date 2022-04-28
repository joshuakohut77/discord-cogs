import sys
import os

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Pokemon

sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def setup(bot: Red):
    bot.add_cog(Pokemon(bot))
