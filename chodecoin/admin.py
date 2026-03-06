from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import logging

import discord
from redbot.core import commands
from .abc import MixinMeta
from .db import ChodeCoinDB
from .constants import COIN_EMOJI, EMBED_COLOR

if TYPE_CHECKING:
    pass

log = logging.getLogger("red.chodecoin.admin")


class AdminMixin(MixinMeta):
    """Admin-only ChodeCoin commands."""

    __slots__: tuple = ()

    @commands.group(name="ccadmin", aliases=["chodecoinadmin"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def ccadmin(self, ctx: commands.Context):
        """Admin commands for ChodeCoin management."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # ------------------------------------------------------------------
    # Set balance
    # ------------------------------------------------------------------

    @ccadmin.command(name="set")
    async def set_balance(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Set a user's ChodeCoin balance to an exact amount.

        Example: `[p]ccadmin set @User 100`
        """
        new_bal = await asyncio.to_thread(
            ChodeCoinDB.admin_set_balance,
            ctx.guild.id, member.id, amount, ctx.author.id,
        )
        embed = discord.Embed(
            title=f"{COIN_EMOJI} Balance Updated",
            description=f"{member.mention}'s balance set to **{new_bal}** {COIN_EMOJI}.",
            color=EMBED_COLOR,
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Reset user
    # ------------------------------------------------------------------

    @ccadmin.command(name="resetuser")
    async def reset_user(self, ctx: commands.Context, member: discord.Member):
        """Soft-reset a single user's ChodeCoin (sets to 0, marks inactive).

        Example: `[p]ccadmin resetuser @User`
        """
        await asyncio.to_thread(
            ChodeCoinDB.soft_reset_user,
            ctx.guild.id, member.id, ctx.author.id,
        )
        embed = discord.Embed(
            title=f"{COIN_EMOJI} User Reset",
            description=f"{member.mention}'s ChodeCoin has been reset.",
            color=EMBED_COLOR,
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Reset all
    # ------------------------------------------------------------------

    @ccadmin.command(name="resetall")
    async def reset_all(self, ctx: commands.Context, confirm: str = ""):
        """Soft-reset ALL ChodeCoin in the server.

        Type `[p]ccadmin resetall YES` to confirm.
        """
        if confirm.upper() != "YES":
            return await ctx.send(
                "⚠️ This will reset **all** ChodeCoin balances in this server.\n"
                f"Type `{ctx.prefix}ccadmin resetall YES` to confirm."
            )

        count = await asyncio.to_thread(
            ChodeCoinDB.soft_reset, ctx.guild.id, ctx.author.id
        )
        embed = discord.Embed(
            title=f"{COIN_EMOJI} Full Reset",
            description=f"All ChodeCoin balances reset. **{count}** wallets affected.",
            color=EMBED_COLOR,
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Add / Remove arbitrary amounts
    # ------------------------------------------------------------------

    @ccadmin.command(name="add")
    async def admin_add(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Add ChodeCoin to a user's balance.

        Example: `[p]ccadmin add @User 50`
        """
        if amount <= 0:
            return await ctx.send("Amount must be positive. Use `remove` to subtract.")

        current = await asyncio.to_thread(ChodeCoinDB.get_balance, ctx.guild.id, member.id)
        new_bal = await asyncio.to_thread(
            ChodeCoinDB.admin_set_balance,
            ctx.guild.id, member.id, current + amount, ctx.author.id,
        )
        await ctx.send(f"Added **{amount}** {COIN_EMOJI} to {member.mention}. New balance: **{new_bal}** {COIN_EMOJI}.")

    @ccadmin.command(name="remove")
    async def admin_remove(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Remove ChodeCoin from a user's balance.

        Example: `[p]ccadmin remove @User 25`
        """
        if amount <= 0:
            return await ctx.send("Amount must be positive.")

        current = await asyncio.to_thread(ChodeCoinDB.get_balance, ctx.guild.id, member.id)
        new_bal = await asyncio.to_thread(
            ChodeCoinDB.admin_set_balance,
            ctx.guild.id, member.id, current - amount, ctx.author.id,
        )
        await ctx.send(f"Removed **{amount}** {COIN_EMOJI} from {member.mention}. New balance: **{new_bal}** {COIN_EMOJI}.")