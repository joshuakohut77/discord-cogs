# encounter class
from dbclass import db as dbconn
from expclass import experiance as exp
from inventoryclass import inventory as inv
import pokebase as pb
from pokedexclass import pokedex
# import config
import random

# POKEMON_WIN_RATE =  config.pokemon_win_rate
# POKEMON_CATCH_RATE = config.pokemon_catch_rate

POKEMON_WIN_RATE = 95
POKEMON_CATCH_RATE = 85

# this class is to handle encounters with pokemon.


class encounter:
    def __init__(self, pokemon1, pokemon2):
        # pokemon1 for PvE will always be the discord trainers pokemon
        self.pokemon1 = pokemon1
        self.pokemon2 = pokemon2
        pokedex(self.pokemon1.discordId, pokemon2)

    def fight(self):
        """ two pokemon fight and a outcome is decided """
        # two pokemon fight with an outcome calling victory or defeat
        # todo update with better fight outcome algorithm
        if self.pokemon1.currentHP == 0:
            return "Your active Pokemon has no HP left!"
        if random.randrange(1, 100) <= POKEMON_WIN_RATE:
            retMsg = self.__victory()
        else:
            retMsg = self.__defeat()
        return retMsg

    def runAway(self):
        """ run away from battle """
        # todo add a very small chance to not run away and result in defeat using random
        if random.randrange(1,100) <= 8:
            retMsg = 'You failed to run away! '
            retMsg = retMsg + self.__defeat()
        else:
            return "You successfully got away"

    def catch(self, item=None):
        # roll chance to catch pokemon and it either runs away or
        if not self.pokemon2.wildPokemon:
            return False, "You can only catch Wild Pokemon!"

        inventory = inv(self.pokemon1.discordId)
        if inventory.pokeball > 0:
            inventory.pokeball = inventory.pokeball - 1
            inventory.save()

        pokemonCaught = False
        # todo update with better catch algorithm
        if random.randrange(1, 100) <= POKEMON_CATCH_RATE:
            pokemonCaught = True

        if pokemonCaught:
            # pokemon caught successfully. Save it to the trainers inventory
            self.pokemon2.save(self.pokemon1.discordId)
            retMsg = "You successfully caught the pokemon"
        else:
            retMsg = "You failed to catch the pokemon. The pokemon ran away!"
        return retMsg

    def __victory(self):
        # pokemon1 had victory, calculate gained exp and update current exp
        # calculate money earned, reduced HP points
        expObj = exp(self.pokemon2)
        expGained = expObj.getExpGained()
        evGained = expObj.getEffortValue()
        newCurrentHP = self.__calculateDamageTaken()

        levelUp, retMsg = self.pokemon1.processBattleOutcome(
            expGained, evGained, newCurrentHP)

        resultString = "Your Pokemon gained %s exp." % (expGained)
        # if pokemon leved up
        if levelUp:
            resultString = resultString + ' Your Pokemon leveled up!'
        if retMsg != '':
            resultString = resultString + ' ' + retMsg

        return resultString

    def __defeat(self):
        # pokemon1 lost, update currentHP to 0
        expGained = 0
        evGained = None
        newCurrentHP = 0
        self.pokemon1.processBattleOutcome(expGained, evGained, newCurrentHP)
        return "Your Pokemon Fainted."

    def __calculateDamageTaken(self):
        """ calculates the damage taken during a fight """
        # todo update with better HP algorithm
        newCurrentHP = self.pokemon1.currentHP - 3

        if newCurrentHP < 0:
            newCurrentHP = 0
        return newCurrentHP

    def __calculateDamageOfMove(self, move):
        """ calcualtes the damage of the move against opponent """
        calculatedDamage = 0
        moveHit = True
        pbMove = pb.move(move)
        accuracy = pbMove.accuracy
        if accuracy is None:
            accuracy = 100
        if accuracy < 100:
            rand_accuracy = random.randrange(1, accuracy+1)
            if rand_accuracy > accuracy:
                moveHit = False
        if moveHit:
            power = pbMove.power
            if power is None:
                return 0
            moveType = pbMove.type.name
            damage_class = pbMove.damage_class.name # physical or special
            pokemon1Stats = self.pokemon1.getPokeStats()
            pokemon2Stats = self.pokemon2.getPokeStats()
            attack = 0
            defense = 0
            if damage_class == 'physical':
                attack = pokemon1Stats['attack']
                defense = pokemon2Stats['defense']
            else:
                attack = pokemon1Stats['special-attack']
                defense = pokemon2Stats['special-defense']
            randmonMult = random.randrange(217, 256) / 255
            defendingType = self.pokemon2.types
            if moveType in defendingType:
                stab = 1.5
            else:
                stab = 1
            level = self.pokemon1.currentLevel
            type_effectiveness = self.__getDamageTypeMultiplier(moveType, defendingType)

            # formula found here: https://bulbapedia.bulbagarden.net/wiki/Damage#Example
            calc_level = ((2*level)/5)+2
            calc_numerator = ((calc_level * power * (attack/defense))/50) + 2
            calculatedDamage = calc_numerator * randmonMult * stab * type_effectiveness

        return calculatedDamage

    def __getDamageTypeMultiplier(self, moveType, defendingTypeStr):
        """ returns a multiplier for the type-effectiveness """
        # pokemon can have multipl types so query both and return the smaller modifier of the two
        defendingTypeStr = defendingTypeStr.replace('{', '')
        defendingTypeStr = defendingTypeStr.replace('}', '')
        typeList = defendingTypeStr.split(',')
        moveType = 'normal'
        dmgMultList = []
        db = dbconn()
        for defType in typeList:
            # TODO update this query string to not use string replacement like this. Psycog has a method but more complex 
            queryString = """SELECT %s FROM "type-effectiveness" WHERE source = '%s'""" %(defType, moveType)
            result = db.querySingle(queryString)
            dmgMultList.append(result[0])
        # delete and close connection
        del db
        return dmgMultList.sort()[0]


