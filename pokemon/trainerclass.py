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
        return "Trainer deleted successfully!"

    def getPokeon(self):
        """ returns a list of pokemon objects for every pokemon in the database belonging to the trainer """
        db = dbconn()
        pokemonList = []
        queryString = 'SELECT id FROM pokemon WHERE discord_id = %s'
        results = db.runQuery(queryString, (self.discordId,))
        for row in results:
            trainerId = row[0]
            pokemon = pokeClass()
            pokemon.load(trainerId=trainerId)
            pokemonList.append(pokemon)
        
        # delete and close connection
        del db 
        return pokemonList

    def getActivePokemon(self):
        """ returns pokemon object of active pokemon for the trainer """
        db = dbconn() 
        
        queryString = 'SELECT "activePokemon" FROM trainer WHERE discord_id = %s'
        results = db.runQuery(queryString, (self.discordId,))
        
        trainerId = results[0][0]
        pokemon = pokeClass()
        pokemon.load(trainerId=trainerId)
        
        # delete and close connection
        del db 
        return pokemon

    def setActivePokemon(self, trainerId):
        """ sets an active pokemon unique Id in the trainer db """
        updateSuccess = False
        db = dbconn()
        queryString = 'SELECT "currentHP" FROM pokemon WHERE id=%s'
        results = db.runQuery(queryString, (trainerId,))
        if len(results) > 0:
            currentHP = results[0][0]
            if currentHP > 0:
                updateString = 'UPDATE trainer SET "activePokemon"=%s WHERE "discord_id"=%s'
                db.runUpdateQuery(updateString, (trainerId, self.discordId))
                updateSuccess = True
        
        if updateSuccess:
            retMsg = 'New Active Pokemon Set!'
        else:
            retMsg = 'Cannot set fainted Pokemon as active.'
        
        # delete and close connection
        del db
        return retMsg

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


    def heal(self, item_potion):
        # todo 
        return

    def healAll(self):
        # todo 
        return

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
        # if trainers' inventory does not exist
        queryString = 'SELECT 1 FROM inventory WHERE discord_id=%s'
        results = db.runQuery(queryString, (self.discordId,))
        if len(results) == 0:
            updateQuery = 'INSERT INTO inventory (discord_id) VALUES(%s)'
            db.runUpdateQuery(updateQuery, (self.discordId,))
        
        self.trainerExists = True

        # delete and close connection        
        del db
