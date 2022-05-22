# quests class
import sys
from typing import List
from keyitemsclass import keyitems as kitems
from loggerclass import logger as log
import models.quest as QuestModel
from keyitemsclass import keyitems as kitems

# Class Logger
logger = log()


class quests:
    def __init__(self, discordId: str):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId

    def locationBlocked(self, blockers: List):
        """ verifies the trainer has no blockers to the location """
        locationBlocked = False
        if blockers == []:
            return
        keyitems = kitems(self.discordId)
        for item in blockers:
            if item == 'HM01':
                if not keyitems.HM01:
                    locationBlocked = True
                    break
            if item == 'HM02':
                if not keyitems.HM02:
                    locationBlocked = True
                    break
            if item == 'HM03':
                if not keyitems.HM03:
                    locationBlocked = True
                    break
            if item == 'HM04':
                if not keyitems.HM04:
                    locationBlocked = True
                    break
            if item == 'HM05':
                if not keyitems.HM05:
                    locationBlocked = True
                    break
            if item == 'badge_boulder':
                if not keyitems.badge_boulder:
                    locationBlocked = True
                    break
            if item == 'badge_cascade':
                if not keyitems.badge_cascade:
                    locationBlocked = True
                    break
            if item == 'badge_thunder':
                if not keyitems.badge_thunder:
                    locationBlocked = True
                    break
            if item == 'badge_rainbow':
                if not keyitems.badge_rainbow:
                    locationBlocked = True
                    break
            if item == 'badge_soul':
                if not keyitems.badge_soul:
                    locationBlocked = True
                    break
            if item == 'badge_marsh':
                if not keyitems.badge_marsh:
                    locationBlocked = True
                    break
            if item == 'badge_volcano':
                if not keyitems.badge_volcano:
                    locationBlocked = True
                    break
            if item == 'badge_earth':
                if not keyitems.badge_earth:
                    locationBlocked = True
                    break
            if item == 'pokeflute':
                if not keyitems.pokeflute:
                    locationBlocked = True
                    break
            if item == 'silph_scope':
                if not keyitems.silph_scope:
                    locationBlocked = True
                    break
            if item == 'oaks_parcel':
                if not keyitems.oaks_parcel:
                    locationBlocked = True
                    break
            if item == 'oaks_parcel_delivered':
                if not keyitems.oaks_parcel_delivered:
                    locationBlocked = True
                    break
            if item == 'ss_ticket':
                if not keyitems.ss_ticket:
                    locationBlocked = True
                    break
            if item == 'bicycle':
                if not keyitems.bicycle:
                    locationBlocked = True
                    break
            if item == 'old_rod':
                if not keyitems.old_rod:
                    locationBlocked = True
                    break
            if item == 'good_rod':
                if not keyitems.good_rod:
                    locationBlocked = True
                    break
            if item == 'super_rod':
                if not keyitems.super_rod:
                    locationBlocked = True
                    break
            if item == 'item_finder':
                if not keyitems.item_finder:
                    locationBlocked = True
                    break
        
        return locationBlocked


    def prerequsitesValid(self, prerequsites: List):
        """ verifies the trainers prerequsites are met """
        requirementsMet = True
        if prerequsites == []:
            return
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

# List of quests 
"""
Professor Oak - deliver parcel
Super Nerd - Get Helix Fossil item
Fishing Guru - get old-rod item
Bike Voucher - get bicycle item
Speak to Captain - get HM01
Oaks Aide - get HM05
Museum of Science - get Old Amber
Cafe - get coin_case item
Rooftop Square - get lemonade item
Rocket Hideout - get silph_scope
Free Spirits - nothing
Mr Fuji - get pokeflute
Lone House - get HM03
Secret Resort - get HM02
Fishing Brother - get super_rod
Fishing Dude - get good_rod
The Warden - get gold_teeth
Return Teeth - get HM04
Pokemon Lab - take helix or dome fossile and Old Amber and turn into Pokemon
SS Anne - get ss_ticket item
The Pokemon League - battle the elite 4
"""