# trainer class
import sys
import random
from dbclass import db as dbconn
from encounterclass import encounter
from inventoryclass import inventory as inv
from locationclass import location
from loggerclass import logger as log
from pokeclass import Pokemon as pokeClass
from time import time

# import config
# STARTER_LEVEL = config.starterLevel
# TOTAL_POKEMON = config.total_pokemon
STARTER_LEVEL = 5
TOTAL_POKEMON = 150
RELEASE_MONEY_MODIFIER = 15 # when you release a pokemon, you will get 15*level of released pokemon
logger = log()

class trainer:
    def __init__(self, discordId):
        self.faulted = False
        self.discordId = str(discordId)
        self.trainerExists = False
        # check create trainer if exists or not
        self.__checkCreateTrainer()

    def deleteTrainer(self):
        """soft deletes a trainer and all of their pokemon """
        retMsg = ''
        try:
            db = dbconn()
            # use milliseconds as a way to get a unique number. used to soft delete a value and still retain original discordId
            milliString = str(int(time() * 1000))
            newDiscordId = self.discordId + '_' + milliString
            pokemonUpdateQuery = 'UPDATE pokemon SET discord_id = %s WHERE discord_id = %s'
            db.executeWithoutCommit(pokemonUpdateQuery, (newDiscordId, self.discordId))
            trainerUpdateQuery = 'UPDATE trainer SET discord_id = %s WHERE discord_id = %s'
            db.executeWithoutCommit(trainerUpdateQuery, (newDiscordId, self.discordId))
            inventoryUpdateQuery = 'UPDATE inventory SET discord_id = %s WHERE discord_id = %s'
            db.executeWithoutCommit(inventoryUpdateQuery, (newDiscordId, self.discordId))
            db.commit()
            retMsg = "Trainer deleted successfully!"
        except:
            self.faulted = True
            retMsg = "Error occured while trying to delete trainer"
            db.rollback()
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return retMsg

    # TODO: This needs to update the trainers pokedex
    def getStarterPokemon(self):
        """Returns a random starter pokemon dictionary {pokemon: id} """
        if not self.trainerExists:
            return None
        pokemon = None
        try:
            db = dbconn()
            queryString = 'SELECT "starterId" FROM trainer WHERE discord_id = %(discordId)s'
            result = db.querySingle(queryString, { 'discordId': self.discordId })

            starterId: int = None

            # if at least one row returned then the trainer exists otherwise they do not
            if result:
                starterId = result[0]

            # create pokemon with unique stats using the pokemon class
            if starterId is not None:
                pokemon = pokeClass(self.discordId, starterId)
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

                pokemon = pokeClass(self.discordId, pokeId)
                pokemon.create(STARTER_LEVEL)

                # BUG:  It is possible for the pokemon to save to the db as one of the
                #       trainers pokemon, but fail to update the trainer with the starter.
                # TODO: Make the all the queries part of one transaction that will rollback
                #       if it fails.
                
                # save starter into
                pokemon.discordId = self.discordId
                pokemon.save()

                starterId = pokemon.trainerId
                
                # set as starter
                updateString = 'UPDATE trainer SET "starterId"=%(starterId)s, "activePokemon"=%(starterId)s WHERE "discord_id"=%(discordId)s'
                db.execute(updateString, { 'starterId': starterId, 'discordId': self.discordId })
        except:
            self.faulted = True
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return pokemon

    def addPokemon(self, pokeId: int):
        pokemon = pokeClass(self.discordId, pokeId)
        pokemon.create(STARTER_LEVEL)
        pokemon.discordId = self.discordId
        pokemon.save()
        return pokemon

    def releasePokemon(self, pokemonId):
        """ release a pokemon and get any rewards from it """
        pokemon = pokeClass(self.discordId)
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
        pokemonList = []
        try:
            db = dbconn()
            queryString = 'SELECT id FROM pokemon WHERE discord_id = %(discordId)s'
            results = db.queryAll(queryString, { 'discordId': self.discordId })
            for row in results:
                pokemonId = row[0]
                pokemon = pokeClass(self.discordId)
                pokemon.load(pokemonId=pokemonId)
                pokemonList.append(pokemon)
        except:
            self.faulted = True
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return pokemonList

    def getActivePokemon(self):
        """ returns pokemon object of active pokemon for the trainer """
        pokemon = None
        try:
            db = dbconn()
            queryString = 'SELECT "activePokemon" FROM trainer WHERE discord_id = %(discordId)s'
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                pokemonId = result[0]
                if pokemonId is None:
                    pokemon = "You do not have an active Pokemon!"
                else:
                    pokemon = pokeClass(self.discordId)
                    pokemon.load(pokemonId=pokemonId)
        except:
            self.faulted = True
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return pokemon

    def setActivePokemon(self, trainerId):
        """ sets an active pokemon unique Id in the trainer db """
        updateSuccess = False
        retMsg = ''
        try:
            db = dbconn()
            queryString = 'SELECT "currentHP" FROM pokemon WHERE id=%(trainerId)s'
            result = db.querySingle(queryString, { 'trainerId': trainerId })
            if result:
                currentHP = result[0]
                if currentHP > 0:
                    updateString = 'UPDATE trainer SET "activePokemon"=%(trainerId)s WHERE "discord_id"=%(discordId)s'
                    db.execute(updateString, { 'trainerId': trainerId, 'discordId' : self.discordId })
                    updateSuccess = True
            
            if updateSuccess:
                retMsg = 'New Active Pokemon Set!'
            else:
                retMsg = 'Cannot set fainted Pokemon as active.'
        except:
            self.faulted = True 
            retMsg = 'An error occured'
            logger.error(excInfo=sys.exc_info())
        finally:
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
        pokemon = self.getActivePokemon()
        if pokemon is None:
            return 'You do not have an active Pokemon'
        locationId = self.getLocationId()
        loc = location()
        areaIdList = loc.getAreaList(locationId)
        areaEncounters = loc.getAreaEncounterDetails(areaIdList)
        return loc.getMethods(areaEncounters)

    def getRandomEncounter(self, method):
        """ gets a random encounter in the current area using the selected method """
        pokemon = None
        locationId = self.getLocationId()
        loc = location()
        areaIdList = loc.getAreaList(locationId)
        areaEncounters = loc.getAreaEncounterDetails(areaIdList)
        randomEncounter = loc.generateEncounter(areaEncounters, method)
        if randomEncounter is not None:
            # this means a pokemon was found with the method
            name = randomEncounter['name']
            min_level = randomEncounter['min_level']
            max_level = randomEncounter['max_level']
            level = random.randrange(int(min_level), int(max_level)+1)
            pokemon = pokeClass(self.discordId, name)
            pokemon.create(level)
        
        return pokemon

    def getPokedex(self):
        """ returns a list of dictionary from the trainers pokedex """
        pokedex = []
        try:
            db = dbconn()
            queryString = 'SELECT "pokemonId", "pokemonName", "mostRecent" FROM pokedex WHERE "discord_id"=%(discordId)s ORDER BY "pokemonId"'
            results = db.queryAll(queryString, { 'discordId': self.discordId })
            for row in results:
                pokemonId = row[0]
                pokemonName = row[1]
                mostRecent = row[2]
                pokeDict = {'id': pokemonId,
                            'name': pokemonName, 'lastSeen': mostRecent}
                pokedex.append(pokeDict)
        except:
            self.faulted = True
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return pokedex

    def heal(self, pokeTrainerId, item):
        """ uses a potion to heal a pokemon """
        # this function is only designed to work with potion, super-potion, hyper-potion, max-potion
        if 'potion' not in item:
            return 'You cannot use that item like that'
        inventory = inv(self.discordId)
        if item == 'potion':
            inventory.potion -= 1
        elif item == 'super-potion':
            inventory.superpotion -= 1
        elif item == 'hyper-potion':
            inventory.hyperpotion -= 1
        elif item == 'max-potion':
            inventory.maxpotion -= 1
        self.__healPokemon(pokeTrainerId, item)
        inventory.save()
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
                pokemon.discordId = self.discordId
                pokemon.save()
        return

    def getLocationId(self):
        """ returns the current location Id of the trainer """
        locationId = None
        try:
            db = dbconn()
            queryString = 'SELECT "locationId" FROM trainer WHERE discord_id=%(discordId)s'
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                locationId = result[0]
        except:
            self.faulted = True
            logger.error(excInfo=sys.exc_info())
        finally:
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
        try:
            db = dbconn()        
            db.executeWithoutCommit('INSERT INTO trainer (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.executeWithoutCommit('INSERT INTO inventory (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.commit()
            self.trainerExists = True
        except:
            self.faulted = True
            db.rollback()
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db   

    def __healPokemon(self, pokemonId, item):
        """ heals a pokemons currentHP """
        # this function is only designed to work with potion, super-potion, hyper-potion, max-potion
        pokemon = pokeClass(self.discordId)
        pokemon.load(pokemonId)
        statsDict = pokemon.getPokeStats()
        maxHP = statsDict['hp']
        currentHP = pokemon.currentHP
        if item == 'potion':
            newHP = currentHP + 20
        elif item == 'super-potion':
            newHP = currentHP + 50
        elif item == 'hyper-potion':
            newHP = currentHP + 200
        elif item == 'max-potion':
            newHP = maxHP

        if newHP > maxHP:
            newHP = maxHP

        pokemon.currentHP = newHP
        pokemon.discordId = self.discordId
        pokemon.save()

