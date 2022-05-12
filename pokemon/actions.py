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

    def __init__(self, discordId: str, location: LocationModel, messageId: int) -> None:
        self.discordId = discordId
        self.location = location
        self.messageId = messageId


class ActionsMixin(MixinMeta):
    """Map"""

    __useractions: dict[str, ActionState] = {}

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """

    @_trainer.command()
    async def action(self, ctx: commands.Context):
        user = ctx.author

        trainer = TrainerClass(str(user.id))
        model = trainer.getLocation()

        location = LocationClass(str(user.id))
        methods = location.getMethods()
        # areaMethods = trainer.getAreaMethods()

        btns = []
        for method in methods:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label=f"{method}", custom_id=f'{method}'),
                self.on_action
            ))
   
        message = await ctx.send(
            content="What do you want to do?",
            components=[btns]
        )
        self.__useractions[str(user.id)] = ActionState(str(user.id), model, message.id)


    async def on_action(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__useractions[str(user.id)]
        method = interaction.custom_id

        if method == 'walk':
            trainer = TrainerClass(str(user.id))
            pokemon = trainer.encounter(method)
            if pokemon is None:
                await interaction.send('No pokemon encountered.')
            else:
                await interaction.send(f'You encountered a {pokemon.pokemonName}!')
                await interaction.user.send(f'You encountered a {pokemon.pokemonName}!')
            return


    def __checkTrainerState(self, user: discord.User, message: discord.Message):
        state: ActionState
        if str(user.id) not in self.__useractions.keys():
            return False
        else:
            state = self.__useractions[str(user.id)]
            if state.messageId != message.id:
                return False
        return True