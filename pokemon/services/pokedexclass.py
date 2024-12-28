# pokedex class
import os
import json
import sys
from datetime import datetime
from services.dbclass import db as dbconn
from services.loggerclass import logger as log
from services.pokeclass import Pokemon as PokemonClass
from models.pokedex import PokedexModel

# Class Logger
logger = log()


class pokedex:
    def __init__(self, discordId: str, pokemon: PokemonClass):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId
        self.pokemon = pokemon
        if pokemon is not None:
            self.__pokedex()

    def __pokedex(self):
        """ will update the database with information on the pokemon """
        now = str(datetime.now())
        try:
            db = dbconn()
            queryString = '''SELECT 1 FROM pokedex 
                            WHERE "discord_id"=%(discordId)s AND "pokemonId"=%(pokemonId)s'''
            values = {'discordId': self.discordId,
                      'pokemonId': self.pokemon.pokedexId}
            result = db.querySingle(queryString, values)
            if result:
                updateQuery = '''UPDATE pokedex SET "mostRecent"=%(now)s 
                                WHERE "discord_id"=%(discordId)s AND "pokemonId"=%(pokemonId)s'''
                values = {'now': now, 'discordId': self.discordId,
                          'pokemonId': self.pokemon.pokedexId}
            else:
                updateQuery = '''INSERT INTO pokedex ("discord_id", "pokemonId", 
                                    "pokemonName", "mostRecent") 
                                    VALUES (%(discordId)s, %(pokemonId)s, %(pokemonName)s, %(now)s)'''
                values = {'discordId': self.discordId, 'pokemonId': str(self.pokemon.pokedexId),
                          'pokemonName': self.pokemon.pokemonName, 'now': now}
            db.execute(updateQuery, values)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db

    def getPokedex(self):
        """ returns the pokedex of a trainer in a model format """
        try:
            db = dbconn()
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/pokemon.json')
            pokemonConfig = json.load(open(p, 'r'))
            queryString = '''SELECT "pokemonId", "pokemonName", "mostRecent" FROM pokedex 
                            WHERE "discord_id"=%(discordId)s'''
            values = { 'discordId': self.discordId }
            result = db.queryAll(queryString, values)

            pokedexList = []
            pokemonJson = {}
            for row in result:
                pokemonJson['pokemonId'] = row[0]
                pokemonJson['pokemonName'] = row[1]
                pokemonJson['mostRecent'] = row[2]
                pokemonJson['height'] = pokemonConfig[row[1]]['height']
                pokemonJson['weight'] = pokemonConfig[row[1]]['weight']
                pokemonJson['description'] = pokemonConfig[row[1]]['description']

                pokedexList.append(PokedexModel(pokemonJson))
            
            return pokedexList

        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db

    @staticmethod
    def getPokedexEntry(pokemon: PokemonClass):
        """ returns the pokedex of a trainer in a model format """
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/pokemon.json')
        pokemonConfig = json.load(open(p, 'r'))

        pokemonJson = {}
        
        pokemonJson['pokemonId'] = pokemon.pokedexId
        pokemonJson['pokemonName'] = pokemon.pokemonName
        pokemonJson['mostRecent'] = None
        pokemonJson['height'] = pokemonConfig[pokemon.pokemonName]['height']
        pokemonJson['weight'] = pokemonConfig[pokemon.pokemonName]['weight']
        pokemonJson['description'] = pokemonConfig[pokemon.pokemonName]['description']

        entry = PokedexModel(pokemonJson)
        return entry