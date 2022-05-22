from __future__ import annotations
from re import L
from typing import Any, Dict, List, Union, TYPE_CHECKING
import asyncio

import discord
from discord import (Embed, Member)
from discord import message
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction, component)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from models.state import PokemonState

from .abcd import MixinMeta
from services.pokeclass2 import Pokemon as PokemonClass
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


# class PokemonState:
#     discordId: str
#     messageId: int
#     pokemon: list
#     active: int
#     idx: int

#     def __init__(self, discordId: str, messageId: int, pokemon: list, active: int, idx: int) -> None:
#         self.discordId = discordId
#         self.messageId = messageId
#         self.pokemon = pokemon
#         self.active = active
#         self.idx = idx


class PartyMixin(MixinMeta):
    """Party"""

    # __party: dict[str, PokemonState] = {}

    # def __checkPartyState(self, user: discord.User, message: discord.Message):
    #     state: PokemonState
    #     if str(user.id) not in self.__party.keys():
    #         return False
    #     else:
    #         state = self.__party[str(user.id)]
    #         if state.messageId != message.id:
    #             return False
    #     return True


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    # TODO: Apparently there is a limit of 5 buttons at a time
    @_trainer.command()
    async def party(self, ctx: commands.Context, user: Union[discord.Member,discord.User] = None):
        if user is None:
            user = ctx.author

        trainer = TrainerClass(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        # TODO: we should just get the ids since that's all we need
        active = trainer.getActivePokemon()

        pokeLength = len(pokeList)
        i = 0

        if pokeLength == 0:
            await ctx.reply(content=f'{user.display_name} does not have any Pokemon.')
            return

        state = PokemonState(str(user.id), None, pokeList, active.trainerId, i)
        embed, components = self.__pokemonStatsCard(user, state)

        # if interaction is None:
        message = await ctx.send(
            embed=embed,
            components=components
        )
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, pokeList, active.trainerId, i)

    
    async def __on_set_active(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPartyState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__pokemon[str(user.id)]
        pokemon: PokemonClass = state.pokemon[state.idx]

        trainer = TrainerClass(str(user.id))
        trainer.setActivePokemon(pokemon.trainerId)

        await interaction.channel.send(f'{user.display_name} set their active pokemon to {pokemon.pokemonName.capitalize()}.')
        
        state.active = pokemon.trainerId
        embed, components = self.__pokemonStatsCard(user, state)

        message = await interaction.edit_origin(embed=embed, components=components)
        
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)
        

    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPartyState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__pokemon[str(user.id)]
        state.idx = state.idx + 1

        embed, components = self.__pokemonStatsCard(user, state)

        message = await interaction.edit_origin(embed=embed, components=components)
        
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)
        

    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPartyState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__pokemon[str(user.id)]
        state.idx = state.idx - 1

        embed, components = self.__pokemonStatsCard(user, state)

        message = await interaction.edit_origin(embed=embed, components=components)
        
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)


    async def __on_moves_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPartyState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__pokemon[str(user.id)]

        embed, firstRow, secondRow = self.__pokemonMovesCard(user, state)

        message = await interaction.edit_origin(embed=embed, components=[firstRow, secondRow])
        
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)

    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPartyState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__pokemon[str(user.id)]

        embed, components = self.__pokemonStatsCard(user, state)

        message = await interaction.edit_origin(embed=embed, components=components)
        
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)


    async def __on_pokemon_deposit(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPartyState(user, interaction.message):
            await interaction.send('This is not for you.')
            return
        
        state = self.__pokemon[str(user.id)]

        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx
        activeId = state.active

        pokemon: PokemonClass = pokeList[i]

        trainer = TrainerClass(str(user.id))
        trainer.deposit(pokemon.trainerId)

        if trainer.statuscode == 420:
            await interaction.send(trainer.message)
            return
        
        if trainer.statuscode == 69:
            await interaction.channel.send(f'{user.display_name} returned {pokemon.pokemonName} to their pc.')

            pokeList = trainer.getPokemon(party=True)
            pokeLength = len(pokeList)
            self.__pokemon[str(user.id)] = PokemonState(str(user.id), state.messageId, pokeList, state.active, state.idx)

            if pokeLength == 1:
                state.pokemon = pokeList
                state.idx = 0

                embed, components = self.__pokemonStatsCard(user, state)
                message = await interaction.edit_origin(embed=embed, components=components)
                
                self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)
            elif i < pokeLength - 1:
                await self.__on_next_click(interaction)
            else:
                await self.__on_prev_click(interaction)
        

    

    async def __on_pokedex_click(self, interaction: Interaction):
        await interaction.send('Pokedex is not implemented yet')


    async def __on_release_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPartyState(user, interaction.message):
            await interaction.send('This is not for you.')
            return
        
        state = self.__pokemon[str(user.id)]

        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx
        activeId = state.active

        pokemon: PokemonClass = pokeList[i]

        if pokemon.trainerId == activeId:
            await interaction.send('You cannot release your active pokemon.')
            return

        trainer = TrainerClass(str(user.id))
        starter = trainer.getStarterPokemon()

        if pokemon.trainerId == starter.trainerId:
            await interaction.send('You cannot release your starter pokemon.')
            return

        pokemon.release()

        await interaction.channel.send(f'{user.display_name} released {pokemon.pokemonName.capitalize()}')
        pokeList = trainer.getPokemon()
        pokeLength = len(pokeList)
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), state.messageId, pokeList, state.active, state.idx)

        if i < pokeLength - 1:
            await self.__on_next_click(interaction)
        else:
            await self.__on_prev_click(interaction)


    def __pokemonStatsCard(self, user: discord.User, state: PokemonState):
        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx
        activeId = state.active

        pokemon: PokemonClass = pokeList[i]

        embed = createStatsEmbed(user, pokemon)
        
        firstRowBtns = []
        if i > 0:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'),
                self.__on_prev_click
            ))
        if i < pokeLength - 1:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
                self.__on_next_click
            ))

        secondRowBtns = []
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Moves", custom_id='moves'),
            self.__on_moves_click
        ))
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
            self.__on_pokedex_click
        ))

        activeDisabled = (activeId is not None) and (pokemon.trainerId == activeId)
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=activeDisabled),
            self.__on_set_active
        ))
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.red, label="Release", custom_id='release', disabled=activeDisabled),
            self.__on_release_click
        ))

        thirdRowBtns = []
        thirdRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Deposit", custom_id='deposit', disabled=activeDisabled),
            self.__on_pokemon_deposit
        ))

        # Check that each row has btns in it.
        # It's not guaranteed that the next/previous btns will
        # always be there if there is just one pokemon in the list.
        # Returning an empty component row is a malformed request to discord.
        # Check each btn row to be safe.
        components = []
        if len(firstRowBtns) > 0:
            components.append(firstRowBtns)
        if len(secondRowBtns) > 0:
            components.append(secondRowBtns)
        if len(thirdRowBtns) > 0:
            components.append(thirdRowBtns)

        return embed, components


    def __pokemonMovesCard(self, user: discord.User, state: PokemonState):
        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx
        activeId = state.active

        pokemon: PokemonClass = pokeList[i]
        embed = createPokemonAboutEmbed(user, pokemon)
        
        firstRowBtns = []
        if i > 0:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'),
                self.__on_prev_click
            ))
        if i < pokeLength - 1:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
                self.__on_next_click
            ))

        secondRowBtns = []
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.__on_stats_click
        ))
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
            self.__on_pokedex_click
        ))

        activeDisabled = (activeId is not None) and (pokemon.trainerId == activeId)
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=activeDisabled),
            self.__on_set_active
        ))
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.red, label="Release", custom_id='release', disabled=activeDisabled),
            self.__on_release_click
        ))

        return embed, firstRowBtns, secondRowBtns

