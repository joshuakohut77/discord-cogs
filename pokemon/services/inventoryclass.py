# inventory class
import sys
from dbclass import db as dbconn
from loggerclass import logger as log

# Class Logger
logger = log()

class inventory:
    def __init__(self, discordId):
        self.statuscode = 69
        self.message = ''

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
        try:
            db = dbconn()
            updateString = '''UPDATE inventory set "money"=%(money)s, "poke-ball"=%(pokeball)s, "potion"=%(potion)s,
                                "great-ball"=%(greatball)s, "ultra-ball"=%(ultraball)s, "super-potion"=%(superpotion)s, 
                                "hyper-potion"=%(hyperpotion)s, "revive"=%(revive)s, "full-restore"=%(fullrestore)s, 
                                "repel"=%(repel)s, "awakening"=%(awakening)s, "master-ball"=%(masterball)s,
                                "escape-rope"=%(escaperope)s, "full-heal"=%(fullheal)s, "ice-heal"=%(iceheal)s, 
                                "max-repel"=%(maxrepel)s, "burn-heal"=%(burnheal)s, "paralyze-heal"=%(paralyzeheal)s, 
                                "max-potion"=%(maxpotion)s, "antidote"=%(antidote)s
                                WHERE "discord_id"=%(discordId)s'''
            values = { 'money': self.money, 'pokeball':self.pokeball,
                            'potion': self.potion, 'greatball': self.greatball, 'ultraball': self.ultraball,
                            'superpotion': self.superpotion, 'hyperpotion': self.hyperpotion, 'revive': self.revive,
                            'fullrestore': self.fullrestore, 'repel': self.repel, 'awakening': self.awakening, 
                            'masterball': self.masterball, 'escaperope': self.escaperope, 'fullheal': self.fullheal, 
                            'iceheal': self.iceheal, 'maxrepel': self.maxrepel, 'burnheal': self.burnheal, 
                            'paralyzeheal': self.paralyzeheal, 'maxpotion': self.maxpotion, 'antidote': self.antidote, 
                            'discordId': self.discordId }
            db.execute(updateString, values)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return

    def __loadInventory(self):
        """ loads a trainers inventory into the class object """
        try:
            db = dbconn()
            queryString = '''SELECT "money", "poke-ball", "great-ball", "ultra-ball", 
                            "master-ball", "potion", "super-potion", "hyper-potion", "revive", 
                            "full-restore", "repel", "awakening", "escape-rope", "full-heal",
                            "ice-heal", "max-repel", "burn-heal", "paralyze-heal", 
                            "max-potion", "antidote" FROM inventory WHERE "discord_id"=%(discordId)s'''
            result = db.querySingle(queryString, { 'discordId': self.discordId })
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
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return
