# location class
import os
import sys
import config
import json
import random
from keyitemsclass import keyitems as kitems
from loggerclass import logger as log
from dbclass import db as dbconn
from questclass import quests as qObj
from models.location import LocationModel
from models.quest import QuestModel
from models.actionmodel import ActionType, ActionModel

# Global Config Variables
VERSION_DETAILS_LIST = config.version_details_list
# Class Logger
logger = log()


actions = {
    'walk': ActionModel('Tall Grass', ActionType.ENCOUNTER, 'walk'),
    'surf': ActionModel('Surf', ActionType.ENCOUNTER, 'surf'),
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
            # Extract unique methods
            methods = list(dict.fromkeys(x['method'] for x in areaEncounters))
            
            # Define desired method order
            method_order = ['walk', 'surf', 'old-rod', 'good-rod', 'super-rod', 'pokeflute', 'gift', 'only-one']
            
            # Sort methods by the defined order
            methods = sorted(methods, key=lambda m: method_order.index(m) if m in method_order else 999)
            
            # Load trainer's key items to filter out unavailable methods
            keyitems = kitems(self.discordId)
            
            for method in methods:
                # Check if trainer owns required key item for this method
                include_method = True
                
                if method == 'old-rod':
                    if not keyitems.old_rod:
                        include_method = False
                elif method == 'good-rod':
                    if not keyitems.good_rod:
                        include_method = False
                elif method == 'super-rod':
                    if not keyitems.super_rod:
                        include_method = False
                elif method == 'surf':
                    if not keyitems.HM03:
                        include_method = False
                elif method == 'pokeflute':
                    if not keyitems.pokeflute:
                        include_method = False
                
                # Only add method if trainer has the required item (or no item required)
                if include_method:
                    methodList.append(actions[method])
            
            # --- MissingNo Easter Egg: inject Surf at Cinnabar Island ---
            if locationId == 71:
                try:
                    db2 = dbconn()
                    stepQuery = 'SELECT missingno_step FROM trainer WHERE discord_id = %(discordId)s'
                    stepResult = db2.querySingle(stepQuery, {'discordId': self.discordId})
                    missingno_step = stepResult[0] if stepResult and stepResult[0] else 0
                    del db2
                    
                    if missingno_step == 2 and keyitems.HM03:
                        from helpers.helpers import check_hm_usable
                        can_surf, _ = check_hm_usable(self.discordId, 'HM03')
                        if can_surf:
                            # Only add surf if it's not already in the list
                            surf_already_present = any(m.value == 'surf' for m in methodList)
                            if not surf_already_present:
                                methodList.append(actions['surf'])
                except:
                    logger.error(excInfo=sys.exc_info())
            # --- End MissingNo injection ---

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
            
            # --- MissingNo Easter Egg: Surf at Cinnabar Island ---
            if locationId == 71 and selectedMethod == 'surf':
                try:
                    db_check = dbconn()
                    stepQuery = 'SELECT missingno_step FROM trainer WHERE discord_id = %(discordId)s'
                    stepResult = db_check.querySingle(stepQuery, {'discordId': self.discordId})
                    missingno_step = stepResult[0] if stepResult and stepResult[0] else 0
                    del db_check
                    
                    if missingno_step == 2:
                        # Return missing-chode encounter data
                        areaEncounterPokemon = {
                            'name': 'missing-chode',
                            'chance': 100,
                            'max_level': 55,
                            'min_level': 55,
                            'method': 'surf'
                        }
                        return areaEncounterPokemon
                except:
                    logger.error(excInfo=sys.exc_info())
            # --- End MissingNo override ---
            
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

            # Reset Elite Four progress when entering Indigo Plateau Center
            if int(locationId) == 2331:
                from battleclass import battle as BattleClass
                BattleClass.resetEliteFour(self.discordId)

            # Elite Four room progression - must defeat current room's trainer before advancing
            elite_four_requirements = {
                2333: 'elite-4-1',  # Must beat Lorelei (2332) to enter Bruno's room
                2334: 'elite-4-2',  # Must beat Bruno (2333) to enter Agatha's room
                2335: 'elite-4-3',  # Must beat Agatha (2334) to enter Lance's room
                2336: 'elite-4-4',  # Must beat Lance (2335) to enter Champion's room
            }
            required_uuid = elite_four_requirements.get(int(locationId))
            if required_uuid:
                checkQuery = 'SELECT 1 FROM trainer_battles WHERE discord_id = %(discordId)s AND enemy_uuid = %(enemy_uuid)s'
                result = db.querySingle(checkQuery, { 'discordId': self.discordId, 'enemy_uuid': required_uuid })
                if not result:
                    self.statuscode = 420
                    self.message = 'You must defeat the trainer in this room before advancing!'
                    return

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

            # --- MissingNo Easter Egg step tracking ---
            try:
                stepQuery = 'SELECT missingno_step FROM trainer WHERE discord_id = %(discordId)s'
                stepResult = db.querySingle(stepQuery, {'discordId': self.discordId})
                current_step = stepResult[0] if stepResult and stepResult[0] else 0
                
                if current_step == 1:
                    # Player talked to old man, now check if they're flying to cinnabar (71)
                    if int(locationId) == 71:
                        db.execute('UPDATE trainer SET missingno_step = 2 WHERE discord_id = %(discordId)s', {'discordId': self.discordId})
                    else:
                        # Went somewhere else — reset
                        db.execute('UPDATE trainer SET missingno_step = 0 WHERE discord_id = %(discordId)s', {'discordId': self.discordId})
                elif current_step == 2:
                    # Player is at cinnabar with step 2 active, leaving resets it
                    if int(locationId) != 71:
                        db.execute('UPDATE trainer SET missingno_step = 0 WHERE discord_id = %(discordId)s', {'discordId': self.discordId})
            except:
                logger.error(excInfo=sys.exc_info())
            # --- End MissingNo tracking ---

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
