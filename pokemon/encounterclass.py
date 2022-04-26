# encounter class

from dbclass import db as dbconn
from pokeclass import Pokemon as pokeClass
from expclass import experiance as exp
from inventoryclass import inventory as inv
import config
import random

# this class is to handle encounters with pokemon.

class encounter:
    def __init__(self, pokemon1, pokemon2):
        # pokemon1 for PvE will always be the discord trainers pokemon
        self.pokemon1 = pokemon1
        self.pokemon2 = pokemon2


    def fight(self):
        # two pokemon fight with an outcome calling victory or defeat
        if random.randrange(1, 100) <= config.pokemon_win_rate:
            retMsg = self.__victory()
        else:
            retMsg = self.__defeat()
        return retMsg

    def __victory(self):
        # pokemon1 had victory, calculate gained exp and update current exp
        # calculate money earned, reduced HP points
        expObj = exp(self.pokemon2)
        expGained = expObj.getExpGained()
        evGained = expObj.getEffortValue()
        newCurrentHP = self.__calculateDamageTaken()

        levelUp = self.pokemon1.processBattleOutcome(expGained, evGained, newCurrentHP)

        resultString = "Your Pokemon gained %s exp." %(expGained)
        # if pokemon leved up
        if levelUp:
            resultString = resultString + ' Your Pokemon leveled up!'

        return resultString
    
    def __defeat(self):
        # pokemon1 lost, update currentHP to 0
        expGained = 0
        evGained = None
        newCurrentHP = 0
        self.pokemon1.processBattleOutcome(expGained, evGained, newCurrentHP)
        return "Your Pokemon Fainted."

    def runAway(self):
        """ run away message """
        # todo add a very small chance to not run away and result in defeat using random
        return "You successfully got away"
    
    def catch(self, item):
        # roll chance to catch pokemon and it either runs away or
        if not self.pokemon2.wildPokemon:
            return False, "You can only catch Wild Pokemon!"
        
        inventory = inv(self.pokemon1.discordId)
        if inventory.pokeball > 0:
            inventory.pokeball = inventory.pokeball - 1
            inventory.save()
        
        pokemonCaught = False
        if random.randrange(1, 100) <= config.pokemon_catch_rate:
           pokemonCaught = True 

        if pokemonCaught:
            # pokemon caught successfully. Save it to the trainers inventory
            self.pokemon2.save(self.pokemon1.discordId)
            retMsg = "You successfully caught the pokemon"
        else:
            retMsg = "You failed to catch the pokemon. The pokemon ran away!"
        return retMsg

    def __calculateDamageTaken(self):
        """ calculates the damage taken during a fight """
        newCurrentHP = self.pokemon1.currentHP - 3
        
        if newCurrentHP < 0:
            newCurrentHP = 0
        return newCurrentHP
