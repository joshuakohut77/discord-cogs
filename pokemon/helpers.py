import pokebase as pb
import config as config
import random
import math


def getStarterPokemon(username):
    """ returns a random starter pokemon dictionary {pokemon: id} """
    if username is not None:
        if 'cactitwig' in username.lower():
            return {'rattata': 19}
        else:
            sequence=[{'bulbasaur': 1}, {'charmander': 4}, {'squirtle': 7}]
            starter = random.choice(sequence)
            print(starter)
            return starter


"""
#
# Below are functions for calculating experience for each level at different exp rates
#
"""


def expGain(baseExp, level):
    a = 1 # 1 if wild, 1.5 if owned by trainer
    b = baseExp # base exp of fainted pokemon
    L = level # level of fainted pokemon
    s = 1 # number of participating pokemon
    t = 1 # 1 if pokemon is current owner, 1.5 if pokemon was gained in a trade
    exp = (a*t*b*L) / (7 * s)
    return exp


def getEffortValue(id_or_name):
    """ returns dictionary of effort values gained upon defeat """
    effortValueDict = {}
    pokemon = pb.pokemon(id_or_name)
    for stat in pokemon.stats:
        statName = stat.stat.name
        effortValue = stat.effort * config.overallExperienceModifier
        effortValueDict[statName] = effortValue
    
    return effortValueDict











