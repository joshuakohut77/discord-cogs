# store class

from dbclass import db as dbconn
from inventoryclass import inventory as inv
from trainerclass import trainer


class store:
    def __init__(self, discordId):
        self.discordId = discordId
        self.storeList = []
        self.storeMap = {}
        self.__loadStore()

    def __loadStore(self):
        """ loads a trainers store into the class object """
        storeList = []
        db = dbconn()
        trainerObj = trainer(self.discordId)
        locationId = trainerObj.getLocationId()
        queryString = 'SELECT "item", "price" FROM store WHERE "locationId"=%s'
        results = db.queryAll(queryString, (locationId,))
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

    def buyItem(self, itemId, quantity):
        """ buy and item and update trainers inventory """
        inventory = inv(self.discordId)

        for item in self.storeList:
            if item['item'] == itemId:
                if inventory.money < (item['price'] * quantity):
                    return 'You do not have enough money to buy that.'
                else:
                    inventory.money = inventory.money - \
                        (item['price'] * quantity)
                    # todo update this so it's not hard coded
                    if itemId == 4:
                        inventory.pokeball = inventory.pokeball + quantity
                    elif itemId == 17:
                        inventory.potion = inventory.potion + quantity
                    inventory.save()
                    return "You successfully bought that item!"

        return "Invalid itemId %s. Please report this error." % (itemId)

    def __getSpriteUrl(self, itemName):
        """ returns a constructed spriteUrl """
        baseUrl = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/"
        spriteUrl = baseUrl + itemName + ".png"
        return spriteUrl
