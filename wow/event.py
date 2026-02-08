from __future__ import annotations
from typing import TYPE_CHECKING
import re
import logging

from redbot.core import commands
from .abc import MixinMeta
from .wowclass import Wow

if TYPE_CHECKING:
    import discord

log = logging.getLogger("red.owenWilson")

class EventMixin(MixinMeta):
    """Event handler for detecting 'wow' in messages."""
    
    __slots__: tuple = ()
    
    # Compile regex pattern once at class level for efficiency
    WOW_PATTERN = re.compile(r"w+o+w+", re.IGNORECASE)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Respond to messages containing 'wow'."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        msg = message.content.lower()
        
        # Check if message contains wow pattern
        if not self.WOW_PATTERN.search(msg):
            return
        
        # Fetch and send wow clip
        wow_instance = Wow()
        try:
            result = wow_instance.get_wow()
            if result:
                embed, file = result
                await message.reply(file=file, embed=embed)
            else:
                log.warning("Failed to fetch wow clip for message")
        except Exception as e:
            log.error(f"Error sending wow clip: {e}")
        finally:
            wow_instance.close()