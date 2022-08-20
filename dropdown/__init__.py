from __future__ import annotations
from typing import TYPE_CHECKING

from discord_components import DiscordComponents, Select, SelectOption, Button,ButtonStyle

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Dropdown

def setup(bot: Red):
    bot.add_cog(Dropdown(bot))

    # @bot.event
    # async def on_ready():
    #     DiscordComponents(bot)

