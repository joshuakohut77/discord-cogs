from __future__ import annotations
from re import S
from typing import Any, Dict, List, Union, TYPE_CHECKING

import random

import discord

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass

from .abcd import MixinMeta


class DebugMixin(MixinMeta):
    """Debug"""


    @commands.group(name="debug", aliases=['d'])
    @commands.guild_only()
    async def _debug(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    @_debug.command()
    async def add(self, ctx: commands.Context, user: discord.Member = None) -> None:
        if user is None:
            user = ctx.author

        trainer = TrainerClass(str(user.id))
        ids = range(1, 152)
        id = random.choice(ids)
        pokemon = trainer.addPokemon(id)

        await ctx.send(f'{pokemon.pokemonName} added.')

