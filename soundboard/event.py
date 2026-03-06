from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
import lavalink
from redbot.core import commands

from .abc import MixinMeta

if TYPE_CHECKING:
    import discord

log = logging.getLogger("red.soundboard.event")


class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Auto-join voice when the bot owner joins a channel."""
        # Only react to the bot owner
        if not await self.bot.is_owner(member):
            return

        # Owner joined or moved to a voice channel
        if after.channel is not None and (before.channel is None or before.channel != after.channel):
            guild = after.channel.guild

            # Check if cog is enabled for this guild
            enabled = await self.config.guild(guild).enabled()
            if not enabled:
                return

            # If we're already in the target channel, do nothing
            try:
                player = lavalink.get_player(guild.id)
                if player and player.channel and player.channel.id == after.channel.id:
                    return
            except (KeyError, IndexError):
                pass

            # Disconnect any existing voice connection in this guild first
            await self.disconnect_from_guild(guild)

            try:
                player = await lavalink.connect(after.channel)
                log.info(f"[VOICE] Auto-joined: {after.channel.name} in {guild.name}")
            except Exception as e:
                log.error(f"[VOICE] Failed to join {after.channel.name}: {e}")

        # Owner left voice entirely (didn't just move)
        elif after.channel is None and before.channel is not None:
            guild = before.channel.guild

            auto_leave = await self.config.guild(guild).auto_leave()
            if not auto_leave:
                return

            await self.disconnect_from_guild(guild)
            log.info(f"[VOICE] Auto-left voice in {guild.name} (owner disconnected)")
