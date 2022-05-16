# store class

import sys
from dbclass import db as dbconn
from inventoryclass import inventory as inv
from keyitemsclass import keyitems as kitems
from loggerclass import logger as log

# Class Logger
logger = log()


class store:
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
        storeList = []
        try:
            # this section is to check if user has Oaks Parcel
            if self.locationId == 154:
                keyitems = keyitems(self.discordId)
                if not keyitems.oaks_parcel:
                    self.statuscode = 420
                    self.message = 'here takes the oaks_parcel'
                    return 
            db = dbconn()
            queryString = 'SELECT "item", "price" FROM store WHERE "locationId"=%(locationId)s'
            results = db.queryAll(queryString, {'locationId': self.locationId})

            # If there are not items, then there is no PokeMart
            # at this location.
            # Relay that message back to the user
            if len(results) == 0:
                self.message = 'There is not a PokeMart at your location.'
                self.statuscode = 420
                return

            for row in results:
                item = row[0]
                price = row[1]
                storeOption = {'item': item, 'price': price,
                               'spriteUrl': self.__getSpriteUrl(item)}
                storeList.append(storeOption)

            self.storeMap = {}
            for item in storeList:
                if item['item'] not in self.storeMap.keys():
                    self.storeMap[item['item']] = {}

                if item['item'] in self.storeMap.keys():
                    self.storeMap[item['item']]['price'] = item['price']
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            self.storeList = storeList

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
                inventory.greatball += quantity
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
            
            inventory.save()
            
            if inventory.statuscode == 96:
                self.statuscode = 96
                self.message = "Error occured during inventory save()"
                return
            self.statuscode = 420
            self.message = f"You successfully bought {quantity} {name}"

    def __getSpriteUrl(self, itemName):
        """ returns a path to item sprite on disk """
        return "/data/cogs/CogManager/cogs/pokemon/sprites/items/%s.png" % itemName
