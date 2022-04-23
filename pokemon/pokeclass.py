# pokemon user class
import statclass 
import pokebase as pb
import random
import math


class Pokemon:
    def __init__(self, id_or_name):
        self.id_or_name = id_or_name
        self.name = None
        self.id = None
        self.spriteURL = None
        self.growthRate = None
        self.currentLevel = None
        self.currentExp = None
        self.traded = None
        self.base_exp = None
        self.hp = statclass.PokeStats('hp')
        self.attack = statclass.PokeStats('attack')
        self.defense = statclass.PokeStats('defense')
        self.speed = statclass.PokeStats('speed')
        self.special_attack = statclass.PokeStats('special-attack')
        self.special_defense = statclass.PokeStats('special-defense')

    def load(self):
        """ populates the object with stats from pokeapi """
        pokemon = pb.pokemon(self.id_or_name)
        self.name = pokemon.species.name
        self.id = pokemon.id
        self.spriteURL = pb.SpriteResource('pokemon', pokemon.id).url
        self.growthRate = pb.pokemon_species(pokemon.id).growth_rate.name
        self.base_exp = pokemon.base_experience

    def create(self, level):
        """ creates a new pokemon with generated stats at a given level """
        self.load()
        self.currentLevel = level
        self.traded = False
        self.currentExp = self.__getBaseLevelExperience()
        ivDict = self.__generatePokemonIV()
        evDict = self.__generatePokemonEV()
        baseDict = self.__getPokemonBaseStats()

        self.setPokeStats(baseDict, ivDict, evDict)



    
    def setPokeStats(self, baseDict, ivDict, evDict):
        """ populates PokeStats class value with given stats """
        self.hp.base = baseDict['hp']
        self.hp.IV = ivDict['hp']
        self.hp.EV = evDict['hp']

        self.attack.base = baseDict['attack']
        self.attack.IV = ivDict['attack']
        self.attack.EV = evDict['attack']

        self.defense.base = baseDict['defense']
        self.defense.IV = ivDict['defense']
        self.defense.EV = evDict['defense']

        self.speed.base = baseDict['speed']
        self.speed.IV = ivDict['speed']
        self.speed.EV = evDict['speed']

        self.special_attack.base = baseDict['special-attack']
        self.special_attack.IV = ivDict['special-attack']
        self.special_attack.EV = evDict['special-attack']

        self.special_defense.base = baseDict['special-defense']
        self.special_defense.IV = ivDict['special-defense']
        self.special_defense.EV = evDict['special-defense']

    ####
    ###   Private Class Methods
    ####

    def __generatePokemonIV(self):
        """ returns dictionary of random generated individual values """
        # a pokemon has 6 IVs for each base stat
        # attack, defense, speed, special_attack, and special_defense are random 0-15
        # hp is calculated from the other IV using a binary string conversion formula
        ivDict = {}
        attack = random.randrange(0,16)
        defense = random.randrange(0,16)
        speed = random.randrange(0,16)
        special_attack = random.randrange(0,16)
        special_defense = special_attack

        hp = int(format(attack, 'b').zfill(4)[3] + format(defense, 'b').zfill(4)[3] + format(speed, 'b').zfill(4)[3] + format(special_attack, 'b').zfill(4)[3], 2)

        ivDict['hp'] = hp
        ivDict['attack'] = attack
        ivDict['defense'] = defense
        ivDict['speed'] = speed
        ivDict['special-attack'] = special_attack
        ivDict['special-defense'] = special_defense
        return ivDict

    def __generatePokemonEV(self):
        """ returns dictionary of base generated effort values """
        evDict = {'hp': 1, 'attack': 1, 'defense': 1, 'speed': 1, 'special-attack': 1, 'special-defense': 1}
        return evDict

    def __getPokemonBaseStats(self):
        """ returns dictionary of {stat: value} for a pokemons base stats """
        baseDict = {}
        pokemon = pb.pokemon(self.id_or_name)
        for stat in pokemon.stats:
            statName = stat.stat.name
            statVal = stat.base_stat
            baseDict[statName] = statVal
        return baseDict


    def __getBaseLevelExperience(self):
        """ returns minimum total experience at a given level """
        if self.growthRate == 'Fast':
            return round(0.8 * (self.currentLevel ** 3))
        elif self.growthRate == 'medium-fast':
            return round(self.currentLevel ** 3)
        elif self.growthRate == 'medium-slow':
            return round(1.2*(self.currentLevel ** 3)-(15*(self.currentLevel ** 2)) + 100*self.currentLevel - 140)
        elif self.growthRate == 'slow':
            return round(1.25 * (self.currentLevel ** 3))
        else:
            return None






pokemon = Pokemon('charizard')
pokemon.create(7)


print(pokemon.currentExp)


