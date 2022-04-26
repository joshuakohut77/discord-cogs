# pokedex class

from dbclass import db as dbconn
from pokeclass import Pokemon as pokeClass
from datetime import datetime


class pokedex:
    def __init__(self, discordId, pokemon):
        self.discordId = discordId
        self.pokemon = pokemon
        self.__pokedex()


    def __pokedex(self):
        """ will update the database with information on the pokemon """
        now = datetime.now()
        db = dbconn()
        updateQuery = """
            IF EXISTS
                (SELECT 1 FROM pokedex WHERE "discord_id"=%s AND "pokemonId"=%s)
            THEN
                UPDATE pokedex 
                SET "mostRecent"=%s
                WHERE "discord_id"=%s AND "pokemonId"=%s
            ELSE
                INSERT INTO pokedex ("discord_id", "pokemonId", "pokemonName", "mostRecent")
                    VALUES (%s, %s, %s, %s)
            END IF;
        """
        values = (self.discordId, self.pokemon.id, now, self.discordId, self.pokemon.id, self.discordId, self.pokemon.id, self.pokemon.name, now)
        db.runUpdateQuery(updateQuery, values)

        # delete and close connection
        del db