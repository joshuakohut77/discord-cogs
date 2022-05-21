import json

class LocationModel:
    
    def __init__(self, results: json):
        self.locationId = results['locationId']
        self.name = results['name']
        self.north = results['north']
        self.east = results['east']
        self.south = results['south']
        self.west = results['west']
        self.spritePath = results['spritePath']
        self.pokecenter = results['pokecenter']
        self.gym = results['gym']
