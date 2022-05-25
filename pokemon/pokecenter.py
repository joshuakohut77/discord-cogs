from __future__ import annotations
from re import A
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
from discord import (Embed, Member)
from discord import message
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from services.storeclass import store as StoreClass


from .abcd import MixinMeta
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)
import constant


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


    async def trade(self, ctx: commands.Context, trainerUser: Union[discord.Member,discord.User], pokemonId: str):
        user = ctx.author

        trader = TrainerClass(user.id)
        pokemon = trader.getPokemonById(pokemonId)

        if trader.statuscode == 96:
            await ctx.send('Trade failed')
            return


        await ctx.send('Other trainer has to accept your trade request')



        # tradee = TrainerClass(trainerUser.id)

