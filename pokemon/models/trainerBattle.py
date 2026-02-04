import json
from typing import List

class TrainerBattleModel:
    
    def __init__(self, results: json):
        self.name = results['name']
        
        # Handle both 'spritePath' and 'filename' keys
        # Some entries in enemyTrainers.json use 'filename', others use 'spritePath'
        if 'spritePath' in results:
            self.spritePath = results['spritePath']
        elif 'filename' in results:
            self.spritePath = results['filename']
        else:
            # Fallback - no sprite path provided
            self.spritePath = None
        
        self.money = results['money']
        self.enemy_uuid = results['enemy_uuid']
        self.pokemon = results['pokemon'] # this is a list of pokemon json in the format of { "pokemon": level }
