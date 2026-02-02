from __future__ import annotations
from re import A
from typing import Any, Dict, List, Union, TYPE_CHECKING
import asyncio
import json
import os

import discord
from discord import (Embed, Member)
from discord import message

from discord import ButtonStyle, Interaction
from discord.ui import Button, View

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from models.location import LocationModel
from models.actionmodel import ActionModel, ActionType
from services.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass
from services.inventoryclass import inventory as InventoryClass
from services.pokeclass import Pokemon as PokemonClass
from services.questclass import quests as QuestsClass
from services.battleclass import battle as BattleClass

from .abcd import MixinMeta
from .functions import (getTypeColor)
from .helpers import (getTrainerGivenPokemonName)


class ActionState:
    discordId: str
    location: LocationModel

    channelId: int
    messageId: int

    activePokemon: PokemonClass
    wildPokemon: PokemonClass
    descLog: str

    def __init__(self, discordId: str, channelId: int, messageId: int, location: LocationModel, activePokemon: PokemonClass, wildPokemon: PokemonClass, descLog: str) -> None:
        self.discordId = discordId
        self.location = location

        self.channelId = channelId
        self.messageId = messageId

        self.activePokemon = activePokemon
        self.wildPokemon = wildPokemon
        self.descLog = descLog


class EncountersMixin(MixinMeta):
    """Encounters"""

    __useractions: dict[str, ActionState] = {}
    __quests_data: dict = None
    __gyms_data: dict = None
    __locations_data: dict = None

    def __load_quests_data(self):
        """Load quests.json file"""
        if self.__quests_data is None:
            config_path = os.path.join(os.path.dirname(__file__), 'configs', 'quests.json')
            with open(config_path, 'r') as f:
                self.__quests_data = json.load(f)
        return self.__quests_data

    def __load_gyms_data(self):
        """Load gyms.json file"""
        if self.__gyms_data is None:
            config_path = os.path.join(os.path.dirname(__file__), 'configs', 'gyms.json')
            with open(config_path, 'r') as f:
                self.__gyms_data = json.load(f)
        return self.__gyms_data

    def __load_locations_data(self):
        """Load locations.json file"""
        if self.__locations_data is None:
            config_path = os.path.join(os.path.dirname(__file__), 'configs', 'locations.json')
            with open(config_path, 'r') as f:
                self.__locations_data = json.load(f)
        return self.__locations_data

    def __get_available_quests(self, user_id: str, location_name: str) -> list:
        """
        Get available quest buttons for the current location.
        Checks if trainer has pre-requisites needed to do the quest.
        Returns list of Button objects for available quests.
        """
        quests_data = self.__load_quests_data()
        quest_buttons = []

        # Find quests for this location
        for quest_id, quest_info in quests_data.items():
            if quest_info.get('name') == location_name:
                quest_list = quest_info.get('quest', [])
                pre_requisites = quest_info.get('pre-requsites', [])

                # Add a button for each quest at this location
                for quest_name in quest_list:
                    # Check if trainer has pre-requisites
                    has_prerequisites = self.__check_prerequisites(user_id, pre_requisites)

                    button = Button(
                        style=ButtonStyle.blurple,
                        label=f"Quest: {quest_name}",
                        custom_id=f'quest_{quest_name}',
                        disabled=not has_prerequisites
                    )
                    button.callback = self.on_quest_click
                    quest_buttons.append(button)

        return quest_buttons

    def __check_prerequisites(self, user_id: str, pre_requisites: list) -> bool:
        """Check if trainer has all pre-requisites for a quest"""
        if not pre_requisites:
            return True

        quest_obj = QuestsClass(user_id)

        for prereq in pre_requisites:
            if hasattr(quest_obj.keyitems, prereq):
                if not getattr(quest_obj.keyitems, prereq):
                    return False
            else:
                return False

        return True

    def __get_gym_button(self, user_id: str, location_id: str) -> Button:
        """
        Get gym button if location has a gym and trainer meets requirements.
        Returns Button object or None.
        """
        locations_data = self.__load_locations_data()

        # Check if location has a gym
        location_info = locations_data.get(str(location_id))
        if not location_info or not location_info.get('gym', False):
            return None

        # Load gym data
        gyms_data = self.__load_gyms_data()
        gym_info = gyms_data.get(str(location_id))

        if not gym_info:
            return None

        # Check if trainer has requirements for gym leader
        requirements = gym_info['leader'].get('requirements', [])
        has_requirements = self.__check_prerequisites(user_id, requirements)

        # Create gym button (disabled if requirements not met)
        button = Button(
            style=ButtonStyle.red,
            label="Gym Challenge",
            custom_id='gym_challenge',
            disabled=not has_requirements
        )
        button.callback = self.on_gym_click

        return button

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
        methods: list[ActionModel] = location.getMethods()

        # Get quest buttons before checking if methods are empty
        quest_buttons = self.__get_available_quests(str(user.id), model.name)

        # Get gym button if location has a gym
        gym_button = self.__get_gym_button(str(user.id), model.locationId)

        # If no encounters, quests, or gym, return early
        if len(methods) == 0 and len(quest_buttons) == 0 and gym_button is None:
            await ctx.send('No encounters, quests, or gyms available at your location.')
            return

        view = View()
        for method in methods:
            button = Button(style=ButtonStyle.gray, label=f"{method.name}", custom_id=f'{method.value}', disabled=False)
            button.callback = self.on_action_encounter
            view.add_item(button)

        # Add quest buttons
        for quest_button in quest_buttons:
            view.add_item(quest_button)

        # Add gym button
        if gym_button:
            view.add_item(gym_button)

        message: discord.Message = await ctx.send(
            content="What do you want to do?",
            view=view
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, model, trainer.getActivePokemon(), None, '')

    async def get_encounters(self, interaction: Interaction):
        user = interaction.user
        trainer = TrainerClass(str(user.id))
        model = trainer.getLocation()

        location = LocationClass(str(user.id))
        methods: list[ActionModel] = location.getMethods()

        message = interaction.message
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, model, trainer.getActivePokemon(), None, '')

        if len(methods) == 0:
            return None

        viewList = []
        for method in methods:
            button = Button(style=ButtonStyle.gray, label=f"{method.name}", custom_id=f'{method.value}', disabled=False)
            button.callback = self.on_action_encounter
            viewList.append(button)

        return viewList

    # @discord.ui.button(custom_id='clickNorth', style=ButtonStyle.gray)
    async def on_action_encounter(self, interaction: discord.Interaction):
        await self.__on_action(interaction)

    async def on_quest_click(self, interaction: discord.Interaction):
        """Handle quest button clicks"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        # Extract quest name from custom_id (format: 'quest_QuestName')
        quest_name = interaction.data['custom_id'].replace('quest_', '')

        # Get location and pre-requisites
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()

        quests_data = self.__load_quests_data()
        location_quest_info = None

        for quest_id, quest_info in quests_data.items():
            if quest_info.get('name') == location.name:
                location_quest_info = quest_info
                break

        if not location_quest_info:
            await interaction.response.send_message('Quest data not found.', ephemeral=True)
            return

        # Check pre-requisites again
        pre_requisites = location_quest_info.get('pre-requsites', [])
        if not self.__check_prerequisites(str(user.id), pre_requisites):
            missing = [prereq.replace('_', ' ').title() for prereq in pre_requisites]
            await interaction.response.send_message(
                f'You do not meet the requirements for this quest. You need: {", ".join(missing)}',
                ephemeral=True
            )
            return

        # Execute the quest
        trainer.quest(quest_name)

        await interaction.response.send_message(trainer.message, ephemeral=False)

        # Disable the quest button after completion
        view = View()
        for item in interaction.message.components:
            for button in item.children:
                new_button = Button(
                    style=button.style,
                    label=button.label,
                    custom_id=button.custom_id,
                    disabled=button.custom_id == interaction.data['custom_id']
                )
                if button.custom_id == interaction.data['custom_id']:
                    new_button.callback = self.on_quest_click
                else:
                    new_button.callback = self.on_action_encounter
                view.add_item(new_button)

        await interaction.message.edit(view=view)

    async def on_gym_click(self, interaction: discord.Interaction):
        """Handle gym button clicks"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        # Get location and gym data
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()

        gyms_data = self.__load_gyms_data()
        gym_info = gyms_data.get(str(location.locationId))

        if not gym_info:
            await interaction.response.send_message('Gym data not found.', ephemeral=True)
            return

        # Check requirements again
        requirements = gym_info['leader'].get('requirements', [])
        if not self.__check_prerequisites(str(user.id), requirements):
            missing = [req.replace('_', ' ').title() for req in requirements]
            await interaction.response.send_message(
                f'You do not meet the requirements to challenge this gym. You need: {", ".join(missing)}',
                ephemeral=True
            )
            return

        # Use battle class to check gym progress
        battle = BattleClass(str(user.id), location.locationId, enemyType="gym")

        # Get remaining trainer count first
        remaining_trainers = battle.getRemainingTrainerCount()

        if remaining_trainers > 0:
            # Need to defeat trainers first
            next_trainer = battle.getNextTrainer()
            if next_trainer:
                await interaction.response.send_message(
                    f'**{gym_info["leader"]["gym-name"]}**\n\n'
                    f'You must defeat all {remaining_trainers} remaining gym trainers before you can challenge {gym_info["leader"]["gym-leader"]}.\n\n'
                    f'**Next Trainer:** {next_trainer.name}\n'
                    f'**Reward:** ${next_trainer.money}\n\n'
                    f'*[Battle system not yet implemented - this would start the trainer battle]*',
                    ephemeral=False
                )
            else:
                await interaction.response.send_message('Error getting next trainer.', ephemeral=True)
        else:
            # All trainers defeated, try to get gym leader
            gym_leader = battle.getGymLeader()

            if battle.statuscode == 420:
                # Check if already completed
                if "already completed" in battle.message.lower():
                    await interaction.response.send_message(
                        f'**{gym_info["leader"]["gym-name"]}**\n\n'
                        f'You have already defeated Gym Leader {gym_info["leader"]["gym-leader"]} and earned the {gym_info["leader"]["badge"]}!',
                        ephemeral=False
                    )
                else:
                    await interaction.response.send_message(battle.message, ephemeral=True)
                return

            if gym_leader:
                await interaction.response.send_message(
                    f'**{gym_info["leader"]["gym-name"]}**\n\n'
                    f'All gym trainers have been defeated! You are ready to challenge Gym Leader {gym_info["leader"]["gym-leader"]} for the {gym_info["leader"]["badge"]}!\n\n'
                    f'**Gym Leader:** {gym_leader.gym_leader}\n'
                    f'**Badge:** {gym_leader.badge}\n'
                    f'**Reward:** ${gym_leader.money}\n\n'
                    f'*[Battle system not yet implemented - this would start the gym leader battle]*',
                    ephemeral=False
                )
            else:
                await interaction.response.send_message(
                    f'Error: Could not load gym leader data. Status: {battle.statuscode}, Message: {battle.message}',
                    ephemeral=True
                )

    async def __on_action(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return


        await interaction.response.defer()

        location = LocationClass(str(user.id))
        methods: list[ActionModel] = location.getMethods()

        view = View()
        # btns = []
        for method in methods:
            color = ButtonStyle.gray
            if method == interaction.data['custom_id']:
                color = ButtonStyle.green
            
            # btns.append(
            #     Button(style=color, label=f"{method.name}", custom_id=f'{method.value}', disabled=True)
            # )

            button = Button(style=color, label=f"{method.name}", custom_id=f'{method.value}', disabled=True)
            # button.callback = self.on_action_encounter
            view.add_item(button)

        action: ActionModel
        for method in methods:
            if method.value == interaction.data['custom_id']:
                action = method
                break

        msg = 'Walking through tall grass...'

        if action.value == 'old-rod':
            msg = 'Fishing with an old rod...'
        elif action.value == 'good-rod':
            msg = 'Fishing with a good rod...'
        elif action.value == 'super-rod':
            msg = 'Fishing with a super rod...'
        elif action.value == 'gift':
            msg = 'Waiting to receive a gift...'
        elif action.value == 'pokeflute':
            msg = 'You played the Poké Flute!'

        await interaction.message.edit(
            content=msg,
            view=view
        )

        # await interaction.respond(type=5, content="Walking through tall grass...")

        state = self.__useractions[str(user.id)]
        method = interaction.data['custom_id']

        # if method == 'walk':
        trainer = TrainerClass(str(user.id))


        if ActionType.GIFT.value == action.type.value:
            trainer.gift()
            await interaction.channel.send(trainer.message)
            return
        
        if ActionType.QUEST.value == action.type.value:
            trainer.quest(interaction.data['custom_id'])
            await interaction.channel.send(trainer.message)
            return


        wildPokemon: PokemonClass
        # Only one can potentially trigger a pokemon encounter
        if ActionType.ONLYONE.value == action.type.value:
            wildPokemon = trainer.onlyone()
            if wildPokemon is None:
                if trainer.statuscode == 420:
                    await interaction.channel.send(trainer.message)
                else:
                    await interaction.channel.send('No pokemon encountered.')
                return


            # await interaction.channel.send(trainer.message)

        # A wild pokemon encounter
        if ActionType.ENCOUNTER.value == action.type.value:
            wildPokemon = trainer.encounter(method)
            if wildPokemon is None:
                if trainer.statuscode == 420:
                    await interaction.channel.send(trainer.message)
                else:
                    await interaction.channel.send('No pokemon encountered.')
                # await interaction.response.send_message('No pokemon encountered.')
                return

        # active = trainer.getActivePokemon()
        active = state.activePokemon
        
        # await interaction.response.send_message(f'You encountered a wild {pokemon.pokemonName}!')
        desc = f'''
{user.display_name} encountered a wild {wildPokemon.pokemonName.capitalize()}!
{user.display_name} sent out {getTrainerGivenPokemonName(active)}.
'''

        embed = self.__wildPokemonEncounter(user, wildPokemon, active, desc)

        view = View()

        button = Button(style=ButtonStyle.green, label="Fight", custom_id='fight')
        button.callback = self.on_fight_click_encounter
        view.add_item(button)

        button = Button(style=ButtonStyle.green, label="Run away", custom_id='runaway')
        button.callback = self.on_runaway_click_encounter
        view.add_item(button)

        button = Button(style=ButtonStyle.green, label="Catch", custom_id='catch')
        button.callback = self.on_catch_click_encounter
        view.add_item(button)

        message = await interaction.channel.send(
            # content=f'{user.display_name} encountered a wild {pokemon.pokemonName.capitalize()}!',
            embed=embed,
            view=view
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, active, wildPokemon, desc)


    async def __on_fight_click_encounter(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()

        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))

        # await interaction.edit_original_response(
        #     content=f'{trainer.message}',
        #     embed=embed,
        #     view=[]
        # )

        trainer.fight(state.wildPokemon)

        if trainer.statuscode == 96:
            await interaction.followup.send(trainer.message, ephemeral=True)
            return

        channel: discord.TextChannel = self.bot.get_channel(state.channelId)
        if channel is None:
            await interaction.followup.send('Error: Channel not found. The original message may have been deleted.', ephemeral=True)
            return
        message: discord.Message = await channel.fetch_message(state.messageId)

        desc = state.descLog
        desc += f'''{user.display_name} chose to fight!
{trainer.message}
'''
        active = trainer.getActivePokemon()

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, active, desc)

        # await interaction.channel.send(
        await message.edit(
            content=f'{trainer.message}',
            embed=embed,
            view=View()
        )
        del self.__useractions[str(user.id)]


    async def __on_runaway_click_encounter(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()
        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        trainer.runAway(state.wildPokemon)

        if trainer.statuscode == 96:
            await interaction.followup.send(trainer.message)
            return

        desc = state.descLog
        desc += f'''{user.display_name} chose to run away.
{trainer.message}
'''

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, state.activePokemon, desc)


        await interaction.message.edit(
            # content=f'{user.display_name} ran away from a wild {state.pokemon.pokemonName.capitalize()}!',
            embed=embed,
            view=View()
        )
        del self.__useractions[str(user.id)]
        

    async def __on_catch_click_encounter(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()
        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        items = InventoryClass(trainer.discordId)

        ctx = await self.bot.get_context(interaction.message)

        view = View()
        has_balls = False

        if items.pokeball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.POKEBALL)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Poke Ball", custom_id='pokeball')
            button.callback = self.on_throw_pokeball_encounter
            view.add_item(button)
            has_balls = True

        if items.greatball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.GREATBALL)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Great Ball", custom_id='greatball')
            button.callback = self.on_throw_pokeball_encounter
            view.add_item(button)
            has_balls = True

        if items.ultraball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.ULTRABALL)
            button = Button(style=ButtonStyle.gray, emoji=emote, label=f"Ultra Ball", custom_id='ultraball')
            button.callback = self.on_throw_pokeball_encounter
            view.add_item(button)
            has_balls = True

        if items.masterball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.MASTERBALL)
            button = Button(style=ButtonStyle.gray, emoji=emote, label=f"Master Ball", custom_id='masterball')
            button.callback = self.on_throw_pokeball_encounter
            view.add_item(button)
            has_balls = True

        if not has_balls:
            # TODO: Achievement Unlocked: No Balls
            await interaction.followup.send('You have no balls!', ephemeral=True)
            return

        button = Button(style=ButtonStyle.gray, label=f"Back", custom_id='back')
        button.callback = self.on_catch_back_encounter
        view.add_item(button)

        desc = state.descLog
        desc += f'''{user.display_name} chose to catch the wild {state.wildPokemon.pokemonName.capitalize()}.
'''

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, state.activePokemon, desc)

        message = await interaction.message.edit(
            embed=embed,
            view=view
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, state.activePokemon, state.wildPokemon, desc)


    async def __on_catch_back_encounter(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()
        # active = trainer.getActivePokemon()
        state = self.__useractions[str(user.id)]
        wildPokemon = state.wildPokemon
        active = state.activePokemon
        
        # await interaction.response.send_message(f'You encountered a wild {pokemon.pokemonName}!')
        desc = f'''
{user.display_name} encountered a wild {wildPokemon.pokemonName.capitalize()}!
{user.display_name} sent out {getTrainerGivenPokemonName(active)}.
'''

        embed = self.__wildPokemonEncounter(user, wildPokemon, active, desc)

        view = View()

        button = Button(style=ButtonStyle.green, label="Fight", custom_id='fight')
        button.callback = self.on_fight_click_encounter
        view.add_item(button)

        button = Button(style=ButtonStyle.green, label="Run away", custom_id='runaway')
        button.callback = self.on_runaway_click_encounter
        view.add_item(button)

        button = Button(style=ButtonStyle.green, label="Catch", custom_id='catch')
        button.callback = self.on_catch_click_encounter
        view.add_item(button)

        message = await interaction.message.edit(
            # content=f'{user.display_name} encountered a wild {pokemon.pokemonName.capitalize()}!',
            embed=embed,
            view=view
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, active, wildPokemon, desc)


    async def __on_throw_pokeball_encounter(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        # items = InventoryClass(trainer.discordId)

        if interaction.data['custom_id'] == 'pokeball':
            trainer.catch(state.wildPokemon, 'poke-ball')
        elif interaction.data['custom_id'] == 'greatball':
            trainer.catch(state.wildPokemon, 'great-ball')
        elif interaction.data['custom_id'] == 'ultraball':
            trainer.catch(state.wildPokemon, 'ultra-ball')
        elif interaction.data['custom_id'] == 'masterball':
            trainer.catch(state.wildPokemon, 'master-ball')

        desc = state.descLog
        desc += f'''{user.display_name} threw a {interaction.data['custom_id']}!
{trainer.message}
'''

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, state.activePokemon, desc)

        await interaction.message.edit(
            embed=embed,
            view=View()
        )
        del self.__useractions[str(user.id)]

        # Send to logging channel
        await self.sendToLoggingChannel(None, embed=embed)
    

    def __wildPokemonEncounter(self, user: discord.User, wildPokemon: PokemonClass, activePokemon: PokemonClass, descLog: str):
        stats = wildPokemon.getPokeStats()
        color = getTypeColor(wildPokemon.type1)
        # Create the embed object
        embed = discord.Embed(
            title=f"Wild {wildPokemon.pokemonName.capitalize()}",
            # description=descLog,
            color=color
        )
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.display_avatar.url))
        
        types = wildPokemon.type1
        # Pokemon are not guaranteed to have a second type.
        # Check that the second type is not set to None and is not an empty string.
        if wildPokemon.type2 is not None and wildPokemon.type2:
            types += ', ' + wildPokemon.type2

        activeTypes = activePokemon.type1
        if activePokemon.type2 is not None and activePokemon.type2:
            activeTypes += ', ' + activePokemon.type2
            
        # embed.add_field(
        #     name="Type", value=f"{types}", inline=False)
        # embed.add_field(
        #     name="Level", value=f"{pokemon.currentLevel}", inline=True)
        # embed.add_field(
        #     name="HP", value=f"{pokemon.currentHP} / {stats['hp']}", inline=True)

        activeStats = activePokemon.getPokeStats()

        embed.add_field(
            name=f"{getTrainerGivenPokemonName(activePokemon)}",
            value=f'''
Type : {activeTypes}
Level : {activePokemon.currentLevel}
HP    : {activePokemon.currentHP} / {activeStats['hp']}
            ''',
            inline=True
        )

        embed.add_field(
            name=f"{wildPokemon.pokemonName.capitalize()}",
            value=f'''
Type  : {types}
Level : {wildPokemon.currentLevel}
HP    : {wildPokemon.currentHP} / {stats['hp']}
            ''',
            inline=True
        )

        embed.set_thumbnail(url=wildPokemon.frontSpriteURL)
        embed.set_image(url = activePokemon.backSpriteURL)
        
        # activeStats = active.getPokeStats()

        embed.set_footer(text=descLog)
        return embed


#     def __wildPokemonEncounter(self, user: discord.User, pokemon: PokemonClass, active: PokemonClass, descLog: str):
#         stats = pokemon.getPokeStats()
#         color = getTypeColor(pokemon.type1)
#         # Create the embed object
#         embed = discord.Embed(
#             title=f"Wild {pokemon.pokemonName.capitalize()}",
#             description=descLog,
#             color=color
#         )
#         embed.set_author(name=f"{user.display_name}",
#                         icon_url=str(user.display_avatar.url))
        
#         types = pokemon.type1
#         # Pokemon are not guaranteed to have a second type.
#         # Check that the second type is not set to None and is not an empty string.
#         if pokemon.type2 is not None and pokemon.type2:
#             types += ', ' + pokemon.type2

#         embed.add_field(
#             name="Type", value=f"{types}", inline=False)
#         embed.add_field(
#             name="Level", value=f"{pokemon.currentLevel}", inline=True)
#         embed.add_field(
#             name="HP", value=f"{pokemon.currentHP} / {stats['hp']}", inline=True)

#         embed.set_thumbnail(url=pokemon.frontSpriteURL)
#         embed.set_image(url = active.backSpriteURL)
        
#         activeStats = active.getPokeStats()

#         embed.set_footer(text=f'''
# {active.pokemonName.capitalize()}
# Level: {active.currentLevel}
# HP: {active.currentHP} / {activeStats['hp']}
#         ''')
#         return embed


    def __checkUserActionState(self, user: discord.User, message: discord.Message):
        state: ActionState
        if str(user.id) not in self.__useractions.keys():
            return False
        else:
            state = self.__useractions[str(user.id)]
            if state.messageId != message.id:
                return False
        return True

    @discord.ui.button(custom_id='fight', label='Fight', style=ButtonStyle.green)
    async def on_fight_click_encounter(self, interaction: discord.Interaction):
        await self.__on_fight_click_encounter(interaction)

    @discord.ui.button(custom_id='runaway', label='Run away', style=ButtonStyle.green)
    async def on_runaway_click_encounter(self, interaction: discord.Interaction):
        await self.__on_runaway_click_encounter(interaction)

    @discord.ui.button(custom_id='catch', label='Catch', style=ButtonStyle.green)
    async def on_catch_click_encounter(self, interaction: discord.Interaction):
        await self.__on_catch_click_encounter(interaction)

    @discord.ui.button(custom_id='back', label='Back', style=ButtonStyle.gray)
    async def on_catch_back_encounter(self, interaction: discord.Interaction):
        await self.__on_catch_back_encounter(interaction)

    @discord.ui.button(custom_id='pokeball', label='Poke Ball', style=ButtonStyle.gray)
    async def on_throw_pokeball_encounter(self, interaction: discord.Interaction):
        await self.__on_throw_pokeball_encounter(interaction)
