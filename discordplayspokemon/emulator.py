"""Wraps PyBoy in a background thread so the Game Boy runs continuously
without blocking the Discord bot's async event loop."""

import asyncio
import io
import logging
import queue
import threading
import time
from pathlib import Path

from PIL import Image

log = logging.getLogger("red.discordplayspokemon.emulator")

# How many frames to hold a button press (Game Boy runs at ~60 fps)
PRESS_FRAMES = 8
# Small gap between sequential presses so the game registers them individually
GAP_FRAMES = 4
# Target ticks-per-second in the background thread (approx real-time)
TARGET_TPS = 60
# How many idle frames to tick between checking the queue when no inputs
IDLE_FRAMES = 10
# Max inputs to process in a burst before ticking idle frames (prevents starvation)
BURST_LIMIT = 10


class EmulatorManager:
    """Manages a PyBoy instance running in a dedicated daemon thread.

    Communication is handled through thread-safe primitives:
      • input_queue   — button names pushed from the async side
      • _screen_lock  — guards the latest screenshot buffer
      • _stop_event   — signals the thread to shut down
    """

    def __init__(self, rom_path: str, data_path: Path, scale: int = 3):
        self.rom_path = rom_path
        self.data_path = data_path
        self.save_path = data_path / "save_state.state"
        self.scale = scale

        self.pyboy = None
        self.running = False

        # Thread-safe communication
        self.input_queue: queue.Queue[str] = queue.Queue(maxsize=1000)
        self._screen_lock = threading.Lock()
        self._latest_screen: bytes | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        # Stats
        self.total_inputs = 0
        self.total_frames = 0

    # ------------------------------------------------------------------
    # Lifecycle (called from the async side)
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Initialise PyBoy and kick off the background thread."""
        from pyboy import PyBoy

        self.data_path.mkdir(parents=True, exist_ok=True)

        # PyBoy must be created on the thread that will call tick(),
        # but for simplicity we create here and pass to the thread.
        self.pyboy = PyBoy(self.rom_path, window="null")
        self.pyboy.set_emulation_speed(1)  # real-time

        # Restore previous save if present
        if self.save_path.exists():
            try:
                with open(self.save_path, "rb") as f:
                    self.pyboy.load_state(f)
                log.info("Loaded existing save state.")
            except Exception as e:
                log.warning(f"Failed to load save state: {e}")

        self._stop_event.clear()
        self.running = True
        self._thread = threading.Thread(
            target=self._run, name="pyboy-emu", daemon=True
        )
        self._thread.start()
        log.info("Emulator thread started.")

    async def stop(self) -> None:
        """Save state and shut down the emulator thread."""
        if not self.running:
            return
        self._stop_event.set()
        self.running = False
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        if self.pyboy:
            self._save_state_sync()
            self.pyboy.stop()
            self.pyboy = None
        log.info("Emulator stopped and state saved.")

    async def save_state(self) -> None:
        """Trigger a save from the async side."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._save_state_sync)

    async def queue_input(self, button: str) -> None:
        """Queue a button press (non-blocking, drops if full)."""
        try:
            self.input_queue.put_nowait(button)
        except queue.Full:
            pass  # drop excess inputs gracefully

    async def get_screenshot(self) -> io.BytesIO | None:
        """Return the most recent screenshot as a PNG BytesIO."""
        with self._screen_lock:
            data = self._latest_screen
        if data is None:
            return None
        buf = io.BytesIO(data)
        buf.seek(0)
        return buf

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Emulator main loop — runs in its own thread.

        When inputs are queued, they are processed in bursts (up to
        BURST_LIMIT) with no artificial sleep between them so the game
        catches up quickly.  When the queue is empty the loop ticks
        IDLE_FRAMES at real-time pacing to keep the game alive without
        burning CPU.
        """
        frame_time = 1.0 / TARGET_TPS
        frames_since_screenshot = 0
        frames_since_save = 0
        screenshot_every = TARGET_TPS  # update screenshot buffer once/sec

        while not self._stop_event.is_set():
            # --- drain queued inputs in a burst ---
            processed = 0
            while processed < BURST_LIMIT:
                try:
                    button = self.input_queue.get_nowait()
                except queue.Empty:
                    break
                self._press_button(button)
                self.total_inputs += 1
                processed += 1
                # Bookkeeping for periodic tasks
                frames_done = PRESS_FRAMES + GAP_FRAMES
                frames_since_screenshot += frames_done
                frames_since_save += frames_done
                # Screenshot mid-burst if needed
                if frames_since_screenshot >= screenshot_every:
                    self._capture_screen()
                    frames_since_screenshot = 0

            # --- idle ticks (real-time paced) when no inputs ---
            if processed == 0:
                for _ in range(IDLE_FRAMES):
                    if self._stop_event.is_set():
                        break
                    t0 = time.monotonic()
                    self.pyboy.tick()
                    self.total_frames += 1
                    frames_since_screenshot += 1
                    frames_since_save += 1
                    elapsed = time.monotonic() - t0
                    sleep_for = frame_time - elapsed
                    if sleep_for > 0:
                        time.sleep(sleep_for)

            # --- periodic screenshot ---
            if frames_since_screenshot >= screenshot_every:
                self._capture_screen()
                frames_since_screenshot = 0

            # --- periodic auto-save (every ~5 min) ---
            if frames_since_save >= TARGET_TPS * 300:
                self._save_state_sync()
                frames_since_save = 0

    def _press_button(self, button: str) -> None:
        """Hold a button for PRESS_FRAMES then release, with a gap."""
        self.pyboy.button_press(button)
        for _ in range(PRESS_FRAMES):
            self.pyboy.tick()
            self.total_frames += 1
        self.pyboy.button_release(button)
        for _ in range(GAP_FRAMES):
            self.pyboy.tick()
            self.total_frames += 1

    def _capture_screen(self) -> None:
        """Grab the current screen and store as PNG bytes."""
        try:
            img: Image.Image = self.pyboy.screen.image
            w, h = img.size
            img = img.resize((w * self.scale, h * self.scale), Image.NEAREST)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            with self._screen_lock:
                self._latest_screen = buf.getvalue()
        except Exception as e:
            log.warning(f"Screenshot capture failed: {e}")

    def _save_state_sync(self) -> None:
        """Save emulator state to disk (called from either thread)."""
        if not self.pyboy:
            return
        try:
            self.data_path.mkdir(parents=True, exist_ok=True)
            with open(self.save_path, "wb") as f:
                self.pyboy.save_state(f)
            log.info("Save state written.")
        except Exception as e:
            log.error(f"Failed to write save state: {e}")