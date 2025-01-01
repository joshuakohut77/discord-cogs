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
import time
from dbclass import db as dbconn

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
        ticks_per_second = 60  # Accurate emulation speed
        frame_interval = 1 / ticks_per_second  # Time between ticks
        await ctx.send(str(self.state_file))
        # Load the saved game state if exists
        try:
            with open(self.state_file, "rb") as state_file:
                self.pyboy.load_state(state_file)
        except Exception as e:
            print(f"No saved state found: {e}")

        # while self.running and self.pyboy.tick(30):
        while self.running:
            start_time = time.time()
            try:
                self.pyboy.tick(5)

                if self.pyboy.frame_count % 12 == 0:
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

                        # await asyncio.sleep(1)
                        

                    except Exception as e:
                        # await self.channel.send(f"Error sending file to Discord: {e}")
                        await ctx.send(f"Error sending file to Discord: {e}")
                        break
                    
                    elapsed_time = time.time() - start_time

                    # await asyncio.sleep(0.5)  # Adjust frame rate
                    await asyncio.sleep(max(0, frame_interval - elapsed_time))
            except Exception as e:
                # await self.channel.send(f"Unexpected error: {e}")
                await ctx.send(f"Unexpected error: {e}")
                self.running = False
                break

        # Cleanup
        self.running = False
        if self.pyboy:
            self.pyboy.stop()
            self.pyboy = None
        await ctx.send("Game loop ended.")


    @commands.command()
    async def stop_game(self, ctx):
        """Stop the current game."""
        if not self.running:
            await ctx.send("No game is currently running.")
            return
        
        try:
            # Save state in a file
            with open(self.state_file, "wb") as state_file:
                self.pyboy.save_state(state_file)
                

            # self.pyboy.save_state(self.state_file)
            # await ctx.send("Game Saved!")
        except Exception as e:
            await ctx.send(f"Save error: {e}")
        self.running = False
        self.pyboy.stop()
        self.pyboy = None
        self.channel = None
        await ctx.send("The game has been stopped.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle user inputs."""
        if not self.channel:
            return
        if str(message.channel.guild.id) != '958537357634719804':
            return
        if message.content[0] == '.' or message.author.id == self.bot.user.id:
            return

        target_letters = {'A', 'B', 'S', 'U', 'D', 'L', 'R'}
        extracted_letters = [char for char in message.content.upper() if char in target_letters]

        cmdCount = len(extracted_letters)

        if cmdCount > 25:
            return
        for letter in extracted_letters:
            if letter.upper() == "A":
                self.pyboy.button('a')  # Press the 'A' button
            elif letter.upper() == "B":
                self.pyboy.button('b')
            elif letter.upper() == "S":
                self.pyboy.button('start')
            elif letter.upper() == "U":
                self.pyboy.button('up')
            elif letter.upper() == "D":
                self.pyboy.button('down')
            elif letter.upper() == "L":
                self.pyboy.button('left')
            elif letter.upper() == "R":
                self.pyboy.button('right')

            await asyncio.sleep(10/60)  # Small delay to allow input processing
        userId = message.author.id
        if userId != self.bot.user.id and cmdCount > 0:
            await self.__log_message_data(userId, cmdCount)
        
        if message.channel == self.channel and message.author.id != self.bot.user.id:
            await message.delete()
        


        


    async def __log_message_data(self, userId, cmdCount):
        # log to the database 
        try:
            db = dbconn()
            db.executeWithoutCommit('INSERT INTO "PyBoyStats" ("UserId", "CommandCount") VALUES(%(userId)s, %(cmdCount)s);', { 'userId': userId, 'cmdCount': cmdCount })
            db.commit()
        except:
            db.rollback()
        finally:
            del db
        return