from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import asyncio
import logging

import discord
from redbot.core import commands
from .abc import MixinMeta
from .db import ChodeCoinDB
from .constants import COIN_EMOJI, EMBED_COLOR

if TYPE_CHECKING:
    pass

log = logging.getLogger("red.chodecoin.commands")


class CommandsMixin(MixinMeta):
    """User-facing ChodeCoin commands."""

    __slots__: tuple = ()

    # ------------------------------------------------------------------
    # Command group
    # ------------------------------------------------------------------

    @commands.group(name="chodecoin", aliases=["cc"], invoke_without_command=True)
    @commands.guild_only()
    async def chodecoin(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Check your ChodeCoin balance (or someone else's)."""
        target = member or ctx.author
        balance = await asyncio.to_thread(ChodeCoinDB.get_balance, ctx.guild.id, target.id)
        rank = await asyncio.to_thread(ChodeCoinDB.get_rank, ctx.guild.id, target.id)

        embed = discord.Embed(
            title=f"{COIN_EMOJI} ChodeCoin Balance",
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="User", value=target.mention, inline=True)
        embed.add_field(name="Balance", value=f"**{balance}** {COIN_EMOJI}", inline=True)
        if rank is not None:
            embed.add_field(name="Rank", value=f"#{rank}", inline=True)
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Gift
    # ------------------------------------------------------------------

    @chodecoin.command(name="gift", aliases=["give", "send"])
    @commands.guild_only()
    async def gift(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Gift ChodeCoin to another user.

        Example: `[p]cc gift @User 10`
        """
        if amount <= 0:
            return await ctx.send("Amount must be positive.")
        if member.id == ctx.author.id:
            return await ctx.send("You can't gift yourself, weirdo.")
        if member.bot:
            return await ctx.send("Bots have no use for ChodeCoin.")

        try:
            sender_bal, recip_bal = await asyncio.to_thread(
                ChodeCoinDB.gift, ctx.guild.id, ctx.author.id, member.id, amount
            )
        except ValueError as e:
            return await ctx.send(str(e))

        embed = discord.Embed(
            title=f"{COIN_EMOJI} ChodeCoin Gift",
            description=(
                f"{ctx.author.mention} gifted **{amount}** {COIN_EMOJI} to {member.mention}!"
            ),
            color=EMBED_COLOR,
        )
        embed.add_field(
            name=f"{ctx.author.display_name}'s Balance",
            value=f"**{sender_bal}** {COIN_EMOJI}",
            inline=True,
        )
        embed.add_field(
            name=f"{member.display_name}'s Balance",
            value=f"**{recip_bal}** {COIN_EMOJI}",
            inline=True,
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------

    @chodecoin.command(name="leaderboard", aliases=["lb", "top"])
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context, count: int = 10):
        """Show the ChodeCoin leaderboard.

        Example: `[p]cc lb 15`
        """
        count = max(1, min(count, 25))
        rows = await asyncio.to_thread(ChodeCoinDB.leaderboard, ctx.guild.id, count)

        if not rows:
            return await ctx.send("No one has any ChodeCoin yet. Start giving!")

        lines: list[str] = []
        for i, (user_id_str, balance) in enumerate(rows, 1):
            member = ctx.guild.get_member(int(user_id_str))
            name = member.display_name if member else f"Unknown ({user_id_str})"
            medal = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}.get(i, f"**{i}.**")
            lines.append(f"{medal} {name} — **{balance}** {COIN_EMOJI}")

        embed = discord.Embed(
            title=f"{COIN_EMOJI} ChodeCoin Leaderboard",
            description="\n".join(lines),
            color=EMBED_COLOR,
        )
        embed.set_footer(text=f"Top {len(rows)} in {ctx.guild.name}")
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @chodecoin.command(name="stats")
    @commands.guild_only()
    async def stats(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """View detailed ChodeCoin statistics for a user.

        Example: `[p]cc stats @User`
        """
        target = member or ctx.author
        s = await asyncio.to_thread(ChodeCoinDB.get_stats, ctx.guild.id, target.id)
        balance = await asyncio.to_thread(ChodeCoinDB.get_balance, ctx.guild.id, target.id)
        rank = await asyncio.to_thread(ChodeCoinDB.get_rank, ctx.guild.id, target.id)

        embed = discord.Embed(
            title=f"{COIN_EMOJI} {target.display_name}'s ChodeCoin Stats",
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Balance", value=f"**{balance}** {COIN_EMOJI}", inline=True)
        embed.add_field(name="Rank", value=f"#{rank}" if rank else "N/A", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # spacer

        embed.add_field(
            name="++ Given / Received",
            value=f"{s.get('increments_given', 0)} / {s.get('increments_recv', 0)}",
            inline=True,
        )
        embed.add_field(
            name="-- Given / Received",
            value=f"{s.get('decrements_given', 0)} / {s.get('decrements_recv', 0)}",
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(
            name="Gifts Sent",
            value=f"{s.get('gifts_sent', 0)} ({s.get('gifts_sent_total', 0)} {COIN_EMOJI} total)",
            inline=True,
        )
        embed.add_field(
            name="Gifts Received",
            value=f"{s.get('gifts_recv', 0)} ({s.get('gifts_recv_total', 0)} {COIN_EMOJI} total)",
            inline=True,
        )

        await ctx.send(embed=embed)