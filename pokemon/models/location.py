from typing import List


class LocationModel:
    
    def __init__(self, results: List):
        self.locationId: int = results[0]
        self.name: str = results[1]
        self.north: str = results[2]
        self.east: str = results[3]
        self.south: str = results[4]
        self.west: str = results[5]
        self.prerequisites = results[6]
        self.spritePath: str = results[7]
