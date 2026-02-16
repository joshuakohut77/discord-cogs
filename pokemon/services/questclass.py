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
from dbclass import db as dbconn
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
        self.found_easter_egg = None  # Tuple of (egg_id, display_name) when found

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
                # Also check if they have a Pokemon that can use HM01
                from helpers.helpers import check_hm_usable
                can_use, _ = check_hm_usable(self.discordId, 'HM01')
                if not can_use:
                    locationBlocked = True
                    break
            if item == 'HM02':
                if not self.keyitems.HM02:
                    locationBlocked = True
                    break
                from helpers.helpers import check_hm_usable
                can_use, _ = check_hm_usable(self.discordId, 'HM02')
                if not can_use:
                    locationBlocked = True
                    break
            if item == 'HM03':
                if not self.keyitems.HM03:
                    locationBlocked = True
                    break
                from helpers.helpers import check_hm_usable
                can_use, _ = check_hm_usable(self.discordId, 'HM03')
                if not can_use:
                    locationBlocked = True
                    break
            if item == 'HM04':
                if not self.keyitems.HM04:
                    locationBlocked = True
                    break
                from helpers.helpers import check_hm_usable
                can_use, _ = check_hm_usable(self.discordId, 'HM04')
                if not can_use:
                    locationBlocked = True
                    break
            if item == 'HM05':
                if not self.keyitems.HM05:
                    locationBlocked = True
                    break
                from helpers.helpers import check_hm_usable
                can_use, _ = check_hm_usable(self.discordId, 'HM05')
                if not can_use:
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
            
            if item == 'game_shark':
                if not self.keyitems.game_shark:
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
                if not self.keyitems.badge_volcano:
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

            if item == 'game_shark':
                if not self.keyitems.game_shark:
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
            if self.keyitems.helixfossil != 0 or self.keyitems.domefossil != 0:
                return True
        elif questName == 'Fishing Guru':
            if self.keyitems.old_rod:
                return True
        elif questName == 'Bike Voucher':
            if self.keyitems.bicycle:
                return True
        elif questName == 'Pokemon Fan Club':
            if self.keyitems.bike_voucher or self.keyitems.bicycle:
                return True
        elif questName == 'Porygon':
            uniqueEncounters = uEnc(self.discordId)
            if uniqueEncounters.porygon:
                return True
        # easter eggs
        elif questName == 'Play SNES':
            if self.keyitems.elite_four and self.keyitems.game_shark:
                return True
            elif not self.keyitems.elite_four:
                return True  # Quest is "complete" before Elite Four (no reward)

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
            'Mew': constant.POKEMON_EMOJIS['MEW'],
            'Porygon': constant.POKEMON_EMOJIS['PORYGON'],
            'Aerodactyl': constant.POKEMON_EMOJIS['AERODACTYL'],
            'Kabuto': constant.POKEMON_EMOJIS['KABUTO'],
            'Omanyte': constant.POKEMON_EMOJIS['OMANYTE'],
            'Mr. Fuji\'s Finger': constant.MR_FUJI_FINGER,
            'Eevee\'s Tail': constant.EEVEE_TAIL,
            'Master Ball': constant.MASTERBALL
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
    Play SNES - Fun canon quest
    Search Room - Fun non-canon quest of finding Ash's Mom's toy
    Professor Oak - deliver parcel
    Old Man - the old man teaches you to capture a pokemon
    Super Nerd - Get Helix Fossil item
    Fishing Guru - get old-rod item
    Bike Voucher - get bicycle item
    Speak to Captain - get HM01
    Oaks Aide - get HM05
    Museum of Science - get Old Amber
    Cafe - get coin_case item
    Porygon - get porygon for 100k coin
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
    Master Ball - get master_ball after defeating Giovani
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
        elif questName == 'Old Man':
            return self.oldMan()
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
        elif questName == 'Porygon':
            return self.porygon()
        elif questName == 'Rooftop Square':
            return self.rooftopSquare()
        elif questName == 'Rocket Hideout':
            return self.rocketHideout()
        elif questName == 'Free Spirits':
            return self.freeSpirits()
        elif questName == 'Rescue Mr Fuji':
            return self.rescueMrFuji()
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
        elif questName == 'Pokemon Fan Club':
            return self.pokemonFanClub()
        elif questName == 'Pokemon Lab':
            return self.pokemonLab()
        elif questName == 'SS Anne':
            return self.ssAnne()
        elif questName == 'Master Ball':
            return self.masterBall()
        elif questName == 'The Pokemon League':
            return self.thePokemonLeague()
        elif questName == 'Mysterious Cave':
            return self.mysteriousCave()
        elif questName ==  "Play SNES":
            return self.playSNES()
        elif questName ==  "Search Room":
            return self.searchRoom()
        # easter eggs
        elif questName == 'Check Truck':
            return self.checkTruck()

        return
    
    def garysSister(self):
        self.inventory.townmap = 1
        self.message = dedent("""\
                        You decided to have one last quickie with Gary's sister. She handed you her number on the back of a peice of paper.""")
        self.inventory.save()
        return self.create_key_item_embed('Town Map')

    def searchRoom(self):
        if not self.keyitems.oaks_parcel_delivered:
            # Before delivering Oak's parcel - find nothing
            self.message = dedent("""\
                                You rummage through the room looking for anything interesting. Nothing but dusty old furniture and outdated magazines. What a waste of time.""")
            return None  # No embed, just message
        else:
            # After delivering Oak's parcel - check if already received Eevee's Tail
            if self.keyitems.eevee_tail:
                # Already have Eevee's Tail - just show message
                self.message = dedent("""\
                                    You search the room again, but there's nothing left to find. You already took the mysterious tail you found earlier.""")
                return None
            else:
                # First time - receive Eevee's Tail
                self.keyitems.eevee_tail = True
                self.message = dedent("""\
                                    You rummage through the room more carefully this time. Hidden under your moms bed, you discover a soft, fluffy tail. It seems oddly familiar... You pocket it for later.""")
                self.keyitems.save()
                
                # Track easter egg completion
                from services.leaderboardclass import leaderboard as LeaderboardClass
                lb = LeaderboardClass(str(self.discordId))
                lb.easter_eggs()
                
                # Store easter egg for achievement announcement
                self.found_easter_egg = ('search_room', "Eevee's Tail")
                
                return self.create_key_item_embed('Eevee\'s Tail')
            
    def playSNES(self):
        if not self.keyitems.elite_four:
            # Before Elite Four - just play the game
            self.message = dedent("""\
                                You boot up the dusty old SNES and pop in a cartridge. After hours of gaming, you realize you've accomplished nothing productive. Time well spent.""")
            return None  # No embed, just message
        else:
            # After Elite Four - check if already received Game Shark
            if self.keyitems.game_shark:
                # Already have Game Shark - just show message
                self.message = dedent("""\
                                    You boot up the dusty old SNES and pop in a cartridge. You've already taken the Game Shark from behind the console. Time to play some classics.""")
                return None
            else:
                # First time - receive Game Shark
                self.keyitems.game_shark = True
                self.message = dedent("""\
                                    You boot up the dusty old SNES and pop in a cartridge. Hidden behind the console, you discover an ancient Game Shark device. With this, you could unlock the true potential of your Pokemon...""")
                self.keyitems.save()
                
                # Track easter egg completion
                from services.leaderboardclass import leaderboard as LeaderboardClass
                lb = LeaderboardClass(str(self.discordId))
                lb.easter_eggs()
                
                # Store easter egg for achievement announcement
                self.found_easter_egg = ('play_snes', 'Game Shark')
                
                return self.create_key_item_embed('Game Shark', '🎮')

    def professorOak(self):
        self.keyitems.oaks_parcel_delivered = True
        self.keyitems.oaks_parcel = False
        self.message = dedent("""\
                            Professor Oak was busy in your mothers bedroom. You left his parcel on his desk.""")
        self.keyitems.save()
        return

    def oldMan(self):
        # do stuff here for easter egg pre-fix
        if self.keyitems.elite_four:
            setSomeVariable = 1

        self.message = dedent("""\
                            A nice old man teaches you how to catch a pokemon.""")
        return

    def superNerd(self):
        
        x = ['Helix Fossil', 'Dome Fossil']
        fossil = random.choice(x)
        self.keyitems.helix_fossil = (fossil == 'Helix Fossil')
        self.keyitems.dome_fossil = (fossil == 'Dome Fossil')
        self.message = dedent("""\
                            Some nerd was super excited about finding two rocks. You take one just to ruin his day.""")
        self.keyitems.save()
        return self.create_key_item_embed(fossil)

    def fishingGuru(self):
        self.keyitems.old_rod = True
        self.message = dedent("""\
                            Some creepy guy gave you an old-rod with missing fishing line. You notice bubbles coming from the water near you.""")
        self.keyitems.save()
        return self.create_key_item_embed('Old Rod')

    def pokemonFanClub(self):
        self.keyitems.bike_voucher = True
        self.message = dedent("""\
                            You met a guy who found out his wife was cheating on him with some professor. He gave you the bike voucher which was her birthday surprise.""")
        self.keyitems.save()
        return self.create_key_item_embed('Bike Voucher')

    def bikeVoucher(self):
        self.keyitems.bike_voucher = False
        self.keyitems.bicycle = True
        self.message = dedent("""\
                            A robbery distracted the bike shop clerk. You stole a bicycle. Your voucher fell out of your pocket in the process.""")
        self.keyitems.save()
        return self.create_key_item_embed('Bicycle')

    def speakToCaptain(self):
        self.keyitems.HM01 = True
        self.message = dedent("""\
                        You caught the captain and his crew smuggling black tar heroine. The captin bribed you to keep quiet.""")
        self.keyitems.save()
        return self.create_key_item_embed('HM01')

    def oaksAide(self):
        self.keyitems.HM05 = True
        self.message = dedent("""\
                            You met Professor Oaks aide. She was jealous to hear about Oak's relationship with your mother. She gave you a valuable item from Oaks collection. She seemed suspiciously young.""")
        self.keyitems.save()
        return self.create_key_item_embed('HM05')

    def museumOfScience(self):
        self.keyitems.old_amber = True
        self.message = dedent("""\
                            You browsed the Museum of Science and found a cool looking stone. You placed the stone in your bag when no one was looking. The inscription said \"Property of John Hammond\"""")
        self.keyitems.save()
        return self.create_key_item_embed('Old Amber')

    def returnTeeth(self):
        self.keyitems.HM04 = True
        self.keyitems.gold_teeth = False
        self.message = dedent("""\
                            Speaking to the warden about the dead pokemon you found, he didn't seem phased. He did ask you for the gold teeth. They fit perfectly...""")
        self.keyitems.save()
        return self.create_key_item_embed('HM04')

    def cafe(self):
        self.inventory.coincase = 1
        self.message = dedent("""\
                            In a cafe you meet a man who was down on his gambling luck. He has bet and lost his wife in a bet. In an attempt to quit he gives you his coin case.
                            """)
        self.inventory.save()
        return self.create_key_item_embed('Coin Case')

    def porygon(self):
        from trainerclass import trainer as trainerClass
        from pokedexclass import pokedex
        
        PORYGON_COST = 100000
        
        # Check if trainer has already received Porygon
        uniqueEncounters = uEnc(self.discordId)
        if uniqueEncounters.porygon:
            self.statuscode = 420
            self.message = "You already purchased Porygon!"
            return
        
        # Check if trainer has enough money
        if self.inventory.money < PORYGON_COST:
            self.statuscode = 420
            self.message = f"You don't have enough money! You need ¥{PORYGON_COST:,} but only have ¥{self.inventory.money:,}."
            return
        
        # Deduct money
        self.inventory.money -= PORYGON_COST
        self.inventory.save()
        
        # Create trainer object to check party size
        trainer = trainerClass(self.discordId)
        party_count = trainer.getPartySize()
        
        # Create Porygon Pokemon
        pokemon = pokeClass(self.discordId, 'porygon')
        pokemon.create(26)
        
        # CRITICAL: Set discordId and party status before saving
        pokemon.discordId = self.discordId
        pokemon.party = party_count < 6  # Add to party if there's space, otherwise to PC
        
        # Save the Pokemon
        pokemon.save()
        
        # Check if save was successful
        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "Error occurred while creating Porygon"
            # Refund money on failure
            self.inventory.money += PORYGON_COST
            self.inventory.save()
            return
        
        # Register to Pokedex
        pokedex(self.discordId, pokemon)
        
        # Update unique encounters to mark Porygon as received
        uniqueEncounters.porygon = True
        uniqueEncounters.save()
        
        self.statuscode = 420
        if party_count < 6:
            self.message = f"You purchased Porygon for ¥{PORYGON_COST:,}! Porygon was added to your party."
        else:
            self.message = f"You purchased Porygon for ¥{PORYGON_COST:,}! Your party is full, so Porygon was sent to your PC."
        
        return self.create_key_item_embed('Porygon')

    def rooftopSquare(self):
        self.inventory.lemonade = 1
        self.message = dedent("""\
                            On the rooftop square you find a little girl flossing for a TikTok video. In a blinding rage you crush her body with a vending machine. In the process a bottle was disloged. 
                            """)
        self.inventory.save()
        return self.create_key_item_embed('Lemonade')

    def rocketHideout(self):
        self.keyitems.silph_scope = True
        self.message = dedent("""\
                            Deep inside Team Rockets hideout, you stumble upon a Free Mason sex ritual. Soon you were discovered. You tried to use your escape-rope but instead were bound by it. For two days you were used as a sex slave in an endless train. In a comotose of post nut clarity, you grab the Grand Masters headdress and escape. 
                            """)
        self.keyitems.save()
        return self.create_key_item_embed('Silph Scope')

    def freeSpirits(self):
        self.message = dedent("""\
                            During a search for a Big Tiddy Goth GF you stumble upon some ghosts in a tower. Using your Silph Scope you battle your way to the top. You slayed an endangered pokemon species. Why did you come here again?
                            You received Nothing!""")
        return

    def mrFuji(self):
        self.keyitems.pokeflute = True
        self.message = dedent("""\
                            You meet a feeble old Mr. Fuji alone in his house. You notice a cool instrument haning on his wall. You asked if you could have it. He declined. He was alone...""")
        self.keyitems.save()
        return self.create_key_item_embed('Poké Flute')

    def rescueMrFuji(self):
        self.keyitems.mr_fujis_finger = True
        self.message = dedent("""\
                            At the top of Pokemon Tower, you find Mr. Fuji being held captive by Team Rocket. Using your Silph Scope, you defeat the ghost Pokemon and rescue him. In the scuffle, Mr. Fuji loses a finger. You pocket it as a souvenir.""")
        self.keyitems.save()
        return self.create_key_item_embed('Mr. Fuji\'s Finger', '👆')

    def loneHouse(self):
        self.keyitems.HM03 = True
        self.message = dedent("""\
                            Deep inside the safari zone you find a lone house. Inside was a man who told you get off his property. You left and reported to the authories he has dirt on the Clintons. The next day you scavanged his house.
                            """)
        self.keyitems.save()
        return self.create_key_item_embed('HM03')

    def secretResort(self):
        self.keyitems.HM02 = True
        self.message = dedent("""\
                            You find a secret resort. Inside was a man reminissing about his private island. He offered you an item to keep quiet about this place.""")
        self.keyitems.save()
        return self.create_key_item_embed('HM02')

    def fishingBrother(self):
        self.keyitems.super_rod = True
        self.message = dedent("""\
                            You met the brother of a previous fisherman. You shared the story about seeing the bubbles in the water. He quickly became anxious for you to leave. He offered you a new rod in exchange for your silence.""")
        self.keyitems.save()
        return self.create_key_item_embed('Super Rod')

    def fishingDude(self):
        self.keyitems.good_rod = True
        self.message = dedent("""\
                            Along the path you met a cool fishing dude. All day you spent drinking and fishing together. While he was taking a piss you stole his rod simply because it was nicer than yours.
                            """)
        self.keyitems.save()
        return self.create_key_item_embed('Good Rod')

    # def theWarden(self):
    #     self.keyitems.gold_teeth = True
    #     self.message = dedent("""\
    #                         Walking through the safari zone you find a set of gold teeth lying next to some dead pokemon.
    #                         You received some Gold Teeth""")
    #     self.keyitems.save()
    #     return

    def theWarden(self):
        self.keyitems.gold_teeth = True
        self.message = dedent("""\
                            You walked into a house and found some old guy in pain. He was unable to speak. You notice a corpse of a dead Marowak in the corner. You search the body for loot and found the back of the skull with gold teeth stuck in it.""")
        self.keyitems.save()
        return self.create_key_item_embed('Gold Teeth')

    def pokemonLab(self):
        # special quest where you trade in Helix/Dome Fossil and old amber for pokemon later
        if self.keyitems.dome_fossil or self.keyitems.helix_fossil or self.keyitems.old_amber:
            if self.keyitems.dome_fossil:
                self.keyitems.dome_fossil = False
                self.keyitems.gave_dome = True
            if self.keyitems.helix_fossil:
                self.keyitems.helix_fossil = False
                self.keyitems.gave_helix = True
            if self.keyitems.old_amber:
                self.keyitems.old_amber = False
                self.keyitems.gave_amber = True
            self.message = dedent("""\
                                You find some german scientists in a lab. They offer to experiement on your prehistoric rocks. You gladly give them your stupid rocks.
                                """)
            self.keyitems.save()
            return
        elif self.keyitems.gave_dome or self.keyitems.gave_helix or self.keyitems.gave_amber:
            from trainerclass import trainer as trainerClass
            from pokedexclass import pokedex
            
            trainer = trainerClass(self.discordId)
            received_pokemon = []
            
            if self.keyitems.gave_dome:
                self.keyitems.gave_dome = False
                party_count = trainer.getPartySize()
                
                pokemon1 = pokeClass(self.discordId, 'kabuto')
                pokemon1.create(35)
                pokemon1.discordId = self.discordId
                pokemon1.party = party_count < 6
                pokemon1.save()
                
                if pokemon1.statuscode == 96:
                    self.statuscode = 96
                    self.message = "Error occurred while creating Kabuto"
                    return
                
                pokedex(self.discordId, pokemon1)
                received_pokemon.append(('Kabuto', "The scientists return your Dome Fossil... but it's not a fossil anymore!"))
            
            if self.keyitems.gave_helix:
                self.keyitems.gave_helix = False
                party_count = trainer.getPartySize()
                
                pokemon2 = pokeClass(self.discordId, 'omanyte')
                pokemon2.create(35)
                pokemon2.discordId = self.discordId
                pokemon2.party = party_count < 6
                pokemon2.save()
                
                if pokemon2.statuscode == 96:
                    self.statuscode = 96
                    self.message = "Error occurred while creating Omanyte"
                    return
                
                pokedex(self.discordId, pokemon2)
                received_pokemon.append(('Omanyte', "The scientists return your Helix Fossil... but it's not a fossil anymore!"))
            
            if self.keyitems.gave_amber:
                self.keyitems.gave_amber = False
                party_count = trainer.getPartySize()
                
                pokemon3 = pokeClass(self.discordId, 'aerodactyl')
                pokemon3.create(35)
                pokemon3.discordId = self.discordId
                pokemon3.party = party_count < 6
                pokemon3.save()
                
                if pokemon3.statuscode == 96:
                    self.statuscode = 96
                    self.message = "Error occurred while creating Aerodactyl"
                    return
                
                pokedex(self.discordId, pokemon3)
                received_pokemon.append(('Aerodactyl', "The scientists return your Old Amber... but it's not amber anymore!"))
            
            if received_pokemon:
                import discord
                import constant
                self.keyitems.save()
                pokemon_emojis = []
                for pokemon_name, _ in received_pokemon:
                    emoji = constant.POKEMON_EMOJIS.get(pokemon_name.upper(), '✨')
                    pokemon_emojis.append(f"{emoji} **{pokemon_name}**")
                
                embed = discord.Embed(
                    title="Pokémon Received!",
                    description="\n".join(pokemon_emojis),
                    color=discord.Color.gold()
                )
                
                messages = [msg for _, msg in received_pokemon]
                self.message = "\n\n".join(messages)
                
                return {'embed': embed}
            else:
                self.message = """The scientists begin to shout at you in german. You decide to leave"""
        else:
            self.message = """You don't have any fossils to give the scientists. They shoo you away."""
        
        return

    def masterBall(self):
        """Awards Master Ball if Giovanni (8bf79b06) has been defeated"""
        try:
            db = dbconn()
            queryString = 'SELECT 1 FROM trainer_battles WHERE enemy_uuid = %(enemy_uuid)s AND discord_id = %(discordId)s'
            result = db.querySingle(queryString, {'enemy_uuid': '8bf79b06', 'discordId': self.discordId})
        except:
            logger.error(excInfo=sys.exc_info())
            self.message = "An error occurred checking battle records."
            return
        finally:
            del db

        if not result:
            self.message = "The Master Ball is guarded by Giovanni. You must defeat him first!"
            return

        self.inventory.masterball = 1
        self.inventory.save()
        self.message = dedent("""\
                            After defeating Giovanni, you find a glowing Poké Ball sitting on his desk. The Master Ball — the ultimate catching device. You pocket it before anyone notices.""")
        return self.create_key_item_embed('Master Ball')

    def ssAnne(self):
        self.keyitems.ss_ticket = True
        self.message = dedent("""\
                            Rummaging through someones mailbox you find an evelope. Inside it says "For Tommy. Sincerely, The Make a Wish Foundation""")
        self.keyitems.save()
        return self.create_key_item_embed('S.S. Ticket')

    def thePokemonLeague(self):
        # start battle with Elite 4
        
        return

    def mysteriousCave(self):
        from trainerclass import trainer as trainerClass
        locationId = 147
        trainer = trainerClass(self.discordId)
        trainer.setLocation(locationId)
        self.message = """Your eight badges begin to glow... The ground shifts beneath your feet and suddenly you find yourself standing at the entrance of a mysterious cave. The air is thick with an unknown power."""
        return {'teleport': True}

    def checkTruck(self):
        from trainerclass import trainer as trainerClass
        from pokedexclass import pokedex
        
        # Check if trainer has already received Mew
        uniqueEncounters = uEnc(self.discordId)
        if uniqueEncounters.mew:
            self.statuscode = 420
            self.message = "You already found something here!"
            return
        
        # Create trainer object to check party size
        trainer = trainerClass(self.discordId)
        party_count = trainer.getPartySize()
        
        # Create Mew Pokemon
        pokemon = pokeClass(self.discordId, 'mew')
        pokemon.create(25)
        
        # CRITICAL: Set discordId and party status before saving
        pokemon.discordId = self.discordId
        pokemon.party = party_count < 6  # Add to party if there's space, otherwise to PC
        
        # Save the Pokemon
        pokemon.save()
        
        # Check if save was successful
        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "Error occurred while creating Mew"
            return
        
        # Register to Pokedex
        pokedex(self.discordId, pokemon)
        
        # Update unique encounters to mark Mew as received
        uniqueEncounters.mew = True
        uniqueEncounters.save()
        
        # Track easter egg completion
        from services.leaderboardclass import leaderboard as LeaderboardClass
        lb = LeaderboardClass(self.discordId)
        lb.easter_eggs()
        
        # Store easter egg for achievement announcement
        self.found_easter_egg = ('check_truck', 'Mew')


        self.statuscode = 420
        self.message = dedent("""\
                        You find an abandoned truck. Using your massive penis, you pushed it out of the way. Underneath you discover a pokeball.""")
        return self.create_key_item_embed('Mew')
























