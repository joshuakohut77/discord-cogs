"""
Battle state models for tracking ongoing battles.

These classes maintain the state of active battles including
player/enemy Pokemon, turn tracking, and battle logs.
"""
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..services.pokeclass import Pokemon as PokemonClass
else:
    # Runtime import to avoid circular dependencies
    PokemonClass = 'PokemonClass'


class BattleState:
    """Track ongoing manual battle state with multiple Pokemon support"""

    def __init__(self, user_id: str, channel_id: int, message_id: int,
                 player_party: list, enemy_pokemon_list: list,
                 enemy_name: str, trainer_model, battle_manager):
        self.user_id = user_id
        self.channel_id = channel_id
        self.message_id = message_id

        # Player's full party
        self.player_party = player_party  # List of PokemonClass objects
        self.player_current_index = 0  # Index of current Pokemon
        self.player_pokemon = player_party[0]  # Current Pokemon

        # Enemy's full team
        self.enemy_pokemon_data = enemy_pokemon_list  # List of dicts like [{"geodude": 12}, {"onix": 14}]
        self.enemy_current_index = 0  # Index of current Pokemon
        self.enemy_pokemon = None  # Will be set after creating first Pokemon

        self.enemy_name = enemy_name
        self.trainer_model = trainer_model
        self.battle_manager = battle_manager
        self.battle_log: List[str] = []
        self.turn_number = 1
        self.defeated_enemies: List = []  # Track defeated enemy Pokemon
        self.is_wild_trainer: bool = False


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
