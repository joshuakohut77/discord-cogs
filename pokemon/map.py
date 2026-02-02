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

        # UPDATED: Pass user_id to enable action buttons
        file, btns = self.__createMapCard(location, authorIsTrainer, str(user.id) if authorIsTrainer else None)

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
        self.__locations[str(user.id)] = LocationState(str(user.id), location, message.id)
    

    def __createMapCard(self, location: LocationModel, authorIsTrainer = True, user_id: str = None):
        """Create map card with ALL direction buttons (disabled if unavailable) AND action buttons"""
        file = discord.File(f"{location.spritePath}", filename=f"{location.name}.png")

        view = View()
        
        if authorIsTrainer:
            # ROW 0: North/South buttons - ALWAYS SHOW
            if location.north is not None:
                north = constant.LOCATION_DISPLAY_NAMES[location.north]
                button = Button(style=ButtonStyle.gray, emoji='⬆', label=f"{north[:15]}", custom_id='clickNorth', disabled=False, row=0)
                button.callback = self.on_north
                view.add_item(button)
            else:
                # Disabled button
                button = Button(style=ButtonStyle.gray, emoji='⬆', label="---", custom_id='clickNorth', disabled=True, row=0)
                view.add_item(button)

            if location.south is not None:
                south = constant.LOCATION_DISPLAY_NAMES[location.south]
                button = Button(style=ButtonStyle.gray, emoji='⬇', label=f"{south[:15]}", custom_id='clickSouth', disabled=False, row=0)
                button.callback = self.on_south
                view.add_item(button)
            else:
                # Disabled button
                button = Button(style=ButtonStyle.gray, emoji='⬇', label="---", custom_id='clickSouth', disabled=True, row=0)
                view.add_item(button)
            
            # ROW 1: East/West buttons - ALWAYS SHOW
            if location.east is not None:
                east = constant.LOCATION_DISPLAY_NAMES[location.east]
                button = Button(style=ButtonStyle.gray, emoji='➡', label=f"{east[:15]}", custom_id='clickEast', disabled=False, row=1)
                button.callback = self.on_east
                view.add_item(button)
            else:
                # Disabled button
                button = Button(style=ButtonStyle.gray, emoji='➡', label="---", custom_id='clickEast', disabled=True, row=1)
                view.add_item(button)

            if location.west is not None:
                west = constant.LOCATION_DISPLAY_NAMES[location.west]
                button = Button(style=ButtonStyle.gray, emoji='⬅', label=f"{west[:15]}", custom_id='clickWest', disabled=False, row=1)
                button.callback = self.on_west
                view.add_item(button)
            else:
                # Disabled button
                button = Button(style=ButtonStyle.gray, emoji='⬅', label="---", custom_id='clickWest', disabled=True, row=1)
                view.add_item(button)
            
            # ROW 2: Action buttons (Encounters, Quests, Gym) - only if user_id provided
            if user_id:
                # Check for encounters
                location_obj = LocationClass(user_id)
                methods = location_obj.getMethods()
                
                if len(methods) > 0:
                    enc_btn = Button(style=ButtonStyle.green, label="⚔️ Encounters", custom_id='map_encounters', row=2)
                    enc_btn.callback = self.on_map_encounters_click
                    view.add_item(enc_btn)
                
                # Check for quests
                quests_data = self.__load_quests()
                has_quests = False
                if quests_data:
                    for quest_id, quest_info in quests_data.items():
                        if quest_info.get('name') == location.name:
                            if quest_info.get('quest'):
                                has_quests = True
                                break
                
                if has_quests:
                    quest_btn = Button(style=ButtonStyle.blurple, label="📜 Quests", custom_id='map_quests', row=2)
                    quest_btn.callback = self.on_map_quests_click
                    view.add_item(quest_btn)
                
                # Check for gym
                if location.gym:
                    gym_btn = Button(style=ButtonStyle.red, label="🏛️ Gym", custom_id='map_gym', row=2)
                    gym_btn.callback = self.on_map_gym_click
                    view.add_item(gym_btn)
                
                # ROW 3: Party button
                party_btn = Button(style=ButtonStyle.primary, label="👥 Party", custom_id='map_party', row=3)
                party_btn.callback = self.on_map_party_click
                view.add_item(party_btn)

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
        
        file, btns = self.__createMapCard(direction, True, str(user.id))

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
        

        file, btns = self.__createMapCard(direction, True, str(user.id))

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

        file, btns = self.__createMapCard(direction, True, str(user.id))

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

        file, btns = self.__createMapCard(direction, True, str(user.id))

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

    async def _forward_to_encounter_handler(self, interaction: discord.Interaction):
        """Temporary - forward encounter method clicks"""
        await interaction.response.send_message(
            'Use `,trainer encounter` to access encounters.',
            ephemeral=True
        )

    async def _forward_quest_handler(self, interaction: discord.Interaction):
        """Temporary - forward quest clicks"""
        await interaction.response.send_message(
            'Use `,trainer encounter` to access quests.',
            ephemeral=True
        )

    async def _forward_gym_handler(self, interaction: discord.Interaction):
        """Temporary - forward gym clicks"""
        await interaction.response.send_message(
            'Use `,trainer encounter` to access the gym.',
            ephemeral=True
        )

    def _get_gym_button_for_location(self, user_id: str, location_id: str):
        """Helper to get gym button"""
        # Load locations and gyms data
        locations_path = os.path.join(os.path.dirname(__file__), 'configs', 'locations.json')
        with open(locations_path, 'r') as f:
            locations_data = json.load(f)
        
        location_info = locations_data.get(str(location_id))
        if not location_info or not location_info.get('gym', False):
            return None
        
        gyms_path = os.path.join(os.path.dirname(__file__), 'configs', 'gyms.json')
        with open(gyms_path, 'r') as f:
            gyms_data = json.load(f)
        
        gym_info = gyms_data.get(str(location_id))
        if not gym_info:
            return None
        
        # Check requirements
        requirements = gym_info['leader'].get('requirements', [])
        has_requirements = True
        
        if requirements:
            quest_obj = QuestsClass(user_id)
            for req in requirements:
                if hasattr(quest_obj.keyitems, req):
                    if not getattr(quest_obj.keyitems, req):
                        has_requirements = False
                        break
                else:
                    has_requirements = False
                    break
        
        button = Button(
            style=ButtonStyle.red,
            label="Gym Challenge",
            custom_id='gym_challenge',
            disabled=not has_requirements
        )
        button.callback = self._forward_gym_handler
        
        return button

    async def on_map_encounters_click(self, interaction: discord.Interaction):
        """Handle Encounters button click from map - show encounter options"""
        user = interaction.user
        
        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Get location
        trainer = TrainerClass(str(user.id))
        location_model = trainer.getLocation()
        
        # Get encounter methods
        location_obj = LocationClass(str(user.id))
        methods = location_obj.getMethods()
        
        # Get quest and gym buttons too
        from .encounters import EncountersMixin
        quest_buttons = self._get_quest_buttons_for_location(str(user.id), location_model.name)
        gym_button = self._get_gym_button_for_location(str(user.id), location_model.locationId)
        
        if len(methods) == 0 and len(quest_buttons) == 0 and gym_button is None:
            await interaction.followup.send('No encounters, quests, or gyms available.', ephemeral=True)
            return
        
        # Create encounter view (same as ,trainer encounter command)
        view = View()
        for method in methods:
            button = Button(style=ButtonStyle.gray, label=f"{method.name}", custom_id=f'{method.value}', disabled=False)
            # Note: We need to forward to encounters.py handler, but we're in map.py
            # For now, show message to use command
            button.callback = self._forward_to_encounter_handler
            view.add_item(button)
        
        # Add quest buttons
        for quest_btn in quest_buttons:
            view.add_item(quest_btn)
        
        # Add gym button
        if gym_button:
            view.add_item(gym_button)
        
        # Back button
        back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='back_to_map', row=2)
        back_btn.callback = self.on_back_to_map
        view.add_item(back_btn)
        
        message = await interaction.message.edit(
            content=f"**{constant.LOCATION_DISPLAY_NAMES.get(location_model.name, location_model.name)}**\nWhat do you want to do?",
            view=view
        )
        
        # Store state for encounter handlers
        self.__locations[str(user.id)].messageId = message.id

    def _get_quest_buttons_for_location(self, user_id: str, location_name: str) -> list:
        """Helper to get quest buttons - similar to encounters.py version"""
        quests_data = self.__load_quests()
        quest_buttons = []

        for quest_id, quest_info in quests_data.items():
            if quest_info.get('name') == location_name:
                quest_list = quest_info.get('quest', [])
                pre_requisites = quest_info.get('pre-requsites', [])

                for quest_name in quest_list:
                    # Check prerequisites
                    quest_obj = QuestsClass(user_id)
                    has_prerequisites = True
                    
                    for prereq in pre_requisites:
                        if hasattr(quest_obj.keyitems, prereq):
                            if not getattr(quest_obj.keyitems, prereq):
                                has_prerequisites = False
                                break
                        else:
                            has_prerequisites = False
                            break

                    button = Button(
                        style=ButtonStyle.blurple,
                        label=f"Quest: {quest_name}",
                        custom_id=f'quest_{quest_name}',
                        disabled=not has_prerequisites
                    )
                    # Note: callback would need to forward to encounters.py
                    button.callback = self._forward_quest_handler
                    quest_buttons.append(button)

        return quest_buttons

    async def on_map_quests_click(self, interaction: discord.Interaction):
        """Handle Quests button from map - show quests"""
        user = interaction.user
        
        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()
        
        quest_buttons = self._get_quest_buttons_for_location(str(user.id), location.name)
        
        if len(quest_buttons) == 0:
            await interaction.followup.send('No quests available here.', ephemeral=True)
            return
        
        # Show quests
        view = View()
        for quest_btn in quest_buttons:
            view.add_item(quest_btn)
        
        # Back button
        back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='back_to_map', row=1)
        back_btn.callback = self.on_back_to_map
        view.add_item(back_btn)
        
        await interaction.message.edit(
            content=f"**{constant.LOCATION_DISPLAY_NAMES.get(location.name, location.name)}**\nAvailable Quests:",
            view=view
        )

    async def on_gym_battle_from_map(self, interaction: discord.Interaction):
        """Forward gym battle to encounters.py - tell user to use encounter command for now"""
        await interaction.response.send_message(
            'Gym battle integration in progress. Please use `,trainer encounter` then click "Gym Challenge" for now.',
            ephemeral=True
        )

    async def on_map_gym_click(self, interaction: discord.Interaction):
        """Handle Gym button from map - show gym battle options"""
        user = interaction.user
        
        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Load gym data
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()
        
        gyms_path = os.path.join(os.path.dirname(__file__), 'configs', 'gyms.json')
        with open(gyms_path, 'r') as f:
            gyms_data = json.load(f)
        
        gym_info = gyms_data.get(str(location.locationId))
        
        if not gym_info:
            await interaction.followup.send('No gym at this location.', ephemeral=True)
            return
        
        # Check requirements
        requirements = gym_info['leader'].get('requirements', [])
        has_requirements = True
        
        if requirements:
            quest_obj = QuestsClass(str(user.id))
            for req in requirements:
                if hasattr(quest_obj.keyitems, req):
                    if not getattr(quest_obj.keyitems, req):
                        has_requirements = False
                        break
                else:
                    has_requirements = False
                    break
        
        if not has_requirements:
            missing = [req.replace('_', ' ').title() for req in requirements]
            await interaction.followup.send(
                f'You do not meet the requirements for this gym. You need: {", ".join(missing)}',
                ephemeral=True
            )
            return
        
        # Import battle class to check progress
        from services.battleclass import battle as BattleClass
        battle = BattleClass(str(user.id), location.locationId, enemyType="gym")
        remaining_trainers = battle.getRemainingTrainerCount()
        
        if remaining_trainers > 0:
            # Show trainer battle options
            next_trainer = battle.getNextTrainer()
            if next_trainer:
                view = View()
                
                # Auto Battle button
                auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Battle", custom_id='gym_battle_auto_map')
                auto_button.callback = self.on_gym_battle_from_map
                view.add_item(auto_button)
                
                # Manual Battle button
                manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Battle", custom_id='gym_battle_manual_map')
                manual_button.callback = self.on_gym_battle_from_map
                view.add_item(manual_button)
                
                # Back button
                back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='back_to_map')
                back_btn.callback = self.on_back_to_map
                view.add_item(back_btn)

                await interaction.message.edit(
                    content=f'**{gym_info["leader"]["gym-name"]}**\n\n'
                            f'Trainers Remaining: {remaining_trainers}\n\n'
                            f'**Next Opponent:** {next_trainer.name}\n'
                            f'**Reward:** ${next_trainer.money}\n\n'
                            f'Choose your battle mode:',
                    view=view
                )
            else:
                await interaction.followup.send('Error getting next trainer.', ephemeral=True)
        else:
            # Show gym leader options
            gym_leader = battle.getGymLeader()
            
            if battle.statuscode == 420:
                await interaction.followup.send(battle.message, ephemeral=True)
                return
            
            if gym_leader:
                view = View()
                
                # Auto Battle button
                auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Battle Leader", custom_id='gym_leader_battle_auto_map')
                auto_button.callback = self.on_gym_battle_from_map
                view.add_item(auto_button)
                
                # Manual Battle button
                manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Battle Leader", custom_id='gym_leader_battle_manual_map')
                manual_button.callback = self.on_gym_battle_from_map
                view.add_item(manual_button)
                
                # Back button
                back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='back_to_map')
                back_btn.callback = self.on_back_to_map
                view.add_item(back_btn)

                await interaction.message.edit(
                    content=f'**{gym_info["leader"]["gym-name"]}**\n\n'
                            f'All gym trainers defeated!\n\n'
                            f'**Gym Leader:** {gym_leader.name}\n'
                            f'**Badge:** {gym_leader.badge}\n'
                            f'**Reward:** ${gym_leader.money}\n\n'
                            f'Choose your battle mode:',
                    view=view
                )
            else:
                await interaction.followup.send('Error loading gym leader.', ephemeral=True)


    async def on_map_party_click(self, interaction: discord.Interaction):
        """Handle Party button from map - show party"""
        user = interaction.user
        
        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Show simplified party view
        trainer = TrainerClass(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        active = trainer.getActivePokemon()

        if len(pokeList) == 0:
            await interaction.followup.send('You do not have any Pokemon.', ephemeral=True)
            return

        # Create party display
        embed = discord.Embed(
            title="👥 Your Party",
            description="Your Pokemon team",
            color=discord.Color.blue()
        )
        
        # Show all party Pokemon
        for i, poke in enumerate(pokeList, 1):
            poke.load(pokemonId=poke.trainerId)
            stats = poke.getPokeStats()
            is_active = "⭐" if poke.trainerId == active.trainerId else ""
            status = "💚" if poke.currentHP > 0 else "💀"
            
            poke_name = poke.nickName if poke.nickName else poke.pokemonName.capitalize()
            
            embed.add_field(
                name=f"{i}. {poke_name} {is_active}",
                value=f"{status} Lv.{poke.currentLevel} | HP: {poke.currentHP}/{stats['hp']}",
                inline=False
            )
        
        # Back to map button
        view = View()
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='back_to_map')
        map_btn.callback = self.on_back_to_map
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_back_to_map(self, interaction: discord.Interaction):
        """Handle Back to Map button - recreate map view"""
        user = interaction.user
        
        if not self.__checkMapState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Get current location
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()
        
        # Recreate map card with action buttons
        file, btns = self.__createMapCard(location, True, str(user.id))
        
        temp_message = await self.sendToLoggingChannel(f'{user.display_name} viewing map', file)
        attachment = temp_message.attachments[0]
        
        name = constant.LOCATION_DISPLAY_NAMES[location.name]
        embed = discord.Embed(title=f'{name}', description=f'You are at {name}.')
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        embed.set_image(url=attachment.url)
        
        await interaction.message.edit(embed=embed, view=btns)

    def __checkMapState(self, user: discord.User, message: discord.Message):
        state: LocationState
        if str(user.id) not in self.__locations.keys():
            return False
        else:
            state = self.__locations[str(user.id)]
            if state.messageId != message.id:
                return False
        return True