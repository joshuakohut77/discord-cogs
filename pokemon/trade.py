from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
# from discord_components import (ButtonStyle, Button, Interaction, interaction)
from discord import ui, ButtonStyle, Button, Interaction

from redbot.core.commands.context import Context

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass
from services.encounterclass import encounter as EncounterClass

from .abcd import MixinMeta
from .functions import (createStatsEmbed)


class TradeState:
    senderDiscordId: str
    receiverDiscordId: str
    senderPokemonId: int
    receiverPokemonId: int

    messageId: int
    channelId: int

    pokemonList: List[PokemonClass]
    idx: int


    def __init__(self, messageId: int, channelId: int) -> None:
        self.messageId = messageId
        self.channelId = channelId



class TradeMixin(MixinMeta):
    """Pokecenter"""
    
    __tradeState: dict[str, TradeState] = {}

    @commands.group(name="pokecenter", aliases=['pmc'])
    @commands.guild_only()
    async def _pokecenter(self, ctx: commands.Context) -> None:
        """Base command to manage the pokecenter (heal)
        """
        pass


    @_pokecenter.command()
    async def trade(self, ctx: commands.Context, trainerUser: Union[discord.Member,discord.User], pokemonId: str):
        user: discord.User = ctx.author

        trader = TrainerClass(user.id)
        pokemon = trader.getPokemonById(pokemonId)

        if trader.statuscode == 96:
            await ctx.send(f'{user.display_name}\'s trade failed.')
            return

        # Don't allow trades of your current active starter pokemon
        active = trader.getActivePokemon()
        if active.trainerId == pokemon.trainerId:
            await ctx.send(f'{user.mention} you cannot trade your active Pokemon. Change your active Pokemon or select a different Pokemon.')
            return

        # await ctx.send('Other trainer has to accept your trade request')

        embed, btns = self.__pokemonSingleCard(user, pokemon)

        message: discord.Message = await ctx.send(
            content=f'{trainerUser.mention} {user.display_name} wants to trade with you.',
            embed=embed,
            components=btns

        )

        state = TradeState(message.id, message.channel.id)
        state.senderDiscordId = str(user.id)
        state.receiverDiscordId = str(trainerUser.id)
        state.senderPokemonId = pokemon.trainerId

        self.__tradeState[state.receiverDiscordId] = state



    async def __on_trade_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTradeState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__tradeState[str(user.id)]
        
        channel: discord.TextChannel = self.bot.get_channel(state.channelId)
        message: discord.Message = await channel.fetch_message(state.messageId)

        ctx: Context = await self.bot.get_context(interaction.message)
        sender = await ctx.guild.fetch_member(int(state.senderDiscordId))
        # sender: discord.User = ctx.message.server.get_member(int(state.senderDiscordId))
        # sender: discord.User = self.bot.get_user(int(state.senderDiscordId))
        

        if interaction.custom_id == 'accept':
            await interaction.send('You accepted this trade.')

            trainer = TrainerClass(str(user.id))
            pokemonList = trainer.getPokemon(False, True)

            state.pokemonList = pokemonList
            state.idx = 0

            embed, btns = self.__pokemonPcTradeCard(user, pokemonList, 0)

            message: discord.Message = await message.edit(
                content=f'{user.display_name} is choosing a pokemon to offer {sender.display_name}.',
                embed=embed,
                components=btns
            )
            state.messageId = message.id
            self.__tradeState[str(user.id)] = state
        else:
            await interaction.send('You declined this trade.')

            trader = TrainerClass(state.senderDiscordId)
            pokemon = trader.getPokemonById(state.senderPokemonId)

            embed, btns = self.__pokemonSingleCard(user, pokemon)

            message: discord.Message = await message.edit(
                content=f'{user.display_name} declined {sender.display_name}\'s trade.',
                embed=embed,
                components=btns
            )
            del self.__tradeState[str(user.id)]


    def __checkTradeState(self, user: discord.User, message: discord.Message):
        state: TradeState
        if str(user.id) not in self.__tradeState.keys():
            return False
        else:
            state = self.__tradeState[str(user.id)]
            if state.messageId != message.id:
                return False
        return True
    

    def __pokemonSingleCard(self, user: discord.User, pokemon: PokemonClass):

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


    async def __on_offer_trade(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTradeState(user, interaction.message):
            await interaction.send('This is not for you.')
            return
        
        state = self.__tradeState[str(user.id)]

        receiverPokemon = state.pokemonList[state.idx]

        sender = TrainerClass(state.senderDiscordId)
        senderPokemon = sender.getPokemonById(state.senderPokemonId)
        
        enc = EncounterClass(senderPokemon, receiverPokemon)
        enc.trade()

        await interaction.send('Trade complete')

        embed, btns = self.__pokemonPcTradeCard(user, state.pokemonList, state.idx)

        channel: discord.TextChannel = self.bot.get_channel(state.channelId)
        message: discord.Message = await channel.fetch_message(state.messageId)

        ctx: Context = await self.bot.get_context(interaction.message)
        senderDiscord = await ctx.guild.fetch_member(int(state.senderDiscordId))

        message: discord.Message = await message.edit(
            content=f'{user.display_name} traded his {receiverPokemon.pokemonName} for {senderDiscord.display_name}\'s {senderPokemon.pokemonName}!',
            embed=embed,
            components=[]
        )
        del self.__tradeState[str(user.id)]


    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTradeState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__tradeState[str(user.id)]
        state.idx = state.idx + 1

        embed, btns = self.__pokemonPcTradeCard(user, state.pokemonList, state.idx)
        message = await interaction.edit_origin(embed=embed, components=btns)
        state.messageId = message.id
        self.__tradeState[str(user.id)] = state
    

    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__tradeState[str(user.id)]
        state.idx = state.idx - 1

        embed, btns = self.__pokemonPcTradeCard(user, state.pokemonList, state.idx)
        message = await interaction.edit_origin(embed=embed, components=btns)
        state.messageId = message.id
        self.__tradeState[str(user.id)] = state

    
    def __pokemonPcTradeCard(self, user: discord.User, pokemonList: List[PokemonClass], idx: int):
        pokemon = pokemonList[idx]

        # Kind of a hack, but if the property is still set to None,
        # then we probably haven't loaded this pokemon yet.
        if pokemon.pokemonName is None:
            pokemon.load(pokemonId=pokemon.trainerId)


        embed = createStatsEmbed(user, pokemon)

        firstRowBtns = []
        if idx > 0:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'),
                self.__on_prev_click
            ))
        if idx < len(pokemonList) - 1:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
                self.__on_next_click
            ))

        secondRowBtns = []
        firstRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Offer to trade", custom_id='offer'),
            self.__on_offer_trade
        ))


        btns = []
        if len(firstRowBtns) > 0:
            btns.append(firstRowBtns)
        if len(secondRowBtns) > 0:
            btns.append(secondRowBtns)

        return embed, btns