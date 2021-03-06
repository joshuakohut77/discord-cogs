from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass

from .abcd import MixinMeta



class PokecenterMixin(MixinMeta):
    """Pokecenter"""
    

    @commands.group(name="pokecenter", aliases=['pmc'])
    @commands.guild_only()
    async def _pokecenter(self, ctx: commands.Context) -> None:
        """Base command to manage the pokecenter (heal)
        """
        pass

    @_pokecenter.command()
    async def heal(self, ctx: commands.Context, user: discord.Member = None) -> None:
        if user is None:
            user = ctx.author
        
        trainer = TrainerClass(user.id)
        trainer.healAll()

        # partySize = trainer.getPartySize()


        if trainer.statuscode == 420:
            await ctx.send(trainer.message)
        else:
            await ctx.send('Something went wrong')

