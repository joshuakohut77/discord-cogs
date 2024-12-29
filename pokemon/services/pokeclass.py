# pokemon user class

import sys

# import discord
import os
import config
import math
import json
import random
from services.dbclass import db as dbconn
from leaderboardclass import leaderboard
from loggerclass import logger as log
# from pokebase.interface import APIResource
from statclass import PokeStats
from ailmentsclass import ailment
from time import time

# Global Config Variables
STARTER_LEVEL = config.starterLevel
VERSION_GROUP_NAME = config.version_group_name
MAX_PARTY_SIZE = 6
# Class Logger
logger = log()


class Pokemon:
    def __init__(self, discordId, pokedexId = None):
        self.statuscode = 69 
        self.message = '' 

        self.trainerId = None
        self.discordId = discordId
        self.pokedexId = pokedexId
        self.pokemonName = None
        self.pokebaseObj = None
        self.nickName = None
        self.frontSpriteURL = None
        self.backSpriteURL = None
        self.growthRate = None
        self.currentLevel = None
        self.currentExp = None
        self.traded = None
        self.base_exp = None
        self.type1 = None
        self.type2 = None
        self.shiny = False
        self.party = None
        self.hp = PokeStats('hp')
        self.attack = PokeStats('attack')
        self.defense = PokeStats('defense')
        self.speed = PokeStats('speed')
        self.special_attack = PokeStats('special-attack')
        self.special_defense = PokeStats('special-defense')
        self.move_1 = None
        self.move_2 = None
        self.move_3 = None
        self.move_4 = None
        self.currentHP = None
        self.uniqueEncounter = False
        self.ailments = ailment(None)

    def load(self, pokemonId=None):
        """ populates the object with stats from pokeapi """
        if pokemonId is None:
            self.statuscode = 96
            self.message = 'pokeclass#load pokemonId is None'
            return
        
        # load pokemon from db using trainerId as unique primary key from Pokemon table
        self.__loadPokemonFromDB(pokemonId)
        self.frontSpriteURL = self.__getFrontSpritePath()
        self.backSpriteURL = self.__getBackSpritePath()

    # TODO: make static method
    def create(self, level):
        """ creates a new pokemon with generated stats at a given level """
        # this function is used to create new pokemon and will auto generate their level 1 moves
        if type(level) != int:
            self.statuscode = 96
            self.message = 'pokeclass#create level is not an int'
        if level <= 0 or level > 100:
            self.statuscode = 96
            self.message = 'pokeclass#create level must be greater than 0 and less than or equal to 100'
        
        try:
            # this section is for Gary/Blue to dynamically change the pokemon based on the trainers starter pokemon
            if self.pokedexId == 'dynamic-1' or self.pokedexId == 'dynamic-2' or self.pokedexId == 'dynamic-3':
                # pokemon needs changed to fit the trainers playthru
                starterName = self.__getStarterName()
                if starterName == 'squirtle':
                    if self.pokedexId == 'dynamic-1':
                        self.pokedexId = 'bulbasaur'
                    elif self.pokedexId == 'dynamic-2':
                        self.pokedexId = 'ivysaur'
                    elif self.pokedexId == 'dynamic-3':
                        self.pokedexId = 'venusaur'
                elif starterName == 'charmander':
                    if self.pokedexId == 'dynamic-1':
                        self.pokedexId = 'squirtle'
                    elif self.pokedexId == 'dynamic-2':
                        self.pokedexId = 'wartortle'
                    elif self.pokedexId == 'dynamic-3':
                        self.pokedexId = 'blastoise'
                elif starterName == 'bulbasaur' or starterName == 'rattata': # rattata is for trolling purposes 
                    if self.pokedexId == 'dynamic-1':
                        self.pokedexId = 'charmander'
                    elif self.pokedexId == 'dynamic-2':
                        self.pokedexId = 'charmeleon'
                    elif self.pokedexId == 'dynamic-3':
                        self.pokedexId = 'charizard'

            # this is the pokemon json object from the config file
            pokemon = self.__loadPokemonConfig()

            self.currentLevel = level

            self.pokemonName = pokemon['name']
            self.pokedexId = pokemon['id']
            self.frontSpriteURL = self.__getFrontSpritePath()
            self.backSpriteURL = self.__getBackSpritePath()
            self.growthRate = pokemon['growthRate']
            self.base_exp = pokemon['base_experience']

            self.type1 = pokemon['type1']
            self.type2 = pokemon['type2']

            self.traded = False
            self.currentExp = self.__getBaseLevelExperience()
            ivDict = self.__generatePokemonIV()
            evDict = self.__generatePokemonEV()
            baseDict = pokemon['stats']
            self.__setPokeStats(baseDict, ivDict, evDict)

            moveList = self.getMoves(pokemon['moves'])
            self.move_1 = moveList[0]
            self.move_2 = moveList[1]
            self.move_3 = moveList[2]
            self.move_4 = moveList[3]

            statsDict = self.getPokeStats()
            self.currentHP = statsDict['hp']
            self.statuscode = 69

        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())


    def save(self):
        """ saves a pokemon to the database """
        # this function assumes the pokemon class object is already populated
        try:
            db = dbconn()
            if self.trainerId is None:
                queryString = """
                    INSERT INTO
                        pokemon("discord_id", "pokemonId", "pokemonName", "growthRate", 
                            "currentLevel", "currentExp", "traded", "base_hp", 
                            "base_attack", "base_defense", "base_speed", "base_special_attack", 
                            "base_special_defense", "IV_hp", "IV_attack", "IV_defense", 
                            "IV_speed", "IV_special_attack", "IV_special_defense", "EV_hp", 
                            "EV_attack", "EV_defense", "EV_speed", "EV_special_attack", 
                            "EV_special_defense", "move_1", "move_2", "move_3", "move_4", 
                            "type_1", "type_2", "nickName", "currentHP", "party")
                        VALUES (%(discordId)s, %(pokemonId)s, %(pokemonName)s,
                            %(growthRate)s, %(currentLevel)s, %(currentExp)s,
                            %(traded)s, %(base_hp)s,%(base_attack)s,
                            %(base_defense)s, %(base_speed)s,
                            %(base_special_attack)s, %(base_special_defense)s,
                            %(IV_hp)s, %(IV_attack)s, %(IV_defense)s, 
                            %(IV_speed)s, %(IV_special_attack)s,
                            %(IV_special_defense)s, %(EV_hp)s, 
                            %(EV_attack)s, %(EV_defense)s, %(EV_speed)s,
                            %(EV_special_attack)s, %(EV_special_defense)s,
                            %(move_1)s, %(move_2)s, %(move_3)s, %(move_4)s, 
                            %(type_1)s, %(type_2)s, %(nickName)s, 
                            %(currentHP)s, %(party)s)
                        RETURNING id
                """
                values = {'discordId': self.discordId, 'pokemonId': self.pokedexId, 'pokemonName': self.pokemonName,
                          'growthRate': self.growthRate, 'currentLevel': self.currentLevel, 'currentExp': self.currentExp,
                          'traded': self.traded, 'base_hp': self.hp.base, 'base_attack': self.attack.base,
                          'base_defense': self.defense.base, 'base_speed': self.speed.base,
                          'base_special_attack': self.special_attack.base, 'base_special_defense': self.special_defense.base,
                          'IV_hp': self.hp.IV, 'IV_attack': self.attack.IV, 'IV_defense': self.defense.IV,
                          'IV_speed': self.speed.IV, 'IV_special_attack': self.special_attack.IV,
                          'IV_special_defense': self.special_defense.IV, 'EV_hp': self.hp.EV,
                          'EV_attack': self.attack.EV, 'EV_defense': self.defense.EV, 'EV_speed': self.speed.EV,
                          'EV_special_attack': self.special_attack.EV, 'EV_special_defense': self.special_defense.EV,
                          'move_1': self.move_1, 'move_2': self.move_2, 'move_3': self.move_3, 'move_4': self.move_4,
                          'type_1': self.type1, 'type_2': self.type2, 'nickName': self.nickName, 
                          'currentHP': self.currentHP, 'party': self.party }
                trainerIds = db.executeAndReturn(queryString, values)
                if trainerIds:
                    self.trainerId = trainerIds[0]
            else:
                queryString = """
                    UPDATE pokemon
                        SET "discord_id"=%(discordId)s, "pokemonId"=%(pokemonId)s, "pokemonName"=%(pokemonName)s, 
                            "growthRate"=%(growthRate)s, "currentLevel"=%(currentLevel)s, "currentExp"=%(currentExp)s,
                            "traded"=%(traded)s, "base_hp"=%(base_hp)s, "base_attack"=%(base_attack)s, 
                            "base_defense"=%(base_defense)s, "base_speed"=%(base_speed)s, 
                            "base_special_attack"=%(base_special_attack)s, "base_special_defense"=%(base_special_defense)s, 
                            "IV_hp"=%(IV_hp)s, "IV_attack"=%(IV_attack)s, "IV_defense"=%(IV_defense)s, 
                            "IV_speed"=%(IV_speed)s, "IV_special_attack"=%(IV_special_attack)s, 
                            "IV_special_defense"=%(IV_special_defense)s, "EV_hp"=%(EV_hp)s, "EV_attack"=%(EV_attack)s, 
                            "EV_defense"=%(EV_defense)s, "EV_speed"=%(EV_speed)s, 
                            "EV_special_attack"=%(EV_special_attack)s, "EV_special_defense"=%(EV_special_defense)s,
                            "move_1"=%(move_1)s, "move_2"=%(move_2)s, "move_3"=%(move_3)s, 
                            "move_4"=%(move_4)s, "nickName"=%(nickName)s, "currentHP"=%(currentHP)s, "party"=%(party)s
                        WHERE id = %(trainerId)s;
                """
                values = {'discordId': self.discordId, 'pokemonId': self.pokedexId, 'pokemonName': self.pokemonName,
                          'growthRate': self.growthRate, 'currentLevel': self.currentLevel, 'currentExp': self.currentExp,
                          'traded': self.traded, 'base_hp': self.hp.base, 'base_attack': self.attack.base,
                          'base_defense': self.defense.base, 'base_speed': self.speed.base,
                          'base_special_attack': self.special_attack.base, 'base_special_defense': self.special_defense.base,
                          'IV_hp': self.hp.IV, 'IV_attack': self.attack.IV, 'IV_defense': self.defense.IV,
                          'IV_speed': self.speed.IV, 'IV_special_attack': self.special_attack.IV,
                          'IV_special_defense': self.special_defense.IV, 'EV_hp': self.hp.EV,
                          'EV_attack': self.attack.EV, 'EV_defense': self.defense.EV, 'EV_speed': self.speed.EV,
                          'EV_special_attack': self.special_attack.EV, 'EV_special_defense': self.special_defense.EV,
                          'move_1': self.move_1, 'move_2': self.move_2, 'move_3': self.move_3, 'move_4': self.move_4,
                          'nickName': self.nickName, 'currentHP': self.currentHP, 'party': self.party, 
                          'trainerId': self.trainerId }

                db.execute(queryString, values)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db

    def release(self):
        """ release a pokemon """
        return self.__delete()

    def getPokeStats(self):
        """ returns a dictionary of a pokemon's unique stats based off level, EV, and IV """
        statsDict = {}
        try:
            level = self.currentLevel
            statsDict['hp'] = self.__calculateUniqueStat(self.hp) + level + 10
            statsDict['attack'] = self.__calculateUniqueStat(self.attack) + 5
            statsDict['defense'] = self.__calculateUniqueStat(self.defense) + 5
            statsDict['speed'] = self.__calculateUniqueStat(self.speed) + 5
            statsDict['special-attack'] = self.__calculateUniqueStat(
                self.special_attack) + 5
            statsDict['special-defense'] = self.__calculateUniqueStat(
                self.special_defense) + 5
        except:
             self.statuscode = 96
             logger.error(excInfo=sys.exc_info())
        finally:
            return statsDict
    
    def getPartySprite(self):
        """ reutrns a path to a pokemon party sprite"""
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/pokemon.json')
        pokemonConfig = json.load(open(p, 'r'))
        return pokemonConfig[self.pokemonName['partySprite']]

    def getMoves(self, moveDict=None):
        """ returns a list of the pokemon's current moves """
        moveList = []
        if moveDict is None:
            moveDict = {}
            # this is the pokemon json object from the config file
            pokemon = self.__loadPokemonConfig()
            moveDict = pokemon['moves']
        try:
            level = self.currentLevel
            # user starter level for pokemon without a level
            if level is None:
                level = STARTER_LEVEL
            # itterate throught he dictionary selecting the top 4 highest moves at the current level
            defaultList = sorted(
                moveDict.items(), key=lambda x: x[1], reverse=True)
            for move in defaultList:
                moveLevel = move[1]
                moveName = move[0]
                if int(moveLevel) <= level:
                    moveList.append(moveName)
            # check if list is padded to move and if not, append blank moves
            if len(moveList) < 4:
                diff = 4-len(moveList)
                for x in range(diff):
                    x = None
                    moveList.append(x)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())

        # return only 4 moves
        return moveList[0: 4]

    def getNextLevelExperience(self):
        return self.__getBaseLevelExperience(level=self.currentLevel+1)

    def processBattleOutcome(self, expGained, evGained, newCurrentHP):
        """ process victory updates and calculations """

        self.currentHP = newCurrentHP
        levelUp = False
        retMsg = ''
        try:
            if newCurrentHP > 0:
                self.currentExp = self.currentExp + expGained

                # {'hp': 0, 'attack': 0, 'defense': 0, 'special-attack': 0, 'special-defense': 0, 'speed': 6}
                if evGained is not None:
                    self.hp.EV = self.hp.EV + evGained['hp']
                    self.attack.EV = self.attack.EV + evGained['attack']
                    self.defense.EV = self.defense.EV + evGained['defense']
                    self.speed.EV = self.speed.EV + evGained['speed']
                    self.special_attack.EV = self.special_attack.EV + \
                        evGained['special-attack']
                    self.special_defense.EV = self.special_defense.EV + \
                        evGained['special-defense']

                # get the base exp of the next level
                nextLevelBaseExp = self.getNextLevelExperience()
                if self.currentExp >= nextLevelBaseExp:
                    # pokemon leveled up. iteratively check exp thresholds to determine the new level
                    for x in range(99):
                        tempLevelBaseExp = self.__getBaseLevelExperience(
                            level=self.currentLevel+x)
                        if tempLevelBaseExp > self.currentExp:
                            self.currentLevel = self.currentLevel + x-1
                            # if a pokemon gains multiple levels, notifications of moves learned will be skipped.
                            # this next section is to handle that unique case
                            moveList = self.getMoves()

                            levelUp = True
                            newMove = self.__getNewMoves()
                            if newMove != '':
                                retMsg += 'Your pokemon learned %s. ' % (
                                    newMove)

                            self.move_1 = moveList[3]
                            self.move_2 = moveList[2]
                            self.move_3 = moveList[1]
                            self.move_4 = moveList[0]
                            evolvedForm = self.__checkForEvolution()
                            if evolvedForm is not None:
                                # leaderboard stats
                                lb = leaderboard(self.discordId)
                                lb.evolved()
                                retMsg += 'Your pokemon is evolving......... Your pokemon evolved into %s!' % (
                                    evolvedForm)
                                evolvedPokemon = Pokemon(evolvedForm)
                                evolvedPokemon.create(self.currentLevel)
                                evolvedPokemon.discordId = self.discordId
                                evolvedPokemon.save()
                                self.__delete()
                            break

            # save all above changes included the change in currentHP
            self.save()
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return levelUp, retMsg

    ####
    # Private Class Methods
    ####

    def __loadPokemonFromDB(self, pokemonId):
        """ loads and creates a pokemon object from the database """
        db = dbconn()
        queryString = '''
        SELECT
            pokemon."id",
            "discord_id",
            pokemon."pokemonId",
            "pokemonName", 
            "growthRate",
            "currentLevel",
            "currentExp",
            traded,
            base_hp, base_attack, base_defense, base_speed,
            base_special_attack, base_special_defense, 
            "IV_hp", "IV_attack", "IV_defense", "IV_speed", "IV_special_attack", 
            "IV_special_defense", "EV_hp", "EV_attack", "EV_defense", "EV_speed", 
            "EV_special_attack", "EV_special_defense",
            "move_1", "move_2", "move_3", "move_4",
            "type_1", "type_2",
            "nickName",
            "currentHP",
            "party",
            ailments."mostRecent",
            ailments."sleep",
            ailments."poison",
            ailments."burn",
            ailments."freeze",
            ailments."paralysis",
            ailments."trap",
            ailments."confusion",
            ailments."disable"
            FROM pokemon
            LEFT JOIN ailments ON pokemon."id" = ailments."pokemonId"
            WHERE "id" = %(pokemonId)s'''
    
        result = db.querySingle(queryString, {'pokemonId': int(pokemonId)})

        if result:
            self.trainerId = result[0]
            self.discordId = result[1]
            self.pokedexId = result[2]
            self.pokemonName = result[3]
            self.growthRate = result[4]
            self.currentLevel = result[5]
            self.currentExp = result[6]
            self.traded = result[7]
            self.hp.base = result[8]
            self.attack.base = result[9]
            self.defense.base = result[10]
            self.speed.base = result[11]
            self.special_attack.base = result[12]
            self.special_defense.base = result[13]
            self.hp.IV = result[14]
            self.attack.IV = result[15]
            self.defense.IV = result[16]
            self.speed.IV = result[17]
            self.special_attack.IV = result[18]
            self.special_defense.IV = result[19]
            self.hp.EV = result[20]
            self.attack.EV = result[21]
            self.defense.EV = result[22]
            self.speed.EV = result[23]
            self.special_attack.EV = result[24]
            self.special_defense.EV = result[25]
            self.move_1 = result[26]
            self.move_2 = result[27]
            self.move_3 = result[28]
            self.move_4 = result[29]
            self.type1 = result[30]
            self.type2 = result[31]
            self.nickName = result[32]
            self.currentHP = result[33]
            self.party = result[34]

            self.ailments = ailment(self.trainerId)
            # below is populating the ailments from the pokemon load class.
            # this saves a db call from having to call the load method from the ailments class
            # only populate if the mostRecent result is not Null
            if result[35] is not None:
                self.ailments.mostRecent = result[35]
                self.ailments.sleep = result[36]
                self.ailments.poison = result[37]
                self.ailments.burn = result[38]
                self.ailments.freeze = result[39]
                self.ailments.paralysis = result[40]
                self.ailments.trap = result[41]
                self.ailments.confusion = result[42]
                self.ailments.disable = result[43]

        # delete and close connection
        del db

    def __delete(self):
        """ soft deletes pokemon from database """
        try:
            db = dbconn()
            # use milliseconds as a way to get a unique number. used to soft delete a value and still retain original discordId
            milliString = str(int(time() * 1000))
            newDiscordId = self.discordId + '_' + milliString
            pokemonUpdateQuery = 'UPDATE pokemon SET "discord_id" = %(newDiscordId)s WHERE "id" = %(trainerId)s'
            db.execute(pokemonUpdateQuery, {
                       'newDiscordId': newDiscordId, 'trainerId': self.trainerId})
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db

    def __getFrontSpritePath(self):
        """ returns a path to pokemon front sprite """
        basePath = self.__getSpriteBasePath()
        return basePath + "%s.png" % self.pokedexId

    def __getBackSpritePath(self):
        """ returns a path to pokemon back sprite """
        basePath = self.__getSpriteBasePath()
        return basePath + "back/%s.png" % self.pokedexId

    def __getSpriteBasePath(self):
        """ returns a base path to pokemon sprites """
        #query the db to see if they're using legacy sprites or not
        # result = None
        # try:
        #     db = dbconn()
        #     queryString = 'SELECT "legacySprites" FROM trainer WHERE "discord_id" = %(discordId)s'
        #     result = db.querySingle(queryString, { 'discordId': str(self.discordId) })
        # except:
        #     self.statuscode = 96
        #     logger.error(excInfo=sys.exc_info())
        # finally:
        #     # delete object and close connection
        #     del db

        # legacySprites = False
        # if result:
        #     legacySprites = result[0]

        # if legacySprites:
        #     basePath = "https://pokesprites.joshkohut.com/sprites/pokemon/versions/generation-i/red-blue/transparent/"
        # else:
        #     basePath = "https://pokesprites.joshkohut.com/sprites/pokemon/"
        basePath = "https://pokesprites.joshkohut.com/sprites/pokemon/"
        # if the pokemon is a shiny, there is no legacy shiny, so the path will be overwritten regardless
        if self.shiny:
            return"https://pokesprites.joshkohut.com/sprites/pokemon/shiny/"
        return basePath

    def __getNewMoves(self, moveDict=None):
        """ returns a pokemons moves at a specific level """
        newMove = ''
        if moveDict is None:
            moveDict = {}
            # this is the pokemon json object from the config file
            pokemon = self.__loadPokemonConfig()
            moveDict = pokemon['moves']
        try:
            for key, value in moveDict.items():
                if value == self.currentLevel:
                    newMove = key
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return newMove

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
        try:
            attack = random.randrange(0, 16)
            defense = random.randrange(0, 16)
            speed = random.randrange(0, 16)
            special_attack = random.randrange(0, 16)
            special_defense = special_attack

            hp = int(format(attack, 'b').zfill(4)[3] + format(defense, 'b').zfill(4)[
                    3] + format(speed, 'b').zfill(4)[3] + format(special_attack, 'b').zfill(4)[3], 2)

            ivDict['hp'] = hp
            ivDict['attack'] = attack
            ivDict['defense'] = defense
            ivDict['speed'] = speed
            ivDict['special-attack'] = special_attack
            ivDict['special-defense'] = special_defense
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return ivDict

    def __generatePokemonEV(self):
        """ returns dictionary of base generated effort values """
        evDict = {'hp': 1, 'attack': 1, 'defense': 1, 'speed': 1,
                  'special-attack': 1, 'special-defense': 1}
        return evDict

    def __getBaseLevelExperience(self, level=None):
        """ returns minimum total experience at a given level """
        if level is None:
            level = self.currentLevel
        if self.growthRate == 'fast':
            return round(0.8 * (level ** 3))
        elif self.growthRate == 'medium-fast' or self.growthRate == 'medium':
            return round(level ** 3)
        elif self.growthRate == 'medium-slow':
            return round(1.2*(level ** 3)-(15*(level ** 2)) + 100*level - 140)
        elif self.growthRate == 'slow':
            return round(1.25 * (level ** 3))
        else:
            self.statuscode = 96
            self.message = 'pokemons growRate was not valid. '
            return 0

    def __setPokeStats(self, baseDict, ivDict, evDict):
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

    def __checkForEvolution(self):
        """ returns boolean if a current pokemon is eligible for evolution """
        evoList = self.__loadEvolutionConfig()
        evolvedForm = None
        for item in evoList:
            name = item['name']
            min_level = item['min_level']
            if min_level is not None and name != self.pokemonName:
                # possible evolution
                if self.currentLevel >= min_level:
                    # eligibal evolution, continue checking for more
                    evolvedForm = name
        return evolvedForm

    def __getPokemonNameById(self, pokedexId):
        """ returns a pokemon name from thier id """
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/pokemonId.json')
        pokemonIdConfig = json.load(open(p, 'r'))
        return pokemonIdConfig[str(pokedexId)]

    def __loadPokemonConfig(self):
        """ loads and returns the pokmonconfig for the current pokemon """
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/pokemon.json')
        pokemonConfig = json.load(open(p, 'r'))
        
        # check if pokedexId is int and convert to string name
        if type(self.pokedexId) is int:
            key = self.__getPokemonNameById(self.pokedexId)
        else:
            key = self.pokedexId
        # this is the pokemon json object from the config file
        pokemon = pokemonConfig[str(key)]
        return pokemon
    
    def __loadEvolutionConfig(self):
        """ loads and returns the evolutiononfig for the current pokemon """
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/evolutions.json')
        evolutionConfig = json.load(open(p, 'r'))

        # check if pokedexId is int and convert to string name
        if type(self.pokedexId) is int:
            key = self.__getPokemonNameById(self.pokedexId)
        else:
            key = self.pokedexId
        # this is the evolution json object from the config file
        evolutionList = evolutionConfig[str(key)]
        return evolutionList
    
    def __getStarterName(self):
        """ returns the name of the starter pokemon for the current trainer"""
        starterName = ''
        try:
            db = dbconn()
            queryString = 'SELECT "starterName" FROM trainer WHERE "discord_id" = %(discordId)s'
            result = db.querySingle(queryString, { 'discordId': str(self.discordId) })
            starterName = result[0]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete object and close connection
            del db
            return starterName
