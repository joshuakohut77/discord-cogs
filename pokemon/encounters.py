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
from services.encounterclass import encounter as EncounterClass

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

class BattleState:
    """Track ongoing manual battle state"""
    def __init__(self, user_id: str, channel_id: int, message_id: int, 
                 player_pokemon: PokemonClass, enemy_pokemon: PokemonClass,
                 enemy_name: str, trainer_model, battle_manager):
        self.user_id = user_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.player_pokemon = player_pokemon
        self.enemy_pokemon = enemy_pokemon
        self.enemy_name = enemy_name
        self.trainer_model = trainer_model  # TrainerBattleModel or GymLeaderModel
        self.battle_manager = battle_manager  # BattleClass instance
        self.battle_log = []
        self.turn_number = 1


class EncountersMixin(MixinMeta):
    """Encounters"""

    __useractions: dict[str, ActionState] = {}
    __quests_data: dict = None
    __gyms_data: dict = None
    __locations_data: dict = None
    __battle_states: dict[str, BattleState] = {}

    def __create_battle_embed(self, user: discord.User, battle_state: BattleState) -> discord.Embed:
        """Create an embed showing the current battle state"""
        player_poke = battle_state.player_pokemon
        enemy_poke = battle_state.enemy_pokemon
        
        player_stats = player_poke.getPokeStats()
        enemy_stats = enemy_poke.getPokeStats()
        
        # Calculate HP percentages for visual bar
        player_hp_pct = (player_poke.currentHP / player_stats['hp']) * 100 if player_stats['hp'] > 0 else 0
        enemy_hp_pct = (enemy_poke.currentHP / enemy_stats['hp']) * 100 if enemy_stats['hp'] > 0 else 0
        
        # Create HP bar visualization
        def make_hp_bar(percentage):
            filled = int(percentage / 10)
            empty = 10 - filled
            return '█' * filled + '░' * empty
        
        embed = discord.Embed(
            title=f"⚔️ Battle: {user.display_name} vs {battle_state.enemy_name}",
            description=f"**Turn {battle_state.turn_number}**\nChoose your move!",
            color=discord.Color.red()
        )
        
        # Player Pokemon info
        player_types = player_poke.type1
        if player_poke.type2:
            player_types += f", {player_poke.type2}"
        
        embed.add_field(
            name=f"💚 Your {player_poke.pokemonName.capitalize()} (Lv.{player_poke.currentLevel})",
            value=f"**HP:** {player_poke.currentHP}/{player_stats['hp']} {make_hp_bar(player_hp_pct)}\n"
                f"**Type:** {player_types}",
            inline=False
        )
        
        # Enemy Pokemon info
        enemy_types = enemy_poke.type1
        if enemy_poke.type2:
            enemy_types += f", {enemy_poke.type2}"
        
        embed.add_field(
            name=f"❤️ Enemy {enemy_poke.pokemonName.capitalize()} (Lv.{enemy_poke.currentLevel})",
            value=f"**HP:** {enemy_poke.currentHP}/{enemy_stats['hp']} {make_hp_bar(enemy_hp_pct)}\n"
                f"**Type:** {enemy_types}",
            inline=False
        )
        
        # Battle log (last 5 messages)
        if battle_state.battle_log:
            log_text = "\n".join(battle_state.battle_log[-5:])
            embed.add_field(
                name="📜 Battle Log",
                value=log_text[:1024],  # Discord field limit
                inline=False
            )
        
        embed.set_thumbnail(url=enemy_poke.frontSpriteURL)
        embed.set_image(url=player_poke.backSpriteURL)
        
        return embed

    def __create_move_buttons(self, battle_state: BattleState) -> View:
        """Create buttons for each of the player's Pokemon's moves"""
        view = View()
        moves = battle_state.player_pokemon.getMoves()
        
        # Load move data to show power/type
        try:
            p = os.path.join(os.path.dirname(__file__), 'configs', 'moves.json')
            with open(p, 'r') as f:
                moves_config = json.load(f)
        except:
            moves_config = {}
        
        for i, move_name in enumerate(moves):
            if move_name and move_name.lower() != 'none':
                move_data = moves_config.get(move_name, {})
                power = move_data.get('power', 0)
                move_type = move_data.get('moveType', '???')
                
                # Create button label with move info
                if power and power > 0:
                    label = f"{move_name.replace('-', ' ').title()} ({move_type.title()}, PWR:{power})"
                else:
                    label = f"{move_name.replace('-', ' ').title()} ({move_type.title()})"
                
                button = Button(
                    style=ButtonStyle.primary,
                    label=label[:80],  # Discord label limit
                    custom_id=f'battle_move_{move_name}'
                )
                button.callback = self.on_battle_move_click
                view.add_item(button)
        
        return view

    async def on_battle_move_click(self, interaction: discord.Interaction):
        """Handle when player selects a move during manual battle"""
        user = interaction.user
        user_id = str(user.id)
        
        if user_id not in self.__battle_states:
            await interaction.response.send_message('Battle state not found.', ephemeral=True)
            return
        
        battle_state = self.__battle_states[user_id]
        
        # Verify this is the correct message
        if battle_state.message_id != interaction.message.id:
            await interaction.response.send_message('This is not the current battle.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Extract move name from custom_id
        move_name = interaction.data['custom_id'].replace('battle_move_', '')
        
        # Store HP before battle for damage calculation
        player_hp_before = battle_state.player_pokemon.currentHP
        enemy_hp_before = battle_state.enemy_pokemon.currentHP
        
        # WORKAROUND: Since manual mode doesn't apply damage, we'll use auto mode
        # but capture the state after just one exchange
        # Create a fresh encounter for this turn
        enc = EncounterClass(battle_state.player_pokemon, battle_state.enemy_pokemon)
        
        # Use auto battle but we'll manually track what happened
        # The issue is that manual mode doesn't work, so let's do our own calculation
        import random
        import json
        import os
        
        # Load moves config to calculate damage
        moves_path = os.path.join(os.path.dirname(__file__), 'configs', 'moves.json')
        with open(moves_path, 'r') as f:
            moves_config = json.load(f)
        
        # Load type effectiveness
        type_path = os.path.join(os.path.dirname(__file__), 'configs', 'typeEffectiveness.json')
        with open(type_path, 'r') as f:
            type_effectiveness = json.load(f)
        
        # Get player's move data
        player_move = moves_config.get(move_name, {})
        player_power = player_move.get('power', 0)
        player_accuracy = player_move.get('accuracy', 100)
        player_move_type = player_move.get('moveType', 'normal')
        damage_class = player_move.get('damage_class', 'physical')
        
        # Calculate if player's move hits
        player_hit = random.randint(1, 100) <= player_accuracy
        player_damage = 0
        
        if player_hit and player_power and player_power > 0:
            # Get stats
            player_stats = battle_state.player_pokemon.getPokeStats()
            enemy_stats = battle_state.enemy_pokemon.getPokeStats()
            
            # Determine attack and defense stats
            if damage_class == 'physical':
                attack = player_stats['attack']
                defense = enemy_stats['defense']
            else:
                attack = player_stats['special-attack']
                defense = enemy_stats['special-defense']
            
            # Calculate base damage
            level = battle_state.player_pokemon.currentLevel
            base_damage = ((2 * level / 5 + 2) * player_power * (attack / defense) / 50 + 2)
            
            # Apply random multiplier
            random_mult = random.uniform(0.85, 1.0)
            
            # STAB (Same Type Attack Bonus)
            stab = 1.5 if (player_move_type == battle_state.player_pokemon.type1 or 
                        player_move_type == battle_state.player_pokemon.type2) else 1.0
            
            # Type effectiveness
            defending_type = battle_state.enemy_pokemon.type1
            effectiveness = type_effectiveness.get(player_move_type, {}).get(defending_type, 1.0)
            
            # Final damage
            player_damage = int(base_damage * random_mult * stab * effectiveness)
            
            # Apply damage
            new_enemy_hp = max(0, battle_state.enemy_pokemon.currentHP - player_damage)
            battle_state.enemy_pokemon.currentHP = new_enemy_hp
        
        # Now enemy attacks back (if still alive)
        enemy_damage = 0
        if battle_state.enemy_pokemon.currentHP > 0:
            # Enemy picks random move
            enemy_moves = [m for m in battle_state.enemy_pokemon.getMoves() if m and m.lower() != 'none']
            if enemy_moves:
                enemy_move_name = random.choice(enemy_moves)
                enemy_move = moves_config.get(enemy_move_name, {})
                enemy_power = enemy_move.get('power', 0)
                enemy_accuracy = enemy_move.get('accuracy', 100)
                enemy_move_type = enemy_move.get('moveType', 'normal')
                enemy_damage_class = enemy_move.get('damage_class', 'physical')
                
                # Calculate if enemy hits
                enemy_hit = random.randint(1, 100) <= enemy_accuracy
                
                if enemy_hit and enemy_power and enemy_power > 0:
                    enemy_stats = battle_state.enemy_pokemon.getPokeStats()
                    player_stats = battle_state.player_pokemon.getPokeStats()
                    
                    if enemy_damage_class == 'physical':
                        attack = enemy_stats['attack']
                        defense = player_stats['defense']
                    else:
                        attack = enemy_stats['special-attack']
                        defense = player_stats['special-defense']
                    
                    level = battle_state.enemy_pokemon.currentLevel
                    base_damage = ((2 * level / 5 + 2) * enemy_power * (attack / defense) / 50 + 2)
                    random_mult = random.uniform(0.85, 1.0)
                    
                    stab = 1.5 if (enemy_move_type == battle_state.enemy_pokemon.type1 or 
                                enemy_move_type == battle_state.enemy_pokemon.type2) else 1.0
                    
                    defending_type = battle_state.player_pokemon.type1
                    effectiveness = type_effectiveness.get(enemy_move_type, {}).get(defending_type, 1.0)
                    
                    enemy_damage = int(base_damage * random_mult * stab * effectiveness)
                    
                    new_player_hp = max(0, battle_state.player_pokemon.currentHP - enemy_damage)
                    battle_state.player_pokemon.currentHP = new_player_hp
        
        # Create battle log
        log_lines = []
        log_lines.append(f"**Turn {battle_state.turn_number}:**")
        
        # Player's action
        if player_hit and player_damage > 0:
            log_lines.append(f"• {battle_state.player_pokemon.pokemonName.capitalize()} used {move_name.replace('-', ' ').title()}! Dealt {player_damage} damage!")
        elif player_hit and player_power == 0:
            log_lines.append(f"• {battle_state.player_pokemon.pokemonName.capitalize()} used {move_name.replace('-', ' ').title()}! (Status move)")
        else:
            log_lines.append(f"• {battle_state.player_pokemon.pokemonName.capitalize()} used {move_name.replace('-', ' ').title()} but it missed!")
        
        # Enemy's action
        if battle_state.enemy_pokemon.currentHP > 0:
            if enemy_damage > 0:
                log_lines.append(f"• Enemy {battle_state.enemy_pokemon.pokemonName.capitalize()} attacked! Dealt {enemy_damage} damage!")
            else:
                log_lines.append(f"• Enemy {battle_state.enemy_pokemon.pokemonName.capitalize()} attacked but missed!")
        
        battle_state.battle_log = ["\n".join(log_lines)]
        battle_state.turn_number += 1
        
        # Check for battle end
        if battle_state.enemy_pokemon.currentHP <= 0:
            # Save the player's pokemon HP to database before victory
            battle_state.player_pokemon.save()
            await self.__handle_gym_battle_victory(interaction, battle_state)
            del self.__battle_states[user_id]
            return
        
        elif battle_state.player_pokemon.currentHP <= 0:
            # Save the player's pokemon HP to database before defeat
            battle_state.player_pokemon.save()
            await self.__handle_gym_battle_defeat(interaction, battle_state)
            del self.__battle_states[user_id]
            return
        
        # Battle continues - update display
        embed = self.__create_battle_embed(user, battle_state)
        view = self.__create_move_buttons(battle_state)
        
        await interaction.message.edit(embed=embed, view=view)
    
    
    async def __handle_gym_battle_victory(self, interaction: discord.Interaction, battle_state: BattleState):
        """Handle when player wins a gym battle"""
        trainer_model = battle_state.trainer_model
        battle_manager = battle_state.battle_manager
        
        # Award rewards
        if hasattr(trainer_model, 'gym_leader'):  # It's a gym leader
            battle_manager.gymLeaderVictory(trainer_model)
            
            embed = discord.Embed(
                title="🏆 VICTORY!",
                description=f"You defeated Gym Leader {trainer_model.gym_leader}!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="💰 Rewards",
                value=f"**Badge:** {trainer_model.badge}\n**Money:** ${trainer_model.money}",
                inline=False
            )
        else:  # It's a trainer
            battle_manager.battleVictory(trainer_model)
            
            embed = discord.Embed(
                title="🎉 VICTORY!",
                description=f"You defeated {trainer_model.name}!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Rewards",
                value=f"**Money:** ${trainer_model.money}",
                inline=False
            )
        
        # Add battle summary
        if battle_state.battle_log:
            log_text = "\n".join(battle_state.battle_log[-3:])
            embed.add_field(name="📜 Battle Summary", value=log_text[:1024], inline=False)
        
        await interaction.message.edit(embed=embed, view=View())
        
        # Check for more trainers
        remaining = battle_manager.getRemainingTrainerCount()
        if remaining > 0:
            next_up = battle_manager.getNextTrainer()
            await interaction.followup.send(
                f"**Trainers Remaining:** {remaining}\n"
                f"**Next Opponent:** {next_up.name if next_up else 'Unknown'}",
                ephemeral=False
            )
        else:
            gym_leader = battle_manager.getGymLeader()
            if gym_leader and not hasattr(trainer_model, 'gym_leader'):
                await interaction.followup.send(
                    f"All gym trainers defeated! You can now challenge Gym Leader {gym_leader.gym_leader}!",
                    ephemeral=False
                )

    async def __handle_gym_battle_defeat(self, interaction: discord.Interaction, battle_state: BattleState):
        """Handle when player loses a gym battle"""
        embed = discord.Embed(
            title="💀 DEFEAT",
            description=f"You were defeated by {battle_state.enemy_name}...",
            color=discord.Color.dark_red()
        )
        
        # Add battle summary
        if battle_state.battle_log:
            log_text = "\n".join(battle_state.battle_log[-3:])
            embed.add_field(name="📜 Battle Summary", value=log_text[:1024], inline=False)
        
        embed.add_field(
            name="💊 Next Steps",
            value="Head to a Pokemon Center to heal your Pokemon and try again!",
            inline=False
        )
        
        await interaction.message.edit(embed=embed, view=View())

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

    async def on_gym_battle_auto(self, interaction: discord.Interaction):
        """Handle AUTO battle with gym trainer"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()
        active_pokemon = trainer.getActivePokemon()

        if active_pokemon.currentHP == 0:
            await interaction.followup.send('Your active Pokemon has fainted! Heal at a Pokemon Center first.', ephemeral=True)
            return

        battle = BattleClass(str(user.id), location.locationId, enemyType="gym")
        next_trainer = battle.getNextTrainer()
        
        if not next_trainer:
            await interaction.followup.send('No trainer to battle.', ephemeral=True)
            return

        # Create enemy Pokemon
        trainer_pokemon_data = next_trainer.pokemon[0]
        enemy_name = list(trainer_pokemon_data.keys())[0]
        enemy_level = trainer_pokemon_data[enemy_name]

        try:
            enemy_pokemon = PokemonClass(None, enemy_name)
            enemy_pokemon.create(enemy_level)
        except Exception as e:
            await interaction.followup.send(f'Error creating enemy Pokemon: {str(e)}', ephemeral=True)
            return

        # Store initial stats for summary
        player_start_hp = active_pokemon.currentHP
        enemy_start_hp = enemy_pokemon.currentHP
        player_level = active_pokemon.currentLevel
        enemy_level_start = enemy_pokemon.currentLevel

        # AUTO BATTLE
        enc = EncounterClass(active_pokemon, enemy_pokemon)
        result = enc.fight(battleType='auto')

        # Get final stats
        player_end_hp = active_pokemon.currentHP
        enemy_end_hp = enemy_pokemon.currentHP
        
        # Parse the battle message for additional context
        battle_text = enc.message if enc.message else ""

        # Create a nice embed with battle summary
        if result.get('result') == 'victory':
            battle.battleVictory(next_trainer)
            remaining = battle.getRemainingTrainerCount()

            embed = discord.Embed(
                title="🎉 Victory!",
                description=f"You defeated {next_trainer.name}!",
                color=discord.Color.green()
            )

            # Battle Summary
            summary = []
            summary.append(f"**Your {active_pokemon.pokemonName.capitalize()}** (Lv.{player_level})")
            summary.append(f"HP: {player_start_hp} → {player_end_hp}")
            summary.append("")
            summary.append(f"**Enemy {enemy_pokemon.pokemonName.capitalize()}** (Lv.{enemy_level_start})")
            summary.append(f"HP: {enemy_start_hp} → {enemy_end_hp} ❌")
            
            embed.add_field(
                name="📊 Battle Summary",
                value="\n".join(summary),
                inline=False
            )

            # Experience and rewards info
            if battle_text:
                embed.add_field(
                    name="📈 Results",
                    value=battle_text[:1024],
                    inline=False
                )

            embed.add_field(
                name="💰 Reward",
                value=f"${next_trainer.money}",
                inline=True
            )

            if remaining > 0:
                next_up = battle.getNextTrainer()
                embed.add_field(
                    name="⚔️ Next",
                    value=f"{remaining} trainers remaining\nNext: {next_up.name if next_up else 'Unknown'}",
                    inline=True
                )
            else:
                gym_leader = battle.getGymLeader()
                embed.add_field(
                    name="🏆 Gym Progress",
                    value=f"All trainers defeated!\nChallenge {gym_leader.gym_leader if gym_leader else 'Gym Leader'}!",
                    inline=True
                )

            await interaction.followup.send(embed=embed, ephemeral=False)

        else:
            # DEFEAT
            embed = discord.Embed(
                title="💀 Defeat",
                description=f"You were defeated by {next_trainer.name}...",
                color=discord.Color.red()
            )

            # Battle Summary
            summary = []
            summary.append(f"**Your {active_pokemon.pokemonName.capitalize()}** (Lv.{player_level})")
            summary.append(f"HP: {player_start_hp} → {player_end_hp} ❌")
            summary.append("")
            summary.append(f"**Enemy {enemy_pokemon.pokemonName.capitalize()}** (Lv.{enemy_level_start})")
            summary.append(f"HP: {enemy_start_hp} → {enemy_end_hp}")
            
            embed.add_field(
                name="📊 Battle Summary",
                value="\n".join(summary),
                inline=False
            )

            # Battle details
            if battle_text:
                embed.add_field(
                    name="⚔️ Battle Details",
                    value=battle_text[:1024],
                    inline=False
                )

            embed.add_field(
                name="💊 Next Steps",
                value="Visit a Pokemon Center to heal your team!",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=False)

    # New handler for MANUAL trainer battles
    async def on_gym_battle_manual(self, interaction: discord.Interaction):
        """Handle MANUAL battle with gym trainer"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()
        active_pokemon = trainer.getActivePokemon()

        if active_pokemon.currentHP == 0:
            await interaction.followup.send('Your active Pokemon has fainted!', ephemeral=True)
            return

        battle = BattleClass(str(user.id), location.locationId, enemyType="gym")
        next_trainer = battle.getNextTrainer()
        
        if not next_trainer:
            await interaction.followup.send('No trainer to battle.', ephemeral=True)
            return

        # Create enemy Pokemon
        trainer_pokemon_data = next_trainer.pokemon[0]
        enemy_name = list(trainer_pokemon_data.keys())[0]
        enemy_level = trainer_pokemon_data[enemy_name]

        try:
            enemy_pokemon = PokemonClass(None, enemy_name)
            enemy_pokemon.create(enemy_level)
        except Exception as e:
            await interaction.followup.send(f'Error creating enemy Pokemon: {str(e)}', ephemeral=True)
            return

        # START MANUAL BATTLE
        battle_state = BattleState(
            user_id=str(user.id),
            channel_id=interaction.channel_id,
            message_id=0,
            player_pokemon=active_pokemon,
            enemy_pokemon=enemy_pokemon,
            enemy_name=next_trainer.name,
            trainer_model=next_trainer,
            battle_manager=battle
        )

        self.__battle_states[str(user.id)] = battle_state

        embed = self.__create_battle_embed(user, battle_state)
        view = self.__create_move_buttons(battle_state)

        message = await interaction.followup.send(
            content=f"**Manual Battle Started!**",
            embed=embed,
            view=view
        )

        battle_state.message_id = message.id
    
    async def on_gym_leader_battle_auto(self, interaction: discord.Interaction):
        """Handle gym leader AUTO battle with full summary"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()
        active_pokemon = trainer.getActivePokemon()

        if active_pokemon.currentHP == 0:
            await interaction.followup.send('Your active Pokemon has fainted! Heal at a Pokemon Center first.', ephemeral=True)
            return

        gyms_data = self.__load_gyms_data()
        gym_info = gyms_data.get(str(location.locationId))
        battle = BattleClass(str(user.id), location.locationId, enemyType="gym")

        gym_leader = battle.getGymLeader()
        if not gym_leader or battle.statuscode == 420:
            await interaction.followup.send(battle.message if battle.message else 'Cannot challenge gym leader.', ephemeral=True)
            return

        if not gym_leader.pokemon or len(gym_leader.pokemon) == 0:
            await interaction.followup.send(f'Error: Gym Leader {gym_leader.gym_leader} has no Pokemon data.', ephemeral=True)
            return

        leader_pokemon_data = gym_leader.pokemon[0]
        
        if not isinstance(leader_pokemon_data, dict) or not leader_pokemon_data:
            await interaction.followup.send(f'Error: Invalid Pokemon data for gym leader {gym_leader.gym_leader}', ephemeral=True)
            return
            
        enemy_name = list(leader_pokemon_data.keys())[0]
        enemy_level = leader_pokemon_data[enemy_name]

        if not enemy_name or enemy_name == 'None' or enemy_name == None:
            await interaction.followup.send(f'Error: Invalid Pokemon name in gym leader data: {enemy_name}', ephemeral=True)
            return

        try:
            enemy_pokemon = PokemonClass(None, enemy_name)
            enemy_pokemon.create(enemy_level)
        except Exception as e:
            await interaction.followup.send(f'Error creating gym leader Pokemon: {str(e)}', ephemeral=True)
            return

        # Store initial stats
        player_start_hp = active_pokemon.currentHP
        enemy_start_hp = enemy_pokemon.currentHP
        player_level = active_pokemon.currentLevel

        # Start the battle
        enc = EncounterClass(active_pokemon, enemy_pokemon)
        result = enc.fight(battleType='auto')

        # Get final stats
        player_end_hp = active_pokemon.currentHP
        enemy_end_hp = enemy_pokemon.currentHP
        battle_text = enc.message if enc.message else ""

        if result.get('result') == 'victory':
            battle.gymLeaderVictory(gym_leader)

            embed = discord.Embed(
                title="🏆 VICTORY!",
                description=f"You defeated Gym Leader {gym_leader.gym_leader}!",
                color=discord.Color.gold()
            )

            # Battle Summary
            summary = []
            summary.append(f"**Your {active_pokemon.pokemonName.capitalize()}** (Lv.{player_level})")
            summary.append(f"HP: {player_start_hp} → {player_end_hp}")
            summary.append("")
            summary.append(f"**{gym_leader.gym_leader}'s {enemy_pokemon.pokemonName.capitalize()}** (Lv.{enemy_level})")
            summary.append(f"HP: {enemy_start_hp} → {enemy_end_hp} ❌")
            
            embed.add_field(
                name="📊 Battle Summary",
                value="\n".join(summary),
                inline=False
            )

            if battle_text:
                embed.add_field(
                    name="📈 Results",
                    value=battle_text[:1024],
                    inline=False
                )

            embed.add_field(
                name="🎖️ Badge Earned",
                value=gym_leader.badge,
                inline=True
            )

            embed.add_field(
                name="💰 Prize Money",
                value=f"${gym_leader.money}",
                inline=True
            )

            await interaction.followup.send(embed=embed, ephemeral=False)
            
        else:
            embed = discord.Embed(
                title="💀 Defeat",
                description=f"You were defeated by Gym Leader {gym_leader.gym_leader}...",
                color=discord.Color.dark_red()
            )

            # Battle Summary
            summary = []
            summary.append(f"**Your {active_pokemon.pokemonName.capitalize()}** (Lv.{player_level})")
            summary.append(f"HP: {player_start_hp} → {player_end_hp} ❌")
            summary.append("")
            summary.append(f"**{gym_leader.gym_leader}'s {enemy_pokemon.pokemonName.capitalize()}** (Lv.{enemy_level})")
            summary.append(f"HP: {enemy_start_hp} → {enemy_end_hp}")
            
            embed.add_field(
                name="📊 Battle Summary",
                value="\n".join(summary),
                inline=False
            )

            if battle_text:
                embed.add_field(
                    name="⚔️ Battle Details",
                    value=battle_text[:1024],
                    inline=False
                )

            embed.add_field(
                name="💊 Next Steps",
                value="Visit a Pokemon Center to heal and try again!",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=False)

    async def on_gym_click(self, interaction: discord.Interaction):
        """Handle gym button clicks - now shows battle type choice"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        # Get location and gym data
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()

        gyms_data = self.__load_gyms_data()
        gym_info = gyms_data.get(str(location.locationId))

        if not gym_info:
            await interaction.followup.send('Gym data not found.', ephemeral=True)
            return

        # Check requirements
        requirements = gym_info['leader'].get('requirements', [])
        if not self.__check_prerequisites(str(user.id), requirements):
            missing = [req.replace('_', ' ').title() for req in requirements]
            await interaction.followup.send(
                f'You do not meet the requirements to challenge this gym. You need: {", ".join(missing)}',
                ephemeral=True
            )
            return

        # Use battle class to check gym progress
        battle = BattleClass(str(user.id), location.locationId, enemyType="gym")
        remaining_trainers = battle.getRemainingTrainerCount()

        if remaining_trainers > 0:
            # Need to defeat trainers first - show battle type choice
            next_trainer = battle.getNextTrainer()
            if next_trainer:
                view = View()
                
                # Auto Battle button
                auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Battle", custom_id='gym_battle_auto')
                auto_button.callback = self.on_gym_battle_auto
                view.add_item(auto_button)
                
                # Manual Battle button  
                manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Battle", custom_id='gym_battle_manual')
                manual_button.callback = self.on_gym_battle_manual
                view.add_item(manual_button)

                message = await interaction.followup.send(
                    f'**{gym_info["leader"]["gym-name"]}**\n\n'
                    f'Trainers Remaining: {remaining_trainers}\n\n'
                    f'**Next Opponent:** {next_trainer.name}\n'
                    f'**Reward:** ${next_trainer.money}\n\n'
                    f'Choose your battle mode:',
                    view=view
                )
                self.__useractions[str(user.id)].messageId = message.id
            else:
                await interaction.followup.send('Error getting next trainer.', ephemeral=True)
        else:
            # All trainers defeated, try to get gym leader
            gym_leader = battle.getGymLeader()

            if battle.statuscode == 420:
                if "already completed" in battle.message.lower():
                    await interaction.followup.send(
                        f'**{gym_info["leader"]["gym-name"]}**\n\n'
                        f'You have already defeated Gym Leader {gym_info["leader"]["gym-leader"]} and earned the {gym_info["leader"]["badge"]}!',
                        ephemeral=False
                    )
                else:
                    await interaction.followup.send(battle.message, ephemeral=True)
                return

            if gym_leader:
                view = View()
                
                # Auto Battle button
                auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Battle Leader", custom_id='gym_leader_battle_auto')
                auto_button.callback = self.on_gym_leader_battle_auto
                view.add_item(auto_button)
                
                # Manual Battle button
                manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Battle Leader", custom_id='gym_leader_battle_manual')
                manual_button.callback = self.on_gym_leader_battle_manual
                view.add_item(manual_button)

                message = await interaction.followup.send(
                    f'**{gym_info["leader"]["gym-name"]}**\n\n'
                    f'All gym trainers defeated!\n\n'
                    f'**Gym Leader:** {gym_leader.gym_leader}\n'
                    f'**Badge:** {gym_leader.badge}\n'
                    f'**Reward:** ${gym_leader.money}\n\n'
                    f'Choose your battle mode:',
                    view=view
                )
                self.__useractions[str(user.id)].messageId = message.id
            else:
                await interaction.followup.send(
                    f'Error: Could not load gym leader data.',
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
