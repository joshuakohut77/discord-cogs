# location class

import pokebase as pb
import random
# import config

# VERSION_DETAILS_LIST = config.version_details_list
VERSION_DETAILS_LIST = ['red', 'blue']

"""
list of cities and locations: https://pokeapi.co/api/v2/region/1/
"""

class location:
    
    def getAreaEncounterDetails(self, areaId):
        """ returns a list of encounter details in json format """
        pokemonEncounterList = []
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
        return pokemonEncounterList

    def getLocationList(self, region=1):
        """ returns a dictionary list of locations and their unique API number """
        # default region to 1 for Gen1 pokemon locations
        locationList = []
        regionObj = pb.region(region)
        for location in regionObj.locations:
            name = location.name
            locationNumber = self.__getUrlNumber(location.url)
            locationList.append({name: locationNumber})
        return locationList

    def getAreaList(self, location):
        """ returns a dictionary list of location areas and their unique API number """
        areaList = []
        areaObj = pb.location(location)
        for area in areaObj.areas:
            name = area.name
            areaNumber = self.__getUrlNumber(area.url)
            areaList.append({name: areaNumber})
        return areaList

    def getMethods(self, areaEncounters):
        """ returns a list of methods available in that area """
        methodList = []
        
        for x in areaEncounters:
            method = x['method']
            if method not in methodList:
                methodList.append(method)
        
        return methodList

    def generateEncounter(self, areaEncounters, selectedMethod):
        """ returns a list of chance items for the given method in that area """
        encounter = None
        for x in areaEncounters:
            method = x['method']
            if method == selectedMethod:
                randNum = random.randrange(1, 101)
                chance = x['chance']
                if randNum <= chance:
                    encounter = x
            
        return encounter

    def __getUrlNumber(self, url):
        """ takes a url string and parses the unique key value from the end of the url """
        split = url.split('/')
        if split[-1] == '':
            split.pop()
        return split[-1]



