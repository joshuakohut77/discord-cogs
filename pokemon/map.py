from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING
import json
import os

import discord

from discord import ButtonStyle, Interaction
from discord.ui import Button, View

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands
from redbot.core.commands.context import Context

import constant

from models.location import LocationModel
from services.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass
from services.questclass import quests as QuestsClass
from .encounters import EncountersMixin as enc

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
    __quests_data: dict = None

    def __load_quests(self):
        """Load quests.json file"""
        if self.__quests_data is None:
            config_path = os.path.join(os.path.dirname(__file__), 'configs', 'quests.json')
            with open(config_path, 'r') as f:
                self.__quests_data = json.load(f)
        return self.__quests_data

    def __check_location_blockers(self, user_id: str, location_name: str) -> tuple[bool, str]:
        """
        Check if trainer has required key items to enter a location.
        Returns (can_travel, error_message)
        Uses the existing quests.locationBlocked() method for consistency.
        """
        quests_data = self.__load_quests()

        # Find the quest entry for this location
        location_quest = None
        for quest_id, quest_data in quests_data.items():
            if quest_data.get('name') == location_name:
                location_quest = quest_data
                break

        # If no quest entry or no blockers, allow travel
        if not location_quest or not location_quest.get('blockers'):
            return True, ""

        # Use the existing quests class to check blockers
        quest_obj = QuestsClass(user_id)
        blockers = location_quest['blockers']

        if quest_obj.locationBlocked(blockers):
            # Location is blocked - provide helpful message about what's needed
            blocker_names = [blocker.replace('_', ' ').title() for blocker in blockers]
            message = f"You cannot travel there yet. Required: {', '.join(blocker_names)}"
            return False, message

        return True, ""

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

        view = View()
        if authorIsTrainer:
            if location.north is not None:
                north = constant.LOCATION_DISPLAY_NAMES[location.north]
                button = Button(style=ButtonStyle.gray, emoji='⬆', label=f"{north}", custom_id='clickNorth', disabled=False)
                button.callback = self.on_north
                view.add_item(button)
            else:
                button = Button(style=ButtonStyle.gray, emoji='⬆', label=f"--", custom_id='clickNorth', disabled=False)
                button.callback = self.on_north
                view.add_item(button)

            if location.east is not None:
                east = constant.LOCATION_DISPLAY_NAMES[location.east]
                button = Button(style=ButtonStyle.gray, emoji='➡', label=f"{east}", custom_id='clickEast', disabled=False)
                button.callback = self.on_east
                view.add_item(button)
            else:
                button = Button(style=ButtonStyle.gray, emoji='➡', label=f"--", custom_id='clickEast', disabled=False)
                button.callback = self.on_east
                view.add_item(button)

            if location.south is not None:
                south = constant.LOCATION_DISPLAY_NAMES[location.south]
                button = Button(style=ButtonStyle.gray, emoji='⬇', label=f"{south}", custom_id='clickSouth', disabled=False)
                button.callback = self.on_south
                view.add_item(button)
            else:
                button = Button(style=ButtonStyle.gray, emoji='⬇', label=f"--", custom_id='clickSouth', disabled=False)
                button.callback = self.on_south
                view.add_item(button)

            if location.west is not None:
                west = constant.LOCATION_DISPLAY_NAMES[location.west]
                button = Button(style=ButtonStyle.gray, emoji='⬅', label=f"{west}", custom_id='clickWest', disabled=False)
                button.callback = self.on_west
                view.add_item(button)
            else:
                button = Button(style=ButtonStyle.gray, emoji='⬅', label=f"--", custom_id='clickWest', disabled=False)
                button.callback = self.on_west
                view.add_item(button)

        return file, view
    
    @discord.ui.button(custom_id='clickNorth', style=ButtonStyle.gray)
    async def on_north(self, interaction: discord.Interaction):
        await self.__on_north(interaction)

    @discord.ui.button(custom_id='clickSouth', style=ButtonStyle.gray)
    async def on_south(self, interaction: discord.Interaction):
        await self.__on_south(interaction)

    @discord.ui.button(custom_id='clickWest', style=ButtonStyle.gray)
    async def on_west(self, interaction: discord.Interaction):
        await self.__on_west(interaction)

    @discord.ui.button(custom_id='clickEast', style=ButtonStyle.gray)
    async def on_east(self, interaction: discord.Interaction):
        await self.__on_east(interaction)

    async def __on_north(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.__locations[str(user.id)]
        north = state.location.north

        if north is None:
            await interaction.response.send_message('You can not travel North from here.', ephemeral=True)
            return

        # Check if trainer has required key items to enter this location
        can_travel, blocker_message = self.__check_location_blockers(str(user.id), north)
        if not can_travel:
            await interaction.response.send_message(blocker_message, ephemeral=True)
            return

        await interaction.response.defer()

        loc = LocationClass()
        direction = loc.getLocationByName(north)
        if loc.statuscode == 96:
            await interaction.response.send_message(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        
        file, btns = self.__createMapCard(direction)

        temp_message = await self.sendToLoggingChannel(
            content=f'{user.display_name} walked North to {north}',
            file=file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked North to {name}.')
        embed.set_image(url = attachment.url)
        
        message = await interaction.message.edit(
            embed=embed,
            view=btns
        )

        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)
        

    async def __on_south(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.__locations[str(user.id)]
        south = state.location.south

        if south is None:
            await interaction.response.send_message('You can not travel South from here.', ephemeral=True)
            return

        # Check if trainer has required key items to enter this location
        can_travel, blocker_message = self.__check_location_blockers(str(user.id), south)
        if not can_travel:
            await interaction.response.send_message(blocker_message, ephemeral=True)
            return

        await interaction.response.defer()

        loc = LocationClass()
        direction = loc.getLocationByName(south)
        if loc.statuscode == 96:
            await interaction.response.send_message(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        

        file, btns = self.__createMapCard(direction)

        temp_message = await self.sendToLoggingChannel(
            content=f'{user.display_name} walked South to {south}',
            file=file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[direction.name]
        
        embed = discord.Embed(title = f'{name}', description = f'You walked South to {name}.')
        embed.set_image(url = attachment.url)
        
        # encounter = enc(MixinMeta)
        # encViewList = await encounter.get_encounters(interaction)
        
        # if encViewList is not None:
        #     for method in encViewList:
        #         btns.add_item(method)
        
        message = await interaction.message.edit(
            embed=embed,
            view=btns
        )

        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)


    async def __on_east(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.__locations[str(user.id)]
        east = state.location.east

        if east is None:
            await interaction.response.send_message('You can not travel East from here.', ephemeral=True)
            return

        # Check if trainer has required key items to enter this location
        can_travel, blocker_message = self.__check_location_blockers(str(user.id), east)
        if not can_travel:
            await interaction.response.send_message(blocker_message, ephemeral=True)
            return

        await interaction.response.defer()
        loc = LocationClass()
        direction = loc.getLocationByName(east)
        if loc.statuscode == 96:
            await interaction.response.send_message(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.response.send_message(f'You walked East to {east}.')

        file, btns = self.__createMapCard(direction)

        temp_message = await self.sendToLoggingChannel(
            content=f'{user.display_name} walked East to {east}',
            file=file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked East to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.message.edit(
            embed=embed,
            view=btns
        )

        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)


    async def __on_west(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.__locations[str(user.id)]
        west = state.location.west

        if west is None:
            await interaction.response.send_message('You can not travel West from here.', ephemeral=True)
            return

        # Check if trainer has required key items to enter this location
        can_travel, blocker_message = self.__check_location_blockers(str(user.id), west)
        if not can_travel:
            await interaction.response.send_message(blocker_message, ephemeral=True)
            return

        await interaction.response.defer()
        loc = LocationClass()
        direction = loc.getLocationByName(west)
        if loc.statuscode == 96:
            await interaction.response.send_message(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.response.send_message(f'You walked West to {west}.')

        file, btns = self.__createMapCard(direction)

        temp_message = await self.sendToLoggingChannel(
            content=f'{user.display_name} walked West to {west}',
            file=file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = constant.LOCATION_DISPLAY_NAMES[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked West to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.message.edit(
            embed=embed,
            view=btns
        )

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