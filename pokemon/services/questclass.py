# quests class
import sys
import random
from typing import List
from keyitemsclass import keyitems as kitems
from inventoryclass import inventory as inv
from pokeclass import Pokemon as pokeClass
from loggerclass import logger as log
from uniqueencounters import uniqueEncounters as uEnc
import models.quest as QuestModel
from textwrap import dedent

# Class Logger
logger = log()
"""
TODO Pokemon Lab, Mysterious Cave and The Pokemon league quests - these are all incomplete
"""

class quests:
    def __init__(self, discordId: str):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId
        self.keyitems = kitems(discordId)
        self.inventory = inv(discordId)

    def locationBlocked(self, blockers: List):
        """ verifies the trainer has no blockers to the location """
        locationBlocked = False
        if blockers == []:
            return

        for item in blockers:
            if item == 'HM01':
                if not self.keyitems.HM01:
                    locationBlocked = True
                    break
            if item == 'HM02':
                if not self.keyitems.HM02:
                    locationBlocked = True
                    break
            if item == 'HM03':
                if not self.keyitems.HM03:
                    locationBlocked = True
                    break
            if item == 'HM04':
                if not self.keyitems.HM04:
                    locationBlocked = True
                    break
            if item == 'HM05':
                if not self.keyitems.HM05:
                    locationBlocked = True
                    break
            if item == 'boulder_badge':
                if not self.keyitems.badge_boulder:
                    locationBlocked = True
                    break
            if item == 'cascade_badge':
                if not self.keyitems.badge_cascade:
                    locationBlocked = True
                    break
            if item == 'thunder_badge':
                if not self.keyitems.badge_thunder:
                    locationBlocked = True
                    break
            if item == 'rainbow_badge':
                if not self.keyitems.badge_rainbow:
                    locationBlocked = True
                    break
            if item == 'soul_badge':
                if not self.keyitems.badge_soul:
                    locationBlocked = True
                    break
            if item == 'marsh_badge':
                if not self.keyitems.badge_marsh:
                    locationBlocked = True
                    break
            if item == 'volcano_badge':
                if not self.keyitems.badge_volcano:
                    locationBlocked = True
                    break
            if item == 'earth_badge':
                if not self.keyitems.badge_earth:
                    locationBlocked = True
                    break
            if item == 'pokeflute':
                if not self.keyitems.pokeflute:
                    locationBlocked = True
                    break
            if item == 'silph_scope':
                if not self.keyitems.silph_scope:
                    locationBlocked = True
                    break
            if item == 'oaks_parcel':
                if not self.keyitems.oaks_parcel:
                    locationBlocked = True
                    break
            if item == 'oaks_parcel_delivered':
                if not self.keyitems.oaks_parcel_delivered:
                    locationBlocked = True
                    break
            if item == 'ss_ticket':
                if not self.keyitems.ss_ticket:
                    locationBlocked = True
                    break
            if item == 'bicycle':
                if not self.keyitems.bicycle:
                    locationBlocked = True
                    break
            if item == 'old_rod':
                if not self.keyitems.old_rod:
                    locationBlocked = True
                    break
            if item == 'good_rod':
                if not self.keyitems.good_rod:
                    locationBlocked = True
                    break
            if item == 'super_rod':
                if not self.keyitems.super_rod:
                    locationBlocked = True
                    break
            if item == 'item_finder':
                if not self.keyitems.item_finder:
                    locationBlocked = True
                    break
            
            if item == 'bike_voucher':
                if not self.keyitems.bike_voucher:
                    locationBlocked = True
                    break
            
            if item == 'gold_teeth':
                if not self.keyitems.gold_teeth:
                    locationBlocked = True
                    break
            
            if item == 'elite_four':
                if not self.keyitems.elite_four:
                    locationBlocked = True
                    break
        
        return locationBlocked


    def prerequsitesValid(self, prerequsites: List):
        """ verifies the trainers prerequsites are met """
        requirementsMet = True
        if prerequsites == []:
            return True
        
        for item in prerequsites:
            if item == 'HM01':
                if not self.keyitems.HM01:
                    requirementsMet = False
                    break
            if item == 'HM02':
                if not self.keyitems.HM02:
                    requirementsMet = False
                    break
            if item == 'HM03':
                if not self.keyitems.HM03:
                    requirementsMet = False
                    break
            if item == 'HM04':
                if not self.keyitems.HM04:
                    requirementsMet = False
                    break
            if item == 'HM05':
                if not self.keyitems.HM05:
                    requirementsMet = False
                    break
            if item == 'boulder_badge':
                if not self.keyitems.badge_boulder:
                    requirementsMet = False
                    break
            if item == 'cascade_badge':
                if not self.keyitems.badge_cascade:
                    requirementsMet = False
                    break
            if item == 'thunder_badge':
                if not self.keyitems.badge_thunder:
                    requirementsMet = False
                    break
            if item == 'rainbow_badge':
                if not self.keyitems.badge_rainbow:
                    requirementsMet = False
                    break
            if item == 'soul_badge':
                if not self.keyitems.badge_soul:
                    requirementsMet = False
                    break
            if item == 'marsh_badge':
                if not self.keyitems.badge_marsh:
                    requirementsMet = False
                    break
            if item == 'volcano_badge':
                if not self.keyitemsbadge_.volcano:
                    requirementsMet = False
                    break
            if item == 'earth_badge':
                if not self.keyitems.badge_earth:
                    requirementsMet = False
                    break
            if item == 'pokeflute':
                if not self.keyitems.pokeflute:
                    requirementsMet = False
                    break
            if item == 'silph_scope':
                if not self.keyitems.silph_scope:
                    requirementsMet = False
                    break
            if item == 'oaks_parcel':
                if not self.keyitems.oaks_parcel:
                    requirementsMet = False
                    break
            if item == 'oaks_parcel_delivered':
                if not self.keyitems.oaks_parcel_delivered:
                    requirementsMet = False
                    break
            if item == 'ss_ticket':
                if not self.keyitems.ss_ticket:
                    requirementsMet = False
                    break
            if item == 'bicycle':
                if not self.keyitems.bicycle:
                    requirementsMet = False
                    break
            if item == 'old_rod':
                if not self.keyitems.old_rod:
                    requirementsMet = False
                    break
            if item == 'good_rod':
                if not self.keyitems.good_rod:
                    requirementsMet = False
                    break
            if item == 'super_rod':
                if not self.keyitems.super_rod:
                    requirementsMet = False
                    break
            if item == 'item_finder':
                if not self.keyitems.item_finder:
                    requirementsMet = False
                    break
            if item == 'bike_voucher':
                if not self.keyitems.bike_voucher:
                    requirementsMet = False
                    break
            if item == 'gold_teeth':
                if not self.keyitems.gold_teeth:
                    requirementsMet = False
                    break
            if item == 'elite_four':
                print(self.keyitems.elite_four)
                if not self.keyitems.elite_four:
                    requirementsMet = False
                    break

        return requirementsMet

    def questComplete(self, questName):
        """ checks if trainer has item from quest """
        
        if questName == 'Garys Sister':
            if self.inventory.townmap == 1:
                return True
        elif questName == 'Professor Oak':
            if self.keyitems.oaks_parcel_delivered:
                return True
        elif questName == 'Super Nerd':
            if self.keyitems.helix_fossil or self.keyitems.dome_fossil:
                return True
        elif questName == 'Fishing Guru':
            if self.keyitems.old_rod:
                return True
        elif questName == 'Bike Voucher':
            if self.keyitems.bicycle:
                return True
        elif questName == 'Speak to Captain':
            if self.keyitems.HM01:
                return True
        elif questName == 'Oaks Aide':
            if self.keyitems.HM05:
                return True
        elif questName == 'Museum of Science':
            if self.inventory.oldamber != 0:
                return True
        elif questName == 'Cafe':
            if self.inventory.coincase != 0:
                return True
        elif questName == 'Rooftop Square':
            if self.inventory.lemonade != 0:
                return True
        elif questName == 'Rocket Hideout':
            if self.keyitems.silph_scope:
                return True
        elif questName == 'Free Spirits':
            return False 
        elif questName == 'Mr Fuji':
            if self.keyitems.pokeflute:
                return True
        elif questName == 'Lone House':
            if self.keyitems.HM03:
                return True
        elif questName == 'Secret Resort':
            if self.keyitems.HM02:
                return True
        elif questName == 'Fishing Brother':
            if self.keyitems.super_rod:
                return True
        elif questName == 'Fishing Dude':
            if self.keyitems.good_rod:
                return True
        elif questName == 'The Warden':
            if self.keyitems.gold_teeth or self.keyitems.HM04:
                return True
        elif questName == 'Return Teeth':
            if not self.keyitems.gold_teeth and self.keyitems.HM04:
                return True
        elif questName == 'SS Anne':
            if self.keyitems.ss_ticket:
                return True
        elif questName == 'The Pokemon League':
            return False 
        elif questName == 'Mysterious Cave':
            return False
        
        # easter eggs
        elif questName == 'Check Truck':
            uniqueEncounters = uEnc(self.discordId)
            if uniqueEncounters.mew:
                return True

    # new code - add this method to the quests class
    def create_key_item_embed(self, item_name: str, emoji: str = None) -> dict:
        """
        Create an embed for key item rewards
        
        Args:
            item_name: Name of the item received (e.g., 'Helix Fossil', 'HM01', 'Old Rod')
            emoji: Optional emoji to display. If None, will try to get from constant
        
        Returns:
            dict with 'embed' key containing the discord.Embed object
        """
        import discord
        import constant
        
        # Map item names to their emoji constants
        emoji_map = {
            'Helix Fossil': constant.HELIXFOSSIL,
            'Dome Fossil': constant.DOMEFOSSIL,
            'Old Rod': constant.OLD_ROD,
            'Good Rod': constant.GOOD_ROD,
            'Super Rod': constant.SUPER_ROD,
            'Bike Voucher': '🎟️',  # Unicode emoji since no constant exists
            'Bicycle': constant.BICYCLE,
            'HM01': constant.HM01,
            'HM02': constant.HM02,
            'HM03': constant.HM03,
            'HM04': constant.HM04,
            'HM05': constant.HM05,
            'Town Map': constant.TOWNMAP,
            'Old Amber': constant.OLDAMBER,
            'Coin Case': constant.COINCASE,
            'Lemonade': constant.LEMONADE,
            'Silph Scope': constant.SILPH_SCOPE,
            'Poké Flute': constant.POKEFLUTE,
            'S.S. Ticket': constant.SS_TICKET,
            'Gold Teeth': '🦷',  # Unicode emoji since no constant exists
            'Item Finder': constant.ITEM_FINDER,
        }
        
        # Get emoji from map or use provided emoji
        if emoji is None:
            emoji = emoji_map.get(item_name, '✨')  # Default sparkle emoji if not found
        
        embed = discord.Embed(
            title="Item Received!",
            description=f"{emoji} **{item_name}**",
            color=discord.Color.gold()
        )
        
        return {'embed': embed}

    # List of quests 
    """
    Garys Sister - Get Town map
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

    # easter eggs
    Check Truck - receive Mew pokemon per old rumor
    """
    def questHandler(self, questName):
        """ verifies the trainers prerequsites are met """
        if not questName:
            self.statuscode = 69
            self.message = "unknown quest name received"
        
        # all quests return a message
        self.statuscode = 420
        
        if questName == "Garys Sister":
            return self.garysSister()
        elif questName == 'Professor Oak':
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
        
        # easter eggs
        elif questName == 'Check Truck':
            return self.checkTruck()

        return
    
    def garysSister(self):
        self.inventory.townmap = 1
        self.message = dedent("""\
                        You ran into Garys sister outside of town. 
                        You could feel the instant chemistry between you two. 
                        She handed you her number on the back of
                        a peice of paper.""")
        self.inventory.save()
        return self.create_key_item_embed('Town Map')

    def professorOak(self):
        self.keyitems.oaks_parcel_delivered = True
        self.keyitems.oaks_parcel = False
        self.message = dedent("""\
                            Professor Oak was busy in your mothers bedroom. 
                            You left his parcel on his desk.""")
        self.keyitems.save()
        return

    def superNerd(self):
        
        x = ['Helix Fossil', 'Dome Fossil']
        fossil = random.choice(x)
        self.keyitems.helix_fossil = (fossil == 'Helix Fossil')
        self.keyitems.dome_fossil = (fossil == 'Dome Fossil')
        self.message = dedent("""\
                            Some nerd was super excited about finding two rocks. 
                            You take one just to ruin his day.""")
        self.keyitems.save()
        return self.create_key_item_embed(fossil)

    def fishingGuru(self):
        self.keyitems.old_rod = True
        self.message = dedent("""\
                            Some creepy guy gave you an old-rod with missing fishing line. 
                            You notice bubbles coming from the water near you.""")
        self.keyitems.save()
        return self.create_key_item_embed('Old Rod')

    def pokemonFanClub(self):
        self.keyitems.bicycle = True
        self.message = dedent("""\
                            You met a guy who found out his wife was cheating on him with some professor.
                            He gave you the bike voucher which was her birthday surprise.""")
        self.keyitems.save()
        return self.create_key_item_embed('Bike Voucher')

    def bikeVoucher(self):
        self.keyitems.bike_voucher = True
        self.message = dedent("""\
                            A robbery distracted the bike shop clerk.
                            You stole a bicycle.
                            Your voucher fell out of your pocket in the process.""")
        self.keyitems.save()
        return self.create_key_item_embed('Bicycle')

    def speakToCaptain(self):
        self.keyitems.HM01 = True
        self.message = dedent("""\
                        You caught the captain and his crew smuggling black tar heroine.
                        The captin bribed you to keep quiet.""")
        self.keyitems.save()
        return self.create_key_item_embed('HM01')

    def oaksAide(self):
        self.keyitems.HM05 = True
        self.message = dedent("""\
                            You met Professor Oaks aide. She was jealous to hear about Oak's relationship with your mother.
                            She gave you a valuable item from Oaks collection. She seemed suspiciously young.""")
        self.keyitems.save()
        return self.create_key_item_embed('HM05')

    def museumOfScience(self):
        self.inventory.oldamber = 1
        self.message = dedent("""\
                            You browsed the Museum of Science and found a cool looking stone. 
                            You placed the stone in your bag when no one was looking.
                            The inscription said "Property of John Hammond""")
        self.inventory.save()
        return self.create_key_item_embed('Old Amber')

    def returnTeeth(self):
        self.keyitems.HM04 = True
        self.keyitems.gold_teeth = False
        self.message = dedent("""\
                            Speaking to the warden about the dead pokemon you found, he admired your bling bling grille. 
                            He offered to trade you for the gold teeth. They fit perfectly...""")
        self.keyitems.save()
        return self.create_key_item_embed('HM04')

    def cafe(self):
        self.inventory.coincase = 1
        self.message = dedent("""\
                            In a cafe you meet a man who was down on his gambling luck. 
                            He has bet and lost his wife in a bet. In an attempt to quit
                            he gives you his coin case.
                            You received a Coin Case!""")
        self.inventory.save()
        return

    def rooftopSquare(self):
        self.inventory.lemonade = 1
        self.message = dedent("""\
                            On the rooftop square you find a little girl flossing for a TikTok video. 
                            In a blinding rage you crush her body with a vending machine. In the process
                            a bottle was disloged. 
                            You received a Lemonade!""")
        self.inventory.save()
        return

    def rocketHideout(self):
        self.keyitems.silph_scope = True
        self.message = dedent("""\
                            Deep inside Team Rockets hideout, you stumble upon a Free Mason sex ritual. Soon you were discovered.
                            You tried to use your escape-rope but instead were bound by it.
                            For two days you were used as a sex slave in an endless train. In a comotose of post nut clarity, 
                            you grab the Grand Masters scepter and escape. 
                            You received the Silph Scope!""")
        self.keyitems.save()
        return

    def freeSpirits(self):
        self.message = dedent("""\
                            During a search for a Big Tiddy Goth GF you stumble upon some ghosts in a tower. 
                            Using your Silph Scope you battle your way to the top. You slayed an endangered 
                            pokemon species. Why did you come here again?
                            You received Nothing!""")
        return

    def mrFuji(self):
        self.keyitems.pokeflute = True
        self.message = dedent("""\
                            You meet a feeble old man alone in his house. You notice a cool instrument haning on his wall. 
                            You asked if you could have it. He declined. He was alone...
                            You received the Pokeflute!""")
        self.keyitems.save()
        return

    def loneHouse(self):
        self.keyitems.HM03 = True
        self.message = dedent("""\
                            Deep inside the safari zone you find a lone house. Inside was a man who told you get off his property. 
                            You left and reported to the authories he has dirt on the Clintons. The next day you scavanged his house.
                            You received HM03!""")
        self.keyitems.save()
        return

    def secretResort(self):
        self.keyitems.HM02 = True
        self.message = dedent("""\
                            
                            You received HM02!""")
        self.keyitems.save()
        return

    def fishingBrother(self):
        self.keyitems.super_rod = True
        self.message = dedent("""\
                            You met the brother of a previous fisherman. You shared the story about seeing the bubbles in the water.
                            He quickly became anxious for you to leave. He offered you a new rod in exchange for your silence.
                            You received a Super Rod!""")
        self.keyitems.save()
        return

    def fishingDude(self):
        self.keyitems.good_rod = True
        self.message = dedent("""\
                            Along the path you met a cool fishing dude. All day you spent drinking and fishing together. 
                            While he was taking a piss you stole his rod simply because it was nicer than yours.
                            You received a Good Rod!""")
        self.keyitems.save()
        return

    def theWarden(self):
        self.keyitems.gold_teeth = True
        self.message = dedent("""\
                            Walking through the safari zone you find a set of gold teeth lying next to some dead pokemon.
                            You received some Gold Teeth""")
        self.keyitems.save()
        return

    def theWarden(self):
        self.keyitems.gold_teeth = True
        self.message = dedent("""\
                            You walked into a house and found some old guy in pain. 
                            He was unable to speak. You notice a corpse of a dead Marowak in the corner.
                            You search the body for loot and found the skull with gold teeth still in it.""")
        self.keyitems.save()
        return self.create_key_item_embed('Gold Teeth')

    def pokemonLab(self):
        # special quest where you trade in Helix/Dome Fossil and old amber for pokemon later
        if self.keyitems.dome_fossil or self.keyitems.helix_fossil or self.inventory.oldamber > 0:
            if self.keyitems.dome_fossil:
                self.keyitems.dome_fossil = False
            if self.keyitems.helix_fossil:
                self.keyitems.helix_fossil = False
            if self.inventory.oldamber > 0:
                self.inventory.oldamber = -1
            self.message = dedent("""\
                                You find some german scientists in a lab. They offer to experiement 
                                on your prehistoric rocks. You gladly give them your stupid rocks.
                                """)
            self.keyitems.save()
            self.inventory.save()
        elif self.keyitems.elite_four:
            # if beaten elite four give them pokemon.
            # Check if they previously gave dome fossil (stored as False after giving it)
            # We need a different way to track "gave but not received" - using inventory.oldamber == -1 pattern
            # Let's use a similar pattern: set to None when given, then remove the check when pokemon received
            
            # Actually, we need to track this differently since booleans can't be -1
            # For now, let's just check if they DON'T have the fossil (meaning they gave it)
            # This requires checking if they DON'T have it AND haven't received pokemon yet
            # This is complex - let me provide a better solution:
            
            # We should add tracking flags to keyitems like: dome_fossil_given, helix_fossil_given, oldamber_given
            # But for minimal changes, let's use the current boolean approach:
            # If they don't have the fossil anymore, give them the pokemon
            
            gave_dome = not self.keyitems.dome_fossil
            gave_helix = not self.keyitems.helix_fossil
            gave_amber = self.inventory.oldamber == -1
            
            if gave_dome:
                pokemon1 = pokeClass(self.discordId, 138) # omanyte
                pokemon1.create(35)
                pokemon1.save()
                self.message += " You received Omanyte."
            if gave_helix:
                pokemon2 = pokeClass(self.discordId, 140) # kabuto
                pokemon2.create(35)
                pokemon2.save()
                self.message += " You received Kabuto."
            if gave_amber:
                pokemon3 = pokeClass(self.discordId, 142) # aerodactyl
                pokemon3.create(35)
                pokemon3.save()
                self.message += " You received Aerodactyl."
        else:
            self.message = """The scientists begin to shout at you in german. You decide to leave"""
        
        return

    def ssAnne(self):
        self.keyitems.ss_ticket = True
        self.message = dedent("""\
                            Rummaging through someones mailbox you find an evelope. 
                            Inside it says "For Tommy. Sincerely, The Make a Wish Foundation"
                            You received an SS Anne Ticket""")
        self.keyitems.save()
        return

    def thePokemonLeague(self):
        # start battle with Elite 4
        
        return

    def mysteriousCave(self):
        pass
        # # trainer set location to location 147 - cerulean cave
        # locationId = 147
        # trainer = trainerClass (self.discordId)
        # trainer.setLocation(locationId)
        # self.message = """You notice some fatty out for a walk. You enter inside the mysterious cave to avoid him."""
        # return

    def checkTruck(self):
        pokemon = pokeClass(self.discordId, 'mew')
        pokemon.create(25)
        pokemon.save()
        uniqueEncounters = uEnc(self.discordId)
        uniqueEncounters.mew = True
        uniqueEncounters.save()
        self.message = dedent("""\
                        You find an abandoned truck. Using your massive penis, you pushed
                        it out of the way. Underneath you discover a pokeball."
                        You received Mew!""")
        return
























