from __future__ import annotations
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from redbot.core.bot import Red

from .main import Pokemon

from discord_components import DiscordComponents
import discord.ext.commands


def setup(bot: Red):
    if not isinstance(discord.ext.commands.Bot, bot):
        raise 'incorrect bot type'

    DiscordComponents(bot)
    bot.add_cog(Pokemon(bot))
