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
            str(user.id), model, message.id)

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

    def __checkUserActionState(self, user: discord.User, message: discord.Message):
        state: ActionState
        if str(user.id) not in self.__useractions.keys():
            return False
        else:
            state = self.__useractions[str(user.id)]
            if state.messageId != message.id:
                return False
        return True
