from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import asyncio
import logging

import discord
from redbot.core import commands
from .abc import MixinMeta
from .db import VaultDB
from .constants import COIN_EMOJI, EMBED_COLOR

if TYPE_CHECKING:
    pass

log = logging.getLogger("red.vault.commands")


class CommandsMixin(MixinMeta):
    """User-facing Vault commands."""

    __slots__: tuple = ()

    @commands.group(name="vault", aliases=["v"], invoke_without_command=True)
    @commands.guild_only()
    async def vault(self, ctx: commands.Context):
        """The Vault — your collection of cards, artifacts, and allies."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # TODO: Subcommands to be built after interface discussion
    # - vault inventory / vault inv
    # - vault store / vault shop
    # - vault buy <card>
    # - vault use <card>
    # - vault equip <card>
    # - vault unequip <card>
    # - vault inspect <card>
    # - vault stats
