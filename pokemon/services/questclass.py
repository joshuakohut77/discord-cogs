# quests class
import sys
from typing import List
from keyitemsclass import keyitems as kitems
from loggerclass import logger as log
import models.quest as quests
from services.keyitemsclass import keyitems

# Class Logger
logger = log()


class quests:
    def __init__(self, discordId: str):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId

    def prerequsitesValid(self, prerequsites: List):
        """ verifies the trainers prerequsites are met """
        requirementsMet = True
        keyitems = kitems(self.discordId)
        for item in prerequsites:
            if item == 'HM01':
                if not keyitems.HM01:
                    requirementsMet = False
                    break
            if item == 'HM02':
                if not keyitems.HM02:
                    requirementsMet = False
                    break
            if item == 'HM03':
                if not keyitems.HM03:
                    requirementsMet = False
                    break
            if item == 'HM04':
                if not keyitems.HM04:
                    requirementsMet = False
                    break
            if item == 'HM05':
                if not keyitems.HM05:
                    requirementsMet = False
                    break
            if item == 'badge_boulder':
                if not keyitems.badge_boulder:
                    requirementsMet = False
                    break
            if item == 'badge_cascade':
                if not keyitems.badge_cascade:
                    requirementsMet = False
                    break
            if item == 'badge_thunder':
                if not keyitems.badge_thunder:
                    requirementsMet = False
                    break
            if item == 'badge_rainbow':
                if not keyitems.badge_rainbow:
                    requirementsMet = False
                    break
            if item == 'badge_soul':
                if not keyitems.badge_soul:
                    requirementsMet = False
                    break
            if item == 'badge_marsh':
                if not keyitems.badge_marsh:
                    requirementsMet = False
                    break
            if item == 'badge_volcano':
                if not keyitems.badge_volcano:
                    requirementsMet = False
                    break
            if item == 'badge_earth':
                if not keyitems.badge_earth:
                    requirementsMet = False
                    break
            if item == 'pokeflute':
                if not keyitems.pokeflute:
                    requirementsMet = False
                    break
            if item == 'silph_scope':
                if not keyitems.silph_scope:
                    requirementsMet = False
                    break
            if item == 'oaks_parcel':
                if not keyitems.oaks_parcel:
                    requirementsMet = False
                    break
            if item == 'oaks_parcel_delivered':
                if not keyitems.oaks_parcel_delivered:
                    requirementsMet = False
                    break
            if item == 'ss_ticket':
                if not keyitems.ss_ticket:
                    requirementsMet = False
                    break
            if item == 'bicycle':
                if not keyitems.bicycle:
                    requirementsMet = False
                    break
            if item == 'old_rod':
                if not keyitems.old_rod:
                    requirementsMet = False
                    break
            if item == 'good_rod':
                if not keyitems.good_rod:
                    requirementsMet = False
                    break
            if item == 'super_rod':
                if not keyitems.super_rod:
                    requirementsMet = False
                    break
            if item == 'item_finder':
                if not keyitems.item_finder:
                    requirementsMet = False
                    break
            
        return requirementsMet