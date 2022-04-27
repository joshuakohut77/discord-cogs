# location class

import pokebase as pb
from .config import *

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
                if versionName in version_details_list:
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

    def __getUrlNumber(self, url):
        """ takes a url string and parses the unique key value from the end of the url """
        split = url.split('/')
        if split[-1] == '':
            split.pop()
        return split[-1]



