# store class
import os
import sys
import json
from dbclass import db as dbconn
from inventoryclass import inventory as inv
from keyitemsclass import keyitems as kitems
from loggerclass import logger as log
from typing import List

# Class Logger
logger = log()


class StoreItem:
    name: str
    price: int
    spriteUrl: str

    def __init__(self, name: str, price: int, spriteUrl: str) -> None:
        self.name = name
        self.price = price
        self.spriteUrl = spriteUrl


class store:
    # Public
    storeList: List[List[StoreItem]]

    def __init__(self, discordId: str, locationId: int):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId
        self.locationId = locationId
        self.storeList = []
        self.storeMap = {}
        self.__loadStore()

    def __loadStore(self):
        """ loads a trainers store into the class object """
        self.storeList = []
        try:
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/store.json')
            storeConfig = json.load(open(p, 'r'))
            
            # If there are not items, then there is no PokeMart
            # at this location.
            # Relay that message back to the user
            if str(self.locationId) not in storeConfig:
                self.message = 'There is not a PokeMart at your location.'
                self.statuscode = 420
                return
            
            # this section is to check if user has Oaks Parcel
            if self.locationId == 154:
                keyitems = kitems(self.discordId)
                if not keyitems.oaks_parcel_delivered:
                    if not keyitems.oaks_parcel:
                        self.statuscode = 420
                        self.message = '''Hey there, can you deliver this to Professor Oak for me? You received Oaks Parcel!'''
                        keyitems.oaks_parcel = True
                        keyitems.save()
                        return 
                    elif not keyitems.oaks_parcel_delivered:
                        self.statuscode = 420
                        self.message = 'Hey there, take that parcel to Professor Oak please.'
                        return

            # TODO: general pokemart pagination, [[], []]
            # TODO: update db tables
            results = storeConfig[str(self.locationId)]

            self.storeMap = {}
            for pages in results:
                page = []

                for row in pages:
                    name = row['item']
                    price = row['price']
                    url = self.__getSpriteUrl(name)

                    item = StoreItem(name, price, url)
                    page.append(item)

                    if item.name not in self.storeMap.keys():
                        self.storeMap[item.name] = {}

                    if item.name in self.storeMap.keys():
                        self.storeMap[item.name]['price'] = item.price

                self.storeList.append(page)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        

    def buyItem(self, name, quantity):
        """ buy and item and update trainers inventory """
        if name not in self.storeMap.keys():
            self.statuscode = 420
            self.message = "Item not available at current Poke Mart."
            return

        inventory = inv(self.discordId)
        price = self.storeMap[name]['price']
        totalPrice = price * quantity

        if inventory.money < totalPrice:
            self.statuscode = 420
            self.message = 'You do not have enough money to buy that.'
        else:
            inventory.money = inventory.money - totalPrice
            if name == 'poke-ball':
                inventory.pokeball += quantity
            elif name == 'great-ball':
                inventory.greatball += quantity
            elif name == 'ultra-ball':
                inventory.ultraball += quantity
            elif name == 'master-ball':
                inventory.masterball += quantity
            elif name == 'potion':
                inventory.potion += quantity
            elif name == 'super-potion':
                inventory.superpotion += quantity
            elif name == 'hyper-potion':
                inventory.hyperpotion += quantity
            elif name == 'revive':
                inventory.revive += quantity
            elif name == 'full-restore':
                inventory.fullrestore += quantity
            elif name == 'repel':
                inventory.repel += quantity
            elif name == 'awakening':
                inventory.awakening += quantity
            elif name == 'escape-rope':
                inventory.escaperope += quantity
            elif name == 'full-heal':
                inventory.fullheal += quantity
            elif name == 'ice-heal':
                inventory.iceheal += quantity
            elif name == 'max-repel':
                inventory.maxrepel += quantity
            elif name == 'burn-heal':
                inventory.burnheal += quantity
            elif name == 'paralyze-heal':
                inventory.paralyzeheal += quantity
            elif name == 'antidote':
                inventory.antidote += quantity
            elif name == 'max-potion':
                inventory.maxpotion += quantity
            elif name == 'super-repel':
                inventory.superrepel += quantity
            # Evolution Stones
            elif name == 'fire-stone':
                inventory.firestone += quantity
            elif name == 'water-stone':
                inventory.waterstone += quantity
            elif name == 'thunder-stone':
                inventory.thunderstone += quantity
            elif name == 'leaf-stone':
                inventory.leafstone += quantity
            elif name == 'moon-stone':
                inventory.moonstone += quantity
            # Vitamins and Battle Items
            elif name == 'calcium':
                inventory.calcium += quantity
            elif name == 'carbos':
                inventory.carbos += quantity
            elif name == 'iron':
                inventory.iron += quantity
            elif name == 'protein':
                inventory.protein += quantity
            elif name == 'hp-up':
                inventory.hpup += quantity
            elif name == 'x-accuracy':
                inventory.xaccuracy += quantity
            elif name == 'x-attack':
                inventory.xattack += quantity
            elif name == 'x-defense':
                inventory.xdefense += quantity
            elif name == 'x-sp-atk':
                inventory.xspatk += quantity
            elif name == 'x-sp-def':
                inventory.xspdef += quantity
            elif name == 'x-speed':
                inventory.xspeed += quantity
            elif name == 'dire-hit':
                inventory.direhit += quantity
            # Drinks and Misc Items
            elif name == 'fresh-water':
                inventory.freshwater += quantity
            elif name == 'lemonade':
                inventory.lemonade += quantity
            elif name == 'soda-pop':
                inventory.sodapop += quantity
            elif name == 'poke-doll':
                inventory.pokedoll += quantity
            elif name == 'nugget':
                inventory.nugget += quantity
            elif name == 'pp-up':
                inventory.ppup += quantity
            elif name == 'elixir':
                inventory.elixir += quantity
            elif name == 'max-elixir':
                inventory.maxelixir += quantity
            elif name == 'ether':
                inventory.ether += quantity
            elif name == 'max-ether':
                inventory.maxether += quantity
            elif name == 'old-amber':
                inventory.oldamber += quantity
            # Special Items
            elif name == 'link-cable':
                inventory.linkcable += quantity
            elif name == 'game-shark':
                inventory.gameshark += quantity
            
            inventory.save()
            
            if inventory.statuscode == 96:
                self.statuscode = 96
                self.message = "Error occured during inventory save()"
                return
            self.statuscode = 420
            self.message = f"You successfully bought {quantity} {name}"

    def sellItem(self, name, quantity):
        """ buy and item and update trainers inventory """

        inventory = inv(self.discordId)
        
        # price = self.storeMap[name]['price']
        price = self.__getItemPrice(name)

        # Status code can be set to 420 or 96 if the item
        # does not exist or an error occurs
        if self.statuscode == 420 or self.statuscode == 96:
            return

        if price == 0:
            self.statuscode = 420
            self.message = 'That item can\'t be sold.'
            return

        # all selling is half the buying price
        price = int(price / 2)
        totalPrice = price * quantity

        validQuantity = True
        inventory.money = inventory.money + totalPrice
        if name == 'poke-ball':
            inventory.pokeball -= quantity
            if inventory.pokeball < 0:
                validQuantity = False
        elif name == 'great-ball':
            inventory.greatball -= quantity
            if inventory.greatball < 0:
                validQuantity = False
        elif name == 'ultra-ball':
            inventory.ultraball -= quantity
            if inventory.ultraball < 0:
                validQuantity = False
        elif name == 'master-ball':
            inventory.masterball -= quantity
            if inventory.masterball < 0:
                validQuantity = False
        elif name == 'potion':
            inventory.potion -= quantity
            if inventory.potion < 0:
                validQuantity = False
        elif name == 'super-potion':
            inventory.superpotion -= quantity
            if inventory.superpotion < 0:
                validQuantity = False
        elif name == 'hyper-potion':
            inventory.hyperpotion -= quantity
            if inventory.hyperpotion < 0:
                validQuantity = False
        elif name == 'revive':
            inventory.revive -= quantity
            if inventory.revive < 0:
                validQuantity = False
        elif name == 'full-restore':
            inventory.fullrestore -= quantity
            if inventory.fullrestore < 0:
                validQuantity = False
        elif name == 'repel':
            inventory.repel -= quantity
            if inventory.repel < 0:
                validQuantity = False
        elif name == 'awakening':
            inventory.awakening -= quantity
            if inventory.awakening < 0:
                validQuantity = False
        elif name == 'escape-rope':
            inventory.escaperope -= quantity
            if inventory.escaperope < 0:
                validQuantity = False
        elif name == 'full-heal':
            inventory.fullheal -= quantity
            if inventory.fullheal < 0:
                validQuantity = False
        elif name == 'ice-heal':
            inventory.iceheal -= quantity
            if inventory.iceheal < 0:
                validQuantity = False
        elif name == 'max-repel':
            inventory.maxrepel -= quantity
            if inventory.maxrepel < 0:
                validQuantity = False
        elif name == 'burn-heal':
            inventory.burnheal -= quantity
            if inventory.burnheal < 0:
                validQuantity = False
        elif name == 'paralyze-heal':
            inventory.paralyzeheal -= quantity
            if inventory.paralyzeheal < 0:
                validQuantity = False
        elif name == 'antidote':
            inventory.antidote -= quantity
            if inventory.antidote < 0:
                validQuantity = False
        elif name == 'max-potion':
            inventory.maxpotion -= quantity
            if inventory.maxpotion < 0:
                validQuantity = False
        elif name == 'super-repel':
            inventory.superrepel -= quantity
            if inventory.superrepel < 0:
                validQuantity = False
        elif name == 'calcium':
            inventory.calcium -= quantity
            if inventory.calcium < 0:
                validQuantity = False
        elif name == 'carbos':
            inventory.carbos -= quantity
            if inventory.carbos < 0:
                validQuantity = False
        elif name == 'coin-case':
            inventory.coincase -= quantity
            if inventory.coincase < 0:
                validQuantity = False
        elif name == 'dire-hit':
            inventory.direhit -= quantity
            if inventory.direhit < 0:
                validQuantity = False
        elif name == 'fresh-water':
            inventory.freshwater -= quantity
            if inventory.freshwater < 0:
                validQuantity = False
        elif name == 'hp-up':
            inventory.hpup -= quantity
            if inventory.hpup < 0:
                validQuantity = False
        elif name == 'lemonade':
            inventory.lemonade -= quantity
            if inventory.lemonade < 0:
                validQuantity = False
        elif name == 'elixir':
            inventory.elixir -= quantity
            if inventory.elixir < 0:
                validQuantity = False
        elif name == 'max-elixir':
            inventory.maxelixir -= quantity
            if inventory.maxelixir < 0:
                validQuantity = False
        elif name == 'max-ether':
            inventory.maxether -= quantity
            if inventory.maxether < 0:
                validQuantity = False
        elif name == 'ether':
            inventory.ether -= quantity
            if inventory.ether < 0:
                validQuantity = False
        elif name == 'nugget':
            inventory.nugget -= quantity
            if inventory.nugget < 0:
                validQuantity = False
        elif name == 'old-amber':
            inventory.oldamber -= quantity
            if inventory.oldamber < 0:
                validQuantity = False
        elif name == 'poke-doll':
            inventory.pokedoll -= quantity
            if inventory.pokedoll < 0:
                validQuantity = False
        elif name == 'pp-up':
            inventory.ppup -= quantity
            if inventory.ppup < 0:
                validQuantity = False
        elif name == 'soda-pop':
            inventory.sodapop -= quantity
            if inventory.sodapop < 0:
                validQuantity = False
        elif name == 'x-accuracy':
            inventory.xaccuracy -= quantity
            if inventory.xaccuracy < 0:
                validQuantity = False
        elif name == 'x-attack':
            inventory.xattack -= quantity
            if inventory.xattack < 0:
                validQuantity = False
        elif name == 'x-defense':
            inventory.xdefense -= quantity
            if inventory.xdefense < 0:
                validQuantity = False
        elif name == 'x-sp-atk':
            inventory.xspatk -= quantity
            if inventory.xspatk < 0:
                validQuantity = False
        elif name == 'x-sp-def':
            inventory.xspdef -= quantity
            if inventory.xspdef < 0:
                validQuantity = False
        elif name == 'x-speed':
            inventory.xspeed -= quantity
            if inventory.xspeed < 0:
                validQuantity = False
        elif name == 'fire-stone':
            inventory.firestone -= quantity
            if inventory.firestone < 0:
                validQuantity = False
        elif name == 'water-stone':
            inventory.waterstone -= quantity
            if inventory.waterstone < 0:
                validQuantity = False
        elif name == 'thunder-stone':
            inventory.thunderstone -= quantity
            if inventory.thunderstone < 0:
                validQuantity = False
        elif name == 'leaf-stone':
            inventory.leafstone -= quantity
            if inventory.leafstone < 0:
                validQuantity = False
        elif name == 'moon-stone':
            inventory.moonstone -= quantity
            if inventory.moonstone < 0:
                validQuantity = False

        if not validQuantity:
            self.statuscode = 420
            self.message = "You do not have enough of that item to sell"
            return
        inventory.save()
        
        if inventory.statuscode == 96:
            self.statuscode = 96
            self.message = "Error occured during inventory save()"
            return
        self.statuscode = 420
        self.message = f"You successfully sold {quantity} {name}"
    
    def __getItemPrice(self, itemName):
        """ returns the price of the item """
        price = 0
        try:
            # TODO replace this load with object in memory
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/itempricing.json')
            pricingConfig = json.load(open(p, 'r'))
            price = pricingConfig[itemName]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return price

    def __getSpriteUrl(self, itemName):
        """ returns a path to item sprite on disk """
        return "/data/cogs/CogManager/cogs/pokemon/sprites/items/%s.png" % itemName
