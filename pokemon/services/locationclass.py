# location class
import sys
import config
import pokebase as pb
import random
from loggerclass import logger as log

# Global Config Variables
VERSION_DETAILS_LIST = config.version_details_list
# Class Logger
logger = log()

"""
list of cities and locations: https://pokeapi.co/api/v2/region/1/
"""

class location:
    def __init__(self):
        self.statuscode = 69
        self.message = ''
    
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

    def getMethods(self, areaEncounters):
        """ returns a list of methods available in that area """
        methodList = []
        try:
            for x in areaEncounters:
                method = x['method']
                if method not in methodList:
                    methodList.append(method)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return methodList

    def generateEncounter(self, areaEncounters, selectedMethod):
        """ returns a list of chance items for the given method in that area """
        encounter = None
        try:
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
                        encounter = x
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return encounter

    def __getUrlNumber(self, url):
        """ takes a url string and parses the unique key value from the end of the url """
        split = url.split('/')
        if split[-1] == '':
            split.pop()
        return split[-1]



