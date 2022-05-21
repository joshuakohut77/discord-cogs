import json

class PokedexModel:
    
    def __init__(self, results: json):
        self.pokemonId = results['pokemonId']
        self.pokemonName = results['pokemonName']
        self.height = results['height']
        self.weight = results['weight']
        self.description = results['description']
        self.mostRecent = results['mostRecent']

