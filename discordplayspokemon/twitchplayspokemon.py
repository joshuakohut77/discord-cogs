"""Twitch Plays Pokemon — a Red-DiscordBot cog that lets a Discord server
collectively play a Game Boy game via chat messages."""

import asyncio
import logging
from datetime import datetime, timedelta

import discord
from redbot.core import commands, Config, checks
from redbot.core.data_manager import cog_data_path

from .emulator import EmulatorManager
from .input_handler import InputHandler

log = logging.getLogger("red.twitchplayspokemon")


class TwitchPlaysPokemon(commands.Cog):
    """Community-driven Pokemon gameplay through Discord messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=777000100, force_registration=True)

        default_guild = {
            "channel_id": None,          # channel where the game lives
            "rom_path": None,            # filesystem path to the .gb ROM
            "screenshot_interval": 4,    # seconds between screen posts
            "input_cooldown": 1.0,       # per-user cooldown in seconds
            "max_inputs_per_msg": 5,     # combo cap
            "enabled": False,
            "scale_factor": 3,           # screenshot upscale multiplier
        }
        self.config.register_guild(**default_guild)

        self.input_handler = InputHandler()

        # Per-guild runtime state
        self._emulators: dict[int, EmulatorManager] = {}
        self._game_loops: dict[int, asyncio.Task] = {}
        self._user_cooldowns: dict[tuple[int, int], datetime] = {}

    # ------------------------------------------------------------------
    # Cog lifecycle
    # ------------------------------------------------------------------

    def cog_unload(self):
        for task in self._game_loops.values():
            task.cancel()
        for emu in self._emulators.values():
            asyncio.create_task(emu.stop())

    # ------------------------------------------------------------------
    # Admin command group
    # ------------------------------------------------------------------

    @commands.group(name="tpp", invoke_without_command=True)
    @commands.guild_only()
    async def tpp(self, ctx: commands.Context):
        """Twitch Plays Pokemon — community-driven Game Boy gameplay."""
        await ctx.send_help(ctx.command)

    @tpp.command(name="setchannel")
    @checks.admin_or_permissions(administrator=True)
    async def set_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where the game will be played."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"Game channel set to {channel.mention}.")

    @tpp.command(name="setrom")
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

    @tpp.command(name="setinterval")
    @checks.admin_or_permissions(administrator=True)
    async def set_interval(self, ctx: commands.Context, seconds: int):
        """Set the screenshot posting interval (2–30 seconds)."""
        seconds = max(2, min(30, seconds))
        await self.config.guild(ctx.guild).screenshot_interval.set(seconds)
        await ctx.send(f"Screenshot interval set to **{seconds}s**.")

    @tpp.command(name="setcooldown")
    @checks.admin_or_permissions(administrator=True)
    async def set_cooldown(self, ctx: commands.Context, seconds: float):
        """Set the per-user input cooldown (0.5–10 seconds)."""
        seconds = max(0.5, min(10.0, seconds))
        await self.config.guild(ctx.guild).input_cooldown.set(seconds)
        await ctx.send(f"Input cooldown set to **{seconds}s**.")

    @tpp.command(name="setscale")
    @checks.admin_or_permissions(administrator=True)
    async def set_scale(self, ctx: commands.Context, factor: int):
        """Set the screenshot scale factor (1–6)."""
        factor = max(1, min(6, factor))
        await self.config.guild(ctx.guild).scale_factor.set(factor)
        await ctx.send(f"Scale factor set to **{factor}x**.")

    # ------------------------------------------------------------------
    # Game control
    # ------------------------------------------------------------------

    @tpp.command(name="start")
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
            await ctx.send("No ROM path configured. Use `[p]tpp setrom <path>` first.")
            return
        if not channel_id:
            await ctx.send("No game channel configured. Use `[p]tpp setchannel #channel` first.")
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

        self._game_loops[guild.id] = self.bot.loop.create_task(
            self._game_loop(guild)
        )

        channel = guild.get_channel(channel_id)
        await status_msg.edit(content="🎮 **Game started!** Send inputs in " +
                              (channel.mention if channel else "the game channel") + ".")

    @tpp.command(name="stop")
    @checks.admin_or_permissions(administrator=True)
    async def stop_game(self, ctx: commands.Context):
        """Stop the game, save state, and shut down the emulator."""
        guild = ctx.guild

        if guild.id not in self._emulators:
            await ctx.send("No game is currently running.")
            return

        if guild.id in self._game_loops:
            self._game_loops.pop(guild.id).cancel()
        emu = self._emulators.pop(guild.id, None)
        if emu:
            await emu.stop()
        await self.config.guild(guild).enabled.set(False)
        await ctx.send("Game stopped and state saved. ✅")

    @tpp.command(name="save")
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

    @tpp.command(name="controls")
    async def show_controls(self, ctx: commands.Context):
        """Show the input controls reference."""
        embed = discord.Embed(
            title="🎮 Twitch Plays Pokemon — Controls",
            description=self.input_handler.get_controls_display(),
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @tpp.command(name="status")
    async def game_status(self, ctx: commands.Context):
        """Show whether the game is running and current settings."""
        guild = ctx.guild
        emu = self._emulators.get(guild.id)
        running = emu is not None and emu.running
        channel_id = await self.config.guild(guild).channel_id()
        rom_path = await self.config.guild(guild).rom_path()
        interval = await self.config.guild(guild).screenshot_interval()
        cooldown = await self.config.guild(guild).input_cooldown()

        embed = discord.Embed(
            title="📊 Twitch Plays Pokemon — Status",
            color=discord.Color.green() if running else discord.Color.greyple(),
        )
        embed.add_field(name="Status", value="🟢 Running" if running else "🔴 Stopped", inline=True)
        embed.add_field(name="Channel", value=f"<#{channel_id}>" if channel_id else "Not set", inline=True)
        embed.add_field(name="ROM", value=f"`{rom_path}`" if rom_path else "Not set", inline=False)
        embed.add_field(name="Screenshot Interval", value=f"{interval}s", inline=True)
        embed.add_field(name="Input Cooldown", value=f"{cooldown}s", inline=True)
        if running:
            embed.add_field(name="Queued Inputs", value=str(emu.input_queue.qsize()), inline=True)
            embed.add_field(name="Total Inputs", value=f"{emu.total_inputs:,}", inline=True)
            embed.add_field(name="Frames Processed", value=f"{emu.total_frames:,}", inline=True)
        await ctx.send(embed=embed)

    @tpp.command(name="screenshot", aliases=["ss"])
    async def force_screenshot(self, ctx: commands.Context):
        """Post a screenshot of the current game state."""
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
        if message.channel.id != channel_id:
            return

        # --- Parse input(s) ---
        max_inputs = await self.config.guild(guild).max_inputs_per_msg()
        buttons = self.input_handler.parse(message.content, max_inputs=max_inputs)
        if not buttons:
            return

        # --- Per-user cooldown ---
        cooldown_secs = await self.config.guild(guild).input_cooldown()
        key = (guild.id, message.author.id)
        now = datetime.utcnow()
        if key in self._user_cooldowns and now < self._user_cooldowns[key]:
            return  # silently drop
        self._user_cooldowns[key] = now + timedelta(seconds=cooldown_secs)

        # --- Queue buttons ---
        for btn in buttons:
            await emu.queue_input(btn)

        # --- Visual confirmation ---
        try:
            await message.add_reaction("🎮")
        except discord.HTTPException:
            pass

    # ------------------------------------------------------------------
    # Screenshot posting loop
    # ------------------------------------------------------------------

    async def _game_loop(self, guild: discord.Guild):
        """Periodically grabs the latest screenshot and posts it to the
        game channel. Runs until cancelled or the emulator stops."""
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
                screenshot = await self._emulators[guild_id].get_screenshot()
                if screenshot:
                    try:
                        await channel.send(
                            file=discord.File(screenshot, "pokemon.png")
                        )
                    except discord.HTTPException as e:
                        log.warning(f"Failed to post screenshot: {e}")

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            log.info(f"Screenshot loop cancelled for guild {guild_id}.")
        except Exception as e:
            log.error(f"Screenshot loop crashed for guild {guild_id}: {e}", exc_info=True)
            emu = self._emulators.get(guild_id)
            if emu:
                await emu.save_state()