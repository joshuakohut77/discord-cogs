from __future__ import annotations
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

from models.location import LocationModel
from services.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass


from .abcd import MixinMeta
from services.pokeclass import Pokemon as PokemonClass
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class ActionState:
    discordId: str
    location: LocationModel
    messageId: int
    pokemon: PokemonClass

    def __init__(self, discordId: str, messageId: int, location: LocationModel, pokemon: PokemonClass) -> None:
        self.discordId = discordId
        self.location = location
        self.messageId = messageId
        self.pokemon = pokemon


class EncountersMixin(MixinMeta):
    """Encounters"""

    __useractions: dict[str, ActionState] = {}

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """

    @_trainer.command(aliases=['enc'])
    async def encounter(self, ctx: commands.Context):
        user = ctx.author

        trainer = TrainerClass(str(user.id))
        model = trainer.getLocation()

        location = LocationClass(str(user.id))
        methods = location.getMethods()

        if len(methods) == 0:
            await ctx.send('No encounters available at your location.')
            return

        btns = []
        for method in methods:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray,
                       label=f"{method}", custom_id=f'{method}'),
                self.__on_action
            ))

        message = await ctx.send(
            content="What do you want to do?",
            components=[btns]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id),message.id, model, None)

    async def __on_action(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        await interaction.respond(type=5, content="Walking through tall grass...")

        state = self.__useractions[str(user.id)]
        method = interaction.custom_id

        # if method == 'walk':
        trainer = TrainerClass(str(user.id))
        pokemon: PokemonClass = trainer.encounter(method)
        if pokemon is None:
            await interaction.send('No pokemon encountered.')
            return
        
        await interaction.send(f'You encountered a wild {pokemon.pokemonName}!')

        embed = self.__wildPokemonEncounter(user, pokemon)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Fight", custom_id='fight'),
            self.__on_fight_click,
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Run away", custom_id='runaway'),
            self.__on_runaway_click,
        ))

        message = await interaction.channel.send(
            content=f'{user.display_name} encountered a wild {pokemon.pokemonName.capitalize()}!',
            embed=embed,
            components=[btns]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.id, state.location, pokemon)


    async def __on_fight_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        await interaction.respond(type=5, content="Battling...")

        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        trainer.fight(state.pokemon)

        if trainer.statuscode == 96:
            await interaction.send(trainer.message)
            return

        embed = self.__wildPokemonEncounter(user, state.pokemon)

        btns = []

        await interaction.edit_origin(
            content=f'{trainer.message}',
            embed=embed,
            components=[]
        )
        del self.__useractions[str(user.id)]


    async def __on_runaway_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        trainer.runAway(state.pokemon)

        if trainer.statuscode == 96:
            interaction.send(trainer.message)
            return

        embed = self.__wildPokemonEncounter(user, state.pokemon)

        btns = []

        await interaction.edit_origin(
            content=f'{user.display_name} ran away from a wild {state.pokemon.pokemonName.capitalize()}!',
            embed=embed,
            components=[]
        )
        del self.__useractions[str(user.id)]
        

    
    def __wildPokemonRanAway(self, user: discord.User, pokemon: PokemonClass):
        pass

    def __wildPokemonEncounter(self, user: discord.User, pokemon: PokemonClass):
        stats = pokemon.getPokeStats()
        color = getTypeColor(pokemon.type1)
        # Create the embed object
        embed = discord.Embed(title=f"Wild {pokemon.pokemonName.capitalize()}", color=color)
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))
        
        types = pokemon.type1
        if pokemon.type2 is not None:
            types += ', ' + pokemon.type2
            
        embed.add_field(
            name="Type", value=f"{types}", inline=True)

        embed.add_field(
            name="Level", value=f"{pokemon.currentLevel}", inline=False)
        embed.add_field(
            name="HP", value=f"{pokemon.currentHP} / {stats['hp']}", inline=False)

        embed.set_thumbnail(url=pokemon.frontSpriteURL)
        return embed


    def __checkUserActionState(self, user: discord.User, message: discord.Message):
        state: ActionState
        if str(user.id) not in self.__useractions.keys():
            return False
        else:
            state = self.__useractions[str(user.id)]
            if state.messageId != message.id:
                return False
        return True