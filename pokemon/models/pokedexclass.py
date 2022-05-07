# pokedex class
import sys
from datetime import datetime
from dbclass import db as dbconn
from loggerclass import logger as log

logger = log()

class pokedex:
    def __init__(self, discordId, pokemon):
        self.faulted = False
        self.discordId = discordId
        self.pokemon = pokemon
        self.__pokedex()

    def __pokedex(self):
        """ will update the database with information on the pokemon """
        now = str(datetime.now())
        try:
            db = dbconn()
            queryString = '''SELECT 1 FROM pokedex 
                            WHERE "discord_id"=%(discordId)s AND "pokemonId"=%(pokemonId)s'''
            values = { 'discordId':self.discordId, 'pokemonId':self.pokemon.id }
            result = db.querySingle(queryString, values)
            if result:
                updateQuery = '''UPDATE pokedex SET "mostRecent"=%(now)s 
                                WHERE "discord_id"=%(discordId)s AND "pokemonId"=%(pokemonId)s'''
                values = { 'now':now, 'discordId':self.discordId, 'pokemonId':str(self.pokemon.id) }
            else:
                updateQuery = '''INSERT INTO pokedex ("discord_id", "pokemonId", 
                                    "pokemonName", "mostRecent") 
                                    VALUES (%(discordId)s, %(pokemonId)s, %(pokemonName)s, %(now)s)'''
                values = { 'discordId':self.discordId, 'pokemonId':str(self.pokemon.id),
                        'pokemonName':self.pokemon.name, 'now':now }
            db.execute(updateQuery, values)
        except:
            self.faulted = True
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
