# location class
import sys
import config
import pokebase as pb
import random
from keyitemsclass import keyitems as kitems
from loggerclass import logger as log
from dbclass import db as dbconn
from models.location import LocationModel

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
    
    def getAreaEncounterDetails(self, areaIdList):
        """ returns a list of encounter details in json format """
        pokemonEncounterList = []
        try:
            for areaIdDict in areaIdList:
                for areaId in areaIdDict:
                    locObj = pb.location_area(areaId)
                    for encounter in locObj.pokemon_encounters:
                        encounterDetails = {}
                        for version in encounter.version_details:
                            versionName = version.version.name
                            if versionName in VERSION_DETAILS_LIST:
                                for details in version.encounter_details:
                                    encounterDetails['name'] = encounter.pokemon.name
                                    encounterDetails['chance'] = details.chance
                                    encounterDetails['max_level'] = details.max_level
                                    encounterDetails['min_level'] = details.min_level
                                    encounterDetails['method'] = details.method.name
                                    # this if section is to check for the previous value and not append to list if duplicate
                                    if len(pokemonEncounterList) > 0:
                                        if encounterDetails == pokemonEncounterList[-1]:
                                            continue
                                    pokemonEncounterList.append(encounterDetails)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return pokemonEncounterList

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
    
    def getLocationList(self, region=1):
        """ returns a dictionary list of locations and their unique API number """
        # default region to 1 for Gen1 pokemon locations
        locationList = []
        try:
            regionObj = pb.region(region)
            for location in regionObj.locations:
                name = location.name
                locationNumber = self.__getUrlNumber(location.url)
                locationList.append({name: locationNumber})
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return locationList

    def getAreaList(self, location):
        """ returns a dictionary list of location areas and their unique API number """
        areaList = []
        try:
            areaObj = pb.location(location)
            for area in areaObj.areas:
                name = area.name
                areaNumber = self.__getUrlNumber(area.url)
                areaList.append({name: areaNumber})
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return areaList

    def getMethods(self, areaEncounters=None):
        """ returns a list of methods available in that area """
        methodList = []
        try:
            if self.discordId is not None and areaEncounters is None:
                locationId = self.__getCurrentLocation()
                if locationId > 0:
                    areaList = self.getAreaList(locationId)
                    areaEncounters = self.getAreaEncounterDetails(areaList)
            for x in areaEncounters:
                method = x['method']
                if method not in methodList:
                    methodList.append(method)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return methodList

    def action(self, selectedMethod, areaEncounters=None):
        """ returns a single encounter based on location and method """
        areaEncounterPokemon = None
        try:
            if self.discordId is not None and areaEncounters is None:
                locationId = self.__getCurrentLocation()
                if locationId > 0:
                    areaList = self.getAreaList(locationId)
                    areaEncounters = self.getAreaEncounterDetails(areaList)
            totalChance = 0
            for x in areaEncounters:
                method = x['method']
                if method == selectedMethod:
                    chance = x['chance']
                    totalChance += chance
            for x in areaEncounters:
                method = x['method']
                if method == selectedMethod:
                    chance = x['chance']
                    randNum = random.randrange(1, totalChance+1)
                    chance = x['chance']
                    if randNum <= chance:
                        areaEncounterPokemon = x
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return areaEncounterPokemon

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
