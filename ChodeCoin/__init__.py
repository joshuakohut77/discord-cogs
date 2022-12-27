from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red

from ChodeCoin.core.main import ChodeCoin as chode_coin

def setup(bot: Red):
    bot.add_cog(chode_coin(bot))