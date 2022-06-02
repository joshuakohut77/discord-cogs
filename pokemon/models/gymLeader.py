import json
from typing import List

class GymLeaderModel:
    
    def __init__(self, results: json):
        self.name = results['gym-leader']
        self.spritePath = results['leader_spritePath']
        self.gymSpritePath = results['gym_spritePath']
        self.gymName = results['gym-name']
        self.money = results['money']
        self.badge = results['badge']
        self.enemy_uuid = results['enemy_uuid']
        self.pokemon = results['pokemon'] # this is a list of pokemon json in the format of { "pokemon": level }
