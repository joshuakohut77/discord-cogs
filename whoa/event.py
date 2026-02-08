from __future__ import annotations
from typing import TYPE_CHECKING
import re
import logging

from redbot.core import commands
from .abc import MixinMeta
from .whoaclass import Whoa

if TYPE_CHECKING:
    import discord

log = logging.getLogger("red.keanuReeves")

class EventMixin(MixinMeta):
    """Event handler for detecting 'whoa' in messages."""
    
    __slots__: tuple = ()
    
    # Compile regex patterns once at class level for efficiency
    WHOA_PATTERN = re.compile(r"w+h+o+a+", re.IGNORECASE)
    WOAH_PATTERN = re.compile(r"w+o+a+h+", re.IGNORECASE)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Respond to messages containing 'whoa' or 'woah'."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        msg = message.content.lower()
        
        # Check if message contains whoa/woah patterns
        if not (self.WHOA_PATTERN.search(msg) or self.WOAH_PATTERN.search(msg)):
            return
        
        # Fetch and send whoa clip
        whoa_instance = Whoa()
        try:
            result = whoa_instance.get_whoa()
            if result:
                embed, file = result
                await message.reply(file=file, embed=embed)
            else:
                log.warning("Failed to fetch whoa clip for message")
        except Exception as e:
            log.error(f"Error sending whoa clip: {e}")
        finally:
            whoa_instance.close()