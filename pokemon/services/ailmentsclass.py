# ailments class
import sys
from dbclass import db as dbconn
from loggerclass import logger as log
from datetime import datetime

# Class Logger
logger = log()

class ailment:
    def __init__(self, pokemonId):
        self.statuscode = 69
        self.message = ''

        self.pokemonId = pokemonId
        self.sleep = False
        self.poison = False
        self.burn = False
        self.freeze = False
        self.paralyze = False
        self.mostRecent = datetime.now()
        self.recordExists = False
    

    def load(self):
        """ returns populated ailment object"""
        try:
            db = dbconn()
            queryString = '''SELECT "mostRecent", sleep, 
                            poison, burn, "freeze", paralyze
	                        FROM ailments WHERE "pokemonId"=%(pokemonId)s'''
            result = db.querySingle(queryString, { 'pokemonId': self.pokemonId })
            if len(result) > 0:
                self.mostRecent = result[0]
                self.sleep = result[1]
                self.poison = result[2]
                self.burn = result[3]
                self.freeze = result[4]
                self.paralyze = result[5]
                self.recordExists = True
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return
        
    def save(self):
        """ saves an ailment object to the database"""
        try:
            # check if a recordExists meaning it has a database entry already
            db = dbconn()
            query = None
            if self.recordExists:
                # updateQuery or deleteQuery depending on the object status
                if not self.sleep and not self.poison and not self.burn and not self.freeze and not self.paralyze:
                    # delete row from database
                    query = 'DELETE FROM ailments WHERE "pokemonId"=%(pokemonId)s'
                    values =  { "pokemonId": self.pokemonId }
                else:
                    # update row in database
                    query = '''UPDATE ailments SET "mostRecent"=%(mostRecent)s, 
                                sleep=%(sleep)s, poison=%(poison)s, 
                                burn=%(burn)s, "freeze"=%(freeze)s, paralyze=%(paralyze)s 
                                WHERE "pokemonId"=%(pokemonId)s'''
                    values = { "mostRecent":self.mostRecent, "sleep":self.sleep, "poison":self.poison, 
                                "burn":self.burn, "freeze":self.freeze, "paralyze":self.paralyze, 
                                "pokemonId":self.pokemonId}
            else:
                query = '''INSERT INTO ailments ("mostRecent", sleep, poison, burn, "freeze", paralyze)
                            VALUES(%(mostRecent)s, %(sleep)s, %(poison)s, %(burn)s, %(freeze)s, %(paralyze)s)
                            WHERE "pokemonId"=%(pokemonId)s'''
                values = { "mostRecent":self.mostRecent, "sleep":self.sleep, "poison":self.poison, 
                            "burn":self.burn, "freeze":self.freeze, "paralyze":self.paralyze, 
                            "pokemonId":self.pokemonId}
            db.execute(query, values)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db





