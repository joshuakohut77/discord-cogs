# pokedex class

from dbclass import db as dbconn
from datetime import datetime


class pokedex:
    def __init__(self, discordId, pokemon):
        self.discordId = discordId
        self.pokemon = pokemon
        self.__pokedex()

    def __pokedex(self):
        """ will update the database with information on the pokemon """
        now = str(datetime.now())
        db = dbconn()
        queryString = 'SELECT 1 FROM pokedex WHERE "discord_id"=%s AND "pokemonId"=%s'
        results = db.queryAll(queryString, (self.discordId, self.pokemon.id))
        if len(results):
            updateQuery = 'UPDATE pokedex SET "mostRecent"=%s WHERE "discord_id"=%s AND "pokemonId"=%s'
            values = (now, self.discordId, str(self.pokemon.id))
        else:
            updateQuery = 'INSERT INTO pokedex ("discord_id", "pokemonId", "pokemonName", "mostRecent") VALUES (%s, %s, %s, %s)'
            values = (self.discordId, str(self.pokemon.id),
                      self.pokemon.name, now)

        db.execute(updateQuery, values)

        # delete and close connection
        del db
