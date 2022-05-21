from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)


if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from models.location import LocationModel
from services.trainerclass import trainer as TrainerClass
from services.locationclass2 import location as LocationClass


from .abcd import MixinMeta


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

        ne = []
        sw = []
        if location.north is not None:
            ne.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬆', label=f"{location.north}"),
                self.__on_north,
            ))
        else:
            ne.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬆', label=f"--"),
                self.__on_north,
            ))
        if location.east is not None:
            ne.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='➡', label=f"{location.east}"),
                self.__on_east,
            ))
        else:
            ne.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='➡', label=f"--"),
                self.__on_east,
            ))
        if location.south is not None:
            sw.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬇', label=f"{location.south}"),
                self.__on_south,
            ))
        else:
            sw.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬇', label=f"--"),
                self.__on_south,
            ))
        if location.west is not None:
            sw.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬅', label=f"{location.west}"),
                self.__on_west,
            ))
        else:
            sw.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬅', label=f"--"),
                self.__on_west,
            ))
            # emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument='⬅️')

        message = await ctx.send(
            content=location.name,
            file=file,
            components=[ne, sw]
        )
        self.__locations[str(user.id)] = LocationState(str(user.id), location, message.id)

    async def __on_north(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        north = state.location.north

        if north is None:
            await interaction.send('You can not travel North from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(north)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        await interaction.send(f'You walked North to {north}.')
        

    async def __on_south(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        south = state.location.south

        if south is None:
            await interaction.send('You can not travel South from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(south)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        await interaction.send(f'You walked South to {south}.')

    async def __on_east(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        east = state.location.east

        if east is None:
            await interaction.send('You can not travel East from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(east)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        await interaction.send(f'You walked East to {east}.')

    async def __on_west(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        west = state.location.west

        if west is None:
            await interaction.send('You can not travel West from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(west)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        await interaction.send(f'You walked West to {west}.')


    def __checkMapState(self, user: discord.User, message: discord.Message):
        state: LocationState
        if str(user.id) not in self.__locations.keys():
            return False
        else:
            state = self.__locations[str(user.id)]
            if state.messageId != message.id:
                return False
        return True