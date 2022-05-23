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
            
            if item == 'bike_voucher':
                if not keyitems.bike_voucher:
                    locationBlocked = True
                    break
            
            if item == 'gold_teeth':
                if not keyitems.gold_teeth:
                    locationBlocked = True
                    break
            
            if item == 'elite_four':
                if not keyitems.elite_four:
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
            if item == 'bike_voucher':
                if not keyitems.bike_voucher:
                    requirementsMet = False
                    break
            if item == 'gold_teeth':
                if not keyitems.gold_teeth:
                    requirementsMet = False
                    break
            if item == 'elite_four':
                if not keyitems.elite_four:
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
    Mysterious Cave - move to location 147
    """
    def questHandler(self, questName):
        """ verifies the trainers prerequsites are met """
        if not questName:
            self.statuscode = 69
            self.message = "unknown quest name received"
        
        keyitems = kitems(self.discordId)
        
        if questName == 'Professor Oak':
            return self.professorOak
        elif questName == 'Super Nerd':
            return self.superNerd
        elif questName == 'Fishing Guru':
            return self.fishingGuru
        elif questName == 'Bike Voucher':
            return self.bikeVoucher
        elif questName == 'Speak to Captain':
            return self.speakToCaptain
        elif questName == 'Oaks Aide':
            return self.oaksAide
        elif questName == 'Museum of Science':
            return self.museumOfScience
        elif questName == 'Cafe':
            return self.cafe
        elif questName == 'Rooftop Square':
            return self.rooftopSquare
        elif questName == 'Rocket Hideout':
            return self.rocketHideout
        elif questName == 'Free Spirits':
            return self.freeSpirits
        elif questName == 'Mr Fuji':
            return self.mrFuji
        elif questName == 'Lone House':
            return self.loneHouse
        elif questName == 'Secret Resort':
            return self.secretResort
        elif questName == 'Fishing Brother':
            return self.fishingBrother
        elif questName == 'Fishing Dude':
            return self.fishingDude
        elif questName == 'The Warden':
            return self.theWarden
        elif questName == 'Return Teeth':
            return self.returnTeeth
        elif questName == 'SS Anne':
            return self.ssAnne
        elif questName == 'The Pokemon League':
            return self.thePokemonLeague
        elif questName == 'Mysterious Cave':
            return self.mysteriousCave


        return
    

    def professorOak(self, keyitems):
        
        return

    def superNerd(self, keyitems):
        
        return

    def fishingGuru(self, keyitems):
        
        return

    def bikeVoucher(self, keyitems):
        
        return

    def speakToCaptain(self, keyitems):
        
        return

    def oaksAide(self, keyitems):
        
        return

    def museumOfScience(self, keyitems):
        
        return

    def cafe(self, keyitems):
        
        return

    def rooftopSquare(self, keyitems):
        
        return

    def rocketHideout(self, keyitems):
        
        return

    def freeSpirits(self, keyitems):
        
        return

    def mrFuji(self, keyitems):
        
        return

    def loneHouse(self, keyitems):
        
        return

    def secretResort(self, keyitems):
        
        return

    def fishingBrother(self, keyitems):
        
        return

    def fishingDude(self, keyitems):
        
        return

    def theWarden(self, keyitems):
        
        return

    def returnTeeth(self, keyitems):
        
        return

    def pokemonLab(self, keyitems):
        
        return

    def ssAnne(self, keyitems):
        
        return

    def thePokemonLeague(self, keyitems):
        
        return

    def mysteriousCave(self, keyitems):
        
        return


























