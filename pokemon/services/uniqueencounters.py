# unique-encounters class
import sys
from dbclass import db as dbconn
from loggerclass import logger as log

# Class Logger
logger = log()

class uniqueEncounters:
    def __init__(self, discordId):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId
        # below are all Booleans
        self.articuno = False
        self.zapdos = False
        self.moltres = False
        self.mewtwo = False
        self.magikarp = False
        self.charmander = False
        self.squirtle = False
        self.bulbasaur = False
        self.lapras = False
        self.hitmonchan = False
        self.hitmonlee = False
        self.eevee = False
        self.snorlax = False
        
        # populate object
        self.__load()

    def __load(self):
        """ loads unique encounters from database into object """
        try:
            db = dbconn()
            queryString = '''
                SELECT discord_id, articuno, zapdos, moltres, mewtwo, 
                magikarp, charmander, squirtle, bulbasaur, 
                lapras, hitmonchan, hitmonlee, eevee, snorlax
	            FROM "unique-encounters" WHERE discord_id=%(discordId)s
            '''
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                self.articuno = result[1]
                self.zapdos = result[2]
                self.moltres = result[3]
                self.mewtwo = result[4]
                self.magikarp = result[5]
                self.charmander = result[6]
                self.squirtle = result[7]
                self.bulbasaur = result[8]
                self.lapras = result[9]
                self.hitmonchan = result[10]
                self.hitmonlee = result[11]
                self.eevee = result[12]
                self.snorlax = result[13]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
    
    def save(self):
        """ saves a users key items """
        try:
            db = dbconn()
            if self.discordId is not None:
                updateString = '''
                UPDATE "unique-encounters"
	                SET "articuno"=%(articuno)s, "zapdos"=%(zapdos)s, "moltres"=%(moltres)s,
                    "mewtwo"=%(mewtwo)s, "magikarp"=%(magikarp)s, 
                    "charmander"=%(charmander)s, "squirtle"=%(squirtle)s, "bulbasaur"=%(bulbasaur)s, 
                    lapras=%(lapras)s, hitmonchan=%(hitmonchan)s, hitmonlee=%(hitmonlee)s, 
                    eevee=%(eevee)s, snorlax=%(snorlax)s
	                    WHERE discord_id=%(discordId)s;
                '''
                values = { 'articuno':self.articuno, 'zapdos': self.zapdos, 'moltres':self.moltres,
                            'mewtwo':self.mewtwo, 'magikarp':self.magikarp,
                            'charmander':self.charmander, 'squirtle':self.squirtle,
                            'bulbasaur':self.bulbasaur, 'lapras':self.lapras,
                            'hitmonchan':self.hitmonchan, 'hitmonlee':self.hitmonlee,
                            'eevee':self.eevee, 'snorlax':self.snorlax,
                            'discordId':self.discordId }
                db.execute(updateString, values)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
        