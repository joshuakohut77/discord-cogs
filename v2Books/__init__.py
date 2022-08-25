from __future__ import annotations
from typing import TYPE_CHECKING

import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

if TYPE_CHECKING:
    from redbot.core import Red

from .main import v2Books

def setup(bot: Red):
    bot.add_cog(v2Books(bot))