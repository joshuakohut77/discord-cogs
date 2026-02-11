"""
Finale Audio Manager — handles voice channel connection and audio playback
during the cinematic finale sequence.

Audio files are stored in: sprites/finale/audio/
Supports: .mp3, .wav, .ogg, .flac

Usage in scenes:
    DialogScene(..., audio="battle_theme.mp3", audio_loop=True)
    TransitionScene(..., audio="dramatic_sting.wav")
    DialogScene(..., audio="stop")  # explicitly stop audio
    DialogScene(...)  # no audio field = keep current audio playing
"""
from __future__ import annotations
import asyncio
import os
from typing import Optional, TYPE_CHECKING

import discord

if TYPE_CHECKING:
    pass


class FinaleAudioManager:
    """Manages voice channel connection and audio playback for the finale."""

    def __init__(self):
        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._audio_dir = os.path.join(self._base_dir, 'sprites', 'finale', 'audio')

        self.voice_client: Optional[discord.VoiceClient] = None
        self.current_track: Optional[str] = None
        self.is_looping: bool = False
        self._connected: bool = False
        self._volume: float = 0.5  # 0.0 to 1.0
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    async def connect(self, member: discord.Member) -> bool:
        """
        Connect to the voice channel the member is currently in.
        Returns True if connected successfully, False otherwise.
        """
        # Capture the event loop for use in threaded callbacks later
        self._event_loop = asyncio.get_running_loop()

        if not member.voice or not member.voice.channel:
            print("[FinaleAudio] Member is not in a voice channel.")
            return False

        channel = member.voice.channel
        guild = member.guild

        # Already connected to the right channel
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel.id == channel.id:
                self._connected = True
                return True
            # Connected to wrong channel — move
            try:
                await self.voice_client.move_to(channel)
                self._connected = True
                return True
            except Exception as e:
                print(f"[FinaleAudio] Failed to move to channel: {e}")
                await self.disconnect()

        # Check if bot already has a voice client in this guild (e.g. from Audio cog)
        existing_vc = guild.voice_client
        if existing_vc:
            print("[FinaleAudio] Bot already has a voice connection in this guild "
                  "(likely from the Audio cog). Finale audio disabled.")
            return False

        try:
            self.voice_client = await channel.connect(timeout=10.0, reconnect=True)
            self._connected = True
            return True
        except Exception as e:
            print(f"[FinaleAudio] Failed to connect to voice channel: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Stop playback and disconnect from voice."""
        await self.async_stop()
        if self.voice_client:
            try:
                if self.voice_client.is_connected():
                    await self.voice_client.disconnect(force=True)
            except Exception as e:
                print(f"[FinaleAudio] Error disconnecting: {e}")
            self.voice_client = None
        self._connected = False
        self.current_track = None
        self.is_looping = False

    @property
    def connected(self) -> bool:
        return self._connected and self.voice_client is not None and self.voice_client.is_connected()

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _get_audio_path(self, filename: str) -> Optional[str]:
        """Resolve an audio filename to its full path."""
        path = os.path.join(self._audio_dir, filename)
        if os.path.isfile(path):
            return path
        print(f"[FinaleAudio] Audio file not found: {path}")
        return None

    def _create_source(self, filepath: str) -> discord.PCMVolumeTransformer:
        """Create an FFmpeg audio source with volume control."""
        source = discord.FFmpegPCMAudio(
            filepath,
            options="-loglevel warning"
        )
        return discord.PCMVolumeTransformer(source, volume=self._volume)

    async def async_play(self, filename: str, loop: bool = False):
        """
        Play an audio file. If something is already playing, it stops first
        and waits for the ffmpeg process to terminate cleanly.

        Args:
            filename: Audio file in sprites/finale/audio/
            loop: Whether to loop the track when it finishes
        """
        if not self.connected:
            return

        filepath = self._get_audio_path(filename)
        if not filepath:
            return

        # Stop current playback and wait for ffmpeg to terminate cleanly
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.is_looping = False  # prevent loop callback from re-triggering
            self.voice_client.stop()
            # Give ffmpeg time to terminate via SIGTERM instead of SIGKILL
            await asyncio.sleep(0.15)

        self.current_track = filename
        self.is_looping = loop

        def after_callback(error):
            if error:
                print(f"[FinaleAudio] Playback error: {error}")
                return
            # If looping and still connected, schedule replay on the event loop
            if self.is_looping and self.connected and self.current_track == filename:
                if self._event_loop and not self._event_loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        self._loop_replay(filepath, filename), self._event_loop
                    )

        try:
            source = self._create_source(filepath)
            self.voice_client.play(source, after=after_callback)
        except Exception as e:
            print(f"[FinaleAudio] Play error: {e}")

    async def _loop_replay(self, filepath: str, filename: str):
        """Replay a track for looping. Runs on the event loop (not the thread)."""
        # Small delay to let the previous ffmpeg process finish cleanly
        await asyncio.sleep(0.1)
        if not self.is_looping or not self.connected or self.current_track != filename:
            return
        try:
            source = self._create_source(filepath)
            self.voice_client.play(source, after=lambda e: self._on_loop_after(e, filepath, filename))
        except Exception as e:
            print(f"[FinaleAudio] Loop replay error: {e}")

    def _on_loop_after(self, error, filepath: str, filename: str):
        """After callback for looped tracks."""
        if error:
            print(f"[FinaleAudio] Loop playback error: {error}")
            return
        if self.is_looping and self.connected and self.current_track == filename:
            if self._event_loop and not self._event_loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._loop_replay(filepath, filename), self._event_loop
                )

    async def async_stop(self):
        """Stop current playback and wait for clean ffmpeg shutdown."""
        self.is_looping = False
        self.current_track = None
        if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
            self.voice_client.stop()
            await asyncio.sleep(0.15)

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))
        if (self.voice_client and self.voice_client.source
                and isinstance(self.voice_client.source, discord.PCMVolumeTransformer)):
            self.voice_client.source.volume = self._volume

    # ------------------------------------------------------------------
    # Scene integration
    # ------------------------------------------------------------------

    async def handle_scene_audio(self, audio: Optional[str], audio_loop: bool = False):
        """
        Called when a scene advances. Decides what to do with audio.

        Args:
            audio: The scene's audio field.
                   - None: keep current audio playing (no change)
                   - "stop": stop current audio
                   - "filename.mp3": play this file
            audio_loop: Whether to loop the new track
        """
        if audio is None:
            # No audio directive — keep whatever is playing
            return

        if audio.lower() == "stop":
            await self.async_stop()
            return

        # If it's the same track already playing (and loop status matches), skip
        if audio == self.current_track and self.is_looping == audio_loop:
            return

        await self.async_play(audio, loop=audio_loop)