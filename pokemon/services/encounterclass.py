# encounter class

import sys
import config
import pokebase as pb
import random
from dbclass import db as dbconn
from expclass import experiance as exp
from inventoryclass import inventory as inv
from loggerclass import logger as log
from pokedexclass import pokedex

# Global Config Variables
MAX_BATTLE_TURNS = 50
# MAX_BATTLE_TURNS = config.max_battle_turns
# Class Logger
logger = log()

# this class is to handle encounters with pokemon.
class encounter:
    def __init__(self, pokemon1, pokemon2):
        # pokemon1 for PvE will always be the discord trainers pokemon
        self.faulted = False

        self.pokemon1 = pokemon1
        self.pokemon2 = pokemon2
        pokedex(self.pokemon1.discordId, pokemon2)

    def fight(self):
        """ two pokemon fight and a outcome is decided """
        # two pokemon fight with an outcome calling victory or defeat
        # todo update with better fight outcome algorithm
        if self.pokemon1.currentHP == 0:
            return "Your active Pokemon has no HP left!"

        retMsg = self.battle()
        return retMsg

    def battle(self):
        """ this function simulates a live battle between two pokemon """
        # get pokemons current fighting HP
        battleHP1 = self.pokemon1.currentHP
        if battleHP1 <= 0:
            return "Your active Pokemon has no HP left!"
        battleHP2 = self.pokemon2.currentHP
        # get pokemons list of moves
        battleMoves1 = self.__removeNullMoves(self.pokemon1.getMoves())
        battleMoves2 = self.__removeNullMoves(self.pokemon2.getMoves())

        # pokemon goes first
        for x in range(MAX_BATTLE_TURNS):
            randMoveSelector = random.randrange(1, len(battleMoves1)+1)
            damage = self.__calculateDamageOfMove(battleMoves1[randMoveSelector-1])
            battleHP2 -= damage
            print('%s used %s' %(self.pokemon1.name, battleMoves1[randMoveSelector-1]))
            print('%s did %s damage' %(self.pokemon1.name, str(damage)))
            if battleHP2 <=0:
                self.pokemon1.currentHP = battleHP1
                retMsg = self.__victory()
                break
            randMoveSelector = random.randrange(1, len(battleMoves2)+1)
            damage = self.__calculateDamageOfMove(battleMoves2[randMoveSelector-1])
            battleHP1 -= damage
            print('%s used %s' %(self.pokemon2.name, battleMoves2[randMoveSelector-1]))
            print('%s did %s damage' %(self.pokemon2.name, str(damage)))
            if battleHP1 <=0:
                self.pokemon1.currentHP = battleHP1
                retMsg = self.__defeat()
                break
            
            # max number of turns has occured. Break out of potential infinite loop
            if x == MAX_BATTLE_TURNS - 1:
                retMsg = 'Failed to defeat enemy pokemon. The Pokemon ran away'
                break
        
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
        #poke-ball, great-ball, ultra-ball, master-ball
        if not self.pokemon2.wildPokemon:
            return False, "You can only catch Wild Pokemon!"
        pokemonCaught = False
        inventory = inv(self.pokemon1.discordId)
        if item == 'poke-ball':
            ballValue = 12
            if inventory.pokeball > 0:
                inventory.pokeball -= 1
        elif item == 'great-ball':
            ballValue = 8
            if inventory.greatball > 0:
                inventory.greatball -= 1
        elif item == 'ultra-ball':
            ballValue = 6
            if inventory.ultraball > 0:
                inventory.ultraball -= 1
        if item == 'master-ball':
            if inventory.masterball > 0:
                inventory.masterball -= 1
            pokemonCaught = True
        else:
            breakFree = random.randrange(1, 255+1)
            # todo add some modifier to the HP here to change up the catch statistics
            randHPModifier = (random.randrange(45, 100) / 100)
            currentHP = self.pokemon2.currentHP
            hpMax = self.pokemon2.currentHP
            catchRate = (hpMax * 255 * 4) / (currentHP * randHPModifier * ballValue)
            
            if catchRate >= breakFree:
                pokemonCaught = True

        inventory.save()
        if inventory.faulted:
            self.faulted = True
            return "error occured during inventory save()"

        if pokemonCaught:
            # pokemon caught successfully. Save it to the trainers inventory
            self.pokemon2.discordId = self.pokemon1.discordId
            self.pokemon2.save()
            if self.pokemon2.faulted:
                self.faulted = True
                return 'error occured during pokemon2 save()'
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
        if expObj.faulted:
            self.faulted = True
            return "error occured during expericne calculations"
        newCurrentHP = self.pokemon1.currentHP

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
        if self.pokemon1.faulted:
            self.faulted = True
            return "error occured during processBattleOutcome"
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
            defendingType = self.pokemon2.type1 # type 1 is the primary type 
            if moveType in defendingType:
                stab = 1.5
            else:
                stab = 1
            level = self.pokemon1.currentLevel
            type_effectiveness = self.__getDamageTypeMultiplier(moveType, defendingType)

            # formula found here: https://bulbapedia.bulbagarden.net/wiki/Damage#Example
            calc_level = ((2*level)/5)+2
            calc_numerator = ((calc_level * power * (attack/defense))/50) + 2
            calculatedDamage = round(calc_numerator * randmonMult * stab * type_effectiveness)

        return calculatedDamage

    def __getDamageTypeMultiplier(self, moveType, defendingType):
        """ returns a multiplier for the type-effectiveness """
        dmgMult = None
        try:
            db = dbconn()
            # TODO update this query string to not use string replacement like this. Psycog has a method 
            queryString = """SELECT %s FROM "type-effectiveness" WHERE source = '%s'""" %(defendingType, moveType)
            result = db.querySingle(queryString)
            dmgMult = result[0]
        except:
            self.faulted = True
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return dmgMult

    def __removeNullMoves(self, moveList):
        """ returns a list of moves without any nulls """
        if moveList[3] is None:
            moveList.pop(3)
        if moveList[2] is None:
            moveList.pop(2)
        if moveList[1] is None:
            moveList.pop(1)
        if moveList[0] is None:
            moveList.pop(0)
        return moveList