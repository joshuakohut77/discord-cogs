# location class
import os
import sys
import config
import json
import random
from services.keyitemsclass import keyitems as kitems
from services.loggerclass import logger as log
from services.dbclass import db as dbconn
from services.questclass import quests as qObj
from models.location import LocationModel
from models.quest import QuestModel
from models.actionmodel import ActionType, ActionModel

# Global Config Variables
VERSION_DETAILS_LIST = config.version_details_list
# Class Logger
logger = log()


actions = {
    'walk': ActionModel('Walk', ActionType.ENCOUNTER, 'walk'),
    'old-rod': ActionModel('Old Rod', ActionType.ENCOUNTER, 'old-rod'),
    'good-rod': ActionModel('Good Rod', ActionType.ENCOUNTER, 'good-rod'),
    'super-rod': ActionModel('Super Rod', ActionType.ENCOUNTER, 'super-rod'),
    'only-one': ActionModel('Legendary', ActionType.ONLYONE, 'only-one'),
    'gift': ActionModel('Gift', ActionType.GIFT, 'gift'),
    'pokeflute': ActionModel('Poké Flute', ActionType.ENCOUNTER, 'pokeflute'),
    # TODO: ActionModel for each quest?
}


"""
list of cities and locations: https://pokeapi.co/api/v2/region/1/
"""

class location:
    def __init__(self, discordId=None):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId

    def getLocationByName(self, locationName: str):
        """ Queries and returns location based off of location name """
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/locationNames.json')
        locationsConfig = json.load(open(p, 'r'))

        result = locationsConfig[locationName]
        # TODO replace this load with object in memory
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/locations.json')
        locationsConfig = json.load(open(p, 'r'))
        locResult = locationsConfig[str(result)]
        loc = LocationModel(locResult)
        return loc


    def getMethods(self):
        """ returns a list of methods available in that area """
        methodList = []
        locationId = 0
        try:
            # TODO replace this load with object in memory
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/encounters.json')
            encountersConfig = json.load(open(p, 'r'))
            if self.discordId is None:
                self.statuscode = 420
                self.message = 'discordId required in location constructor'
            else:
                locationId = self.__getCurrentLocation()
                if locationId > 0:
                    areaEncounters = encountersConfig[str(locationId)]

            # map each method name, then make a set.
            # A `set` removes duplicate values.
            methods = set(map(lambda x: x['method'], areaEncounters))
            for method in methods:
                methodList.append(actions[method])
            
            
            # This next section checks if there's any valid quests in current area
            # TODO replace this load with object in memory
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/quests.json')
            questsConfig = json.load(open(p, 'r'))
            quest = QuestModel(questsConfig[str(locationId)])
            if quest.questName != []:
                questObj = qObj(self.discordId)
                if questObj.prerequsitesValid(quest.prerequsites):
                    for questMethod in quest.questName:
                        if not questObj.questComplete(questMethod):
                            methodList.append(ActionModel(questMethod, ActionType.QUEST, questMethod))

        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return methodList

    def action(self, selectedMethod):
        """ returns a single encounter based on location and method """
        areaEncounterPokemon = None
        locationId = 0
        try:
            # TODO replace this load with object in memory
            if self.discordId is None:
                self.statuscode = 420
                self.message = 'discordId required in location constructor'
            else:
                p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/encounters.json')
                encountersConfig = json.load(open(p, 'r'))
                locationId = self.__getCurrentLocation()
                if locationId > 0:
                    areaEncounters = encountersConfig[str(locationId)]
            
            totalChance = 0
            encounterList = []
            action = actions[selectedMethod]

            for x in areaEncounters:
                method = x['method']
                if method == action.value:
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
            # TODO replace this load with object in memory
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/quests.json')
            questsConfig = json.load(open(p, 'r'))
            quest = QuestModel(questsConfig[str(locationId)])
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
