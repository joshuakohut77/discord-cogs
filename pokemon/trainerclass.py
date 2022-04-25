# trainer class

from dbclass import db as dbconn
from pokeclass import Pokemon as pokeClass
import config
import random
from time import time


class trainer:
    def __init__(self, discordId):
        self.discordId = str(discordId)
        self.trainerExists = False
        # check create trainer if exists or not
        self.__checkCreateTrainer()

    
    def deleteTrainer(self):
        """soft deletes a trainer and all of their pokemon """
        db = dbconn()
        # use milliseconds as a way to get a unique number. used to soft delete a value and still retain original discordId
        milliString = str(int(time() * 1000))
        newDiscordId = self.discordId + '_' + milliString
        pokemonUpdateQuery = 'UPDATE pokemon SET discord_id = %s WHERE discord_id = %s'
        db.runUpdateQuery(pokemonUpdateQuery, (newDiscordId, self.discordId))
        trainerUpdateQuery = 'UPDATE trainer SET discord_id = %s WHERE discord_id = %s'
        db.runUpdateQuery(trainerUpdateQuery, (newDiscordId, self.discordId))

        # delete and close connection
        del db 



    def getStarterPokemon(self):
        """ returns a random starter pokemon dictionary {pokemon: id} """
        if not self.trainerExists:
            return None
        db = dbconn()
        queryString = 'SELECT "has_starter", "starterId" FROM trainer WHERE discord_id = %s'
        
        results = db.runQuery(queryString, (self.discordId,))

        hasStarter = False
        starterId = -1
        for result in results:
            # if at least one row returned then the trainer exists otherwise they do not
            hasStarter = result[0]
            starterId = result[1]

        if not hasStarter:
            # trainer does not yet have a starter, create one
            if 'cactitwig' in self.discordId.lower():
                starter = {'rattata': 19}
                starterId = list(starter.values())[0]
            else:
                sequence = [{'bulbasaur': 1}, {'charmander': 4}, {'squirtle': 7}]
                starter = random.choice(sequence)
                starterId = list(starter.values())[0]
        
        #create pokemon with unique stats using the pokemon class
        pokemon = pokeClass(starterId)
        if hasStarter:
            pokemon.load()
        if not hasStarter:
            pokemon.create(config.starterLevel)
            updateString = 'UPDATE trainer SET "has_starter"=True, "starterId"=%s WHERE "discord_id"=%s'
            db.runUpdateQuery(updateString, (starterId, self.discordId))
            # save starter into
            pokemon.save(self.discordId)
        # delete and close connection
        del db

        return pokemon




    ####
    ###   Private Class Methods
    ####

    def __checkCreateTrainer(self):
        """ this will check if a trainerId exists and if not, insert them into the database """
        db = dbconn()
        queryString = 'SELECT 1 FROM trainer WHERE discord_id=%s'
        results = db.runQuery(queryString, (self.discordId,))
        #if trainer does not exist
        if len(results) == 0:
            # insert new row into trainer table 
            updateQuery = 'INSERT INTO trainer (discord_id) VALUES(%s)'
            db.runUpdateQuery(updateQuery, (self.discordId,))

        self.trainerExists = True

        # delete and close connection        
        del db


newTrainer = trainer(discordId='789')

pokemon = newTrainer.getStarterPokemon()

print(pokemon.name)

newTrainer.deleteTrainer()

