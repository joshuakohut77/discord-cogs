"""
Custom Pokemon for the finale system.

FinalePokemon wraps pokemon_config.json data and provides
the same interface as PokemonClass so the battle system works
transparently with custom Pokemon.
"""
import os
import json
from typing import Dict, List


def load_finale_pokemon_config() -> dict:
    """Load the finale pokemon config file."""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'pokemon_config.json'
    )
    with open(config_path, 'r') as f:
        return json.load(f)


class FinalePokemon:
    """A custom Pokemon that mimics PokemonClass interface for finale battles."""

    def __init__(self, config_key: str, config_data: dict):
        self._config_key = config_key
        self.pokemonName = config_data['displayName']
        self.type1 = config_data['type1']
        t2 = config_data.get('type2', 'none')
        self.type2 = t2 if t2 and t2.lower() != 'none' else None
        self.currentLevel = config_data['level']
        self._base_stats = config_data['baseStats']
        self._moves_data = config_data['moves']
        self._front_sprite = config_data.get('frontSprite')

        # Calculate HP from stats
        stats = self.getPokeStats()
        self.currentHP = stats['hp']

        # Compatibility fields so existing code doesn't break
        self.discordId = None
        self.trainerId = None
        self.shiny = False
        self.pokedexId = 0
        self.frontSpriteURL = None
        self.backSpriteURL = None
        self.nickName = None

    def getPokeStats(self) -> dict:
        """Calculate stats from base stats and level (simplified formula)."""
        level = self.currentLevel
        stats = {}
        for stat_name, base in self._base_stats.items():
            if stat_name == 'hp':
                stats['hp'] = int(((base * 2) * level / 100) + level + 10)
            else:
                stats[stat_name] = int(((base * 2) * level / 100) + 5)
        return stats

    def getMoves(self) -> List[str]:
        """Return list of move name strings."""
        return list(self._moves_data.keys())

    def getMoveData(self, move_name: str) -> dict:
        """Get full move data dict for a specific move."""
        return self._moves_data.get(move_name, {})

    def getMovesConfig(self) -> dict:
        """Get all move data as a dict, compatible with moves_config format."""
        return dict(self._moves_data)

    def save(self):
        pass

    def load(self, **kwargs):
        pass