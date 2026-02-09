from __future__ import annotations
from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from redbot.core.bot import Red
    from redbot.core import Config
    from .database import DankDatabase

import discord
from redbot.core import commands

from .abc import MixinMeta


class EventMixin(MixinMeta):
    """Handles Discord events for the Dank Hall cog."""
    
    __slots__: tuple = ()

from __future__ import annotations
from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from redbot.core.bot import Red
    from redbot.core import Config
    from .database import DankDatabase

import discord
from redbot.core import commands

from .abc import MixinMeta


class EventMixin(MixinMeta):
    """Handles Discord events for the Dank Hall cog."""
    
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
        Listen for reactions and certify messages when they hit the threshold.
        Also updates reaction counts for already certified messages.
        """
        # Ignore DMs
        if not payload.guild_id:
            return
        
        # Get guild and check if system is enabled
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        guild_config = await self.config.guild(guild).all()
        if not guild_config["enabled"]:
            return
        
        # Get channel and message
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        
        # Check if channel is blacklisted
        if channel.id in guild_config["blacklisted_channels"]:
            return
        
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden):
            return
        
        # Don't certify bot messages
        if message.author.bot:
            return
        
        # Get the emoji that was added
        emoji = payload.emoji
        
        # Determine emoji ID for comparison
        if emoji.is_custom_emoji():
            emoji_id = str(emoji.id)
            emoji_str = str(emoji)
        else:
            emoji_id = emoji.name
            emoji_str = emoji.name
        
        # Check if emoji is allowed (if allow list is configured)
        allowed_emojis = guild_config["allowed_emojis"]
        if allowed_emojis and emoji_id not in allowed_emojis:
            return
        
        # Find the matching reaction on the message
        matching_reaction = None
        for reaction in message.reactions:
            if emoji.is_custom_emoji():
                # Compare custom emoji IDs
                if hasattr(reaction.emoji, 'id') and reaction.emoji.id == emoji.id:
                    matching_reaction = reaction
                    break
            else:
                # Compare unicode emoji
                if reaction.emoji == emoji.name:
                    matching_reaction = reaction
                    break
        
        if not matching_reaction:
            return
        
        # Check if already certified
        is_certified = await self.db.is_certified(message.id)
        
        if is_certified:
            # Message is already certified, update the count and edit the hall embed
            cert_data = await self.db.get_certified_message(message.id)
            
            if cert_data and matching_reaction.count > cert_data["reaction_count"]:
                # Update database
                await self.db.update_reaction_count(message.id, matching_reaction.count)
                
                # Update the hall embed
                hall_message_id = cert_data["hall_message_id"]
                hall_channel_id = await self._get_hall_channel(channel)
                
                if hall_channel_id and hall_message_id:
                    hall_channel = guild.get_channel(hall_channel_id)
                    if hall_channel:
                        try:
                            hall_message = await hall_channel.fetch_message(hall_message_id)
                            
                            # Get the existing embed and update the Reactions field
                            if hall_message.embeds:
                                embed = hall_message.embeds[0]
                                
                                # Find and update the Reactions field
                                for i, field in enumerate(embed.fields):
                                    if field.name == "Reactions":
                                        embed.set_field_at(
                                            i,
                                            name="Reactions",
                                            value=str(matching_reaction.count),
                                            inline=True
                                        )
                                        break
                                
                                await hall_message.edit(embed=embed)
                        except (discord.NotFound, discord.Forbidden):
                            pass  # Hall message deleted or no permission
            
            return
        
        # Check if threshold is met for new certification
        threshold = await self._get_threshold(channel)
        if matching_reaction.count < threshold:
            return
        
        # Get hall of fame channel
        hall_channel_id = await self._get_hall_channel(channel)
        if not hall_channel_id:
            return
        
        hall_channel = guild.get_channel(hall_channel_id)
        if not hall_channel:
            return
        
        # Check permissions
        permissions = hall_channel.permissions_for(guild.me)
        if not permissions.send_messages or not permissions.embed_links:
            return
        
        # === CERTIFICATION TIME ===
        
        # Send random response to original message
        responses = guild_config["responses"]
        if responses:
            response = random.choice(responses)
            try:
                await message.reply(response, mention_author=False)
            except:
                pass  # Don't fail if we can't reply
        
        # Create and send hall embed
        embed = await self._create_hall_embed(message, emoji_str, matching_reaction.count)
        hall_msg = await self._send_hall_message(hall_channel, message, embed)
        
        if hall_msg:
            # Record in database
            await self.db.add_certified_message(
                message_id=message.id,
                guild_id=guild.id,
                channel_id=channel.id,
                user_id=message.author.id,
                emoji=emoji_id,
                hall_message_id=hall_msg.id,
                reaction_count=matching_reaction.count,
                hall_channel_id=hall_channel.id
            )