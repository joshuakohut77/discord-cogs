from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
# from discord_components import (ButtonStyle, Button, Interaction, interaction)
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

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
            view=btns

        )

        state = TradeState(message.id, message.channel.id)
        state.senderDiscordId = str(user.id)
        state.receiverDiscordId = str(trainerUser.id)
        state.senderPokemonId = pokemon.trainerId

        self.__tradeState[state.receiverDiscordId] = state



    async def __on_trade_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTradeState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.__tradeState[str(user.id)]

        channel: discord.TextChannel = self.bot.get_channel(state.channelId)
        if channel is None:
            await interaction.response.send_message('Error: Channel not found. The original message may have been deleted.', ephemeral=True)
            return
        message: discord.Message = await channel.fetch_message(state.messageId)

        ctx: Context = await self.bot.get_context(interaction.message)
        sender = await ctx.guild.fetch_member(int(state.senderDiscordId))
        # sender: discord.User = ctx.message.server.get_member(int(state.senderDiscordId))
        # sender: discord.User = self.bot.get_user(int(state.senderDiscordId))
        

        if interaction.custom_id == 'accept':
            await interaction.response.send_message('You accepted this trade.')

            trainer = TrainerClass(str(user.id))
            pokemonList = trainer.getPokemon(False, True)

            state.pokemonList = pokemonList
            state.idx = 0

            embed, btns = self.__pokemonPcTradeCard(user, pokemonList, 0)

            message: discord.Message = await message.edit(
                content=f'{user.display_name} is choosing a pokemon to offer {sender.display_name}.',
                embed=embed,
                view=btns
            )
            state.messageId = message.id
            self.__tradeState[str(user.id)] = state
        else:
            await interaction.response.send_message('You declined this trade.')

            trader = TrainerClass(state.senderDiscordId)
            pokemon = trader.getPokemonById(state.senderPokemonId)

            embed, btns = self.__pokemonSingleCard(user, pokemon)

            message: discord.Message = await message.edit(
                content=f'{user.display_name} declined {sender.display_name}\'s trade.',
                embed=embed,
                view=btns
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

        view = View()

        button = Button(style=ButtonStyle.green, label="Accept Trade", custom_id='accept')
        button.callback = self.on_trade_click_trade
        view.add_item(button)

        button = Button(style=ButtonStyle.red, label="Decline Trade", custom_id='decline')
        button.callback = self.on_trade_click_trade
        view.add_item(button)

        return embed, view


    async def __on_offer_trade(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTradeState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return
        
        state = self.__tradeState[str(user.id)]

        receiverPokemon = state.pokemonList[state.idx]

        sender = TrainerClass(state.senderDiscordId)
        senderPokemon = sender.getPokemonById(state.senderPokemonId)
        
        enc = EncounterClass(senderPokemon, receiverPokemon)
        enc.trade()

        await interaction.response.send_message('Trade complete')

        embed, btns = self.__pokemonPcTradeCard(user, state.pokemonList, state.idx)

        channel: discord.TextChannel = self.bot.get_channel(state.channelId)
        if channel is None:
            await interaction.response.send_message('Error: Channel not found. The original message may have been deleted.', ephemeral=True)
            return
        message: discord.Message = await channel.fetch_message(state.messageId)

        ctx: Context = await self.bot.get_context(interaction.message)
        senderDiscord = await ctx.guild.fetch_member(int(state.senderDiscordId))

        message: discord.Message = await message.edit(
            content=f'{user.display_name} traded his {receiverPokemon.pokemonName} for {senderDiscord.display_name}\'s {senderPokemon.pokemonName}!',
            embed=embed,
            view=[]
        )
        del self.__tradeState[str(user.id)]


    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()

        if not self.__checkTradeState(user, interaction.message):
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return

        state = self.__tradeState[str(user.id)]
        state.idx = state.idx + 1

        embed, btns = self.__pokemonPcTradeCard(user, state.pokemonList, state.idx)
        message = await interaction.message.edit(embed=embed, view=btns)
        state.messageId = message.id
        self.__tradeState[str(user.id)] = state
    

    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()

        if not self.__checkTradeState(user, interaction.message):
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return

        state = self.__tradeState[str(user.id)]
        state.idx = state.idx - 1

        embed, btns = self.__pokemonPcTradeCard(user, state.pokemonList, state.idx)
        message = await interaction.message.edit(embed=embed, view=btns)
        state.messageId = message.id
        self.__tradeState[str(user.id)] = state

    
    def __pokemonPcTradeCard(self, user: discord.User, pokemonList: List[PokemonClass], idx: int):
        pokemon = pokemonList[idx]

        # Always reload pokemon data to ensure we have the latest stats from database
        pokemon.load(pokemonId=pokemon.trainerId)


        embed = createStatsEmbed(user, pokemon)

        view = View()

        if idx > 0:
            button = Button(style=ButtonStyle.gray, label='Previous', custom_id='previous')
            button.callback = self.on_prev_click_trade
            view.add_item(button)

        if idx < len(pokemonList) - 1:
            button = Button(style=ButtonStyle.gray, label="Next", custom_id='next')
            button.callback = self.on_next_click_trade
            view.add_item(button)

        button = Button(style=ButtonStyle.green, label="Offer to trade", custom_id='offer')
        button.callback = self.on_offer_trade_trade
        view.add_item(button)

        return embed, view

    @discord.ui.button(custom_id='accept', label='Accept Trade', style=ButtonStyle.green)
    async def on_trade_click_trade(self, interaction: discord.Interaction):
        await self.__on_trade_click(interaction)

    @discord.ui.button(custom_id='next', label='Next', style=ButtonStyle.gray)
    async def on_next_click_trade(self, interaction: discord.Interaction):
        await self.__on_next_click(interaction)

    @discord.ui.button(custom_id='previous', label='Previous', style=ButtonStyle.gray)
    async def on_prev_click_trade(self, interaction: discord.Interaction):
        await self.__on_prev_click(interaction)

    @discord.ui.button(custom_id='offer', label='Offer to trade', style=ButtonStyle.green)
    async def on_offer_trade_trade(self, interaction: discord.Interaction):
        await self.__on_offer_trade(interaction)