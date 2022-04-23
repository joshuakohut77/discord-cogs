# pokemon user class

import pokebase as pb
import random
import math
from statclass import PokeStats

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
        self.wildPokemon = True
        self.base_exp = None
        self.types = None
        self.hp = PokeStats('hp')
        self.attack = PokeStats('attack')
        self.defense = PokeStats('defense')
        self.speed = PokeStats('speed')
        self.special_attack = PokeStats('special-attack')
        self.special_defense = PokeStats('special-defense')

    def load(self, pokeDict=None):
        """ populates the object with stats from pokeapi """
        pokemon = pb.pokemon(self.id_or_name)
        self.name = pokemon.species.name
        self.id = pokemon.id
        self.spriteURL = pb.SpriteResource('pokemon', pokemon.id).url
        self.growthRate = pb.pokemon_species(pokemon.id).growth_rate.name
        self.base_exp = pokemon.base_experience
        self.types = self.__getPokemonType()

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
    
    def getPokeStats(self):
        """ returns a dictionary of a pokemon's unique stats based off level, EV, and IV """
        statsDict = {}
        level = self.currentLevel

        statsDict['hp'] = self.__calculateUniqueStat(self.hp) + level + 10
        statsDict['attack'] = self.__calculateUniqueStat(self.attack) + 5
        statsDict['defense'] = self.__calculateUniqueStat(self.defense) + 5
        statsDict['speed'] = self.__calculateUniqueStat(self.speed) + 5
        statsDict['special-attack'] = self.__calculateUniqueStat(self.special_attack) + 5
        statsDict['special-defense'] = self.__calculateUniqueStat(self.special_defense) + 5

        return statsDict

    def getPokemonLevelMoves(self):
        """ returns a dictionary of {move: level} for a pokemons base move set"""
        moveDict = {}
        pokemon = pb.pokemon(self.id)
        for move in pokemon.moves:
            for version in move.version_group_details:
                    if version.version_group.name != 'red-blue':
                        continue
                    elif version.move_learn_method.name != 'level-up':
                        continue
                    else:
                        moveName = move.move.name
                        moveLevel = version.level_learned_at
                        moveDict[moveName] = moveLevel
        return moveDict

    def evolve(self):
        """ takes a current pokemon and returns an evolved version """
        # todo check if pokemon has evolution, verify level is right
        # retain EV stats through creation. 

        return

    ####
    ###   Private Class Methods
    ####

    def __getPokemonType(self):
        """ returns string of pokemons base type """
        typeList = []
        pokemon = pb.pokemon(self.id)
        for type in pokemon.types:
            typeList.append(type.type.name)
        
        return typeList

    def __getNewMoves(self):
        """ returns a pokemons moves at a specific level """
        newMoves = {}
        moveDict = self.getPokemonLevelMoves()
        for key, value in moveDict.items():
            if value == self.currentLevel:
                newMoves[key] = value
        return newMoves

    def __calculateUniqueStat(self, statObj):
        """ returns integer of a stat calculated from various parameters """
        level = self.currentLevel
        EV = statObj.EV
        IV = statObj.IV
        base = statObj.base
        evCalc = math.floor(math.ceil(math.sqrt(EV))/4)
        baseIVCalc = (base + IV) * 2
        numerator = (baseIVCalc + evCalc) * level
        baseCalc = math.floor(numerator/100)
        return baseCalc

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
        pokemon = pb.pokemon(self.id)
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
pokemon.create(8)


print(pokemon.getPokeStats())



