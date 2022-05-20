# location class
import sys
import config
import configs.quests
import json
import random
from keyitemsclass import keyitems as kitems
from loggerclass import logger as log
from dbclass import db as dbconn
from questclass import quests as qObj
from models.location import LocationModel
from models.quest import QuestModel

# Global Config Variables
VERSION_DETAILS_LIST = config.version_details_list
# Class Logger
logger = log()

"""
list of cities and locations: https://pokeapi.co/api/v2/region/1/
"""

class location:
    def __init__(self, discordId = None):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId

    def getLocationByName(self, locationName: str):
        """ Queries and returns location based off of location name """
        try:
            db = dbconn()
            queryStr = """
            SELECT
                *
            FROM locations
                WHERE locations."name" = %(name)s
            """
            result = db.querySingle(queryStr, { 'name': locationName })
            if result:
                loc = LocationModel(result)
                return loc
            else:
                self.statuscode = 96
                self.message = 'Location not found'
        except:
            self.statuscode = 96
        finally:
            del db

    def getMethods(self, areaEncounters=None):
        """ returns a list of methods available in that area """
        methodList = []
        try:
            # TODO replace this load with object in memory
            encountersConfig = json.load(open('./configs/encounters.json', 'r'))

            if self.discordId is not None and areaEncounters is None:
                locationId = self.__getCurrentLocation()
                if locationId > 0:
                    areaEncounters = encountersConfig[str(locationId)]
            for x in areaEncounters:
                method = x['method']
                if method not in methodList:
                    methodList.append(method)
            
            # This next section checks if there's any valid quests in current area
            quest = QuestModel(configs.quests.questConfig[locationId])
            questObj = qObj(self.discordId)
            if quest.prerequsites != []:
                if questObj.prerequsitesValid(quest.prerequsites):
                    methodList.append(quest.questName)

        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return methodList

    def action(self, selectedMethod, areaEncounters=None):
        """ returns a single encounter based on location and method """
        areaEncounterPokemon = None
        try:
            # TODO replace this load with object in memory
            encountersConfig = json.load(open('./configs/encounters.json', 'r'))
            if self.discordId is not None and areaEncounters is None:
                locationId = self.__getCurrentLocation()
                if locationId > 0:
                    areaEncounters = encountersConfig[str(locationId)]
            totalChance = 0
            encounterList = []
            for x in areaEncounters:
                method = x['method']
                if method == selectedMethod:
                    chance = x['chance']
                    for counter in range(chance):
                        encounterList.append(x)
                    totalChance += chance
            
            randNum = random.randrange(0, totalChance)
            areaEncounterPokemon = encounterList[randNum]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return areaEncounterPokemon
    
    def setLocation(self, locationId):
        """ updates the trainer table to set the locationId """
        try:
            db = dbconn()

            # This next section checks if there's any valid quests in current area
            quest = QuestModel(configs.quests.questConfig[locationId])
            questObj = qObj(self.discordId)
            if quest.blockers != []:
                if questObj.locationBlocked(quest.blockers):
                    self.statuscode = 420
                    self.message = 'You have not completed all prior quests to advance'
                    return

            updateString = """
            UPDATE trainer
                SET "locationId"=%(locationId)s
            WHERE trainer."discord_id" = %(discordId)s
            """
            db.execute(updateString, { 'locationId': locationId, 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
            raise
        finally:
            # delete and close connection
            del db

    def __getUrlNumber(self, url):
        """ takes a url string and parses the unique key value from the end of the url """
        split = url.split('/')
        if split[-1] == '':
            split.pop()
        return split[-1]

    def __getCurrentLocation(self):
        """ returns the location of the discordId user if not None """
        locationId = 0
        try:
            db = dbconn()
            if self.discordId is not None:
                queryStr = """
                SELECT
                    "locationId"
                FROM trainer
                    WHERE trainer."discord_id" = %(discordId)s
                """
                result = db.querySingle(queryStr, { 'discordId': self.discordId })
                if result:
                    locationId = result[0]
                    return locationId
                else:
                    self.statuscode = 96
                    self.message = 'Location not found'
        except:
            self.statuscode = 96
        finally:
            del db
