from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

# from .main import Pokemon
from .leaderboard import LeaderboardMixin
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'models'))
sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'services'))

# sys.path.append(os)
# sys.path.append(os.path.join(os.path.dirname(
#     os.path.realpath(__file__)), 'models'))

for p in sys.path:
    print(p)


from .main import Pokemon

async def setup(bot: Red):
    await bot.add_cog(Pokemon(bot))
