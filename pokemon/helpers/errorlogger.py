"""
Discord Error Logger — captures Python logging ERROR+ messages
and sends them to a configured Discord channel.
"""
import logging
import asyncio
import traceback
from datetime import datetime, timezone
from typing import Optional

import discord


class DiscordErrorHandler(logging.Handler):
    """Custom logging handler that forwards ERROR+ logs to a Discord channel."""

    def __init__(self, bot, config):
        super().__init__(level=logging.ERROR)
        self.bot = bot
        self.config = config
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None

    def start(self):
        """Start the background consumer task."""
        if self._task is None or self._task.done():
            loop = asyncio.get_event_loop()
            self._task = loop.create_task(self._consumer())

    def stop(self):
        """Stop the background consumer task."""
        if self._task and not self._task.done():
            self._task.cancel()

    def emit(self, record: logging.LogRecord):
        """Called by the logging framework for each log record."""
        try:
            # Format the full log entry
            formatted = self.format(record)
            # Put it in the queue (non-blocking)
            self._queue.put_nowait(formatted)
        except Exception:
            self.handleError(record)

    async def _consumer(self):
        """Background task that drains the queue and sends to Discord."""
        while True:
            try:
                message_text = await self._queue.get()
                await self._send_to_channels(message_text)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Don't let consumer die — just print and continue
                print(f"[ErrorLogger] Consumer error: {e}")
                await asyncio.sleep(2)

    async def _send_to_channels(self, message_text: str):
        """Send error message to all configured guild error channels."""
        for guild in self.bot.guilds:
            try:
                channel_id = await self.config.guild(guild).error_log_channel()
                if not channel_id:
                    continue

                channel = guild.get_channel(channel_id)
                if not channel:
                    continue

                # Truncate if needed (Discord limit is 2000 chars)
                # Use a code block for readability
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                content = f"🔴 **Error** — `{timestamp}`\n```\n{message_text[:1900]}\n```"

                await channel.send(content)
            except Exception as e:
                print(f"[ErrorLogger] Failed to send to guild {guild.id}: {e}")