from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord_components import (ButtonStyle, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass
from services.pokedexclass import pokedex as PokedexClass
from models.state import PokemonState, DisplayCard

from .abcd import MixinMeta
from .functions import (createStatsEmbed, createPokedexEntryEmbed,
                        createPokemonAboutEmbed)



class StarterMixin(MixinMeta):
    """Starter"""


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    @_trainer.command(name='nickname', aliases=['nn'])
    async def nickName(self, ctx: commands.Context, id: int, name: str):
        user = ctx.author

        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getPokemonById(id)

        if pokemon is not None:
            pokemon.nickName = name
            pokemon.save()
            await ctx.send(f'You changed {pokemon.pokemonName.capitalize()} nickname to {name}')
        else:
            await ctx.send(f'That pokemon does not exist')
        


    @_trainer.command()
    async def active(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the currect active pokemon for the trainer."""
        if user is None:
            user = ctx.author

         # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getActivePokemon()

        state = PokemonState(str(user.id), None, DisplayCard.STATS, [pokemon], pokemon.trainerId, None)

        embed, btns = self.__pokemonSingleCard(user, state, state.card)

        message: discord.Message = await ctx.send(embed=embed, components=[btns])       
        self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, None))


    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the starter pokemon for the trainer."""
        if user is None:
            user = ctx.author

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()
        active = trainer.getActivePokemon()

        state = PokemonState(str(user.id), None, DisplayCard.STATS, [pokemon], active.trainerId, None)

        embed, btns = self.__pokemonSingleCard(user, state, state.card)

        message: discord.Message = await ctx.send(embed=embed, components=[btns])
        self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, None))


    async def __on_moves_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonSingleCard(user, state, DisplayCard.MOVES)

        message = await interaction.edit_origin(embed=embed, components=[btns])
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.MOVES, state.pokemon, state.active, None))
    

    async def __on_pokedex_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonSingleCard(user, state, DisplayCard.DEX)

        message = await interaction.edit_origin(embed=embed, components=[btns])
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.DEX, state.pokemon, state.active, None))
    

    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonSingleCard(user, state, DisplayCard.STATS)

        message = await interaction.edit_origin(embed=embed, components=[btns])
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.STATS, state.pokemon, state.active, None))
    

    async def __on_set_active_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)
        pokemon = state.pokemon[0]

        trainer = TrainerClass(str(user.id))
        trainer.setActivePokemon(pokemon.trainerId)

        await interaction.channel.send(f'{user.display_name} set their active pokemon to {pokemon.pokemonName.capitalize()}.')

        await self.__on_stats_click(interaction)



    def __pokemonSingleCard(self, user: discord.User, state: PokemonState, card: DisplayCard):
        pokemon = state.pokemon[0]
        activeId = state.active

        if DisplayCard.STATS.value == card.value:
            embed = createStatsEmbed(user, pokemon)
        elif DisplayCard.MOVES.value == card.value:
            embed = createPokemonAboutEmbed(user, pokemon)
        else:
            dex = PokedexClass.getPokedexEntry(pokemon)
            embed = createPokedexEntryEmbed(user, pokemon, dex)


        btns = []

        if DisplayCard.MOVES.value != card.value:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.green, label="Moves", custom_id='moves'),
                self.__on_moves_click
            ))
        if DisplayCard.STATS.value != card.value:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
                self.__on_stats_click,
            ))
        if DisplayCard.DEX.value != card.value:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
                self.__on_pokedex_click
            ))

        # Disable the "Set Active" button if the starter is currently the active pokemon
        # Disable the "Set Active" button if the starter is currently the active pokemon
        disabled = (activeId is not None) and (
            pokemon.trainerId == activeId)
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active",
                   custom_id='setactive', disabled=disabled),
            self.__on_set_active_click,
        ))

        return embed, btns

