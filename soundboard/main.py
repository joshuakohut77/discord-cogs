from __future__ import annotations

import asyncio
import json
import logging
import math
import os
from abc import ABCMeta
from typing import Any, Dict, Optional, TYPE_CHECKING

import discord
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
    Auto-joins the bot owner's voice channel.
    """

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.current_vc: Optional[discord.VoiceClient] = None
        self.api_server: Optional[SoundboardAPI] = None

        # Read env vars that mirror the web app's docker-compose
        self.sounds_dir: str = os.environ.get("SOUNDS_DIR", "/app/sounds")
        self.api_secret: str = os.environ.get("API_SECRET", "")
        self.api_port: int = int(os.environ.get("API_PORT", "8765"))
        self.config_file: str = os.environ.get("SOUNDBOARD_CONFIG", "/app/soundboard_config.json")

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
        """Clean up voice and API server."""
        if self.api_server:
            asyncio.create_task(self.api_server.stop())

        if self.current_vc and self.current_vc.is_connected():
            asyncio.create_task(self.current_vc.disconnect(force=True))

    # ── soundboard config helpers ────────────────────────────────────────

    def _load_soundboard_config(self) -> dict:
        """Load the soundboard config.json for normalization settings."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"Could not load soundboard config: {e}")
        return {}

    # ── playback ─────────────────────────────────────────────────────────

    async def play_sound(self, sound: str, volume: int = 100) -> dict:
        """Play a sound file through the current voice connection.

        Args:
            sound: Relative path to the sound file (e.g. "memes/Bruh Sound Effect.mp3")
            volume: Volume percentage 0-100

        Returns:
            dict with "error" key on failure, or empty dict on success.
        """
        if not self.current_vc or not self.current_vc.is_connected():
            return {"error": "Bot is not in a voice channel", "status": 503}

        sound_path = os.path.join(self.sounds_dir, sound)
        if not os.path.isfile(sound_path):
            return {"error": f"Sound file not found: {sound}", "status": 404}

        # Stop anything currently playing
        if self.current_vc.is_playing():
            self.current_vc.stop()

        # Build ffmpeg options
        sb_config = self._load_soundboard_config()
        before_options = "-nostdin"
        after_options = self._build_ffmpeg_filters(sb_config, volume)

        try:
            source = discord.FFmpegPCMAudio(
                sound_path,
                before_options=before_options,
                options=after_options,
            )
            self.current_vc.play(source, after=lambda e: self._playback_done(e))
            log.info(f"[PLAY] Now playing: {sound}")
            return {}
        except Exception as e:
            log.error(f"[PLAY] Error playing {sound}: {e}")
            return {"error": str(e), "status": 500}

    async def stop_sound(self) -> dict:
        """Stop the currently playing sound."""
        if not self.current_vc or not self.current_vc.is_connected():
            return {"error": "Bot is not in a voice channel", "status": 503}

        if self.current_vc.is_playing():
            self.current_vc.stop()

        return {}

    @staticmethod
    def _build_ffmpeg_filters(sb_config: dict, volume: int) -> str:
        """Build the ffmpeg -af filter string based on soundboard config."""
        filters = []

        # Volume adjustment (convert 0-100 percentage to 0.0-1.0 float)
        vol = max(0, min(volume, 100)) / 100.0
        if vol != 1.0:
            filters.append(f"volume={vol:.2f}")

        # Normalization
        normalize = sb_config.get("normalize_audio", True)
        if normalize:
            gain = sb_config.get("normalization_gain", -9)
            # dynaudnorm for real-time normalization
            filters.append("dynaudnorm=f=150:g=15")
            # Apply gain offset
            if gain != 0:
                linear_gain = math.pow(10, gain / 20.0)
                filters.append(f"volume={linear_gain:.4f}")

        if filters:
            return f'-af {",".join(filters)}'
        return ""

    def _playback_done(self, error: Optional[Exception]) -> None:
        if error:
            log.error(f"[PLAY] Playback error: {error}")

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
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect(force=True)

        try:
            self.current_vc = await channel.connect()
            await ctx.send(f"Joined **{channel.name}**.")
        except Exception as e:
            await ctx.send(f"Failed to join: {e}")

    @soundboard.command()
    @commands.is_owner()
    async def leave(self, ctx: commands.Context) -> None:
        """Leave the current voice channel."""
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect(force=True)
            self.current_vc = None
            await ctx.send("Disconnected from voice.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @soundboard.command()
    @commands.is_owner()
    async def status(self, ctx: commands.Context) -> None:
        """Show soundboard status."""
        vc_status = "Not connected"
        if self.current_vc and self.current_vc.is_connected():
            vc_status = f"Connected to **{self.current_vc.channel.name}**"
            if self.current_vc.is_playing():
                vc_status += " (playing)"

        api_status = "Running" if self.api_server and self.api_server.site else "Not running"

        embed = discord.Embed(title="🎵 Soundboard Status", color=0x0066FF)
        embed.add_field(name="Voice", value=vc_status, inline=False)
        embed.add_field(name="API Server", value=f"{api_status} (port {self.api_port})", inline=False)
        embed.add_field(name="Sounds Directory", value=self.sounds_dir, inline=False)

        sb_config = self._load_soundboard_config()
        norm_status = "Enabled" if sb_config.get("normalize_audio", True) else "Disabled"
        embed.add_field(name="Normalization", value=norm_status, inline=True)
        embed.add_field(name="Gain", value=f"{sb_config.get('normalization_gain', -9)} dB", inline=True)

        await ctx.send(embed=embed)

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
