# quests class
import sys
import random
from typing import List
from keyitemsclass import keyitems as kitems
from inventoryclass import inventory as inv
from pokeclass import Pokemon as pokeClass
from loggerclass import logger as log
from trainerclass import trainer as trainerClass
import models.quest as QuestModel

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
        
        # all quests return a message
        self.statuscode = 420
        
        if questName == 'Professor Oak':
            return self.professorOak()
        elif questName == 'Super Nerd':
            return self.superNerd()
        elif questName == 'Fishing Guru':
            return self.fishingGuru()
        elif questName == 'Bike Voucher':
            return self.bikeVoucher()
        elif questName == 'Speak to Captain':
            return self.speakToCaptain()
        elif questName == 'Oaks Aide':
            return self.oaksAide()
        elif questName == 'Museum of Science':
            return self.museumOfScience()
        elif questName == 'Cafe':
            return self.cafe()
        elif questName == 'Rooftop Square':
            return self.rooftopSquare()
        elif questName == 'Rocket Hideout':
            return self.rocketHideout()
        elif questName == 'Free Spirits':
            return self.freeSpirits()
        elif questName == 'Mr Fuji':
            return self.mrFuji()
        elif questName == 'Lone House':
            return self.loneHouse()
        elif questName == 'Secret Resort':
            return self.secretResort()
        elif questName == 'Fishing Brother':
            return self.fishingBrother()
        elif questName == 'Fishing Dude':
            return self.fishingDude()
        elif questName == 'The Warden':
            return self.theWarden()
        elif questName == 'Return Teeth':
            return self.returnTeeth()
        elif questName == 'SS Anne':
            return self.ssAnne()
        elif questName == 'The Pokemon League':
            return self.thePokemonLeague()
        elif questName == 'Mysterious Cave':
            return self.mysteriousCave()


        return
    

    def professorOak(self):
        keyitems = kitems(self.discordId)
        keyitems.oaks_parcel_delivered = True
        keyitems.oaks_parcel = False
        self.message = """You found Professor Oak in your 
                            mothers bedroom and delivered his parcel."""
        keyitems.save()
        return

    def superNerd(self):
        inventory = inv(self.discordId)
        
        x = ['Helix Fossil', 'Dome Fossil']
        fossil = random.choice(x)
        if fossil == 'Helix Fossil':
            inventory.helixfossil = 1
            inventory.domefossil = 0
        else:
            inventory.helixfossil = 0
            inventory.domefossil = 1
        self.message = """Some nerd was super excited about finding two rocks. 
                            You take one just to ruin his day. 
                            You received a %s!""" %(fossil)
        inventory.save()
        return

    def fishingGuru(self):
        keyitems = kitems(self.discordId)
        keyitems.old_rod = True
        self.message = """Some creepy guy gave you an old-rod with missing fishing line. 
                            You notice bubbles comeing from the lake near you.
                            You received an Old Rod!"""
        keyitems.save()
        return

    def bikeVoucher(self):
        keyitems = kitems(self.discordId)
        keyitems.bike_voucher = True
        self.message = """You met a guy who found out his wife was cheating on him with some professor.
                            He gave you the bike voucher which was her birthday surprise. 
                            You received a Bike Voucher!"""
        keyitems.save()
        return

    def speakToCaptain(self):
        keyitems = kitems(self.discordId)
        keyitems.HM01 = True
        self.message = """You caught the captain and his crew smuggling black tar heroine.
                            The captin bribed you to keep quiet.  
                            You received HM01!"""
        keyitems.save()
        return

    def oaksAide(self):
        keyitems = kitems(self.discordId)
        keyitems.HM05 = True
        self.message = """You met Professor Oaks aide. She was jealous to hear about his relationship with your mother.
                            She gave you a valuable item from Oaks collection. She seemed suspiciously young.
                            You received HM05!"""
        keyitems.save()
        return

    def museumOfScience(self):
        inventory = inv(self.discordId)
        inventory.oldamber = 1
        self.message = """You browsed the Museum of Science and found a cool looking stone. 
                            You placed the stone in your bag when no one was looking.
                            The inscription said "Property of John Hammond"
                            You received some Old Amber!"""
        inventory.save()
        return

    def cafe(self):
        inventory = inv(self.discordId)
        inventory.coincase = 1
        self.message = """In a cafe you meet a man who was down on his gambling luck. 
                            He has bet and lost his wife in a bet. In an attempt to quit
                            he gives you his coin case.
                            You received a Coin Case!"""
        inventory.save()
        return

    def rooftopSquare(self):
        inventory = inv(self.discordId)
        inventory.lemonade = 1
        self.message = """On the rooftop square you find a little girl flossing for a TikTok video. 
                            In a blinding rage you crush her body with a vending machine. In the process
                            a bottle was disloged. 
                            You received a Lemonade!"""
        inventory.save()
        return

    def rocketHideout(self):
        keyitems = kitems(self.discordId)
        keyitems.silph_scope = True
        self.message = """Deep inside Team Rockets hideout, you stumble upon a Free Mason sex ritual. Soon you were discovered.
                            You tried to use your escape-rope but instead were bound by it.
                            For two days you were used as a sex slave in an endless train. In a comotose of post nut clarity, 
                            you grab the Grand Masters scepter and escape. 
                            You received the Silph Scope!"""
        keyitems.save()
        return

    def freeSpirits(self):
        self.message = """During a search for a Big Tiddy Goth GF you stumble upon some ghosts in a tower. 
                            Using your Silph Scope you battle your way to the top. You slayed an endangered 
                            pokemon species. Why did you come here again?
                            You received Nothing!"""
        return

    def mrFuji(self):
        keyitems = kitems(self.discordId)
        keyitems.pokeflute = True
        self.message = """You meet a feeble old man alone in his house. You notice a cool instrument haning on his wall. 
                            You asked if you could have it. He declined. He was alone...
                            You received the Pokeflute!"""
        keyitems.save()
        return

    def loneHouse(self):
        keyitems = kitems(self.discordId)
        keyitems.HM03 = True
        self.message = """Deep inside the safari zone you find a lone house. Inside was a man who told you get off his property. 
                            You left and reported to the authories he has dirt on the Clintons. The next day you scavanged his house.
                            You received HM03!"""
        keyitems.save()
        return

    def secretResort(self):
        keyitems = kitems(self.discordId)
        keyitems.HM02 = True
        self.message = """
                            You received HM02!"""
        keyitems.save()
        return

    def fishingBrother(self):
        keyitems = kitems(self.discordId)
        keyitems.super_rod = True
        self.message = """You met the brother of a previous fisherman. You shared the story about seeing the bubbles in the water.
                            He quickly became anxious for you to leave. He offered you a new rod in exchange for your silence.
                            You received a Super Rod!"""
        keyitems.save()
        return

    def fishingDude(self):
        keyitems = kitems(self.discordId)
        keyitems.good_rod = True
        self.message = """Along the path you met a cool fishing dude. All day you spent drinking and fishing together. 
                            While he was taking a piss you stole his rod simply because it was nicer than yours.
                            You received a Good Rod!"""
        keyitems.save()
        return

    def theWarden(self):
        keyitems = kitems(self.discordId)
        keyitems.gold_teeth = True
        self.message = """Walking through the safari zone you find a set of gold teeth lying next to some dead pokemon.
                            You received some Gold Teeth"""
        keyitems.save()
        return

    def returnTeeth(self):
        keyitems = kitems(self.discordId)
        keyitems.HM04 = True
        keyitems.gold_teeth = False
        self.message = """Speaking to the warden about the dead pokemon you found, he admired your bling bling grille. 
                            He offered to trade you for the gold teeth. They fit perfectly...
                            You received HM04"""
        keyitems.save()
        return

    def pokemonLab(self):
        # special quest where you trade in Helix/Dome Fossil and old amber for pokemon later
        keyitems = kitems(self.discordId)
        inventory = inv(self.discordId)
        if inventory.domefossil > 0 or inventory.helixfossil > 0 or inventory.oldamber > 0:
            if inventory.domefossil > 0:
                inventory.domefossil = -1
            if inventory.helixfossil > 0:
                inventory.helixfossil = -1
            if inventory.oldamber > 0:
                inventory.oldamber = -1
            self.message = """You find some german scientists in a lab. They offer to experiement 
                                on your prehistoric rocks. You gladly give them your stupid rocks.
                                """
            inventory.save()
        elif keyitems.elite_four:
            # if beaten elite four give them pokemon.
            if inventory.domefossil == -1:
                pokemon1 = pokeClass(self.discordId, 138) # omanyte
                pokemon1.create(35)
                pokemon1.save()
                self.message += " You received Omanyte."
            if inventory.helixfossil == -1:
                pokemon2 = pokeClass(self.discordId, 140) # kabuto
                pokemon2.create(35)
                pokemon2.save()
                self.message += " You received Kabuto."
            if inventory.oldamber == -1:
                pokemon3 = pokeClass(self.discordId, 142) # aerodactyl
                pokemon3.create(35)
                pokemon3.save()
                self.message += " You received Aerodactyl."
        else:
            self.message = """The scientists begin to shout at you in german. You decide to leave"""
        
        return

    def ssAnne(self):
        keyitems = kitems(self.discordId)
        keyitems.ss_ticket = True
        self.message = """Rummaging through someones mailbox you find an evelope. 
                            Inside it says "For Tommy. Sincerely, The Make a Wish Foundation"
                            You received an SS Anne Ticket"""
        keyitems.save()
        return

    def thePokemonLeague(self):
        # start battle with Elite 4
        
        return

    def mysteriousCave(self):
        # trainer set location to location 147 - cerulean cave
        locationId = 147
        trainer = trainerClass (self.discordId)
        trainer.setLocation(locationId)
        self.message = """You notice some fatty out for a walk. You enter inside the mysterious cave to avoid him."""
        return


























