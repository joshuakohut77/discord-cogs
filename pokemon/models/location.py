from typing import List


class Location:
    def __init__(self, results: List):
        self.location = results[0]
        self.name = results[1]
        self.north = results[2]
        self.east = results[3]
        self.south = results[4]
        self.west = results[5]
        self.prerequisites = results[6]
        self.spritePath = results[7]