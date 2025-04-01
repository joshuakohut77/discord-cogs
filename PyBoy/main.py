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
from .dbclass import db as dbconn

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
            self.rom_name = rom_name
            # await ctx.send(f"Starting {rom_name}. Use messages like `A`, `B`, `U`, `D`, `L`, `R`, or `S` for inputs. Type `stop_game` to end.")
            await self._game_loop(ctx)
        except Exception as e:
            await ctx.send(f"An error occurred while starting the game: {e}")
            self.running = False
            self.pyboy = None

    async def _game_loop(self, ctx):
        """Main game loop with debugging."""
        # await ctx.send("Starting...")
        message = None
        messageArr = []
        frames_per_update = 12  # Capture a frame every 12 emulator ticks (5 FPS updates)
        ticks_per_second = 60  # Maintain accurate emulation speed
        # Load the saved game state if exists
        try:
            with open(self.state_file, "rb") as state_file:
                self.pyboy.load_state(state_file)
        except Exception as e:
            print(f"No saved state found: {e}")
        
        last_save = time.time() 
        # while self.running and self.pyboy.tick(30):
        while self.running:
            start_time = time.time()
            
            ten_minutes = 10*60
            try:
                self.pyboy.tick()

                if self.pyboy.frame_count % frames_per_update == 0:
                    # Capture the frame
                    screen_image = self.pyboy.screen.image
                    if screen_image is None:
                        # await self.channel.send("Error: Unable to capture screen image.")
                        await ctx.send("Error: Unable to capture screen image.")
                        
                    

                    # Convert to BytesIO
                    img_bytes = BytesIO()
                    try:
                        screen_image.save(img_bytes, format="PNG")
                        img_bytes.seek(0)
                    except Exception as e:
                        # await self.channel.send(f"Error saving image: {e}")
                        await ctx.send(f"Error saving image: {e}")
                        

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
                        
                    
                    elapsed_time = time.time() - start_time

                    if (time.time() - last_save) >= ten_minutes:
                         with open(self.state_file, "wb") as state_file:
                            # save the current state:
                            self.pyboy.save_state(state_file)
                            last_save = time.time()

                            # stop and restart the PyBoy due to some unknown bug where the emulator stops responding to buttons
                            self.pyboy.stop()
                            
                            rom_path = f"/roms/{self.rom_name}.gb"  # Path to ROM
                            self.pyboy = PyBoy(rom_path, window="null")  # Headless mode
                            

                            # Load the saved game state if exists
                            try:
                                with open(self.state_file, "rb") as state_file:
                                    self.pyboy.load_state(state_file)
                            except Exception as e:
                                print(f"No saved state found: {e}")

                    # await asyncio.sleep(0.5)  # Adjust frame rate
                    time.sleep(max(0, 1 / ticks_per_second - elapsed_time))
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
        if str(message.channel.guild.id) != '501142330351550498':
            return
        
        if len(str(message.content)) > 0:
            if str(message.content)[0] == '.' or message.author.id == self.bot.user.id:
                return

        target_letters = {'A', 'B', 'S', 'U', 'D', 'L', 'R'}
        extracted_letters = [char for char in message.content.upper() if char in target_letters]

        if message.attachments:
            for attachment in message.attachments:
                extracted_letters.extend([char for char in attachment.filename.upper() if char in target_letters])


        cmdCount = len(extracted_letters)

        if cmdCount > 55:
            return
        try:
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

                await asyncio.sleep(1)  # Small delay to allow input processing
            userId = message.author.id
            if userId != self.bot.user.id and cmdCount > 0:
                await self.__log_message_data(userId, cmdCount)
            
            if message.channel == self.channel and message.author.id != self.bot.user.id:
                await message.delete()
        except Exception as e:
            # await self.channel.send(f"Unexpected error: {e}")
            ctx = await self.bot.get_context(message)
            await ctx.send(f"Unexpected error: {e}")

    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return

        emoji = reaction.emoji


        target_letters = {'A', 'B', 'S', 'U', 'D', 'L', 'R'}
        
        extracted_letters = []
        if isinstance(emoji, str):
            # Unicode emoji
            
            extracted_letters.extend([char for char in str(emoji).upper() if char in target_letters])
        elif isinstance(emoji, discord.Emoji):
            # Custom emoji
            
            extracted_letters.extend([char for char in str(emoji.name).upper() if char in target_letters])

        cmdCount = len(extracted_letters)

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

            await asyncio.sleep(1)  # Small delay to allow input processing
        userId = user.id
        if userId != self.bot.user.id and cmdCount > 0:
            await self.__log_message_data(userId, cmdCount)


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