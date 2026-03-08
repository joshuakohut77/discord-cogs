from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import logging

import discord
from redbot.core import commands
from .abc import MixinMeta
from .db import VaultDB
from .constants import EMBED_COLOR

if TYPE_CHECKING:
    pass

log = logging.getLogger("red.vault.admin")


class AdminMixin(MixinMeta):
    """Admin commands for Vault card management."""

    __slots__: tuple = ()

    @commands.group(name="vaultadmin", aliases=["va"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def vaultadmin(self, ctx: commands.Context):
        """Admin commands for managing The Vault card catalog."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # TODO: Admin subcommands to be built
    # - va addcard
    # - va editcard
    # - va removecard
    # - va setprop <card> <key> <value>
    # - va delprop <card> <key>
    # - va grant <user> <card>    (give card without purchase)
    # - va revoke <user> <inv_id> (remove from inventory)
    # - va listcards [category] [rarity]
