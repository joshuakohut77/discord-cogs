# encounter class
import os
import sys
import config
import json
import random
from datetime import datetime

from dbclass import db as dbconn
from expclass import experiance as exp
from inventoryclass import inventory as inv
from leaderboardclass import leaderboard
from loggerclass import logger as log
from uniqueencounters import uniqueEncounters as uEnc
from pokedexclass import pokedex
from pokeclass import Pokemon as PokemonClass
from ailmentsclass import ailment 
from typing import TYPE_CHECKING

# if TYPE_CHECKING:
from .trainerclass import trainer as trainer_import

# Global Config Variables
MAX_BATTLE_TURNS = 50
# MAX_BATTLE_TURNS = config.max_battle_turns
# Class Logger
logger = log()

# Export list for module
__all__ = ['encounter', 'calculate_battle_damage']

# this class is to handle encounters with pokemon.
class encounter:
    pokemon1: PokemonClass
    pokemon2: PokemonClass

    def __init__(self, pokemon1: PokemonClass, pokemon2: PokemonClass):
        # pokemon1 for PvE will always be the discord trainers pokemon
        self.statuscode = 69
        self.message = ''

        self.battle_log = []  # Track battle turn-by-turn
        self.pokemon1 = pokemon1
        self.pokemon2 = pokemon2
        self.ailment1 = ailment(pokemon1.trainerId)
        self.ailment2 = ailment(pokemon2.trainerId)
        self.ailment1.load()
        pokedex(self.pokemon1.discordId, pokemon2)

    def trade(self):
        """
        Trades pokemon between two trainers.
        Returns (retVal1, retVal2) - messages for each trainer.
        retVal1 = message for the person RECEIVING pokemon1
        retVal2 = message for the person RECEIVING pokemon2
        
        Also returns evolution info via self.trade_evolution_info dict:
        {
            'pokemon1_evolved': bool,
            'pokemon1_original': str or None,
            'pokemon1_evolved_into': str or None,
            'pokemon2_evolved': bool,
            'pokemon2_original': str or None,
            'pokemon2_evolved_into': str or None,
        }
        """
        discordId1 = self.pokemon1.discordId
        discordId2 = self.pokemon2.discordId
        retVal1 = ""
        retVal2 = ""
        
        # Track evolution info for the UI
        self.trade_evolution_info = {
            'pokemon1_evolved': False,
            'pokemon1_original': None,
            'pokemon1_evolved_into': None,
            'pokemon2_evolved': False,
            'pokemon2_original': None,
            'pokemon2_evolved_into': None,
        }
        
        # Check trade evolution for pokemon1
        # pokemon1 is being sent FROM discordId1 TO discordId2
        evolvedPokemon = self.checkTradeEvolution(self.pokemon1)
        if evolvedPokemon is not None:
            originalName = self.pokemon1.pokemonName
            self.pokemon1.release()
            self.pokemon1 = evolvedPokemon
            self.trade_evolution_info['pokemon1_evolved'] = True
            self.trade_evolution_info['pokemon1_original'] = originalName
            self.trade_evolution_info['pokemon1_evolved_into'] = evolvedPokemon.pokemonName
            retVal1 = f"You traded for a {originalName.capitalize()}, but it evolved into {evolvedPokemon.pokemonName.capitalize()}! "

        # Check trade evolution for pokemon2
        # pokemon2 is being sent FROM discordId2 TO discordId1
        evolvedPokemon = self.checkTradeEvolution(self.pokemon2)
        if evolvedPokemon is not None:
            originalName = self.pokemon2.pokemonName
            self.pokemon2.release()
            self.pokemon2 = evolvedPokemon
            self.trade_evolution_info['pokemon2_evolved'] = True
            self.trade_evolution_info['pokemon2_original'] = originalName
            self.trade_evolution_info['pokemon2_evolved_into'] = evolvedPokemon.pokemonName
            retVal2 = f"You traded for a {originalName.capitalize()}, but it evolved into {evolvedPokemon.pokemonName.capitalize()}! "
        
        if not self.trade_evolution_info['pokemon1_evolved']:
            retVal1 += "You received %s" % self.pokemon1.pokemonName.capitalize()
        else:
            retVal1 += "You received %s" % self.pokemon1.pokemonName.capitalize()
        
        if not self.trade_evolution_info['pokemon2_evolved']:
            retVal2 += "You received %s" % self.pokemon2.pokemonName.capitalize()
        else:
            retVal2 += "You received %s" % self.pokemon2.pokemonName.capitalize()

        # Swap ownership
        self.pokemon1.discordId = discordId2
        self.pokemon2.discordId = discordId1
        self.pokemon1.traded = True
        self.pokemon2.traded = True

        self.pokemon1.save()
        self.pokemon2.save()

        # Leaderboard: trades for BOTH trainers
        lb1 = leaderboard(discordId1)
        lb1.trades()
        lb2 = leaderboard(discordId2)
        lb2.trades()

        # Pokedex: register the pokemon each trainer is RECEIVING
        # discordId2 receives pokemon1, discordId1 receives pokemon2
        pokedex(discordId2, self.pokemon1)
        pokedex(discordId1, self.pokemon2)

        return retVal1, retVal2

    def checkTradeEvolution(self, pokemon):
        """
        Checks if a pokemon evolves during a trade and returns new pokemon if it does.
        Handles: party status, active pokemon, pokedex, leaderboard evolution stat.
        Returns the evolved PokemonClass or None.
        """
        tradedEvoList = ['kadabra', 'machoke', 'graveler', 'haunter', 'missing-chode']
        evolvedPokemon = None
        
        if pokemon.pokemonName in tradedEvoList:
            if pokemon.pokemonName == 'kadabra':
                newPokemon = 'alakazam'
            elif pokemon.pokemonName == 'machoke':
                newPokemon = 'machamp'
            elif pokemon.pokemonName == 'graveler':
                newPokemon = 'golem'
            elif pokemon.pokemonName == 'haunter':
                newPokemon = 'gengar'
            elif pokemon.pokemonName == 'missing-chode':
                newPokemon = 'giant-chode'
            
            # Store old pokemon info before evolution
            oldPartyStatus = pokemon.party
            wasActivePokemon = False
            try:
                db = dbconn()
                queryString = 'SELECT "activePokemon" FROM trainer WHERE "discord_id" = %(discordId)s'
                result = db.querySingle(queryString, {'discordId': pokemon.discordId})
                if result and result[0] == pokemon.trainerId:
                    wasActivePokemon = True
            except:
                logger.error(excInfo=sys.exc_info())
            finally:
                del db
            
            # Create the evolved pokemon
            evolvedPokemon = PokemonClass(pokemon.discordId, newPokemon)
            evolvedPokemon.create(pokemon.currentLevel, is_shiny=pokemon.is_shiny)

            if evolvedPokemon.statuscode == 96:
                logger.error("Error creating evolved trade Pokemon during create()")
                return None

            # Transfer moves from pre-evolution
            evolvedPokemon.move_1 = pokemon.move_1
            evolvedPokemon.move_2 = pokemon.move_2
            evolvedPokemon.move_3 = pokemon.move_3
            evolvedPokemon.move_4 = pokemon.move_4

            # Set party status from original
            evolvedPokemon.party = oldPartyStatus

            # Save to get its trainerId
            evolvedPokemon.save()
            
            if evolvedPokemon.statuscode == 96:
                logger.error("Error creating evolved trade Pokemon")
                return None
            
            # If this was the active pokemon, update trainer's active pokemon
            if wasActivePokemon:
                try:
                    db = dbconn()
                    updateString = 'UPDATE trainer SET "activePokemon" = %(trainerId)s WHERE "discord_id" = %(discordId)s'
                    db.execute(updateString, {'trainerId': evolvedPokemon.trainerId, 'discordId': pokemon.discordId})
                except:
                    logger.error(excInfo=sys.exc_info())
                finally:
                    del db
            
            # Register evolved form to Pokedex (owner is still original trainer at this point)
            pokedex(pokemon.discordId, evolvedPokemon)
            
            # Leaderboard: evolution stat
            lb = leaderboard(pokemon.discordId)
            lb.evolved()

        return evolvedPokemon

    def fight(self, battleType='auto', move=''):
        """ two pokemon fight and a outcome is decided """
        # two pokemon fight with an outcome calling victory or defeat
        # todo update with better fight outcome algorithm
        if self.pokemon1.currentHP == 0:
            self.statuscode = 420
            self.message = "Your active Pokemon has no HP left!"
            return

        if battleType == 'auto':
            retVal = self.battle_fight(move1=None)
        else:
            retVal = self.battle_fight(move1=move)
        self.statuscode = 420
        return retVal

 

    def battle_fight(self, move1):
        """ main pokemon battle method with special move + stat stage support """
        retVal = {'result': None}
        battleHP1 = self.pokemon1.currentHP
        battleHP2 = self.pokemon2.currentHP
        
        if move1:
            battleMoves1 = [move1]
        else:
            battleMoves1 = self.__removeNullMoves(self.pokemon1.getMoves())
        battleMoves2 = self.__removeNullMoves(self.pokemon2.getMoves())

        statusMovesCount = 0
        turn_number = 1

        # Special move tracking
        rest_turns_1 = 0
        rest_turns_2 = 0
        leech_seed_1 = False
        leech_seed_2 = False

        # Stat stage tracking
        from helpers.statstages import StatStages, apply_stat_change, apply_secondary_stat_change
        from helpers.specialmoves import (
            handle_rest, handle_recover, calculate_drain_heal,
            calculate_night_shade_damage, calculate_leech_seed_damage,
            check_accuracy, handle_haze
        )
        stat_stages_1 = StatStages()  # Player
        stat_stages_2 = StatStages()  # Enemy

        p1_stats = self.pokemon1.getPokeStats()
        p2_stats = self.pokemon2.getPokeStats()
        p1_max_hp = p1_stats['hp']
        p2_max_hp = p2_stats['hp']
        
        if move1 == None:
            max_battle_turns = MAX_BATTLE_TURNS
        else:
            max_battle_turns = 1
        
        for x in range(max_battle_turns):
            self.battle_log.append(f"**Turn {turn_number}:**")

            # =================================================================
            # POKEMON 1'S TURN (Player)
            # =================================================================
            p1_skip_turn = False
            if rest_turns_1 > 0:
                rest_turns_1 -= 1
                if rest_turns_1 == 0:
                    self.battle_log.append(f'💤 {self.pokemon1.pokemonName.capitalize()} woke up from Rest!')
                else:
                    self.battle_log.append(f'💤 {self.pokemon1.pokemonName.capitalize()} is sleeping from Rest!')
                p1_skip_turn = True

            if not p1_skip_turn:
                if move1 == None:
                    # Smart move selection for auto-battle:
                    # Separate moves into damaging and non-damaging
                    damaging_moves = []
                    non_damaging_moves = []
                    for m in battleMoves1:
                        mData = self.__loadMovesConfig(m)
                        if mData.get('power') is not None and mData['power'] > 0:
                            damaging_moves.append(m)
                        else:
                            non_damaging_moves.append(m)
                    
                    # Prefer damaging moves: 85% chance if available, 
                    # allow 1 non-damaging move per battle
                    use_damaging = True
                    if non_damaging_moves and statusMovesCount < 1 and random.random() < 0.15:
                        use_damaging = False
                    
                    if use_damaging and damaging_moves:
                        move1 = random.choice(damaging_moves)
                    elif non_damaging_moves and statusMovesCount < 1:
                        move1 = random.choice(non_damaging_moves)
                        statusMovesCount += 1
                    elif damaging_moves:
                        move1 = random.choice(damaging_moves)
                    else:
                        # Fallback: all moves are non-damaging, just pick one
                        move1 = random.choice(battleMoves1)
                    
                    pbMove = self.__loadMovesConfig(move1)
                    special_fn = pbMove.get('special_function', '')
                    has_stat_change = 'stat_change' in pbMove
                else:
                    pbMove = self.__loadMovesConfig(move1)
                    special_fn = pbMove.get('special_function', '')
                    has_stat_change = 'stat_change' in pbMove

                modifiedPokemon1, attackViability = self.ailment1.calculateAilmentDamage(self.pokemon1)
                move_display = move1.replace("-", " ").title()

                if self.ailment2.trap:
                    self.battle_log.append(f'{self.pokemon2.pokemonName.capitalize()} is still trapped')
                
                if not attackViability and not self.ailment2.trap:
                    # Pokemon CAN attack

                    # --- STAT CHANGE MOVES ---
                    if has_stat_change and not special_fn:
                        self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used {move_display}!')
                        apply_stat_change(
                            pbMove, stat_stages_1, stat_stages_2,
                            self.battle_log,
                            self.pokemon1.pokemonName.capitalize(),
                            f'Enemy {self.pokemon2.pokemonName.capitalize()}'
                        )

                    # --- HAZE ---
                    elif special_fn == 'haze':
                        handle_haze(stat_stages_1, stat_stages_2)
                        self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Haze! All stat changes were eliminated!')

                    # --- REST ---
                    elif special_fn == 'rest':
                        heal_amount, new_hp = handle_rest(battleHP1, p1_max_hp)
                        battleHP1 = new_hp
                        rest_turns_1 = 2
                        self.ailment1.resetAilments()
                        self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Rest! Recovered {heal_amount} HP and fell asleep! 💤')

                    elif special_fn == 'recover':
                        actual_heal, new_hp = handle_recover(battleHP1, p1_max_hp)
                        battleHP1 = new_hp
                        self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Recover! Restored {actual_heal} HP! 💚')

                    elif special_fn == 'night_shade':
                        if check_accuracy(pbMove.get('accuracy', 100)):
                            ns_damage = calculate_night_shade_damage(self.pokemon1.currentLevel)
                            battleHP2 -= ns_damage
                            self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Night Shade! Dealt {ns_damage} damage!')
                        else:
                            self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Night Shade but it missed!')

                    elif special_fn == 'leech_seed':
                        if check_accuracy(pbMove.get('accuracy', 100)):
                            leech_seed_2 = True
                            self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Leech Seed! Enemy was seeded! 🌱')
                        else:
                            self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Leech Seed but it missed!')

                    elif special_fn == 'dream_eater':
                        if self.ailment2.sleep or rest_turns_2 > 0:
                            damage = self.__calculateDamageOfMove(pbMove, stat_stages_1, stat_stages_2)
                            if damage > 0:
                                battleHP2 -= damage
                                drain_heal = calculate_drain_heal(damage)
                                battleHP1 = min(p1_max_hp, battleHP1 + drain_heal)
                                self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Dream Eater! Dealt {damage} damage and drained {drain_heal} HP! 💜')
                            else:
                                self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Dream Eater but it missed!')
                        else:
                            self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used Dream Eater but it failed! Target is not asleep.')

                    elif special_fn == 'drain':
                        damage = self.__calculateDamageOfMove(pbMove, stat_stages_1, stat_stages_2)
                        if damage > 0:
                            battleHP2 -= damage
                            drain_heal = calculate_drain_heal(damage)
                            battleHP1 = min(p1_max_hp, battleHP1 + drain_heal)
                            self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used {move_display}! Dealt {damage} damage and drained {drain_heal} HP! 💚')
                        else:
                            self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used {move_display} but it missed!')

                    else:
                        # --- NORMAL MOVE ---
                        damage = self.__calculateDamageOfMove(pbMove, stat_stages_1, stat_stages_2)
                        isAilment2 = self.ailment2.rollAilmentChance(pbMove)
                        if isAilment2:
                            self.ailment2.setAilment(pbMove['ailment'])
                        battleHP2 -= damage
                        self.battle_log.append(f'• {self.pokemon1.pokemonName.capitalize()} used {move_display}! Dealt {damage} damage.')

                        # Secondary stat change on damaging moves
                        if damage > 0:
                            apply_secondary_stat_change(
                                pbMove, stat_stages_1, stat_stages_2,
                                self.battle_log,
                                self.pokemon1.pokemonName.capitalize(),
                                f'Enemy {self.pokemon2.pokemonName.capitalize()}'
                            )
                    
                    if battleHP2 <= 0:
                        self.pokemon1.currentHP = battleHP1
                        self.__victory()
                        self.statuscode = 420
                        retVal = {'result': 'victory'}
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} fainted!')
                        break
                    
                    if pbMove['moveType'] == 'fire' and self.ailment2.freeze:
                        self.battle_log.append(f'{self.pokemon2.pokemonName.capitalize()} is no longer frozen')
                        self.ailment2.freeze = False
                else:
                    if not self.ailment2.trap:
                        self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} has an ailment preventing it from attacking!')
                    
                    enemyMove = ''
                    if self.ailment1.trap:
                        self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is trapped!')
                        pbMove = self.__loadMovesConfig('bind')
                        trapDamage = self.__calculateDamageOfMove(pbMove, attacker=self.pokemon2, defender=self.pokemon1, stat_stages_attacker=stat_stages_2, stat_stages_defender=stat_stages_1)
                        self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} took {trapDamage} trap damage')
                        battleHP1 -= trapDamage
                    elif self.ailment1.confusion:
                        self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is confused!')
                        if random.randrange(1, 1+1) == 1:
                            pbMove = self.__loadMovesConfig('tackle')
                            confusionDamage = self.__calculateDamageOfMove(pbMove, attacker=self.pokemon2, defender=self.pokemon2)
                            battleHP1 -= confusionDamage
                            self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} hurt itself in confusion! {confusionDamage} damage.')
                    elif self.ailment1.sleep:
                        self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is asleep!')
                    elif self.ailment1.freeze:
                        self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is frozen!')
                    
                    if battleHP1 <= 0:
                        self.__defeat()
                        self.statuscode = 420
                        retVal = {'result': 'defeat'}
                        self.battle_log.append(f'Your {self.pokemon1.pokemonName.capitalize()} fainted!')
                        return retVal
                
                if battleHP2 <= 0:
                    self.pokemon1.currentHP = battleHP1
                    self.__victory()
                    self.statuscode = 420
                    retVal = {'result': 'victory'}
                    break
            
                elif battleHP2 > 0:
                    if self.ailment1.burn or self.ailment1.poison:
                        self.pokemon1.currentHP = modifiedPokemon1.currentHP
                        battleHP1 = modifiedPokemon1.currentHP
                        if self.ailment1.burn:
                            self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is hurt by burn!')
                        else:
                            self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is hurt by poison!')
                        if battleHP1 <= 0:
                            self.__defeat()
                            self.statuscode = 420
                            retVal = {'result': 'defeat'}
                            self.battle_log.append(f'Your {self.pokemon1.pokemonName.capitalize()} fainted!')
                            return retVal

            # =================================================================
            # POKEMON 2'S TURN (Enemy)
            # =================================================================
            p2_skip_turn = False
            if rest_turns_2 > 0:
                rest_turns_2 -= 1
                if rest_turns_2 == 0:
                    self.battle_log.append(f'💤 Enemy {self.pokemon2.pokemonName.capitalize()} woke up from Rest!')
                else:
                    self.battle_log.append(f'💤 Enemy {self.pokemon2.pokemonName.capitalize()} is sleeping from Rest!')
                p2_skip_turn = True

            if not p2_skip_turn:
                randMoveSelector = random.randrange(1, len(battleMoves2)+1)
                move2 = battleMoves2[randMoveSelector-1]
                pbMove = self.__loadMovesConfig(move2)
                enemy_special_fn = pbMove.get('special_function', '')
                enemy_has_stat_change = 'stat_change' in pbMove
                move2_display = move2.replace("-", " ").title()

                modifiedPokemon2, attackViability = self.ailment2.calculateAilmentDamage(self.pokemon2)
                
                if self.ailment1.trap:
                    self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is still trapped')
                
                if not attackViability and not self.ailment1.trap:
                    # Enemy CAN attack

                    if enemy_has_stat_change and not enemy_special_fn:
                        self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used {move2_display}!')
                        apply_stat_change(
                            pbMove, stat_stages_2, stat_stages_1,
                            self.battle_log,
                            f'Enemy {self.pokemon2.pokemonName.capitalize()}',
                            self.pokemon1.pokemonName.capitalize()
                        )

                    elif enemy_special_fn == 'haze':
                        handle_haze(stat_stages_1, stat_stages_2)
                        self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Haze! All stat changes were eliminated!')

                    elif enemy_special_fn == 'rest':
                        heal_amount, new_hp = handle_rest(battleHP2, p2_max_hp)
                        battleHP2 = new_hp
                        rest_turns_2 = 2
                        self.ailment2.resetAilments()
                        self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Rest! Recovered {heal_amount} HP and fell asleep! 💤')

                    elif enemy_special_fn == 'recover':
                        actual_heal, new_hp = handle_recover(battleHP2, p2_max_hp)
                        battleHP2 = new_hp
                        self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Recover! Restored {actual_heal} HP! 💚')

                    elif enemy_special_fn == 'night_shade':
                        if check_accuracy(pbMove.get('accuracy', 100)):
                            ns_damage = calculate_night_shade_damage(self.pokemon2.currentLevel)
                            battleHP1 -= ns_damage
                            self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Night Shade! Dealt {ns_damage} damage!')
                        else:
                            self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Night Shade but it missed!')

                    elif enemy_special_fn == 'leech_seed':
                        if check_accuracy(pbMove.get('accuracy', 100)):
                            leech_seed_1 = True
                            self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Leech Seed! Your Pokemon was seeded! 🌱')
                        else:
                            self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Leech Seed but it missed!')

                    elif enemy_special_fn == 'dream_eater':
                        if self.ailment1.sleep or rest_turns_1 > 0:
                            damage = self.__calculateDamageOfMove(pbMove, attacker=self.pokemon2, defender=self.pokemon1, stat_stages_attacker=stat_stages_2, stat_stages_defender=stat_stages_1)
                            if damage > 0:
                                battleHP1 -= damage
                                drain_heal = calculate_drain_heal(damage)
                                battleHP2 = min(p2_max_hp, battleHP2 + drain_heal)
                                self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Dream Eater! Dealt {damage} damage and drained {drain_heal} HP! 💜')
                            else:
                                self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Dream Eater but it missed!')
                        else:
                            self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used Dream Eater but it failed! Target is not asleep.')

                    elif enemy_special_fn == 'drain':
                        damage = self.__calculateDamageOfMove(pbMove, attacker=self.pokemon2, defender=self.pokemon1, stat_stages_attacker=stat_stages_2, stat_stages_defender=stat_stages_1)
                        if damage > 0:
                            battleHP1 -= damage
                            drain_heal = calculate_drain_heal(damage)
                            battleHP2 = min(p2_max_hp, battleHP2 + drain_heal)
                            self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used {move2_display}! Dealt {damage} damage and drained {drain_heal} HP! 💚')
                        else:
                            self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used {move2_display} but it missed!')

                    else:
                        # --- NORMAL ENEMY MOVE ---
                        damage = self.__calculateDamageOfMove(pbMove, attacker=self.pokemon2, defender=self.pokemon1, stat_stages_attacker=stat_stages_2, stat_stages_defender=stat_stages_1)
                        isAilment1 = self.ailment1.rollAilmentChance(pbMove)
                        if isAilment1:
                            self.ailment1.setAilment(pbMove['ailment'])
                        battleHP1 -= damage
                        self.battle_log.append(f'• Enemy {self.pokemon2.pokemonName.capitalize()} used {move2_display}! Dealt {damage} damage.')

                        if damage > 0:
                            apply_secondary_stat_change(
                                pbMove, stat_stages_2, stat_stages_1,
                                self.battle_log,
                                f'Enemy {self.pokemon2.pokemonName.capitalize()}',
                                self.pokemon1.pokemonName.capitalize()
                            )

                else:
                    if not self.ailment1.trap:
                        self.battle_log.append(f'{self.pokemon2.pokemonName.capitalize()} has an ailment preventing it from attacking!')
                    
                    if self.ailment2.trap:
                        pbMove = self.__loadMovesConfig('bind')
                        trapDamage = self.__calculateDamageOfMove(pbMove, attacker=self.pokemon1, defender=self.pokemon2, stat_stages_attacker=stat_stages_1, stat_stages_defender=stat_stages_2)
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} took {trapDamage} trap damage')
                        battleHP2 -= trapDamage
                    elif self.ailment2.confusion:
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} is confused!')
                        if random.randrange(1, 1+1) == 1:
                            pbMove = self.__loadMovesConfig('tackle')
                            confusionDamage = self.__calculateDamageOfMove(pbMove, attacker=self.pokemon2, defender=self.pokemon2)
                            battleHP2 -= confusionDamage
                            self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} hurt itself in confusion! {confusionDamage} damage.')
                    elif self.ailment2.sleep:
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} is asleep!')
                    elif self.ailment2.freeze:
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} is frozen!')
                    
                    if battleHP2 <= 0:
                        self.__victory()
                        self.statuscode = 420
                        retVal = {'result': 'victory'}
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} fainted!')
                        return retVal

            # =================================================================
            # END OF TURN — Leech Seed drain
            # =================================================================
            if leech_seed_1 and battleHP1 > 0 and battleHP2 > 0:
                seed_damage = calculate_leech_seed_damage(p1_max_hp)
                battleHP1 -= seed_damage
                battleHP2 = min(p2_max_hp, battleHP2 + seed_damage)
                self.battle_log.append(f'🌱 {self.pokemon1.pokemonName.capitalize()} had its energy drained by Leech Seed! (-{seed_damage} HP)')

            if leech_seed_2 and battleHP2 > 0 and battleHP1 > 0:
                seed_damage = calculate_leech_seed_damage(p2_max_hp)
                battleHP2 -= seed_damage
                battleHP1 = min(p1_max_hp, battleHP1 + seed_damage)
                self.battle_log.append(f'🌱 Enemy {self.pokemon2.pokemonName.capitalize()} had its energy drained by Leech Seed! (-{seed_damage} HP)')

            # =================================================================
            # END OF TURN — Victory/Defeat + burn/poison
            # =================================================================
            if battleHP1 <= 0:
                self.pokemon1.currentHP = battleHP1
                self.__defeat()
                self.statuscode = 420
                retVal = {'result': 'defeat'}
                self.battle_log.append(f'Your {self.pokemon1.pokemonName.capitalize()} fainted!')
                break

            elif battleHP2 <= 0:
                self.pokemon1.currentHP = battleHP1
                self.__victory()
                self.statuscode = 420
                retVal = {'result': 'victory'}
                self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} fainted!')
                break

            elif battleHP1 > 0 and battleHP2 > 0:
                if pbMove['moveType'] == 'fire' and self.ailment1.freeze:
                    self.ailment1.freeze = False  
                    self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is no longer frozen')
                    
                if self.ailment1.burn or self.ailment1.poison:
                    self.pokemon1.currentHP = modifiedPokemon1.currentHP
                    battleHP1 = modifiedPokemon1.currentHP
                    if self.ailment1.burn:
                        self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is hurt by burn!')
                    else:
                        self.battle_log.append(f'{self.pokemon1.pokemonName.capitalize()} is hurt by poison!')
                    if battleHP1 <= 0:
                        self.__defeat()
                        self.statuscode = 420
                        retVal = {'result': 'defeat'}
                        self.battle_log.append(f'Your {self.pokemon1.pokemonName.capitalize()} fainted!')
                        return retVal

                if self.ailment2.burn or self.ailment2.poison:
                    self.pokemon2.currentHP = modifiedPokemon2.currentHP
                    battleHP2 = modifiedPokemon2.currentHP
                    if self.ailment2.burn:
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} is hurt by burn!')
                    else:
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} is hurt by poison!')
                    if battleHP2 <= 0:
                        self.__victory()
                        self.statuscode = 420
                        retVal = {'result': 'victory'}
                        self.battle_log.append(f'Enemy {self.pokemon2.pokemonName.capitalize()} fainted!')
                        return retVal

            turn_number += 1
            move1 = None

        return retVal


    def runAway(self):
        """ run away from battle """
        # todo add a very small chance to not run away and result in defeat using random
        if random.randrange(1,100) <= 8:
            self.__defeat()
            self.statuscode = 420
            self.message = 'You failed to run away! ' + self.message
        else:
            # leaderboard stats
            lb = leaderboard(self.pokemon1.discordId)
            lb.run_away()
            self.statuscode = 420
            self.message = "You successfully got away"
        return self.message

    def catch(self, item=None):
        # roll chance to catch pokemon and it either runs away or
        #poke-ball, great-ball, ultra-ball, master-ball
        if self.pokemon2.discordId is not None:
            self.statuscode = 420
            self.message = "You can only catch Wild Pokemon!"
            return
        
        pokemonCaught = False
        inventory = inv(self.pokemon1.discordId)
        if item == 'poke-ball':
            ballValue = 12
            if inventory.pokeball > 0:
                inventory.pokeball -= 1
        elif item == 'great-ball':
            ballValue = 8
            if inventory.greatball > 0:
                inventory.greatball -= 1
        elif item == 'ultra-ball':
            ballValue = 6
            if inventory.ultraball > 0:
                inventory.ultraball -= 1
        if item == 'master-ball':
            if inventory.masterball > 0:
                inventory.masterball -= 1
            pokemonCaught = True
        else:
            breakFree = random.randrange(1, 255+1)
            # todo add some modifier to the HP here to change up the catch statistics
            randHPModifier = (random.randrange(45, 100) / 100)
            currentHP = self.pokemon2.currentHP
            hpMax = self.pokemon2.currentHP
            catchRate = (hpMax * 255 * 4) / (currentHP * randHPModifier * ballValue)
            
            if catchRate >= breakFree:
                pokemonCaught = True

        # leaderboard stats
        lb = leaderboard(self.pokemon1.discordId)
        lb.balls_thrown()

        inventory.save()
        if inventory.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during inventory save()"
            return self.message

        if pokemonCaught:
            
            # leaderboard stats
            lb = leaderboard(self.pokemon1.discordId)
            lb.catch()
            
            # Check party size before saving
            trainer = trainer_import(self.pokemon1.discordId)
            party_count = trainer.getPartySize()
            
            # Set party status based on party size
            self.pokemon2.discordId = self.pokemon1.discordId
            self.pokemon2.party = party_count < 6  # True if party < 6, False otherwise
            
            
            # Save it to the trainers inventory
            self.pokemon2.save()
            if self.pokemon2.statuscode == 96:
                self.statuscode = 96
                self.message = 'error occured during pokemon2 save()'
                return self.message
            
            
            self.statuscode = 420
            self.message = f"You successfully caught the pokemon!"
            self.updateUniqueEncounters()

        else:
            self.statuscode = 96
            self.message = "You failed to catch the pokemon. The pokemon ran away!"

        return self.message

    def __victory(self):
        # pokemon1 had victory, calculate gained exp and update current exp
        # calculate money earned, reduced HP points
        self.updateUniqueEncounters()
        self.ailment1.save()
        expObj = exp(self.pokemon2)
        expGained = expObj.getExpGained()
        evGained = expObj.getEffortValue()
        if expObj.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during experience calculations"
            return 
        newCurrentHP = self.pokemon1.currentHP

        levelUp, retMsg, pendingMoves = self.pokemon1.processBattleOutcome(
            expGained, evGained, newCurrentHP)

        resultString = "Your Pokemon gained %s exp." % (expGained)
        # if pokemon leveled up
        if levelUp:
            resultString = resultString + ' Your Pokemon leveled up!'
        if retMsg != '':
            resultString = resultString + ' ' + retMsg
        if pendingMoves:
            resultString = resultString + ' (Moves pending: %s)' % ', '.join(pendingMoves)

        # leaderboard stats
        lb = leaderboard(self.pokemon1.discordId)
        lb.victory()

        self.statuscode = 420
        self.message = resultString
        return 'victory'

    def __defeat(self):
        # pokemon1 lost, update currentHP to 0
        expGained = 0
        evGained = None
        newCurrentHP = 0
        self.pokemon1.processBattleOutcome(expGained, evGained, newCurrentHP)
        if self.pokemon1.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during processBattleOutcome"
            return
        self.ailment1.resetAilments()
        self.ailment1.save()
        # leaderboard stats
        lb = leaderboard(self.pokemon1.discordId)
        lb.defeat()

        self.statuscode = 420
        self.message = "Your Pokemon Fainted."
        return 'defeat'

    def __calculateDamageTaken(self):
        """ calculates the damage taken during a fight """
        # todo update with better HP algorithm
        newCurrentHP = self.pokemon1.currentHP - 3
        if newCurrentHP < 0:
            newCurrentHP = 0
        return newCurrentHP

    def __calculateDamageOfMove(self, move, attacker=None, defender=None, stat_stages_attacker=None, stat_stages_defender=None):
        """ calculates the damage of the move, with stat stage support.
            attacker/defender default to pokemon1/pokemon2 if not provided. """
        if attacker is None:
            attacker = self.pokemon1
        if defender is None:
            defender = self.pokemon2
            
        calculatedDamage = 0
        moveHit = True
        pbMove = move
        accuracy = pbMove['accuracy']
        if accuracy is None or accuracy == 'null':
            accuracy = 100
        if accuracy < 100:
            rand_accuracy = random.randrange(1, accuracy+1)
            if rand_accuracy > accuracy:
                moveHit = False
        if moveHit:
            power = pbMove['power']
            if power is None:
                return 0
            moveType = pbMove['moveType']
            damage_class = pbMove['damage_class']
            attackerStats = attacker.getPokeStats()
            defenderStats = defender.getPokeStats()
            attack = 0
            defense = 0
            if damage_class == 'physical':
                attack = attackerStats['attack']
                defense = defenderStats['defense']
                # Apply stat stage multipliers
                if stat_stages_attacker:
                    from helpers.statstages import get_modified_stat
                    attack = get_modified_stat(attack, 'attack', stat_stages_attacker)
                if stat_stages_defender:
                    from helpers.statstages import get_modified_stat
                    defense = get_modified_stat(defense, 'defense', stat_stages_defender)
            else:
                attack = attackerStats['special-attack']
                defense = defenderStats['special-defense']
                if stat_stages_attacker:
                    from helpers.statstages import get_modified_stat
                    attack = get_modified_stat(attack, 'special-attack', stat_stages_attacker)
                if stat_stages_defender:
                    from helpers.statstages import get_modified_stat
                    defense = get_modified_stat(defense, 'special-defense', stat_stages_defender)
            randmonMult = random.randrange(217, 256) / 255
            defendingType = defender.type1
            if moveType in attacker.type1:
                stab = 1.5
            else:
                stab = 1
            level = attacker.currentLevel
            type_effectiveness = self.__getDamageTypeMultiplier(moveType, defendingType)
            calculatedDamage = int(((2 * level / 5 + 2) * power * (attack / defense) / 50 + 2) * randmonMult * stab * type_effectiveness)
        return calculatedDamage


    def __getDamageTypeMultiplier(self, moveType, defendingType):
        """ returns a multiplier for the type-effectiveness """
        dmgMult = None
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/typeEffectiveness.json')
        typeEffectivenessConfig = json.load(open(p, 'r'))
        dmgMult = typeEffectivenessConfig[moveType][defendingType]
        return dmgMult

    def __removeNullMoves(self, moveList):
        """ returns a list of moves without any nulls """
        if moveList[3] is None:
            moveList.pop(3)
        if moveList[2] is None:
            moveList.pop(2)
        if moveList[1] is None:
            moveList.pop(1)
        if moveList[0] is None:
            moveList.pop(0)
        return moveList
    
    def updateUniqueEncounters(self):
        """ updates the unique encounters table """
        name = self.pokemon2.pokemonName
        discordId = self.pokemon1.discordId
        
        # Create encounter object and check before/after
        uEncObj = uEnc(discordId)
        before_value = uEncObj.articuno if name == 'articuno' else None

        if name == 'articuno':
            uEncObj.articuno = True
        elif name == 'zapdos':
            uEncObj.zapdos = True
        elif name == 'moltres':
            uEncObj.moltres = True
        elif name == 'mewtwo':
            uEncObj.mewtwo = True
        elif name == 'snorlax':
            uEncObj.snorlax = True                
        elif name == 'magikarp':
            uEncObj.magikarp = True
        elif name == 'charmander':
            uEncObj.charmander = True
        elif name == 'squirtle':
            uEncObj.squirtle = True
        elif name == 'bulbasaur':
            uEncObj.bulbasaur = True
        elif name == 'lapras':
            uEncObj.lapras = True
        elif name == 'hitmonchan':
            uEncObj.hitmonchan = True
        elif name == 'hitmonlee':
            uEncObj.hitmonlee = True                                                                                    
        elif name == 'eevee':
            uEncObj.eevee = True
        elif name == 'missing-chode':
            if not uEncObj.missingno:
                uEncObj.missingno = True


        after_value = uEncObj.articuno if name == 'articuno' else None

        uEncObj.save()      
        save_status = uEncObj.statuscode
    
        return f"UpdateEncounter: {name}, before={before_value}, after={after_value}, saveStatus={save_status}, discordId={discordId}"
    

    def __loadMovesConfig(self, move):
        """ loads and returns the evolutiononfig for the current pokemon """
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/moves.json')
        movesConfig = json.load(open(p, 'r'))
        
        # this is the pokemon move json object from the config file
        moveJson = movesConfig[move]
        return moveJson


# Module-level utility function for damage calculation
def calculate_battle_damage(attacker, defender,
                            move_name: str, moves_config: dict,
                            type_effectiveness: dict,
                            attacker_stat_stages=None,
                            defender_stat_stages=None) -> tuple:
    """
    Calculate battle damage using Pokemon battle formula.
    Now supports stat stage modifiers.

    Args:
        attacker: The attacking Pokemon
        defender: The defending Pokemon
        move_name: Name of the move being used
        moves_config: Loaded moves.json configuration
        type_effectiveness: Loaded typeEffectiveness.json configuration
        attacker_stat_stages: Optional StatStages object for attacker
        defender_stat_stages: Optional StatStages object for defender

    Returns:
        tuple: (damage_dealt: int, attack_hit: bool)
    """
    move_data = moves_config.get(move_name, {})
    power = move_data.get('power', 0)
    accuracy = move_data.get('accuracy', 100)
    move_type = move_data.get('moveType', 'normal')
    damage_class = move_data.get('damage_class', 'physical')

    hit_roll = random.randint(1, 100)
    if hit_roll > accuracy:
        return 0, False

    if power is None or power == 0:
        return 0, True

    attacker_stats = attacker.getPokeStats()
    defender_stats = defender.getPokeStats()

    if damage_class == 'physical':
        attack = attacker_stats['attack']
        defense = defender_stats['defense']
        if attacker_stat_stages:
            from helpers.statstages import get_modified_stat
            attack = get_modified_stat(attack, 'attack', attacker_stat_stages)
        if defender_stat_stages:
            from helpers.statstages import get_modified_stat
            defense = get_modified_stat(defense, 'defense', defender_stat_stages)
    else:
        attack = attacker_stats['special-attack']
        defense = defender_stats['special-defense']
        if attacker_stat_stages:
            from helpers.statstages import get_modified_stat
            attack = get_modified_stat(attack, 'special-attack', attacker_stat_stages)
        if defender_stat_stages:
            from helpers.statstages import get_modified_stat
            defense = get_modified_stat(defense, 'special-defense', defender_stat_stages)

    level = attacker.currentLevel
    base_damage = ((2 * level / 5 + 2) * power * (attack / defense) / 50 + 2)

    random_mult = random.randrange(217, 256) / 255

    stab = 1.5 if (move_type == attacker.type1 or move_type == attacker.type2) else 1.0

    defending_type = defender.type1
    effectiveness = type_effectiveness.get(move_type, {}).get(defending_type, 1.0)

    damage = int(base_damage * random_mult * stab * effectiveness)

    return damage, True

