"""
Battle state models for tracking ongoing battles.

These classes maintain the state of active battles including
player/enemy Pokemon, turn tracking, and battle logs.
"""
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..services.pokeclass import Pokemon as PokemonClass
else:
    PokemonClass = 'PokemonClass'

from helpers.statstages import StatStages


class BattleState:
    """Track ongoing manual battle state with multiple Pokemon support"""

    def __init__(self, user_id: str, channel_id: int, message_id: int,
                 player_party: list, enemy_pokemon_list: list,
                 enemy_name: str, trainer_model, battle_manager):
        self.user_id = user_id
        self.channel_id = channel_id
        self.message_id = message_id

        # Player's full party
        self.player_party = player_party
        self.player_current_index = 0
        self.player_pokemon = player_party[0]

        # Enemy's full team
        self.enemy_pokemon_data = enemy_pokemon_list
        self.enemy_current_index = 0
        self.enemy_pokemon = None

        self.enemy_name = enemy_name
        self.trainer_model = trainer_model
        self.battle_manager = battle_manager
        self.battle_log: List[str] = []
        self.turn_number = 1
        self.defeated_enemies: List = []
        self.is_wild_trainer: bool = False
        self.level_up_data = None

        # Ailment tracking
        self.player_ailment = None
        self.enemy_ailment = None

        # Special move tracking
        self.rest_turns_player = 0
        self.rest_turns_enemy = 0
        self.leech_seed_player = False
        self.leech_seed_enemy = False

        # Stat stage tracking
        self.player_stat_stages = StatStages()
        self.enemy_stat_stages = StatStages()


class WildBattleState:
    """Track ongoing wild Pokemon battle state"""

    user_id: str
    channel_id: int
    message_id: int

    player_pokemon: 'PokemonClass'
    wild_pokemon: 'PokemonClass'

    turn_number: int
    battle_log: List[str]

    def __init__(self, user_id: str, channel_id: int, message_id: int,
                 player_pokemon: 'PokemonClass', wild_pokemon: 'PokemonClass'):
        self.user_id = user_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.player_pokemon = player_pokemon
        self.wild_pokemon = wild_pokemon
        self.turn_number = 1
        self.battle_log = []
        self.level_up_data = None

        # Ailment tracking
        self.player_ailment = None
        self.enemy_ailment = None

        # Special move tracking
        self.rest_turns_player = 0
        self.rest_turns_enemy = 0
        self.leech_seed_player = False
        self.leech_seed_enemy = False

        # Stat stage tracking
        self.player_stat_stages = StatStages()
        self.enemy_stat_stages = StatStages()