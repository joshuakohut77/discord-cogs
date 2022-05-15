from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING
import asyncio

import discord
from discord import (Embed, Member)
from discord import message
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass


from .abcd import MixinMeta
from services.pokeclass import Pokemon as PokemonClass
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class PokemonState:
    discordId: str
    messageId: int
    pokemon: list
    active: int
    idx: int

    def __init__(self, discordId: str, messageId: int, pokemon: list, active: int, idx: int) -> None:
        self.discordId = discordId
        self.messageId = messageId
        self.pokemon = pokemon
        self.active = active
        self.idx = idx


class PcMixin(MixinMeta):
    """PC"""

    __pokemon: dict[str, PokemonState] = {}

    def __checkPokemonState(self, user: discord.User, message: discord.Message):
        state: PokemonState
        if str(user.id) not in self.__pokemon.keys():
            return False
        else:
            state = self.__pokemon[str(user.id)]
            if state.messageId != message.id:
                return False
        return True


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    # TODO: Apparently there is a limit of 5 buttons at a time
    @_trainer.command()
    async def pc(self, ctx: commands.Context, user: Union[discord.Member,discord.User] = None):
        # author: Union[discord.Member,discord.User] = ctx.author

        if user is None:
            user = ctx.author

        # def nextBtnClick():
        #     return lambda x: x.custom_id == "next" or x.custom_id == 'previous' or x.custom_id == 'stats' or x.custom_id == 'pokedex' or x.custom_id == 'active'

        trainer = TrainerClass(str(user.id))
        pokeList = trainer.getPokemon()
        # TODO: we should just get the ids since that's all we need
        active = trainer.getActivePokemon()
        # starter = trainer.getStarterPokemon()

        # interaction: Interaction = None
        pokeLength = len(pokeList)
        i = 0

        if pokeLength == 0:
            await ctx.reply(content=f'{user.display_name} does not have any Pokemon.')
            return

        pokemon: PokemonClass = pokeList[i]
        embed = createPokemonAboutEmbed(user, pokemon)
        
        firstRowBtns = []
        if i > 0:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'),
                self.on_prev_click
            ))
        if i < pokeLength - 1:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
                self.on_next_click
            ))

        secondRowBtns = []
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.on_stats_click
        ))
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
            self.on_pokedex_click
        ))

        activeDisabled = (active is not None) and (pokemon.trainerId == active.trainerId)
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=activeDisabled),
            self.on_set_active
        ))
        
        # TODO: need to add the release button somewhere
        # # releaseDisabled = (active is not None and pokemon.id == active.id) or (starter is not None and pokemon.id == starter.id)
        # btns.append(Button(style=ButtonStyle.red, label="Release", custom_id='release'))

        # if interaction is None:
        message = await ctx.send(
            embed=embed,
            components=[firstRowBtns, secondRowBtns]
        )
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, pokeList, active.trainerId, i)
        # interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
        # else:
        #     await interaction.edit_origin(
        #         embed=embed,
        #         # file=file,
        #         components=[firstRowBtns, secondRowBtns]
        #     )
        #     interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
        
        # # Users who are not the author cannot click other users buttons
        # if interaction.user.id != author.id:
        #     await interaction.send('This is not for you.')
        #     return

        # if interaction.custom_id == 'next':
        #     i = i + 1
        # if (interaction.custom_id == 'previous'):
        #     i = i - 1
        # if interaction.custom_id == 'active':
        #     res = trainer.setActivePokemon(pokemon.trainerId)
        #     await interaction.send(content=f'{res}')
        # if interaction.custom_id == 'stats':
        #     await interaction.send('Not implemented')
        # if interaction.custom_id == 'pokedex':
        #     await interaction.send('Not implemented')

    
    async def on_set_active(self, interaction: Interaction):
        user = interaction.user

        state = self.__pokemon[str(user.id)]
        pokemon: PokemonClass = state.pokemon[state.idx]

        trainer = TrainerClass(str(user.id))
        trainer.setActivePokemon(pokemon.trainerId)

        message = await interaction.channel.send(f'{user.display_name} set their active pokemon to {pokemon.pokemonName}.')

        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, pokemon.trainerId, state.idx)
        

    async def on_next_click(self, interaction: Interaction):
        user = interaction.user

        state = self.__pokemon[str(user.id)]
        state.idx = state.idx + 1

        embed, btns = self.pokemonCard(user, state)

        message = await interaction.edit_origin(embed=embed, components=btns)
        
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)
        

    async def on_prev_click(self, interaction: Interaction):
        user = interaction.user

        state = self.__pokemon[str(user.id)]
        state.idx = state.idx - 1

        embed, btns = self.pokemonCard(user, state)

        message = await interaction.edit_origin(embed=embed, components=btns)
        
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)


    async def on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__pokemon[str(user.id)]

        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx
        activeId = state.active
        # pokemon = PokemonClass(str(user.id))
        # pokemon.load(currentPokemon.)        

        # trainer = TrainerClass(str(user.id))
        # pokemon = trainer.getStarterPokemon()

        pokemon: PokemonClass = pokeList[i]
        embed = createStatsEmbed(user, pokemon)
        
        firstRowBtns = []
        if i > 0:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'),
                self.on_prev_click
            ))
        if i < pokeLength - 1:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
                self.on_next_click
            ))

        secondRowBtns = []
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.on_stats_click
        ))
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
            self.on_pokedex_click
        ))

        activeDisabled = (activeId is not None) and (pokemon.trainerId == activeId)
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=activeDisabled),
            self.on_set_active
        ))

        message = await interaction.edit_origin(embed=embed, components=[firstRowBtns, secondRowBtns])
        
        self.__pokemon[str(user.id)] = PokemonState(str(user.id), message.id, state.pokemon, state.active, state.idx)



    async def on_pokedex_click(self, interaction: Interaction):
        pass


    async def pokemonCard(self, user: discord.User, state: PokemonState):
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
                self.on_prev_click
            ))
        if i < pokeLength - 1:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
                self.on_next_click
            ))

        secondRowBtns = []
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.on_stats_click
        ))
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
            self.on_pokedex_click
        ))

        activeDisabled = (activeId is not None) and (pokemon.trainerId == activeId)
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=activeDisabled),
            self.on_set_active
        ))
        return embed, [firstRowBtns, secondRowBtns]


    # # TODO: Apparently there is a limit of 5 buttons at a time
    # @_trainer.command()
    # async def pc(self, ctx: commands.Context, user: Union[discord.Member,discord.User] = None):
    #     author: Union[discord.Member,discord.User] = ctx.author

    #     if user is None:
    #         user = ctx.author

    #     def nextBtnClick():
    #         return lambda x: x.custom_id == "next" or x.custom_id == 'previous' or x.custom_id == 'stats' or x.custom_id == 'pokedex' or x.custom_id == 'active'

    #     trainer = TrainerClass(str(user.id))
    #     pokeList = trainer.getPokemon()

    #     # TODO: we should just get the ids since that's all we need
    #     active = trainer.getActivePokemon()
    #     # starter = trainer.getStarterPokemon()

    #     interaction: Interaction = None
    #     pokeLength = len(pokeList)
    #     i = 0

    #     if pokeLength == 0:
    #         await ctx.reply(content=f'{user.display_name} does not have any Pokemon.')
    #         return

    #     # TODO: there is a better way to do this that doesn't involve a loop
    #     #       discord-components gives an example use case
    #     #       https://github.com/kiki7000/discord.py-components/blob/master/examples/paginator.py
    #     while True:
    #         try:
    #             pokemon: PokemonClass = pokeList[i]
    #             embed = createPokemonAboutEmbed(user, pokemon)
                
    #             firstRowBtns = []
    #             if i > 0:
    #                 firstRowBtns.append(Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'))
    #             if i < pokeLength - 1:
    #                 firstRowBtns.append(Button(style=ButtonStyle.gray, label="Next", custom_id='next'))

    #             secondRowBtns = []
    #             secondRowBtns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
    #             secondRowBtns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))

    #             activeDisabled = (active is not None) and (pokemon.trainerId == active.trainerId)
    #             secondRowBtns.append(Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=activeDisabled))
                
    #             # TODO: need to add the release button somewhere
    #             # # releaseDisabled = (active is not None and pokemon.id == active.id) or (starter is not None and pokemon.id == starter.id)
    #             # btns.append(Button(style=ButtonStyle.red, label="Release", custom_id='release'))

    #             if interaction is None:
    #                 await ctx.send(
    #                     embed=embed,
    #                     # file=file,
    #                     components=[firstRowBtns, secondRowBtns]
    #                 )
    #                 interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
    #             else:
    #                 await interaction.edit_origin(
    #                     embed=embed,
    #                     # file=file,
    #                     components=[firstRowBtns, secondRowBtns]
    #                 )
    #                 interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                
    #             # Users who are not the author cannot click other users buttons
    #             if interaction.user.id != author.id:
    #                 await interaction.send('This is not for you.')
    #                 continue

    #             if interaction.custom_id == 'next':
    #                 i = i + 1
    #             if (interaction.custom_id == 'previous'):
    #                 i = i - 1
    #             if interaction.custom_id == 'active':
    #                 res = trainer.setActivePokemon(pokemon.trainerId)
    #                 await interaction.send(content=f'{res}')
    #                 break
    #             if interaction.custom_id == 'stats':
    #                 await interaction.send('Not implemented')
    #                 break
    #             if interaction.custom_id == 'pokedex':
    #                 await interaction.send('Not implemented')
    #                 break
    #         except asyncio.TimeoutError:
    #             break
