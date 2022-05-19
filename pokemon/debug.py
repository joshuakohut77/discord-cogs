from __future__ import annotations
from re import S
from typing import Any, Dict, List, Union, TYPE_CHECKING

import random

import discord

from redbot.core import commands

from services.dbclass import db as dbconn
from services.trainerclass import trainer as TrainerClass
from models.location import LocationModel

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


    async def marts(self, ctx: commands.Context):
        db = dbconn()
        queryStr = """
        select distinct
            store."locationId",
            locations."name"
        from store
            join locations on locations."locationId" = store."locationId"
        """
        result = db.queryAll(queryStr)

        locations = ''
        for r in result:
            locations += f'{r[0]} {r[1]} \r\n'

        await ctx.send(f'Pokemart locations \r\n {locations}')    


    async def loc(self, ctx: commands.Context, id: int = 86):
        user = ctx.author()

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(locationId=id)

        location = trainer.getLocation()

        await ctx.send(f'Location set to {location.name}.')