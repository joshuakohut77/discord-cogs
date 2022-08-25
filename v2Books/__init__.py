from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core import Red

from .main import v2Books

def setup(bot: Red):
    bot.add_cog(v2Books(bot))