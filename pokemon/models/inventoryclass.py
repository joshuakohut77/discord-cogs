# inventory class

from dbclass import db as dbconn


class inventory:
    def __init__(self, discordId):
        self.discordId = discordId
        self.money = None
        self.pokeball = None
        self.greatball = None
        self.ultraball = None
        self.masterball = None
        self.potion = None
        self.superpotion = None
        self.hyperpotion = None
        self.revive = None
        self.fullrestore = None
        self.repel = None
        self.awakening = None
        self.escaperope = None
        self.fullheal = None
        self.iceheal = None
        self.maxrepel = None
        self.burnheal = None
        self.paralyzeheal = None
        self.maxpotion = None
        self.antidote = None
        self.__loadInventory()

    def save(self):
        """ updates a trainers inventory """
        db = dbconn()
        updateString = '''UPDATE inventory set "money"=%s, "poke-ball"=%s, "potion"=%s,
                            "great-ball"=%s, "ultra-ball"=%s, "super-potion"=%s, "hyper-potion"=%s,
                            "revive"=%s, "full-restore"=%s, "repel"=%s, "awakening"=%s, "master-ball"=%s
                            "escape-rope"=%s, "full-heal"=%s, "ice-heal"=%s, "max-repel"=%s,
                            "burn-heal"=%s, "paralyze-heal"=%s, "max-potion"=%s, "antidote"=%s
                            WHERE "discord_id"=%s'''
        db.execute(updateString, (self.money, self.pokeball,
                   self.potion, self.greatball, self.ultraball,
                   self.superpotion, self.hyperpotion, self.revive,
                   self.fullrestore, self.repel, self.awakening, 
                   self.masterball, self.escaperope, self.fullheal, 
                   self.iceheal, self.maxrepel, self.burnheal, 
                   self.paralyzeheal, self.maxpotion, self.antidote, 
                   self.discordId))

        # delete and close connection
        del db
        return

    def __loadInventory(self):
        """ loads a trainers inventory into the class object """
        db = dbconn()
        queryString = '''SELECT "money", "poke-ball", "great-ball", "ultra-ball", 
                        "master-ball", "potion", "super-potion", "hyper-potion", "revive", 
                        "full-restore", "repel", "awakening", "escape-rope", "full-heal",
                        "ice-heal", "max-repel", "burn-heal", "paralyze-heal", 
                        "max-potion", "antidote" FROM inventory WHERE "discord_id"=%s'''
        result = db.querySingle(queryString, (self.discordId,))
        if len(result) > 0:
            self.money = result[0]
            self.pokeball = result[1]
            self.greatball = result[2]
            self.ultraball = result[3]
            self.masterball = result[4]
            self.potion = result[5]
            self.superpotion = result[6]
            self.hyperpotion = result[7]
            self.revive = result[8]
            self.fullrestore = result[9]
            self.repel = result[10]
            self.awakening = result[11]
            self.escaperope = result[12]
            self.fullheal = result[13]
            self.iceheal = result[14]
            self.maxrepel = result[15]
            self.burnheal = result[16]
            self.paralyzeheal = result[17]
            self.maxpotion = result[18]
            self.antidote = result[19]

        # delete and close connection
        del db
        return
