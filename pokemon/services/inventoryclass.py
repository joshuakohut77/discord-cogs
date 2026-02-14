
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
        self.iron = None
        self.protein = None
        self.coincase = None
        self.direhit = None
        self.freshwater = None
        self.hpup = None
        self.lemonade = None
        self.elixir = None
        self.maxelixir = None
        self.maxether = None
        self.ether = None
        self.nugget = None
        self.pokedoll = None
        self.ppup = None
        self.sodapop = None
        self.townmap = None
        self.xaccuracy = None
        self.xattack = None
        self.xdefense = None
        self.xspatk = None
        self.xspdef = None
        self.xspeed = None
        self.firestone = None
        self.waterstone = None
        self.thunderstone = None
        self.leafstone = None
        self.moonstone = None
        # Special Items
        self.linkcable = None
        self.gameshark = None
        # TMs (TM01-TM50)
        for i in range(1, 51):
            setattr(self, f'tm{i:02d}', None)
        self.__loadInventory()

    def getTM(self, tm_number):
        """Get quantity of a specific TM by number (1-50) or string like 'TM01'"""
        if isinstance(tm_number, str):
            # Handle "TM01" format
            tm_number = int(tm_number.replace("TM", ""))
        return getattr(self, f'tm{tm_number:02d}', 0) or 0

    def setTM(self, tm_number, value):
        """Set quantity of a specific TM by number (1-50) or string like 'TM01'"""
        if isinstance(tm_number, str):
            tm_number = int(tm_number.replace("TM", ""))
        setattr(self, f'tm{tm_number:02d}', value)

    def getOwnedTMs(self):
        """Returns list of (tm_key, quantity) for TMs with quantity > 0.
        e.g. [('TM01', 2), ('TM05', 1)]"""
        owned = []
        for i in range(1, 51):
            qty = getattr(self, f'tm{i:02d}', 0) or 0
            if qty > 0:
                owned.append((f'TM{i:02d}', qty))
        return owned

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
                                "iron"=%(iron)s, "protein"=%(protein)s,
                                "dire-hit"=%(direhit)s, "fresh-water"=%(freshwater)s,
                                "hp-up"=%(hpup)s, "lemonade"=%(lemonade)s, 
                                "elixir"=%(elixir)s, "max-elixir"=%(maxelixir)s, "max-ether"=%(maxether)s, 
                                "ether"=%(ether)s, "nugget"=%(nugget)s, 
                                "poke-doll"=%(pokedoll)s, "pp-up"=%(ppup)s, "soda-pop"=%(sodapop)s, 
                                "town-map"=%(townmap)s, "x-accuracy"=%(xaccuracy)s, "x-attack"=%(xattack)s, 
                                "x-defense"=%(xdefense)s, "x-sp-atk"=%(xspatk)s, "x-sp-def"=%(xspdef)s, 
                                "x-speed"=%(xspeed)s, "fire-stone"=%(firestone)s, 
                                "water-stone"=%(waterstone)s, "thunder-stone"=%(thunderstone)s, 
                                "leaf-stone"=%(leafstone)s, "moon-stone"=%(moonstone)s,
                                "link-cable"=%(linkcable)s, "game-shark"=%(gameshark)s'''
            # Append TM columns to update string
            tm_updates = ', '.join([f'"TM{i:02d}"=%(tm{i:02d})s' for i in range(1, 51)])
            updateString += ', ' + tm_updates
            updateString += ' WHERE "discord_id"=%(discordId)s'

            values = { 'money': self.money, 'pokeball':self.pokeball,
                            'potion': self.potion, 'greatball': self.greatball, 'ultraball': self.ultraball,
                            'superpotion': self.superpotion, 'hyperpotion': self.hyperpotion, 'revive': self.revive,
                            'fullrestore': self.fullrestore, 'repel': self.repel, 'awakening': self.awakening, 
                            'masterball': self.masterball, 'escaperope': self.escaperope, 'fullheal': self.fullheal, 
                            'iceheal': self.iceheal, 'maxrepel': self.maxrepel, 'burnheal': self.burnheal, 
                            'paralyzeheal': self.paralyzeheal, 'maxpotion': self.maxpotion, 'antidote': self.antidote, 
                            'superrepel': self.superrepel, 'calcium': self.calcium, 'carbos': self.carbos, 
                            'iron': self.iron, 'protein': self.protein, 
                            'coincase': self.coincase, 'direhit': self.direhit,
                            'freshwater': self.freshwater,
                            'hpup': self.hpup, 'lemonade': self.lemonade, 
                            'elixir': self.elixir, 'maxelixir': self.maxelixir, 'maxether': self.maxether, 
                            'ether': self.ether, 'nugget': self.nugget, 
                            'pokedoll': self.pokedoll, 'ppup': self.ppup, 'sodapop': self.sodapop, 
                            'townmap': self.townmap, 'xaccuracy': self.xaccuracy, 
                            'xattack': self.xattack, 'xdefense': self.xdefense, 'xspatk': self.xspatk, 
                            'xspdef': self.xspdef, 'xspeed': self.xspeed, 'firestone': self.firestone, 
                            'waterstone': self.waterstone, 'thunderstone': self.thunderstone, 
                            'leafstone': self.leafstone, 'moonstone': self.moonstone,
                            "linkcable": self.linkcable, "gameshark": self.gameshark,
                            'discordId': self.discordId }
            # Add TM values
            for i in range(1, 51):
                values[f'tm{i:02d}'] = getattr(self, f'tm{i:02d}', 0) or 0
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
            # Build TM column list
            tm_columns = ', '.join([f'"TM{i:02d}"' for i in range(1, 51)])
            queryString = f'''SELECT "money", "poke-ball", "great-ball", "ultra-ball", 
                            "master-ball", "potion", "super-potion", "hyper-potion", "revive", 
                            "full-restore", "repel", "awakening", "escape-rope", "full-heal",
                            "ice-heal", "max-repel", "burn-heal", "paralyze-heal", 
                            "max-potion", "antidote", "super-repel", calcium, carbos, 
                            "coin-case", "dire-hit", "fresh-water", 
                            "hp-up", lemonade, elixir, "max-elixir", 
                            "max-ether", ether, nugget, "poke-doll", 
                            "pp-up", "soda-pop", "town-map", "x-accuracy", "x-defense", 
                            "x-attack", "x-sp-atk", "x-sp-def", "x-speed", 
                            "fire-stone", "water-stone", 
                            "thunder-stone", "leaf-stone", "moon-stone",
                            "iron", "protein", "link-cable", "game-shark",
                            {tm_columns}
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
                self.freshwater = result[25]
                self.hpup = result[26]
                self.lemonade = result[27]
                self.elixir = result[28]
                self.maxelixir = result[29]
                self.maxether = result[30]
                self.ether = result[31]
                self.nugget = result[32]
                self.pokedoll = result[33]
                self.ppup = result[34]
                self.sodapop = result[35]
                self.townmap = result[36]
                self.xaccuracy = result[37]
                self.xdefense = result[38]
                self.xattack = result[39]
                self.xspatk = result[40]
                self.xspdef = result[41]
                self.xspeed = result[42]
                self.firestone = result[43]
                self.waterstone = result[44]
                self.thunderstone = result[45]
                self.leafstone = result[46]
                self.moonstone = result[47]
                self.iron = result[48]
                self.protein = result[49]
                self.linkcable = result[50]
                self.gameshark = result[51]
                # TM01-TM50 start at index 52
                for i in range(1, 51):
                    setattr(self, f'tm{i:02d}', result[51 + i])
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            del db
            return