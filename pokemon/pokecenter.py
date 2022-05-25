from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
from discord_components import (ButtonStyle, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from services.trainerclass import trainer as TrainerClass
from services.storeclass import store as StoreClass
from services.pokeclass import Pokemon as PokemonClass

from .abcd import MixinMeta
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)



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
        user: discord.User = ctx.author

        trader = TrainerClass(user.id)
        pokemon = trader.getPokemonById(pokemonId)

        if trader.statuscode == 96:
            await ctx.send(f'{user.display_name}\'s trade failed.')
            return


        # await ctx.send('Other trainer has to accept your trade request')

        embed, btns = self.__pokemonSingleCard(user, pokemon)

        await ctx.send(
            content=f'{trainerUser.mention} {user.display_name} wants to trade with you.',
            embed=embed,
            components=btns

        )

        # tradee = TrainerClass(trainerUser.id)


    async def __on_trade_click(self, interaction: Interaction):
        pass


    def __pokemonSingleCard(self, user: discord.User, pokemon: Pokemon):

        embed = createStatsEmbed(user, pokemon)

        firstRowBtns = []

        firstRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Accept Trade", custom_id='accept'),
            self.__on_trade_click
        ))
        firstRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.red, label="Decline Trade", custom_id='decline'),
            self.__on_trade_click
        ))

        btns = []
        if len(firstRowBtns) > 0:
            btns.append(firstRowBtns)

        return embed, btns

