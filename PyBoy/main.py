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
        self.state_file = None # File where the ROM state is saved

    @commands.command()
    async def start_game(self, ctx, rom_name: str):
        """Start a Game Boy game."""
        if self.running:
            await ctx.send("A game is already running. Please stop it first.")
            return

        rom_path = f"/roms/{rom_name}.gb"  # Path to ROM
        sav_path = f"/roms/{rom_name}.sav"  # Path to save file
        if not os.path.exists(rom_path):
            await ctx.send("The specified ROM does not exist.")
            return

        try:
            self.pyboy = PyBoy(rom_path, window="null")  # Headless mode
            self.running = True
            self.channel = ctx.channel
            self.state_file = sav_path
            self.pyboy.tick()
            await ctx.send(f"Starting {rom_name}. Use messages like `A`, `B`, `U`, `D`, `L`, `R`, or `S` for inputs. Type `stop_game` to end.")
            await self._game_loop(ctx)
        except Exception as e:
            await ctx.send(f"An error occurred while starting the game: {e}")
            self.running = False
            self.pyboy = None

    async def _game_loop(self, ctx):
        """Main game loop with debugging."""
        await ctx.send("Starting...")
        message = None
        messageArr = []
        await ctx.send(str(self.state_file))
        # Load the saved game state if exists
        try:
            self.pyboy.load_state(self.state_file)
            print("Game state loaded successfully.")
        except Exception as e:
            print(f"No saved state found: {e}")

        while self.running and self.pyboy.tick(25):
            try:
                # Capture the frame
                screen_image = self.pyboy.screen.image
                if screen_image is None:
                    # await self.channel.send("Error: Unable to capture screen image.")
                    await ctx.send("Error: Unable to capture screen image.")
                    break

                # Convert to BytesIO
                img_bytes = BytesIO()
                try:
                    screen_image.save(img_bytes, format="PNG")
                    img_bytes.seek(0)
                except Exception as e:
                    # await self.channel.send(f"Error saving image: {e}")
                    await ctx.send(f"Error saving image: {e}")
                    break

                # Send image to Discord
                file = discord.File(img_bytes, filename="game_frame.png")
                try:
                    
                    message = await ctx.send(content="Melkor Plays Pokemon", file=file)
                    messageArr.append(message)
                    
                    if len(messageArr)>2:
                        old_message = messageArr.pop(0)
                        await old_message.delete()

                    await asyncio.sleep(1)

                except Exception as e:
                    # await self.channel.send(f"Error sending file to Discord: {e}")
                    await ctx.send(f"Error sending file to Discord: {e}")
                    break

                await asyncio.sleep(0.5)  # Adjust frame rate
            except Exception as e:
                # await self.channel.send(f"Unexpected error: {e}")
                await ctx.send(f"Unexpected error: {e}")
                self.running = False
                break

        # Cleanup
        self.running = False
        if self.pyboy:
            self.pyboy.save_state(self.state_file)
            self.pyboy.stop()
            self.pyboy = None
        # await self.channel.send("Game loop ended.")
        await ctx.send("Game loop ended.")


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
        # if not self.running or message.channel != self.channel:
        #     return

        if message.content.upper() == "A":
            self.pyboy.button('a')  # Press the 'A' button
        elif message.content.upper() == "B":
            self.pyboy.button('b')
        elif message.content.upper() == "S":
            self.pyboy.button('start')
        elif message.content.upper() == "U":
            self.pyboy.button('up')
        elif message.content.upper() == "D":
            self.pyboy.button('down')
        elif message.content.upper() == "L":
            self.pyboy.button('left')
        elif message.content.upper() == "R":
            self.pyboy.button('right')

        await asyncio.sleep(0.1)  # Small delay to allow input processing
