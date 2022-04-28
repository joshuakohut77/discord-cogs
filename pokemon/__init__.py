from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Pokemon

import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'models'))

for p in sys.path:
    print(p)


def setup(bot: Red):
    bot.add_cog(Pokemon(bot))
