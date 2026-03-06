from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import logging
import re

from redbot.core import commands
from .abc import MixinMeta
from .db import ChodeCoinDB

if TYPE_CHECKING:
    import discord

log = logging.getLogger("red.chodecoin.events")

# ---------------------------------------------------------------
# Patterns to match:
#   <@123456>++      <@123456> ++
#   <@!123456>++     <@!123456> ++
#   <@123456>--      <@123456> --
#   <@!123456>--     <@!123456> --
# Works anywhere in the message (mid-sentence is fine).
# ---------------------------------------------------------------
KARMA_PATTERN = re.compile(
    r"<@!?(\d+)>\s*(\+\+|--)"
)


class EventMixin(MixinMeta):
    """Listens for @user++ and @user-- in messages."""

    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        if not message.content:
            return

        matches = KARMA_PATTERN.findall(message.content)
        if not matches:
            return

        # Deduplicate — only process each (user, op) pair once per message
        seen: set[tuple[int, str]] = set()
        results: list[str] = []

        for raw_id, operator in matches:
            try:
                target_id = int(raw_id)
            except ValueError:
                continue

            pair = (target_id, operator)
            if pair in seen:
                continue
            seen.add(pair)

            # Can't ++ / -- yourself
            if target_id == message.author.id:
                results.append("You can't change your own ChodeCoin, nerd.")
                continue

            # Make sure target is a real member
            target = message.guild.get_member(target_id)
            if target is None:
                continue

            # Don't award coins to bots
            if target.bot:
                continue

            try:
                if operator == "++":
                    new_bal = await asyncio.to_thread(
                        ChodeCoinDB.increment,
                        message.guild.id, target_id, message.author.id,
                    )
                    results.append(
                        f"**{target.display_name}** gained a ChodeCoin! (Balance: **{new_bal}** CC)"
                    )
                else:
                    new_bal = await asyncio.to_thread(
                        ChodeCoinDB.decrement,
                        message.guild.id, target_id, message.author.id,
                    )
                    results.append(
                        f"**{target.display_name}** lost a ChodeCoin. (Balance: **{new_bal}** CC)"
                    )
            except Exception as e:
                log.error(f"Error processing karma for {target_id}: {e}")

        if results:
            await message.reply("\n".join(results), mention_author=False)
