from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord import (Embed, Member)
from discord import message
from discord.abc import User
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass

from .abcd import MixinMeta
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class TrainerState:
    discordId: str
    pokemonId: int
    messageId: int

    def __init__(self, discordId: str, pokemonId: int, messageId: int) -> None:
        self.discordId = discordId
        self.pokemonId = pokemonId
        self.messageId = messageId


class StarterMixin(MixinMeta):
    """Starter"""

    __trainers: dict[str, TrainerState] = {}


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    @_trainer.command()
    async def active(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the currect active pokemon for the trainer."""
        if user is None:
            user = ctx.author

         # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getActivePokemon()

        embed, btns = self.__pokemonStatsCard(user, pokemon, pokemon)

        message = await ctx.send(embed=embed, components=[btns])       
        self.__trainers[str(user.id)] = TrainerState(str(user.id), pokemon.trainerId, message.id)


    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the starter pokemon for the trainer."""
        if user is None:
            user = ctx.author

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()
        active = trainer.getActivePokemon()

        embed, btns = self.__pokemonStatsCard(user, pokemon, active)

        message: discord.Message = await ctx.send(embed=embed, components=[btns])
        self.__trainers[str(user.id)] = TrainerState(str(user.id), pokemon.trainerId, message.id)


    async def __on_moves_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__trainers[str(user.id)]


        # TODO: all i need is the active id, get that when the trainer is first loaded
        trainer = TrainerClass(str(user.id))
        active = trainer.getActivePokemon()

        pokemonId = state.pokemonId
        pokemon = PokemonClass(str(user.id))
        pokemon.load(pokemonId)   

        embed = createPokemonAboutEmbed(user, pokemon)

        btns = []

        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.__on_stats_click,
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
            self.__on_pokedex_click
        ))

        # Disable the "Set Active" button if the starter is currently the active pokemon
        disabled = (active is not None) and (
            pokemon.trainerId == active.trainerId)
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active",
                   custom_id='setactive', disabled=disabled),
            self.__on_set_active_click,
        ))

        message = await interaction.edit_origin(embed=embed, components=[btns])
        self.__trainers[str(user.id)] = TrainerState(str(user.id), pokemon.trainerId, message.id)
    

    async def __on_pokedex_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        await interaction.send('Pokedex is not implemented yet')


    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__trainers[str(user.id)]
        
        trainer = TrainerClass(str(user.id))
        active = trainer.getActivePokemon()

        pokemonId = state.pokemonId
        pokemon = PokemonClass(str(user.id))
        pokemon.load(pokemonId)

        embed, btns = self.__pokemonStatsCard(user, pokemon, active)

        message = await interaction.edit_origin(embed=embed, components=[btns])
        self.__trainers[str(user.id)] = TrainerState(str(user.id), pokemon.trainerId, message.id)


    def __pokemonStatsCard(self, user: discord.User, pokemon: PokemonClass, active: PokemonClass):
        embed = createStatsEmbed(user, pokemon)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Moves", custom_id='moves'),
            self.__on_moves_click
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
            self.__on_pokedex_click
        ))

        # Disable the "Set Active" button if the starter is currently the active pokemon
        # Disable the "Set Active" button if the starter is currently the active pokemon
        disabled = (active is not None) and (
            pokemon.trainerId == active.trainerId)
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active",
                   custom_id='setactive', disabled=disabled),
            self.__on_set_active_click,
        ))

        return embed, btns
    

    async def __on_set_active_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__trainers[str(user.id)]

        trainer = TrainerClass(str(user.id))

        trainer.setActivePokemon(state.pokemonId)
        pokemon = trainer.getPokemonById(state.pokemonId)

        await interaction.channel.send(f'{user.display_name} set their active pokemon to {pokemon.pokemonName.capitalize()}.')

        await self.__on_stats_click(interaction)


    def __checkTrainerState(self, user: discord.User, message: discord.Message):
        state: TrainerState
        if str(user.id) not in self.__trainers.keys():
            return False
        else:
            state = self.__trainers[str(user.id)]
            if state.messageId != message.id:
                return False
        return True