from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
# from discord_components import (ButtonStyle, Button, Interaction)
from discord import ui, ButtonStyle, Button, Interaction

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands
from redbot.core.commands.context import Context

import constant
from models.location import LocationModel
from services.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass

from .abcd import MixinMeta


DiscordUser = Union[discord.Member,discord.User]


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
        author: DiscordUser = ctx.author

        if user is None:
            user = ctx.author

        # Check if author is trainer
        authorIsTrainer = user.id == author.id
        
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()

        file, btns = self.__createMapCard(location, authorIsTrainer)

        temp_message = await self.sendToLoggingChannel(f'{user.display_name} is at {location.name}', file)
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[location.name]

        desc = f'You are at {name}.' if authorIsTrainer else f'{user.display_name} is at {name}.'

        embed = discord.Embed(title = f'{name}', description = desc)
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        embed.set_image(url = attachment.url)

        message = await ctx.send(
            embed=embed,
            view=btns
        )
        # message = await ctx.send(
        #     content=location.name,
        #     file=file,
        #     view=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), location, message.id)
    

    def __createMapCard(self, location: LocationModel, authorIsTrainer = True):
        file = discord.File(f"{location.spritePath}", filename=f"{location.name}.png")

        ne = []
        sw = []
        if authorIsTrainer:
            if location.north is not None:
                north = constant.LOCATION_DISPLAY_NAMES[location.north]
                ne.append(self.client.add_callback(
                    Button(style=ButtonStyle.gray, emoji='⬆', label=f"{north}", disabled=False),
                    self.__on_north,
                ))
            else:
                ne.append(self.client.add_callback(
                    Button(style=ButtonStyle.gray, emoji='⬆', label=f"--", disabled=False),
                    self.__on_north,
                ))
            if location.east is not None:
                east = constant.LOCATION_DISPLAY_NAMES[location.east]
                ne.append(self.client.add_callback(
                    Button(style=ButtonStyle.gray, emoji='➡', label=f"{east}", disabled=False),
                    self.__on_east,
                ))
            else:
                ne.append(self.client.add_callback(
                    Button(style=ButtonStyle.gray, emoji='➡', label=f"--", disabled=False),
                    self.__on_east,
                ))
            if location.south is not None:
                south = constant.LOCATION_DISPLAY_NAMES[location.south]
                sw.append(self.client.add_callback(
                    Button(style=ButtonStyle.gray, emoji='⬇', label=f"{south}", disabled=False),
                    self.__on_south,
                ))
            else:
                sw.append(self.client.add_callback(
                    Button(style=ButtonStyle.gray, emoji='⬇', label=f"--", disabled=False),
                    self.__on_south,
                ))
            if location.west is not None:
                west = constant.LOCATION_DISPLAY_NAMES[location.west]
                sw.append(self.client.add_callback(
                    Button(style=ButtonStyle.gray, emoji='⬅', label=f"{west}", disabled=False),
                    self.__on_west,
                ))
            else:
                sw.append(self.client.add_callback(
                    Button(style=ButtonStyle.gray, emoji='⬅', label=f"--", disabled=False),
                    self.__on_west,
                ))

        btns = []
        if len(ne) > 0:
            btns.append(ne)
        if len(sw) > 0:
            btns.append(sw)


        return file, btns


    async def __on_north(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        north = state.location.north

        if north is None:
            await interaction.response.send_message('You can not travel North from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(north)
        if loc.statuscode == 96:
            await interaction.response.send_message(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.response.send_message(f'You walked North to {north}.')

        file, btns = self.__createMapCard(direction)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} walked North to {north}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked North to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.edit_original_response(
            embed=embed,
            view=btns
        )
        # message = await interaction.edit_original_response(
        #     content=f'You walked North to {north}.',
        #     file=file,
        #     view=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)
        

    async def __on_south(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        south = state.location.south

        if south is None:
            await interaction.response.send_message('You can not travel South from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(south)
        if loc.statuscode == 96:
            await interaction.response.send_message(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.response.send_message(f'You walked South to {south}.')

        file, btns = self.__createMapCard(direction)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} walked South to {south}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[direction.name]
        
        embed = discord.Embed(title = f'{name}', description = f'You walked South to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.edit_original_response(
            embed=embed,
            view=btns
        )

        # message = await interaction.edit_original_response(
        #     content=f'You walked South to {south}.',
        #     file=file,
        #     view=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)


    async def __on_east(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        east = state.location.east

        if east is None:
            await interaction.response.send_message('You can not travel East from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(east)
        if loc.statuscode == 96:
            await interaction.response.send_message(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.response.send_message(f'You walked East to {east}.')

        file, btns = self.__createMapCard(direction)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} walked East to {east}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked East to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.edit_original_response(
            embed=embed,
            view=btns
        )
        # message = await interaction.edit_original_response(
        #     content=f'You walked East to {east}.',
        #     file=file,
        #     view=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)


    async def __on_west(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        west = state.location.west

        if west is None:
            await interaction.response.send_message('You can not travel West from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(west)
        if loc.statuscode == 96:
            await interaction.response.send_message(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.response.send_message(f'You walked West to {west}.')

        file, btns = self.__createMapCard(direction)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} walked West to {west}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked West to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.edit_original_response(
            embed=embed,
            view=btns
        )
        # message = await interaction.edit_original_response(
        #     content=f'You walked West to {west}.',
        #     file=file,
        #     view=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)


    def __checkMapState(self, user: discord.User, message: discord.Message):
        state: LocationState
        if str(user.id) not in self.__locations.keys():
            return False
        else:
            state = self.__locations[str(user.id)]
            if state.messageId != message.id:
                return False
        return True