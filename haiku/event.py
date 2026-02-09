from __future__ import annotations
from typing import TYPE_CHECKING
import discord

from .abc import MixinMeta

if TYPE_CHECKING:
    import discord

from redbot.core import commands
from .haikuclass import HaikuDetector

class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore commands (messages starting with bot prefix)
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        
        msg: str = message.content
        
        # Skip empty messages or very short messages
        if not msg or len(msg.strip()) < 10:
            return
        
        # Try to detect a haiku
        try:
            haiku_lines = HaikuDetector.detect_haiku(msg)
            
            if haiku_lines:
                # Format the haiku for display
                formatted_haiku = '\n'.join(haiku_lines)
                
                # Create embed
                embed = discord.Embed(
                    title="🍃 Accidental Haiku? 🍃",
                    description=formatted_haiku,
                    color=0x90EE90  # Light green color
                )
                embed.set_footer(text=f"Detected from {message.author.display_name}")
                
                # Reply to the message
                await message.reply(embed=embed, mention_author=False)
                
                # Log to database
                HaikuDetector.insert_haiku(
                    user_id=message.author.id,
                    username=message.author.name,
                    guild_id=message.guild.id if message.guild else None,
                    channel_id=message.channel.id,
                    message_id=message.id,
                    original_text=msg,
                    formatted_haiku=haiku_lines
                )
        except Exception as e:
            # Silently fail to avoid disrupting chat
            print(f"Error detecting haiku: {e}")