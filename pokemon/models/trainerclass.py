# trainer class

from dbclass import db as dbconn
from pokeclass import Pokemon as pokeClass
from inventoryclass import inventory as inv
from locationclass import location
from encounterclass import encounter
# import config
import random
from time import time

# STARTER_LEVEL = config.starterLevel
# TOTAL_POKEMON = config.total_pokemon
STARTER_LEVEL = 6
TOTAL_POKEMON = 150

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
        db.execute(pokemonUpdateQuery, (newDiscordId, self.discordId))
        trainerUpdateQuery = 'UPDATE trainer SET discord_id = %s WHERE discord_id = %s'
        db.execute(trainerUpdateQuery, (newDiscordId, self.discordId))
        inventoryUpdateQuery = 'UPDATE inventory SET discord_id = %s WHERE discord_id = %s'
        db.execute(inventoryUpdateQuery, (newDiscordId, self.discordId))

        # delete and close connection
        del db
        return "Trainer deleted successfully!"

    def getPokemon(self):
        """ returns a list of pokemon objects for every pokemon in the database belonging to the trainer """
        db = dbconn()
        pokemonList = []
        queryString = 'SELECT id FROM pokemon WHERE "discord_id" = %s'
        results = db.queryAll(queryString, (self.discordId,))

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
        results = db.queryAll(queryString, (self.discordId,))

        trainerId = results[0][0]
        if trainerId is None:
            pokemon = "You do not have an active Pokemon!"
        else:
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
        results = db.queryAll(queryString, (trainerId,))
        if len(results) > 0:
            currentHP = results[0][0]
            if currentHP > 0:
                updateString = 'UPDATE trainer SET "activePokemon"=%s WHERE "discord_id"=%s'
                db.execute(updateString, (trainerId, self.discordId))
                updateSuccess = True

        if updateSuccess:
            retMsg = 'New Active Pokemon Set!'
        else:
            retMsg = 'Cannot set fainted Pokemon as active.'

        # delete and close connection
        del db
        return retMsg
    
    def fight(self, pokemon2):
        """ creates a fight encounter """
        pokemon1 = self.getActivePokemon()
        if pokemon1 is None:
            return 'You do not have an active Pokemon'        
        enc = encounter(pokemon1, pokemon2)
        return enc.fight()

    def catch(self, pokemon2, item):
        """ creates a catch encounter """
        pokemon1 = self.getActivePokemon()
        if pokemon1 is None:
            return 'You do not have an active Pokemon'        
        enc = encounter(pokemon1, pokemon2)
        return enc.catch(item)

    def runAway(self, pokemon2):
        """ creates a run away encounter """
        pokemon1 = self.getActivePokemon()
        if pokemon1 is None:
            return 'You do not have an active Pokemon'        
        enc = encounter(pokemon1, pokemon2)
        return enc.runAway()

    def getAreaMethods(self):
        """ returns the encounter methods in the trainers area """
        # before starting any area business, verify an active pokemon is set
        pokemon1 = self.getActivePokemon()
        if pokemon1 is None:
            return 'You do not have an active Pokemon'
        areaId = self.getAreaId()
        loc = location()
        areaEncounters = loc.getAreaEncounterDetails(areaId)
        return loc.getMethods(areaEncounters)

    def getRandomEncounter(self, method):
        """ gets a random encounter in the current area using the selected method """
        pokemon = None
        areaId = self.getAreaId()
        loc = location()
        areaEncounters = loc.getAreaEncounterDetails(areaId)
        randomEncounter = loc.generateEncounter(areaEncounters, method)
        if randomEncounter is not None:
            # this means a pokemon was found with the method
            name = randomEncounter['name']
            min_level = randomEncounter['min_level']
            max_level = randomEncounter['max_level']
            level = random.randrange(int(min_level), int(max_level)+1)
            pokemon = pokeClass(name)
            pokemon.create(level)
        
        return pokemon

    # TODO: This needs to update the trainers pokedex
    def getStarterPokemon(self):
        """ returns a random starter pokemon dictionary {pokemon: id} """
        if not self.trainerExists:
            return None
        db = dbconn()
        queryString = 'SELECT "starterId" FROM trainer WHERE discord_id = %s'

        result = db.querySingle(queryString, (self.discordId,))

        hasStarter = False
        starterId = -1
        if len(result) > 0:
            # if at least one row returned then the trainer exists otherwise they do not
            starterId = result[0]
            if starterId is not None:
                hasStarter = True

        if not hasStarter:
            # trainer does not yet have a starter, create one
            if 'cactitwig' in self.discordId.lower():
                starter = {'rattata': 19}
                starterId = list(starter.values())[0]
            else:
                sequence = [{'bulbasaur': 1}, {
                    'charmander': 4}, {'squirtle': 7}]
                starter = random.choice(sequence)
                starterId = list(starter.values())[0]

        # create pokemon with unique stats using the pokemon class
        pokemon = pokeClass(starterId)
        if hasStarter:
            pokemon.load(pokemon.id)
        if not hasStarter:
            pokemon.create(STARTER_LEVEL)
            updateString = 'UPDATE trainer SET "starterId"=%s WHERE "discord_id"=%s'
            db.execute(updateString, (starterId, self.discordId))
            # save starter into
            pokemon.save(self.discordId)
        # delete and close connection
        del db

        return pokemon

    # def getPokemon(self, pokemonId):
    #     pokemon = pokeClass(pokemonId)
    #     pokemon.load()
    #     return pokemon

    def getPokedex(self):
        """ returns a list of dictionary from the trainers pokedex """
        pokedex = []
        db = dbconn()
        queryString = 'SELECT "pokemonId", "pokemonName", "mostRecent" FROM pokedex WHERE "discord_id"=%s ORDER BY "pokemonId"'
        results = db.queryAll(queryString, (self.discordId,))

        for row in results:
            pokemonId = row[0]
            pokemonName = row[1]
            mostRecent = row[2]
            pokeDict = {'id': pokemonId,
                        'name': pokemonName, 'lastSeen': mostRecent}
            pokedex.append(pokeDict)

        totalCaught = str(len(results)) + '/' + str(TOTAL_POKEMON)

        # delete and close connection
        del db
        # return totalCaught, pokedex
        return pokedex

    def heal(self, trainerId, item):
        """ uses a potion to heal a pokemon """
        inventory = inv(self.discordId)
        if inventory.potion > 0:
            inventory.potion = inventory.potion - 1
            inventory.save()

        self.__healPokemon(trainerId, item)
        return

    def healAll(self):
        """ heals all pokemon to max HP """
        pokeList = self.getPokemon()
        for pokemon in pokeList:
            trainerId = pokemon.trainerId
            pokemon.load(trainerId)
            statsDict = pokemon.getPokeStats()
            maxHP = statsDict['hp']
            if maxHP != pokemon.currentHP:
                pokemon.currentHP = maxHP
                pokemon.save(self.discordId)
        return

    def getAreaId(self):
        """ returns the current area Id of the trainer """
        db = dbconn()
        queryString = 'SELECT "areaId" FROM trainer WHERE discord_id=%s'
        result = db.querySingle(queryString, (self.discordId,))
        areaId = result[0]

        # delete and close connection
        del db
        return areaId

    def getLocationId(self):
        """ returns the current location Id of the trainer """
        db = dbconn()
        queryString = 'SELECT "locationId" FROM trainer WHERE discord_id=%s'
        result = db.querySingle(queryString, (self.discordId,))
        locationId = result[0]

        # delete and close connection
        del db
        return locationId

    ####
    # Private Class Methods
    ####

    def __checkCreateTrainer(self):
        """ this will check if a trainerId exists and if not, insert them into the database """
        # Only do this check once
        if self.trainerExists:
            return

        db = dbconn()
        queryString = 'SELECT 1 FROM trainer WHERE discord_id=%s'
        results = db.queryAll(queryString, (self.discordId,))
        # if trainer does not exist
        if len(results) == 0:
            # insert new row into trainer table
            updateQuery = 'INSERT INTO trainer (discord_id) VALUES(%s)'
            db.execute(updateQuery, (self.discordId,))
        # if trainers' inventory does not exist
        queryString = 'SELECT 1 FROM inventory WHERE discord_id=%s'
        results = db.queryAll(queryString, (self.discordId,))
        if len(results) == 0:
            updateQuery = 'INSERT INTO inventory (discord_id) VALUES(%s)'
            db.execute(updateQuery, (self.discordId,))

        self.trainerExists = True

        # delete and close connection
        del db

    def __healPokemon(self, trainerId, item):
        """ heals a pokemons currentHP """
        pokemon = pokeClass()
        pokemon.load(trainerId)
        statsDict = pokemon.getPokeStats()
        maxHP = statsDict['hp']
        currentHP = pokemon.currentHP
        # todo update to not hard coded value
        newHP = currentHP + 20
        if newHP > maxHP:
            newHP = maxHP

        pokemon.currentHP = newHP
        pokemon.save(self.discordId)

