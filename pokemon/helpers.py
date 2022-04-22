import pokebase as pb
import config as config
import random
import math

def getPokemonLevelMoves(id_or_name):
    """ returns a dictionary of {move: level} for a pokemons base move set"""
    moveDict = {}
    if id_or_name is not None:
        pokemon = pb.pokemon(id_or_name)
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

def getNewMoves(id_or_name, level):
    """ returns a pokemons moves at a specific level """
    newMoves = {}
    if id_or_name is not None:
        moveDict = getPokemonLevelMoves(id_or_name)
        for key, value in moveDict.items():
            if value == level:
                newMoves[key] = value
    return newMoves


def getPokemonSpriteUrl(id_or_name, sprite_type='pokemon'):
    """ returns a pokemons base sprite url.png """
    if id_or_name is not None:
        if type(id_or_name) == int:
            pokemonId = id_or_name
        else:
            try:
                pokemon = pb.pokemon(id_or_name)
                pokemonId = pokemon.id
            except:
                return None
        return pb.SpriteResource(sprite_type, pokemonId).url

def getPokemonType(id_or_name):
    """ returns string of pokemons base type """
    if id_or_name is not None:
        pokemon = pb.pokemon(id_or_name)
        return pokemon.types[0].type.name

def getPokemonBaseStats(id_or_name):
    """ returns dictionary of {stat: value} for a pokemons base stats """
    baseStatDict = {}
    if id_or_name is not None:
        pokemon = pb.pokemon(id_or_name)
        for stat in pokemon.stats:
            statName = stat.stat.name
            statVal = stat.base_stat
            baseStatDict[statName] = statVal
    return baseStatDict

def getStarterPokemon(username):
    """ returns a random starter pokemon dictionary {pokemon: id} """
    if username is not None:
        if 'cactitwig' in username.lower():
            return {'rattata': 19}
        else:
            sequence=[{'bulbasaur': 1}, {'charmander': 4}, {'squirtle': 7}]
            print(random.choice(sequence))


# def caughtNewPokemon(id_or_name, level):
#     """ returns a new pokemons stats modified by level and randMult """

#     return

# def randMultiplier(value):
#     """ retuans a random modified value within the percentMultiplier range """
#     percentValue = value * config.baseStatRandMult
#     return round(random.uniform(value-percentValue, value+percentValue))

"""
#
# Below are functions for calculating experience for each level at different exp rates
#
"""
def baseExpFast(level):
    """ returns minimum total experience at a given level """
    return round(0.8 * (level ** 3))

def baseExpMedFast(level):
    """ returns minimum total experience at a given level """
    return round(level ** 3)

def baseExpMedSlow(level):
    """ returns minimum total experience at a given level """
    return round(1.2*(level ** 3)-(15*(level ** 2)) + 100*level - 140)

def baseExpSlow(level):
    """ returns minimum total experience at a given level """
    return round(1.25 * (level ** 3))

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
    if id_or_name is not None:
        pokemon = pb.pokemon(id_or_name)
        for stat in pokemon.stats:
            statName = stat.stat.name
            effortValue = stat.effort * config.overallExperienceModifier
            effortValueDict[statName] = effortValue
    
    return effortValueDict


def generatePokemonIV():
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

def getPokemonStats(pokemonObj):
    """ returns a dictionary of a pokemon's unique stats based off level, EV, and IV """
    statsDict = {}
    if pokemonObj is not None:
        #global
        level = 5

        # hp
        EV = 1
        base = 39
        IV = 8
        statsDict['hp'] = calculateUniqueStat(level, base, EV, IV) + level + 10

        # attack
        EV = 1
        base = 55
        IV = 14
        statsDict['attack'] = calculateUniqueStat(level, base, EV, IV) + 5

        # defense
        EV = 1
        base = 40
        IV = 2
        statsDict['defense'] = calculateUniqueStat(level, base, EV, IV) + 5
        
        # speed
        EV = 1
        base = 90
        IV = 3
        statsDict['speed'] = calculateUniqueStat(level, base, EV, IV) + 5
        
        # special
        EV = 1
        base = 50
        IV = 12
        statsDict['special-attack'] = calculateUniqueStat(level, base, EV, IV) + 5
        statsDict['special-defense'] = calculateUniqueStat(level, base, EV, IV) + 5

        return statsDict


def calculateUniqueStat(level, base, EV, IV):
    """ returns integer of a stat calculated from various parameters """
    evCalc = math.floor(math.ceil(math.sqrt(EV))/4)
    baseIVCalc = (base + IV) * 2
    numerator = (baseIVCalc + evCalc) * level
    baseCalc = math.floor(numerator/100)
    return baseCalc

