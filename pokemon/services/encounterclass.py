# encounter class
import os
import sys
import config
import json
import random
from expclass import experiance as exp
from inventoryclass import inventory as inv
from leaderboardclass import leaderboard
from loggerclass import logger as log
from uniqueencounters import uniqueEncounters as uEnc
from pokedexclass import pokedex
from pokeclass import Pokemon as PokemonClass
from ailmentsclass import ailment 

# Global Config Variables
MAX_BATTLE_TURNS = 50
# MAX_BATTLE_TURNS = config.max_battle_turns
# Class Logger
logger = log()

# this class is to handle encounters with pokemon.
class encounter:
    pokemon1: PokemonClass
    pokemon2: PokemonClass

    def __init__(self, pokemon1: PokemonClass, pokemon2: PokemonClass):
        # pokemon1 for PvE will always be the discord trainers pokemon
        self.statuscode = 69
        self.message = ''

        self.pokemon1 = pokemon1
        self.pokemon2 = pokemon2
        self.ailment1 = ailment(pokemon1.trainerId)
        self.ailment2 = ailment(pokemon2.trainerId)
        self.ailment1.load()
        pokedex(self.pokemon1.discordId, pokemon2)

    def trade(self):
        """ trades pokemon between two trainers """
        discordId1 = self.pokemon1.discordId
        discordId2 = self.pokemon2.discordId
        retVal1 = ""
        retVal2 = ""
        
        # 4 pokemon evolve when traded Alakazam, Machamp, Golem, Gengar
        evolvedPokemon = self.checkTradeEvolution(self.pokemon1)
        if evolvedPokemon is not None:
            self.pokemon1.release()
            self.pokemon1 = evolvedPokemon
            retVal1 = "Your pokemon evolved, "

        evolvedPokemon = self.checkTradeEvolution(self.pokemon2)
        if evolvedPokemon is not None:
            self.pokemon2.release()
            self.pokemon2 = evolvedPokemon
            retVal2 = "Your pokemon evolved, "
        
        retVal1 += "You received %s" %self.pokemon1.pokemonName
        retVal2 += "You received %s" %self.pokemon2.pokemonName

        self.pokemon1.discordId = discordId2
        self.pokemon2.discordId = discordId1
        self.pokemon1.traded = True
        self.pokemon2.traded = True

        self.pokemon1.save()
        self.pokemon2.save()

        # leaderboard stats
        lb = leaderboard(self.pokemon1.discordId)
        lb.trades()  

        return retVal1, retVal2

    def checkTradeEvolution(self, pokemon):
        """ checks if a pokemon evolves during a trade and returns new pokemon if it does"""
        tradedEvoList = ['kadabra', 'machoke', 'graveler', 'haunter']        
        evolvedPokemon = None
        if pokemon.pokemonName in tradedEvoList:
            if pokemon.pokemonName == 'kadabra':
                newPokemon = 'alakazam'
            elif pokemon.pokemonName == 'machoke':
                newPokemon = 'machamp'
            elif pokemon.pokemonName == 'graveler':
                newPokemon = 'golem'
            elif pokemon.pokemonName == 'haunter':
                newPokemon = 'gengar'
            evolvedPokemon = PokemonClass(newPokemon)
            evolvedPokemon.create(pokemon.currentLevel)

        return evolvedPokemon

    def fight(self, battleType='auto', move=''):
        """ two pokemon fight and a outcome is decided """
        # two pokemon fight with an outcome calling victory or defeat
        # todo update with better fight outcome algorithm
        if self.pokemon1.currentHP == 0:
            self.statuscode = 420
            self.message = "Your active Pokemon has no HP left!"
            return

        if battleType == 'auto':
            retVal = self.battle_auto()
        else:
            retVal = self.battle_turn(move)
        self.statuscode = 420
        return retVal

    def battle_turn(self, move1):
        retVal = {'result': None}
        if move1 == '':
            self.statuscode = 96
            self.message = 'Invalid move sent for turn based battle'
            return retVal
        # get pokemons current fighting HP
        battleHP1 = self.pokemon1.currentHP
        battleHP2 = self.pokemon2.currentHP
        # get pokemons list of moves
        battleMoves2 = self.__removeNullMoves(self.pokemon2.getMoves())

        pbMove = self.__loadMovesConfig(move1)
        damage1 = self.__calculateDamageOfMove(pbMove)
        battleHP2 -= damage1

        if battleHP2 <=0:
            self.pokemon1.currentHP = battleHP1
            self.__victory()
            self.statuscode = 420
            retVal = {'result': 'victory', 'activeMove': move1, 'activeDamage': damage1}
            
        else:
            randMoveSelector = random.randrange(1, len(battleMoves2)+1)
            move2 = battleMoves2[randMoveSelector-1]
            pbMove = self.__loadMovesConfig(move2)
            damage2 = self.__calculateDamageOfMove(pbMove)
            battleHP1 -= damage2
            if battleHP1 <=0:
                self.pokemon1.currentHP = battleHP1
                self.__defeat()
                self.statuscode = 420
                retVal = {'result': 'defeat', 'activeMove': move1, 'activeDamage': damage1, 'enemyMove': move2, 'enemyDamage': damage2}
                
        
        return retVal

    def battle_auto(self):
        """ this function simulates a live battle between two pokemon """
        retVal = {'result': None}
        # get pokemons current fighting HP
        battleHP1 = self.pokemon1.currentHP        
        battleHP2 = self.pokemon2.currentHP
        # get pokemons list of moves
        battleMoves1 = self.__removeNullMoves(self.pokemon1.getMoves())
        battleMoves2 = self.__removeNullMoves(self.pokemon2.getMoves())

        statusMovesCount = 0
        # pokemon goes first
        for x in range(MAX_BATTLE_TURNS):
            randMoveSelector = random.randrange(1, len(battleMoves1)+1)
            move1 = battleMoves1[randMoveSelector-1]
            pbMove = self.__loadMovesConfig(move1)
            power = pbMove['power']
            if power is None and statusMovesCount >= 1:
                continue
            elif power is None:
                statusMovesCount += 1
            damage = self.__calculateDamageOfMove(pbMove)
            battleHP2 -= damage
            print('%s used %s' %(self.pokemon1.pokemonName, battleMoves1[randMoveSelector-1]))
            print('%s did %s damage' %(self.pokemon1.pokemonName, str(damage)))
            if battleHP2 <=0:
                self.pokemon1.currentHP = battleHP1
                self.__victory()
                self.statuscode = 420
                retVal = {'result': 'victory'}
                break
            randMoveSelector = random.randrange(1, len(battleMoves2)+1)
            move2 = battleMoves2[randMoveSelector-1]
            pbMove = self.__loadMovesConfig(move2)
            damage = self.__calculateDamageOfMove(pbMove)
            battleHP1 -= damage
            print('%s used %s' %(self.pokemon2.pokemonName, battleMoves2[randMoveSelector-1]))
            print('%s did %s damage' %(self.pokemon2.pokemonName, str(damage)))
            if battleHP1 <=0:
                self.pokemon1.currentHP = battleHP1
                self.__defeat()
                self.statuscode = 420
                retVal = {'result': 'defeat'}
                break
            
            # max number of turns has occured. Break out of potential infinite loop
            if x == MAX_BATTLE_TURNS - 1:
                self.statuscode = 420
                self.message = 'Failed to defeat enemy pokemon. The Pokemon ran away'
                break
        
        return retVal

    def runAway(self):
        """ run away from battle """
        # todo add a very small chance to not run away and result in defeat using random
        if random.randrange(1,100) <= 8:
            self.__defeat()
            self.statuscode = 420
            self.message = 'You failed to run away! ' + self.message
        else:
            # leaderboard stats
            lb = leaderboard(self.pokemon1.discordId)
            lb.run_away()
            self.statuscode = 420
            self.message = "You successfully got away"
        return self.message

    def catch(self, item=None):
        # roll chance to catch pokemon and it either runs away or
        #poke-ball, great-ball, ultra-ball, master-ball
        if self.pokemon2.discordId is not None:
            self.statuscode = 420
            self.message = "You can only catch Wild Pokemon!"
            return
        
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

        # leaderboard stats
        lb = leaderboard(self.pokemon1.discordId)
        lb.balls_thrown()

        inventory.save()
        if inventory.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during inventory save()"
            return self.message

        if pokemonCaught:
            # leaderboard stats
            lb = leaderboard(self.pokemon1.discordId)
            lb.catch()
            # pokemon caught successfully. Save it to the trainers inventory
            self.pokemon2.discordId = self.pokemon1.discordId
            self.pokemon2.save()
            if self.pokemon2.statuscode == 96:
                self.statuscode = 96
                self.message = 'error occured during pokemon2 save()'
            self.statuscode = 420
            self.message = "You successfully caught the pokemon"
            self.updateUniqueEncounters()

        else:
            self.statuscode = 96
            self.message = "You failed to catch the pokemon. The pokemon ran away!"

        return self.message

    def __victory(self):
        # pokemon1 had victory, calculate gained exp and update current exp
        # calculate money earned, reduced HP points
        self.updateUniqueEncounters()
        expObj = exp(self.pokemon2)
        expGained = expObj.getExpGained()
        evGained = expObj.getEffortValue()
        if expObj.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during experience calculations"
            return 
        newCurrentHP = self.pokemon1.currentHP

        levelUp, retMsg = self.pokemon1.processBattleOutcome(
            expGained, evGained, newCurrentHP)

        resultString = "Your Pokemon gained %s exp." % (expGained)
        # if pokemon leved up
        if levelUp:
            resultString = resultString + ' Your Pokemon leveled up!'
        if retMsg != '':
            resultString = resultString + ' ' + retMsg

        # leaderboard stats
        lb = leaderboard(self.pokemon1.discordId)
        lb.victory()

        self.statuscode = 420
        self.message = resultString
        return 'victory'

    def __defeat(self):
        # pokemon1 lost, update currentHP to 0
        expGained = 0
        evGained = None
        newCurrentHP = 0
        self.pokemon1.processBattleOutcome(expGained, evGained, newCurrentHP)
        if self.pokemon1.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during processBattleOutcome"
            return
        
        # leaderboard stats
        lb = leaderboard(self.pokemon1.discordId)
        lb.defeat()

        self.statuscode = 420
        self.message = "Your Pokemon Fainted."
        return 'defeat'

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
        pbMove = move
        accuracy = pbMove['accuracy']
        if accuracy is None or accuracy == 'null':
            accuracy = 100
        if accuracy < 100:
            rand_accuracy = random.randrange(1, accuracy+1)
            if rand_accuracy > accuracy:
                moveHit = False
        if moveHit:
            power = pbMove['power']
            if power is None:
                return 0
            moveType = pbMove['moveType']
            damage_class = pbMove['damage_class'] # physical or special or status
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

    # TODO: make this a dict, save a db call
    def __getDamageTypeMultiplier(self, moveType, defendingType):
        """ returns a multiplier for the type-effectiveness """
        dmgMult = None
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/typeEffectiveness.json')
        typeEffectivenessConfig = json.load(open(p, 'r'))
        dmgMult = typeEffectivenessConfig[moveType][defendingType]
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
    
    def updateUniqueEncounters(self):
        """ updates the unique encounters table """
        uEncObj = uEnc(self.pokemon1.discordId)
        name = self.pokemon2.pokemonName
        if name == 'articuno':
            uEncObj.articuno = True
        elif name == 'zapdos':
            uEncObj.zapdos = True
        elif name == 'moltres':
            uEncObj.moltres = True
        elif name == 'mewtwo':
            uEncObj.mewtwo = True
        elif name == 'snorlax':
            uEncObj.snorlax = True                
        # elif name == 'magikarp':
        #     uEncObj.magikarp = True
        # elif name == 'charmander':
        #     uEncObj.charmander = True
        # elif name == 'squirtle':
        #     uEncObj.squirtle = True
        # elif name == 'bulbasaur':
        #     uEncObj.bulbasaur = True
        # elif name == 'lapras':
        #     uEncObj.lapras = True
        # elif name == 'hitmonchan':
        #     uEncObj.hitmonchan = True
        # elif name == 'hitmonlee':
        #     uEncObj.hitmonlee = True                                                                                    
        # elif name == 'eevee':
        #     uEncObj.eevee = True
        
        uEncObj.save()      

    def __loadMovesConfig(self, move):
        """ loads and returns the evolutiononfig for the current pokemon """
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/moves.json')
        movesConfig = json.load(open(p, 'r'))
        
        # this is the evolution json object from the config file
        moveJson = movesConfig[move]
        return moveJson