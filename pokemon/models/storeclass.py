# store class

import sys
from dbclass import db as dbconn
from inventoryclass import inventory as inv
from trainerclass import trainer
from loggerclass import logger as log

# Class Logger
logger = log()

class store:
    def __init__(self, discordId):
        self.faulted = False
        self.discordId = discordId
        self.storeList = []
        self.storeMap = {}
        self.__loadStore()

    def __loadStore(self):
        """ loads a trainers store into the class object """
        storeList = []
        try:
            trainerObj = trainer(self.discordId)
            locationId = trainerObj.getLocationId()
            db = dbconn()
            queryString = 'SELECT "item", "price" FROM store WHERE "locationId"=%(locationId)s'
            results = db.queryAll(queryString, { 'locationId':locationId })
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
            self.faulted = True
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            self.storeList = storeList

    def buyItemEx(self, name, quantity):
        """ buy and item and update trainers inventory Ex"""
        if name not in self.storeMap.keys():
            return "Item not available"

        price = self.storeMap[name]['price']
        totalPrice = price * quantity

        inventory = inv(self.discordId)

        if inventory.money < totalPrice:
            return 'You do not have enough money to buy that.'
        else:
            inventory.money = inventory.money - totalPrice
            # todo update this so it's not hard coded
            if name == 'poke-ball':
                inventory.pokeball = inventory.pokeball + quantity
            elif name == 'potion':
                inventory.potion = inventory.potion + quantity
            inventory.save()
            return "You successfully bought that item!"

    def buyItem(self, name, quantity):
        """ buy and item and update trainers inventory """
        if name not in self.storeMap.keys():
            return "Item not available"
        
        inventory = inv(self.discordId)
        price = self.storeMap[name]['price']
        totalPrice = price * quantity
        
        if inventory.money < totalPrice:
            return 'You do not have enough money to buy that.'
        else:
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
            return "You successfully bought that item!"

        

    def __getSpriteUrl(self, itemName):
        """ returns a path to item sprite on disk """
        return "/data/cogs/CogManager/cogs/pokemon/sprites/items/%s.png" %itemName

