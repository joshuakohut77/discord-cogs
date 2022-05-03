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
STARTER_LEVEL = 5
TOTAL_POKEMON = 150
RELEASE_MONEY_MODIFIER = 20 # when you release a pokemon, you will get 15*level of released pokemon

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

    # TODO: This needs to update the trainers pokedex
    def getStarterPokemon(self):
        """Returns a random starter pokemon dictionary {pokemon: id} """
        if not self.trainerExists:
            return None
        db = dbconn()
        queryString = 'SELECT "starterId" FROM trainer WHERE discord_id = %s'

        result = db.querySingle(queryString, (self.discordId,))

        starterId: int = None

        # if at least one row returned then the trainer exists otherwise they do not
        if len(result) > 0:
            starterId = result[0]

        # create pokemon with unique stats using the pokemon class
        if starterId is not None:
            pokemon = pokeClass(starterId)
            pokemon.load(pokemonId=starterId)
        else:
            pokeId: int = None
            # trainer does not yet have a starter, create one
            if '500047678378344449' in self.discordId.lower() or self.discordId == '500047678378344449':
                starter = {'rattata': 19}
                pokeId = starter['rattata']
            else:
                sequence = [
                    {'bulbasaur': 1},
                    {'charmander': 4},
                    {'squirtle': 7}]
                starter = random.choice(sequence)
                pokeId = list(starter.values())[0]

            pokemon = pokeClass(pokeId)
            pokemon.create(STARTER_LEVEL)

            # BUG:  It is possible for the pokemon to save to the db as one of the
            #       trainers pokemon, but fail to update the trainer with the starter.
            # TODO: Make the all the queries part of one transaction that will rollback
            #       if it fails.
            
            # save starter into
            pokemon.save(self.discordId)

            starterId = pokemon.trainerId
            
            # set as starter
            updateString = 'UPDATE trainer SET "starterId"=%s, "activePokemon"=%s WHERE "discord_id"=%s'
            db.execute(updateString, (starterId, starterId, self.discordId))
        # delete and close connection
        del db

        return pokemon

    def addPokemon(self, pokeId: int):
        pokemon = pokeClass(pokeId)
        pokemon.create(STARTER_LEVEL)
        pokemon.save(self.discordId)
        return pokemon

    def releasePokemon(self, pokemonId):
        """ release a pokemon and get any rewards from it """
        pokemon = pokeClass()
        pokemon.load(pokemonId)
        level = pokemon.currentLevel
        pokemon.release()
        inventory = inv(self.discordId)
        releaseMoney = level * RELEASE_MONEY_MODIFIER
        inventory.money += releaseMoney
        inventory.save()
        return 

    def getPokemon(self):
        """ returns a list of pokemon objects for every pokemon in the database belonging to the trainer """
        db = dbconn()
        pokemonList = []
        queryString = 'SELECT id FROM pokemon WHERE discord_id = %s'
        results = db.queryAll(queryString, (self.discordId,))

        for row in results:
            pokemonId = row[0]
            pokemon = pokeClass()
            pokemon.load(pokemonId=pokemonId)
            pokemonList.append(pokemon)
        # delete and close connection
        del db
        return pokemonList

    def getActivePokemon(self):
        """ returns pokemon object of active pokemon for the trainer """
        db = dbconn()

        queryString = 'SELECT "activePokemon" FROM trainer WHERE discord_id = %s'
        results = db.queryAll(queryString, (self.discordId,))

        pokemonId = results[0][0]
        if pokemonId is None:
            pokemon = "You do not have an active Pokemon!"
        else:
            pokemon = pokeClass()
            pokemon.load(pokemonId=pokemonId)

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
        # TODO update for all healing items
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

    def __healPokemon(self, pokemonId, item):
        """ heals a pokemons currentHP """
        pokemon = pokeClass()
        pokemon.load(pokemonId)
        statsDict = pokemon.getPokeStats()
        maxHP = statsDict['hp']
        currentHP = pokemon.currentHP
        # todo update to not hard coded value
        newHP = currentHP + 20
        if newHP > maxHP:
            newHP = maxHP

        pokemon.currentHP = newHP
        pokemon.save(self.discordId)

