# inventory class

from dbclass import db as dbconn
from pokeclass import Pokemon as pokeClass


class inventory:
    def __init__(self, discordId):
        self.discordId = discordId
        self.money = None
        self.pokeball = None
        self.potion = None
        self.__loadInventory()

    def save(self):
        """ updates a trainers inventory """
        db = dbconn()
        updateString = 'UPDATE inventory set "money"=%s, "pokeball"=%s, "potion"=%s WHERE "discord_id"=%s'
        db.execute(updateString, (self.money, self.pokeball,
                   self.potion, self.discordId))

        # delete and close connection
        del db
        return

    def __loadInventory(self):
        """ loads a trainers inventory into the class object """
        db = dbconn()
        queryString = 'SELECT "money", "pokeball", "potion" FROM inventory WHERE "discord_id"=%s'
        results = db.queryAll(queryString, (self.discordId,))
        if len(results) > 0:
            self.money = results[0][0]
            self.pokeball = results[0][1]
            self.potion = results[0][2]

        # delete and close connection
        del db
        return
