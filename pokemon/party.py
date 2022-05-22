from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord_components import (ButtonStyle, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from services.pokedexclass import pokedex as PokedexClass
from models.state import PokemonState, DisplayCard

from .abcd import MixinMeta
from services.pokeclass import Pokemon as PokemonClass
from .functions import (createStatsEmbed, createPokedexEntryEmbed,
                        createPokemonAboutEmbed)



class PartyMixin(MixinMeta):
    """Party"""


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

        state = PokemonState(str(user.id), None, DisplayCard.STATS, pokeList, active.trainerId, i)
        embed, components = self.__pokemonPcCard(user, state, state.card)

        message = await ctx.send(
            embed=embed,
            components=components
        )
        self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, pokeList, active.trainerId, i))

    
    async def __on_set_active(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)
        pokemon: PokemonClass = state.pokemon[state.idx]

        trainer = TrainerClass(str(user.id))
        trainer.setActivePokemon(pokemon.trainerId)

        await interaction.channel.send(f'{user.display_name} set their active pokemon to {pokemon.pokemonName.capitalize()}.')
        
        state.active = pokemon.trainerId
        embed, components = self.__pokemonPcCard(user, state, state.card)

        message = await interaction.edit_origin(embed=embed, components=components)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
        

    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)
        state.idx = state.idx + 1

        embed, components = self.__pokemonPcCard(user, state, state.card)

        message = await interaction.edit_origin(embed=embed, components=components)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
        

    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)
        state.idx = state.idx - 1

        embed, components = self.__pokemonPcCard(user, state, state.card)

        message = await interaction.edit_origin(embed=embed, components=components)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))


    async def __on_moves_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, firstRow, secondRow = self.__pokemonPcCard(user, state, DisplayCard.MOVES)

        message = await interaction.edit_origin(embed=embed, components=[firstRow, secondRow])
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.MOVES, state.pokemon, state.active, state.idx))


    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, components = self.__pokemonPcCard(user, state, DisplayCard.STATS)

        message = await interaction.edit_origin(embed=embed, components=components)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.STATS, state.pokemon, state.active, state.idx))


    async def __on_pokemon_deposit(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return
        
        state = self.getPokemonState(user)

        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx

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
            self.setPokemonState(user, PokemonState(str(user.id), state.messageId, state.card, pokeList, state.active, state.idx))

            if pokeLength == 1:
                state.pokemon = pokeList
                state.idx = 0

                embed, components = self.__pokemonPcCard(user, state, state.card)
                message = await interaction.edit_origin(embed=embed, components=components)
                
                self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
            elif i < pokeLength - 1:
                await self.__on_next_click(interaction)
            else:
                await self.__on_prev_click(interaction)
        

    
    async def __on_pokedex_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonPcCard(user, state, DisplayCard.DEX)

        message = await interaction.edit_origin(embed=embed, components=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.DEX, state.pokemon, state.active, state.idx))



    async def __on_release_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return
        
        state = self.getPokemonState(user)

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
        self.setPokemonState(user, PokemonState(str(user.id), state.messageId, state.card, pokeList, state.active, state.idx))

        if i < pokeLength - 1:
            await self.__on_next_click(interaction)
        else:
            await self.__on_prev_click(interaction)


    def __pokemonPcCard(self, user: discord.User, state: PokemonState, card: DisplayCard):
        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx
        activeId = state.active

        pokemon: PokemonClass = pokeList[i]

        # Kind of a hack, but if the property is still set to None,
        # then we probably haven't loaded this pokemon yet.
        if pokemon.pokemonName is None:
            pokemon.load(pokemonId=pokemon.trainerId)


        embed: discord.Embed

        if DisplayCard.STATS.value == card.value:
            embed = createStatsEmbed(user, pokemon)
        elif DisplayCard.MOVES.value == card.value:
            embed = createPokemonAboutEmbed(user, pokemon)
        else:
            dex = PokedexClass.getPokedexEntry(pokemon)
            embed = createPokedexEntryEmbed(user, pokemon, dex)

        embed.set_footer(text=f'''
--------------------
{i + 1} / {pokeLength}
        ''')
        
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
        if DisplayCard.MOVES.value != card.value:
            secondRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.green, label="Moves", custom_id='moves'),
                self.__on_moves_click
            ))
        if DisplayCard.STATS.value != card.value:
            secondRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
                self.__on_stats_click
            ))
        if DisplayCard.DEX.value != card.value:
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
            Button(style=ButtonStyle.green, label="Deposit", custom_id='deposit'),
            self.__on_pokemon_deposit
        ))

        # Check that each row has btns in it.
        # It's not guaranteed that the next/previous btns will
        # always be there if there is just one pokemon in the list.
        # Returning an empty component row is a malformed request to discord.
        # Check each btn row to be safe.
        btns = []
        if len(firstRowBtns) > 0:
            btns.append(firstRowBtns)
        if len(secondRowBtns) > 0:
            btns.append(secondRowBtns)
        if len(thirdRowBtns) > 0:
            btns.append(thirdRowBtns)

        return embed, btns


