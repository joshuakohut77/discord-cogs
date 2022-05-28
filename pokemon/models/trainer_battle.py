import json
from typing import List

class TrainerBattleModel:
    
    def __init__(self, results: json):
        self.name = results['name']
        self.spritePath = results['spritePath']
        self.money = results['money']
        self.enemy_uuid = results['enemy_uuid']
        self.pokemon = results['pokemon'] # this is a list of pokemon json in the format of { "pokemon": level }
