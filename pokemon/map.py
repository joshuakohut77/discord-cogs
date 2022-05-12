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


class LocationState:
    discordId: str
    location: LocationModel
    messageId: int

    def __init__(self, discordId: str, location: LocationModel, messageId: int) -> None:
        self.discordId = discordId
        self.location = location
        self.messageId = messageId


class MapMixin(MixinMeta):
    """Map"""

    __locations: dict[str, LocationState] = {}

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """

    @_trainer.command()
    async def map(self, ctx: commands.Context, user: discord.User = None):
        if user is None:
            user = ctx.author

        
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()

        file = discord.File(f"{location.spritePath}", filename=f"{location.name}.png")

        btns = []
        if location.north is not None:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬆', label=f"{location.north}"),
                self.on_north,
            ))
        if location.south is not None:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬇', label=f"{location.south}"),
                self.on_south,
            ))
        if location.east is not None:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='➡', label=f"{location.east}"),
                self.on_east,
            ))
            # emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument='⬅️')
        if location.west is not None:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬅', label=f"{location.west}"),
                self.on_west,
            ))
            # emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument='⬅️')

        message = await ctx.send(
            content=location.name,
            file=file,
            components=[btns]
        )
        self.__locations[str(user.id)] = LocationState(str(user.id), location, message.id)

    async def on_north(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        north = state.location.north

        loc = LocationClass()
        direction = loc.getLocationByName(north)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        await interaction.respond(f'You walked to {north}')
        

    async def on_south(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        south = state.location.south

        loc = LocationClass()
        direction = loc.getLocationByName(south)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        await interaction.respond(f'You walked to {south}')

    async def on_east(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        east = state.location.east
        await interaction.send(east)

        loc = LocationClass()
        direction = loc.getLocationByName(east)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        await interaction.respond(f'You walked to {east}')

    async def on_west(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        west = state.location.west

        loc = LocationClass()
        direction = loc.getLocationByName(west)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        await interaction.respond(f'You walked to {west}')


    def __checkTrainerState(self, user: discord.User, message: discord.Message):
        state: LocationState
        if str(user.id) not in self.__locations.keys():
            return False
        else:
            state = self.__locations[str(user.id)]
            if state.messageId != message.id:
                return False
        return True