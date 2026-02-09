"""Discord Plays Pokemon — a Red-DiscordBot cog that lets a Discord server
collectively play a Game Boy game via chat messages.

Game channel messages:  Parsed as intentional button inputs, then deleted.
Other channel messages:  Letters are passively harvested and silently fed
                         into the emulator without deleting the message.
"""

import asyncio
import logging
from datetime import datetime, timedelta

import discord
from redbot.core import commands, Config, checks
from redbot.core.data_manager import cog_data_path

from .emulator import EmulatorManager
from .input_handler import InputHandler

log = logging.getLogger("red.discordplayspokemon")


class DiscordPlaysPokemon(commands.Cog):
    """Community-driven Pokemon gameplay through Discord messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=777000200, force_registration=True)

        default_guild = {
            "channel_id": None,              # channel where the game lives
            "rom_path": None,                # filesystem path to the .gb ROM
            "screenshot_interval": 6,        # seconds between screen updates
            "input_cooldown": 1.0,           # per-user cooldown in seconds
            "max_inputs_per_msg": 5,         # combo cap for game channel
            "max_passive_inputs": 20,        # cap for passive letter harvesting
            "passive_enabled": True,         # server-wide passive harvesting on/off
            "enabled": False,
            "scale_factor": 3,               # screenshot upscale multiplier
            "log_channel_id": None,          # channel for historical screenshot log
            "log_interval_minutes": 60,      # how often to post to the log channel
        }
        self.config.register_guild(**default_guild)

        self.input_handler = InputHandler()

        # Per-guild runtime state
        self._emulators: dict[int, EmulatorManager] = {}
        self._game_loops: dict[int, asyncio.Task] = {}
        self._user_cooldowns: dict[tuple[int, int], datetime] = {}
        # Track the message we edit for the game screen (guild_id → Message)
        self._screen_messages: dict[int, discord.Message] = {}
        # Prevent stacking screenshot edits (guild_id → Lock)
        self._screen_locks: dict[int, asyncio.Lock] = {}
        # Historical log loop tasks (guild_id → Task)
        self._log_loops: dict[int, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Cog lifecycle
    # ------------------------------------------------------------------

    async def cog_load(self):
        """Called when the cog is loaded. Kick off auto-start as a
        background task so we don't block cog loading."""
        self._autostart_task = self.bot.loop.create_task(self._autostart())

    async def _autostart(self):
        """Wait for the bot to be fully ready, then auto-start any guilds
        that were running before a reload/restart."""
        try:
            await self.bot.wait_until_ready()
        except asyncio.CancelledError:
            return

        for guild in self.bot.guilds:
            try:
                enabled = await self.config.guild(guild).enabled()
                if not enabled:
                    continue

                rom_path = await self.config.guild(guild).rom_path()
                channel_id = await self.config.guild(guild).channel_id()
                scale = await self.config.guild(guild).scale_factor()

                if not rom_path or not channel_id:
                    continue

                data_path = cog_data_path(self) / str(guild.id)
                emu = EmulatorManager(rom_path, data_path, scale=scale)
                await emu.start()

                self._emulators[guild.id] = emu
                self._screen_messages.pop(guild.id, None)

                self._game_loops[guild.id] = self.bot.loop.create_task(
                    self._game_loop(guild)
                )
                await self._ensure_log_loop(guild)

                log.info(f"Auto-started emulator for guild {guild.name} ({guild.id})")
            except Exception as e:
                log.error(
                    f"Failed to auto-start for guild {guild.name} ({guild.id}): {e}",
                    exc_info=True,
                )

    def cog_unload(self):
        if hasattr(self, '_autostart_task') and not self._autostart_task.done():
            self._autostart_task.cancel()
        for task in self._game_loops.values():
            task.cancel()
        for task in self._log_loops.values():
            task.cancel()
        for emu in self._emulators.values():
            asyncio.create_task(emu.stop())

    # ------------------------------------------------------------------
    # Admin command group
    # ------------------------------------------------------------------

    @commands.group(name="dpp", invoke_without_command=True)
    @commands.guild_only()
    async def dpp(self, ctx: commands.Context):
        """Discord Plays Pokemon — community-driven Game Boy gameplay."""
        await ctx.send_help(ctx.command)

    @dpp.command(name="setchannel")
    @checks.admin_or_permissions(administrator=True)
    async def set_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where the game will be played."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"Game channel set to {channel.mention}.")

    @dpp.command(name="setrom")
    @checks.admin_or_permissions(administrator=True)
    async def set_rom(self, ctx: commands.Context, *, rom_path: str):
        """Set the filesystem path to the Game Boy ROM file."""
        from pathlib import Path

        if not Path(rom_path).is_file():
            await ctx.send(
                f"⚠️ File not found at `{rom_path}`. "
                "Make sure the path is correct and accessible by the bot process."
            )
            return
        await self.config.guild(ctx.guild).rom_path.set(rom_path)
        await ctx.send(f"ROM path set to `{rom_path}`.")

    @dpp.command(name="setinterval")
    @checks.admin_or_permissions(administrator=True)
    async def set_interval(self, ctx: commands.Context, seconds: int):
        """Set the screenshot update interval (5–30 seconds)."""
        seconds = max(5, min(30, seconds))
        await self.config.guild(ctx.guild).screenshot_interval.set(seconds)
        await ctx.send(f"Screenshot interval set to **{seconds}s**.")

    @dpp.command(name="setcooldown")
    @checks.admin_or_permissions(administrator=True)
    async def set_cooldown(self, ctx: commands.Context, seconds: float):
        """Set the per-user input cooldown (0.5–10 seconds)."""
        seconds = max(0.5, min(10.0, seconds))
        await self.config.guild(ctx.guild).input_cooldown.set(seconds)
        await ctx.send(f"Input cooldown set to **{seconds}s**.")

    @dpp.command(name="setscale")
    @checks.admin_or_permissions(administrator=True)
    async def set_scale(self, ctx: commands.Context, factor: int):
        """Set the screenshot scale factor (1–6)."""
        factor = max(1, min(6, factor))
        await self.config.guild(ctx.guild).scale_factor.set(factor)
        await ctx.send(f"Scale factor set to **{factor}x**.")

    @dpp.command(name="passive")
    @checks.admin_or_permissions(administrator=True)
    async def toggle_passive(self, ctx: commands.Context, on_off: bool = None):
        """Toggle or set passive server-wide input harvesting.

        `[p]dpp passive`       — toggle
        `[p]dpp passive true`  — enable
        `[p]dpp passive false` — disable
        """
        current = await self.config.guild(ctx.guild).passive_enabled()
        new_val = (not current) if on_off is None else on_off
        await self.config.guild(ctx.guild).passive_enabled.set(new_val)
        state = "enabled" if new_val else "disabled"
        await ctx.send(f"Passive input harvesting **{state}**.")

    @dpp.command(name="setlogchannel")
    @checks.admin_or_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set a channel for historical screenshot logs.

        The bot will post a new screenshot at a set interval (see setloginterval)
        so you have a scrollable timeline of game progress.
        Use `[p]dpp clearlogchannel` to disable.
        """
        await self.config.guild(ctx.guild).log_channel_id.set(channel.id)
        interval = await self.config.guild(ctx.guild).log_interval_minutes()
        await ctx.send(
            f"Log channel set to {channel.mention}. "
            f"A screenshot will be posted every **{interval} minute(s)** while the game is running."
        )
        # If the game is already running, start the log loop immediately
        await self._ensure_log_loop(ctx.guild)

    @dpp.command(name="clearlogchannel")
    @checks.admin_or_permissions(administrator=True)
    async def clear_log_channel(self, ctx: commands.Context):
        """Disable the historical screenshot log."""
        await self.config.guild(ctx.guild).log_channel_id.set(None)
        task = self._log_loops.pop(ctx.guild.id, None)
        if task:
            task.cancel()
        await ctx.send("Log channel cleared. Historical logging disabled.")

    @dpp.command(name="setloginterval")
    @checks.admin_or_permissions(administrator=True)
    async def set_log_interval(self, ctx: commands.Context, minutes: int):
        """Set how often (in minutes) a screenshot is posted to the log channel (1–1440)."""
        minutes = max(1, min(1440, minutes))
        await self.config.guild(ctx.guild).log_interval_minutes.set(minutes)
        await ctx.send(f"Log interval set to **{minutes} minute(s)**.")
        # Restart the log loop so it picks up the new interval
        await self._ensure_log_loop(ctx.guild)

    # ------------------------------------------------------------------
    # Game control
    # ------------------------------------------------------------------

    @dpp.command(name="start")
    @checks.admin_or_permissions(administrator=True)
    async def start_game(self, ctx: commands.Context):
        """Start the emulator and begin accepting inputs."""
        guild = ctx.guild

        if guild.id in self._emulators and self._emulators[guild.id].running:
            await ctx.send("The game is already running!")
            return

        rom_path = await self.config.guild(guild).rom_path()
        channel_id = await self.config.guild(guild).channel_id()
        scale = await self.config.guild(guild).scale_factor()

        if not rom_path:
            await ctx.send("No ROM path configured. Use `[p]dpp setrom <path>` first.")
            return
        if not channel_id:
            await ctx.send("No game channel configured. Use `[p]dpp setchannel #channel` first.")
            return

        data_path = cog_data_path(self) / str(guild.id)
        emu = EmulatorManager(rom_path, data_path, scale=scale)

        status_msg = await ctx.send("Starting emulator...")
        try:
            await emu.start()
        except Exception as e:
            await status_msg.edit(content=f"Failed to start emulator:\n```{e}```")
            log.error(f"Emulator start failed for guild {guild.id}", exc_info=True)
            return

        self._emulators[guild.id] = emu
        await self.config.guild(guild).enabled.set(True)

        # Clear any stale screen message reference
        self._screen_messages.pop(guild.id, None)

        self._game_loops[guild.id] = self.bot.loop.create_task(
            self._game_loop(guild)
        )

        # Start log loop if a log channel is configured
        await self._ensure_log_loop(guild)

        channel = guild.get_channel(channel_id)
        await status_msg.edit(content="🎮 **Game started!** Send inputs in " +
                              (channel.mention if channel else "the game channel") + ".")

    @dpp.command(name="stop")
    @checks.admin_or_permissions(administrator=True)
    async def stop_game(self, ctx: commands.Context):
        """Stop the game, save state, and shut down the emulator."""
        guild = ctx.guild

        if guild.id not in self._emulators:
            await ctx.send("No game is currently running.")
            return

        if guild.id in self._game_loops:
            self._game_loops.pop(guild.id).cancel()
        task = self._log_loops.pop(guild.id, None)
        if task:
            task.cancel()
        emu = self._emulators.pop(guild.id, None)
        if emu:
            await emu.stop()
        self._screen_messages.pop(guild.id, None)
        await self.config.guild(guild).enabled.set(False)
        await ctx.send("Game stopped and state saved. ✅")

    @dpp.command(name="save")
    @checks.admin_or_permissions(administrator=True)
    async def save_game(self, ctx: commands.Context):
        """Manually save the current game state."""
        emu = self._emulators.get(ctx.guild.id)
        if not emu or not emu.running:
            await ctx.send("No game is currently running.")
            return
        await emu.save_state()
        await ctx.send("Game state saved. ✅")

    # ------------------------------------------------------------------
    # Info commands (no admin required)
    # ------------------------------------------------------------------

    @dpp.command(name="controls")
    async def show_controls(self, ctx: commands.Context):
        """Show the input controls reference."""
        embed = discord.Embed(
            title="🎮 Discord Plays Pokemon — Controls",
            description=self.input_handler.get_controls_display(),
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @dpp.command(name="status")
    async def game_status(self, ctx: commands.Context):
        """Show whether the game is running and current settings."""
        guild = ctx.guild
        emu = self._emulators.get(guild.id)
        running = emu is not None and emu.running
        channel_id = await self.config.guild(guild).channel_id()
        rom_path = await self.config.guild(guild).rom_path()
        interval = await self.config.guild(guild).screenshot_interval()
        cooldown = await self.config.guild(guild).input_cooldown()
        passive = await self.config.guild(guild).passive_enabled()
        log_channel_id = await self.config.guild(guild).log_channel_id()
        log_interval = await self.config.guild(guild).log_interval_minutes()

        embed = discord.Embed(
            title="📊 Discord Plays Pokemon — Status",
            color=discord.Color.green() if running else discord.Color.greyple(),
        )
        embed.add_field(name="Status", value="🟢 Running" if running else "🔴 Stopped", inline=True)
        embed.add_field(name="Channel", value=f"<#{channel_id}>" if channel_id else "Not set", inline=True)
        embed.add_field(name="Passive Harvesting", value="On" if passive else "Off", inline=True)
        embed.add_field(name="ROM", value=f"`{rom_path}`" if rom_path else "Not set", inline=False)
        embed.add_field(name="Screenshot Interval", value=f"{interval}s", inline=True)
        embed.add_field(name="Input Cooldown", value=f"{cooldown}s", inline=True)
        log_val = f"<#{log_channel_id}> (every {log_interval}m)" if log_channel_id else "Not set"
        embed.add_field(name="History Log", value=log_val, inline=True)
        if running:
            embed.add_field(name="Queued Inputs", value=str(emu.input_queue.qsize()), inline=True)
            embed.add_field(name="Total Inputs", value=f"{emu.total_inputs:,}", inline=True)
            embed.add_field(name="Frames Processed", value=f"{emu.total_frames:,}", inline=True)
        await ctx.send(embed=embed)

    @dpp.command(name="screenshot", aliases=["ss"])
    async def force_screenshot(self, ctx: commands.Context):
        """Post a fresh screenshot of the current game state."""
        emu = self._emulators.get(ctx.guild.id)
        if not emu or not emu.running:
            await ctx.send("No game is currently running.")
            return
        screenshot = await emu.get_screenshot()
        if screenshot:
            await ctx.send(file=discord.File(screenshot, "pokemon.png"))
        else:
            await ctx.send("No screenshot available yet — the emulator may still be starting up.")

    # ------------------------------------------------------------------
    # Message listener — input processing
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild = message.guild
        emu = self._emulators.get(guild.id)
        if not emu or not emu.running:
            return

        channel_id = await self.config.guild(guild).channel_id()
        is_game_channel = message.channel.id == channel_id

        # --- Ignore bot commands everywhere ---
        prefixes = await self.bot.get_valid_prefixes(guild)
        content = message.content
        is_command = any(content.startswith(p) for p in prefixes)

        if is_game_channel:
            await self._handle_game_channel(message, emu, is_command)
        else:
            await self._handle_passive_channel(message, emu, is_command)

    async def _handle_game_channel(
        self, message: discord.Message, emu: EmulatorManager, is_command: bool
    ):
        """Game channel: parse as intentional inputs, delete non-command messages."""
        guild = message.guild

        if is_command:
            # Let the command framework handle it; don't delete
            return

        # --- Parse intentional input(s) ---
        max_inputs = await self.config.guild(guild).max_inputs_per_msg()
        buttons = self.input_handler.parse(message.content, max_inputs=max_inputs)

        # --- Per-user cooldown ---
        if buttons:
            cooldown_secs = await self.config.guild(guild).input_cooldown()
            key = (guild.id, message.author.id)
            now = datetime.utcnow()
            if key in self._user_cooldowns and now < self._user_cooldowns[key]:
                buttons = []  # on cooldown; still delete the message below
            else:
                self._user_cooldowns[key] = now + timedelta(seconds=cooldown_secs)

        # --- Queue buttons ---
        for btn in buttons:
            await emu.queue_input(btn)

        # --- Delete the user's message to keep the channel clean ---
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass  # missing perms or message already gone

    async def _handle_passive_channel(
        self, message: discord.Message, emu: EmulatorManager, is_command: bool
    ):
        """Non-game channel: silently harvest individual letters as inputs.
        Messages are NOT deleted.  Harvests from message text, URLs,
        attachment filenames, and any embed text already present."""
        if is_command:
            return

        passive_on = await self.config.guild(message.guild).passive_enabled()
        if not passive_on:
            return

        max_passive = await self.config.guild(message.guild).max_passive_inputs()
        text = self._gather_message_text(message)
        buttons = self.input_handler.harvest_letters(text, max_inputs=max_passive)

        for btn in buttons:
            await emu.queue_input(btn)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Catch embed arrivals. When someone posts a URL, Discord fills in
        the embed asynchronously which triggers an edit. Harvest any new
        embed text that wasn't present in the original message."""
        if after.author.bot or not after.guild:
            return

        emu = self._emulators.get(after.guild.id)
        if not emu or not emu.running:
            return

        channel_id = await self.config.guild(after.guild).channel_id()
        if after.channel.id == channel_id:
            return  # game channel is handled differently

        passive_on = await self.config.guild(after.guild).passive_enabled()
        if not passive_on:
            return

        # Only care about new embeds appearing (not user text edits)
        if len(after.embeds) <= len(before.embeds):
            return

        # Harvest only from the newly added embeds
        new_embeds = after.embeds[len(before.embeds):]
        parts: list[str] = []
        for embed in new_embeds:
            if embed.title:
                parts.append(embed.title)
            if embed.description:
                parts.append(embed.description)
            if embed.url:
                parts.append(embed.url)

        if not parts:
            return

        max_passive = await self.config.guild(after.guild).max_passive_inputs()
        text = " ".join(parts)
        buttons = self.input_handler.harvest_letters(text, max_inputs=max_passive)

        for btn in buttons:
            await emu.queue_input(btn)

    @staticmethod
    def _gather_message_text(message: discord.Message) -> str:
        """Combine all harvestable text from a message: content, URLs,
        attachment filenames, and any embeds already present."""
        parts: list[str] = [message.content]

        # Attachment filenames (e.g. "funny_dog.png")
        for attachment in message.attachments:
            if attachment.filename:
                parts.append(attachment.filename)

        # Embeds that arrived with the message (rare but possible)
        for embed in message.embeds:
            if embed.title:
                parts.append(embed.title)
            if embed.description:
                parts.append(embed.description)
            if embed.url:
                parts.append(embed.url)

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Screenshot update loop — edits one message instead of spamming
    # ------------------------------------------------------------------

    async def _game_loop(self, guild: discord.Guild):
        """Periodically grabs the latest screenshot and edits a single
        message in the game channel. If the message is lost (deleted,
        too old to edit, etc.) a new one is posted."""
        guild_id = guild.id
        try:
            interval = await self.config.guild(guild).screenshot_interval()
            channel_id = await self.config.guild(guild).channel_id()
            channel = guild.get_channel(channel_id)

            if not channel:
                log.error(f"Game channel {channel_id} not found in guild {guild_id}.")
                return

            # Give the emulator a moment to produce the first frame
            await asyncio.sleep(2)

            while guild_id in self._emulators and self._emulators[guild_id].running:
                try:
                    # Skip this cycle if the previous edit is still in flight
                    lock = self._screen_locks.setdefault(guild_id, asyncio.Lock())
                    if lock.locked():
                        log.debug(f"Screenshot update still in progress for guild {guild_id}, skipping cycle.")
                    else:
                        async with lock:
                            screenshot = await self._emulators[guild_id].get_screenshot()
                            if screenshot:
                                await self._update_screen_message(guild_id, channel, screenshot)
                except (discord.HTTPException, asyncio.TimeoutError) as e:
                    log.warning(f"Screenshot update failed (will retry): {e}")

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            log.info(f"Screenshot loop cancelled for guild {guild_id}.")
        except Exception as e:
            log.error(f"Screenshot loop crashed for guild {guild_id}: {e}", exc_info=True)
            emu = self._emulators.get(guild_id)
            if emu:
                await emu.save_state()

    async def _update_screen_message(
        self,
        guild_id: int,
        channel: discord.TextChannel,
        screenshot,
    ):
        """Edit the existing screen message with a new screenshot.

        If a non-deletable message (bot command, command response, or
        message posted while the cog was stopped) has appeared below
        the screen message, send a fresh one so the screenshot stays
        at the bottom of the channel.
        """
        existing = self._screen_messages.get(guild_id)

        if existing is not None:
            # Check if our message is still the latest in the channel
            needs_new = False
            try:
                async for msg in channel.history(limit=1, after=existing):
                    # There's at least one message newer than ours
                    needs_new = True
                    break
            except (discord.HTTPException, asyncio.TimeoutError):
                needs_new = True

            if not needs_new:
                # Still the latest — edit in place
                try:
                    await existing.edit(
                        attachments=[discord.File(screenshot, "pokemon.png")]
                    )
                    return
                except (discord.NotFound, discord.HTTPException):
                    pass  # fall through to send new

            # Old message is buried or gone — clean up reference
            self._screen_messages.pop(guild_id, None)

        # Send a fresh message and track it
        try:
            msg = await channel.send(file=discord.File(screenshot, "pokemon.png"))
            self._screen_messages[guild_id] = msg
            # Clean up old bot messages so only the new screenshot remains
            await self._cleanup_bot_messages(channel, msg)
        except discord.HTTPException as e:
            log.warning(f"Failed to post screenshot: {e}")

    async def _cleanup_bot_messages(
        self, channel: discord.TextChannel, keep: discord.Message
    ):
        """Delete all messages sent by the bot in the game channel except
        the one we want to keep (the new screenshot)."""
        try:
            to_delete: list[discord.Message] = []
            async for msg in channel.history(limit=50):
                if msg.id == keep.id:
                    continue
                if msg.author.id == self.bot.user.id:
                    to_delete.append(msg)

            if not to_delete:
                return

            # bulk_delete only works on messages < 14 days old
            # and requires between 2-100 messages
            if len(to_delete) >= 2:
                try:
                    await channel.delete_messages(to_delete)
                    return
                except discord.HTTPException:
                    pass  # fall through to individual deletes

            for msg in to_delete:
                try:
                    await msg.delete()
                except (discord.NotFound, discord.HTTPException):
                    pass
        except (discord.HTTPException, asyncio.TimeoutError) as e:
            log.warning(f"Cleanup of old bot messages failed: {e}")

    # ------------------------------------------------------------------
    # Historical log loop — posts new screenshots on a longer interval
    # ------------------------------------------------------------------

    async def _ensure_log_loop(self, guild: discord.Guild):
        """Start (or restart) the log loop if a log channel is configured
        and the emulator is running."""
        # Cancel any existing loop first
        task = self._log_loops.pop(guild.id, None)
        if task:
            task.cancel()

        log_channel_id = await self.config.guild(guild).log_channel_id()
        emu = self._emulators.get(guild.id)
        if log_channel_id and emu and emu.running:
            self._log_loops[guild.id] = self.bot.loop.create_task(
                self._log_loop(guild)
            )

    async def _log_loop(self, guild: discord.Guild):
        """Periodically posts a new screenshot to the log channel as a
        permanent historical record. Each post is a new message (never edited)."""
        guild_id = guild.id
        try:
            log_channel_id = await self.config.guild(guild).log_channel_id()
            interval_min = await self.config.guild(guild).log_interval_minutes()
            channel = guild.get_channel(log_channel_id)

            if not channel:
                log.error(f"Log channel {log_channel_id} not found in guild {guild_id}.")
                return

            # Wait the full interval before the first post
            await asyncio.sleep(interval_min * 60)

            while guild_id in self._emulators and self._emulators[guild_id].running:
                screenshot = await self._emulators[guild_id].get_screenshot()
                if screenshot:
                    emu = self._emulators[guild_id]
                    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                    embed = discord.Embed(
                        title="📸 Game Progress Snapshot",
                        description=f"🕐 {timestamp}\n🎮 Total inputs: {emu.total_inputs:,}",
                        color=discord.Color.blue(),
                    )
                    embed.set_image(url="attachment://pokemon.png")
                    try:
                        await channel.send(
                            embed=embed,
                            file=discord.File(screenshot, "pokemon.png"),
                        )
                    except discord.HTTPException as e:
                        log.warning(f"Failed to post to log channel: {e}")

                await asyncio.sleep(interval_min * 60)

        except asyncio.CancelledError:
            log.info(f"Log loop cancelled for guild {guild_id}.")
        except Exception as e:
            log.error(f"Log loop crashed for guild {guild_id}: {e}", exc_info=True)