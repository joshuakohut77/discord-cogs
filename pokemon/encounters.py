from __future__ import annotations
from re import A
from typing import Any, Dict, List, Union, TYPE_CHECKING
import asyncio
import json
import os

import discord
from discord import (Embed, Member)
from discord import message

from discord.ui import View, Button, Select, Modal
from discord import SelectOption, ButtonStyle, Interaction

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from models.location import LocationModel
from models.actionmodel import ActionModel, ActionType
from models.battlestate import BattleState, WildBattleState
from models.sessionstate import ActionState, BagState, ItemUsageState, MartState
from services.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass
from services.inventoryclass import inventory as InventoryClass
from services.pokeclass import Pokemon as PokemonClass
from services.questclass import quests as QuestsClass
from services.battleclass import battle as BattleClass
from services.encounterclass import encounter as EncounterClass, calculate_battle_damage
from services.ailmentsclass import ailment as AilmentClass
from services.expclass import experiance as exp
from services.leaderboardclass import leaderboard as LeaderboardClass

from .abcd import MixinMeta
from .functions import (getTypeColor, create_hp_bar)
from .helpers import (getTrainerGivenPokemonName)
from .helpers.pathhelpers import (get_config_path, load_json_config, get_sprite_path)
from .helpers.decorators import (require_action_state, require_battle_state,
                                  require_wild_battle_state, require_bag_state)

class NicknameModal(Modal, title="Set Pokemon Nickname"):
    def __init__(self, pokemon):
        super().__init__()
        self.pokemon = pokemon
        
        current_nick = pokemon.nickName if pokemon.nickName else ""
        
        # Add nickname input field
        self.nickname_input = discord.ui.TextInput(
            label="Nickname",
            placeholder=f"Enter nickname for {pokemon.pokemonName.capitalize()}",
            default=current_nick,
            required=False,
            max_length=20,
            style=discord.TextStyle.short
        )
        self.add_item(self.nickname_input)
        
        # Add clear option
        self.clear_input = discord.ui.TextInput(
            label='Type "CLEAR" to remove nickname',
            placeholder="Leave blank to set nickname above",
            required=False,
            max_length=5,
            style=discord.TextStyle.short
        )
        self.add_item(self.clear_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        nickname = self.nickname_input.value.strip()
        clear_text = self.clear_input.value.strip().upper()
        
        # Check if user wants to clear
        if clear_text == "CLEAR":
            self.pokemon.nickName = None
            self.pokemon.save()
            
            embed = discord.Embed(
                title="✅ Nickname Cleared",
                description=f"**{self.pokemon.pokemonName.capitalize()}** no longer has a nickname.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Set new nickname
        if nickname:
            self.pokemon.nickName = nickname
            self.pokemon.save()
            
            embed = discord.Embed(
                title="✅ Nickname Set",
                description=f"**{self.pokemon.pokemonName.capitalize()}** is now nicknamed **{nickname}**!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ No Change",
                description="No nickname entered.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class EncountersMixin(MixinMeta):
    """Encounters"""

    __useractions: dict[str, ActionState] = {}
    __quests_data: dict = None
    __gyms_data: dict = None
    __locations_data: dict = None
    __battle_states: dict[str, BattleState] = {}
    __wild_battle_states: Dict[str, WildBattleState] = {}
    __bag_states: dict[str, BagState] = {}
    __item_usage_states: dict = {}
    __flight_states: dict = {}
    __enemy_trainers_data: dict = None
    __trainer_cache: Dict[str, TrainerClass] = {}  # Cache for TrainerClass instances

    def _get_trainer(self, user_id: str) -> TrainerClass:
        """
        Get TrainerClass instance with caching.

        Caches trainer instances to reduce repeated instantiations.
        Cache persists for the lifetime of the cog.

        Args:
            user_id: Discord user ID

        Returns:
            TrainerClass instance

        Example:
            >>> trainer = self._get_trainer(str(user.id))
            >>> location = trainer.getLocation()
        """
        if user_id not in self.__trainer_cache:
            self.__trainer_cache[user_id] = TrainerClass(user_id)
        return self.__trainer_cache[user_id]

    def _clear_trainer_cache(self, user_id: str = None):
        """
        Clear trainer cache for user or all users.

        Args:
            user_id: Specific user to clear, or None to clear all
        """
        if user_id:
            self.__trainer_cache.pop(user_id, None)
        else:
            self.__trainer_cache.clear()

    def __load_enemy_trainers_data(self):
        """Load enemy trainers configuration"""
        if self.__enemy_trainers_data is None:
            self.__enemy_trainers_data = load_json_config('enemyTrainers.json')
        return self.__enemy_trainers_data


    def __create_level_up_embed(self, pokemon, old_level, new_level, learned_moves=None, evolution_name=None):
        """ Creates a dismissable level-up notification embed """
        if evolution_name:
            title = f"🌟 Evolution! {pokemon.pokemonName.capitalize()} → {evolution_name.capitalize()}!"
            description = f"**{pokemon.pokemonName.capitalize()}** evolved into **{evolution_name.capitalize()}**!"
            color = discord.Color.gold()
        else:
            title = f"⬆️ Level Up!"
            description = f"**{pokemon.pokemonName.capitalize()}** grew to level **{new_level}**!"
            color = discord.Color.green()
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        # Add Pokemon sprite
        sprite_url = pokemon.frontSpriteURL
        if sprite_url:
            embed.set_thumbnail(url=sprite_url)
        
        embed.add_field(
            name="Level",
            value=f"{old_level} → {new_level}",
            inline=True
        )
        
        current_hp = pokemon.currentHP
        max_hp = pokemon.getPokeStats()['hp']
        embed.add_field(
            name="HP",
            value=f"{current_hp}/{max_hp}",
            inline=True
        )
        
        # Add learned moves if any
        if learned_moves and len(learned_moves) > 0:
            moves_text = "\n".join([f"• {move.replace('-', ' ').title()}" for move in learned_moves])
            embed.add_field(
                name="📚 New Moves Learned",
                value=moves_text,
                inline=False
            )
        
        return embed

    def __create_move_learning_embed(self, pokemon, move_to_learn, moves_config):
        """ Creates embed showing the new move being learned """
        embed = discord.Embed(
            title=f"📚 New Move Available!",
            description=f"**{pokemon.pokemonName.capitalize()}** wants to learn **{move_to_learn.replace('-', ' ').title()}**!",
            color=discord.Color.blue()
        )
        
        # Add Pokemon sprite
        if pokemon.frontSpriteURL:
            embed.set_thumbnail(url=pokemon.frontSpriteURL)
        
        # Show new move details
        move_data = moves_config.get(move_to_learn, {})
        power = move_data.get('power', 'N/A')
        accuracy = move_data.get('accuracy', 'N/A')
        move_type = move_data.get('moveType', 'normal')
        pp = move_data.get('pp', 'N/A')
        
        embed.add_field(
            name=f"New Move: {move_to_learn.replace('-', ' ').title()}",
            value=f"Type: {move_type.title()} | Power: {power} | Accuracy: {accuracy} | PP: {pp}",
            inline=False
        )
        
        embed.add_field(
            name="Current Moves",
            value="Choose which move to replace, or don't learn this move.",
            inline=False
        )
        
        return embed

    async def __handle_move_learning(self, interaction: discord.Interaction, pokemon, pending_moves, battle_state=None):
        """
        Handles the UI for learning new moves when Pokemon has 4 moves.
        
        Args:
            interaction: The interaction to respond to
            pokemon: The Pokemon learning moves
            pending_moves: List of move names to learn
            battle_state: Optional BattleState if this is during a battle
        """
        from helpers.pathhelpers import load_json_config
        moves_config = load_json_config('moves.json')
        
        for move_to_learn in pending_moves:
            # Create the embed
            embed = self.__create_move_learning_embed(pokemon, move_to_learn, moves_config)
            
            # Get current moves
            current_moves = pokemon.getCurrentMovesList()
            
            # Add current move details to embed
            for slot, move_name in current_moves:
                move_data = moves_config.get(move_name, {})
                power = move_data.get('power', 'N/A')
                move_type = move_data.get('moveType', 'normal')
                embed.add_field(
                    name=f"Slot {slot}: {move_name.replace('-', ' ').title()}",
                    value=f"Type: {move_type.title()} | Power: {power}",
                    inline=True
                )
            
            # Create buttons for each current move + Don't Learn
            view = discord.ui.View(timeout=180)
            
            for slot, move_name in current_moves:
                button = discord.ui.Button(
                    label=f"Replace {move_name.replace('-', ' ').title()}",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"replace_move_{slot}"
                )
                
                async def button_callback(inter: discord.Interaction, slot_num=slot, old_move=move_name):
                    if inter.user.id != interaction.user.id:
                        await inter.response.send_message("This is not for you!", ephemeral=True)
                        return
                    
                    # Learn the move in the selected slot
                    pokemon.learnMove(move_to_learn, replaceSlot=slot_num)
                    pokemon.save()
                    
                    # Delete the original message
                    await inter.message.delete()
                    
                    # Send ephemeral confirmation
                    await inter.response.send_message(
                        f"✅ {pokemon.pokemonName.capitalize()} forgot {old_move.replace('-', ' ').title()} and learned {move_to_learn.replace('-', ' ').title()}!",
                        ephemeral=True
                    )
                
                button.callback = button_callback
                view.add_item(button)
            
            # Add "Don't Learn" button
            dont_learn_button = discord.ui.Button(
                label="Don't Learn",
                style=discord.ButtonStyle.secondary,
                custom_id="dont_learn_move"
            )
            
            async def dont_learn_callback(inter: discord.Interaction):
                if inter.user.id != interaction.user.id:
                    await inter.response.send_message("This is not for you!", ephemeral=True)
                    return
                
                # Delete the original message
                await inter.message.delete()
                
                # Send ephemeral confirmation
                await inter.response.send_message(
                    f"❌ {pokemon.pokemonName.capitalize()} did not learn {move_to_learn.replace('-', ' ').title()}.",
                    ephemeral=True
                )
            
            dont_learn_button.callback = dont_learn_callback
            view.add_item(dont_learn_button)
            
            # Send as followup (works both during and after battle)
            await interaction.followup.send(embed=embed, view=view, ephemeral=False)
            
            # Wait for button interaction
            try:
                await view.wait()
            except:
                pass  # Timeout or error


    async def __handle_tm_usage(self, interaction, user, item_state):
        """Handle using a TM on a Pokemon from the party Use Items menu."""
        import constant
        from services.inventoryclass import inventory as InventoryClass
        from services.pokeclass import Pokemon as PokemonClass
        from helpers.pathhelpers import load_json_config

        tm_key = item_state.selected_item  # e.g. "TM24"
        move_name = constant.TM_MOVE_MAPPING.get(tm_key)

        if not move_name:
            await interaction.followup.send(f'❌ Unknown TM: {tm_key}', ephemeral=True)
            return

        # Load the target Pokemon
        pokemon = PokemonClass(str(user.id))
        pokemon.load(int(item_state.selected_pokemon_id))

        # Check if Pokemon can learn this TM (check tms.json)
        tms_config = load_json_config('tms.json')
        compatible_pokemon = tms_config.get(tm_key, [])

        can_learn = False
        for entry in compatible_pokemon:
            if entry.get('Name', '').lower() == pokemon.pokemonName.lower():
                can_learn = True
                break

        if not can_learn:
            display_move = move_name.replace('-', ' ').title()
            await interaction.followup.send(
                f'❌ {pokemon.pokemonName.capitalize()} is not compatible with {tm_key} ({display_move})!',
                ephemeral=True
            )
            return

        # Check if Pokemon already knows this move
        current_moves = pokemon.getCurrentMovesList()
        for slot, existing_move in current_moves:
            if existing_move == move_name:
                display_move = move_name.replace('-', ' ').title()
                await interaction.followup.send(
                    f'❌ {pokemon.pokemonName.capitalize()} already knows {display_move}!',
                    ephemeral=True
                )
                return

        # Check TM quantity
        inv = InventoryClass(str(user.id))
        current_qty = inv.getTM(tm_key)
        if current_qty <= 0:
            await interaction.followup.send(f'❌ You don\'t have any {tm_key}!', ephemeral=True)
            return

        current_move_count = pokemon.getCurrentMoveCount()
        display_move = move_name.replace('-', ' ').title()

        if current_move_count < 4:
            # Auto-learn — consume TM and learn immediately
            inv.setTM(tm_key, current_qty - 1)
            inv.save()

            pokemon.learnMove(move_name)
            pokemon.save()

            await interaction.followup.send(
                f'✅ {pokemon.pokemonName.capitalize()} learned {display_move}!',
                ephemeral=True
            )

            # Refresh the item usage view
            embed, view = self.__create_item_usage_view(user)
            await interaction.message.edit(embed=embed, view=view)
        else:
            # Has 4 moves — show replacement UI, only consume TM on confirm
            await self.__handle_tm_move_learning(interaction, user, pokemon, move_name, tm_key)

    async def __handle_tm_move_learning(self, interaction, user, pokemon, move_to_learn, tm_key):
        """TM-specific move learning UI. Only consumes the TM if the player replaces a move."""
        from helpers.pathhelpers import load_json_config
        from services.inventoryclass import inventory as InventoryClass
        import constant

        moves_config = load_json_config('moves.json')

        # Create the embed (reuse existing helper)
        embed = self.__create_move_learning_embed(pokemon, move_to_learn, moves_config)
        embed.title = f"📀 {tm_key} — {move_to_learn.replace('-', ' ').title()}"

        # Get current moves
        current_moves = pokemon.getCurrentMovesList()

        # Add current move details to embed
        for slot, move_name in current_moves:
            move_data = moves_config.get(move_name, {})
            power = move_data.get('power', 'N/A')
            move_type = move_data.get('moveType', 'normal')
            embed.add_field(
                name=f"Slot {slot}: {move_name.replace('-', ' ').title()}",
                value=f"Type: {move_type.title()} | Power: {power}",
                inline=True
            )

        # Create buttons for each current move + Don't Learn
        view = discord.ui.View(timeout=180)

        for slot, move_name in current_moves:
            button = discord.ui.Button(
                label=f"Replace {move_name.replace('-', ' ').title()}",
                style=discord.ButtonStyle.primary,
                custom_id=f"tm_replace_move_{slot}"
            )

            async def replace_callback(inter: discord.Interaction, slot_num=slot, old_move=move_name):
                if inter.user.id != interaction.user.id:
                    await inter.response.send_message("This is not for you!", ephemeral=True)
                    return

                # NOW consume the TM
                inv = InventoryClass(str(inter.user.id))
                current_qty = inv.getTM(tm_key)
                inv.setTM(tm_key, current_qty - 1)
                inv.save()

                # Learn the move in the selected slot
                pokemon.learnMove(move_to_learn, replaceSlot=slot_num)
                pokemon.save()

                display_move = move_to_learn.replace('-', ' ').title()
                old_display = old_move.replace('-', ' ').title()

                # Delete the move learning message
                await inter.message.delete()

                await inter.response.send_message(
                    f"✅ {pokemon.pokemonName.capitalize()} forgot {old_display} and learned {display_move}!",
                    ephemeral=True
                )

                # Refresh the item usage view on the original message
                embed, view = self.__create_item_usage_view(inter.user)
                await interaction.message.edit(embed=embed, view=view)

            button.callback = replace_callback
            view.add_item(button)

        # Don't Learn button — TM is NOT consumed
        dont_learn_button = discord.ui.Button(
            label="Don't Learn",
            style=discord.ButtonStyle.secondary,
            custom_id="tm_dont_learn_move"
        )

        async def dont_learn_callback(inter: discord.Interaction):
            if inter.user.id != interaction.user.id:
                await inter.response.send_message("This is not for you!", ephemeral=True)
                return

            display_move = move_to_learn.replace('-', ' ').title()

            await inter.message.delete()

            await inter.response.send_message(
                f"❌ {pokemon.pokemonName.capitalize()} did not learn {display_move}. {tm_key} was not used.",
                ephemeral=True
            )

        dont_learn_button.callback = dont_learn_callback
        view.add_item(dont_learn_button)

        await interaction.followup.send(embed=embed, view=view, ephemeral=False)

    def __get_wild_trainers_button(self, user_id: str, location_id: int):
        """
        Check if location has wild trainers and return button if available.
        Returns Button object or None.
        """
        from services.battleclass import battle as BattleClass
        
        try:
            # Load enemy trainers data
            enemy_trainers_data = self.__load_enemy_trainers_data()
            
            # Check if location has wild trainers
            if str(location_id) not in enemy_trainers_data:
                return None
            
            # Check if there are any remaining trainers to battle
            battle = BattleClass(user_id, location_id, enemyType="wild")
            remaining = battle.getRemainingTrainerCount()
            
            if remaining == 0:
                return None
            
            # Create trainers button
            button = Button(
                style=ButtonStyle.blurple,
                label=f"⚔️ Trainers ({remaining})",
                custom_id='wild_trainers',
                row=2
            )
            button.callback = self.on_wild_trainers_click
            
            return button
            
        except:
            return None

    async def on_wild_trainers_click(self, interaction: discord.Interaction):
        """Handle wild trainers button clicks - shows battle type choice"""
        user = interaction.user
        
        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Get location
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        # Use battle class to check trainer progress
        battle = BattleClass(str(user.id), location.locationId, enemyType="wild")
        remaining_trainers = battle.getRemainingTrainerCount()
        
        if remaining_trainers > 0:
            next_trainer = battle.getNextTrainer()
            if next_trainer:
                # Create embed
                embed = discord.Embed(
                    title="⚔️ Wild Trainer Battle",
                    description=f"Choose your battle mode to face the next trainer!",
                    color=discord.Color.blurple()
                )
                
                embed.add_field(
                    name="Trainers Remaining",
                    value=f"{remaining_trainers}",
                    inline=True
                )
                
                embed.add_field(
                    name="Next Opponent",
                    value=next_trainer.name,
                    inline=True
                )
                
                embed.add_field(
                    name="Reward",
                    value=f"${next_trainer.money}",
                    inline=True
                )
                
                # ADD TRAINER SPRITE - Try file first, then URL fallback
                sprite_loaded = False
                sprite_file = None
                
                if next_trainer.spritePath:
                    try:
                        # Try to load from local file system first
                        # spritePath is like "/sprites/trainers/jrtrainer.png"
                        full_sprite_path = get_sprite_path(next_trainer.spritePath)

                        # Check if file exists
                        if os.path.exists(full_sprite_path):
                            # Extract filename for attachment
                            filename = os.path.basename(next_trainer.spritePath)
                            sprite_file = discord.File(full_sprite_path, filename=filename)
                            embed.set_image(url=f"attachment://{filename}")
                            sprite_loaded = True
                        else:
                            raise FileNotFoundError("Sprite file not found locally")
                    except Exception as e:
                        print(f"Error loading trainer sprite from file: {e}")
                        # Fallback to URL
                        try:
                            sprite_url = f"https://pokesprites.joshkohut.com{next_trainer.spritePath}"
                            embed.set_image(url=sprite_url)
                        except Exception as url_error:
                            print(f"Error loading trainer sprite from URL: {url_error}")
                
                # Create view with battle mode buttons
                view = View()
                
                # Auto Battle button
                auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Battle", custom_id='wild_battle_auto')
                auto_button.callback = self.on_wild_battle_auto
                view.add_item(auto_button)
                
                # Manual Battle button  
                manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Battle", custom_id='wild_battle_manual')
                manual_button.callback = self.on_wild_battle_manual
                view.add_item(manual_button)
                
                # Back button
                back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back", custom_id='wild_back', row=1)
                back_btn.callback = self.on_wild_back_click
                view.add_item(back_btn)
                
                # Edit the message - if sprite file was loaded, need to send new message
                if sprite_loaded:
                    # When editing with a file attachment, use followup.send to replace the message
                    new_message = await interaction.followup.send(
                        embed=embed,
                        view=view,
                        file=sprite_file
                    )
                    # Delete the old message
                    try:
                        await interaction.message.delete()
                    except:
                        pass
                    
                    # CRITICAL: Update ActionState with new message ID
                    if str(user.id) in self.__useractions:
                        self.__useractions[str(user.id)].messageId = new_message.id
                else:
                    # No file attachment, can use regular edit
                    await interaction.message.edit(
                        content=None,
                        embed=embed,
                        view=view
                    )
                    # messageId stays the same, no need to update
            else:
                await interaction.followup.send('Error getting next trainer.', ephemeral=True)
        else:
            await interaction.followup.send('All trainers in this area have been defeated!', ephemeral=True)


    async def on_wild_back_click(self, interaction: discord.Interaction):
        """Handle back button from wild trainers menu"""
        user = interaction.user
        
        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Return to map
        await self.on_nav_map_click(interaction)

    async def on_wild_battle_auto(self, interaction: discord.Interaction):
        """Handle AUTO battle with wild trainer"""
        user = interaction.user
        
        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        # Get player's full party
        player_party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in player_party:
            poke.load(pokemonId=poke.trainerId)
            if poke.currentHP > 0:
                alive_party.append(poke)
        
        if len(alive_party) == 0:
            await interaction.followup.send('All your party Pokemon have fainted! Heal at a Pokemon Center first.', ephemeral=True)
            return
        
        alive_party = self.__sort_party_active_first(alive_party, str(user.id))
        battle = BattleClass(str(user.id), location.locationId, enemyType="wild")
        next_trainer = battle.getNextTrainer()
        
        if not next_trainer:
            await interaction.followup.send('No trainer to battle.', ephemeral=True)
            return
        
        # Build battle log
        battle_log = []
        battle_log.append(f"⚔️ **Battle vs {next_trainer.name}**\n")
        
        # Create enemy Pokemon from trainer data
        enemy_pokemon_list = next_trainer.pokemon
        player_pokemon_index = 0
        enemy_pokemon_index = 0
        defeated_enemies = []
        defeated_players = []
        exp_messages = []
        
        max_turns = 100
        turn = 0
        
        while turn < max_turns:
            turn += 1
            
            # Check if battle is over
            if player_pokemon_index >= len(alive_party):
                # Player lost
                battle_log.append("\n💀 **All your Pokemon have fainted! You lost!**")
                    # LEADERBOARD TRACKING
                from services.leaderboardclass import leaderboard as LeaderboardClass
                lb = LeaderboardClass(str(user.id))
                lb.defeat()
                lb.actions()
                break
            
            if enemy_pokemon_index >= len(enemy_pokemon_list):
                # Player won!
                battle_log.append(f"\n🏆 **Victory! You defeated {next_trainer.name}!**")
                battle.battleVictory(next_trainer)

                # LEADERBOARD TRACKING
                from services.leaderboardclass import leaderboard as LeaderboardClass
                lb = LeaderboardClass(str(user.id))
                lb.victory()
                lb.actions()
                break
            
            # Get current Pokemon
            player_pokemon = alive_party[player_pokemon_index]
            current_enemy = enemy_pokemon_list[enemy_pokemon_index]
            enemy_name = list(current_enemy.keys())[0]
            enemy_level = current_enemy[enemy_name]
            
            from services.pokedexclass import pokedex as PokedexClass

            # Create enemy Pokemon - FIX: Use positional parameter
            enemy_pokemon = PokemonClass(str(user.id), enemy_name)
            enemy_pokemon.create(enemy_level)
            enemy_pokemon.discordId = None 
            
            PokedexClass(str(user.id), enemy_pokemon)

            # Battle turn
            enc = EncounterClass(player_pokemon, enemy_pokemon)
            result = enc.fight(battleType='auto')
            
            battle_log.append(f"\n**Turn {turn}:**")
            battle_log.append(f"• {player_pokemon.pokemonName.capitalize()} (HP: {player_pokemon.currentHP}) vs {enemy_name.capitalize()} (HP: {enemy_pokemon.currentHP})")
            
            # Capture experience message
            if enc.message:
                exp_messages.append(f"{player_pokemon.pokemonName.capitalize()}: {enc.message}")

            # Check if enemy fainted
            if enemy_pokemon.currentHP <= 0:
                defeated_enemies.append(enemy_name)
                battle_log.append(f"💥 Enemy {enemy_name.capitalize()} fainted!")
                enemy_pokemon_index += 1
                
                # Level up check for player's Pokemon
                if player_pokemon.currentLevel > player_pokemon.previousLevel:
                    battle_log.append(f"✨ {player_pokemon.pokemonName.capitalize()} leveled up to {player_pokemon.currentLevel}!")
            
            # Check if player's Pokemon fainted
            if player_pokemon.currentHP <= 0:
                defeated_players.append(player_pokemon.pokemonName)
                battle_log.append(f"💀 Your {player_pokemon.pokemonName.capitalize()} fainted!")
                player_pokemon.save()  # Save fainted state
                player_pokemon_index += 1
        
        # Save all Pokemon states
        for poke in alive_party:
            poke.save()
        
        # Create result embed
        embed = discord.Embed(
            title="⚔️ Battle Complete!",
            description="\n".join(battle_log[:20]),  # Limit to prevent embed size issues
            color=discord.Color.green() if enemy_pokemon_index >= len(enemy_pokemon_list) else discord.Color.red()
        )
        
        embed.add_field(
            name="💚 Your Team",
            value=f"Active: {len(alive_party) - len(defeated_players)}/{len(alive_party)}",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Enemy Team",
            value=f"Defeated: {len(defeated_enemies)}/{len(enemy_pokemon_list)}",
            inline=True
        )
        
        if enemy_pokemon_index >= len(enemy_pokemon_list):
            embed.add_field(
                name="💰 Reward",
                value=f"${next_trainer.money}",
                inline=False
            )
        
        view_nav = self.__create_post_battle_buttons(str(user.id))
        
        # Edit message instead of followup
        await interaction.message.edit(
            content=None,
            embed=embed,
            view=view_nav
        )

        # Check if player just defeated the Champion (elite-4-5)
        if enemy_pokemon_index >= len(enemy_pokemon_list) and hasattr(next_trainer, 'enemy_uuid') and next_trainer.enemy_uuid == "elite-4-5":
            finale_embed = discord.Embed(
                title="🏆 Congratulations, Champion!",
                description="You have defeated the Elite Four!\n\n"
                            "**You have unlocked the finale!**\n"
                            "Please type the command `,finale` and read the instructions to continue.",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=finale_embed)

    async def on_wild_battle_manual(self, interaction: discord.Interaction):
        """Handle MANUAL turn-by-turn battle with wild trainer"""
        user = interaction.user
        
        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        battle_manager = BattleClass(str(user.id), location.locationId, enemyType="wild")
        opponent = battle_manager.getNextTrainer()
        
        await self._start_manual_trainer_battle(
            interaction,
            enemy_type="wild",
            opponent=opponent,
            battle_manager=battle_manager,
            sprite_path=None,
            is_wild_trainer=True
        )


    def __create_post_battle_buttons(self, user_id: str, show_trainer_buttons: bool = True) -> View:
        """Create navigation buttons to show after battle ends
        
        Args:
            user_id: The user's Discord ID
            show_trainer_buttons: Whether to show trainer battle buttons (False for wild Pokemon)
        """
        view = View()
        
        trainer = self._get_trainer(user_id)
        location = trainer.getLocation()
        
        # Check if player has any alive Pokemon
        player_party = trainer.getPokemon(party=True)
        has_alive_pokemon = False
        for poke in player_party:
            poke.load(pokemonId=poke.trainerId)
            if poke.currentHP > 0:
                has_alive_pokemon = True
                break
        
        # Only show trainer battle buttons if enabled AND player has alive Pokemon
        if show_trainer_buttons and has_alive_pokemon:
            # Check for wild trainers
            battle_wild = BattleClass(user_id, location.locationId, enemyType="wild")
            remaining_wild = battle_wild.getRemainingTrainerCount()
            
            if remaining_wild > 0:
                wild_btn = Button(style=ButtonStyle.blurple, label=f"⚔️ Next Trainer ({remaining_wild})", custom_id='post_battle_wild')
                wild_btn.callback = self.on_wild_trainers_click
                view.add_item(wild_btn)
            
            # Check for gym trainers
            battle_gym = BattleClass(user_id, location.locationId, enemyType="gym")
            remaining_gym = battle_gym.getRemainingTrainerCount()
            
            if remaining_gym > 0:
                gym_btn = Button(style=ButtonStyle.red, label=f"🏛️ Gym Trainer ({remaining_gym})", custom_id='post_battle_gym')
                gym_btn.callback = self.on_gym_click
                view.add_item(gym_btn)

        # Always show map button
        map_button = Button(style=ButtonStyle.primary, label="🗺️ Map", custom_id='nav_map', row=1)
        map_button.callback = self.on_nav_map_click
        view.add_item(map_button)
        
        # Always show bag button
        party_button = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_party', row=1)
        party_button.callback = self.on_nav_bag_click
        view.add_item(party_button)
        
        # Always show heal button if at Pokemon Center
        if location.pokecenter:
            heal_button = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal', row=1)
            heal_button.callback = self.on_nav_heal_click
            view.add_item(heal_button)
        
        return view


# =============================================================================
# SEPARATOR - NEXT METHOD
# =============================================================================
    async def __handle_wild_battle_victory(self, interaction: discord.Interaction, battle_state: WildBattleState):
        """Handle when player defeats wild Pokemon"""
        user = interaction.user
        
        # LEADERBOARD TRACKING
        from services.leaderboardclass import leaderboard as LeaderboardClass
        lb = LeaderboardClass(str(user.id))
        lb.victory()
        lb.actions()

        player_max_hp = battle_state.player_pokemon.getPokeStats()['hp']
        player_level = battle_state.player_pokemon.currentLevel
        
        embed = discord.Embed(
            title="🏆 VICTORY!",
            description=f"You defeated the wild {battle_state.wild_pokemon.pokemonName.capitalize()}!",
            color=discord.Color.green()
        )
        
        player_summary = []
        from .functions import get_pokemon_display_name
        player_display = get_pokemon_display_name(battle_state.player_pokemon)
        player_summary.append(f"**{player_display}** (Lv.{player_level})")
        player_summary.append(f"HP: {battle_state.player_pokemon.currentHP}/{player_max_hp}")
        
        embed.add_field(
            name="💚 Your Pokemon",
            value="\n".join(player_summary),
            inline=True
        )
        
        if battle_state.battle_log:
            log_text = "\n".join(battle_state.battle_log)
            embed.add_field(
                name="⚔️ Final Turn",
                value=log_text[:1024],
                inline=False
            )
        
        # KEY CHANGE: Use existing post battle buttons
        view = self.__create_post_battle_buttons(battle_state.user_id, show_trainer_buttons=False)
        
        # KEY CHANGE: Clear content and use existing message
        await interaction.message.edit(content=None, embed=embed, view=view)
    
    async def __handle_wild_battle_defeat(self, interaction: discord.Interaction, battle_state: WildBattleState):
        """Handle when player loses to wild Pokemon"""
        user = interaction.user
        
        player_max_hp = battle_state.player_pokemon.getPokeStats()['hp']
        player_level = battle_state.player_pokemon.currentLevel
        
        embed = discord.Embed(
            title="💀 DEFEAT",
            description=f"You were defeated by the wild {battle_state.wild_pokemon.pokemonName.capitalize()}...",
            color=discord.Color.dark_red()
        )
        
        player_summary = []
        from .functions import get_pokemon_display_name
        player_display = get_pokemon_display_name(battle_state.player_pokemon)
        player_summary.append(f"**{player_display}** (Lv.{player_level})")
        player_summary.append(f"HP: 0/{player_max_hp} ❌")
        
        embed.add_field(
            name="💚 Your Pokemon",
            value="\n".join(player_summary),
            inline=True
        )
        
        if battle_state.battle_log:
            log_text = "\n".join(battle_state.battle_log)
            embed.add_field(
                name="⚔️ Final Turn",
                value=log_text[:1024],
                inline=False
            )
        
        # KEY CHANGE: Use existing post battle buttons
        view = self.__create_post_battle_buttons(str(user.id), show_trainer_buttons=False)
        
        # KEY CHANGE: Clear content and use existing message
        await interaction.message.edit(content=None, embed=embed, view=view)

    @require_wild_battle_state()
    async def on_wild_battle_run_click(self, interaction: discord.Interaction):
        """Handle running away from wild battle"""
        user = interaction.user
        user_id = str(user.id)
        battle_state = self.__wild_battle_states[user_id]

        await interaction.response.defer()
        
        battle_state.player_pokemon.save()

        # LEADERBOARD TRACKING
        from services.leaderboardclass import leaderboard as LeaderboardClass
        lb = LeaderboardClass(str(user.id))
        lb.run_away()
        lb.actions()
        
        embed = discord.Embed(
            title="🏃 Ran Away!",
            description=f"You ran away from the wild {battle_state.wild_pokemon.pokemonName.capitalize()}!",
            color=discord.Color.blue()
        )
        
        # KEY CHANGE: Use existing post battle buttons
        view = self.__create_post_battle_buttons(user_id, show_trainer_buttons=False)
        
        # KEY CHANGE: Clear content and use existing message
        await interaction.message.edit(content=None, embed=embed, view=view)
        
        del self.__wild_battle_states[user_id]

    async def on_wild_battle_catch_back(self, interaction: discord.Interaction):
        """Go back to battle from catch screen"""
        user = interaction.user
        user_id = str(user.id)
        
        if user_id not in self.__wild_battle_states:
            await interaction.response.send_message('No active wild battle found.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        battle_state = self.__wild_battle_states[user_id]
        
        # Restore battle interface
        embed = self.__create_wild_battle_embed(user, battle_state)
        view = self.__create_battle_move_buttons_with_items(battle_state)
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_wild_battle_throw_ball(self, interaction: discord.Interaction):
        """Handle throwing a Pokeball at wild Pokemon"""
        user = interaction.user
        user_id = str(user.id)
        
        if user_id not in self.__wild_battle_states:
            await interaction.response.send_message('No active wild battle found.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        battle_state = self.__wild_battle_states[user_id]
        trainer = self._get_trainer(user_id)
        
        # Get ball type from custom_id
        ball_id = interaction.data['custom_id'].replace('wild_catch_', '')
        
        # Convert button ID to item format
        ball_type_map = {
            'pokeball': 'poke-ball',
            'greatball': 'great-ball',
            'ultraball': 'ultra-ball',
            'masterball': 'master-ball'
        }
        ball_type = ball_type_map.get(ball_id, 'poke-ball')
                
        # Call catch method
        trainer.catch(battle_state.wild_pokemon, ball_type)       
        
        if trainer.statuscode == 420:
            # Successful catch
            
            embed = discord.Embed(
                title="🎉 CAUGHT!",
                description=f"{trainer.message}",
                color=discord.Color.green()
            )
            
            # Check for capture milestones
            if interaction.guild:
                await self.check_capture_milestones(str(user.id), interaction.guild)

            view = self.__create_post_battle_buttons(user_id)
            
            await interaction.message.edit(
                content=None,
                embed=embed,
                view=view
            )
            
            del self.__wild_battle_states[user_id]

    @require_wild_battle_state()
    async def on_wild_battle_catch_click(self, interaction: discord.Interaction):
        """Handle attempting to catch Pokemon during battle"""
        user = interaction.user
        user_id = str(user.id)
        battle_state = self.__wild_battle_states[user_id]

        await interaction.response.defer()
        
        # Show Pokeball selection (reuse existing logic)
        trainer = self._get_trainer(user_id)
        items = InventoryClass(trainer.discordId)
        
        ctx = await self.bot.get_context(interaction.message)
        
        view = View()
        has_balls = False
        
        # IMPORTANT: Use custom_id format that matches the old system
        # Format: 'wild_catch_pokeball' not just 'pokeball'
        # This ensures the ball_type_map in on_wild_battle_throw_ball works correctly
        
        if items.pokeball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.POKEBALL)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Poke Ball", custom_id='wild_catch_pokeball')
            button.callback = self.on_wild_battle_throw_ball
            view.add_item(button)
            has_balls = True
        
        if items.greatball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.GREATBALL)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Great Ball", custom_id='wild_catch_greatball')
            button.callback = self.on_wild_battle_throw_ball
            view.add_item(button)
            has_balls = True
        
        if items.ultraball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.ULTRABALL)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Ultra Ball", custom_id='wild_catch_ultraball')
            button.callback = self.on_wild_battle_throw_ball
            view.add_item(button)
            has_balls = True
        
        if items.masterball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.MASTERBALL)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Master Ball", custom_id='wild_catch_masterball')
            button.callback = self.on_wild_battle_throw_ball
            view.add_item(button)
            has_balls = True
        
        if not has_balls:
            await interaction.followup.send('You have no Poke Balls!', ephemeral=True)
            return
        
        # Add back button
        back_button = Button(style=ButtonStyle.gray, label="Back", custom_id='wild_catch_back')
        back_button.callback = self.on_wild_battle_catch_back
        view.add_item(back_button)
        
        # Update embed to show catch attempt
        embed = self.__create_wild_battle_embed(user, battle_state)
        embed.description = "**Choose a Poke Ball to throw!**"
        
        await interaction.message.edit(embed=embed, view=view)


    @require_wild_battle_state()
    async def on_wild_battle_move_click(self, interaction: discord.Interaction):
        """Handle move selection in wild battle - with ailment + special move support"""
        user = interaction.user
        user_id = str(user.id)
        battle_state = self.__wild_battle_states[user_id]

        await interaction.response.defer()

        # Extract move name from custom_id
        move_name = interaction.data['custom_id'].replace('wild_battle_move_', '')

        import random
        import math
        moves_config = load_json_config('moves.json')
        type_effectiveness = load_json_config('typeEffectiveness.json')
        from helpers.specialmoves import (
            handle_rest, handle_recover, calculate_drain_heal,
            calculate_night_shade_damage, calculate_leech_seed_damage,
            check_dream_eater_valid, check_accuracy, get_special_function,
            handle_haze
        )
        from helpers.statstages import apply_stat_change, apply_secondary_stat_change

        player_move_data = moves_config.get(move_name, {})
        player_power = player_move_data.get('power', 0)
        player_special_fn = get_special_function(player_move_data)

        log_lines = []
        log_lines.append(f"**Turn {battle_state.turn_number}:**")

        # Safety: init ailments if missing
        if not hasattr(battle_state, 'player_ailment') or battle_state.player_ailment is None:
            battle_state.player_ailment = AilmentClass(battle_state.player_pokemon.trainerId)
            battle_state.enemy_ailment = AilmentClass('wild_enemy')

        # Safety: init special move tracking if missing
        if not hasattr(battle_state, 'rest_turns_player'):
            battle_state.rest_turns_player = 0
            battle_state.rest_turns_enemy = 0
            battle_state.leech_seed_player = False
            battle_state.leech_seed_enemy = False
            battle_state.player_stat_stages.reset()
            battle_state.enemy_stat_stages.reset()

        if not hasattr(battle_state, 'player_stat_stages'):
            from helpers.statstages import StatStages
            battle_state.player_stat_stages = StatStages()
            battle_state.enemy_stat_stages = StatStages()

        p_ailment = battle_state.player_ailment
        e_ailment = battle_state.enemy_ailment
        p_stages = battle_state.player_stat_stages
        e_stages = battle_state.enemy_stat_stages

        p_name = battle_state.player_pokemon.pokemonName.capitalize()
        w_name = f"Wild {battle_state.wild_pokemon.pokemonName.capitalize()}"
        move_display = move_name.replace('-', ' ').title()

        # =====================================================================
        # PLAYER'S TURN - Check Rest sleep first
        # =====================================================================
        player_can_attack = True
        player_burn_halve = False
        player_hit = False

        if battle_state.rest_turns_player > 0:
            battle_state.rest_turns_player -= 1
            if battle_state.rest_turns_player == 0:
                p_ailment.sleep = False
                p_ailment.turnCounter = 0
                log_lines.append(f"💤 {p_name} woke up from Rest!")
            else:
                log_lines.append(f"💤 {p_name} is sleeping from Rest!")
            player_can_attack = False

        elif p_ailment.sleep:
            if p_ailment.turnCounter >= random.randint(1, 7):
                p_ailment.sleep = False
                p_ailment.turnCounter = 0
                log_lines.append(f"💤 {p_name} woke up!")
            else:
                p_ailment.turnCounter += 1
                log_lines.append(f"💤 {p_name} is fast asleep!")
                player_can_attack = False

        elif p_ailment.freeze:
            if random.randint(1, 5) == 1:
                p_ailment.freeze = False
                log_lines.append(f"🧊 {p_name} thawed out!")
            else:
                log_lines.append(f"🧊 {p_name} is frozen solid!")
                player_can_attack = False

        elif p_ailment.paralysis:
            if random.randint(1, 4) == 1:
                log_lines.append(f"⚡ {p_name} is paralyzed and can't move!")
                player_can_attack = False

        elif p_ailment.confusion:
            if p_ailment.turnCounter >= random.randint(2, 5):
                p_ailment.confusion = False
                p_ailment.turnCounter = 0
                log_lines.append(f"💫 {p_name} snapped out of confusion!")
            else:
                p_ailment.turnCounter += 1
                if random.randint(1, 2) == 1:
                    p_stats = battle_state.player_pokemon.getPokeStats()
                    self_damage = int(((2 * battle_state.player_pokemon.currentLevel / 5 + 2) * 40 * (p_stats['attack'] / p_stats['defense']) / 50 + 2))
                    self_damage = max(1, self_damage)
                    battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - self_damage)
                    log_lines.append(f"💫 {p_name} is confused and hurt itself for {self_damage} damage!")
                    player_can_attack = False

        elif p_ailment.trap:
            if p_ailment.turnCounter >= random.randint(2, 5):
                p_ailment.trap = False
                p_ailment.turnCounter = 0
                log_lines.append(f"🪢 {p_name} broke free!")
            else:
                p_ailment.turnCounter += 1
                p_stats = battle_state.player_pokemon.getPokeStats()
                trap_damage = max(1, p_stats['hp'] // 16)
                battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - trap_damage)
                log_lines.append(f"🪢 {p_name} is trapped! Took {trap_damage} damage!")
                player_can_attack = False

        if p_ailment.burn:
            player_burn_halve = True

        # =====================================================================
        # PLAYER ATTACKS (if able)
        # =====================================================================
        if player_can_attack:
            p_stats = battle_state.player_pokemon.getPokeStats()
            p_max_hp = p_stats['hp']
            w_stats = battle_state.wild_pokemon.getPokeStats()
            w_max_hp = w_stats['hp']

            if 'stat_change' in player_move_data and not player_special_fn:
                move_hit = check_accuracy(player_move_data.get('accuracy', 100))
                if move_hit:
                    log_lines.append(f"• {p_name} used {move_display}!")
                    apply_stat_change(
                        player_move_data, p_stages, e_stages,
                        log_lines, p_name, w_name
                    )
                else:
                    log_lines.append(f"• {p_name} used {move_display} but it missed!")
                player_hit = True

            elif player_special_fn == 'haze':
                handle_haze(p_stages, e_stages)
                log_lines.append(f"• {p_name} used Haze! All stat changes were eliminated!")
                player_hit = True

            elif player_special_fn == 'rest':
                heal_amount, new_hp = handle_rest(battle_state.player_pokemon.currentHP, p_max_hp)
                battle_state.player_pokemon.currentHP = new_hp
                battle_state.rest_turns_player = 2
                p_ailment.resetAilments()
                p_ailment.sleep = True
                log_lines.append(f"• {p_name} used Rest! Recovered {heal_amount} HP and fell asleep! 💤")
                player_hit = True

            elif player_special_fn == 'recover':
                actual_heal, new_hp = handle_recover(battle_state.player_pokemon.currentHP, p_max_hp)
                battle_state.player_pokemon.currentHP = new_hp
                log_lines.append(f"• {p_name} used Recover! Restored {actual_heal} HP! 💚")
                player_hit = True

            elif player_special_fn == 'night_shade':
                if check_accuracy(player_move_data.get('accuracy', 100)):
                    ns_damage = calculate_night_shade_damage(battle_state.player_pokemon.currentLevel)
                    battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - ns_damage)
                    log_lines.append(f"• {p_name} used Night Shade! Dealt {ns_damage} damage!")
                    player_hit = True
                else:
                    log_lines.append(f"• {p_name} used Night Shade but it missed!")

            elif player_special_fn == 'leech_seed':
                if check_accuracy(player_move_data.get('accuracy', 100)):
                    if not battle_state.leech_seed_enemy:
                        battle_state.leech_seed_enemy = True
                        log_lines.append(f"• {p_name} used Leech Seed! {w_name} was seeded! 🌱")
                    else:
                        log_lines.append(f"• {p_name} used Leech Seed but {w_name} is already seeded!")
                    player_hit = True
                else:
                    log_lines.append(f"• {p_name} used Leech Seed but it missed!")

            elif player_special_fn == 'dream_eater':
                if e_ailment.sleep or battle_state.rest_turns_enemy > 0:
                    player_damage, player_hit = calculate_battle_damage(
                        battle_state.player_pokemon, battle_state.enemy_pokemon,
                        move_name, moves_config, type_effectiveness,
                        p_stages, e_stages
                    )
                    if player_burn_halve and player_move_data.get('damage_class') == 'physical' and player_damage > 0:
                        player_damage = max(1, player_damage // 2)
                    if player_hit and player_damage > 0:
                        battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - player_damage)
                        drain_heal = calculate_drain_heal(player_damage)
                        battle_state.player_pokemon.currentHP = min(p_max_hp, battle_state.player_pokemon.currentHP + drain_heal)
                        log_lines.append(f"• {p_name} used Dream Eater! Dealt {player_damage} damage and drained {drain_heal} HP! 💜")
                    elif player_hit:
                        log_lines.append(f"• {p_name} used Dream Eater but dealt no damage!")
                    else:
                        log_lines.append(f"• {p_name} used Dream Eater but it missed!")
                else:
                    log_lines.append(f"• {p_name} used Dream Eater but it failed! Target is not asleep.")
                    player_hit = False

            elif player_special_fn == 'drain':
                player_damage, player_hit = calculate_battle_damage(
                    battle_state.player_pokemon, battle_state.enemy_pokemon,
                    move_name, moves_config, type_effectiveness,
                    p_stages, e_stages
                )
                if player_burn_halve and player_move_data.get('damage_class') == 'physical' and player_damage > 0:
                    player_damage = max(1, player_damage // 2)
                if player_hit and player_damage > 0:
                    battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - player_damage)
                    drain_heal = calculate_drain_heal(player_damage)
                    battle_state.player_pokemon.currentHP = min(p_max_hp, battle_state.player_pokemon.currentHP + drain_heal)
                    log_lines.append(f"• {p_name} used {move_display}! Dealt {player_damage} damage and drained {drain_heal} HP! 💚")
                elif player_hit:
                    log_lines.append(f"• {p_name} used {move_display}!")
                else:
                    log_lines.append(f"• {p_name} used {move_display} but it missed!")

            else:
                # --- NORMAL ATTACK ---
                player_damage, player_hit = calculate_battle_damage(
                    battle_state.player_pokemon, battle_state.wild_pokemon,
                    move_name, moves_config, type_effectiveness,
                    p_stages, e_stages
                )

                if player_burn_halve and player_move_data.get('damage_class') == 'physical' and player_damage > 0:
                    player_damage = max(1, player_damage // 2)

                if player_hit and player_damage > 0:
                    battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - player_damage)
                    log_lines.append(f"• {p_name} used {move_display}! Dealt {player_damage} damage!")
                elif player_hit and (player_power is None or player_power == 0):
                    log_lines.append(f"• {p_name} used {move_display}!")
                else:
                    log_lines.append(f"• {p_name} used {move_display} but it missed!")
                    player_hit = False

                # Roll ailment on wild pokemon
                if player_hit:
                    ailment_name = player_move_data.get('ailment', '')
                    if ailment_name:
                        ailment_chance = player_move_data.get('ailment_chance', 0)
                        should_apply = False
                        if ailment_chance == 0 and player_move_data.get('damage_class') == 'status':
                            should_apply = True
                        elif ailment_chance > 0:
                            should_apply = random.randint(1, 100) <= ailment_chance

                        if should_apply and not self.__has_ailment(e_ailment, battle_state.rest_turns_enemy):
                            e_ailment.setAilment(ailment_name)
                            log_lines.append(f"🔥 {w_name} is now {self.__ailment_display(ailment_name)}!")

                    if player_move_data.get('moveType') == 'fire' and e_ailment.freeze:
                        e_ailment.freeze = False
                        log_lines.append(f"🔥 {w_name} was thawed by the fire!")

                    # Secondary stat change on damaging moves (e.g. Acid, Psychic)
                    if player_hit and player_damage > 0:
                        apply_secondary_stat_change(
                            player_move_data, p_stages, e_stages,
                            log_lines, p_name, w_name
                        )

        # =====================================================================
        # CHECK: Did wild Pokemon faint?
        # =====================================================================
        if battle_state.wild_pokemon.currentHP <= 0:
            log_lines.append(f"💀 {w_name} fainted!")

            from services.leaderboardclass import leaderboard as LeaderboardClass
            lb = LeaderboardClass(str(user.id))
            lb.victory()
            lb.actions()

            enc = EncounterClass(battle_state.player_pokemon, battle_state.wild_pokemon)
            enc.updateUniqueEncounters()
            expObj = exp(battle_state.wild_pokemon)
            expGained = expObj.getExpGained()
            evGained = expObj.getEffortValue()

            current_hp = battle_state.player_pokemon.currentHP
            old_level = battle_state.player_pokemon.currentLevel
            levelUp, expMsg, pendingMoves = battle_state.player_pokemon.processBattleOutcome(expGained, evGained, current_hp)

            auto_learned_moves = []
            if expMsg and "learned" in expMsg.lower():
                import re
                learned_matches = re.findall(r'learned ([a-z\-]+)', expMsg.lower())
                auto_learned_moves.extend(learned_matches)

            if levelUp:
                new_level = battle_state.player_pokemon.currentLevel
                log_lines.append(f"⬆️ {p_name} leveled up to {new_level}!")

            evolution_name = None
            if hasattr(battle_state.player_pokemon, 'evolvedInto') and battle_state.player_pokemon.evolvedInto:
                evolution_name = battle_state.player_pokemon.evolvedInto
                log_lines.append(f"✨ {p_name} is evolving into {evolution_name.capitalize()}!")
                # addExperience() already handled evolution internally via self.load()
                # battle_state.player_pokemon is already the evolved pokemon - don't replace it

            if levelUp or (pendingMoves and len(pendingMoves) > 0):
                battle_state.level_up_data = {
                    'pokemon': battle_state.player_pokemon,
                    'old_level': old_level,
                    'new_level': battle_state.player_pokemon.currentLevel,
                    'auto_learned_moves': auto_learned_moves,
                    'pending_moves': pendingMoves if pendingMoves else [],
                    'evolution_name': evolution_name
                }

            battle_state.battle_log = ["\n".join(log_lines)]
            battle_state.player_pokemon.save()
            await self.__handle_wild_battle_victory(interaction, battle_state)

            if hasattr(battle_state, 'level_up_data') and battle_state.level_up_data:
                data = battle_state.level_up_data
                level_up_embed = self.__create_level_up_embed(
                    data['pokemon'], data['old_level'], data['new_level'],
                    learned_moves=data['auto_learned_moves'],
                    evolution_name=data['evolution_name']
                )
                await interaction.followup.send(embed=level_up_embed, ephemeral=True)
                if data['pending_moves']:
                    await self.__handle_move_learning(interaction, data['pokemon'], data['pending_moves'], battle_state)

            del self.__wild_battle_states[user_id]
            return

        # Check if player fainted from confusion/trap self-damage before enemy turn
        if battle_state.player_pokemon.currentHP <= 0:
            log_lines.append(f"💀 Your {p_name} fainted!")
            battle_state.battle_log = ["\n".join(log_lines)]
            battle_state.player_pokemon.save()
            await self.__handle_wild_battle_defeat(interaction, battle_state)
            del self.__wild_battle_states[user_id]
            return

        # =====================================================================
        # ENEMY'S TURN - Check Rest sleep first
        # =====================================================================
        enemy_can_attack = True

        if battle_state.rest_turns_enemy > 0:
            battle_state.rest_turns_enemy -= 1
            if battle_state.rest_turns_enemy == 0:
                e_ailment.sleep = False
                e_ailment.turnCounter = 0
                log_lines.append(f"💤 {w_name} woke up from Rest!")
            else:
                log_lines.append(f"💤 {w_name} is sleeping from Rest!")
            enemy_can_attack = False

        elif e_ailment.sleep:
            if e_ailment.turnCounter >= random.randint(1, 7):
                e_ailment.sleep = False
                e_ailment.turnCounter = 0
                log_lines.append(f"💤 {w_name} woke up!")
            else:
                e_ailment.turnCounter += 1
                log_lines.append(f"💤 {w_name} is fast asleep!")
                enemy_can_attack = False

        elif e_ailment.freeze:
            if random.randint(1, 5) == 1:
                e_ailment.freeze = False
                log_lines.append(f"🧊 {w_name} thawed out!")
            else:
                log_lines.append(f"🧊 {w_name} is frozen solid!")
                enemy_can_attack = False

        elif e_ailment.paralysis:
            if random.randint(1, 4) == 1:
                log_lines.append(f"⚡ {w_name} is paralyzed and can't move!")
                enemy_can_attack = False

        elif e_ailment.confusion:
            if e_ailment.turnCounter >= random.randint(2, 5):
                e_ailment.confusion = False
                e_ailment.turnCounter = 0
                log_lines.append(f"💫 {w_name} snapped out of confusion!")
            else:
                e_ailment.turnCounter += 1
                if random.randint(1, 2) == 1:
                    e_stats = battle_state.wild_pokemon.getPokeStats()
                    self_damage = int(((2 * battle_state.wild_pokemon.currentLevel / 5 + 2) * 40 * (e_stats['attack'] / e_stats['defense']) / 50 + 2))
                    self_damage = max(1, self_damage)
                    battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - self_damage)
                    log_lines.append(f"💫 {w_name} is confused and hurt itself for {self_damage} damage!")
                    enemy_can_attack = False

        elif e_ailment.trap:
            if e_ailment.turnCounter >= random.randint(2, 5):
                e_ailment.trap = False
                e_ailment.turnCounter = 0
                log_lines.append(f"🪢 {w_name} broke free!")
            else:
                e_ailment.turnCounter += 1
                e_stats = battle_state.wild_pokemon.getPokeStats()
                trap_damage = max(1, e_stats['hp'] // 16)
                battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - trap_damage)
                log_lines.append(f"🪢 {w_name} is trapped! Took {trap_damage} damage!")
                enemy_can_attack = False

        # =====================================================================
        # WILD POKEMON ATTACKS (if able)
        # =====================================================================
        if enemy_can_attack:
            wild_moves = [m for m in battle_state.wild_pokemon.getMoves() if m and m.lower() != 'none']
            if wild_moves:
                wild_move_name = random.choice(wild_moves)
                wild_move_data = moves_config.get(wild_move_name, {})
                wild_special_fn = get_special_function(wild_move_data)
                wild_move_display = wild_move_name.replace('-', ' ').title()

                w_stats = battle_state.wild_pokemon.getPokeStats()
                w_max_hp = w_stats['hp']
                p_stats = battle_state.player_pokemon.getPokeStats()
                p_max_hp = p_stats['hp']

                wild_burn_halve = e_ailment.burn

                if 'stat_change' in wild_move_data and not wild_special_fn:
                    move_hit = check_accuracy(wild_move_data.get('accuracy', 100))
                    if move_hit:
                        log_lines.append(f"• {w_name} used {wild_move_display}!")
                        apply_stat_change(
                            wild_move_data, e_stages, p_stages,
                            log_lines, w_name, p_name
                        )
                    else:
                        log_lines.append(f"• {w_name} used {wild_move_display} but it missed!")

                elif wild_special_fn == 'haze':
                    handle_haze(p_stages, e_stages)
                    log_lines.append(f"• {w_name} used Haze! All stat changes were eliminated!")

                elif wild_special_fn == 'rest':
                    heal_amount, new_hp = handle_rest(battle_state.wild_pokemon.currentHP, w_max_hp)
                    battle_state.wild_pokemon.currentHP = new_hp
                    battle_state.rest_turns_enemy = 2
                    e_ailment.resetAilments()
                    e_ailment.sleep = True
                    log_lines.append(f"• {w_name} used Rest! Recovered {heal_amount} HP and fell asleep! 💤")

                elif wild_special_fn == 'recover':
                    actual_heal, new_hp = handle_recover(battle_state.wild_pokemon.currentHP, w_max_hp)
                    battle_state.wild_pokemon.currentHP = new_hp
                    log_lines.append(f"• {w_name} used Recover! Restored {actual_heal} HP! 💚")

                elif wild_special_fn == 'night_shade':
                    if check_accuracy(wild_move_data.get('accuracy', 100)):
                        ns_damage = calculate_night_shade_damage(battle_state.wild_pokemon.currentLevel)
                        battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - ns_damage)
                        log_lines.append(f"• {w_name} used Night Shade! Dealt {ns_damage} damage!")
                    else:
                        log_lines.append(f"• {w_name} used Night Shade but it missed!")

                elif wild_special_fn == 'leech_seed':
                    if check_accuracy(wild_move_data.get('accuracy', 100)):
                        if not battle_state.leech_seed_player:
                            battle_state.leech_seed_player = True
                            log_lines.append(f"• {w_name} used Leech Seed! Your Pokemon was seeded! 🌱")
                        else:
                            log_lines.append(f"• {w_name} used Leech Seed but your Pokemon is already seeded!")
                    else:
                        log_lines.append(f"• {w_name} used Leech Seed but it missed!")

                elif wild_special_fn == 'dream_eater':
                    if p_ailment.sleep or battle_state.rest_turns_player > 0:
                        wild_damage, wild_hit = calculate_battle_damage(
                            battle_state.wild_pokemon, battle_state.player_pokemon,
                            wild_move_name, moves_config, type_effectiveness,
                            e_stages, p_stages
                        )
                        if wild_burn_halve and wild_move_data.get('damage_class') == 'physical' and wild_damage > 0:
                            wild_damage = max(1, wild_damage // 2)
                        if wild_hit and wild_damage > 0:
                            battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - wild_damage)
                            drain_heal = calculate_drain_heal(wild_damage)
                            battle_state.wild_pokemon.currentHP = min(w_max_hp, battle_state.wild_pokemon.currentHP + drain_heal)
                            log_lines.append(f"• {w_name} used Dream Eater! Dealt {wild_damage} damage and drained {drain_heal} HP! 💜")
                        elif wild_hit:
                            log_lines.append(f"• {w_name} used Dream Eater but dealt no damage!")
                        else:
                            log_lines.append(f"• {w_name} used Dream Eater but it missed!")
                    else:
                        log_lines.append(f"• {w_name} used Dream Eater but it failed! Target is not asleep.")

                elif wild_special_fn == 'drain':
                    wild_damage, wild_hit = calculate_battle_damage(
                        battle_state.wild_pokemon, battle_state.player_pokemon,
                        wild_move_name, moves_config, type_effectiveness,
                        e_stages, p_stages
                    )
                    if wild_burn_halve and wild_move_data.get('damage_class') == 'physical' and wild_damage > 0:
                        wild_damage = max(1, wild_damage // 2)
                    if wild_hit and wild_damage > 0:
                        battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - wild_damage)
                        drain_heal = calculate_drain_heal(wild_damage)
                        battle_state.wild_pokemon.currentHP = min(w_max_hp, battle_state.wild_pokemon.currentHP + drain_heal)
                        log_lines.append(f"• {w_name} used {wild_move_display}! Dealt {wild_damage} damage and drained {drain_heal} HP! 💚")
                    elif wild_hit:
                        log_lines.append(f"• {w_name} used {wild_move_display}!")
                    else:
                        log_lines.append(f"• {w_name} used {wild_move_display} but it missed!")

                else:
                    # --- NORMAL WILD ATTACK ---
                    wild_damage, wild_hit = calculate_battle_damage(
                        battle_state.wild_pokemon, battle_state.player_pokemon,
                        wild_move_name, moves_config, type_effectiveness,
                        e_stages, p_stages
                    )

                    if wild_burn_halve and wild_move_data.get('damage_class') == 'physical' and wild_damage > 0:
                        wild_damage = max(1, wild_damage // 2)

                    if wild_hit and wild_damage > 0:
                        battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - wild_damage)
                        log_lines.append(f"• {w_name} used {wild_move_display}! Dealt {wild_damage} damage!")
                    elif wild_hit and (wild_move_data.get('power') is None or wild_move_data.get('power', 0) == 0):
                        log_lines.append(f"• {w_name} used {wild_move_display}!")
                    else:
                        log_lines.append(f"• {w_name} used {wild_move_display} but it missed!")
                        wild_hit = False

                    # Roll ailment on player
                    if wild_hit:
                        ailment_name = wild_move_data.get('ailment', '')
                        if ailment_name:
                            ailment_chance = wild_move_data.get('ailment_chance', 0)
                            should_apply = False
                            if ailment_chance == 0 and wild_move_data.get('damage_class') == 'status':
                                should_apply = True
                            elif ailment_chance > 0:
                                should_apply = random.randint(1, 100) <= ailment_chance

                            if should_apply and not self.__has_ailment(p_ailment, battle_state.rest_turns_player):
                                p_ailment.setAilment(ailment_name)
                                log_lines.append(f"🔥 {p_name} is now {self.__ailment_display(ailment_name)}!")

                        if wild_move_data.get('moveType') == 'fire' and p_ailment.freeze:
                            p_ailment.freeze = False
                            log_lines.append(f"🔥 {p_name} was thawed by the fire!")

                        # Secondary stat change on damaging moves
                        if wild_hit and wild_damage > 0:
                            apply_secondary_stat_change(
                                wild_move_data, e_stages, p_stages,
                                log_lines, w_name, p_name
                            )

        # =====================================================================
        # END OF TURN - Burn/Poison residual damage
        # =====================================================================
        if p_ailment.burn and battle_state.player_pokemon.currentHP > 0:
            p_stats = battle_state.player_pokemon.getPokeStats()
            burn_damage = max(1, p_stats['hp'] // 16)
            battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - burn_damage)
            log_lines.append(f"🔥 {p_name} is hurt by its burn! (-{burn_damage})")

        if p_ailment.poison and battle_state.player_pokemon.currentHP > 0:
            p_stats = battle_state.player_pokemon.getPokeStats()
            poison_damage = max(1, p_stats['hp'] // 16)
            battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - poison_damage)
            log_lines.append(f"☠️ {p_name} is hurt by poison! (-{poison_damage})")

        if e_ailment.burn and battle_state.wild_pokemon.currentHP > 0:
            e_stats = battle_state.wild_pokemon.getPokeStats()
            burn_damage = max(1, e_stats['hp'] // 16)
            battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - burn_damage)
            log_lines.append(f"🔥 {w_name} is hurt by its burn! (-{burn_damage})")

        if e_ailment.poison and battle_state.wild_pokemon.currentHP > 0:
            e_stats = battle_state.wild_pokemon.getPokeStats()
            poison_damage = max(1, e_stats['hp'] // 16)
            battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - poison_damage)
            log_lines.append(f"☠️ {w_name} is hurt by poison! (-{poison_damage})")

        # =====================================================================
        # END OF TURN - Leech Seed drain
        # =====================================================================
        if battle_state.leech_seed_player and battle_state.player_pokemon.currentHP > 0:
            p_stats = battle_state.player_pokemon.getPokeStats()
            seed_damage = calculate_leech_seed_damage(p_stats['hp'])
            battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - seed_damage)
            w_stats = battle_state.wild_pokemon.getPokeStats()
            battle_state.wild_pokemon.currentHP = min(w_stats['hp'], battle_state.wild_pokemon.currentHP + seed_damage)
            log_lines.append(f"🌱 {p_name} had its energy drained by Leech Seed! (-{seed_damage} HP)")

        if battle_state.leech_seed_enemy and battle_state.wild_pokemon.currentHP > 0:
            w_stats = battle_state.wild_pokemon.getPokeStats()
            seed_damage = calculate_leech_seed_damage(w_stats['hp'])
            battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - seed_damage)
            p_stats = battle_state.player_pokemon.getPokeStats()
            battle_state.player_pokemon.currentHP = min(p_stats['hp'], battle_state.player_pokemon.currentHP + seed_damage)
            log_lines.append(f"🌱 {w_name} had its energy drained by Leech Seed! (-{seed_damage} HP)")

        # =====================================================================
        # POST-TURN FAINT CHECKS
        # =====================================================================
        # Check if wild Pokemon fainted from burn/poison/leech seed
        if battle_state.wild_pokemon.currentHP <= 0:
            log_lines.append(f"💀 {w_name} fainted!")

            from services.leaderboardclass import leaderboard as LeaderboardClass
            lb = LeaderboardClass(str(user.id))
            lb.victory()
            lb.actions()

            enc = EncounterClass(battle_state.player_pokemon, battle_state.wild_pokemon)
            enc.updateUniqueEncounters()
            expObj = exp(battle_state.wild_pokemon)
            expGained = expObj.getExpGained()
            evGained = expObj.getEffortValue()

            current_hp = battle_state.player_pokemon.currentHP
            old_level = battle_state.player_pokemon.currentLevel
            levelUp, expMsg, pendingMoves = battle_state.player_pokemon.processBattleOutcome(expGained, evGained, current_hp)

            auto_learned_moves = []
            if expMsg and "learned" in expMsg.lower():
                import re
                learned_matches = re.findall(r'learned ([a-z\-]+)', expMsg.lower())
                auto_learned_moves.extend(learned_matches)

            if levelUp:
                new_level = battle_state.player_pokemon.currentLevel
                log_lines.append(f"⬆️ {p_name} leveled up to {new_level}!")

            evolution_name = None
            if hasattr(battle_state.player_pokemon, 'evolvedInto') and battle_state.player_pokemon.evolvedInto:
                evolution_name = battle_state.player_pokemon.evolvedInto
                log_lines.append(f"✨ {p_name} is evolving into {evolution_name.capitalize()}!")
                evolved_pokemon = PokemonClass(battle_state.player_pokemon.discordId, evolution_name)
                evolved_pokemon.load()
                battle_state.player_pokemon = evolved_pokemon

            if levelUp or (pendingMoves and len(pendingMoves) > 0):
                battle_state.level_up_data = {
                    'pokemon': battle_state.player_pokemon,
                    'old_level': old_level,
                    'new_level': battle_state.player_pokemon.currentLevel,
                    'auto_learned_moves': auto_learned_moves,
                    'pending_moves': pendingMoves if pendingMoves else [],
                    'evolution_name': evolution_name
                }

            battle_state.battle_log = ["\n".join(log_lines)]
            battle_state.player_pokemon.save()
            await self.__handle_wild_battle_victory(interaction, battle_state)

            if hasattr(battle_state, 'level_up_data') and battle_state.level_up_data:
                data = battle_state.level_up_data
                level_up_embed = self.__create_level_up_embed(
                    data['pokemon'], data['old_level'], data['new_level'],
                    learned_moves=data['auto_learned_moves'],
                    evolution_name=data['evolution_name']
                )
                await interaction.followup.send(embed=level_up_embed, ephemeral=True)
                if data['pending_moves']:
                    await self.__handle_move_learning(interaction, data['pokemon'], data['pending_moves'], battle_state)

            del self.__wild_battle_states[user_id]
            return

        # Check if player fainted from burn/poison/leech seed/enemy attack
        if battle_state.player_pokemon.currentHP <= 0:
            log_lines.append(f"💀 Your {p_name} fainted!")
            battle_state.battle_log = ["\n".join(log_lines)]
            battle_state.player_pokemon.save()

            from services.leaderboardclass import leaderboard as LeaderboardClass
            lb = LeaderboardClass(str(user.id))
            lb.defeat()
            lb.actions()

            await self.__handle_wild_battle_defeat(interaction, battle_state)
            del self.__wild_battle_states[user_id]
            return

        # Battle continues
        battle_state.battle_log = ["\n".join(log_lines)]
        battle_state.turn_number += 1

        embed = self.__create_wild_battle_embed(user, battle_state)
        view = self.__create_battle_move_buttons_with_items(battle_state)
        await interaction.message.edit(embed=embed, view=view)

    def __create_wild_battle_embed(self, user: discord.User, battle_state: WildBattleState) -> discord.Embed:
        """Create an embed showing the current wild battle state"""
        player_poke = battle_state.player_pokemon
        wild_poke = battle_state.wild_pokemon
        
        player_stats = player_poke.getPokeStats()
        wild_stats = wild_poke.getPokeStats()
        
        # Calculate HP percentages for visual bar
        player_hp_pct = (player_poke.currentHP / player_stats['hp']) * 100 if player_stats['hp'] > 0 else 0
        wild_hp_pct = (wild_poke.currentHP / wild_stats['hp']) * 100 if wild_stats['hp'] > 0 else 0

        # Get ailment emojis
        p_ailment_emoji = self.__get_ailment_emoji(battle_state.player_ailment, getattr(battle_state, 'rest_turns_player', 0))
        e_ailment_emoji = self.__get_ailment_emoji(battle_state.enemy_ailment, getattr(battle_state, 'rest_turns_enemy', 0))



        embed = discord.Embed(
            title=f"⚔️ Wild Battle: {user.display_name} vs Wild {wild_poke.pokemonName.capitalize()}",
            description=f"**Turn {battle_state.turn_number}**\nChoose your move!",
            color=discord.Color.gold()
        )
        
        # Wild Pokemon info FIRST
        wild_types = wild_poke.type1
        if wild_poke.type2:
            wild_types += f", {wild_poke.type2}"
        
        embed.add_field(
            name=f"❤️ Wild {wild_poke.pokemonName.capitalize()} (Lv.{wild_poke.currentLevel}){e_ailment_emoji}",
            value=f"**HP:** {wild_poke.currentHP}/{wild_stats['hp']} {create_hp_bar(wild_hp_pct)}\n"
                f"**Type:** {wild_types}",
            inline=False
        )
        
        # Player Pokemon info SECOND
        player_types = player_poke.type1
        if player_poke.type2:
            player_types += f", {player_poke.type2}"
        
        from .functions import get_pokemon_display_name
        player_display = get_pokemon_display_name(player_poke)
        embed.add_field(
            name=f"💚 Your {player_display} (Lv.{player_poke.currentLevel}){p_ailment_emoji}",
            value=f"**HP:** {player_poke.currentHP}/{player_stats['hp']} {create_hp_bar(player_hp_pct)}\n"
                f"**Type:** {player_types}",
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
        
        embed.set_thumbnail(url=wild_poke.frontSpriteURL)
        embed.set_image(url=player_poke.backSpriteURL)
        
        return embed
    

    async def on_nav_map_click(self, interaction: discord.Interaction, already_deferred: bool = False):
        """Handle Map button click - show map with sprite and buttons"""
        user = interaction.user
        
        # Check if response was already done
        if not already_deferred and not interaction.response.is_done():
            await interaction.response.defer()
        
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        # Get available actions at this location
        location_obj = LocationClass(str(user.id))
        methods = location_obj.getMethods()
        quest_buttons = self.__get_available_quests(str(user.id), location.name)
        gym_button = self.__get_gym_button(str(user.id), location.locationId)
        wild_trainers_button = self.__get_wild_trainers_button(str(user.id), location.locationId)
        
        from .constant import LOCATION_DISPLAY_NAMES
        location_name = LOCATION_DISPLAY_NAMES.get(location.name, location.name.replace('-', ' ').title())
        
        # Create embed
        embed = discord.Embed(
            title=f"{location_name}",
            description=f"You are at {location_name}.",
            color=discord.Color.blue()
        )
        
        # Set sprite if available
        if location.spritePath:
            try:
                # Convert to full file system path
                full_sprite_path = get_sprite_path(location.spritePath)
                sprite_file = discord.File(full_sprite_path, filename=f"{location.name}.png")

                temp_message = await self.sendToLoggingChannel(f'{user.display_name} viewing map', sprite_file)
                if temp_message and temp_message.attachments:
                    attachment = temp_message.attachments[0]
                    embed.set_image(url=attachment.url)
            except Exception as e:
                print(f"Error loading location sprite from file: {e}")
                try:
                    sprite_url = f"https://pokesprites.joshkohut.com/sprites/locations/{location.name}.png"
                    embed.set_image(url=sprite_url)
                except:
                    pass
        
        # Create view with direction buttons
        view = View()
        
        # ROW 0: North/South buttons
        if location.north:
            north_name = LOCATION_DISPLAY_NAMES.get(location.north, location.north)
            north_btn = Button(style=ButtonStyle.gray, emoji='⬆️', label=f"{north_name[:15]}", custom_id='dir_north', row=0)
            north_btn.callback = self.on_direction_click
            view.add_item(north_btn)
        else:
            north_btn = Button(style=ButtonStyle.gray, emoji='⬆️', label="---", custom_id='dir_north_disabled', disabled=True, row=0)
            view.add_item(north_btn)
        
        if location.south:
            south_name = LOCATION_DISPLAY_NAMES.get(location.south, location.south)
            south_btn = Button(style=ButtonStyle.gray, emoji='⬇️', label=f"{south_name[:15]}", custom_id='dir_south', row=0)
            south_btn.callback = self.on_direction_click
            view.add_item(south_btn)
        else:
            south_btn = Button(style=ButtonStyle.gray, emoji='⬇️', label="---", custom_id='dir_south_disabled', disabled=True, row=0)
            view.add_item(south_btn)
        
        # ROW 1: East/West buttons
        if location.west:
            west_name = LOCATION_DISPLAY_NAMES.get(location.west, location.west)
            west_btn = Button(style=ButtonStyle.gray, emoji='⬅️', label=f"{west_name[:15]}", custom_id='dir_west', row=1)
            west_btn.callback = self.on_direction_click
            view.add_item(west_btn)
        else:
            west_btn = Button(style=ButtonStyle.gray, emoji='⬅️', label="---", custom_id='dir_west_disabled', disabled=True, row=1)
            view.add_item(west_btn)
        
        if location.east:
            east_name = LOCATION_DISPLAY_NAMES.get(location.east, location.east)
            east_btn = Button(style=ButtonStyle.gray, emoji='➡️', label=f"{east_name[:15]}", custom_id='dir_east', row=1)
            east_btn.callback = self.on_direction_click
            view.add_item(east_btn)
        else:
            east_btn = Button(style=ButtonStyle.gray, emoji='➡️', label="---", custom_id='dir_east_disabled', disabled=True, row=1)
            view.add_item(east_btn)
        
        # AUX button (if exists)
        if hasattr(location, 'aux') and location.aux:
            aux_name = LOCATION_DISPLAY_NAMES.get(location.aux, location.aux)
            aux_btn = Button(style=ButtonStyle.gray, emoji='🔀', label=f"{aux_name[:15]}", custom_id='dir_aux', row=1)
            aux_btn.callback = self.on_direction_click
            view.add_item(aux_btn)

        # ROW 2: Action buttons (Encounters, Quests, Gym, Wild Trainers)
        if len(methods) > 0:
            enc_btn = Button(style=ButtonStyle.green, label="⚔️ Encounters", custom_id='nav_encounters', row=2)
            enc_btn.callback = self.on_nav_encounters_click
            view.add_item(enc_btn)
        
        if len(quest_buttons) > 0:
            quest_btn = Button(style=ButtonStyle.blurple, label="📜 Quests", custom_id='nav_quests', row=2)
            quest_btn.callback = self.on_nav_quests_click
            view.add_item(quest_btn)
        
        if gym_button and not gym_button.disabled:
            gym_btn = Button(style=ButtonStyle.red, label="🏛️ Gym", custom_id='nav_gym', row=2)
            gym_btn.callback = self.on_gym_click
            view.add_item(gym_btn)
        
        # ADD WILD TRAINERS BUTTON
        if wild_trainers_button:
            view.add_item(wild_trainers_button)
        
        # ROW 3: Utility buttons
        bag_btn = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_bag', row=3)
        bag_btn.callback = self.on_nav_bag_click
        view.add_item(bag_btn)
        
        # Add Mart button if location has a Pokemart
        if self.__has_pokemart(location.locationId):
            mart_btn = Button(style=ButtonStyle.blurple, label="🏪 Mart", custom_id='nav_mart', row=3)
            mart_btn.callback = self.on_nav_mart_click
            view.add_item(mart_btn)

        if location.pokecenter:
            heal_btn = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal', row=3)
            heal_btn.callback = self.on_nav_heal_click
            view.add_item(heal_btn)
        
        message = await interaction.message.edit(embed=embed, view=view)
        
        # Update action state
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, location, trainer.getActivePokemon(), None, ''
        )



# =============================================================================
# SEPARATOR - NEXT METHOD
# =============================================================================

    async def on_direction_click(self, interaction: discord.Interaction):
        """Handle direction button clicks (North/South/East/West)"""
        user = interaction.user
        
        if str(user.id) not in self.__useractions:
            await interaction.response.send_message('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Get direction from custom_id (dir_north, dir_south, etc.)
        direction = interaction.data['custom_id'].replace('dir_', '')
        
        trainer = self._get_trainer(str(user.id))
        current_location = trainer.getLocation()
        
        # Get target location ID based on direction
        target_location_name = None
        if direction == 'north':
            target_location_name = current_location.north
        elif direction == 'south':
            target_location_name = current_location.south
        elif direction == 'east':
            target_location_name = current_location.east
        elif direction == 'west':
            target_location_name = current_location.west
        elif direction == 'aux':
            target_location_name = getattr(current_location, 'aux', None)

        if not target_location_name:
            await interaction.followup.send('Cannot go that direction.', ephemeral=True)
            return
        
        # Check for location blockers using quests.json
        from services.questclass import quests as QuestsClass
        from helpers.helpers import check_hm_usable
        
        quest_obj = QuestsClass(str(user.id))
        
        quests_data = self.__load_quests_data()
        location_blocked = False
        blocker_message = ""
        
        for quest_id, quest_data in quests_data.items():
            if quest_data.get('name') == target_location_name:
                blockers = quest_data.get('blockers', [])
                if blockers:
                    # Check each blocker individually for better error messages
                    missing_items = []
                    missing_pokemon = []
                    
                    for blocker in blockers:
                        # Check if it's an HM blocker
                        if blocker in ['HM01', 'HM02', 'HM03', 'HM04', 'HM05']:
                            # Check if they have the HM item
                            hm_attr = getattr(quest_obj.keyitems, blocker, False)
                            if not hm_attr:
                                missing_items.append(blocker.replace('_', ' ').title())
                                continue
                            
                            # Check if they have a Pokemon that can use it
                            can_use, compatible_pokemon = check_hm_usable(str(user.id), blocker)
                            if not can_use:
                                missing_pokemon.append(blocker)
                        else:
                            # Non-HM blocker, check normally
                            if quest_obj.locationBlocked([blocker]):
                                missing_items.append(blocker.replace('_', ' ').title())
                    
                    # Build error message
                    if missing_items or missing_pokemon:
                        location_blocked = True
                        error_parts = []
                        
                        if missing_items:
                            error_parts.append(f"Items: {', '.join(missing_items)}")
                        
                        if missing_pokemon:
                            hm_names = ', '.join(missing_pokemon)
                            error_parts.append(f"You need a Pokemon that can use {hm_names}")
                        
                        blocker_message = f'You cannot travel there yet.\n' + '\n'.join(error_parts)
                        break
        
        if location_blocked:
            await interaction.followup.send(blocker_message, ephemeral=True)
            return
        
        # Get the target location data
        location_obj = LocationClass()
        new_location = location_obj.getLocationByName(target_location_name)
        
        # Move to new location
        trainer.setLocation(new_location.locationId)
        
        # Recreate the map view with action buttons - PASS already_deferred=True
        await self.on_nav_map_click(interaction, already_deferred=True)



    async def on_nav_bag_click(self, interaction: discord.Interaction):
        """Handle Bag button click - show bag with items"""
        user = interaction.user
        self._current_user_id = str(user.id)
        await interaction.response.defer()
        
        # Create bag state
        bag_state = BagState(
            discord_id=str(user.id),
            message_id=interaction.message.id,
            channel_id=interaction.channel_id,
            current_view='items'
        )
        self.__bag_states[str(user.id)] = bag_state
        
        # Show items view
        embed = self.__create_items_embed(user)
        view = self.__create_bag_navigation_view('items')
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_flight_map_click(self, interaction: discord.Interaction):
        """Handle Flight Map button click"""
        user = interaction.user
        
        if str(user.id) not in self.__bag_states:
            await interaction.response.send_message('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Check if they have HM02
        from services.keyitemsclass import keyitems as KeyItemClass
        keyitems = KeyItemClass(str(user.id))
        
        if not keyitems.HM02:
            await interaction.followup.send('You need HM02 (Fly) to use the Flight Map!', ephemeral=True)
            return
        
        # Check if they have a Pokemon that can fly
        from helpers.helpers import check_hm_usable
        can_use, compatible_pokemon = check_hm_usable(str(user.id), 'HM02')
        
        if not can_use:
            await interaction.followup.send(
                'None of your party Pokemon can use Fly! You need a Pokemon that knows Fly.',
                ephemeral=True
            )
            return
        
        # Get current location
        from services.trainerclass import trainer as TrainerClass
        trainer = self._get_trainer(str(user.id))
        current_location = trainer.getLocation()
        
        # Create flight state
        from models.sessionstate import FlightState
        self.__flight_states[str(user.id)] = FlightState(str(user.id), current_location.name)
        
        # Show flight interface
        embed, view = await self.__create_flight_interface(user, current_location.name, None)
        await interaction.message.edit(embed=embed, view=view)


    async def __create_flight_interface(self, user: discord.User, current_location_name: str, selected_destination: str = None) -> tuple[discord.Embed, View]:
        """Create the flight map interface"""
        from helpers.pathhelpers import get_sprite_path
        from .constant import LOCATION_DISPLAY_NAMES
        from discord.ui import Select
        
        # Map of cities that can be flown to (matching the PNG filenames in sprites/town_map/)
        flyable_cities = {
            'pallet-town': 'Pallet Town',
            'viridian-city': 'Viridian City',
            'pewter-city': 'Pewter City',
            'cerulean-city': 'Cerulean City',
            'lavender-town': 'Lavender Town',
            'vermilion-city': 'Vermilion City',
            'celadon-city': 'Celadon City',
            'saffron-city': 'Saffron City',
            'fuchsia-city': 'Fuchsia City',
            'cinnabar-island': 'Cinnabar Island',
            'indigo-plateau': 'Indigo Plateau'
        }
        
        current_display = LOCATION_DISPLAY_NAMES.get(current_location_name, current_location_name.replace('-', ' ').title())
        
        # Create embed
        embed = discord.Embed(
            title="🕊️ Flight Map",
            description=f"**Current Location:** {current_display}\n\nSelect a destination to fly to:",
            color=discord.Color.green()
        )
        embed.set_author(name=user.display_name, icon_url=str(user.display_avatar.url))
        
        # Set image based on selected destination or show base map
        if selected_destination and selected_destination in flyable_cities:
            # Convert from "pallet-town" to "town_map_pallet_town.png"
            location_part = selected_destination.replace('-', '_')
            image_name = f"town_map_{location_part}.png"
        else:
            image_name = "town_map.png"
        
        try:
            full_sprite_path = get_sprite_path(f"/sprites/town_map/{image_name}")
            sprite_file = discord.File(full_sprite_path, filename=image_name)
            
            # Upload to logging channel to get URL
            temp_message = await self.sendToLoggingChannel(f'{user.display_name} flight map - {image_name}', sprite_file)
            
            if temp_message and temp_message.attachments:
                attachment = temp_message.attachments[0]
                embed.set_image(url=attachment.url)
        except Exception as e:
            print(f"Error loading flight map sprite: {e}")
        
        # Create view
        view = View()
        
        # ROW 0: City selector dropdown
        city_select = Select(
            placeholder="Choose destination city",
            custom_id='flight_city_select',
            row=0
        )
        
        for city_key, city_name in flyable_cities.items():
            # Don't show current location in dropdown
            if city_key != current_location_name:
                city_select.add_option(
                    label=city_name,
                    value=city_key,
                    default=(city_key == selected_destination)
                )
        
        city_select.callback = self.on_flight_city_select
        view.add_item(city_select)
        
        # ROW 1: Action buttons
        fly_btn = Button(
            style=ButtonStyle.green,
            label="✈️ Fly",
            custom_id='flight_fly',
            row=1,
            disabled=(selected_destination is None)
        )
        fly_btn.callback = self.on_fly_action_click
        view.add_item(fly_btn)
        
        back_btn = Button(
            style=ButtonStyle.gray,
            label="← Back to Bag",
            custom_id='flight_back_to_bag',
            row=1
        )
        back_btn.callback = self.on_flight_back_to_bag_click
        view.add_item(back_btn)
        
        return embed, view


    async def on_flight_city_select(self, interaction: discord.Interaction):
        """Handle city selection from dropdown"""
        user = interaction.user
        
        if str(user.id) not in self.__flight_states:
            await interaction.response.send_message('Session expired.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        flight_state = self.__flight_states[str(user.id)]
        
        # Get selected city from dropdown
        selected_city = interaction.data['values'][0]
        flight_state.selected_destination = selected_city
        
        # Update interface with new city map
        embed, view = await self.__create_flight_interface(user, flight_state.current_location_name, selected_city)
        await interaction.message.edit(embed=embed, view=view)


    async def on_fly_action_click(self, interaction: discord.Interaction):
        """Execute the flight to selected destination"""
        user = interaction.user
        
        if str(user.id) not in self.__flight_states:
            await interaction.response.send_message('Session expired.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        flight_state = self.__flight_states[str(user.id)]
        
        if not flight_state.selected_destination:
            await interaction.followup.send('Please select a destination first!', ephemeral=True)
            return
        
        # Check location blocking
        from services.questclass import quests as QuestsClass
        from services.locationclass import location as LocationClass
        from helpers.pathhelpers import load_json_config
        
        quest_obj = QuestsClass(str(user.id))
        
        # Get destination location ID
        location_names = load_json_config('locationNames.json')
        destination_location_id = location_names.get(flight_state.selected_destination)
        
        if not destination_location_id:
            await interaction.followup.send('Invalid destination!', ephemeral=True)
            return
        
        # Check if destination is blocked by quest requirements
        quests_data = load_json_config('quests.json')
        
        if str(destination_location_id) in quests_data:
            quest_data = quests_data[str(destination_location_id)]
            blockers = quest_data.get('blockers', [])
            
            if blockers and quest_obj.locationBlocked(blockers):
                # Build error message about missing requirements
                from helpers.helpers import check_hm_usable
                missing_items = []
                
                for blocker in blockers:
                    if blocker in ['HM01', 'HM02', 'HM03', 'HM04', 'HM05']:
                        hm_attr = getattr(quest_obj.keyitems, blocker, False)
                        if not hm_attr:
                            missing_items.append(blocker.replace('_', ' ').title())
                            continue
                        can_use, _ = check_hm_usable(str(user.id), blocker)
                        if not can_use:
                            missing_items.append(f"{blocker} (no compatible Pokemon)")
                    else:
                        if quest_obj.locationBlocked([blocker]):
                            missing_items.append(blocker.replace('_', ' ').title())
                
                if missing_items:
                    missing_text = ", ".join(missing_items)
                    await interaction.followup.send(
                        f'You cannot fly to this location yet! Missing: {missing_text}',
                        ephemeral=True
                    )
                    return
        
        # Execute the flight - update trainer location
        loc_obj = LocationClass(str(user.id))
        loc_obj.setLocation(destination_location_id)
        
        # Clean up flight state
        if str(user.id) in self.__flight_states:
            del self.__flight_states[str(user.id)]
        
        # Return to map at new location
        await self.on_nav_map_click(interaction)


    async def on_flight_back_to_bag_click(self, interaction: discord.Interaction):
        """Return to bag from flight interface"""
        user = interaction.user
        
        # Clean up flight state
        if str(user.id) in self.__flight_states:
            del self.__flight_states[str(user.id)]
        
        # Return to bag items view
        await self.on_bag_items_click(interaction)

    def __create_items_embed(self, user: discord.User) -> discord.Embed:
        """Create embed showing trainer's items"""
        from services.inventoryclass import inventory as InventoryClass
        
        inv = InventoryClass(str(user.id))
        
        embed = discord.Embed(title="Bag - Items", color=discord.Color.blue())
        embed.set_thumbnail(url="https://pokesprites.joshkohut.com/sprites/trainer_bag.png")
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        
        items = []
        
        # Pokeballs
        if inv.pokeball > 0:
            items.append(f'{constant.POKEBALL} **Poké Balls** — {inv.pokeball}')
        if inv.greatball > 0:
            items.append(f'{constant.GREATBALL} **Great Balls** — {inv.greatball}')
        if inv.ultraball > 0:
            items.append(f'{constant.ULTRABALL} **Ultra Balls** — {inv.ultraball}')
        if inv.masterball > 0:
            items.append(f'{constant.MASTERBALL} **Master Ball** — {inv.masterball}')
        
        # Potions
        if inv.potion > 0:
            items.append(f'{constant.POTION} **Potion** — {inv.potion}')
        if inv.superpotion > 0:
            items.append(f'{constant.SUPERPOTION} **Super Potions** — {inv.superpotion}')
        if inv.hyperpotion > 0:
            items.append(f'{constant.HYPERPOTION} **Hyper Potions** — {inv.hyperpotion}')
        if inv.maxpotion > 0:
            items.append(f'{constant.MAXPOTION} **Max Potions** — {inv.maxpotion}')
        if inv.fullrestore > 0:
            items.append(f'{constant.FULLRESTORE} **Full Restore** — {inv.fullrestore}')
        
        # Revival items
        if inv.revive > 0:
            items.append(f'{constant.REVIVE} **Revive** — {inv.revive}')
        
        # Status healers
        if inv.antidote > 0:
            items.append(f'{constant.ANTIDOTE} **Antidote** — {inv.antidote}')
        if inv.awakening > 0:
            items.append(f'{constant.AWAKENING} **Awakening** — {inv.awakening}')
        if inv.burnheal > 0:
            items.append(f'{constant.BURNHEAL} **Burn Heal** — {inv.burnheal}')
        if inv.iceheal > 0:
            items.append(f'{constant.ICEHEAL} **Ice Heal** — {inv.iceheal}')
        if inv.paralyzeheal > 0:
            items.append(f'{constant.PARALYZEHEAL} **Paralyze Heal** — {inv.paralyzeheal}')
        
        # Other items
        if inv.repel > 0:
            items.append(f'{constant.REPEL} **Repel** — {inv.repel}')
        if inv.superrepel > 0:
            items.append(f'{constant.SUPERREPEL} **Super Repel** — {inv.superrepel}')
        if inv.maxrepel > 0:
            items.append(f'{constant.MAXREPEL} **Max Repel** — {inv.maxrepel}')
        if inv.escaperope > 0:
            items.append(f'{constant.ESCAPEROPE} **Escape Rope** — {inv.escaperope}')
        
        # Evolution stones
        if inv.firestone > 0:
            items.append(f'{constant.FIRESTONE} **Fire Stone** — {inv.firestone}')
        if inv.waterstone > 0:
            items.append(f'{constant.WATERSTONE} **Water Stone** — {inv.waterstone}')
        if inv.thunderstone > 0:
            items.append(f'{constant.THUNDERSTONE} **Thunder Stone** — {inv.thunderstone}')
        if inv.leafstone > 0:
            items.append(f'{constant.LEAFSTONE} **Leaf Stone** — {inv.leafstone}')
        if inv.moonstone > 0:
            items.append(f'{constant.MOONSTONE} **Moon Stone** — {inv.moonstone}')
        
        # Other misc items
        if inv.nugget > 0:
            items.append(f'{constant.NUGGET} **Nugget** — {inv.nugget}')
        if inv.freshwater > 0:
            items.append(f'{constant.FRESHWATER} **Fresh Water** — {inv.freshwater}')
        if inv.sodapop > 0:
            items.append(f'{constant.SODAPOP} **Soda Pop** — {inv.sodapop}')
        if inv.lemonade > 0:
            items.append(f'{constant.LEMONADE} **Lemonade** — {inv.lemonade}')
        
        items_text = "\n".join(items) if len(items) > 0 else "No items yet."
        embed.add_field(name="Items", value=items_text, inline=False)
        
        # TMs section
        tm_items = []
        owned_tms = inv.getOwnedTMs()
        for tm_key, qty in owned_tms:
            move_name = constant.TM_MOVE_MAPPING.get(tm_key, 'Unknown')
            display_move = move_name.replace('-', ' ').title()
            tm_items.append(f'{constant.TM_EMOJI} **{tm_key}** {display_move} — {qty}')
        
        if tm_items:
            # Discord embed field value max is 1024 chars, split if needed
            tm_text = "\n".join(tm_items)
            if len(tm_text) <= 1024:
                embed.add_field(name="TMs", value=tm_text, inline=False)
            else:
                # Split into multiple fields
                chunk = []
                chunk_len = 0
                field_num = 1
                for line in tm_items:
                    if chunk_len + len(line) + 1 > 1024:
                        embed.add_field(name=f"TMs ({field_num})", value="\n".join(chunk), inline=False)
                        chunk = []
                        chunk_len = 0
                        field_num += 1
                    chunk.append(line)
                    chunk_len += len(line) + 1
                if chunk:
                    embed.add_field(name=f"TMs ({field_num})" if field_num > 1 else "TMs", value="\n".join(chunk), inline=False)
        
        return embed
    
    def __create_keyitems_embed(self, user: discord.User) -> discord.Embed:
        """Create embed showing trainer's key items (excluding HMs)"""
        from services.keyitemsclass import keyitems as KeyItemClass
        import constant
        
        inv = KeyItemClass(str(user.id))
        
        embed = discord.Embed(title="Bag - Key Items", color=discord.Color.gold())
        embed.set_thumbnail(url="https://pokesprites.joshkohut.com/sprites/trainer_bag.png")
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        
        items = []
        
        # Key items (excluding HMs which are shown in HMs tab)
        if inv.pokeflute:
            items.append(f'{constant.POKEFLUTE} **Poké Flute**')
        if inv.silph_scope:
            items.append(f'{constant.SILPH_SCOPE} **Silph Scope**')
        if inv.oaks_parcel:
            items.append(f'{constant.OAK_PARCEL} **Oak\'s Parcel**')
        if inv.ss_ticket:
            items.append(f'{constant.SS_TICKET} **S.S. Ticket**')
        if inv.bicycle:
            items.append(f'{constant.BICYCLE} **Bicycle**')
        if inv.old_rod:
            items.append(f'{constant.OLD_ROD} **Old Rod**')
        if inv.good_rod:
            items.append(f'{constant.GOOD_ROD} **Good Rod**')
        if inv.super_rod:
            items.append(f'{constant.SUPER_ROD} **Super Rod**')
        if inv.item_finder:
            items.append(f'{constant.ITEM_FINDER} **Item Finder**')
        if inv.bike_voucher:
            items.append(f'🎟️ **Bike Voucher**')
        if inv.gold_teeth:
            items.append(f'🦷 **Gold Teeth**')
        if inv.dome_fossil:
            items.append(f'{constant.DOMEFOSSIL} **Dome Fossil**')
        if inv.helix_fossil:
            items.append(f'{constant.HELIXFOSSIL} **Helix Fossil**')
        if inv.old_amber:
            items.append(f'{constant.OLDAMBER} **Old Amber**')
        if inv.game_shark:
            items.append(f'{constant.GAMESHARK} **Game Shark**')
        if inv.eevee_tail:
            items.append(f'{constant.EEVEE_TAIL} **Eevee\'s Tail**')


        items_text = "\n".join(items) if len(items) > 0 else "No key items yet."
        embed.add_field(name="Key Items", value=items_text, inline=False)
        
        return embed

    async def on_bag_trainer_card_click(self, interaction: discord.Interaction):
        """Show trainer card from bag menu"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'trainer'
        
        embed = self.__create_trainer_embed(user)
        view = self.__create_bag_navigation_view('trainer')
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_bag_items_click(self, interaction: discord.Interaction):
        """Show items view"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'items'
        
        embed = self.__create_items_embed(user)
        view = self.__create_bag_navigation_view('items')
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_bag_keyitems_click(self, interaction: discord.Interaction):
        """Show key items view"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'keyitems'
        
        embed = self.__create_keyitems_embed(user)
        view = self.__create_bag_navigation_view('keyitems')
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_bag_hms_click(self, interaction: discord.Interaction):
        """Show HMs view"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'hms'
        
        embed = self.__create_hms_embed(user)
        view = self.__create_bag_navigation_view('hms')
        
        await interaction.message.edit(embed=embed, view=view)



    async def on_bag_pokemon_select(self, interaction: discord.Interaction):
        """Handle Pokemon selection in bag party view"""
        user = interaction.user
        
        if str(user.id) not in self.__bag_states:
            await interaction.response.send_message('Session expired.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        bag_state = self.__bag_states[str(user.id)]
        
        # Get selected Pokemon ID from select menu
        selected_trainer_id = interaction.data['values'][0]
        bag_state.selected_pokemon_id = selected_trainer_id
        
        from services.trainerclass import trainer as TrainerClass
        
        trainer = self._get_trainer(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        active = trainer.getActivePokemon()
        
        # Find the selected Pokemon
        selected_pokemon = None
        for poke in pokeList:
            if str(poke.trainerId) == selected_trainer_id:
                selected_pokemon = poke
                break
        
        if selected_pokemon is None:
            await interaction.followup.send('Pokemon not found.', ephemeral=True)
            return
        
        # Reload to get latest stats
        selected_pokemon.load(pokemonId=selected_pokemon.trainerId)
        
        # Create embed for selected Pokemon
        from .functions import createStatsEmbed
        embed = createStatsEmbed(user, selected_pokemon)
        
        # Mark if this is the active Pokemon
        if selected_pokemon.trainerId == active.trainerId:
            embed.title = f"⭐ {embed.title}"
            embed.set_footer(text="This is your active Pokemon!")
        
        # Recreate view with updated selection
        from discord.ui import Select
        from discord import SelectOption
        
        view = View()
        
        # ROW 0: Pokemon selector
        select = Select(placeholder="Choose a Pokemon", custom_id='pokemon_select', row=0)
        for poke in pokeList:
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            if poke.trainerId == active.trainerId:
                label += " ⭐"
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_bag_pokemon_select
        view.add_item(select)
        
        # ROW 1: Party management actions
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='bag_party_moves', row=1)
        moves_btn.callback = self.on_bag_party_moves_click
        view.add_item(moves_btn)
        
        is_already_active = (selected_pokemon.trainerId == active.trainerId)
        set_active_btn = Button(
            style=ButtonStyle.green if not is_already_active else ButtonStyle.gray,
            label="⭐ Set Active",
            custom_id='bag_party_set_active',
            row=1,
            disabled=is_already_active
        )
        set_active_btn.callback = self.on_bag_party_set_active_click
        view.add_item(set_active_btn)
        
        # ROW 2: Pokemon actions
        use_items_btn = Button(style=ButtonStyle.blurple, label="💊 Use Items", custom_id='bag_party_use_items', row=2)
        use_items_btn.callback = self.on_bag_party_use_items_click
        view.add_item(use_items_btn)

        # Only show Deposit if at a Pokemon Center
        _dep_location = self._get_trainer(str(user.id)).getLocation()
        if _dep_location.pokecenter:
            deposit_btn = Button(style=ButtonStyle.gray, label="💾 Deposit", custom_id='bag_party_deposit', row=2)
            deposit_btn.callback = self.on_bag_party_deposit_click
            view.add_item(deposit_btn)
        
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='bag_party_release', row=2)
        release_btn.callback = self.on_bag_party_release_click
        view.add_item(release_btn)
        
        # ROW 3: Navigation
        back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='party_back_to_bag', row=3)
        back_btn.callback = self.on_party_back_to_bag_click
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='party_back_to_map', row=3)
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_bag_party_use_items_click(self, interaction: discord.Interaction):
        """Show item usage interface"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        
        # Create item usage state
        self.__item_usage_states[str(user.id)] = ItemUsageState(str(user.id))
        
        # Show item usage interface
        embed, view = self.__create_item_usage_view(user)
        await interaction.message.edit(embed=embed, view=view)


    def __create_item_usage_view(self, user: discord.User) -> tuple[discord.Embed, View]:
        """Create the item usage interface with Pokemon and Item dropdowns"""
        from services.trainerclass import trainer as TrainerClass
        from services.inventoryclass import inventory as InventoryClass
        from discord.ui import Select
        
        trainer = self._get_trainer(str(user.id))
        inv = InventoryClass(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        
        item_state = self.__item_usage_states.get(str(user.id), ItemUsageState(str(user.id)))
        
        # Create embed
        embed = discord.Embed(
            title="💊 Use Items on Pokemon",
            description="Select a Pokemon and an item to use.",
            color=discord.Color.blue()
        )
        embed.set_author(name=user.display_name, icon_url=str(user.display_avatar.url))
        
        view = View()
        
        # ROW 0: Pokemon selector
        pokemon_select = Select(placeholder="Choose a Pokemon", custom_id='item_usage_pokemon_select', row=0)
        for poke in pokeList:
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            pokemon_select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == item_state.selected_pokemon_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        pokemon_select.callback = self.on_item_usage_pokemon_select
        view.add_item(pokemon_select)
        
        # ROW 1: Item selector - now includes healing items AND evolution stones
        item_select = Select(placeholder="Choose an Item", custom_id='item_usage_item_select', row=1)
        
        # Define usable items with their inventory attributes and display names
        usable_items = [
            # Healing items
            ('potion', inv.potion, 'Potion', 'Restores 20 HP'),
            ('super-potion', inv.superpotion, 'Super Potion', 'Restores 50 HP'),
            ('hyper-potion', inv.hyperpotion, 'Hyper Potion', 'Restores 200 HP'),
            ('max-potion', inv.maxpotion, 'Max Potion', 'Fully restores HP'),
            ('revive', inv.revive, 'Revive', 'Revives fainted Pokemon (50% HP)'),
            ('full-restore', inv.fullrestore, 'Full Restore', 'Fully restores HP'),
            # Evolution stones
            ('fire-stone', inv.firestone, 'Fire Stone', 'Evolves certain Pokemon'),
            ('water-stone', inv.waterstone, 'Water Stone', 'Evolves certain Pokemon'),
            ('thunder-stone', inv.thunderstone, 'Thunder Stone', 'Evolves certain Pokemon'),
            ('leaf-stone', inv.leafstone, 'Leaf Stone', 'Evolves certain Pokemon'),
            ('moon-stone', inv.moonstone, 'Moon Stone', 'Evolves certain Pokemon'),
        ]
        
        # Add TMs to usable items list
        owned_tms = inv.getOwnedTMs()
        for tm_key, qty in owned_tms:
            move_name = constant.TM_MOVE_MAPPING.get(tm_key, 'Unknown')
            display_move = move_name.replace('-', ' ').title()
            usable_items.append((tm_key, qty, f'{tm_key} {display_move}', f'Teaches {display_move}'))
        
        has_items = False
        for item_key, quantity, display_name, description in usable_items:
            if quantity > 0:
                has_items = True
                item_select.add_option(
                    label=f"{display_name} (x{quantity})",
                    value=item_key,
                    description=description[:100],
                    default=(item_key == item_state.selected_item)
                )
        
        if not has_items:
            embed.add_field(
                name="❌ No Usable Items",
                value="You don't have any items to use on Pokemon. Visit a Pokemart to buy some!",
                inline=False
            )
        else:
            item_select.callback = self.on_item_usage_item_select
            view.add_item(item_select)
            
            # ROW 2: Action buttons
            # Only enable Use button if both Pokemon and Item are selected
            use_disabled = not (item_state.selected_pokemon_id and item_state.selected_item)
            use_btn = Button(
                style=ButtonStyle.green,
                label="✅ Use Item",
                custom_id='item_usage_use',
                row=2,
                disabled=use_disabled
            )
            use_btn.callback = self.on_item_usage_use_click
            view.add_item(use_btn)
        
        # ROW 3: Back button (always available)
        back_btn = Button(
            style=ButtonStyle.gray,
            label="← Back to Party",
            custom_id='item_usage_back',
            row=3
        )
        back_btn.callback = self.on_item_usage_back_click
        view.add_item(back_btn)
        
        return embed, view


    async def on_item_usage_pokemon_select(self, interaction: discord.Interaction):
        """Handle Pokemon selection in item usage"""
        user = interaction.user
        
        if str(user.id) not in self.__item_usage_states:
            await interaction.response.send_message('Session expired.', ephemeral=True)
            return
        
        # Update selected Pokemon
        selected_value = interaction.data['values'][0]
        self.__item_usage_states[str(user.id)].selected_pokemon_id = selected_value
        
        # Recreate view with updated selection
        embed, view = self.__create_item_usage_view(user)
        await interaction.response.edit_message(embed=embed, view=view)


    async def on_item_usage_item_select(self, interaction: discord.Interaction):
        """Handle item selection in item usage"""
        user = interaction.user
        
        if str(user.id) not in self.__item_usage_states:
            await interaction.response.send_message('Session expired.', ephemeral=True)
            return
        
        # Update selected item
        selected_value = interaction.data['values'][0]
        self.__item_usage_states[str(user.id)].selected_item = selected_value
        
        # Recreate view with updated selection
        embed, view = self.__create_item_usage_view(user)
        await interaction.response.edit_message(embed=embed, view=view)


    async def on_item_usage_use_click(self, interaction: discord.Interaction):
        """Use the selected item on the selected Pokemon"""
        user = interaction.user
        await interaction.response.defer(ephemeral=True)
        
        if str(user.id) not in self.__item_usage_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        item_state = self.__item_usage_states[str(user.id)]
        
        if not item_state.selected_pokemon_id or not item_state.selected_item:
            await interaction.followup.send('Please select both a Pokemon and an item.', ephemeral=True)
            return
        
        # Check if selected item is a TM
        if item_state.selected_item.startswith('TM') and len(item_state.selected_item) <= 4:
            await self.__handle_tm_usage(interaction, user, item_state)
            return

        from services.trainerclass import trainer as TrainerClass
        from services.pokeclass import Pokemon as PokemonClass
        
        trainer = self._get_trainer(str(user.id))
        
        # Load the Pokemon before evolution to get its name
        old_pokemon = PokemonClass(str(user.id))
        old_pokemon.load(int(item_state.selected_pokemon_id))
        old_pokemon_name = old_pokemon.pokemonName
        
        # Check if this is an evolution stone
        evolution_stones = ['fire-stone', 'water-stone', 'thunder-stone', 'leaf-stone', 'moon-stone']
        is_evolution_stone = item_state.selected_item in evolution_stones
        
        # Use the item - CORRECT ORDER: pokeTrainerId first, then item
        trainer.useItem(int(item_state.selected_pokemon_id), item_state.selected_item)
        
        # Check if evolution happened by looking at the message
        did_evolve = is_evolution_stone and trainer.statuscode == 420 and "evolved into" in trainer.message.lower()
        
        if did_evolve:
            # Extract the evolved Pokemon name from the message
            # Message format: "Something's happening... Your pokemon evolved into [NAME]!"
            import re
            match = re.search(r'evolved into (.+?)!', trainer.message, re.IGNORECASE)
            if match:
                evolved_name = match.group(1).strip().lower()
                
                # Load the evolved Pokemon to get its data
                evolved_pokemon = PokemonClass(str(user.id))
                # Find the new Pokemon by name
                pokeList = trainer.getPokemon(party=True)
                for poke in pokeList:
                    poke.load(pokemonId=poke.trainerId)
                    if poke.pokemonName == evolved_name:
                        evolved_pokemon = poke
                        break
                
                # Create evolution embed
                evolution_embed = discord.Embed(
                    title="✨ What's this?",
                    description=f"Your **{old_pokemon_name.capitalize()}** evolved into **{evolved_name.capitalize()}**!",
                    color=discord.Color.gold()
                )
                evolution_embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
                
                # After evolution is complete and shown to user
                if hasattr(trainer, 'last_evolved_pokemon') and trainer.last_evolved_pokemon:
                    # Check for first evolution (especially for Vaporeon, Jolteon, Flareon)
                    special_evolutions = ['vaporeon']
                    if trainer.last_evolved_pokemon.lower() in special_evolutions:
                        if interaction.guild:
                            await self.check_first_evolution(
                                str(user.id),
                                interaction.guild,
                                trainer.last_evolved_pokemon
                            )
                    trainer.last_evolved_pokemon = None  # Clear it

                # Add Pokemon sprite
                sprite_file = None
                try:
                    sprite_path = f"/sprites/pokemon/{evolved_name}.png"
                    full_sprite_path = get_sprite_path(sprite_path)
                    sprite_file = discord.File(full_sprite_path, filename=f"{evolved_name}.png")
                    evolution_embed.set_image(url=f"attachment://{evolved_name}.png")
                except Exception as e:
                    print(f"Error loading evolution sprite: {e}")
                
                # Send evolution embed as ephemeral message
                if sprite_file:
                    await interaction.followup.send(embed=evolution_embed, file=sprite_file, ephemeral=True)
                else:
                    await interaction.followup.send(embed=evolution_embed, ephemeral=True)
        else:
            # Send result as ephemeral message (healing items or failed evolution)
            if trainer.statuscode == 420:  # Success or expected error
                await interaction.followup.send(f'✅ {trainer.message}', ephemeral=True)
            else:
                await interaction.followup.send(f'❌ {trainer.message}', ephemeral=True)
        
        # Refresh the item usage view (to update quantities and HP)
        embed, view = self.__create_item_usage_view(user)
        await interaction.message.edit(embed=embed, view=view)


    async def on_item_usage_back_click(self, interaction: discord.Interaction):
        """Return to party view from item usage"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        # Clean up item usage state
        if str(user.id) in self.__item_usage_states:
            del self.__item_usage_states[str(user.id)]
        
        # Return to party view - need to rebuild it
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'party'
        
        from services.trainerclass import trainer as TrainerClass
        from discord.ui import Select
        
        trainer = self._get_trainer(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        active = trainer.getActivePokemon()
        
        if len(pokeList) == 0:
            await interaction.followup.send('You do not have any Pokemon.', ephemeral=True)
            return
        
        # Default to previously selected or active Pokemon
        selected_trainer_id = bag_state.selected_pokemon_id or str(active.trainerId)
        
        # Find the selected Pokemon
        selected_pokemon = None
        for poke in pokeList:
            if str(poke.trainerId) == selected_trainer_id:
                selected_pokemon = poke
                break
        
        if selected_pokemon is None:
            selected_pokemon = pokeList[0]
            selected_trainer_id = str(selected_pokemon.trainerId)
            bag_state.selected_pokemon_id = selected_trainer_id
        
        selected_pokemon.load(pokemonId=selected_pokemon.trainerId)
        
        from .functions import createStatsEmbed
        embed = createStatsEmbed(user, selected_pokemon)
        
        if selected_pokemon.trainerId == active.trainerId:
            embed.title = f"⭐ {embed.title}"
            embed.set_footer(text="This is your active Pokemon!")
        
        # Rebuild party view with all buttons
        view = View()
        
        # ROW 0: Pokemon selector
        select = Select(placeholder="Choose a Pokemon", custom_id='pokemon_select', row=0)
        for poke in pokeList:
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            if poke.trainerId == active.trainerId:
                label += " ⭐"
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_bag_pokemon_select
        view.add_item(select)
        
        # ROW 1: Party management actions
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='bag_party_moves', row=1)
        moves_btn.callback = self.on_bag_party_moves_click
        view.add_item(moves_btn)
        
        is_already_active = (selected_pokemon.trainerId == active.trainerId)
        set_active_btn = Button(
            style=ButtonStyle.green if not is_already_active else ButtonStyle.gray,
            label="⭐ Set Active",
            custom_id='bag_party_set_active',
            row=1,
            disabled=is_already_active
        )
        set_active_btn.callback = self.on_bag_party_set_active_click
        view.add_item(set_active_btn)
        
        # ROW 2: Pokemon actions - INCLUDING USE ITEMS
        use_items_btn = Button(style=ButtonStyle.blurple, label="💊 Use Items", custom_id='bag_party_use_items', row=2)
        use_items_btn.callback = self.on_bag_party_use_items_click
        view.add_item(use_items_btn)
        
        # Only show Deposit if at a Pokemon Center
        _dep_location = self._get_trainer(str(user.id)).getLocation()
        if _dep_location.pokecenter:
            deposit_btn = Button(style=ButtonStyle.gray, label="💾 Deposit", custom_id='bag_party_deposit', row=2)
            deposit_btn.callback = self.on_bag_party_deposit_click
            view.add_item(deposit_btn)
        
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='bag_party_release', row=2)
        release_btn.callback = self.on_bag_party_release_click
        view.add_item(release_btn)
        
        # ROW 3: Navigation
        back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='party_back_to_bag', row=3)
        back_btn.callback = self.on_party_back_to_bag_click
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='party_back_to_map', row=3)
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_bag_party_moves_click(self, interaction: discord.Interaction):
        """Show moves for selected Pokemon"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        selected_trainer_id = bag_state.selected_pokemon_id
        
        if not selected_trainer_id:
            await interaction.followup.send('No Pokemon selected.', ephemeral=True)
            return
        
        from services.trainerclass import trainer as TrainerClass
        
        trainer = self._get_trainer(str(user.id))
        pokemon = trainer.getPokemonById(int(selected_trainer_id))
        
        if not pokemon:
            await interaction.followup.send('Pokemon not found.', ephemeral=True)
            return
        
        # Reload to get latest data
        pokemon.load(pokemonId=pokemon.trainerId)
        
        from .functions import createPokemonAboutEmbed
        embed = createPokemonAboutEmbed(user, pokemon)
        
        # Keep same view structure
        await interaction.followup.send(embed=embed, ephemeral=True)


    async def on_bag_party_set_active_click(self, interaction: discord.Interaction):
        """Set selected Pokemon as active"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        selected_trainer_id = bag_state.selected_pokemon_id
        
        if not selected_trainer_id:
            await interaction.followup.send('No Pokemon selected.', ephemeral=True)
            return
        
        from services.trainerclass import trainer as TrainerClass
        
        trainer = self._get_trainer(str(user.id))
        trainer.setActivePokemon(int(selected_trainer_id))
        
        # Refresh the party view - REBUILD IT HERE instead of calling on_bag_party_click
        from discord.ui import Select
        from discord import SelectOption
        
        pokeList = trainer.getPokemon(party=True)
        active = trainer.getActivePokemon()

        if len(pokeList) == 0:
            await interaction.followup.send('You do not have any Pokemon.', ephemeral=True)
            return

        # Find the selected Pokemon and RELOAD IT
        selected_pokemon = None
        for poke in pokeList:
            if str(poke.trainerId) == selected_trainer_id:
                selected_pokemon = poke
                break
        
        if selected_pokemon is None:
            selected_pokemon = pokeList[0]
            selected_trainer_id = str(selected_pokemon.trainerId)
            bag_state.selected_pokemon_id = selected_trainer_id
        
        # Always persist the selected Pokemon ID so button handlers can find it
        bag_state.selected_pokemon_id = selected_trainer_id

        # Reload the selected Pokemon to get all its data
        selected_pokemon.load(pokemonId=selected_pokemon.trainerId)

        # Create embed for selected Pokemon
        from .functions import createStatsEmbed
        embed = createStatsEmbed(user, selected_pokemon)
        
        # Mark if this is the active Pokemon
        if selected_pokemon.trainerId == active.trainerId:
            embed.title = f"⭐ {embed.title}"
            embed.set_footer(text="This is your active Pokemon!")
        
        # Create view with Pokemon selector
        view = View()
        
        # ROW 0: Pokemon selector
        select = Select(placeholder="Choose a Pokemon", custom_id='pokemon_select', row=0)
        for poke in pokeList:
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            if poke.trainerId == active.trainerId:
                label += " ⭐"
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_bag_pokemon_select
        view.add_item(select)
        
        # ROW 1: Party management actions
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='bag_party_moves', row=1)
        moves_btn.callback = self.on_bag_party_moves_click
        view.add_item(moves_btn)
        
        # Disable Set Active if already active
        is_already_active = (selected_pokemon.trainerId == active.trainerId)
        set_active_btn = Button(
            style=ButtonStyle.green if not is_already_active else ButtonStyle.gray,
            label="⭐ Set Active",
            custom_id='bag_party_set_active',
            row=1,
            disabled=is_already_active
        )
        set_active_btn.callback = self.on_bag_party_set_active_click
        view.add_item(set_active_btn)
        
        # ROW 2: Pokemon actions
        use_items_btn = Button(style=ButtonStyle.blurple, label="💊 Use Items", custom_id='bag_party_use_items', row=2)
        use_items_btn.callback = self.on_bag_party_use_items_click
        view.add_item(use_items_btn)

        # Only show Deposit if at a Pokemon Center
        _dep_location = self._get_trainer(str(user.id)).getLocation()
        if _dep_location.pokecenter:
            deposit_btn = Button(style=ButtonStyle.gray, label="💾 Deposit", custom_id='bag_party_deposit', row=2)
            deposit_btn.callback = self.on_bag_party_deposit_click
            view.add_item(deposit_btn)
        
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='bag_party_release', row=2)
        release_btn.callback = self.on_bag_party_release_click
        view.add_item(release_btn)
        
        # ROW 3: Navigation back
        back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='party_back_to_bag', row=3)
        back_btn.callback = self.on_party_back_to_bag_click
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='party_back_to_map', row=3)
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_bag_party_deposit_click(self, interaction: discord.Interaction):
        """Deposit Pokemon from party to PC"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        
        # Check if location has a Pokemon Center
        trainer_obj = self._get_trainer(str(user.id))
        deposit_location = trainer_obj.getLocation()
        if not deposit_location.pokecenter:
            await interaction.followup.send('You need to be at a Pokémon Center to deposit Pokémon!', ephemeral=True)
            return
        
        selected_trainer_id = bag_state.selected_pokemon_id
        
        if not selected_trainer_id:
            await interaction.followup.send('No Pokemon selected.', ephemeral=True)
            return
        
        from services.trainerclass import trainer as TrainerClass
        
        trainer = self._get_trainer(str(user.id))
        
        # Get Pokemon name before depositing
        pokemon = trainer.getPokemonById(int(selected_trainer_id))
        if pokemon:
            pokemon.load(pokemonId=pokemon.trainerId)
            poke_name = pokemon.nickName if pokemon.nickName else pokemon.pokemonName.capitalize()
        else:
            poke_name = "Pokemon"
        
        # Attempt deposit
        trainer.deposit(int(selected_trainer_id))
        
        if trainer.statuscode == 420:
            # Failed - must keep at least one in party
            await interaction.followup.send(trainer.message, ephemeral=True)
            return
        
        # Success - show message
        await interaction.followup.send(f'✅ {poke_name} deposited to PC!', ephemeral=True)
        
        # Reset party selection
        bag_state.selected_pokemon_id = None
        
        # Refresh party view - manually rebuild since interaction is already deferred
        from discord.ui import Select
        from discord import SelectOption
        
        trainer = self._get_trainer(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        active = trainer.getActivePokemon()

        if len(pokeList) == 0:
            # Should never happen but just in case
            await interaction.followup.send('Error: No Pokemon in party.', ephemeral=True)
            return

        # Select first Pokemon in updated party
        selected_trainer_id = str(pokeList[0].trainerId)
        bag_state.selected_pokemon_id = selected_trainer_id
        
        selected_pokemon = pokeList[0]
        selected_pokemon.load(pokemonId=selected_pokemon.trainerId)

        # Create embed for selected Pokemon
        from .functions import createStatsEmbed
        embed = createStatsEmbed(user, selected_pokemon)
        
        # Mark if this is the active Pokemon
        if selected_pokemon.trainerId == active.trainerId:
            embed.title = f"⭐ {embed.title}"
            embed.set_footer(text="This is your active Pokemon!")
        
        # Create view with Pokemon selector
        view = View()
        
        # ROW 0: Pokemon selector
        select = Select(placeholder="Choose a Pokemon", custom_id='pokemon_select', row=0)
        for poke in pokeList:
            # Reload to get latest stats from database
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            if poke.trainerId == active.trainerId:
                label += " ⭐"
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_bag_pokemon_select
        view.add_item(select)
        
        # ROW 1: Party management actions
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='bag_party_moves', row=1)
        moves_btn.callback = self.on_bag_party_moves_click
        view.add_item(moves_btn)
        
        # Disable Set Active if already active
        is_already_active = (selected_pokemon.trainerId == active.trainerId)
        set_active_btn = Button(
            style=ButtonStyle.green if not is_already_active else ButtonStyle.gray,
            label="⭐ Set Active",
            custom_id='bag_party_set_active',
            row=1,
            disabled=is_already_active
        )
        set_active_btn.callback = self.on_bag_party_set_active_click
        view.add_item(set_active_btn)
        
        # ROW 2: Pokemon actions
        use_items_btn = Button(style=ButtonStyle.blurple, label="💊 Use Items", custom_id='bag_party_use_items', row=2)
        use_items_btn.callback = self.on_bag_party_use_items_click
        view.add_item(use_items_btn)

        # Only show Deposit if at a Pokemon Center
        _dep_location = self._get_trainer(str(user.id)).getLocation()
        if _dep_location.pokecenter:
            deposit_btn = Button(style=ButtonStyle.gray, label="💾 Deposit", custom_id='bag_party_deposit', row=2)
            deposit_btn.callback = self.on_bag_party_deposit_click
            view.add_item(deposit_btn)
        
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='bag_party_release', row=2)
        release_btn.callback = self.on_bag_party_release_click
        view.add_item(release_btn)
        
        # ROW 3: Navigation back
        back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='party_back_to_bag', row=3)
        back_btn.callback = self.on_party_back_to_bag_click
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='party_back_to_map', row=3)
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_bag_party_release_click(self, interaction: discord.Interaction):
        """Release Pokemon (placeholder)"""
        await interaction.response.send_message(
            'Release cuming soon!',
            ephemeral=True
        )


    async def on_party_back_to_bag_click(self, interaction: discord.Interaction):
        """Return to bag items view from party"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'items'
        bag_state.selected_pokemon_id = None  # Clear selection
        
        embed = self.__create_items_embed(user)
        view = self.__create_bag_navigation_view('items')
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_bag_party_click(self, interaction: discord.Interaction):
        """Show party view with full party management interface"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'party'
        
        from services.trainerclass import trainer as TrainerClass
        from discord.ui import Select
        from discord import SelectOption
        
        trainer = self._get_trainer(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        active = trainer.getActivePokemon()

        if len(pokeList) == 0:
            await interaction.followup.send('You do not have any Pokemon.', ephemeral=True)
            return

        # Default to active Pokemon or first in party
        selected_trainer_id = bag_state.selected_pokemon_id or str(active.trainerId)
        
        # Find the selected Pokemon and RELOAD IT
        selected_pokemon = None
        for poke in pokeList:
            if str(poke.trainerId) == selected_trainer_id:
                selected_pokemon = poke
                break
        
        if selected_pokemon is None:
            selected_pokemon = pokeList[0]
            selected_trainer_id = str(selected_pokemon.trainerId)
            bag_state.selected_pokemon_id = selected_trainer_id
        
        # Always persist the selected Pokemon ID so button handlers can find it
        bag_state.selected_pokemon_id = selected_trainer_id

        # Reload the selected Pokemon to get all its data
        selected_pokemon.load(pokemonId=selected_pokemon.trainerId)

        # Create embed for selected Pokemon
        from .functions import createStatsEmbed
        embed = createStatsEmbed(user, selected_pokemon)
        
        # Mark if this is the active Pokemon
        if selected_pokemon.trainerId == active.trainerId:
            embed.title = f"⭐ {embed.title}"
            embed.set_footer(text="This is your active Pokemon!")
        
        # Create view with Pokemon selector
        view = View()
        
        # ROW 0: Pokemon selector
        select = Select(placeholder="Choose a Pokemon", custom_id='pokemon_select', row=0)
        for poke in pokeList:
            # Reload to get latest stats from database
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            if poke.trainerId == active.trainerId:
                label += " ⭐"
            
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_bag_pokemon_select
        view.add_item(select)
        
        # ROW 1: Party management actions
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='bag_party_moves', row=1)
        moves_btn.callback = self.on_bag_party_moves_click
        view.add_item(moves_btn)
        
        # Disable Set Active if already active
        is_already_active = (selected_pokemon.trainerId == active.trainerId)
        set_active_btn = Button(
            style=ButtonStyle.green if not is_already_active else ButtonStyle.gray,
            label="⭐ Set Active",
            custom_id='bag_party_set_active',
            row=1,
            disabled=is_already_active
        )
        set_active_btn.callback = self.on_bag_party_set_active_click
        view.add_item(set_active_btn)
        
        # ROW 2: Pokemon actions
        use_items_btn = Button(style=ButtonStyle.blurple, label="💊 Use Items", custom_id='bag_party_use_items', row=2)
        use_items_btn.callback = self.on_bag_party_use_items_click
        view.add_item(use_items_btn)

        # Only show Deposit if at a Pokemon Center
        _dep_location = self._get_trainer(str(user.id)).getLocation()
        if _dep_location.pokecenter:
            deposit_btn = Button(style=ButtonStyle.gray, label="💾 Deposit", custom_id='bag_party_deposit', row=2)
            deposit_btn.callback = self.on_bag_party_deposit_click
            view.add_item(deposit_btn)
        
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='bag_party_release', row=2)
        release_btn.callback = self.on_bag_party_release_click
        view.add_item(release_btn)

        # Trade button
        trade_button, _ = self.get_trade_button_for_pc(str(user.id))
        view.add_item(trade_button)
        
        # ROW 3: Navigation back
        back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='party_back_to_bag', row=3)
        back_btn.callback = self.on_party_back_to_bag_click
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='party_back_to_map', row=3)
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_bag_pokedex_click(self, interaction: discord.Interaction):
        """Show pokedex view"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'pokedex'
        bag_state.pokedex_index = 0  # Reset to first entry
        
        embed = self.__create_pokedex_embed(user, 0)
        view = self.__create_bag_navigation_view('pokedex')
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_pokedex_prev_click(self, interaction: discord.Interaction):
        """Navigate to previous Pokemon in pokedex"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        
        # Get pokedex list to check bounds
        from services.trainerclass import trainer as TrainerClass
        trainer = self._get_trainer(str(user.id))
        pokedex_list = trainer.getPokedex()
        
        if bag_state.pokedex_index > 0:
            bag_state.pokedex_index -= 1
        else:
            # Loop to end
            bag_state.pokedex_index = len(pokedex_list) - 1
        
        embed = self.__create_pokedex_embed(user, bag_state.pokedex_index)
        view = self.__create_bag_navigation_view('pokedex')
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_pokedex_next_click(self, interaction: discord.Interaction):
        """Navigate to next Pokemon in pokedex"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        
        # Get pokedex list to check bounds
        from services.trainerclass import trainer as TrainerClass
        trainer = self._get_trainer(str(user.id))
        pokedex_list = trainer.getPokedex()
        
        if bag_state.pokedex_index < len(pokedex_list) - 1:
            bag_state.pokedex_index += 1
        else:
            # Loop to start
            bag_state.pokedex_index = 0
        
        embed = self.__create_pokedex_embed(user, bag_state.pokedex_index)
        view = self.__create_bag_navigation_view('pokedex')
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_bag_back_to_map_click(self, interaction: discord.Interaction):
        """Return to map from bag"""
        user = interaction.user
        
        # Clean up bag state
        if str(user.id) in self.__bag_states:
            del self.__bag_states[str(user.id)]
        
        # Call existing map navigation
        await self.on_nav_map_click(interaction)

    def __create_bag_navigation_view(self, current_view: str) -> View:
        """Create navigation buttons for bag system"""
        view = View()
        
        # ROW 0: Bag category buttons
        items_btn = Button(
            style=ButtonStyle.blurple if current_view == 'items' else ButtonStyle.gray,
            label="Items",
            custom_id='bag_items',
            row=0
        )
        items_btn.callback = self.on_bag_items_click
        view.add_item(items_btn)
        
        keyitems_btn = Button(
            style=ButtonStyle.blurple if current_view == 'keyitems' else ButtonStyle.gray,
            label="Key Items",
            custom_id='bag_keyitems',
            row=0
        )
        keyitems_btn.callback = self.on_bag_keyitems_click
        view.add_item(keyitems_btn)
        
        hms_btn = Button(
            style=ButtonStyle.blurple if current_view == 'hms' else ButtonStyle.gray,
            label="HMs",
            custom_id='bag_hms',
            row=0
        )
        hms_btn.callback = self.on_bag_hms_click
        view.add_item(hms_btn)
        
        # Trainer button
        trainer_btn = Button(
            style=ButtonStyle.blurple if current_view == 'trainer' else ButtonStyle.gray,
            label="Trainer",
            custom_id='bag_trainer',
            row=0
        )
        trainer_btn.callback = self.on_bag_trainer_card_click
        view.add_item(trainer_btn)

        # ROW 1: Party, PC (if pokecenter), Pokedex buttons
        party_btn = Button(
            style=ButtonStyle.blurple if current_view == 'party' else ButtonStyle.gray,
            label="👥 Party",
            custom_id='bag_party',
            row=1
        )
        party_btn.callback = self.on_bag_party_click
        view.add_item(party_btn)
        
        # Only show PC button if current location has a Pokemon Center
        user_id = None
        if hasattr(self, '_current_user_id'):
            user_id = self._current_user_id
        
        has_pokecenter = False
        if user_id:
            try:
                _trainer = self._get_trainer(user_id)
                _location = _trainer.getLocation()
                has_pokecenter = _location.pokecenter
            except Exception:
                has_pokecenter = False
        
        if has_pokecenter:
            pc_btn = Button(
                style=ButtonStyle.blurple if current_view == 'pc' else ButtonStyle.gray,
                label="💾 PC",
                custom_id='bag_pc',
                row=1
            )
            pc_btn.callback = self.on_bag_pc_click
            view.add_item(pc_btn)
        
        pokedex_btn = Button(
            style=ButtonStyle.blurple if current_view == 'pokedex' else ButtonStyle.gray,
            label="📖 Pokédex",
            custom_id='bag_pokedex',
            row=1
        )
        pokedex_btn.callback = self.on_bag_pokedex_click
        view.add_item(pokedex_btn)
        
        # ROW 2: Pokedex navigation (only show when in pokedex view)
        if current_view == 'pokedex':
            prev_btn = Button(
                style=ButtonStyle.gray,
                label="◀ Previous",
                custom_id='pokedex_prev',
                row=2
            )
            prev_btn.callback = self.on_pokedex_prev_click
            view.add_item(prev_btn)
            
            next_btn = Button(
                style=ButtonStyle.gray,
                label="Next ▶",
                custom_id='pokedex_next',
                row=2
            )
            next_btn.callback = self.on_pokedex_next_click
            view.add_item(next_btn)
        
        # ROW 3: Back to Map and Flight Map buttons
        map_btn = Button(
            style=ButtonStyle.primary,
            label="🗺️ Back to Map",
            custom_id='bag_back_to_map',
            row=3
        )
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        # Check if user has HM02 for Flight Map button
        from services.keyitemsclass import keyitems as KeyItemClass
        
        if user_id:
            keyitems = KeyItemClass(user_id)
            if keyitems.HM02:
                flight_btn = Button(
                    style=ButtonStyle.green,
                    label="🕊️ Flight Map",
                    custom_id='bag_flight_map',
                    row=3
                )
                flight_btn.callback = self.on_flight_map_click
                view.add_item(flight_btn)
        
        return view

    async def on_battle_use_items_click(self, interaction: discord.Interaction):
        """Show item usage interface during battle"""
        user = interaction.user
        user_id = str(user.id)
        await interaction.response.defer()
        
        # Check which battle state this user is in
        battle_state = None
        is_wild_battle = False
        
        if user_id in self.__battle_states:
            battle_state = self.__battle_states[user_id]
        elif user_id in self.__wild_battle_states:
            battle_state = self.__wild_battle_states[user_id]
            is_wild_battle = True
        
        if not battle_state:
            await interaction.followup.send('Battle state not found.', ephemeral=True)
            return
        
        # Create item usage state
        self.__item_usage_states[user_id] = ItemUsageState(user_id)
        
        # Show item usage interface
        embed, view = self.__create_battle_item_usage_view(user, battle_state, is_wild_battle)
        await interaction.message.edit(embed=embed, view=view)


    def __create_battle_item_usage_view(self, user: discord.User, battle_state, is_wild_battle: bool) -> tuple[discord.Embed, View]:
        """Create the item usage interface during battle"""
        from services.trainerclass import trainer as TrainerClass
        from services.inventoryclass import inventory as InventoryClass
        from discord.ui import Select
        
        trainer = self._get_trainer(str(user.id))
        inv = InventoryClass(str(user.id))
        
        # Get party Pokemon from battle state
        if hasattr(battle_state, 'player_party'):
            pokeList = battle_state.player_party
        else:
            pokeList = [battle_state.player_pokemon]
        
        item_state = self.__item_usage_states.get(str(user.id), ItemUsageState(str(user.id)))
        
        # Create embed
        embed = discord.Embed(
            title="💊 Use Items in Battle",
            description="Select a Pokemon and an item to use.",
            color=discord.Color.blue()
        )
        embed.set_author(name=user.display_name, icon_url=str(user.display_avatar.url))
        
        view = View()
        
        # ROW 0: Pokemon selector
        pokemon_select = Select(placeholder="Choose a Pokemon", custom_id='battle_item_pokemon_select', row=0)
        for poke in pokeList:
            # Make sure Pokemon is loaded
            if not hasattr(poke, 'currentHP') or poke.currentHP is None:
                poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            pokemon_select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == item_state.selected_pokemon_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        pokemon_select.callback = self.on_battle_item_pokemon_select
        view.add_item(pokemon_select)
        
        # ROW 1: Item selector
        item_select = Select(placeholder="Choose an Item", custom_id='battle_item_item_select', row=1)
        
        usable_items = [
            ('potion', inv.potion, 'Potion', 'Restores 20 HP'),
            ('super-potion', inv.superpotion, 'Super Potion', 'Restores 50 HP'),
            ('hyper-potion', inv.hyperpotion, 'Hyper Potion', 'Restores 200 HP'),
            ('max-potion', inv.maxpotion, 'Max Potion', 'Fully restores HP'),
            ('revive', inv.revive, 'Revive', 'Revives fainted Pokemon (50% HP)'),
            ('full-restore', inv.fullrestore, 'Full Restore', 'Fully restores HP'),
        ]
        
        has_items = False
        for item_key, quantity, display_name, description in usable_items:
            if quantity > 0:
                has_items = True
                item_select.add_option(
                    label=f"{display_name} (x{quantity})",
                    value=item_key,
                    description=description[:100],
                    default=(item_key == item_state.selected_item)
                )
        
        if not has_items:
            embed.add_field(
                name="❌ No Usable Items",
                value="You don't have any healing items!",
                inline=False
            )
        else:
            item_select.callback = self.on_battle_item_item_select
            view.add_item(item_select)
            
            # ROW 2: Use button
            use_disabled = not (item_state.selected_pokemon_id and item_state.selected_item)
            use_btn = Button(
                style=ButtonStyle.green,
                label="✅ Use Item",
                custom_id='battle_item_use',
                row=2,
                disabled=use_disabled
            )
            use_btn.callback = self.on_battle_item_use_click
            view.add_item(use_btn)
        
        # ROW 3: Back to battle button
        back_btn = Button(
            style=ButtonStyle.gray,
            label="← Back to Battle",
            custom_id='battle_item_back',
            row=3
        )
        back_btn.callback = self.on_battle_item_back_click
        view.add_item(back_btn)
        
        return embed, view


    async def on_battle_item_pokemon_select(self, interaction: discord.Interaction):
        """Handle Pokemon selection during battle item usage"""
        user = interaction.user
        user_id = str(user.id)
        
        if user_id not in self.__item_usage_states:
            await interaction.response.send_message('Session expired.', ephemeral=True)
            return
        
        # Update selected Pokemon
        selected_value = interaction.data['values'][0]
        self.__item_usage_states[user_id].selected_pokemon_id = selected_value
        
        # Get battle state
        battle_state = None
        is_wild_battle = False
        if user_id in self.__battle_states:
            battle_state = self.__battle_states[user_id]
        elif user_id in self.__wild_battle_states:
            battle_state = self.__wild_battle_states[user_id]
            is_wild_battle = True
        
        # Recreate view with updated selection
        embed, view = self.__create_battle_item_usage_view(user, battle_state, is_wild_battle)
        await interaction.response.edit_message(embed=embed, view=view)


    async def on_battle_item_item_select(self, interaction: discord.Interaction):
        """Handle item selection during battle item usage"""
        user = interaction.user
        user_id = str(user.id)
        
        if user_id not in self.__item_usage_states:
            await interaction.response.send_message('Session expired.', ephemeral=True)
            return
        
        # Update selected item
        selected_value = interaction.data['values'][0]
        self.__item_usage_states[user_id].selected_item = selected_value
        
        # Get battle state
        battle_state = None
        is_wild_battle = False
        if user_id in self.__battle_states:
            battle_state = self.__battle_states[user_id]
        elif user_id in self.__wild_battle_states:
            battle_state = self.__wild_battle_states[user_id]
            is_wild_battle = True
        
        # Recreate view with updated selection
        embed, view = self.__create_battle_item_usage_view(user, battle_state, is_wild_battle)
        await interaction.response.edit_message(embed=embed, view=view)


    async def on_battle_item_use_click(self, interaction: discord.Interaction):
        """Use the selected item during battle"""
        user = interaction.user
        user_id = str(user.id)
        await interaction.response.defer(ephemeral=True)
        
        if user_id not in self.__item_usage_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        item_state = self.__item_usage_states[user_id]
        
        if not item_state.selected_pokemon_id or not item_state.selected_item:
            await interaction.followup.send('Please select both a Pokemon and an item.', ephemeral=True)
            return
        
        from services.trainerclass import trainer as TrainerClass
        
        # Get battle state
        battle_state = None
        is_wild_battle = False
        if user_id in self.__battle_states:
            battle_state = self.__battle_states[user_id]
        elif user_id in self.__wild_battle_states:
            battle_state = self.__wild_battle_states[user_id]
            is_wild_battle = True
        
        if not battle_state:
            await interaction.followup.send('Battle state not found.', ephemeral=True)
            return
        
        # Find the Pokemon in the battle state's party
        target_pokemon = None
        selected_trainer_id = int(item_state.selected_pokemon_id)
        
        if hasattr(battle_state, 'player_party'):
            for poke in battle_state.player_party:
                if poke.trainerId == selected_trainer_id:
                    target_pokemon = poke
                    break
        elif battle_state.player_pokemon.trainerId == selected_trainer_id:
            target_pokemon = battle_state.player_pokemon
        
        if not target_pokemon:
            await interaction.followup.send('Pokemon not found in battle.', ephemeral=True)
            return
        
        # Get Pokemon stats to calculate healing
        stats = target_pokemon.getPokeStats()
        max_hp = stats['hp']
        current_hp = target_pokemon.currentHP
        item = item_state.selected_item
        
        # Check inventory and calculate healing
        from services.inventoryclass import inventory as InventoryClass
        inv = InventoryClass(user_id)
        
        # Validate item usage
        if item == 'revive' and current_hp > 0:
            await interaction.followup.send('❌ You cannot use Revive on this Pokemon - it is not fainted!', ephemeral=True)
            return
        
        if item != 'revive' and current_hp <= 0:
            await interaction.followup.send('❌ You cannot use a potion on a fainted Pokemon!', ephemeral=True)
            return
        
        # Check inventory quantity
        has_item = False
        if item == 'potion' and inv.potion > 0:
            has_item = True
            inv.potion -= 1
        elif item == 'super-potion' and inv.superpotion > 0:
            has_item = True
            inv.superpotion -= 1
        elif item == 'hyper-potion' and inv.hyperpotion > 0:
            has_item = True
            inv.hyperpotion -= 1
        elif item == 'max-potion' and inv.maxpotion > 0:
            has_item = True
            inv.maxpotion -= 1
        elif item == 'revive' and inv.revive > 0:
            has_item = True
            inv.revive -= 1
        elif item == 'full-restore' and inv.fullrestore > 0:
            has_item = True
            inv.fullrestore -= 1
        
        if not has_item:
            await interaction.followup.send('❌ You do not have that item!', ephemeral=True)
            return
        
        # Calculate new HP based on item type
        new_hp = current_hp
        
        if item == 'revive':
            new_hp = max_hp // 2  # 50% HP
        elif item == 'potion':
            new_hp = min(current_hp + 20, max_hp)
        elif item == 'super-potion':
            new_hp = min(current_hp + 50, max_hp)
        elif item == 'hyper-potion':
            new_hp = min(current_hp + 200, max_hp)
        elif item == 'max-potion' or item == 'full-restore':
            new_hp = max_hp
        
        # Calculate HP restored
        hp_restored = new_hp - current_hp
        
        # UPDATE THE BATTLE STATE POKEMON'S HP (THIS IS THE KEY FIX!)
        target_pokemon.currentHP = new_hp
        
        # Save inventory changes
        inv.save()
        
        # Send success message
        item_display_name = item.replace('-', ' ').title()
        poke_display_name = target_pokemon.nickName if target_pokemon.nickName else target_pokemon.pokemonName.capitalize()
        
        await interaction.followup.send(
            f'✅ Used {item_display_name} on {poke_display_name}! Restored {hp_restored} HP! (Now at {new_hp}/{max_hp} HP)',
            ephemeral=True
        )
        
        # Refresh the item usage view to show updated HP
        embed, view = self.__create_battle_item_usage_view(user, battle_state, is_wild_battle)
        await interaction.message.edit(embed=embed, view=view)


    async def on_battle_item_back_click(self, interaction: discord.Interaction):
        """Return to battle from item usage"""
        user = interaction.user
        user_id = str(user.id)
        await interaction.response.defer()
        
        # Clean up item usage state
        if user_id in self.__item_usage_states:
            del self.__item_usage_states[user_id]
        
        # Get battle state
        battle_state = None
        is_wild_battle = False
        
        if user_id in self.__battle_states:
            battle_state = self.__battle_states[user_id]
        elif user_id in self.__wild_battle_states:
            battle_state = self.__wild_battle_states[user_id]
            is_wild_battle = True
        
        if not battle_state:
            await interaction.followup.send('Battle state not found.', ephemeral=True)
            return
        
        # Return to battle view
        if is_wild_battle:
            embed = self.__create_wild_battle_embed(user, battle_state)
        else:
            embed = self.__create_battle_embed(user, battle_state)
        
        view = self.__create_battle_move_buttons_with_items(battle_state)
        await interaction.message.edit(embed=embed, view=view)

    async def on_pc_back_to_bag_click(self, interaction: discord.Interaction):
        """Return to bag items view from PC"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        bag_state.current_view = 'items'
        bag_state.pc_selected_pokemon_id = None  # Clear PC selection
        
        embed = self.__create_items_embed(user)
        view = self.__create_bag_navigation_view('items')
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_bag_pc_release_click(self, interaction: discord.Interaction):
        """Release Pokemon from PC"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        selected_trainer_id = bag_state.pc_selected_pokemon_id
        
        if not selected_trainer_id:
            await interaction.followup.send('No Pokemon selected.', ephemeral=True)
            return
        
        from services.trainerclass import trainer as TrainerClass
        
        trainer = self._get_trainer(str(user.id))
        
        # Get Pokemon info before releasing
        pokemon = trainer.getPokemonById(int(selected_trainer_id))
        if not pokemon:
            await interaction.followup.send('Pokemon not found.', ephemeral=True)
            return
        
        pokemon.load(pokemonId=pokemon.trainerId)
        
        # Check if it's the starter
        starter = trainer.getStarterPokemon()
        if pokemon.trainerId == starter.trainerId:
            await interaction.followup.send('You cannot release your starter Pokemon!', ephemeral=True)
            return
        
        poke_name = pokemon.nickName if pokemon.nickName else pokemon.pokemonName.capitalize()
        
        # Release the Pokemon
        trainer.releasePokemon(pokemon.trainerId)
        
        await interaction.followup.send(f'Released {poke_name}.', ephemeral=True)
        
        # Reset PC selection
        bag_state.pc_selected_pokemon_id = None
        
        # Refresh PC view
        await self.on_bag_pc_click(interaction)
        

    async def on_bag_pc_withdraw_click(self, interaction: discord.Interaction):
        """Withdraw Pokemon from PC to party"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        selected_trainer_id = bag_state.pc_selected_pokemon_id
        
        if not selected_trainer_id:
            await interaction.followup.send('No Pokemon selected.', ephemeral=True)
            return
        
        from services.trainerclass import trainer as TrainerClass
        
        trainer = self._get_trainer(str(user.id))
        
        # Get Pokemon name before withdrawing
        pokemon = trainer.getPokemonById(int(selected_trainer_id))
        if pokemon:
            pokemon.load(pokemonId=pokemon.trainerId)
            poke_name = pokemon.nickName if pokemon.nickName else pokemon.pokemonName.capitalize()
        else:
            poke_name = "Pokemon"
        
        # Attempt withdraw
        trainer.withdraw(int(selected_trainer_id))
        
        if trainer.statuscode == 420:
            # Failed - party full
            await interaction.followup.send(trainer.message, ephemeral=True)
            return
        
        # Success - show message
        await interaction.followup.send(f'✅ {poke_name} withdrawn to party!', ephemeral=True)
        
        # Reset PC selection
        bag_state.pc_selected_pokemon_id = None
        
        # Refresh PC view - need to manually build it since interaction is already deferred
        from services.trainerclass import trainer as TrainerClass
        from discord.ui import Select
        from discord import SelectOption
        
        trainer = self._get_trainer(str(user.id))
        pc_list = trainer.getPokemon(pc=True)
        pc_list.sort(key=lambda p: (p.nickName if hasattr(p, 'nickName') and p.nickName else p.pokemonName).lower())
        
        if len(pc_list) == 0:
            # PC is now empty
            embed = discord.Embed(
                title="💾 PC Storage",
                description="Your PC is empty! All Pokemon are in your party.",
                color=discord.Color.blue()
            )
            embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
            
            view = View()
            back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='pc_back_to_bag', row=0)
            back_btn.callback = self.on_pc_back_to_bag_click
            view.add_item(back_btn)
            
            map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='pc_back_to_map', row=0)
            map_btn.callback = self.on_bag_back_to_map_click
            view.add_item(map_btn)
            
            await interaction.message.edit(embed=embed, view=view)
            return
        
        # Select first Pokemon in updated list
        selected_trainer_id = str(pc_list[0].trainerId)
        bag_state.pc_selected_pokemon_id = selected_trainer_id
        
        selected_pokemon = pc_list[0]
        selected_pokemon.load(pokemonId=selected_pokemon.trainerId)
        
        # Create embed
        from .functions import createStatsEmbed
        embed = createStatsEmbed(user, selected_pokemon)
        embed.title = f"💾 PC - {embed.title}"
        
        # Create view
        view = View()
        
        # ROW 0: Pokemon selector
        select = Select(placeholder="Choose a Pokemon", custom_id='pc_pokemon_select', row=0)
        for poke in pc_list:
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_bag_pc_pokemon_select
        view.add_item(select)
        
        # ROW 1: PC management actions
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='bag_pc_moves', row=1)
        moves_btn.callback = self.on_bag_pc_moves_click
        view.add_item(moves_btn)
        
        withdraw_btn = Button(
            style=ButtonStyle.green,
            label="⬆️ Withdraw",
            custom_id='bag_pc_withdraw',
            row=1
        )
        withdraw_btn.callback = self.on_bag_pc_withdraw_click
        view.add_item(withdraw_btn)
        
        # ROW 2: Pokemon actions
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='bag_pc_release', row=2)
        release_btn.callback = self.on_bag_pc_release_click
        view.add_item(release_btn)
        
        # ROW 3: Navigation
        back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='pc_back_to_bag', row=3)
        back_btn.callback = self.on_pc_back_to_bag_click
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='pc_back_to_map', row=3)
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_bag_pc_moves_click(self, interaction: discord.Interaction):
        """Show moves for selected PC Pokemon"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        selected_trainer_id = bag_state.pc_selected_pokemon_id
        
        if not selected_trainer_id:
            await interaction.followup.send('No Pokemon selected.', ephemeral=True)
            return
        
        from services.trainerclass import trainer as TrainerClass
        
        trainer = self._get_trainer(str(user.id))
        pokemon = trainer.getPokemonById(int(selected_trainer_id))
        
        if not pokemon:
            await interaction.followup.send('Pokemon not found.', ephemeral=True)
            return
        
        # Reload to get latest data
        pokemon.load(pokemonId=pokemon.trainerId)
        
        from .functions import createPokemonAboutEmbed
        embed = createPokemonAboutEmbed(user, pokemon)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def on_bag_pc_pokemon_select(self, interaction: discord.Interaction):
        """Handle Pokemon selection in PC view"""
        user = interaction.user
        
        if str(user.id) not in self.__bag_states:
            await interaction.response.send_message('Session expired.', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        bag_state = self.__bag_states[str(user.id)]
        
        # Get selected Pokemon ID from select menu
        selected_trainer_id = interaction.data['values'][0]
        bag_state.pc_selected_pokemon_id = selected_trainer_id
        
        from services.trainerclass import trainer as TrainerClass
        
        trainer = self._get_trainer(str(user.id))
        pc_list = trainer.getPokemon(pc=True)
        
        # Find the selected Pokemon
        selected_pokemon = None
        for poke in pc_list:
            if str(poke.trainerId) == selected_trainer_id:
                selected_pokemon = poke
                break
        
        if selected_pokemon is None:
            await interaction.followup.send('Pokemon not found.', ephemeral=True)
            return
        
        # Reload to get latest stats
        selected_pokemon.load(pokemonId=selected_pokemon.trainerId)
        
        # Create embed for selected Pokemon
        from .functions import createStatsEmbed
        embed = createStatsEmbed(user, selected_pokemon)
        embed.title = f"💾 PC - {embed.title}"
        
        # Recreate view with updated selection
        from discord.ui import Select
        from discord import SelectOption
        
        view = View()
        
        # ROW 0: Pokemon selector
        select = Select(placeholder="Choose a Pokemon", custom_id='pc_pokemon_select', row=0)
        for poke in pc_list:
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_bag_pc_pokemon_select
        view.add_item(select)
        
        # ROW 1: PC management actions
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='bag_pc_moves', row=1)
        moves_btn.callback = self.on_bag_pc_moves_click
        view.add_item(moves_btn)
        
        withdraw_btn = Button(
            style=ButtonStyle.green,
            label="⬆️ Withdraw",
            custom_id='bag_pc_withdraw',
            row=1
        )
        withdraw_btn.callback = self.on_bag_pc_withdraw_click
        view.add_item(withdraw_btn)
        
        # ROW 2: Pokemon actions
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='bag_pc_release', row=2)
        release_btn.callback = self.on_bag_pc_release_click
        view.add_item(release_btn)

        # TRADE BUTTON
        trade_button, _ = self.get_trade_button_for_pc(str(user.id))
        view.add_item(trade_button)
        
        # ROW 3: Navigation
        back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='pc_back_to_bag', row=3)
        back_btn.callback = self.on_pc_back_to_bag_click
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='pc_back_to_map', row=3)
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_bag_pc_click(self, interaction: discord.Interaction):
        """Show PC view with Pokemon management interface"""
        user = interaction.user
        await interaction.response.defer()
        
        if str(user.id) not in self.__bag_states:
            await interaction.followup.send('Session expired. Use ,trainer map to start.', ephemeral=True)
            return
        
        bag_state = self.__bag_states[str(user.id)]
        
        # Check if location has a Pokemon Center
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        if not location.pokecenter:
            await interaction.followup.send('You need to be at a Pokémon Center to access the PC!', ephemeral=True)
            return
        
        bag_state.current_view = 'pc'
        
        from services.trainerclass import trainer as TrainerClass
        from discord.ui import Select
        from discord import SelectOption
        
        trainer = self._get_trainer(str(user.id))
        pc_list = trainer.getPokemon(pc=True)  # Get PC Pokemon

        if len(pc_list) == 0:
            # No Pokemon in PC
            embed = discord.Embed(
                title="💾 PC Storage",
                description="Your PC is empty! All Pokemon are in your party.",
                color=discord.Color.blue()
            )
            embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
            
            view = View()
            back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='pc_back_to_bag', row=0)
            back_btn.callback = self.on_pc_back_to_bag_click
            view.add_item(back_btn)
            
            map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='pc_back_to_map', row=0)
            map_btn.callback = self.on_bag_back_to_map_click
            view.add_item(map_btn)
            
            await interaction.message.edit(embed=embed, view=view)
            return

        # CRITICAL FIX: Default to first Pokemon if no selection, OR keep existing selection
        if bag_state.pc_selected_pokemon_id:
            selected_trainer_id = bag_state.pc_selected_pokemon_id
        else:
            # First time opening PC - select first Pokemon
            selected_trainer_id = str(pc_list[0].trainerId)
            bag_state.pc_selected_pokemon_id = selected_trainer_id  # SAVE IT!
        
        # Find the selected Pokemon and RELOAD IT
        selected_pokemon = None
        for poke in pc_list:
            if str(poke.trainerId) == selected_trainer_id:
                selected_pokemon = poke
                break
        
        if selected_pokemon is None:
            # Fallback to first if selected one not found
            selected_pokemon = pc_list[0]
            selected_trainer_id = str(selected_pokemon.trainerId)
            bag_state.pc_selected_pokemon_id = selected_trainer_id
        
        # Reload the selected Pokemon to get all its data
        selected_pokemon.load(pokemonId=selected_pokemon.trainerId)

        # Create embed for selected Pokemon
        from .functions import createStatsEmbed
        embed = createStatsEmbed(user, selected_pokemon)
        embed.title = f"💾 PC - {embed.title}"
        
        # Create view with Pokemon selector
        view = View()
        
        # ROW 0: Pokemon selector
        select = Select(placeholder="Choose a Pokemon", custom_id='pc_pokemon_select', row=0)
        for poke in pc_list:
            # Reload to get latest stats from database
            poke.load(pokemonId=poke.trainerId)
            
            shiny_tag = "✨" if hasattr(poke, 'is_shiny') and poke.is_shiny else ""
            label = f"{shiny_tag}{poke.pokemonName.capitalize()}"
            if poke.nickName:
                label = f"{shiny_tag}{poke.nickName} ({poke.pokemonName.capitalize()})"
            label += f" Lv.{poke.currentLevel}"
            
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_bag_pc_pokemon_select
        view.add_item(select)
        
        # ROW 1: PC management actions (NO Set Active)
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='bag_pc_moves', row=1)
        moves_btn.callback = self.on_bag_pc_moves_click
        view.add_item(moves_btn)
        
        withdraw_btn = Button(
            style=ButtonStyle.green,
            label="⬆️ Withdraw",
            custom_id='bag_pc_withdraw',
            row=1
        )
        withdraw_btn.callback = self.on_bag_pc_withdraw_click
        view.add_item(withdraw_btn)
        
        # ROW 2: Pokemon actions
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='bag_pc_release', row=2)
        release_btn.callback = self.on_bag_pc_release_click
        view.add_item(release_btn)
        
        # TRADE BUTTON 
        trade_button, _ = self.get_trade_button_for_pc(str(user.id))
        view.add_item(trade_button)

        # ROW 3: Navigation
        back_btn = Button(style=ButtonStyle.gray, label="← Back to Bag", custom_id='pc_back_to_bag', row=3)
        back_btn.callback = self.on_pc_back_to_bag_click
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='pc_back_to_map', row=3)
        map_btn.callback = self.on_bag_back_to_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)

    def __create_pokedex_embed(self, user: discord.User, index: int = 0) -> discord.Embed:
        """Create embed showing trainer's pokedex with individual Pokemon details"""
        from services.trainerclass import trainer as TrainerClass
        from services.pokeclass import Pokemon as PokemonClass
        from services.pokedexclass import pokedex as PokedexClass
        from models.pokedex import PokedexModel
        
        trainer = self._get_trainer(str(user.id))
        pokedex_list: List[PokedexModel] = trainer.getPokedex()
        
        if len(pokedex_list) == 0:
            embed = discord.Embed(
                title="Pokédex",
                description="No Pokémon encountered yet!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://pokesprites.joshkohut.com/sprites/pokedex.png")
            embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
            return embed
        
        # Sort by Pokemon ID
        pokedex_list.sort(key=lambda x: x.pokemonId)
        
        # Get current Pokemon entry
        current_entry = pokedex_list[index]
        
        # Load the Pokemon config data (species info from pokemon.json)
        try:
            pokemon_config = load_json_config('pokemon.json')
            poke_data = pokemon_config.get(current_entry.pokemonName, {})
            
            # Get type info directly from config
            type1 = poke_data.get('type1', 'unknown')
            type2 = poke_data.get('type2')  # Can be None
            
            # Get sprite URLs
            sprite_base = "https://pokesprites.joshkohut.com/sprites/pokemon/"
            sprite_url = f"{sprite_base}{current_entry.pokemonId}.png"
            
        except Exception as e:
            print(f"Error loading Pokemon config: {e}")
            # Fallback
            type1 = "unknown"
            type2 = None
            sprite_url = f"https://pokesprites.joshkohut.com/sprites/pokemon/{current_entry.pokemonId}.png"
        
        # Create color based on type (with safety check)
        from .functions import getTypeColor
        try:
            color = getTypeColor(type1) if type1 else discord.Color.blue()
        except:
            color = discord.Color.blue()
        
        embed = discord.Embed(
            title=f"#{str(current_entry.pokemonId).zfill(3)} - {current_entry.pokemonName.capitalize()}",
            color=color
        )
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        embed.set_thumbnail(url=sprite_url)
        
        # Type info - format as Type1/Type2
        if type2 is not None and type2:
            types = f"{type1.capitalize()}/{type2.capitalize()}"
        else:
            types = type1.capitalize()
        embed.add_field(name="Type", value=types, inline=True)
        
        # Physical attributes
        embed.add_field(name="Height", value=f"{current_entry.height / 10} m", inline=True)
        embed.add_field(name="Weight", value=f"{current_entry.weight / 10} kg", inline=True)
        
        # Most recent catch date
        embed.add_field(name="First Seen", value=current_entry.mostRecent, inline=False)
        
        # Description
        embed.add_field(name="Description", value=current_entry.description, inline=False)
        
        # Footer showing progress
        embed.set_footer(text=f"Pokédex Entry {index + 1} of {len(pokedex_list)}")
        
        return embed

    def __create_trainer_embed(self, user: discord.User) -> discord.Embed:
        """Create embed showing trainer card"""
        from services.trainerclass import trainer as TrainerClass
        from services.inventoryclass import inventory as InventoryClass
        from services.keyitemsclass import keyitems as KeyItemsClass
        import constant
        
        trainer = self._get_trainer(str(user.id))
        inventory = InventoryClass(trainer.discordId)
        keyitems = KeyItemsClass(trainer.discordId)
        
        embed = discord.Embed(title="Bag - Trainer", color=discord.Color.blue())
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        
        embed.add_field(name='Money', value=f'¥{inventory.money}', inline=False)
        
        badges = []
        if keyitems.badge_boulder:
            badges.append(constant.BADGE_BOULDER_01)
        if keyitems.badge_cascade:
            badges.append(constant.BADGE_CASCADE_02)
        if keyitems.badge_thunder:
            badges.append(constant.BADGE_THUNDER_03)
        if keyitems.badge_rainbow:
            badges.append(constant.BADGE_RAINBOW_04)
        if keyitems.badge_soul:
            badges.append(constant.BADGE_SOUL_05)
        if keyitems.badge_marsh:
            badges.append(constant.BADGE_MARSH_06)
        if keyitems.badge_volcano:
            badges.append(constant.BADGE_VOLCANO_07)
        if keyitems.badge_earth:
            badges.append(constant.BADGE_EARTH_08)
        
        badgeText = " ".join(badges) if len(badges) > 0 else "--"
        embed.add_field(name='Badges', value=badgeText, inline=False)
        
        pokedex_list = trainer.getPokedex()
        pokedex_count = len(pokedex_list) if pokedex_list else 0
        embed.add_field(name='Pokédex', value=f'{pokedex_count}')
        
        embed.add_field(name='Started', value=f'{trainer.startdate}')
        
        return embed

    def __create_hms_embed(self, user: discord.User) -> discord.Embed:
        """Create embed showing trainer's HMs"""
        from services.keyitemsclass import keyitems as KeyItemClass
        import constant
        
        keyitems = KeyItemClass(str(user.id))
        
        embed = discord.Embed(title="Bag - HMs", color=discord.Color.purple())
        embed.set_thumbnail(url="https://pokesprites.joshkohut.com/sprites/trainer_bag.png")
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        
        hms = []
        
        if keyitems.HM01:
            hms.append(f'{constant.HM01} **HM01** - Cut')
        if keyitems.HM02:
            hms.append(f'{constant.HM02} **HM02** - Fly')
        if keyitems.HM03:
            hms.append(f'{constant.HM03} **HM03** - Surf')
        if keyitems.HM04:
            hms.append(f'{constant.HM04} **HM04** - Strength')
        if keyitems.HM05:
            hms.append(f'{constant.HM05} **HM05** - Flash')
        
        hms_text = "\n".join(hms) if len(hms) > 0 else "No HMs yet."
        embed.add_field(name="HMs", value=hms_text, inline=False)
        
        return embed

    async def on_pokemon_select(self, interaction: discord.Interaction):
        """Handle Pokemon selection from dropdown - enables action buttons"""
        user = interaction.user
        
        # Get selected Pokemon trainerId from dropdown value
        selected_trainer_id = interaction.data['values'][0]
        
        trainer = self._get_trainer(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        active = trainer.getActivePokemon()
        
        # Find the selected Pokemon
        selected_pokemon = None
        for poke in pokeList:
            poke.load(pokemonId=poke.trainerId)
            if str(poke.trainerId) == selected_trainer_id:
                selected_pokemon = poke
                break
        
        if not selected_pokemon:
            await interaction.response.send_message('Pokemon not found.', ephemeral=True)
            return
        
        # Store selected Pokemon in user actions for later use by buttons
        if str(user.id) not in self.__useractions:
            # Create a basic action state if it doesn't exist
            location = trainer.getLocation()
            self.__useractions[str(user.id)] = ActionState(
                str(user.id), 
                interaction.message.channel.id, 
                interaction.message.id, 
                location, 
                selected_pokemon, 
                None, 
                ''
            )
        else:
            self.__useractions[str(user.id)].activePokemon = selected_pokemon
        
        # Update the embed to show selected Pokemon details
        embed = discord.Embed(
            title="💥 Your Party",
            description=f"**Selected:** {selected_pokemon.nickName or selected_pokemon.pokemonName.capitalize()}",
            color=discord.Color.blue()
        )
        
        # Show all party Pokemon
        for i, poke in enumerate(pokeList, 1):
            poke.load(pokemonId=poke.trainerId)
            stats = poke.getPokeStats()
            is_active = "⭐ " if poke.trainerId == active.trainerId else ""
            is_selected = "➤ " if poke.trainerId == selected_pokemon.trainerId else ""
            
            # Use Pokemon emoji from constant
            pokemon_emoji = constant.POKEMON_EMOJIS.get(
                poke.pokemonName.upper(),
                f":{poke.pokemonName}:"
            )
            
            if poke.currentHP <= 0:
                status_text = "💀 FAINTED"
            else:
                status_text = f"HP: {poke.currentHP}/{stats['hp']}"
            
            poke_name = poke.nickName if poke.nickName else poke.pokemonName.capitalize()
            
            embed.add_field(
                name=f"{is_active}{is_selected}{pokemon_emoji} {i}. {poke_name}",
                value=f"Lv.{poke.currentLevel} | {status_text}",
                inline=False
            )
        
        embed.set_footer(text="Use the buttons below to manage the selected Pokemon")
        
        # Recreate view with buttons NOW ENABLED
        view = View()
        
        # ROW 0: Pokemon selection dropdown (keep it)
        from discord.ui import Select
        
        select = Select(
            placeholder=f"Selected: {selected_pokemon.nickName or selected_pokemon.pokemonName.capitalize()}",
            custom_id="pokemon_select",
            row=0
        )
        
        # Re-add all options
        for i, poke in enumerate(pokeList, 1):
            poke.load(pokemonId=poke.trainerId)
            poke_name = poke.nickName if poke.nickName else poke.pokemonName.capitalize()
            
            label = f"{'⭐ ' if poke.trainerId == active.trainerId else ''}{poke_name} (Lv.{poke.currentLevel})"
            
            stats = poke.getPokeStats()
            if poke.currentHP <= 0:
                description = "💀 Fainted"
            else:
                description = f"HP: {poke.currentHP}/{stats['hp']}"
            
            select.add_option(
                label=label[:100],
                value=str(poke.trainerId),
                description=description[:100],
                default=(str(poke.trainerId) == selected_trainer_id),
                emoji=constant.POKEMON_EMOJIS.get(poke.pokemonName.upper())
            )
        
        select.callback = self.on_pokemon_select
        view.add_item(select)
        
        # ROW 1: Party management actions (NOW ENABLED)
        moves_btn = Button(style=ButtonStyle.blurple, label="🎯 Moves", custom_id='party_moves', row=1)
        moves_btn.callback = self.on_party_moves_click
        view.add_item(moves_btn)
        
        # Disable Set Active if already active
        is_already_active = (selected_pokemon.trainerId == active.trainerId)
        set_active_btn = Button(
            style=ButtonStyle.green if not is_already_active else ButtonStyle.gray,
            label="⭐ Set Active",
            custom_id='party_set_active',
            row=1,
            disabled=is_already_active
        )
        set_active_btn.callback = self.on_party_set_active_click
        view.add_item(set_active_btn)
        
        # ROW 2: Pokemon actions
        use_items_btn = Button(style=ButtonStyle.blurple, label="💊 Use Items", custom_id='bag_party_use_items', row=2)
        use_items_btn.callback = self.on_bag_party_use_items_click
        view.add_item(use_items_btn)

        # Only show Deposit if at a Pokemon Center
        _dep_location = self._get_trainer(str(user.id)).getLocation()
        if _dep_location.pokecenter:
            deposit_btn = Button(style=ButtonStyle.gray, label="💾 Deposit", custom_id='bag_party_deposit', row=2)
            deposit_btn.callback = self.on_bag_party_deposit_click
            view.add_item(deposit_btn)
        
        release_btn = Button(style=ButtonStyle.red, label="🗑️ Release", custom_id='party_release', row=2)
        release_btn.callback = self.on_party_release_click
        view.add_item(release_btn)
        
        # ROW 3: Navigation
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='nav_map', row=3)
        map_btn.callback = self.on_nav_map_click
        view.add_item(map_btn)
        
        # IMPORTANT: Use response.edit_message instead of message.edit when responding to Select interaction
        await interaction.response.edit_message(embed=embed, view=view)

    async def on_party_moves_click(self, interaction: discord.Interaction):
        """Show moves for selected Pokemon (PLACEHOLDER)"""
        await interaction.response.send_message(
            'Moves view coming soon! Use `,trainer party` for full functionality.',
            ephemeral=True
        )
    
    async def on_party_set_active_click(self, interaction: discord.Interaction):
        """Set active Pokemon (PLACEHOLDER)"""
        await interaction.response.send_message(
            'Set Active coming soon! Use `,trainer party` for full functionality.',
            ephemeral=True
        )
    
    async def on_party_release_click(self, interaction: discord.Interaction):
        """Release Pokemon (PLACEHOLDER)"""
        await interaction.response.send_message(
            'Release coming soon! Use `,trainer party` for full functionality.',
            ephemeral=True
        )

    async def on_party_deposit_click(self, interaction: discord.Interaction):
        """Deposit Pokemon to PC (PLACEHOLDER)"""
        await interaction.response.send_message(
            'Deposit coming soon! Use `,trainer party` for full functionality.',
            ephemeral=True
        )


    async def on_nav_encounters_click(self, interaction: discord.Interaction):
        """Handle Encounters button - show encounter options with back button"""
        user = interaction.user
        await interaction.response.defer()
        
        trainer = self._get_trainer(str(user.id))
        location_model = trainer.getLocation()
        
        location = LocationClass(str(user.id))
        methods = location.getMethods()
        
        if len(methods) == 0:
            await interaction.followup.send('No encounters available here.', ephemeral=True)
            return
        
        # Create encounter buttons
        view = View()
        for method in methods:
            button = Button(style=ButtonStyle.gray, label=f"{method.name}", custom_id=f'{method.value}')
            button.callback = self.on_action_encounter
            view.add_item(button)
        
        # REMOVED: Wild trainers button code (it only shows on map now)
        
        # Back to map button
        back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='nav_map', row=1)
        back_btn.callback = self.on_nav_map_click
        view.add_item(back_btn)
        
        from .constant import LOCATION_DISPLAY_NAMES
        location_name = LOCATION_DISPLAY_NAMES.get(location_model.name, location_model.name.replace('-', ' ').title())
        
        message = await interaction.message.edit(
            content=f"**{location_name}**\nWhat do you want to do?",
            view=view
        )
        
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, location_model, trainer.getActivePokemon(), None, ''
        )

    async def on_nav_quests_click(self, interaction: discord.Interaction):
        """Handle Quests button - show quest options with back button"""
        user = interaction.user
        await interaction.response.defer()
        
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        quest_buttons = self.__get_available_quests(str(user.id), location.name)
        
        if len(quest_buttons) == 0:
            await interaction.followup.send('No quests available here.', ephemeral=True)
            return
        
        # DON'T delete action state - just create new view
        # Quest buttons don't need action state
        
        # Create view with quest buttons
        view = View()
        for quest_btn in quest_buttons:
            view.add_item(quest_btn)
        
        # Back to map button with dedicated callback
        back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='quest_back_to_map', row=1)
        back_btn.callback = self.on_quest_back_to_map_click
        view.add_item(back_btn)
        
        from .constant import LOCATION_DISPLAY_NAMES
        location_name = LOCATION_DISPLAY_NAMES.get(location.name, location.name.replace('-', ' ').title())
        
        await interaction.message.edit(
            content=f"**{location_name}**\nAvailable Quests:",
            view=view
        )

    async def on_quest_back_to_map_click(self, interaction: discord.Interaction):
        """Handle Back to Map from quest menu"""
        user = interaction.user
        await interaction.response.defer()
        
        # Call the main map navigation method
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        # Get available actions at this location
        location_obj = LocationClass(str(user.id))
        methods = location_obj.getMethods()
        quest_buttons = self.__get_available_quests(str(user.id), location.name)
        gym_button = self.__get_gym_button(str(user.id), location.locationId)
        wild_trainers_button = self.__get_wild_trainers_button(str(user.id), location.locationId)

        from .constant import LOCATION_DISPLAY_NAMES
        location_name = LOCATION_DISPLAY_NAMES.get(location.name, location.name.replace('-', ' ').title())
        
        # Create embed
        embed = discord.Embed(
            title=f"{location_name}",
            description=f"You are at {location_name}.",
            color=discord.Color.blue()
        )

        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        
        # Load location sprite
        try:
            # Convert to full file system path
            full_sprite_path = get_sprite_path(location.spritePath)
            sprite_file = discord.File(full_sprite_path, filename=f"{location.name}.png")

            temp_message = await self.sendToLoggingChannel(f'{user.display_name} viewing map', sprite_file)
            if temp_message and temp_message.attachments:
                attachment = temp_message.attachments[0]
                embed.set_image(url=attachment.url)
        except Exception as e:
            print(f"Error loading location sprite: {e}")
            try:
                sprite_url = f"https://pokesprites.joshkohut.com/sprites/locations/{location.name}.png"
                embed.set_image(url=sprite_url)
            except:
                pass
        
        # Create navigation view
        view = View()
        
        # ROW 0: North/South buttons
        if location.north:
            north_name = LOCATION_DISPLAY_NAMES.get(location.north, location.north)
            north_btn = Button(style=ButtonStyle.gray, emoji='⬆️', label=f"{north_name[:15]}", custom_id='dir_north', row=0)
            north_btn.callback = self.on_direction_click
            view.add_item(north_btn)
        else:
            north_btn = Button(style=ButtonStyle.gray, emoji='⬆️', label="---", custom_id='dir_north_disabled', disabled=True, row=0)
            view.add_item(north_btn)
        
        if location.south:
            south_name = LOCATION_DISPLAY_NAMES.get(location.south, location.south)
            south_btn = Button(style=ButtonStyle.gray, emoji='⬇️', label=f"{south_name[:15]}", custom_id='dir_south', row=0)
            south_btn.callback = self.on_direction_click
            view.add_item(south_btn)
        else:
            south_btn = Button(style=ButtonStyle.gray, emoji='⬇️', label="---", custom_id='dir_south_disabled', disabled=True, row=0)
            view.add_item(south_btn)
        
        # ROW 1: East/West buttons
        if location.west:
            west_name = LOCATION_DISPLAY_NAMES.get(location.west, location.west)
            west_btn = Button(style=ButtonStyle.gray, emoji='⬅️', label=f"{west_name[:15]}", custom_id='dir_west', row=1)
            west_btn.callback = self.on_direction_click
            view.add_item(west_btn)
        else:
            west_btn = Button(style=ButtonStyle.gray, emoji='⬅️', label="---", custom_id='dir_west_disabled', disabled=True, row=1)
            view.add_item(west_btn)
        
        if location.east:
            east_name = LOCATION_DISPLAY_NAMES.get(location.east, location.east)
            east_btn = Button(style=ButtonStyle.gray, emoji='➡️', label=f"{east_name[:15]}", custom_id='dir_east', row=1)
            east_btn.callback = self.on_direction_click
            view.add_item(east_btn)
        else:
            east_btn = Button(style=ButtonStyle.gray, emoji='➡️', label="---", custom_id='dir_east_disabled', disabled=True, row=1)
            view.add_item(east_btn)
        
        # AUX button (if exists)
        if hasattr(location, 'aux') and location.aux:
            aux_name = LOCATION_DISPLAY_NAMES.get(location.aux, location.aux)
            aux_btn = Button(style=ButtonStyle.gray, emoji='🔀', label=f"{aux_name[:15]}", custom_id='dir_aux', row=1)
            aux_btn.callback = self.on_direction_click
            view.add_item(aux_btn)

        # ROW 2: Action buttons (Encounters, Quests, Gym)
        if len(methods) > 0:
            enc_btn = Button(style=ButtonStyle.green, label="⚔️ Encounters", custom_id='nav_encounters', row=2)
            enc_btn.callback = self.on_nav_encounters_click
            view.add_item(enc_btn)
        
        if len(quest_buttons) > 0:
            quest_btn = Button(style=ButtonStyle.blurple, label="📜 Quests", custom_id='nav_quests', row=2)
            quest_btn.callback = self.on_nav_quests_click
            view.add_item(quest_btn)
        
        if gym_button and not gym_button.disabled:
            gym_btn = Button(style=ButtonStyle.red, label="🏛️ Gym", custom_id='nav_gym', row=2)
            gym_btn.callback = self.on_gym_click
            view.add_item(gym_btn)
        
        if wild_trainers_button:
            view.add_item(wild_trainers_button)
        
        # ROW 3: Utility buttons
        bag_btn = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_bag', row=3)
        bag_btn.callback = self.on_nav_bag_click
        view.add_item(bag_btn)
        
        # Add Mart button if location has a Pokemart
        if self.__has_pokemart(location.locationId):
            mart_btn = Button(style=ButtonStyle.blurple, label="🏪 Mart", custom_id='nav_mart', row=3)
            mart_btn.callback = self.on_nav_mart_click
            view.add_item(mart_btn)

        if location.pokecenter:
            heal_btn = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal', row=3)
            heal_btn.callback = self.on_nav_heal_click
            view.add_item(heal_btn)
        
        message = await interaction.message.edit(embed=embed, view=view)
        
        # Update action state
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, location, trainer.getActivePokemon(), None, ''
        )


    async def on_nav_heal_click(self, interaction: discord.Interaction):
        """Handle Heal button - heal all Pokemon at Pokemon Center with detailed feedback"""
        user = interaction.user
        await interaction.response.defer()
        
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        if not location.pokecenter:
            await interaction.followup.send('No Pokemon Center at this location.', ephemeral=True)
            return
        
        # Get party before healing
        party = trainer.getPokemon(party=True)
        
        # Track healing details
        healing_details = []
        healed_count = 0
        
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
            stats = poke.getPokeStats()
            max_hp = stats['hp']
            current_hp = poke.currentHP
            
            from .functions import get_pokemon_display_name
            poke_name = get_pokemon_display_name(poke)
            
            # Try multiple name formats to find emoji
            # First try uppercase without hyphens/spaces
            clean_name = poke.pokemonName.upper().replace('-', '').replace(' ', '').replace('.', '')
            pokemon_emoji = constant.POKEMON_EMOJIS.get(clean_name)
            
            # If still not found, just use a generic Pokeball emoji or nothing
            if not pokemon_emoji:
                pokemon_emoji = constant.POKEBALL  # or just use "" for no emoji
            
            if current_hp < max_hp:
                # Pokemon needs healing
                hp_restored = max_hp - current_hp
                poke.currentHP = max_hp
                poke.save()
                healed_count += 1
                healing_details.append(f"{pokemon_emoji} {poke_name} - Lv.{poke.currentLevel}")
                healing_details.append(f"   HP: {current_hp}/{max_hp} → {max_hp}/{max_hp} (+{hp_restored})")
            else:
                # Already at full HP
                healing_details.append(f"{pokemon_emoji} {poke_name} - Lv.{poke.currentLevel}")
                healing_details.append(f"   HP: {max_hp}/{max_hp} ")
        
        embed = discord.Embed(
            title="🏥 Pokemon Center",
            description=f"Welcome! We've restored your Pokemon to full health!\n\n**Healed {healed_count} Pokemon**",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Your Party Status",
            value="\n".join(healing_details),
            inline=False
        )
        
        embed.set_footer(text="We hope to see you again!")
        
        # Keep the heal view with map navigation
        view = View()
        
        map_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='nav_map')
        map_btn.callback = self.on_nav_map_click
        view.add_item(map_btn)
        
        await interaction.message.edit(embed=embed, view=view)



    # Helper method to get next available Pokemon from party
    def __get_next_party_pokemon(self, party_list: list, current_index: int):
        """Get next Pokemon with HP > 0 from party"""
        for i in range(current_index + 1, len(party_list)):
            pokemon = party_list[i]
            pokemon.load(pokemonId=pokemon.trainerId)
            if pokemon.currentHP > 0:
                return pokemon, i
        return None, -1

    def __sort_party_active_first(self, alive_party: list, user_id: str) -> list:
            """Reorder alive_party so the active Pokemon is first"""
            from services.trainerclass import trainer as TrainerClass
            trainer = self._get_trainer(user_id)
            active = trainer.getActivePokemon()
            
            if active and hasattr(active, 'trainerId'):
                active_id = active.trainerId
                for i, poke in enumerate(alive_party):
                    if poke.trainerId == active_id:
                        if i != 0:
                            alive_party.insert(0, alive_party.pop(i))
                        break
            
            return alive_party

    def __get_battle_ready_pokemon(self, user_id: str, state_active=None):
        """Get the best Pokemon for battle - active if alive, otherwise first alive party Pokemon.
        Does NOT change the active Pokemon setting in the database.
        
        Args:
            user_id: The user's Discord ID
            state_active: The active Pokemon from state (already loaded). If None, fetches from DB.
        
        Returns:
            A loaded PokemonClass with currentHP > 0, or None if all fainted.
        """
        # Check if the provided active is usable
        if state_active is not None and not isinstance(state_active, str):
            # Reload to get latest HP from DB
            state_active.load(pokemonId=state_active.trainerId)
            if state_active.currentHP > 0:
                return state_active
        
        # Active is fainted or missing - find first alive party Pokemon
        trainer = self._get_trainer(user_id)
        party = trainer.getPokemon(party=True)
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
            if poke.currentHP > 0:
                return poke
        
        # All Pokemon fainted
        return None

    async def _start_manual_trainer_battle(self, interaction: discord.Interaction, 
                                            enemy_type: str, opponent, battle_manager,
                                            sprite_path: str = None, is_gym_leader: bool = False,
                                            gym_name: str = None, is_wild_trainer: bool = False):
        """
        Shared helper to start a manual trainer/leader battle.
        
        Args:
            interaction: The Discord interaction (already deferred)
            enemy_type: "gym" or "wild"
            opponent: The trainer/leader model (from getNextTrainer or getGymLeader)
            battle_manager: The BattleClass instance
            sprite_path: Path to intro sprite (None = skip intro)
            is_gym_leader: Whether this is a gym leader fight
            gym_name: Gym name for intro screen (only for gym leaders)
            is_wild_trainer: Whether this is a wild/route trainer
        """
        user = interaction.user
        
        # Get player's alive party
        trainer = self._get_trainer(str(user.id))
        player_party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in player_party:
            poke.load(pokemonId=poke.trainerId)
            if poke.currentHP > 0:
                alive_party.append(poke)
        
        if len(alive_party) == 0:
            await interaction.followup.send('All your party Pokemon have fainted! Heal at a Pokemon Center first.', ephemeral=True)
            return
        
        if not opponent:
            await interaction.followup.send('No trainer to battle.', ephemeral=True)
            return
        
        if not opponent.pokemon or len(opponent.pokemon) == 0:
            await interaction.followup.send(f'Error: {opponent.name} has no Pokemon data.', ephemeral=True)
            return
        
        # Show intro screen if sprite path provided
        target_message = interaction.message
        if sprite_path:
            target_message = await self.__show_battle_intro(
                interaction,
                opponent.name,
                sprite_path,
                is_gym_leader=is_gym_leader,
                gym_name=gym_name
            )
        
        # Create first enemy Pokemon
        enemy_pokemon_list = opponent.pokemon
        try:
            first_enemy_pokemon = self.__create_enemy_pokemon(enemy_pokemon_list[0], str(user.id))
        except Exception as e:
            error_msg = f'Error creating enemy Pokemon: {str(e)}'
            if sprite_path:
                await target_message.edit(content=error_msg)
            else:
                await interaction.followup.send(error_msg, ephemeral=True)
            return
        
        # Create battle state
        battle_state = BattleState(
            user_id=str(user.id),
            channel_id=interaction.channel_id,
            message_id=0,
            player_party=alive_party,
            enemy_pokemon_list=enemy_pokemon_list,
            enemy_name=opponent.name,
            trainer_model=opponent,
            battle_manager=battle_manager
        )
        
        battle_state.enemy_pokemon = first_enemy_pokemon
        battle_state.is_wild_trainer = is_wild_trainer
        
        # Initialize ailments
        battle_state.player_ailment = AilmentClass(alive_party[0].trainerId)
        battle_state.player_ailment.load()
        battle_state.enemy_ailment = AilmentClass('trainer_enemy')
        
        self.__battle_states[str(user.id)] = battle_state
        
        # Create battle UI
        embed = self.__create_battle_embed(user, battle_state)
        view = self.__create_battle_move_buttons_with_items(battle_state)
        
        battle_type = "Gym Leader" if is_gym_leader else "Manual"
        start_text = f"**{battle_type} Battle Started!**\n{opponent.name} has {len(enemy_pokemon_list)} Pokemon!"
        
        if sprite_path:
            message = await target_message.edit(
                content=start_text,
                embed=embed,
                view=view,
                attachments=[]
            )
        else:
            message = await interaction.message.edit(
                content=None,
                embed=embed,
                view=view
            )
        
        battle_state.message_id = message.id

    def __create_enemy_pokemon(self, pokemon_data: dict, player_discord_id: str):
        """
        Create an enemy Pokemon from dictionary data like {"geodude": 12}
            pokemon_data: Dictionary with single key-value pair like {"geodude": 12}
            player_discord_id: The player's Discord ID (needed for dynamic Pokemon resolution)
        """
        from services.pokedexclass import pokedex as PokedexClass
        
        enemy_name = list(pokemon_data.keys())[0]
        enemy_level = pokemon_data[enemy_name]
        
        # Pass player's Discord ID so dynamic Pokemon can resolve based on player's starter
        enemy_pokemon = PokemonClass(player_discord_id, enemy_name)
        
        enemy_pokemon.create(enemy_level)
        
        # IMPORTANT: Reset discordId to None after creation so enemy Pokemon don't save to player's database
        enemy_pokemon.discordId = None
        
        # Register enemy Pokemon to player's Pokedex
        PokedexClass(player_discord_id, enemy_pokemon)
        
        return enemy_pokemon

    async def __show_battle_intro(self, interaction: discord.Interaction, trainer_name: str, 
                                   sprite_path: str, is_gym_leader: bool, gym_name: str = None):
        """Show battle intro screen with trainer/gym leader sprite before battle starts"""
        
        if is_gym_leader:
            title = f"🏛️ {gym_name}"
            description = f"**Gym Leader {trainer_name}** wants to battle!"
        else:
            title = "⚔️ Trainer Battle!"
            description = f"**{trainer_name}** wants to battle!"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )
        
        # Set the trainer/gym leader sprite
        try:
            # The sprite_path from gyms.json is like: "/sprites/trainers/brock.png"
            # Convert to full file system path
            full_sprite_path = get_sprite_path(sprite_path)

            sprite_file = discord.File(full_sprite_path, filename=f"{trainer_name}.png")
            embed.set_image(url=f"attachment://{trainer_name}.png")
            
            message = await interaction.followup.send(
                embed=embed,
                file=sprite_file
            )
        except Exception as e:
            # Fallback if sprite file doesn't work - just show text
            print(f"Error loading sprite: {e}")
            message = await interaction.followup.send(embed=embed)
        
        # Wait 3 seconds
        await asyncio.sleep(3)
        
        return message

    def __create_battle_embed(self, user: discord.User, battle_state: BattleState) -> discord.Embed:
        """Create an embed showing the current battle state - Enemy first, Player second"""
        player_poke = battle_state.player_pokemon
        enemy_poke = battle_state.enemy_pokemon
        
        player_stats = player_poke.getPokeStats()
        enemy_stats = enemy_poke.getPokeStats()
        
        # Calculate HP percentages for visual bar
        player_hp_pct = (player_poke.currentHP / player_stats['hp']) * 100 if player_stats['hp'] > 0 else 0
        enemy_hp_pct = (enemy_poke.currentHP / enemy_stats['hp']) * 100 if enemy_stats['hp'] > 0 else 0

        # Get ailment emojis
        p_ailment_emoji = self.__get_ailment_emoji(battle_state.player_ailment, getattr(battle_state, 'rest_turns_player', 0))
        e_ailment_emoji = self.__get_ailment_emoji(battle_state.enemy_ailment, getattr(battle_state, 'rest_turns_enemy', 0))

        embed = discord.Embed(
            title=f"⚔️ Battle: {user.display_name} vs {battle_state.enemy_name}",
            description=f"**Turn {battle_state.turn_number}**\nChoose your move!",
            color=discord.Color.red()
        )
        
        # Enemy Pokemon info FIRST
        enemy_types = enemy_poke.type1
        if enemy_poke.type2:
            enemy_types += f", {enemy_poke.type2}"
        
        embed.add_field(
            name=f"❤️ Enemy {enemy_poke.pokemonName.capitalize()} (Lv.{enemy_poke.currentLevel}){e_ailment_emoji}",
            value=f"**HP:** {enemy_poke.currentHP}/{enemy_stats['hp']} {create_hp_bar(enemy_hp_pct)}\n"
                  f"**Type:** {enemy_types}",
            inline=False
        )
        
        # Player Pokemon info SECOND
        player_types = player_poke.type1
        if player_poke.type2:
            player_types += f", {player_poke.type2}"
        
        from .functions import get_pokemon_display_name
        player_display = get_pokemon_display_name(player_poke)
        embed.add_field(
            name=f"💚 Your {player_display} (Lv.{player_poke.currentLevel}){p_ailment_emoji}",
            value=f"**HP:** {player_poke.currentHP}/{player_stats['hp']} {create_hp_bar(player_hp_pct)}\n"
                  f"**Type:** {player_types}",
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



    async def on_battle_move_click(self, interaction: discord.Interaction):
        """Handle when player selects a move during manual battle - with ailment + special move support"""
        user = interaction.user
        user_id = str(user.id)

        if user_id not in self.__battle_states:
            await interaction.response.send_message('Battle state not found.', ephemeral=True)
            return

        battle_state = self.__battle_states[user_id]

        if battle_state.message_id != interaction.message.id:
            await interaction.response.send_message('This is not the current battle.', ephemeral=True)
            return

        await interaction.response.defer()

        move_name = interaction.data['custom_id'].replace('battle_move_', '')

        import random
        import math
        moves_config = load_json_config('moves.json')
        type_effectiveness = load_json_config('typeEffectiveness.json')
        from helpers.specialmoves import (
            handle_rest, handle_recover, calculate_drain_heal,
            calculate_night_shade_damage, calculate_leech_seed_damage,
            check_dream_eater_valid, check_accuracy, get_special_function,
            handle_haze
        )
        from helpers.statstages import apply_stat_change, apply_secondary_stat_change

        player_move_data = moves_config.get(move_name, {})
        player_power = player_move_data.get('power', 0)
        player_special_fn = get_special_function(player_move_data)

        log_lines = []
        log_lines.append(f"**Turn {battle_state.turn_number}:**")

        # Safety: init ailments if missing
        if not hasattr(battle_state, 'player_ailment') or battle_state.player_ailment is None:
            battle_state.player_ailment = AilmentClass(battle_state.player_pokemon.trainerId)
            battle_state.enemy_ailment = AilmentClass('trainer_enemy')

        # Safety: init special move tracking if missing (battles started before this update)
        if not hasattr(battle_state, 'rest_turns_player'):
            battle_state.rest_turns_player = 0
            battle_state.rest_turns_enemy = 0
            battle_state.leech_seed_player = False
            battle_state.leech_seed_enemy = False
            battle_state.player_stat_stages.reset()
            battle_state.enemy_stat_stages.reset()

        if not hasattr(battle_state, 'player_stat_stages'):
            from helpers.statstages import StatStages
            battle_state.player_stat_stages = StatStages()
            battle_state.enemy_stat_stages = StatStages()

        p_ailment = battle_state.player_ailment
        e_ailment = battle_state.enemy_ailment
        p_stages = battle_state.player_stat_stages
        e_stages = battle_state.enemy_stat_stages

        p_name = battle_state.player_pokemon.pokemonName.capitalize()
        e_name = f"Enemy {battle_state.enemy_pokemon.pokemonName.capitalize()}"
        move_display = move_name.replace('-', ' ').title()

        # =====================================================================
        # PLAYER'S TURN - Check Rest sleep first
        # =====================================================================
        player_can_attack = True
        player_burn_halve = False
        player_hit = False

        # Rest sleep check (overrides normal sleep)
        if battle_state.rest_turns_player > 0:
            battle_state.rest_turns_player -= 1
            if battle_state.rest_turns_player == 0:
                p_ailment.sleep = False
                p_ailment.turnCounter = 0
                log_lines.append(f"💤 {p_name} woke up from Rest!")
            else:
                log_lines.append(f"💤 {p_name} is sleeping from Rest!")
            player_can_attack = False

        # Normal ailment checks (only if not in Rest sleep)
        elif p_ailment.sleep:
            if p_ailment.turnCounter >= random.randint(1, 7):
                p_ailment.sleep = False
                p_ailment.turnCounter = 0
                log_lines.append(f"💤 {p_name} woke up!")
            else:
                p_ailment.turnCounter += 1
                log_lines.append(f"💤 {p_name} is fast asleep!")
                player_can_attack = False

        elif p_ailment.freeze:
            if random.randint(1, 5) == 1:
                p_ailment.freeze = False
                log_lines.append(f"🧊 {p_name} thawed out!")
            else:
                log_lines.append(f"🧊 {p_name} is frozen solid!")
                player_can_attack = False

        elif p_ailment.paralysis:
            if random.randint(1, 4) == 1:
                log_lines.append(f"⚡ {p_name} is paralyzed and can't move!")
                player_can_attack = False

        elif p_ailment.confusion:
            if p_ailment.turnCounter >= random.randint(2, 5):
                p_ailment.confusion = False
                p_ailment.turnCounter = 0
                log_lines.append(f"💫 {p_name} snapped out of confusion!")
            else:
                p_ailment.turnCounter += 1
                if random.randint(1, 2) == 1:
                    p_stats = battle_state.player_pokemon.getPokeStats()
                    self_damage = int(((2 * battle_state.player_pokemon.currentLevel / 5 + 2) * 40 * (p_stats['attack'] / p_stats['defense']) / 50 + 2))
                    self_damage = max(1, self_damage)
                    battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - self_damage)
                    log_lines.append(f"💫 {p_name} is confused and hurt itself for {self_damage} damage!")
                    player_can_attack = False

        elif p_ailment.trap:
            if p_ailment.turnCounter >= random.randint(2, 5):
                p_ailment.trap = False
                p_ailment.turnCounter = 0
                log_lines.append(f"🪢 {p_name} broke free!")
            else:
                p_ailment.turnCounter += 1
                p_stats = battle_state.player_pokemon.getPokeStats()
                trap_damage = max(1, p_stats['hp'] // 16)
                battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - trap_damage)
                log_lines.append(f"🪢 {p_name} is trapped! Took {trap_damage} damage!")
                player_can_attack = False

        if p_ailment.burn:
            player_burn_halve = True

        # =====================================================================
        # PLAYER ATTACKS (if able)
        # =====================================================================
        if player_can_attack:
            p_stats = battle_state.player_pokemon.getPokeStats()
            p_max_hp = p_stats['hp']
            e_stats = battle_state.enemy_pokemon.getPokeStats()
            e_max_hp = e_stats['hp']

            if 'stat_change' in player_move_data and not player_special_fn:
                move_hit = check_accuracy(player_move_data.get('accuracy', 100))
                if move_hit:
                    log_lines.append(f"• {p_name} used {move_display}!")
                    apply_stat_change(
                        player_move_data, p_stages, e_stages,
                        log_lines, p_name, e_name
                    )
                else:
                    log_lines.append(f"• {p_name} used {move_display} but it missed!")
                player_hit = True

            elif player_special_fn == 'haze':
                handle_haze(p_stages, e_stages)
                log_lines.append(f"• {p_name} used Haze! All stat changes were eliminated!")
                player_hit = True

            elif player_special_fn == 'rest':
                heal_amount, new_hp = handle_rest(battle_state.player_pokemon.currentHP, p_max_hp)
                battle_state.player_pokemon.currentHP = new_hp
                battle_state.rest_turns_player = 2
                p_ailment.resetAilments()
                p_ailment.sleep = True
                log_lines.append(f"• {p_name} used Rest! Recovered {heal_amount} HP and fell asleep! 💤")
                player_hit = True

            elif player_special_fn == 'recover':
                actual_heal, new_hp = handle_recover(battle_state.player_pokemon.currentHP, p_max_hp)
                battle_state.player_pokemon.currentHP = new_hp
                log_lines.append(f"• {p_name} used Recover! Restored {actual_heal} HP! 💚")
                player_hit = True

            elif player_special_fn == 'night_shade':
                if check_accuracy(player_move_data.get('accuracy', 100)):
                    ns_damage = calculate_night_shade_damage(battle_state.player_pokemon.currentLevel)
                    battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - ns_damage)
                    log_lines.append(f"• {p_name} used Night Shade! Dealt {ns_damage} damage!")
                    player_hit = True
                else:
                    log_lines.append(f"• {p_name} used Night Shade but it missed!")

            elif player_special_fn == 'leech_seed':
                if check_accuracy(player_move_data.get('accuracy', 100)):
                    if not battle_state.leech_seed_enemy:
                        battle_state.leech_seed_enemy = True
                        log_lines.append(f"• {p_name} used Leech Seed! {e_name} was seeded! 🌱")
                    else:
                        log_lines.append(f"• {p_name} used Leech Seed but {e_name} is already seeded!")
                    player_hit = True
                else:
                    log_lines.append(f"• {p_name} used Leech Seed but it missed!")

            elif player_special_fn == 'dream_eater':
                if e_ailment.sleep or battle_state.rest_turns_enemy > 0:
                    player_damage, player_hit = calculate_battle_damage(
                        battle_state.player_pokemon, battle_state.wild_pokemon,
                        move_name, moves_config, type_effectiveness,
                        p_stages, e_stages
                    )
                    if player_burn_halve and player_move_data.get('damage_class') == 'physical' and player_damage > 0:
                        player_damage = max(1, player_damage // 2)
                    if player_hit and player_damage > 0:
                        battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - player_damage)
                        drain_heal = calculate_drain_heal(player_damage)
                        battle_state.player_pokemon.currentHP = min(p_max_hp, battle_state.player_pokemon.currentHP + drain_heal)
                        log_lines.append(f"• {p_name} used Dream Eater! Dealt {player_damage} damage and drained {drain_heal} HP! 💜")
                    elif player_hit:
                        log_lines.append(f"• {p_name} used Dream Eater but dealt no damage!")
                    else:
                        log_lines.append(f"• {p_name} used Dream Eater but it missed!")
                else:
                    log_lines.append(f"• {p_name} used Dream Eater but it failed! Target is not asleep.")
                    player_hit = False

            elif player_special_fn == 'drain':
                player_damage, player_hit = calculate_battle_damage(
                    battle_state.player_pokemon, battle_state.wild_pokemon,
                    move_name, moves_config, type_effectiveness,
                    p_stages, e_stages
                )
                if player_burn_halve and player_move_data.get('damage_class') == 'physical' and player_damage > 0:
                    player_damage = max(1, player_damage // 2)
                if player_hit and player_damage > 0:
                    battle_state.wild_pokemon.currentHP = max(0, battle_state.wild_pokemon.currentHP - player_damage)
                    drain_heal = calculate_drain_heal(player_damage)
                    battle_state.player_pokemon.currentHP = min(p_max_hp, battle_state.player_pokemon.currentHP + drain_heal)
                    log_lines.append(f"• {p_name} used {move_display}! Dealt {player_damage} damage and drained {drain_heal} HP! 💚")
                elif player_hit:
                    log_lines.append(f"• {p_name} used {move_display}!")
                else:
                    log_lines.append(f"• {p_name} used {move_display} but it missed!")

            else:
                # --- NORMAL ATTACK (existing logic) ---
                player_damage, player_hit = calculate_battle_damage(
                    battle_state.player_pokemon, battle_state.enemy_pokemon,
                    move_name, moves_config, type_effectiveness,
                    p_stages, e_stages
                )

                if player_burn_halve and player_move_data.get('damage_class') == 'physical' and player_damage > 0:
                    player_damage = max(1, player_damage // 2)

                if player_hit and player_damage > 0:
                    battle_state.enemy_pokemon.currentHP = max(0, battle_state.enemy_pokemon.currentHP - player_damage)
                    log_lines.append(f"• {p_name} used {move_display}! Dealt {player_damage} damage!")
                elif player_hit and (player_power is None or player_power == 0):
                    log_lines.append(f"• {p_name} used {move_display}!")
                else:
                    log_lines.append(f"• {p_name} used {move_display} but it missed!")
                    player_hit = False

                # Roll ailment on enemy (only for normal moves, special moves don't roll ailments)
                if player_hit:
                    ailment_name = player_move_data.get('ailment', '')
                    if ailment_name:
                        ailment_chance = player_move_data.get('ailment_chance', 0)
                        should_apply = False
                        if ailment_chance == 0 and player_move_data.get('damage_class') == 'status':
                            should_apply = True
                        elif ailment_chance > 0:
                            should_apply = random.randint(1, 100) <= ailment_chance

                        if should_apply and not self.__has_ailment(e_ailment, battle_state.rest_turns_enemy):
                            e_ailment.setAilment(ailment_name)
                            log_lines.append(f"🔥 {e_name} is now {self.__ailment_display(ailment_name)}!")

                    if player_move_data.get('moveType') == 'fire' and e_ailment.freeze:
                        e_ailment.freeze = False
                        log_lines.append(f"🔥 {e_name} was thawed by the fire!")

                    # Secondary stat change on damaging moves (e.g. Acid, Psychic)
                    if player_hit and player_damage > 0:
                        apply_secondary_stat_change(
                            player_move_data, p_stages, e_stages,
                            log_lines, p_name, e_name
                        )

        # =====================================================================
        # CHECK: Did enemy Pokemon faint?
        # =====================================================================
        if battle_state.enemy_pokemon.currentHP <= 0:
            log_lines.append(f"💀 {e_name} fainted!")

            battle_state.defeated_enemies.append(battle_state.enemy_pokemon.pokemonName)
            battle_state.enemy_current_index += 1

            # Clear leech seed on defeated enemy
            battle_state.leech_seed_enemy = False
            battle_state.rest_turns_enemy = 0
            battle_state.enemy_stat_stages.reset()

            if battle_state.enemy_current_index < len(battle_state.enemy_pokemon_data):
                next_enemy_data = battle_state.enemy_pokemon_data[battle_state.enemy_current_index]
                try:
                    next_enemy = self.__create_enemy_pokemon(next_enemy_data, battle_state.user_id)
                    battle_state.enemy_pokemon = next_enemy
                    battle_state.enemy_ailment = AilmentClass('trainer_enemy')
                    e_name_new = battle_state.enemy_pokemon.pokemonName.capitalize()
                    log_lines.append(f"⚡ {battle_state.enemy_name} sent out {e_name_new}!")
                except Exception as e:
                    log_lines.append(f"Error creating next enemy Pokemon: {str(e)}")

                battle_state.battle_log = ["\n".join(log_lines)]
                battle_state.turn_number += 1
                embed = self.__create_battle_embed(user, battle_state)
                view = self.__create_battle_move_buttons_with_items(battle_state)
                await interaction.message.edit(embed=embed, view=view)
                return
            else:
                battle_state.battle_log = ["\n".join(log_lines)]
                battle_state.player_pokemon.save()
                await self.__handle_gym_battle_victory(interaction, battle_state)
                del self.__battle_states[user_id]
                return

        # Check if player fainted from confusion/trap self-damage before enemy turn
        if battle_state.player_pokemon.currentHP <= 0:
            log_lines.append(f"💀 Your {p_name} fainted!")
            battle_state.player_pokemon.currentHP = 0
            battle_state.player_pokemon.save()

            # Clear leech seed on fainted player pokemon
            battle_state.leech_seed_player = False
            battle_state.rest_turns_player = 0
            battle_state.player_stat_stages.reset()

            next_pokemon, next_index = self.__get_next_party_pokemon(battle_state.player_party, battle_state.player_current_index)
            if next_pokemon:
                battle_state.player_current_index = next_index
                battle_state.player_pokemon = next_pokemon
                battle_state.player_ailment = AilmentClass(next_pokemon.trainerId)
                log_lines.append(f"⚡ You sent out {battle_state.player_pokemon.pokemonName.capitalize()}!")
                battle_state.battle_log = ["\n".join(log_lines)]
                battle_state.turn_number += 1
                embed = self.__create_battle_embed(user, battle_state)
                view = self.__create_battle_move_buttons_with_items(battle_state)
                await interaction.message.edit(embed=embed, view=view)
                return
            else:
                battle_state.battle_log = ["\n".join(log_lines)]
                await self.__handle_gym_battle_defeat(interaction, battle_state)
                del self.__battle_states[user_id]
                return

        # =====================================================================
        # ENEMY'S TURN - Check Rest sleep first
        # =====================================================================
        enemy_can_attack = True

        if battle_state.rest_turns_enemy > 0:
            battle_state.rest_turns_enemy -= 1
            if battle_state.rest_turns_enemy == 0:
                e_ailment.sleep = False
                e_ailment.turnCounter = 0
                log_lines.append(f"💤 {e_name} woke up from Rest!")
            else:
                log_lines.append(f"💤 {e_name} is sleeping from Rest!")
            enemy_can_attack = False

        elif e_ailment.sleep:
            if e_ailment.turnCounter >= random.randint(1, 7):
                e_ailment.sleep = False
                e_ailment.turnCounter = 0
                log_lines.append(f"💤 {e_name} woke up!")
            else:
                e_ailment.turnCounter += 1
                log_lines.append(f"💤 {e_name} is fast asleep!")
                enemy_can_attack = False

        elif e_ailment.freeze:
            if random.randint(1, 5) == 1:
                e_ailment.freeze = False
                log_lines.append(f"🧊 {e_name} thawed out!")
            else:
                log_lines.append(f"🧊 {e_name} is frozen solid!")
                enemy_can_attack = False

        elif e_ailment.paralysis:
            if random.randint(1, 4) == 1:
                log_lines.append(f"⚡ {e_name} is paralyzed and can't move!")
                enemy_can_attack = False

        elif e_ailment.confusion:
            if e_ailment.turnCounter >= random.randint(2, 5):
                e_ailment.confusion = False
                e_ailment.turnCounter = 0
                log_lines.append(f"💫 {e_name} snapped out of confusion!")
            else:
                e_ailment.turnCounter += 1
                if random.randint(1, 2) == 1:
                    e_stats = battle_state.enemy_pokemon.getPokeStats()
                    self_damage = int(((2 * battle_state.enemy_pokemon.currentLevel / 5 + 2) * 40 * (e_stats['attack'] / e_stats['defense']) / 50 + 2))
                    self_damage = max(1, self_damage)
                    battle_state.enemy_pokemon.currentHP = max(0, battle_state.enemy_pokemon.currentHP - self_damage)
                    log_lines.append(f"💫 {e_name} is confused and hurt itself for {self_damage} damage!")
                    enemy_can_attack = False

        elif e_ailment.trap:
            if e_ailment.turnCounter >= random.randint(2, 5):
                e_ailment.trap = False
                e_ailment.turnCounter = 0
                log_lines.append(f"🪢 {e_name} broke free!")
            else:
                e_ailment.turnCounter += 1
                e_stats = battle_state.enemy_pokemon.getPokeStats()
                trap_damage = max(1, e_stats['hp'] // 16)
                battle_state.enemy_pokemon.currentHP = max(0, battle_state.enemy_pokemon.currentHP - trap_damage)
                log_lines.append(f"🪢 {e_name} is trapped! Took {trap_damage} damage!")
                enemy_can_attack = False

        # =====================================================================
        # ENEMY ATTACKS (if able)
        # =====================================================================
        if enemy_can_attack:
            enemy_moves = [m for m in battle_state.enemy_pokemon.getMoves() if m and m.lower() != 'none']
            if enemy_moves:
                enemy_move_name = random.choice(enemy_moves)
                enemy_move_data = moves_config.get(enemy_move_name, {})
                enemy_special_fn = get_special_function(enemy_move_data)
                enemy_move_display = enemy_move_name.replace('-', ' ').title()

                e_stats = battle_state.enemy_pokemon.getPokeStats()
                e_max_hp = e_stats['hp']
                p_stats = battle_state.player_pokemon.getPokeStats()
                p_max_hp = p_stats['hp']

                enemy_burn_halve = e_ailment.burn

                if 'stat_change' in enemy_move_data and not enemy_special_fn:
                    move_hit = check_accuracy(enemy_move_data.get('accuracy', 100))
                    if move_hit:
                        log_lines.append(f"• {e_name} used {enemy_move_display}!")
                        apply_stat_change(
                            enemy_move_data, e_stages, p_stages,
                            log_lines, e_name, p_name
                        )
                    else:
                        log_lines.append(f"• {e_name} used {enemy_move_display} but it missed!")

                elif enemy_special_fn == 'haze':
                    handle_haze(p_stages, e_stages)
                    log_lines.append(f"• {e_name} used Haze! All stat changes were eliminated!")

                elif enemy_special_fn == 'rest':
                    heal_amount, new_hp = handle_rest(battle_state.enemy_pokemon.currentHP, e_max_hp)
                    battle_state.enemy_pokemon.currentHP = new_hp
                    battle_state.rest_turns_enemy = 2
                    e_ailment.resetAilments()
                    e_ailment.sleep = True
                    log_lines.append(f"• {e_name} used Rest! Recovered {heal_amount} HP and fell asleep! 💤")

                elif enemy_special_fn == 'recover':
                    actual_heal, new_hp = handle_recover(battle_state.enemy_pokemon.currentHP, e_max_hp)
                    battle_state.enemy_pokemon.currentHP = new_hp
                    log_lines.append(f"• {e_name} used Recover! Restored {actual_heal} HP! 💚")

                elif enemy_special_fn == 'night_shade':
                    if check_accuracy(enemy_move_data.get('accuracy', 100)):
                        ns_damage = calculate_night_shade_damage(battle_state.enemy_pokemon.currentLevel)
                        battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - ns_damage)
                        log_lines.append(f"• {e_name} used Night Shade! Dealt {ns_damage} damage!")
                    else:
                        log_lines.append(f"• {e_name} used Night Shade but it missed!")

                elif enemy_special_fn == 'leech_seed':
                    if check_accuracy(enemy_move_data.get('accuracy', 100)):
                        if not battle_state.leech_seed_player:
                            battle_state.leech_seed_player = True
                            log_lines.append(f"• {e_name} used Leech Seed! Your Pokemon was seeded! 🌱")
                        else:
                            log_lines.append(f"• {e_name} used Leech Seed but your Pokemon is already seeded!")
                    else:
                        log_lines.append(f"• {e_name} used Leech Seed but it missed!")

                elif enemy_special_fn == 'dream_eater':
                    if p_ailment.sleep or battle_state.rest_turns_player > 0:
                        enemy_damage, enemy_hit = calculate_battle_damage(
                            battle_state.enemy_pokemon, battle_state.player_pokemon,
                            enemy_move_name, moves_config, type_effectiveness,
                            e_stages, p_stages
                        )
                        if enemy_burn_halve and enemy_move_data.get('damage_class') == 'physical' and enemy_damage > 0:
                            enemy_damage = max(1, enemy_damage // 2)
                        if enemy_hit and enemy_damage > 0:
                            battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - enemy_damage)
                            drain_heal = calculate_drain_heal(enemy_damage)
                            battle_state.enemy_pokemon.currentHP = min(e_max_hp, battle_state.enemy_pokemon.currentHP + drain_heal)
                            log_lines.append(f"• {e_name} used Dream Eater! Dealt {enemy_damage} damage and drained {drain_heal} HP! 💜")
                        elif enemy_hit:
                            log_lines.append(f"• {e_name} used Dream Eater but dealt no damage!")
                        else:
                            log_lines.append(f"• {e_name} used Dream Eater but it missed!")
                    else:
                        log_lines.append(f"• {e_name} used Dream Eater but it failed! Target is not asleep.")

                elif enemy_special_fn == 'drain':
                    enemy_damage, enemy_hit = calculate_battle_damage(
                        battle_state.enemy_pokemon, battle_state.player_pokemon,
                        enemy_move_name, moves_config, type_effectiveness,
                        e_stages, p_stages
                    )
                    if enemy_burn_halve and enemy_move_data.get('damage_class') == 'physical' and enemy_damage > 0:
                        enemy_damage = max(1, enemy_damage // 2)
                    if enemy_hit and enemy_damage > 0:
                        battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - enemy_damage)
                        drain_heal = calculate_drain_heal(enemy_damage)
                        battle_state.enemy_pokemon.currentHP = min(e_max_hp, battle_state.enemy_pokemon.currentHP + drain_heal)
                        log_lines.append(f"• {e_name} used {enemy_move_display}! Dealt {enemy_damage} damage and drained {drain_heal} HP! 💚")
                    elif enemy_hit:
                        log_lines.append(f"• {e_name} used {enemy_move_display}!")
                    else:
                        log_lines.append(f"• {e_name} used {enemy_move_display} but it missed!")

                else:
                    # --- NORMAL ENEMY ATTACK ---
                    enemy_damage, enemy_hit = calculate_battle_damage(
                        battle_state.enemy_pokemon, battle_state.player_pokemon,
                        enemy_move_name, moves_config, type_effectiveness,
                        e_stages, p_stages
                    )

                    if enemy_burn_halve and enemy_move_data.get('damage_class') == 'physical' and enemy_damage > 0:
                        enemy_damage = max(1, enemy_damage // 2)

                    if enemy_hit and enemy_damage > 0:
                        battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - enemy_damage)
                        log_lines.append(f"• {e_name} used {enemy_move_display}! Dealt {enemy_damage} damage!")
                    elif enemy_hit and (enemy_move_data.get('power') is None or enemy_move_data.get('power', 0) == 0):
                        log_lines.append(f"• {e_name} used {enemy_move_display}!")
                    else:
                        log_lines.append(f"• {e_name} used {enemy_move_display} but it missed!")
                        enemy_hit = False

                    # Roll ailment on player from enemy's move
                    if enemy_hit:
                        ailment_name = enemy_move_data.get('ailment', '')
                        if ailment_name:
                            ailment_chance = enemy_move_data.get('ailment_chance', 0)
                            should_apply = False
                            if ailment_chance == 0 and enemy_move_data.get('damage_class') == 'status':
                                should_apply = True
                            elif ailment_chance > 0:
                                should_apply = random.randint(1, 100) <= ailment_chance

                            if should_apply and not self.__has_ailment(p_ailment, battle_state.rest_turns_player):
                                p_ailment.setAilment(ailment_name)
                                log_lines.append(f"🔥 {p_name} is now {self.__ailment_display(ailment_name)}!")

                        if enemy_move_data.get('moveType') == 'fire' and p_ailment.freeze:
                            p_ailment.freeze = False
                            log_lines.append(f"🔥 {p_name} was thawed by the fire!")

                        # Secondary stat change on damaging moves
                        if enemy_hit and enemy_damage > 0:
                            apply_secondary_stat_change(
                                enemy_move_data, e_stages, p_stages,
                                log_lines, e_name, p_name
                            )

        # =====================================================================
        # CHECK: Did player Pokemon faint from enemy attack?
        # =====================================================================
        if battle_state.player_pokemon.currentHP <= 0:
            log_lines.append(f"💀 Your {p_name} fainted!")
            battle_state.player_pokemon.currentHP = 0
            battle_state.player_pokemon.save()

            battle_state.leech_seed_player = False
            battle_state.rest_turns_player = 0
            battle_state.player_stat_stages.reset()

            next_pokemon, next_index = self.__get_next_party_pokemon(battle_state.player_party, battle_state.player_current_index)
            if next_pokemon:
                battle_state.player_current_index = next_index
                battle_state.player_pokemon = next_pokemon
                # Reset PLAYER ailments for new Pokemon
                battle_state.player_ailment = AilmentClass(next_pokemon.trainerId)
                log_lines.append(f"⚡ You sent out {battle_state.player_pokemon.pokemonName.capitalize()}!")
                battle_state.battle_log = ["\n".join(log_lines)]
                battle_state.turn_number += 1
                embed = self.__create_battle_embed(user, battle_state)
                view = self.__create_battle_move_buttons_with_items(battle_state)
                await interaction.message.edit(embed=embed, view=view)
                return
            else:
                battle_state.battle_log = ["\n".join(log_lines)]
                await self.__handle_gym_battle_defeat(interaction, battle_state)
                del self.__battle_states[user_id]
                return

        # =====================================================================
        # END OF TURN - Burn/Poison damage
        # =====================================================================
        if p_ailment.burn and battle_state.player_pokemon.currentHP > 0:
            p_stats = battle_state.player_pokemon.getPokeStats()
            burn_damage = max(1, p_stats['hp'] // 16)
            battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - burn_damage)
            log_lines.append(f"🔥 {p_name} is hurt by its burn! (-{burn_damage})")

        if p_ailment.poison and battle_state.player_pokemon.currentHP > 0:
            p_stats = battle_state.player_pokemon.getPokeStats()
            poison_damage = max(1, p_stats['hp'] // 16)
            battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - poison_damage)
            log_lines.append(f"☠️ {p_name} is hurt by poison! (-{poison_damage})")

        if e_ailment.burn and battle_state.enemy_pokemon.currentHP > 0:
            e_stats = battle_state.enemy_pokemon.getPokeStats()
            burn_damage = max(1, e_stats['hp'] // 16)
            battle_state.enemy_pokemon.currentHP = max(0, battle_state.enemy_pokemon.currentHP - burn_damage)
            log_lines.append(f"🔥 {e_name} is hurt by its burn! (-{burn_damage})")

        if e_ailment.poison and battle_state.enemy_pokemon.currentHP > 0:
            e_stats = battle_state.enemy_pokemon.getPokeStats()
            poison_damage = max(1, e_stats['hp'] // 16)
            battle_state.enemy_pokemon.currentHP = max(0, battle_state.enemy_pokemon.currentHP - poison_damage)
            log_lines.append(f"☠️ {e_name} is hurt by poison! (-{poison_damage})")

        # =====================================================================
        # END OF TURN - Leech Seed drain
        # =====================================================================
        if battle_state.leech_seed_player and battle_state.player_pokemon.currentHP > 0:
            p_stats = battle_state.player_pokemon.getPokeStats()
            seed_damage = calculate_leech_seed_damage(p_stats['hp'])
            battle_state.player_pokemon.currentHP = max(0, battle_state.player_pokemon.currentHP - seed_damage)
            e_stats = battle_state.enemy_pokemon.getPokeStats()
            battle_state.enemy_pokemon.currentHP = min(e_stats['hp'], battle_state.enemy_pokemon.currentHP + seed_damage)
            log_lines.append(f"🌱 {p_name} had its energy drained by Leech Seed! (-{seed_damage} HP)")

        if battle_state.leech_seed_enemy and battle_state.enemy_pokemon.currentHP > 0:
            e_stats = battle_state.enemy_pokemon.getPokeStats()
            seed_damage = calculate_leech_seed_damage(e_stats['hp'])
            battle_state.enemy_pokemon.currentHP = max(0, battle_state.enemy_pokemon.currentHP - seed_damage)
            p_stats = battle_state.player_pokemon.getPokeStats()
            battle_state.player_pokemon.currentHP = min(p_stats['hp'], battle_state.player_pokemon.currentHP + seed_damage)
            log_lines.append(f"🌱 {e_name} had its energy drained by Leech Seed! (-{seed_damage} HP)")

        # =====================================================================
        # POST-TURN FAINT CHECKS
        # =====================================================================
        if battle_state.enemy_pokemon.currentHP <= 0:
            log_lines.append(f"💀 {e_name} fainted from residual damage!")
            battle_state.defeated_enemies.append(battle_state.enemy_pokemon.pokemonName)
            battle_state.enemy_current_index += 1
            battle_state.leech_seed_enemy = False
            battle_state.rest_turns_enemy = 0
            battle_state.enemy_stat_stages.reset()
            

            if battle_state.enemy_current_index < len(battle_state.enemy_pokemon_data):
                next_enemy_data = battle_state.enemy_pokemon_data[battle_state.enemy_current_index]
                try:
                    next_enemy = self.__create_enemy_pokemon(next_enemy_data, battle_state.user_id)
                    battle_state.enemy_pokemon = next_enemy
                    battle_state.enemy_ailment = AilmentClass('trainer_enemy')
                    log_lines.append(f"⚡ {battle_state.enemy_name} sent out {next_enemy.pokemonName.capitalize()}!")
                except Exception as e:
                    log_lines.append(f"Error: {str(e)}")
                battle_state.battle_log = ["\n".join(log_lines)]
                battle_state.turn_number += 1
                embed = self.__create_battle_embed(user, battle_state)
                view = self.__create_battle_move_buttons_with_items(battle_state)
                await interaction.message.edit(embed=embed, view=view)
                return
            else:
                battle_state.battle_log = ["\n".join(log_lines)]
                battle_state.player_pokemon.save()
                await self.__handle_gym_battle_victory(interaction, battle_state)
                del self.__battle_states[user_id]
                return

        if battle_state.player_pokemon.currentHP <= 0:
            log_lines.append(f"💀 Your {p_name} fainted from residual damage!")
            battle_state.player_pokemon.currentHP = 0
            battle_state.player_pokemon.save()
            battle_state.leech_seed_player = False
            battle_state.rest_turns_player = 0
            battle_state.player_stat_stages.reset()

            next_pokemon, next_index = self.__get_next_party_pokemon(battle_state.player_party, battle_state.player_current_index)
            if next_pokemon:
                battle_state.player_current_index = next_index
                battle_state.player_pokemon = next_pokemon
                battle_state.player_ailment = AilmentClass(next_pokemon.trainerId)
                log_lines.append(f"⚡ You sent out {battle_state.player_pokemon.pokemonName.capitalize()}!")
                battle_state.battle_log = ["\n".join(log_lines)]
                battle_state.turn_number += 1
                embed = self.__create_battle_embed(user, battle_state)
                view = self.__create_battle_move_buttons_with_items(battle_state)
                await interaction.message.edit(embed=embed, view=view)
                return
            else:
                battle_state.battle_log = ["\n".join(log_lines)]
                await self.__handle_gym_battle_defeat(interaction, battle_state)
                del self.__battle_states[user_id]
                return

        # Battle continues
        battle_state.battle_log = ["\n".join(log_lines)]
        battle_state.turn_number += 1

        embed = self.__create_battle_embed(user, battle_state)
        view = self.__create_battle_move_buttons_with_items(battle_state)
        await interaction.message.edit(embed=embed, view=view)


    def __get_ailment_emoji(self, ailment_obj, rest_turns=0) -> str:
        """Get emoji for the active ailment, or empty string if none"""
        if rest_turns > 0:
            return ' 💤'
        if ailment_obj is None:
            return ''
        if ailment_obj.sleep:
            return ' 💤'
        if ailment_obj.burn:
            return ' 🔥'
        if ailment_obj.poison:
            return ' ☠️'
        if ailment_obj.freeze:
            return ' 🧊'
        if ailment_obj.paralysis:
            return ' ⚡'
        if ailment_obj.confusion:
            return ' 💫'
        if ailment_obj.trap:
            return ' 🪢'
        return ''

    def __has_ailment(self, ailment_obj, rest_turns=0) -> bool:
        """Check if an ailment object has any active ailment (or is in Rest sleep)"""
        if rest_turns > 0:
            return True
        return (ailment_obj.sleep or ailment_obj.poison or ailment_obj.burn
                or ailment_obj.freeze or ailment_obj.paralysis
                or ailment_obj.trap or ailment_obj.confusion)


    def __ailment_display(self, ailment_name: str) -> str:
        """Get a display-friendly ailment name with emoji"""
        displays = {
            'sleep': '💤 asleep',
            'poison': '☠️ poisoned',
            'burn': '🔥 burned',
            'freeze': '🧊 frozen',
            'paralysis': '⚡ paralyzed',
            'trap': '🪢 trapped',
            'confusion': '💫 confused',
            'leech_seed': '🌱 seeded',
        }
        return displays.get(ailment_name, ailment_name)

    async def __handle_gym_battle_victory(self, interaction: discord.Interaction, battle_state: BattleState):
        """Handle when player wins a gym battle - shows all Pokemon used with navigation"""
        trainer_model = battle_state.trainer_model
        battle_manager = battle_state.battle_manager
        
        player_max_hp = battle_state.player_pokemon.getPokeStats()['hp']
        player_level = battle_state.player_pokemon.currentLevel
        
        # Award rewards
        if hasattr(trainer_model, 'badge'):  # It's a gym leader
            # It's a gym leader
            battle_manager.gymLeaderVictory(trainer_model)
            
            # Send badge achievement
            if interaction.guild:
                await self.send_achievement(
                    guild=interaction.guild,
                    user=user,
                    achievement_type="badge",
                    badge_name=trainer_model.badge,
                    gym_name=trainer_model.name
                )
            
            embed = discord.Embed(
                title="🏆 VICTORY!",
                description=f"You defeated Gym Leader {trainer_model.name}!",
                color=discord.Color.gold()
            )
            
            # Show all defeated enemy Pokemon
            enemy_summary = []
            enemy_summary.append(f"**Defeated {len(battle_state.defeated_enemies)} Pokemon:**")
            for i, poke_name in enumerate(battle_state.defeated_enemies, 1):
                enemy_summary.append(f"{i}. {poke_name.capitalize()} ❌")
            
            embed.add_field(
                name="🎯 Enemy Team",
                value="\n".join(enemy_summary),
                inline=True
            )
            
            # Show player's current Pokemon
            player_summary = []
            player_summary.append(f"**Your {battle_state.player_pokemon.pokemonName.capitalize()}** (Lv.{player_level})")
            player_summary.append(f"HP: {battle_state.player_pokemon.currentHP}/{player_max_hp}")
            
            embed.add_field(
                name="💚 Your Pokemon",
                value="\n".join(player_summary),
                inline=True
            )
            
            # Battle log
            if battle_state.battle_log:
                log_text = "\n".join(battle_state.battle_log)
                embed.add_field(
                    name="⚔️ Final Turn",
                    value=log_text[:1024],
                    inline=False
                )
            
            embed.add_field(
                name="🎖️ Badge Earned",
                value=trainer_model.badge,
                inline=True
            )
            
            embed.add_field(
                name="💰 Prize Money",
                value=f"${trainer_model.money}",
                inline=True
            )
            
        else:  # It's a trainer (wild or gym trainer, not gym leader)
            battle_manager.battleVictory(trainer_model)
            
            embed = discord.Embed(
                title="🎉 VICTORY!",
                description=f"You defeated {trainer_model.name}!",
                color=discord.Color.green()
            )
            
            # Show all defeated enemy Pokemon
            enemy_summary = []
            if len(battle_state.defeated_enemies) > 1:
                enemy_summary.append(f"**Defeated {len(battle_state.defeated_enemies)} Pokemon:**")
                for i, poke_name in enumerate(battle_state.defeated_enemies, 1):
                    enemy_summary.append(f"{i}. {poke_name.capitalize()} ❌")
            else:
                enemy_summary.append(f"**Enemy {battle_state.defeated_enemies[0].capitalize()}** ❌")
            
            embed.add_field(
                name="🎯 Enemy Team",
                value="\n".join(enemy_summary),
                inline=True
            )
            
            # Show player's current Pokemon
            player_summary = []
            from .functions import get_pokemon_display_name
            player_display = get_pokemon_display_name(battle_state.player_pokemon)
            player_summary.append(f"**{player_display}** (Lv.{player_level})")
            player_summary.append(f"HP: {battle_state.player_pokemon.currentHP}/{player_max_hp}")
            
            embed.add_field(
                name="💚 Your Pokemon",
                value="\n".join(player_summary),
                inline=True
            )
            
            # Battle log
            if battle_state.battle_log:
                log_text = "\n".join(battle_state.battle_log)
                embed.add_field(
                    name="⚔️ Final Turn",
                    value=log_text[:1024],
                    inline=False
                )
            
            embed.add_field(
                name="💰 Reward",
                value=f"${trainer_model.money}",
                inline=True
            )
        
        # ADD NAVIGATION BUTTONS
        view = self.__create_post_battle_buttons(battle_state.user_id)
        
        # Send as NEW message, not edit
        new_message = await interaction.followup.send(embed=embed, view=view, ephemeral=False)
        
        # Delete the old battle message
        try:
            await interaction.message.delete()
        except:
            pass
        
        user = interaction.user
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), 
            new_message.channel.id, 
            new_message.id, 
            location, 
            trainer.getActivePokemon(), 
            None, 
            ''
        )

        # Check for more trainers and send as followup (not in embed)
        remaining = battle_manager.getRemainingTrainerCount()
        if remaining > 0:
            next_up = battle_manager.getNextTrainer()
            await interaction.followup.send(
                f"**Trainers Remaining:** {remaining}\n"
                f"**Next Opponent:** {next_up.name if next_up else 'Unknown'}",
                ephemeral=True
            )
        else:
            # Check if player just defeated the Champion (elite-4-5)
            if hasattr(trainer_model, 'enemy_uuid') and trainer_model.enemy_uuid == "elite-4-5":
                finale_embed = discord.Embed(
                    title="🏆 Congratulations, Champion!",
                    description="You have defeated the Elite Four and become the Pokémon Champion!\n\n"
                                "**You have unlocked the finale!**\n"
                                "Please type the command `,finale` and read the instructions to continue.",
                    color=discord.Color.gold()
                )
                await interaction.followup.send(embed=finale_embed)

                # Send Elite Four achievement
                if interaction.guild:
                    await self.send_achievement(
                        guild=interaction.guild,
                        user=user,
                        achievement_type="elite_four"
                    )

            # Check if gym leader is available (only for gym battles, not wild trainers)
            if not hasattr(battle_state, 'is_wild_trainer') or not battle_state.is_wild_trainer:
                gym_leader = battle_manager.getGymLeader()
                if gym_leader and not hasattr(trainer_model, 'badge'):
                    await interaction.followup.send(
                        f"All gym trainers defeated! You can now challenge Gym Leader {gym_leader.name}!",
                        ephemeral=True
                    )

    async def __handle_gym_battle_defeat(self, interaction: discord.Interaction, battle_state: BattleState):
        """Handle when player loses a gym battle - shows team info with navigation"""
        
        # GET user from interaction - THIS WAS MISSING!
        user = interaction.user
        
        player_max_hp = battle_state.player_pokemon.getPokeStats()['hp']
        enemy_max_hp = battle_state.enemy_pokemon.getPokeStats()['hp']
        player_level = battle_state.player_pokemon.currentLevel
        enemy_level = battle_state.enemy_pokemon.currentLevel
        
        embed = discord.Embed(
            title="💀 DEFEAT",
            description=f"You were defeated by {battle_state.enemy_name}...",
            color=discord.Color.dark_red()
        )
        
        # Show player's fainted Pokemon count
        fainted_count = battle_state.player_current_index + 1
        total_party = len(battle_state.player_party)
        
        player_summary = []
        player_summary.append(f"**Your Team:** {fainted_count}/{total_party} fainted")
        player_summary.append(f"Last: {battle_state.player_pokemon.pokemonName.capitalize()} (Lv.{player_level})")
        player_summary.append(f"HP: 0/{player_max_hp} ❌")
        
        embed.add_field(
            name="💚 Your Team",
            value="\n".join(player_summary),
            inline=True
        )
        
        # Show enemy's current Pokemon
        enemy_summary = []
        enemy_summary.append(f"**{battle_state.enemy_pokemon.pokemonName.capitalize()}** (Lv.{enemy_level})")
        enemy_summary.append(f"HP: {battle_state.enemy_pokemon.currentHP}/{enemy_max_hp}")
        if len(battle_state.defeated_enemies) > 0:
            enemy_summary.append(f"\nDefeated: {len(battle_state.defeated_enemies)}/{len(battle_state.enemy_pokemon_data)}")
        
        embed.add_field(
            name="🎯 Enemy Team",
            value="\n".join(enemy_summary),
            inline=True
        )
        
        # Battle log
        if battle_state.battle_log:
            log_text = "\n".join(battle_state.battle_log)
            embed.add_field(
                name="⚔️ Final Turn",
                value=log_text[:1024],
                inline=False
            )
        
        # ADD NAVIGATION BUTTONS - use battle_state.user_id instead of str(user.id)
        view = self.__create_post_battle_buttons(battle_state.user_id)
        
        await interaction.message.edit(embed=embed, view=view)

    def __load_quests_data(self):
        """Load quests.json file"""
        if self.__quests_data is None:
            self.__quests_data = load_json_config('quests.json')
        return self.__quests_data

    def __load_gyms_data(self):
        """Load gyms.json file"""
        if self.__gyms_data is None:
            self.__gyms_data = load_json_config('gyms.json')
        return self.__gyms_data

    def __load_locations_data(self):
        """Load locations.json file"""
        if self.__locations_data is None:
            self.__locations_data = load_json_config('locations.json')
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

        from services.questclass import quests as QuestsClass
        quest_obj = QuestsClass(user_id)
        
        # Use the existing prerequsitesValid method which handles the name mapping correctly
        return quest_obj.prerequsitesValid(pre_requisites)

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
    

    
    @commands.command(name='nickname')
    async def trainer_nickname(self, ctx):
        """Set or clear nicknames for your Pokemon"""
        user = ctx.author
        trainer = self._get_trainer(str(user.id))
        
        # Get party Pokemon
        party = trainer.getPokemon(party=True)
        if not party:
            await ctx.send("You don't have any Pokemon in your party!")
            return
        
        # Load each Pokemon
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
        
        # Create dropdown with party Pokemon
        options = []
        for i, poke in enumerate(party):
            from .functions import get_pokemon_display_name
            display_name = get_pokemon_display_name(poke)
            current_nickname = f" (nicknamed)" if poke.nickName else ""
            label = f"{display_name} - Lv.{poke.currentLevel}{current_nickname}"
            options.append(discord.SelectOption(
                label=label[:100],  # Discord limit
                value=str(poke.trainerId),
                description=f"Species: {poke.pokemonName.capitalize()}"
            ))
        
        select = Select(
            placeholder="Choose a Pokemon to nickname...",
            options=options,
            custom_id="nickname_select"
        )
        
        view = View(timeout=180)
        
        async def select_callback(interaction: discord.Interaction):
            if interaction.user.id != user.id:
                await interaction.response.send_message("This isn't your Pokemon!", ephemeral=True)
                return
            
            selected_trainer_id = int(select.values[0])
            
            # Find the selected Pokemon
            selected_poke = None
            for poke in party:
                if poke.trainerId == selected_trainer_id:
                    selected_poke = poke
                    break
            
            if not selected_poke:
                await interaction.response.send_message("Pokemon not found!", ephemeral=True)
                return
            
            # Create modal for nickname input
            await interaction.response.send_modal(NicknameModal(selected_poke))
        
        select.callback = select_callback
        view.add_item(select)
        
        # Add cancel button
        cancel_btn = Button(style=ButtonStyle.secondary, label="❌ Cancel", custom_id="nickname_cancel")
        async def cancel_callback(interaction: discord.Interaction):
            if interaction.user.id != user.id:
                await interaction.response.send_message("This isn't for you!", ephemeral=True)
                return
            await interaction.message.delete()
        
        cancel_btn.callback = cancel_callback
        view.add_item(cancel_btn)
        
        embed = discord.Embed(
            title="🏷️ Pokemon Nickname Manager",
            description="Select a Pokemon from your party to set or change its nickname.",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed, view=view)


    
    @commands.command(name="play", aliases=['p','m'])
    async def play(self, ctx: commands.Context):
        """Show the map with navigation buttons"""
        user = ctx.author
        
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        # Get available actions at this location
        location_obj = LocationClass(str(user.id))
        methods = location_obj.getMethods()
        quest_buttons = self.__get_available_quests(str(user.id), location.name)
        gym_button = self.__get_gym_button(str(user.id), location.locationId)
        
        wild_trainers_button = self.__get_wild_trainers_button(str(user.id), location.locationId)
        
        from .constant import LOCATION_DISPLAY_NAMES
        location_name = LOCATION_DISPLAY_NAMES.get(location.name, location.name.replace('-', ' ').title())
        
        # Create embed
        embed = discord.Embed(
            title=f"{location_name}",
            description=f"You are at {location_name}.",
            color=discord.Color.blue()
        )

        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        
        # Load location sprite - FIX APPLIED HERE
        if location.spritePath:
            try:
                # Convert to full file system path
                full_sprite_path = get_sprite_path(location.spritePath)
                sprite_file = discord.File(full_sprite_path, filename=f"{location.name}.png")

                temp_message = await self.sendToLoggingChannel(f'{user.display_name} viewing map', sprite_file)
                if temp_message and temp_message.attachments:
                    attachment = temp_message.attachments[0]
                    embed.set_image(url=attachment.url)
            except Exception as e:
                print(f"Error loading location sprite from file: {e}")
                try:
                    sprite_url = f"https://pokesprites.joshkohut.com/sprites/locations/{location.name}.png"
                    embed.set_image(url=sprite_url)
                except:
                    pass
        
        # Create view with direction buttons
        view = View()
        
        # ROW 0: North/South buttons
        if location.north:
            north_name = LOCATION_DISPLAY_NAMES.get(location.north, location.north)
            north_btn = Button(style=ButtonStyle.gray, emoji='⬆️', label=f"{north_name[:15]}", custom_id='dir_north', row=0)
            north_btn.callback = self.on_direction_click
            view.add_item(north_btn)
        else:
            north_btn = Button(style=ButtonStyle.gray, emoji='⬆️', label="---", custom_id='dir_north_disabled', disabled=True, row=0)
            view.add_item(north_btn)
        
        if location.south:
            south_name = LOCATION_DISPLAY_NAMES.get(location.south, location.south)
            south_btn = Button(style=ButtonStyle.gray, emoji='⬇️', label=f"{south_name[:15]}", custom_id='dir_south', row=0)
            south_btn.callback = self.on_direction_click
            view.add_item(south_btn)
        else:
            south_btn = Button(style=ButtonStyle.gray, emoji='⬇️', label="---", custom_id='dir_south_disabled', disabled=True, row=0)
            view.add_item(south_btn)
        
        # ROW 1: East/West buttons
        if location.west:
            west_name = LOCATION_DISPLAY_NAMES.get(location.west, location.west)
            west_btn = Button(style=ButtonStyle.gray, emoji='⬅️', label=f"{west_name[:15]}", custom_id='dir_west', row=1)
            west_btn.callback = self.on_direction_click
            view.add_item(west_btn)
        else:
            west_btn = Button(style=ButtonStyle.gray, emoji='⬅️', label="---", custom_id='dir_west_disabled', disabled=True, row=1)
            view.add_item(west_btn)
        
        if location.east:
            east_name = LOCATION_DISPLAY_NAMES.get(location.east, location.east)
            east_btn = Button(style=ButtonStyle.gray, emoji='➡️', label=f"{east_name[:15]}", custom_id='dir_east', row=1)
            east_btn.callback = self.on_direction_click
            view.add_item(east_btn)
        else:
            east_btn = Button(style=ButtonStyle.gray, emoji='➡️', label="---", custom_id='dir_east_disabled', disabled=True, row=1)
            view.add_item(east_btn)
        
        # AUX button (if exists)
        if hasattr(location, 'aux') and location.aux:
            aux_name = LOCATION_DISPLAY_NAMES.get(location.aux, location.aux)
            aux_btn = Button(style=ButtonStyle.gray, emoji='🔀', label=f"{aux_name[:15]}", custom_id='dir_aux', row=1)
            aux_btn.callback = self.on_direction_click
            view.add_item(aux_btn)

        # ROW 2: Action buttons (Encounters, Quests, Gym, Wild Trainers)
        if len(methods) > 0:
            enc_btn = Button(style=ButtonStyle.green, label="⚔️ Encounters", custom_id='nav_encounters', row=2)
            enc_btn.callback = self.on_nav_encounters_click
            view.add_item(enc_btn)
        
        if len(quest_buttons) > 0:
            quest_btn = Button(style=ButtonStyle.blurple, label="📜 Quests", custom_id='nav_quests', row=2)
            quest_btn.callback = self.on_nav_quests_click
            view.add_item(quest_btn)
        
        if gym_button and not gym_button.disabled:
            gym_btn = Button(style=ButtonStyle.red, label="🏛️ Gym", custom_id='nav_gym', row=2)
            gym_btn.callback = self.on_gym_click
            view.add_item(gym_btn)
        
        # ADD WILD TRAINERS BUTTON HERE ON ROW 2
        if wild_trainers_button:
            view.add_item(wild_trainers_button)
        
        # ROW 3: Utility buttons
        bag_btn = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_bag', row=3)
        bag_btn.callback = self.on_nav_bag_click
        view.add_item(bag_btn)
        
        # Add Mart button if location has a Pokemart
        if self.__has_pokemart(location.locationId):
            mart_btn = Button(style=ButtonStyle.blurple, label="🏪 Mart", custom_id='nav_mart', row=3)
            mart_btn.callback = self.on_nav_mart_click
            view.add_item(mart_btn)

        if location.pokecenter:
            heal_btn = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal', row=3)
            heal_btn.callback = self.on_nav_heal_click
            view.add_item(heal_btn)
        
        message = await ctx.send(embed=embed, view=view)
        
        # Initialize action state
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, location, trainer.getActivePokemon(), None, ''
        )

    async def get_encounters(self, interaction: Interaction):
        user = interaction.user
        trainer = self._get_trainer(str(user.id))
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

        # Extract quest name from custom_id (format: 'quest_QuestName')
        quest_name = interaction.data['custom_id'].replace('quest_', '')

        # Get location and pre-requisites
        trainer = self._get_trainer(str(user.id))
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

        # Special handling for Porygon - show confirmation prompt
        if quest_name == 'Porygon':
            await self.__show_porygon_confirmation(interaction, user)
            return

        # Execute the quest
        from services.questclass import quests as QuestsClass
        quest_obj = QuestsClass(str(user.id))
        result = quest_obj.questHandler(quest_name)

        # Check if an easter egg was found and send achievement
        if hasattr(quest_obj, 'found_easter_egg') and quest_obj.found_easter_egg:
            egg_id, egg_name = quest_obj.found_easter_egg
            if interaction.guild:
                await self.send_easter_egg_achievement(
                    str(user.id),
                    interaction.guild,
                    egg_id
                )

        # Ensure message is never empty to avoid Discord 400 error
        quest_message = quest_obj.message if quest_obj.message else f'Quest "{quest_name}" completed.'

        # new code
        # Check if this quest triggers a teleport (e.g., Mysterious Cave)
        if result and isinstance(result, dict) and result.get('teleport'):
            # Send the quest message as ephemeral first
            await interaction.response.send_message(quest_message, ephemeral=True)
            # Then refresh the main map message to show the new location
            await self.on_nav_map_click(interaction, already_deferred=True)
            return

        # Send response with embed if available
        if result and isinstance(result, dict) and 'embed' in result:
            await interaction.response.send_message(quest_message, embed=result['embed'], ephemeral=True)
        else:
            await interaction.response.send_message(quest_message, ephemeral=True)

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
                # Set proper callbacks based on button type
                if button.custom_id == interaction.data['custom_id']:
                    new_button.callback = self.on_quest_click
                elif button.custom_id == 'quest_back_to_map':
                    new_button.callback = self.on_quest_back_to_map_click
                elif button.custom_id.startswith('quest_'):
                    new_button.callback = self.on_quest_click
                else:
                    new_button.callback = self.on_action_encounter
                view.add_item(new_button)

        await interaction.message.edit(view=view)


    async def __show_porygon_confirmation(self, interaction: discord.Interaction, user):
        """Show confirmation prompt for buying Porygon"""
        from services.inventoryclass import inventory as InventoryClass
        from services.uniqueencounters import uniqueEncounters as uEnc
        
        PORYGON_COST = 100000
        
        # Check if already purchased
        unique_enc = uEnc(str(user.id))
        if unique_enc.porygon:
            await interaction.response.send_message("You already purchased Porygon!", ephemeral=True)
            return
        
        # Get trainer's money
        inventory = InventoryClass(str(user.id))
        has_enough = inventory.money >= PORYGON_COST
        
        embed = discord.Embed(
            title="🖥️ Porygon For Sale!",
            description="A scientist approaches you with a Pokéball containing a digital Pokémon.",
            color=discord.Color.blue() if has_enough else discord.Color.red()
        )
        embed.add_field(name="Price", value=f"¥{PORYGON_COST:,}", inline=True)
        embed.add_field(name="Your Money", value=f"¥{inventory.money:,}", inline=True)
        
        if not has_enough:
            embed.add_field(name="", value=f"❌ You need ¥{PORYGON_COST - inventory.money:,} more!", inline=False)
        else:
            embed.add_field(name="", value="Do you want to buy Porygon for ¥100,000?", inline=False)
        
        view = View()
        
        yes_btn = Button(style=ButtonStyle.green, label="Buy Porygon", custom_id='porygon_confirm_yes', disabled=not has_enough)
        yes_btn.callback = self.on_porygon_confirm
        view.add_item(yes_btn)
        
        no_btn = Button(style=ButtonStyle.gray, label="No Thanks", custom_id='porygon_confirm_no')
        no_btn.callback = self.on_porygon_decline
        view.add_item(no_btn)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def on_porygon_confirm(self, interaction: discord.Interaction):
        """Handle Porygon purchase confirmation"""
        user = interaction.user
        await interaction.response.defer()
        
        # Execute the quest
        from services.questclass import quests as QuestsClass
        quest_obj = QuestsClass(str(user.id))
        result = quest_obj.questHandler('Porygon')
        
        quest_message = quest_obj.message if quest_obj.message else 'Porygon quest completed.'
        
        # Disable the buttons after purchase
        view = View()
        disabled_btn = Button(style=ButtonStyle.green, label="Purchased!", custom_id='porygon_confirm_yes', disabled=True)
        disabled_btn.callback = self.on_porygon_confirm
        view.add_item(disabled_btn)
        
        if result and isinstance(result, dict) and 'embed' in result:
            await interaction.edit_original_response(content=quest_message, embed=result['embed'], view=view)
        else:
            await interaction.edit_original_response(content=quest_message, view=view)

    async def on_porygon_decline(self, interaction: discord.Interaction):
        """Handle Porygon purchase decline"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🖥️ Maybe Next Time",
            description="The scientist nods and walks away with the Pokéball.",
            color=discord.Color.light_gray()
        )
        
        view = View()
        disabled_btn = Button(style=ButtonStyle.gray, label="Declined", custom_id='porygon_confirm_no', disabled=True)
        disabled_btn.callback = self.on_porygon_decline
        view.add_item(disabled_btn)
        
        await interaction.edit_original_response(embed=embed, view=view)

    def __create_battle_move_buttons_with_items(self, battle_state) -> View:
        """
        Create move buttons plus Use Items button for battles.
        Works with both BattleState and WildBattleState.
        """
        view = View()
        
        # Determine which Pokemon to get moves from based on battle state type
        if hasattr(battle_state, 'player_pokemon'):
            player_pokemon = battle_state.player_pokemon
        else:
            # Shouldn't happen, but fallback
            return view
        
        moves = player_pokemon.getMoves()
        
        # Load move data to show power/type
        try:
            moves_config = load_json_config('moves.json')
        except:
            moves_config = {}
        
        # ROW 0: Move buttons (up to 4 moves)
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
                
                # Determine callback based on battle type
                if isinstance(battle_state, WildBattleState):
                    custom_id = f'wild_battle_move_{move_name}'
                    callback = self.on_wild_battle_move_click
                else:  # BattleState (gym/trainer)
                    custom_id = f'battle_move_{move_name}'
                    callback = self.on_battle_move_click
                
                button = Button(
                    style=ButtonStyle.primary,
                    label=label[:80],  # Discord label limit
                    custom_id=custom_id,
                    row=0
                )
                button.callback = callback
                view.add_item(button)
        
        # ROW 1: Action buttons (Use Items, and conditionally Run/Catch for wild battles)
        use_items_btn = Button(
            style=ButtonStyle.blurple,
            label="💊 Use Items",
            custom_id='battle_use_items',
            row=1
        )
        use_items_btn.callback = self.on_battle_use_items_click
        view.add_item(use_items_btn)
        
        # Add Run Away and Catch buttons ONLY for wild Pokemon battles
        if isinstance(battle_state, WildBattleState):
            run_button = Button(
                style=ButtonStyle.danger,
                label="🏃 Run Away",
                custom_id='wild_battle_run',
                row=1
            )
            run_button.callback = self.on_wild_battle_run_click
            view.add_item(run_button)
            
            catch_button = Button(
                style=ButtonStyle.success,
                label="Catch",
                custom_id='wild_battle_catch',
                row=1
            )
            catch_button.callback = self.on_wild_battle_catch_click
            view.add_item(catch_button)
        
        return view

    async def on_gym_battle_auto(self, interaction: discord.Interaction):
        """Handle AUTO battle with gym trainer - now supports multiple Pokemon"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        # Get player's full party
        player_party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in player_party:
            poke.load(pokemonId=poke.trainerId)
            if poke.currentHP > 0:
                alive_party.append(poke)
        
        if len(alive_party) == 0:
            await interaction.followup.send('All your party Pokemon have fainted! Heal at a Pokemon Center first.', ephemeral=True)
            return
        
        alive_party = self.__sort_party_active_first(alive_party, str(user.id))
        battle = BattleClass(str(user.id), location.locationId, enemyType="gym")
        next_trainer = battle.getNextTrainer()
        
        if not next_trainer:
            await interaction.followup.send('No trainer to battle.', ephemeral=True)
            return

        # Get ALL enemy Pokemon
        enemy_pokemon_list = next_trainer.pokemon
        
        # Battle tracking
        player_pokemon_index = 0
        enemy_pokemon_index = 0
        all_battle_logs = []
        defeated_enemies = []
        defeated_player = []
        exp_messages = []  # Track experience gains
        
        # Battle loop - continue until one side has no Pokemon left
        battle_result = None
        
        while player_pokemon_index < len(alive_party) and enemy_pokemon_index < len(enemy_pokemon_list):
            # Get current Pokemon
            player_pokemon = alive_party[player_pokemon_index]
            enemy_data = enemy_pokemon_list[enemy_pokemon_index]
            
            from services.pokedexclass import pokedex as PokedexClass

            # Create enemy Pokemon
            enemy_name = list(enemy_data.keys())[0]
            enemy_level = enemy_data[enemy_name]
            enemy_pokemon = PokemonClass(str(user.id), enemy_name)
            enemy_pokemon.create(enemy_level)
            enemy_pokemon.discordId = None
            
            PokedexClass(str(user.id), enemy_pokemon)

            # Fight this matchup
            enc = EncounterClass(player_pokemon, enemy_pokemon)
            result = enc.fight(battleType='auto')
            
            # Add this battle's logs
            if hasattr(enc, 'battle_log') and enc.battle_log:
                all_battle_logs.extend(enc.battle_log)
            
            # Capture experience message
            if enc.message:
                exp_messages.append(f"{player_pokemon.pokemonName.capitalize()}: {enc.message}")
            
            # Process result
            if result.get('result') == 'victory':
                # Player won this round - enemy Pokemon fainted
                defeated_enemies.append(enemy_name)
                enemy_pokemon_index += 1
                all_battle_logs.append(f"💀 Enemy {enemy_name.capitalize()} fainted!")
                
                if enemy_pokemon_index < len(enemy_pokemon_list):
                    next_enemy_name = list(enemy_pokemon_list[enemy_pokemon_index].keys())[0]
                    all_battle_logs.append(f"⚡ {next_trainer.name} sent out {next_enemy_name.capitalize()}!")
            else:
                # Player lost this round - player Pokemon fainted
                defeated_player.append(player_pokemon.pokemonName)
                player_pokemon_index += 1
                all_battle_logs.append(f"💀 Your {player_pokemon.pokemonName.capitalize()} fainted!")
                
                if player_pokemon_index < len(alive_party):
                    next_player = alive_party[player_pokemon_index]
                    all_battle_logs.append(f"⚡ You sent out {next_player.pokemonName.capitalize()}!")
        
        # Determine overall winner
        if enemy_pokemon_index >= len(enemy_pokemon_list):
            # Player won - defeated all enemy Pokemon
            battle_result = 'victory'
            battle.battleVictory(next_trainer)
            # LEADERBOARD TRACKING
            from services.leaderboardclass import leaderboard as LeaderboardClass
            lb = LeaderboardClass(str(user.id))
            lb.victory()
            lb.actions()
        else:
            # Player lost - all player Pokemon fainted
            battle_result = 'defeat'
            # LEADERBOARD TRACKING
            from services.leaderboardclass import leaderboard as LeaderboardClass
            lb = LeaderboardClass(str(user.id))
            lb.defeat()
            lb.actions()
        
        # Create summary embed
        battle_log_text = "\n".join(all_battle_logs[-20:])  # Last 20 lines
        
        if battle_result == 'victory':
            embed = discord.Embed(
                title="🎉 Victory!",
                description=f"You defeated {next_trainer.name}!",
                color=discord.Color.green()
            )
            
            # Show defeated enemies
            enemy_summary = []
            enemy_summary.append(f"**Defeated {len(defeated_enemies)} Pokemon:**")
            for i, poke_name in enumerate(defeated_enemies, 1):
                enemy_summary.append(f"{i}. {poke_name.capitalize()} ❌")
            
            embed.add_field(
                name="🎯 Enemy Team",
                value="\n".join(enemy_summary),
                inline=True
            )
            
            # Show player's final Pokemon
            final_player = alive_party[player_pokemon_index]
            player_stats = final_player.getPokeStats()
            player_summary = []
            player_summary.append(f"**Your {final_player.pokemonName.capitalize()}** (Lv.{final_player.currentLevel})")
            player_summary.append(f"HP: {final_player.currentHP}/{player_stats['hp']}")
            if len(defeated_player) > 0:
                player_summary.append(f"\nFainted: {len(defeated_player)}/{len(alive_party)}")
            
            embed.add_field(
                name="💚 Your Team",
                value="\n".join(player_summary),
                inline=True
            )
            
            # Battle log
            embed.add_field(
                name="⚔️ Battle Log",
                value=battle_log_text[:1024],
                inline=False
            )
            
            # Experience gains
            if len(exp_messages) > 0:
                exp_text = "\n".join(exp_messages[:5])  # Show up to 5 Pokemon's exp
                embed.add_field(
                    name="📈 Experience Gained",
                    value=exp_text[:1024],
                    inline=False
                )
            
            embed.add_field(
                name="💰 Reward",
                value=f"${next_trainer.money}",
                inline=True
            )
            
            # Check for more trainers
            remaining = battle.getRemainingTrainerCount()
            if remaining > 0:
                next_up = battle.getNextTrainer()
                embed.add_field(
                    name="⚔️ Next",
                    value=f"{remaining} trainers remaining\nNext: {next_up.name if next_up else 'Unknown'}",
                    inline=True
                )
            else:
                gym_leader = battle.getGymLeader()
                if gym_leader:
                    embed.add_field(
                        name="🏆 Gym Progress",
                        value=f"All trainers defeated!\nChallenge {gym_leader.name}!",
                        inline=True
                    )
            
        else:
            # Defeat
            embed = discord.Embed(
                title="💀 Defeat",
                description=f"You were defeated by {next_trainer.name}...",
                color=discord.Color.red()
            )
            
            # Show player's fainted Pokemon
            player_summary = []
            player_summary.append(f"**Your Team:** All {len(alive_party)} Pokemon fainted")
            for i, poke_name in enumerate(defeated_player, 1):
                player_summary.append(f"{i}. {poke_name.capitalize()} ❌")
            
            embed.add_field(
                name="💚 Your Team",
                value="\n".join(player_summary),
                inline=True
            )
            
            # Show enemy's remaining Pokemon
            enemy_summary = []
            if len(defeated_enemies) > 0:
                enemy_summary.append(f"**Defeated:** {len(defeated_enemies)}/{len(enemy_pokemon_list)}")
            
            current_enemy = enemy_pokemon_list[enemy_pokemon_index]
            current_enemy_name = list(current_enemy.keys())[0]
            current_enemy_level = current_enemy[current_enemy_name]
            enemy_summary.append(f"\n**{current_enemy_name.capitalize()}** (Lv.{current_enemy_level}) - Still standing")
            
            embed.add_field(
                name="🎯 Enemy Team",
                value="\n".join(enemy_summary),
                inline=True
            )
            
            # Battle log
            embed.add_field(
                name="⚔️ Battle Log",
                value=battle_log_text[:1024],
                inline=False
            )
        
        # new code
        view_nav = self.__create_post_battle_buttons(str(user.id))
        new_message = await interaction.followup.send(embed=embed, view=view_nav, ephemeral=False)
        
        # CRITICAL: Update ActionState with new message ID so buttons work
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        self.__useractions[str(user.id)] = ActionState(
            str(user.id),
            new_message.channel.id,
            new_message.id,
            location,
            trainer.getActivePokemon(),
            None,
            ''
        )

    async def on_gym_battle_manual(self, interaction: discord.Interaction):
        """Handle MANUAL battle with gym trainer"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()

        battle_manager = BattleClass(str(user.id), location.locationId, enemyType="gym")
        opponent = battle_manager.getNextTrainer()
        
        sprite_path = opponent.spritePath if opponent else None

        await self._start_manual_trainer_battle(
            interaction,
            enemy_type="gym",
            opponent=opponent,
            battle_manager=battle_manager,
            sprite_path=sprite_path,
            is_gym_leader=False
        )

    async def on_mart_sell_menu(self, interaction: discord.Interaction):
        """Show sell menu with player's items"""
        from discord.ui import Select
        from discord import SelectOption
        from .pokemart import itemDisplayNames
        from services.inventoryclass import inventory as InventoryClass
        
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_mart_states') or str(user.id) not in self._mart_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        state = self._mart_states[str(user.id)]
        state.mode = 'sell'
        
        # Get trainer's inventory
        inventory = InventoryClass(str(user.id))
        
        # Build list of sellable items (items with quantity > 0)
        sellable_items = []
        item_mapping = {
            'poke-ball': inventory.pokeball,
            'great-ball': inventory.greatball,
            'ultra-ball': inventory.ultraball,
            'master-ball': inventory.masterball,
            'potion': inventory.potion,
            'super-potion': inventory.superpotion,
            'hyper-potion': inventory.hyperpotion,
            'max-potion': inventory.maxpotion,
            'revive': inventory.revive,
            'full-restore': inventory.fullrestore,
            'repel': inventory.repel,
            'super-repel': inventory.superrepel,
            'max-repel': inventory.maxrepel,
            'antidote': inventory.antidote,
            'burn-heal': inventory.burnheal,
            'ice-heal': inventory.iceheal,
            'paralyze-heal': inventory.paralyzeheal,
            'awakening': inventory.awakening,
            'escape-rope': inventory.escaperope,
        }
        
        for item_name, qty in item_mapping.items():
            if qty > 0:
                sellable_items.append((item_name, qty))
        
        if not sellable_items:
            embed = discord.Embed(
                title="❌ No Items to Sell",
                description="You don't have any items to sell!",
                color=discord.Color.red()
            )
            
            view = View()
            back_btn = Button(style=ButtonStyle.secondary, label="← Back", custom_id='mart_main_menu')
            back_btn.callback = self.on_nav_mart_click
            view.add_item(back_btn)
            
            await interaction.message.edit(embed=embed, view=view)
            return
        
        # Create embed
        from .constant import LOCATION_DISPLAY_NAMES
        embed = discord.Embed(
            title=f"Sell Items - {LOCATION_DISPLAY_NAMES.get(state.location.name, state.location.name)}",
            description=f"Select an item to sell.\n\n💰 Your Money: **${inventory.money:,}**\n\n*Items sell for 50% of purchase price*",
            color=discord.Color.blurple()
        )
        
        # Create dropdown
        options = []
        for item_name, qty in sellable_items[:25]:  # Discord limit
            display_info = itemDisplayNames.get(item_name, {})
            display_name = display_info.get('name', item_name)
            emoji_str = display_info.get('emoji', '📦')
            
            # Get sell price (half of buy price) from storeclass
            from services.storeclass import store as StoreClass
            temp_store = StoreClass(str(user.id), state.location.locationId)
            sell_price = temp_store._store__getItemPrice(item_name) // 2
            
            options.append(SelectOption(
                label=f"{display_name} (x{qty}) - ${sell_price}",
                value=item_name,
                description=f"Sell for ${sell_price} each",
                emoji=emoji_str
            ))
        
        # Create view
        view = View()
        
        select = Select(
            placeholder="Choose an item to sell...",
            options=options,
            custom_id='mart_sell_select'
        )
        select.callback = self.on_mart_sell_item_selected
        view.add_item(select)
        
        back_btn = Button(style=ButtonStyle.secondary, label="← Back", custom_id='mart_main_menu', row=1)
        back_btn.callback = self.on_nav_mart_click
        view.add_item(back_btn)
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_mart_sell_item_selected(self, interaction: discord.Interaction):
        """Handle sell item selection"""
        from .pokemart import itemDisplayNames
        from services.inventoryclass import inventory as InventoryClass
        from services.storeclass import store as StoreClass
        
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_mart_states') or str(user.id) not in self._mart_states:
            return
        
        state = self._mart_states[str(user.id)]
        selected_item = interaction.data['values'][0]
        state.selected_item = selected_item
        state.quantity = 1
        
        # Get item info
        inventory = InventoryClass(str(user.id))
        temp_store = StoreClass(str(user.id), state.location.locationId)
        sell_price = temp_store._store__getItemPrice(selected_item) // 2
        
        display_info = itemDisplayNames.get(selected_item, {})
        display_name = display_info.get('name', selected_item)
        description = display_info.get('desc', 'No description')
        emoji_str = display_info.get('emoji', '📦')
        
        # Create confirmation embed
        embed = discord.Embed(
            title=f"{emoji_str} Sell {display_name}",
            description=description,
            color=discord.Color.blurple()
        )
        embed.add_field(name="Sell Price (50%)", value=f"${sell_price:,}", inline=True)
        embed.add_field(name="Your Money", value=f"${inventory.money:,}", inline=True)
        embed.add_field(name="Quantity", value=f"**{state.quantity}**", inline=True)
        embed.add_field(name="Total Value", value=f"${sell_price * state.quantity:,}", inline=False)
        
        # Create view with quantity buttons
        view = View()
        
        minus_btn = Button(style=ButtonStyle.gray, label="-1", custom_id='mart_sell_qty_minus', row=0)
        minus_btn.callback = self.on_mart_sell_qty_change
        view.add_item(minus_btn)
        
        plus_btn = Button(style=ButtonStyle.gray, label="+1", custom_id='mart_sell_qty_plus', row=0)
        plus_btn.callback = self.on_mart_sell_qty_change
        view.add_item(plus_btn)
        
        plus5_btn = Button(style=ButtonStyle.gray, label="+5", custom_id='mart_sell_qty_plus5', row=0)
        plus5_btn.callback = self.on_mart_sell_qty_change
        view.add_item(plus5_btn)
        
        plus10_btn = Button(style=ButtonStyle.gray, label="+10", custom_id='mart_sell_qty_plus10', row=0)
        plus10_btn.callback = self.on_mart_sell_qty_change
        view.add_item(plus10_btn)
        
        sell_btn = Button(style=ButtonStyle.green, label="✅ Sell", custom_id='mart_confirm_sell', row=1)
        sell_btn.callback = self.on_mart_confirm_sell
        view.add_item(sell_btn)
        
        back_btn = Button(style=ButtonStyle.secondary, label="← Back", custom_id='mart_sell_back', row=1)
        back_btn.callback = self.on_mart_sell_menu
        view.add_item(back_btn)
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_mart_sell_qty_change(self, interaction: discord.Interaction):
        """Handle quantity changes for selling"""
        from .pokemart import itemDisplayNames
        from services.inventoryclass import inventory as InventoryClass
        from services.storeclass import store as StoreClass
        
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_mart_states') or str(user.id) not in self._mart_states:
            return
        
        state = self._mart_states[str(user.id)]
        
        # Adjust quantity
        button_id = interaction.data['custom_id']
        if button_id == 'mart_sell_qty_minus':
            state.quantity = max(1, state.quantity - 1)
        elif button_id == 'mart_sell_qty_plus':
            state.quantity += 1
        elif button_id == 'mart_sell_qty_plus5':
            state.quantity += 5
        elif button_id == 'mart_sell_qty_plus10':
            state.quantity += 10
        
        state.quantity = min(999, state.quantity)
        
        # Update embed
        inventory = InventoryClass(str(user.id))
        temp_store = StoreClass(str(user.id), state.location.locationId)
        sell_price = temp_store._store__getItemPrice(state.selected_item) // 2
        
        display_info = itemDisplayNames.get(state.selected_item, {})
        display_name = display_info.get('name', state.selected_item)
        description = display_info.get('desc', 'No description')
        emoji_str = display_info.get('emoji', '📦')
        
        embed = discord.Embed(
            title=f"{emoji_str} Sell {display_name}",
            description=description,
            color=discord.Color.blurple()
        )
        embed.add_field(name="Sell Price (50%)", value=f"${sell_price:,}", inline=True)
        embed.add_field(name="Your Money", value=f"${inventory.money:,}", inline=True)
        embed.add_field(name="Quantity", value=f"**{state.quantity}**", inline=True)
        embed.add_field(name="Total Value", value=f"${sell_price * state.quantity:,}", inline=False)
        
        await interaction.message.edit(embed=embed)


    async def on_mart_confirm_sell(self, interaction: discord.Interaction):
        """Execute the sale"""
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_mart_states') or str(user.id) not in self._mart_states:
            return
        
        state = self._mart_states[str(user.id)]
        
        # Execute sale
        state.store.sellItem(state.selected_item, state.quantity)
        
        # Show result
        if state.store.statuscode == 420:
            embed = discord.Embed(
                title="✅ Sale Complete!" if "successfully" in state.store.message else "❌ Sale Failed",
                description=state.store.message,
                color=discord.Color.green() if "successfully" in state.store.message else discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred during the sale.",
                color=discord.Color.red()
            )
        
        # Add back buttons
        view = View()
        back_btn = Button(style=ButtonStyle.primary, label="← Back to Mart", custom_id='mart_main')
        back_btn.callback = self.on_mart_back_to_mart_after_purchase
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.secondary, label="🗺️ Map", custom_id='nav_map')
        map_btn.callback = self.on_nav_map_click
        view.add_item(map_btn)
        
        # Reset
        state.quantity = 1
        state.selected_item = None
        
        await interaction.message.edit(embed=embed, view=view)
        await self.sendToLoggingChannel(state.store.message)

    async def on_mart_back_to_mart_after_purchase(self, interaction: discord.Interaction):
        """Handle Back to Mart button after purchase/sell completion"""
        user = interaction.user
        await interaction.response.defer()
        
        # Call the main mart navigation method
        await self.on_nav_mart_click(interaction, already_deferred=True)

    async def on_mart_item_selected(self, interaction: discord.Interaction):
        """Handle item selection from dropdown"""
        from discord.ui import Select
        from discord import SelectOption
        from .pokemart import itemDisplayNames
        from services.inventoryclass import inventory as InventoryClass
        
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_mart_states') or str(user.id) not in self._mart_states:
            await interaction.followup.send('Session expired.', ephemeral=True)
            return
        
        state = self._mart_states[str(user.id)]
        
        # Get selected item
        selected_item = interaction.data['values'][0]
        state.selected_item = selected_item
        
        # Find item price
        item_price = None
        for page in state.store.storeList:
            for item in page:
                if item.name == selected_item:
                    item_price = item.price
                    break
        
        if not item_price:
            await interaction.followup.send('Item not found.', ephemeral=True)
            return
        
        # Get display info
        display_info = itemDisplayNames.get(selected_item, {})
        display_name = display_info.get('name', selected_item)
        description = display_info.get('desc', 'No description available')
        emoji_str = display_info.get('emoji', '📦')
        
        # Get trainer's money
        inventory = InventoryClass(str(user.id))
        
        # Create purchase confirmation embed
        embed = discord.Embed(
            title=f"{emoji_str} {display_name}",
            description=description,
            color=discord.Color.green()
        )
        embed.add_field(name="Price", value=f"${item_price:,}", inline=True)
        embed.add_field(name="Your Money", value=f"${inventory.money:,}", inline=True)
        embed.add_field(name="Quantity", value=f"**{state.quantity}**", inline=True)
        embed.add_field(name="Total Cost", value=f"${item_price * state.quantity:,}", inline=False)
        
        # Create view with quantity buttons and purchase button
        view = View()
        
        # Quantity adjustment buttons
        minus_btn = Button(style=ButtonStyle.gray, label="-1", custom_id='mart_qty_minus', row=0)
        minus_btn.callback = self.on_mart_qty_change
        view.add_item(minus_btn)
        
        plus_btn = Button(style=ButtonStyle.gray, label="+1", custom_id='mart_qty_plus', row=0)
        plus_btn.callback = self.on_mart_qty_change
        view.add_item(plus_btn)
        
        plus5_btn = Button(style=ButtonStyle.gray, label="+5", custom_id='mart_qty_plus5', row=0)
        plus5_btn.callback = self.on_mart_qty_change
        view.add_item(plus5_btn)
        
        plus10_btn = Button(style=ButtonStyle.gray, label="+10", custom_id='mart_qty_plus10', row=0)
        plus10_btn.callback = self.on_mart_qty_change
        view.add_item(plus10_btn)
        
        # Purchase and back buttons
        buy_btn = Button(style=ButtonStyle.green, label="✅ Purchase", custom_id='mart_confirm_buy', row=1)
        buy_btn.callback = self.on_mart_confirm_purchase
        view.add_item(buy_btn)
        
        back_btn = Button(style=ButtonStyle.secondary, label="← Back", custom_id='mart_buy_back', row=1)
        back_btn.callback = self.on_mart_buy_menu
        view.add_item(back_btn)
        
        await interaction.message.edit(embed=embed, view=view)


    async def on_mart_qty_change(self, interaction: discord.Interaction):
        """Handle quantity adjustment buttons"""
        from .pokemart import itemDisplayNames
        from services.inventoryclass import inventory as InventoryClass
        
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_mart_states') or str(user.id) not in self._mart_states:
            return
        
        state = self._mart_states[str(user.id)]
        
        # Adjust quantity based on button
        button_id = interaction.data['custom_id']
        if button_id == 'mart_qty_minus':
            state.quantity = max(1, state.quantity - 1)
        elif button_id == 'mart_qty_plus':
            state.quantity += 1
        elif button_id == 'mart_qty_plus5':
            state.quantity += 5
        elif button_id == 'mart_qty_plus10':
            state.quantity += 10
        
        # Cap at 999
        state.quantity = min(999, state.quantity)
        
        # Find item price
        item_price = None
        for page in state.store.storeList:
            for item in page:
                if item.name == state.selected_item:
                    item_price = item.price
                    break
        
        # Get display info
        display_info = itemDisplayNames.get(state.selected_item, {})
        display_name = display_info.get('name', state.selected_item)
        description = display_info.get('desc', 'No description available')
        emoji_str = display_info.get('emoji', '📦')
        
        # Get trainer's money
        inventory = InventoryClass(str(user.id))
        
        # Update embed
        embed = discord.Embed(
            title=f"{emoji_str} {display_name}",
            description=description,
            color=discord.Color.green()
        )
        embed.add_field(name="Price", value=f"${item_price:,}", inline=True)
        embed.add_field(name="Your Money", value=f"${inventory.money:,}", inline=True)
        embed.add_field(name="Quantity", value=f"**{state.quantity}**", inline=True)
        embed.add_field(name="Total Cost", value=f"${item_price * state.quantity:,}", inline=False)
        
        await interaction.message.edit(embed=embed)


    async def on_mart_confirm_purchase(self, interaction: discord.Interaction):
        """Execute the purchase"""
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_mart_states') or str(user.id) not in self._mart_states:
            return
        
        state = self._mart_states[str(user.id)]
        
        # Execute purchase using StoreClass
        state.store.buyItem(state.selected_item, state.quantity)
        
        # Show result
        if state.store.statuscode == 420:
            embed = discord.Embed(
                title="✅ Purchase Complete!" if "successfully" in state.store.message else "❌ Purchase Failed",
                description=state.store.message,
                color=discord.Color.green() if "successfully" in state.store.message else discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred during the purchase.",
                color=discord.Color.red()
            )
        
        # Add back to mart button
        view = View()
        back_btn = Button(style=ButtonStyle.primary, label="← Back to Mart", custom_id='mart_main', row=0)
        back_btn.callback = self.on_mart_back_to_mart_after_purchase
        view.add_item(back_btn)
        
        map_btn = Button(style=ButtonStyle.secondary, label="🗺️ Map", custom_id='nav_map', row=0)
        map_btn.callback = self.on_nav_map_click
        view.add_item(map_btn)
        
        # Reset quantity for next purchase
        state.quantity = 1
        state.selected_item = None
        
        await interaction.message.edit(embed=embed, view=view)
        
        # Log to channel
        await self.sendToLoggingChannel(state.store.message)

    async def on_mart_buy_menu(self, interaction: discord.Interaction):
        """Show buy menu with item dropdown"""
        from discord.ui import Select
        from discord import SelectOption
        from .pokemart import itemDisplayNames
        from services.inventoryclass import inventory as InventoryClass
        
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_mart_states') or str(user.id) not in self._mart_states:
            await interaction.followup.send('Session expired. Please reopen the mart.', ephemeral=True)
            return
        
        state = self._mart_states[str(user.id)]
        state.mode = 'buy'
        
        # Get all available items from store
        all_items = []
        for page in state.store.storeList:
            for item in page:
                all_items.append(item)
        
        # Get trainer's money
        inventory = InventoryClass(str(user.id))
        
        # Create embed
        from .constant import LOCATION_DISPLAY_NAMES
        embed = discord.Embed(
            title=f"Buy Items - {LOCATION_DISPLAY_NAMES.get(state.location.name, state.location.name)}",
            description=f"Select an item to purchase.\n\n💰 Your Money: **${inventory.money:,}**",
            color=discord.Color.green()
        )
        
        # Create dropdown with items (max 25 options)
        options = []
        for item in all_items[:25]:  # Discord limit
            display_name = itemDisplayNames.get(item.name, {}).get('name', item.name)
            emoji_str = itemDisplayNames.get(item.name, {}).get('emoji', '📦')
            
            options.append(SelectOption(
                label=f"{display_name} - ${item.price}",
                value=item.name,
                description=f"Buy for ${item.price}",
                emoji=emoji_str
            ))
        
        # Create view with dropdown
        view = View()
        
        select = Select(
            placeholder="Choose an item to buy...",
            options=options,
            custom_id='mart_buy_select'
        )
        select.callback = self.on_mart_item_selected
        view.add_item(select)
        
        # Add back button
        back_btn = Button(style=ButtonStyle.secondary, label="← Back", custom_id='mart_main_menu', row=1)
        back_btn.callback = self.on_nav_mart_click
        view.add_item(back_btn)
        
        await interaction.message.edit(embed=embed, view=view)

    async def on_nav_mart_click(self, interaction: discord.Interaction, already_deferred: bool = False):
        """Handle Mart button click - open Pokemart main menu"""
        user = interaction.user
        
        if not already_deferred:
            await interaction.response.defer()
        
        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        # Import StoreClass
        from services.storeclass import store as StoreClass
        from services.inventoryclass import inventory as InventoryClass
        
        store = StoreClass(str(user.id), location.locationId)
        
        # Check if there's a Pokemart at this location
        if store.statuscode == 420:
            # No Pokemart here - show error with navigation buttons
            embed = discord.Embed(
                title="❌ No Poké Mart",
                description=store.message,
                color=discord.Color.red()
            )
            embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
            
            view = View()
            map_button = Button(style=ButtonStyle.primary, label="🗺️ Map", custom_id='nav_map')
            map_button.callback = self.on_nav_map_click
            view.add_item(map_button)
            
            await interaction.message.edit(content=None, embed=embed, view=view)
            return
        
        # Get trainer's money
        inventory = InventoryClass(str(user.id))
        
        # Create main mart menu
        from .constant import LOCATION_DISPLAY_NAMES
        embed = discord.Embed(
            title=f"Poké Mart - {LOCATION_DISPLAY_NAMES.get(location.name, location.name)}",
            description=f"Welcome to the Poké Mart!\n\n💰 Your Money: **${inventory.money:,}**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://pokesprites.joshkohut.com/sprites/locations/poke_mart.png")
        
        # Create Buy/Sell/Back buttons
        view = View()
        
        buy_btn = Button(style=ButtonStyle.green, label="💵 Buy Items", custom_id='mart_buy_menu', row=0)
        buy_btn.callback = self.on_mart_buy_menu
        view.add_item(buy_btn)
        
        sell_btn = Button(style=ButtonStyle.blurple, label="💰 Sell Items", custom_id='mart_sell_menu', row=0)
        sell_btn.callback = self.on_mart_sell_menu
        view.add_item(sell_btn)
        
        back_btn = Button(style=ButtonStyle.secondary, label="🗺️ Back to Map", custom_id='mart_back_to_map', row=1)
        back_btn.callback = self.on_mart_back_to_map
        view.add_item(back_btn)
        
        # Store mart state
        if not hasattr(self, '_mart_states'):
            self._mart_states = {}
        
        self._mart_states[str(user.id)] = MartState(
            str(user.id), 
            interaction.message.id, 
            interaction.message.channel.id, 
            location, 
            store,
            'main'
        )
        
        await interaction.message.edit(content=None, embed=embed, view=view)


    async def on_mart_prev_click(self, interaction: discord.Interaction):
        """Handle Previous page in Mart"""
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_PokemartMixin__store') or str(user.id) not in self._PokemartMixin__store:
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return
        
        state = self._PokemartMixin__store[str(user.id)]
        state.idx = state.idx - 1
        
        embed, btns = self.__create_mart_embed(user, state)
        
        # Add back to map button
        back_btn = Button(style=ButtonStyle.secondary, label="🗺️ Back to Map", custom_id='mart_back_to_map', row=4)
        back_btn.callback = self.on_mart_back_to_map
        btns.add_item(back_btn)
        
        await interaction.message.edit(embed=embed, view=btns)

    async def on_mart_next_click(self, interaction: discord.Interaction):
        """Handle Next page in Mart"""
        user = interaction.user
        await interaction.response.defer()
        
        if not hasattr(self, '_PokemartMixin__store') or str(user.id) not in self._PokemartMixin__store:
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return
        
        state = self._PokemartMixin__store[str(user.id)]
        state.idx = state.idx + 1
        
        embed, btns = self.__create_mart_embed(user, state)
        
        # Add back to map button
        back_btn = Button(style=ButtonStyle.secondary, label="🗺️ Back to Map", custom_id='mart_back_to_map', row=4)
        back_btn.callback = self.on_mart_back_to_map
        btns.add_item(back_btn)
        
        await interaction.message.edit(embed=embed, view=btns)

    async def on_mart_back_to_map(self, interaction: discord.Interaction):
        """Handle Back to Map button from Mart"""
        user = interaction.user
        
        # Clean up mart state
        if hasattr(self, '_PokemartMixin__store') and str(user.id) in self._PokemartMixin__store:
            del self._PokemartMixin__store[str(user.id)]
        
        # Return to map view
        await self.on_nav_map_click(interaction, already_deferred=False)

    def __create_mart_embed(self, user: discord.Member, state):
        """Create the Pokemart shop embed - mirrors pokemart.py's __storePageEmbed"""
        from .constant import LOCATION_DISPLAY_NAMES
        
        embed = discord.Embed(
            title=f"Poké Mart - {LOCATION_DISPLAY_NAMES.get(state.location.name, state.location.name)}"
        )
        embed.set_thumbnail(
            url=f"https://pokesprites.joshkohut.com/sprites/locations/poke_mart.png"
        )
        
        # Import item display names
        from .pokemart import itemDisplayNames
        
        firstList = state.storeList[state.idx]
        
        for item in firstList:
            key = item.name
            price = item.price
            
            emoji = itemDisplayNames[key]['emoji']
            description = itemDisplayNames[key]['desc']
            name = itemDisplayNames[key]['name']
            
            embed.add_field(
                name=f"{emoji}  {name} — {price}",
                value=description,
                inline=False
            )
        
        view = View()
        
        if state.idx > 0:
            button = Button(style=ButtonStyle.gray, label='Previous', custom_id='mart_previous')
            button.callback = self.on_mart_prev_click
            view.add_item(button)
        
        if state.idx < len(state.storeList) - 1:
            button = Button(style=ButtonStyle.gray, label="Next", custom_id='mart_next')
            button.callback = self.on_mart_next_click
            view.add_item(button)
        
        return embed, view

    async def on_gym_leader_battle_auto(self, interaction: discord.Interaction):
        """Handle gym leader AUTO battle - now supports multiple Pokemon"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()
        
        # Get player's full party
        player_party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in player_party:
            poke.load(pokemonId=poke.trainerId)
            if poke.currentHP > 0:
                alive_party.append(poke)
        
        if len(alive_party) == 0:
            await interaction.followup.send('All your party Pokemon have fainted!', ephemeral=True)
            return

        alive_party = self.__sort_party_active_first(alive_party, str(user.id))
        gyms_data = self.__load_gyms_data()
        gym_info = gyms_data.get(str(location.locationId))
        battle = BattleClass(str(user.id), location.locationId, enemyType="gym")

        gym_leader = battle.getGymLeader()
        if not gym_leader or battle.statuscode == 420:
            await interaction.followup.send(battle.message if battle.message else 'Cannot challenge gym leader.', ephemeral=True)
            return

        if not gym_leader.pokemon or len(gym_leader.pokemon) == 0:
            await interaction.followup.send(f'Error: Gym Leader has no Pokemon data.', ephemeral=True)
            return

        # Get ALL gym leader Pokemon
        enemy_pokemon_list = gym_leader.pokemon
        
        # Battle tracking
        player_pokemon_index = 0
        enemy_pokemon_index = 0
        all_battle_logs = []
        defeated_enemies = []
        defeated_player = []
        exp_messages = []  # Track experience gains
        
        # Battle loop - continue until one side has no Pokemon left
        battle_result = None
        
        while player_pokemon_index < len(alive_party) and enemy_pokemon_index < len(enemy_pokemon_list):
            # Get current Pokemon
            player_pokemon = alive_party[player_pokemon_index]
            enemy_data = enemy_pokemon_list[enemy_pokemon_index]
            
            # Create enemy Pokemon
            enemy_name = list(enemy_data.keys())[0]
            enemy_level = enemy_data[enemy_name]
            enemy_pokemon = PokemonClass(str(user.id), enemy_name)
            enemy_pokemon.create(enemy_level)
            enemy_pokemon.discordId = None
            
            # Fight this matchup
            enc = EncounterClass(player_pokemon, enemy_pokemon)
            result = enc.fight(battleType='auto')
            
            # Add this battle's logs
            if hasattr(enc, 'battle_log') and enc.battle_log:
                all_battle_logs.extend(enc.battle_log)
            
            # Capture experience message
            if enc.message:
                exp_messages.append(f"{player_pokemon.pokemonName.capitalize()}: {enc.message}")

            # Process result
            if result.get('result') == 'victory':
                # Player won this round - enemy Pokemon fainted
                defeated_enemies.append(enemy_name)
                enemy_pokemon_index += 1
                all_battle_logs.append(f"💀 Enemy {enemy_name.capitalize()} fainted!")
                
                if enemy_pokemon_index < len(enemy_pokemon_list):
                    next_enemy_name = list(enemy_pokemon_list[enemy_pokemon_index].keys())[0]
                    all_battle_logs.append(f"⚡ {gym_leader.name} sent out {next_enemy_name.capitalize()}!")
            else:
                # Player lost this round - player Pokemon fainted
                defeated_player.append(player_pokemon.pokemonName)
                player_pokemon_index += 1
                all_battle_logs.append(f"💀 Your {player_pokemon.pokemonName.capitalize()} fainted!")
                
                if player_pokemon_index < len(alive_party):
                    next_player = alive_party[player_pokemon_index]
                    all_battle_logs.append(f"⚡ You sent out {next_player.pokemonName.capitalize()}!")
        
        # Determine overall winner
        if enemy_pokemon_index >= len(enemy_pokemon_list):
            # Player won - defeated all enemy Pokemon
            battle_result = 'victory'
            battle.gymLeaderVictory(gym_leader)
            # LEADERBOARD TRACKING
            from services.leaderboardclass import leaderboard as LeaderboardClass
            lb = LeaderboardClass(str(user.id))
            lb.victory()
            lb.actions()
        else:
            # Player lost - all player Pokemon fainted
            battle_result = 'defeat'
            # LEADERBOARD TRACKING
            from services.leaderboardclass import leaderboard as LeaderboardClass
            lb = LeaderboardClass(str(user.id))
            lb.defeat()
            lb.actions()
        
        # Create summary embed
        battle_log_text = "\n".join(all_battle_logs[-20:])  # Last 20 lines
        
        if battle_result == 'victory':
            embed = discord.Embed(
                title="🏆 VICTORY!",
                description=f"You defeated Gym Leader {gym_leader.name}!",
                color=discord.Color.gold()
            )
            
            # Show defeated enemies
            enemy_summary = []
            enemy_summary.append(f"**Defeated {len(defeated_enemies)} Pokemon:**")
            for i, poke_name in enumerate(defeated_enemies, 1):
                enemy_summary.append(f"{i}. {poke_name.capitalize()} ❌")
            
            embed.add_field(
                name="🎯 Enemy Team",
                value="\n".join(enemy_summary),
                inline=True
            )
            
            # Show player's final Pokemon
            final_player = alive_party[player_pokemon_index]
            player_stats = final_player.getPokeStats()
            player_summary = []
            player_summary.append(f"**Your {final_player.pokemonName.capitalize()}** (Lv.{final_player.currentLevel})")
            player_summary.append(f"HP: {final_player.currentHP}/{player_stats['hp']}")
            if len(defeated_player) > 0:
                player_summary.append(f"\nFainted: {len(defeated_player)}/{len(alive_party)}")
            
            embed.add_field(
                name="💚 Your Team",
                value="\n".join(player_summary),
                inline=True
            )
            
            # Battle log
            embed.add_field(
                name="⚔️ Battle Log",
                value=battle_log_text[:1024],
                inline=False
            )
            
            # Experience gains
            if len(exp_messages) > 0:
                exp_text = "\n".join(exp_messages[:5])  # Show up to 5 Pokemon's exp
                embed.add_field(
                    name="📈 Experience Gained",
                    value=exp_text[:1024],
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
            
        else:
            # Defeat
            embed = discord.Embed(
                title="💀 Defeat",
                description=f"You were defeated by Gym Leader {gym_leader.name}...",
                color=discord.Color.dark_red()
            )
            
            # Show player's fainted Pokemon
            player_summary = []
            player_summary.append(f"**Your Team:** All {len(alive_party)} Pokemon fainted")
            for i, poke_name in enumerate(defeated_player, 1):
                player_summary.append(f"{i}. {poke_name.capitalize()} ❌")
            
            embed.add_field(
                name="💚 Your Team",
                value="\n".join(player_summary),
                inline=True
            )
            
            # Show enemy's remaining Pokemon
            enemy_summary = []
            if len(defeated_enemies) > 0:
                enemy_summary.append(f"**Defeated:** {len(defeated_enemies)}/{len(enemy_pokemon_list)}")
            
            current_enemy = enemy_pokemon_list[enemy_pokemon_index]
            current_enemy_name = list(current_enemy.keys())[0]
            current_enemy_level = current_enemy[current_enemy_name]
            enemy_summary.append(f"\n**{current_enemy_name.capitalize()}** (Lv.{current_enemy_level}) - Still standing")
            
            embed.add_field(
                name="🎯 Enemy Team",
                value="\n".join(enemy_summary),
                inline=True
            )
            
            # Battle log
            embed.add_field(
                name="⚔️ Battle Log",
                value=battle_log_text[:1024],
                inline=False
            )
        
        view_nav = self.__create_post_battle_buttons(str(user.id))
        await interaction.followup.send(embed=embed, view=view_nav, ephemeral=False)


    async def on_gym_click(self, interaction: discord.Interaction):
        """Handle gym button clicks - now shows battle type choice with embed"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        # Get location and gym data
        trainer = self._get_trainer(str(user.id))
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
                # Create embed
                embed = discord.Embed(
                    title=f"🏛️ {gym_info['leader']['gym-name']}",
                    description=f"Choose your battle mode to face the next gym trainer!",
                    color=discord.Color.red()
                )
                
                embed.add_field(
                    name="Trainers Remaining",
                    value=f"{remaining_trainers}",
                    inline=True
                )
                
                embed.add_field(
                    name="Next Opponent",
                    value=next_trainer.name,
                    inline=True
                )
                
                embed.add_field(
                    name="Reward",
                    value=f"${next_trainer.money}",
                    inline=True
                )
                
                # ADD GYM SPRITE
                gym_sprite_path = gym_info['leader'].get('gym_spritePath')
                sprite_file = None
                
                if gym_sprite_path:
                    try:
                        full_sprite_path = get_sprite_path(gym_sprite_path)
                        if os.path.exists(full_sprite_path):
                            filename = os.path.basename(gym_sprite_path)
                            sprite_file = discord.File(full_sprite_path, filename=filename)
                            embed.set_image(url=f"attachment://{filename}")
                    except Exception as e:
                        print(f"Error loading gym sprite: {e}")
                        # Fallback to URL
                        sprite_url = f"https://pokesprites.joshkohut.com{gym_sprite_path}"
                        embed.set_image(url=sprite_url)
                
                view = View()
                
                # Auto Battle button
                auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Battle", custom_id='gym_battle_auto')
                auto_button.callback = self.on_gym_battle_auto
                view.add_item(auto_button)
                
                # Manual Battle button  
                manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Battle", custom_id='gym_battle_manual')
                manual_button.callback = self.on_gym_battle_manual
                view.add_item(manual_button)
                
                # Back button
                back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back", custom_id='gym_back', row=1)
                back_btn.callback = self.on_nav_map_click
                view.add_item(back_btn)

                # Send message with sprite file if available
                if sprite_file:
                    new_message = await interaction.followup.send(
                        embed=embed,
                        view=view,
                        file=sprite_file
                    )
                    try:
                        await interaction.message.delete()
                    except:
                        pass
                    if str(user.id) in self.__useractions:
                        self.__useractions[str(user.id)].messageId = new_message.id
                else:
                    await interaction.message.edit(
                        content=None,
                        embed=embed,
                        view=view
                    )
            else:
                await interaction.followup.send('Error getting next trainer.', ephemeral=True)
        else:
            # All trainers defeated, try to get gym leader
            gym_leader = battle.getGymLeader()

            if battle.statuscode == 420:
                if "already completed" in battle.message.lower():
                    embed = discord.Embed(
                        title=f"🏛️ {gym_info['leader']['gym-name']}",
                        description=f'You have already defeated Gym Leader {gym_info["leader"]["gym-leader"]} and earned the {gym_info["leader"]["badge"]}!',
                        color=discord.Color.gold()
                    )
                    
                    view = View()
                    back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back to Map", custom_id='gym_back')
                    back_btn.callback = self.on_nav_map_click
                    view.add_item(back_btn)
                    
                    await interaction.message.edit(
                        content=None,
                        embed=embed,
                        view=view
                    )
                else:
                    await interaction.followup.send(battle.message, ephemeral=True)
                return

            if not gym_leader:
                await interaction.followup.send('Gym leader data not found.', ephemeral=True)
                return

            # Show gym leader challenge
            embed = discord.Embed(
                title=f"🏆 {gym_info['leader']['gym-name']} - Gym Leader",
                description=f"All gym trainers defeated! You can now challenge the Gym Leader!",
                color=discord.Color.gold()
            )

            embed.add_field(
                name="Gym Leader",
                value=gym_leader.name,
                inline=True
            )

            embed.add_field(
                name="Badge",
                value=gym_leader.badge,
                inline=True
            )

            embed.add_field(
                name="Prize Money",
                value=f"${gym_leader.money}",
                inline=True
            )

            # ADD GYM SPRITE
            gym_sprite_path = gym_info['leader'].get('gym_spritePath')
            sprite_file = None

            if gym_sprite_path:
                try:
                    full_sprite_path = get_sprite_path(gym_sprite_path)
                    if os.path.exists(full_sprite_path):
                        filename = os.path.basename(gym_sprite_path)
                        sprite_file = discord.File(full_sprite_path, filename=filename)
                        embed.set_image(url=f"attachment://{filename}")
                except Exception as e:
                    print(f"Error loading gym sprite: {e}")
                    # Fallback to URL
                    sprite_url = f"https://pokesprites.joshkohut.com{gym_sprite_path}"
                    embed.set_image(url=sprite_url)

            view = View()

            # Auto battle button
            auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Battle Leader", custom_id='gym_leader_auto')
            auto_button.callback = self.on_gym_leader_battle_auto
            view.add_item(auto_button)

            # Manual battle button
            manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Battle Leader", custom_id='gym_leader_manual')
            manual_button.callback = self.on_gym_leader_battle_manual
            view.add_item(manual_button)

            # Back button
            back_btn = Button(style=ButtonStyle.primary, label="🗺️ Back", custom_id='gym_back', row=1)
            back_btn.callback = self.on_nav_map_click
            view.add_item(back_btn)

            # Send message with sprite file if available
            if sprite_file:
                new_message = await interaction.followup.send(
                    embed=embed,
                    view=view,
                    file=sprite_file
                )
                try:
                    await interaction.message.delete()
                except:
                    pass
                if str(user.id) in self.__useractions:
                    self.__useractions[str(user.id)].messageId = new_message.id
            else:
                await interaction.message.edit(
                    content=None,
                    embed=embed,
                    view=view
                )

    async def on_gym_leader_battle_manual(self, interaction: discord.Interaction):
        """Handle MANUAL battle with gym leader"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()

        trainer = self._get_trainer(str(user.id))
        location = trainer.getLocation()

        gyms_data = self.__load_gyms_data()
        gym_info = gyms_data.get(str(location.locationId))
        
        battle_manager = BattleClass(str(user.id), location.locationId, enemyType="gym")
        opponent = battle_manager.getGymLeader()
        
        if not opponent or battle_manager.statuscode == 420:
            await interaction.followup.send(
                battle_manager.message if battle_manager.message else 'Cannot challenge gym leader.',
                ephemeral=True
            )
            return

        await self._start_manual_trainer_battle(
            interaction,
            enemy_type="gym",
            opponent=opponent,
            battle_manager=battle_manager,
            sprite_path=gym_info["leader"]["leader_spritePath"],
            is_gym_leader=True,
            gym_name=gym_info["leader"]["gym-name"]
        )


    def __has_pokemart(self, location_id: int) -> bool:
        """Check if the current location has a Pokemart"""
        try:
            store_data = load_json_config('store.json')
            # If locationId exists in store.json, there's a Pokemart
            return str(location_id) in store_data
        except Exception as e:
            return False

    async def __on_action(self, interaction: discord.Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()
        # active = trainer.getActivePokemon()
        state = self.__useractions[str(user.id)]
        wildPokemon = state.wildPokemon
        active = state.activePokemon
        
        location = LocationClass(str(user.id))
        methods: list[ActionModel] = location.getMethods()

        view = View()
        for method in methods:
            color = ButtonStyle.gray
            if method == interaction.data['custom_id']:
                color = ButtonStyle.green
            
            button = Button(style=color, label=f"{method.name}", custom_id=f'{method.value}', disabled=True)
            view.add_item(button)

        # Find the matching action
        action: ActionModel = None
        for method in methods:
            if method.value == interaction.data['custom_id']:
                action = method
                break
        
        # If no matching action found, this button shouldn't have called this method
        if action is None:
            await interaction.followup.send('Invalid action.', ephemeral=True)
            return

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
        elif action.value == 'surf':
            msg = 'Surfing on your pokemon...'
        
        await interaction.message.edit(
            content=msg,
            view=view
        )

        # await interaction.respond(type=5, content="Walking through tall grass...")

        state = self.__useractions[str(user.id)]
        method = interaction.data['custom_id']

        # if method == 'walk':
        trainer = self._get_trainer(str(user.id))


        if ActionType.GIFT.value == action.type.value:
            trainer.gift()
    
            # Get the pokemon that was just received (if successful)
            received_pokemon = None
            if trainer.statuscode == 420 and "received" in trainer.message.lower():
                # Get the pokemon directly from trainer
                if hasattr(trainer, 'lastGiftPokemon') and trainer.lastGiftPokemon:
                    received_pokemon = trainer.lastGiftPokemon
            
            # Create embed for gift result
            sprite_file = None
            if trainer.statuscode == 420:
                # Check if it was successful or already completed
                if "already received" in trainer.message.lower():
                    # Already received gift - show error embed
                    embed = discord.Embed(
                        title="❌ Gift Already Received",
                        description=trainer.message,
                        color=discord.Color.red()
                    )
                else:
                    # Successfully received gift - show success embed
                    embed = discord.Embed(
                        title="🎁 Gift Received!",
                        description=trainer.message,
                        color=discord.Color.green()
                    )
                    
                    # Add pokemon sprite if we got one
                    if received_pokemon:
                        try:
                            # The sprite path is like "/sprites/pokemon/magikarp.png"
                            sprite_path = f"/sprites/pokemon/{received_pokemon.pokemonName}.png"
                            
                            # Convert to full file system path
                            full_sprite_path = get_sprite_path(sprite_path)
                            
                            sprite_file = discord.File(full_sprite_path, filename=f"{received_pokemon.pokemonName}.png")
                            embed.set_image(url=f"attachment://{received_pokemon.pokemonName}.png")
                        except Exception as e:
                            print(f"Error loading pokemon sprite: {e}")
                            # Fallback - no sprite, just show the message
            else:
                # Error occurred
                embed = discord.Embed(
                    title="❌ Error",
                    description=trainer.message,
                    color=discord.Color.red()
                )
            
            embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
            
            # Create navigation view
            nav_view = View()
            
            map_button = Button(style=ButtonStyle.primary, label="🗺️ Map", custom_id='nav_map')
            map_button.callback = self.on_nav_map_click
            nav_view.add_item(map_button)
            
            party_button = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_party')
            party_button.callback = self.on_nav_bag_click
            nav_view.add_item(party_button)
            
            # Check if at Pokemon Center
            location = trainer.getLocation()
            if location.pokecenter:
                heal_button = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal')
                heal_button.callback = self.on_nav_heal_click
                nav_view.add_item(heal_button)
            
            # Edit the message with embed and buttons (include sprite file if we have one)
            if sprite_file:
                await interaction.message.edit(
                    content=None,
                    embed=embed,
                    view=nav_view,
                    attachments=[sprite_file]
                )
            else:
                await interaction.message.edit(
                    content=None,
                    embed=embed,
                    view=nav_view
                )
            
            # Clean up action state
            if str(user.id) in self.__useractions:
                del self.__useractions[str(user.id)]
            
            return
        
        if ActionType.QUEST.value == action.type.value:
            trainer.quest(interaction.data['custom_id'])
            await interaction.followup.send(trainer.message, ephemeral=True)
            return


        wildPokemon: PokemonClass
        # Only one can potentially trigger a pokemon encounter
        if ActionType.ONLYONE.value == action.type.value:
            wildPokemon = trainer.onlyone()
            if wildPokemon is None:
                if trainer.statuscode == 420:
                    # Create error embed with navigation buttons
                    embed = discord.Embed(
                        title="❌ Cannot Perform Action",
                        description=trainer.message,
                        color=discord.Color.red()
                    )
                    embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
                    
                    # Create navigation view
                    view = View()
                    
                    map_button = Button(style=ButtonStyle.primary, label="🗺️ Map", custom_id='nav_map')
                    map_button.callback = self.on_nav_map_click
                    view.add_item(map_button)
                    
                    party_button = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_party')
                    party_button.callback = self.on_nav_bag_click
                    view.add_item(party_button)
                    
                    # Check if at Pokemon Center
                    location = trainer.getLocation()
                    if location.pokecenter:
                        heal_button = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal')
                        heal_button.callback = self.on_nav_heal_click
                        view.add_item(heal_button)
                    
                    # Edit the message with embed and buttons
                    await interaction.message.edit(
                        content=None,
                        embed=embed,
                        view=view
                    )
                    
                    # Clean up action state
                    if str(user.id) in self.__useractions:
                        del self.__useractions[str(user.id)]
                else:
                    await interaction.followup.send('No pokemon encountered.', ephemeral=True)
                return


            # await interaction.channel.send(trainer.message)

        # A wild pokemon encounter
        # A wild pokemon encounter
        if ActionType.ENCOUNTER.value == action.type.value:
            wildPokemon = trainer.encounter(method)
            if wildPokemon is None:
                if trainer.statuscode == 420:
                    # Create error embed with navigation buttons
                    embed = discord.Embed(
                        title="❌ Cannot Use This Method",
                        description=trainer.message,
                        color=discord.Color.red()
                    )
                    embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
                    
                    # Create navigation view
                    view = View()
                    
                    map_button = Button(style=ButtonStyle.primary, label="🗺️ Map", custom_id='nav_map')
                    map_button.callback = self.on_nav_map_click
                    view.add_item(map_button)
                    
                    party_button = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_party')
                    party_button.callback = self.on_nav_bag_click
                    view.add_item(party_button)
                    
                    # Check if at Pokemon Center
                    location = trainer.getLocation()
                    if location.pokecenter:
                        heal_button = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal')
                        heal_button.callback = self.on_nav_heal_click
                        view.add_item(heal_button)
                    
                    # Edit the message with embed and buttons
                    await interaction.message.edit(
                        content=None,
                        embed=embed,
                        view=view
                    )
                    
                    # Clean up action state
                    if str(user.id) in self.__useractions:
                        del self.__useractions[str(user.id)]
                else:
                    await interaction.followup.send('No pokemon encountered.', ephemeral=True)
                return
            
            # Check if this is a shiny encounter and send notification
            if hasattr(trainer, 'encountered_shiny') and trainer.encountered_shiny:
                # Send ephemeral shiny notification
                shiny_embed = discord.Embed(
                    title="✨ SHINY POKEMON! ✨",
                    description=f"You found a **SHINY {wildPokemon.pokemonName.upper()}**!\n\n⭐ Only one of these can be owned on this server at a time!",
                    color=discord.Color.gold()
                )
                shiny_embed.set_thumbnail(url=wildPokemon.frontSpriteURL)
                await interaction.followup.send(embed=shiny_embed, ephemeral=True)

        # active = trainer.getActivePokemon()
        # Get battle-ready Pokemon (active if alive, otherwise first alive party member)
        active = self.__get_battle_ready_pokemon(str(user.id), state.activePokemon)
        if active is None:
            await interaction.followup.send('All your Pokemon have fainted! Heal at a Pokemon Center first.', ephemeral=True)
            if str(user.id) in self.__useractions:
                del self.__useractions[str(user.id)]
            return

        desc = f'''
        {user.display_name} encountered a wild {wildPokemon.pokemonName.capitalize()}!
        {user.display_name} sent out {getTrainerGivenPokemonName(active)}.
        '''

        embed = self.__wildPokemonEncounter(user, wildPokemon, active, desc)

        view = View()

        # Auto Fight button
        auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Fight", custom_id='wild_auto_fight')
        auto_button.callback = self.on_wild_auto_fight_click
        view.add_item(auto_button)

        # Manual Fight button
        manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Fight", custom_id='wild_manual_fight')
        manual_button.callback = self.on_wild_manual_fight_click
        view.add_item(manual_button)

        # Run away button
        run_button = Button(style=ButtonStyle.danger, label="🏃 Run Away", custom_id='wild_run_away')
        run_button.callback = self.on_runaway_click_encounter
        view.add_item(run_button)

        # Catch button
        catch_button = Button(style=ButtonStyle.success, label="🔴 Catch", custom_id='wild_catch')
        catch_button.callback = self.on_catch_click_encounter
        view.add_item(catch_button)

        message = await interaction.message.edit(
            embed=embed,
            view=view
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, active, wildPokemon, desc)


    async def on_wild_manual_fight_click(self, interaction: discord.Interaction):
        """Handle MANUAL fight with wild Pokemon - new battle interface"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()

        state = self.__useractions[str(user.id)]
        
        # Get battle-ready Pokemon (active if alive, otherwise first alive party member)
        active_pokemon = self.__get_battle_ready_pokemon(str(user.id), state.activePokemon)
        if active_pokemon is None:
            await interaction.followup.send('All your Pokemon have fainted! Heal at a Pokemon Center first.', ephemeral=True)
            del self.__useractions[str(user.id)]
            return
        
        # Create wild battle state
        wild_battle_state = WildBattleState(
            user_id=str(user.id),
            channel_id=interaction.channel_id,
            message_id=0,
            player_pokemon=active_pokemon,
            wild_pokemon=state.wildPokemon
        )
        
        # Initialize ailments for manual battle
        wild_battle_state.player_ailment = AilmentClass(active_pokemon.trainerId)
        wild_battle_state.player_ailment.load()  # Load any pre-existing ailments
        wild_battle_state.enemy_ailment = AilmentClass('wild_enemy')  # Fresh, no ailments

        # Store in wild battle states dict
        self.__wild_battle_states[str(user.id)] = wild_battle_state
        
        # Create battle embed and move buttons
        embed = self.__create_wild_battle_embed(user, wild_battle_state)
        view = self.__create_battle_move_buttons_with_items(wild_battle_state)
        
        # Update the existing message with battle interface
        message = await interaction.message.edit(
            content=f"**Wild Battle Started!**",
            embed=embed,
            view=view
        )
        
        wild_battle_state.message_id = message.id
        
        # Clean up old action state since we're now in battle state
        del self.__useractions[str(user.id)]




    async def on_wild_auto_fight_click(self, interaction: discord.Interaction):
        """Handle AUTO fight with wild Pokemon - old auto-battle system with nice embeds"""
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        await interaction.response.defer()

        state = self.__useractions[str(user.id)]
        trainer = self._get_trainer(str(user.id))

        # Get battle-ready Pokemon (active if alive, otherwise first alive party member)
        battle_pokemon = self.__get_battle_ready_pokemon(str(user.id), state.activePokemon)
        if battle_pokemon is None:
            await interaction.followup.send('All your Pokemon have fainted! Heal at a Pokemon Center first.', ephemeral=True)
            del self.__useractions[str(user.id)]
            return

        # Run the fight directly with battle-ready Pokemon (bypasses trainer.fight which always uses DB active)
        enc = EncounterClass(battle_pokemon, state.wildPokemon)
        retVal = enc.fight()

        if enc.statuscode == 96:
            await interaction.followup.send(enc.message, ephemeral=True)
            return

        # Reload battle pokemon to get updated HP after fight
        battle_pokemon.load(pokemonId=battle_pokemon.trainerId)
        
        # Determine if victory or defeat
        is_victory = battle_pokemon.currentHP > 0
        
        # Create appropriate embed
        if is_victory:
            # LEADERBOARD TRACKING
            from services.leaderboardclass import leaderboard as LeaderboardClass
            lb = LeaderboardClass(str(user.id))
            lb.victory()
            lb.actions()

            # VICTORY EMBED
            player_stats = battle_pokemon.getPokeStats()
            player_max_hp = player_stats['hp']
            
            embed = discord.Embed(
                title="🎉 Victory!",
                description=f"You defeated the wild {state.wildPokemon.pokemonName.capitalize()}!",
                color=discord.Color.green()
            )
            
            player_summary = []
            player_summary.append(f"**{battle_pokemon.pokemonName.capitalize()}** (Lv.{battle_pokemon.currentLevel})")
            player_summary.append(f"HP: {battle_pokemon.currentHP}/{player_max_hp}")
            
            embed.add_field(
                name="💚 Your Pokemon",
                value="\n".join(player_summary),
                inline=True
            )
            
            # Add exp info if available
            if enc.message:
                embed.add_field(
                    name="📊 Experience",
                    value=enc.message,
                    inline=False
                )
        else:
            # DEFEAT EMBED
            player_stats = battle_pokemon.getPokeStats()
            player_max_hp = player_stats['hp']
            
            embed = discord.Embed(
                title="💀 Defeat...",
                description=f"You were defeated by the wild {state.wildPokemon.pokemonName.capitalize()}!",
                color=discord.Color.red()
            )
            
            player_summary = []
            player_summary.append(f"**{battle_pokemon.pokemonName.capitalize()}** (Lv.{battle_pokemon.currentLevel})")
            player_summary.append(f"HP: 0/{player_max_hp} ❌")
            
            embed.add_field(
                name="💚 Your Pokemon",
                value="\n".join(player_summary),
                inline=True
            )
            
            # Add battle result message
            embed.add_field(
                name="⚔️ Battle Result",
                value="Your Pokemon fainted!",
                inline=False
            )
        
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        
        # ADD NAVIGATION BUTTONS after battle
        view = View()
        
        map_button = Button(style=ButtonStyle.primary, label="🗺️ Map", custom_id='nav_map')
        map_button.callback = self.on_nav_map_click
        view.add_item(map_button)
        
        party_button = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_party')
        party_button.callback = self.on_nav_bag_click
        view.add_item(party_button)
        
        # Check if at Pokemon Center
        location = trainer.getLocation()
        if location.pokecenter:
            heal_button = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal')
            heal_button.callback = self.on_nav_heal_click
            view.add_item(heal_button)

        await interaction.message.edit(
            content=None,
            embed=embed,
            view=view
        )
        
        del self.__useractions[str(user.id)]


    async def __on_fight_click_encounter(self, interaction: Interaction):
        """Redirect to manual fight (kept for compatibility)"""
        await self.on_wild_manual_fight_click(interaction)


    async def __on_runaway_click_encounter(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()
        state = self.__useractions[str(user.id)]
        trainer = self._get_trainer(str(user.id))
        trainer.runAway(state.wildPokemon)

        if trainer.statuscode == 96:
            await interaction.followup.send(trainer.message, ephemeral=True)
            return

        desc = state.descLog
        desc += f'''{user.display_name} chose to run away.
    {trainer.message}
    '''

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, state.activePokemon, desc)

        # ADD NAVIGATION BUTTONS (same as catch)
        view = View()
        
        map_button = Button(style=ButtonStyle.primary, label="🗺️ Map", custom_id='nav_map')
        map_button.callback = self.on_nav_map_click
        view.add_item(map_button)
        
        party_button = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_party')
        party_button.callback = self.on_nav_bag_click
        view.add_item(party_button)
        
        # Check if at Pokemon Center
        location = trainer.getLocation()
        if location.pokecenter:
            heal_button = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal')
            heal_button.callback = self.on_nav_heal_click
            view.add_item(heal_button)

        await interaction.message.edit(
            embed=embed,
            view=view  # Changed from View() to view with buttons
        )
        
        del self.__useractions[str(user.id)]
        

    async def __on_catch_click_encounter(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        await interaction.response.defer()
        state = self.__useractions[str(user.id)]
        trainer = self._get_trainer(str(user.id))
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
        # Get battle-ready Pokemon (active if alive, otherwise first alive party member)
        active = self.__get_battle_ready_pokemon(str(user.id), state.activePokemon)
        if active is None:
            await interaction.followup.send('All your Pokemon have fainted! Heal at a Pokemon Center first.', ephemeral=True)
            if str(user.id) in self.__useractions:
                del self.__useractions[str(user.id)]
            return

        desc = f'''
        {user.display_name} encountered a wild {wildPokemon.pokemonName.capitalize()}!
        {user.display_name} sent out {getTrainerGivenPokemonName(active)}.
        '''

        embed = self.__wildPokemonEncounter(user, wildPokemon, active, desc)

        view = View()

        # Auto Fight button
        auto_button = Button(style=ButtonStyle.gray, label="⚡ Auto Fight", custom_id='wild_auto_fight')
        auto_button.callback = self.on_wild_auto_fight_click
        view.add_item(auto_button)

        # Manual Fight button
        manual_button = Button(style=ButtonStyle.green, label="🎮 Manual Fight", custom_id='wild_manual_fight')
        manual_button.callback = self.on_wild_manual_fight_click
        view.add_item(manual_button)

        # Run away button
        run_button = Button(style=ButtonStyle.danger, label="🏃 Run Away", custom_id='wild_run_away')
        run_button.callback = self.on_runaway_click_encounter
        view.add_item(run_button)

        # Catch button
        catch_button = Button(style=ButtonStyle.success, label="🔴 Catch", custom_id='wild_catch')
        catch_button.callback = self.on_catch_click_encounter
        view.add_item(catch_button)

        message = await interaction.message.edit(
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
        trainer = self._get_trainer(str(user.id))

        # Determine which ball was thrown
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

        # CREATE NAVIGATION BUTTONS BASED ON RESULT
        # statuscode 420 = success OR failure (both end the encounter)
        # statuscode 96 = also ends encounter
        # Either way, add navigation buttons
        view = View()
        
        map_button = Button(style=ButtonStyle.primary, label="🗺️ Map", custom_id='nav_map')
        map_button.callback = self.on_nav_map_click
        view.add_item(map_button)
        
        party_button = Button(style=ButtonStyle.primary, label="🎒 Bag", custom_id='nav_party')
        party_button.callback = self.on_nav_bag_click
        view.add_item(party_button)
        
        # Check if at Pokemon Center
        location = trainer.getLocation()
        if location.pokecenter:
            heal_button = Button(style=ButtonStyle.green, label="🏥 Heal", custom_id='nav_heal')
            heal_button.callback = self.on_nav_heal_click
            view.add_item(heal_button)

        await interaction.message.edit(
            embed=embed,
            view=view  # Changed from View() to view with buttons
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
