from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from redbot.core import commands
from .abc import MixinMeta
from .alphabeticalclass import AlphabeticalChecker

if TYPE_CHECKING:
    import discord

log = logging.getLogger("red.alphabetical")


class EventMixin(MixinMeta):
    """Event handler for detecting alphabetically ordered messages."""
    
    __slots__: tuple = ()
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Respond to messages with words in alphabetical order."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore empty messages
        if not message.content.strip():
            return
        
        # Check if message meets alphabetical criteria
        try:
            if AlphabeticalChecker.check_message(message.content):
                embed = AlphabeticalChecker.create_embed()
                await message.reply(embed=embed)
        except Exception as e:
            log.error(f"Error checking alphabetical order: {e}")