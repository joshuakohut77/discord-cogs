from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
# from .duplicatesclass import Duplicates as DupeCls

if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands
from pyboy import PyBoy
from io import BytesIO
import asyncio
import os

# from .event import EventMixin

class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass

class PyBoyCog(commands.Cog):
    """A cog to play Game Boy ROMs via Discord."""

    def __init__(self, bot):
        self.bot = bot
        self.pyboy = None  # Emulator instance
        self.running = False  # Game running state
        self.channel = None  # Channel where the game is active

    @commands.command()
    async def start_game(self, ctx, rom_name: str):
        """Start a Game Boy game."""
        if self.running:
            await ctx.send("A game is already running. Please stop it first.")
            return

        rom_path = f"./roms/{rom_name}.gb"  # Path to ROM
        if not os.path.exists(rom_path):
            await ctx.send("The specified ROM does not exist.")
            return

        try:
            self.pyboy = PyBoy(rom_path, window_type="headless")  # Headless mode
            self.running = True
            self.channel = ctx.channel
            
            await ctx.send(f"Starting {rom_name}. Use messages like `A`, `B`, `U`, `D`, `L`, `R`, or `S` for inputs. Type `stop_game` to end.")
            await self._game_loop(ctx)
        except Exception as e:
            await ctx.send(f"An error occurred while starting the game: {e}")
            self.running = False
            self.pyboy = None

    async def _game_loop(self, ctx):
        """Main game loop."""
        
        while self.running and not self.pyboy.tick():
            try:
                # Capture and send the frame
                screen_image = self.pyboy.screen_image()
                if screen_image is None:
                    ctx.send("Error: PyBoy failed to capture screen image.")
                img_bytes = BytesIO()
                screen_image.save(img_bytes, format="PNG")
                img_bytes.seek(0)

                file = discord.File(img_bytes, filename="game_frame.png")
                await self.channel.send(file=file)
                await asyncio.sleep(0.2)  # Adjust frame rate
            except Exception as e:
                await self.channel.send(f"Error during game loop: {e}")
                self.running = False

        self.running = False
        self.pyboy.stop()
        self.pyboy = None

    @commands.command()
    async def stop_game(self, ctx):
        """Stop the current game."""
        if not self.running:
            await ctx.send("No game is currently running.")
            return

        self.running = False
        self.pyboy.stop()
        self.pyboy = None
        self.channel = None
        await ctx.send("The game has been stopped.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle user inputs."""
        if not self.running or message.channel != self.channel:
            return

        if message.content.upper() == "A":
            self.pyboy.send_input(self.pyboy.PRESS_BUTTON_A)
        elif message.content.upper() == "B":
            self.pyboy.send_input(self.pyboy.PRESS_BUTTON_B)
        elif message.content.upper() == "S":
            self.pyboy.send_input(self.pyboy.PRESS_BUTTON_START)
        elif message.content.upper() == "U":
            self.pyboy.send_input(self.pyboy.PRESS_ARROW_UP)
        elif message.content.upper() == "D":
            self.pyboy.send_input(self.pyboy.PRESS_ARROW_DOWN)
        elif message.content.upper() == "L":
            self.pyboy.send_input(self.pyboy.PRESS_ARROW_LEFT)
        elif message.content.upper() == "R":
            self.pyboy.send_input(self.pyboy.PRESS_ARROW_RIGHT)

        await asyncio.sleep(0.1)  # Small delay to allow input processing
