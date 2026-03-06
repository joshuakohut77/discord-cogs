from __future__ import annotations

import asyncio
import json
import logging
import math
import os
from abc import ABCMeta
from typing import Optional, TYPE_CHECKING

import discord
import lavalink
from redbot.core import Config, commands

from .api import SoundboardAPI
from .event import EventMixin

if TYPE_CHECKING:
    from redbot.core.bot import Red

log = logging.getLogger("red.soundboard")


class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class Soundboard(EventMixin, commands.Cog, metaclass=CompositeClass):
    """Web-controlled soundboard for Discord voice channels.

    Runs an HTTP API that the web soundboard sends play/stop commands to.
    Auto-joins the bot owner's voice channel and plays sounds via Lavalink.
    """

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.api_server: Optional[SoundboardAPI] = None

        # Config env vars
        self.sounds_dir: str = os.environ.get("SOUNDS_DIR", "/sounds")
        self.api_secret: str = os.environ.get("API_SECRET", "")
        self.api_port: int = int(os.environ.get("API_PORT", "8765"))
        self.config_file: str = os.environ.get(
            "SOUNDBOARD_CONFIG", "/soundboard_config/config.json"
        )

        # The lavalink path to the sounds dir (as seen by the lavalink container)
        # This may differ from self.sounds_dir if lavalink mounts it differently
        self.lavalink_sounds_dir: str = os.environ.get(
            "LAVALINK_SOUNDS_DIR", "/sounds"
        )

        self.config = Config.get_conf(self, identifier=7364827591, force_registration=True)

        default_guild = {
            "enabled": True,
            "auto_leave": True,
        }
        self.config.register_guild(**default_guild)

    # ── lifecycle ────────────────────────────────────────────────────────

    async def start_api(self) -> None:
        """Start the HTTP API server. Called from __init__.py setup."""
        self.api_server = SoundboardAPI(self, port=self.api_port)
        await self.api_server.start()

    def cog_unload(self) -> None:
        """Clean up API server."""
        if self.api_server:
            asyncio.create_task(self.api_server.stop())

    # ── helpers ──────────────────────────────────────────────────────────

    def _get_player(self, guild_id: int) -> Optional[lavalink.Player]:
        """Get the lavalink player for a guild, if one exists."""
        try:
            return lavalink.get_player(guild_id)
        except Exception:
            return None

    def _load_soundboard_config(self) -> dict:
        """Load the soundboard config.json for normalization settings."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"Could not load soundboard config: {e}")
        return {}

    def _get_voice_guild(self) -> Optional[discord.Guild]:
        """Find the guild where the bot is currently in voice."""
        for guild in self.bot.guilds:
            if guild.voice_client:
                return guild
        return None

    # ── playback ─────────────────────────────────────────────────────────

    async def play_sound(self, sound: str, volume: int = 100) -> dict:
        """Play a sound file through Lavalink in the current voice channel.

        Args:
            sound: Relative path to the sound file (e.g. "memes/Bruh Sound Effect.mp3")
            volume: Volume percentage 0-100

        Returns:
            dict with "error" key on failure, or empty dict on success.
        """
        # Find which guild we're connected to voice in
        guild = self._get_voice_guild()
        if not guild:
            log.warning("[PLAY] No voice guild found")
            return {"error": "Bot is not in a voice channel", "status": 503}

        log.info(f"[PLAY] Found voice guild: {guild.name} ({guild.id})")

        player = self._get_player(guild.id)
        if not player:
            log.warning(f"[PLAY] No lavalink player for guild {guild.id}")
            return {"error": "No Lavalink player for this guild", "status": 503}

        log.info(f"[PLAY] Got player. Connected: {player.connected}, Channel: {player.channel}")

        # Verify the file exists on the bot's filesystem
        sound_path = os.path.join(self.sounds_dir, sound)
        log.info(f"[PLAY] Checking file at bot path: {sound_path}")
        if not os.path.isfile(sound_path):
            log.warning(f"[PLAY] File not found at: {sound_path}")
            return {"error": f"Sound file not found: {sound}", "status": 404}

        # Build the lavalink local file identifier
        # Lavalink needs the absolute path as seen from the lavalink container
        lavalink_path = os.path.join(self.lavalink_sounds_dir, sound)
        log.info(f"[PLAY] Lavalink path: {lavalink_path}")

        try:
            # Load the track through lavalink
            log.info(f"[PLAY] Loading track via lavalink...")
            result = await player.load_tracks(lavalink_path)
            log.info(f"[PLAY] Load result: type={result.load_type}, tracks={len(result.tracks)}")

            if not result.tracks:
                return {"error": f"Lavalink could not load: {sound} (load_type={result.load_type})", "status": 500}

            track = result.tracks[0]
            log.info(f"[PLAY] Track loaded: {track.title}")

            # Set volume (lavalink uses 0-150 scale, we map 0-100 input)
            # Also apply any normalization gain from config
            sb_config = self._load_soundboard_config()
            effective_volume = self._calculate_volume(volume, sb_config)
            await player.set_volume(effective_volume)
            log.info(f"[PLAY] Volume set to {effective_volume}")

            # Stop current playback and play the new sound
            player.store("soundboard_playing", True)
            if player.is_playing:
                await player.stop()
            player.queue.clear()
            player.add(player.channel.guild.me, track)
            await player.play()

            log.info(f"[PLAY] Now playing: {sound} (vol={effective_volume})")
            return {}

        except Exception as e:
            log.error(f"[PLAY] Error playing {sound}: {e}")
            return {"error": str(e), "status": 500}

    async def stop_sound(self) -> dict:
        """Stop the currently playing sound."""
        guild = self._get_voice_guild()
        if not guild:
            return {"error": "Bot is not in a voice channel", "status": 503}

        player = self._get_player(guild.id)
        if not player:
            return {"error": "No Lavalink player for this guild", "status": 503}

        player.queue.clear()
        await player.stop()
        player.store("soundboard_playing", False)

        return {}

    @staticmethod
    def _calculate_volume(volume: int, sb_config: dict) -> int:
        """Calculate effective lavalink volume (0-150) from user volume and config gain."""
        # Start with user volume as a fraction
        vol_fraction = max(0, min(volume, 100)) / 100.0

        # Apply normalization gain if enabled
        normalize = sb_config.get("normalize_audio", True)
        if normalize:
            gain_db = sb_config.get("normalization_gain", -9)
            if gain_db != 0:
                linear_gain = math.pow(10, gain_db / 20.0)
                vol_fraction *= linear_gain

        # Lavalink volume is 0-150 (100 = normal)
        lavalink_vol = int(vol_fraction * 100)
        return max(0, min(lavalink_vol, 150))

    # ── voice connection ─────────────────────────────────────────────────

    async def connect_to_channel(self, channel: discord.VoiceChannel) -> Optional[lavalink.Player]:
        """Connect to a voice channel using lavalink."""
        try:
            player = await lavalink.connect(channel)
            log.info(f"[VOICE] Connected to: {channel.name} in {channel.guild.name}")
            return player
        except Exception as e:
            log.error(f"[VOICE] Failed to connect to {channel.name}: {e}")
            return None

    async def disconnect_from_guild(self, guild: discord.Guild) -> None:
        """Disconnect from voice in a guild."""
        try:
            player = self._get_player(guild.id)
            if player:
                player.queue.clear()
                await player.stop()
                await player.disconnect()
            elif guild.voice_client:
                await guild.voice_client.disconnect(force=True)
            log.info(f"[VOICE] Disconnected from voice in {guild.name}")
        except Exception as e:
            log.error(f"[VOICE] Error disconnecting in {guild.name}: {e}")

    # ── commands ──────────────────────────────────────────────────────────

    @commands.group()
    @commands.guild_only()
    async def soundboard(self, ctx: commands.Context) -> None:
        """Soundboard control commands."""
        pass

    @soundboard.command()
    @commands.is_owner()
    async def join(self, ctx: commands.Context) -> None:
        """Join your current voice channel."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel first.")
            return

        channel = ctx.author.voice.channel

        # Disconnect existing connection in this guild
        await self.disconnect_from_guild(ctx.guild)

        player = await self.connect_to_channel(channel)
        if player:
            await ctx.send(f"Joined **{channel.name}**.")
        else:
            await ctx.send("Failed to join the voice channel.")

    @soundboard.command()
    @commands.is_owner()
    async def leave(self, ctx: commands.Context) -> None:
        """Leave the current voice channel."""
        player = self._get_player(ctx.guild.id)
        if player:
            await self.disconnect_from_guild(ctx.guild)
            await ctx.send("Disconnected from voice.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @soundboard.command()
    @commands.is_owner()
    async def status(self, ctx: commands.Context) -> None:
        """Show soundboard status."""
        player = self._get_player(ctx.guild.id)

        vc_status = "Not connected"
        if player and player.channel:
            channel = ctx.guild.get_channel(player.channel.id)
            channel_name = channel.name if channel else "Unknown"
            vc_status = f"Connected to **{channel_name}**"
            if player.is_playing:
                vc_status += " (playing)"

        api_status = "Running" if self.api_server and self.api_server.site else "Not running"

        embed = discord.Embed(title="🎵 Soundboard Status", color=0x0066FF)
        embed.add_field(name="Voice", value=vc_status, inline=False)
        embed.add_field(name="API Server", value=f"{api_status} (port {self.api_port})", inline=False)
        embed.add_field(name="Sounds Dir (bot)", value=self.sounds_dir, inline=False)
        embed.add_field(name="Sounds Dir (lavalink)", value=self.lavalink_sounds_dir, inline=False)

        sb_config = self._load_soundboard_config()
        norm_status = "Enabled" if sb_config.get("normalize_audio", True) else "Disabled"
        embed.add_field(name="Normalization", value=norm_status, inline=True)
        embed.add_field(name="Gain", value=f"{sb_config.get('normalization_gain', -9)} dB", inline=True)

        await ctx.send(embed=embed)

    @soundboard.command()
    @commands.is_owner()
    async def test(self, ctx: commands.Context, *, sound: str) -> None:
        """Test playing a sound by relative path.

        Example: [p]soundboard test memes/Bruh Sound Effect.mp3
        """
        result = await self.play_sound(sound, volume=100)
        if result.get("error"):
            await ctx.send(f"Error: {result['error']}")
        else:
            await ctx.send(f"Playing: **{sound}**")

    @soundboard.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def toggle(self, ctx: commands.Context) -> None:
        """Toggle auto-join for this server."""
        current = await self.config.guild(ctx.guild).enabled()
        await self.config.guild(ctx.guild).enabled.set(not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Soundboard auto-join has been **{status}** for this server.")

    @soundboard.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def autoleave(self, ctx: commands.Context) -> None:
        """Toggle auto-leave when owner disconnects from voice."""
        current = await self.config.guild(ctx.guild).auto_leave()
        await self.config.guild(ctx.guild).auto_leave.set(not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Soundboard auto-leave has been **{status}** for this server.")