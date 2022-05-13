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
        self.superrepel = None
        self.calcium = None
        self.carbos = None
        self.coincase = None
        self.direhit = None
        self.domefossil = None
        self.freshwater = None
        self.helixfossil = None
        self.hpup = None
        self.lemonade = None
        self.elixer = None
        self.maxelixer = None
        self.maxether = None
        self.ether = None
        self.nugget = None
        self.oldamber = None
        self.pokedoll = None
        self.ppup = None
        self.sodapop = None
        self.townmap = None
        self.xaccuracy = None
        self.xattack = None
        self.xdefense = None
        self.xspatk = None
        self.xspeed = None
        self.firestone = None
        self.waterstone = None
        self.thunderstone = None
        self.leafstone = None
        self.moonstone = None
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
                                "max-potion"=%(maxpotion)s, "antidote"=%(antidote)s, "super-repel"=%(superrepel)s,
                                "calcium"=%(calcium)s, "carbos"=%(carbos)s, "coin-case"=%(coincase)s,
                                "dire-hit"=%(direhit)s, "dome-fossil"=%(domefossil)s, "fresh-water"=%(freshwater)s,
                                "helix-fossil"=%(helixfossil)s, "hp-up"=%(hpup)s, "lemonade"=%(lemonade)s, 
                                "elixer"=%(elixer)s, "max-elixer"=%(maxelixer)s, "max-ether"=%(maxether)s, 
                                "ether"=%(ether)s, "nugget"=%(nugget)s, "old-amber"=%(oldamber)s, 
                                "poke-doll"=%(pokedoll)s, "pp-up"=%(ppup)s, "soda-pop"=%(sodapop)s, 
                                "town-map"=%(townmap)s, "x-accuracy"=%(xaccuracy)s, "x-attack"=%(xattack)s, 
                                "x-defense"=%(xdefense)s, "x-sp-atk"=%(xspatk)s, 
                                "x-speed"=%(xspeed)s, "fire-stone"=%(firestone)s, 
                                "water-stone"=%(waterstone)s, "thunder-stone"=%(thunderstone)s, 
                                "leaf-stone"=%(leafstone)s, "moon-stone"=%(moonstone)s
                                WHERE "discord_id"=%(discordId)s'''
            values = { 'money': self.money, 'pokeball':self.pokeball,
                            'potion': self.potion, 'greatball': self.greatball, 'ultraball': self.ultraball,
                            'superpotion': self.superpotion, 'hyperpotion': self.hyperpotion, 'revive': self.revive,
                            'fullrestore': self.fullrestore, 'repel': self.repel, 'awakening': self.awakening, 
                            'masterball': self.masterball, 'escaperope': self.escaperope, 'fullheal': self.fullheal, 
                            'iceheal': self.iceheal, 'maxrepel': self.maxrepel, 'burnheal': self.burnheal, 
                            'paralyzeheal': self.paralyzeheal, 'maxpotion': self.maxpotion, 'antidote': self.antidote, 
                            'superrepel': self.superrepel, 'calcium': self.calcium, 'carbos': self.carbos, 
                            'coincase': self.coincase, 'direhit': self.direhit, 'domefossil': self.domefossil, 
                            'freshwater': self.freshwater, 'helixfossil': self.helixfossil,
                            'hpup': self.hpup, 'lemonade': self.lemonade, 
                            'elixer': self.elixer, 'maxelixer': self.maxelixer, 'maxether': self.maxether, 
                            'ether': self.ether, 'nugget': self.nugget, 'oldamber': self.oldamber, 
                            'pokedoll': self.pokedoll, 'ppup': self.ppup, 'sodapop': self.sodapop, 
                            'townmap': self.townmap, 'xaccuracy': self.xaccuracy, 
                            'xattack': self.xattack, 'xdefense': self.xdefense, 
                            'xspatk': self.xspatk, 'xspeed': self.xspeed, 'firestone': self.firestone, 
                            'waterstone': self.waterstone, 'thunderstone': self.thunderstone, 
                            'leafstone': self.leafstone, 'moonstone': self.moonstone, 'discordId': self.discordId }
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
                            "max-potion", "antidote", "super-repel", calcium, carbos, 
                            "coin-case", "dire-hit", "dome-fossil", "fresh-water", 
                            "helix-fossil", "hp-up", lemonade, elixer, "max-elixir", 
                            "max-ether", ether, nugget, "old-amber", "poke-doll", 
                            "pp-up", "soda-pop", "town-map", "x-accuracy", "x-defense", 
                            "x-attack", "x-sp-atk", "x-speed", "fire-stone", "water-stone", 
                            "thunder-stone", "leaf-stone", "moon-stone" 
                            FROM inventory WHERE "discord_id"=%(discordId)s'''
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
                self.superrepel = result[20]
                self.calcium = result[21]
                self.carbos = result[22]
                self.coincase = result[23]
                self.direhit = result[24]
                self.domefossil = result[25]
                self.freshwater = result[26]
                self.helixfossil = result[27]
                self.hpup = result[28]
                self.lemonade = result[29]
                self.elixer = result[30]
                self.maxelixer = result[31]
                self.maxether = result[32]
                self.ether = result[33]
                self.nugget = result[34]
                self.oldamber = result[35]
                self.pokedoll = result[36]
                self.ppup = result[37]
                self.sodapop = result[38]
                self.townmap = result[39]
                self.xaccuracy = result[40]
                self.xaccuracy = result[41]
                self.xdefense = result[42]
                self.xspatk = result[43]
                self.xspeed = result[44]
                self.firestone = result[45]
                self.waterstone = result[46]
                self.thunderstone = result[47]
                self.leafstone = result[48]
                self.moonstone = result[49]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return
