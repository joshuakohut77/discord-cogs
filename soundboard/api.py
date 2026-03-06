"""
HTTP API server for receiving soundboard commands from the web app.
Runs on port 8765 inside the bot container.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from aiohttp import web

if TYPE_CHECKING:
    from .main import Soundboard

log = logging.getLogger("red.soundboard.api")


class SoundboardAPI:
    """Lightweight HTTP server that accepts play/stop requests from the web soundboard."""

    def __init__(self, cog: Soundboard, host: str = "0.0.0.0", port: int = 8765):
        self.cog = cog
        self.host = host
        self.port = port
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

    # ── routes ───────────────────────────────────────────────────────────

    async def _handle_play(self, request: web.Request) -> web.Response:
        """Handle POST /play  — expects JSON: {"sound": "path/to/file.mp3", "volume": 100}"""
        # Verify API key if configured
        if not self._check_auth(request):
            return web.json_response({"error": "Unauthorized"}, status=401)

        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        sound = data.get("sound")
        volume = data.get("volume", 100)

        if not sound:
            return web.json_response({"error": "Missing 'sound' field"}, status=400)

        log.info(f"[API] Play request: {sound} (volume={volume})")

        # Delegate to the cog's playback logic
        try:
            result = await self.cog.play_sound(sound, volume)
        except Exception as e:
            log.error(f"[API] Unhandled error in play_sound: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)

        if result.get("error"):
            log.warning(f"[API] Play error: {result['error']}")
            status = result.get("status", 500)
            return web.json_response({"error": result["error"]}, status=status)

        return web.json_response({"success": True, "sound": sound})

    async def _handle_stop(self, request: web.Request) -> web.Response:
        """Handle POST /stop  — stops current playback."""
        if not self._check_auth(request):
            return web.json_response({"error": "Unauthorized"}, status=401)

        log.info("[API] Stop request")
        result = await self.cog.stop_sound()

        if result.get("error"):
            return web.json_response({"error": result["error"]}, status=result.get("status", 500))

        return web.json_response({"success": True})

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle GET /health  — simple health check."""
        vc = self.cog.current_vc
        return web.json_response({
            "status": "ok",
            "in_voice": vc is not None and vc.is_connected(),
        })

    # ── auth ─────────────────────────────────────────────────────────────

    def _check_auth(self, request: web.Request) -> bool:
        """Check the X-API-Key header against the configured secret."""
        secret = self.cog.api_secret
        if not secret:
            return True  # No secret configured — allow all
        return request.headers.get("X-API-Key") == secret

    # ── lifecycle ────────────────────────────────────────────────────────

    async def start(self) -> None:
        self.app = web.Application()
        self.app.router.add_post("/play", self._handle_play)
        self.app.router.add_post("/stop", self._handle_stop)
        self.app.router.add_get("/health", self._handle_health)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        log.info(f"[API] Soundboard API listening on {self.host}:{self.port}")

    async def stop(self) -> None:
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        log.info("[API] Soundboard API shut down")