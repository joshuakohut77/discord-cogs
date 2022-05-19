# trainer class
import sys
from typing import final
import config
import random
from dbclass import db as dbconn
from encounterclass import encounter
from inventoryclass import inventory as inv
from keyitemsclass import keyitems as kitems
from leaderboardclass import leaderboard
from locationclass import location as LocationClass
from loggerclass import logger as log
from pokeclass import Pokemon as pokeClass
from datetime import datetime
from time import time
import models.location as Models

# Global Config Variables
STARTER_LEVEL = 5 #config.starterLevel
RELEASE_MONEY_MODIFIER = 15 #config.release_money_modifier 
MAX_PARTY_SIZE = 6
# Class Logger
logger = log()

class trainer:
    def __init__(self, discordId):
        self.statuscode = 69 
        self.message = '' 

        self.discordId = str(discordId)
        self.trainerExists = False
        self.startdate = None
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
            pokemonUpdateQuery = 'UPDATE pokemon SET discord_id = %(newDiscordId)s WHERE discord_id = %(discordId)s'
            db.executeWithoutCommit(pokemonUpdateQuery, { 'newDiscordId': newDiscordId, 'discordId': self.discordId })
            trainerUpdateQuery = 'UPDATE trainer SET discord_id = %(newDiscordId)s WHERE discord_id = %(discordId)s'
            db.executeWithoutCommit(trainerUpdateQuery, { 'newDiscordId': newDiscordId, 'discordId': self.discordId })
            inventoryUpdateQuery = 'UPDATE inventory SET discord_id = %(newDiscordId)s WHERE discord_id = %(discordId)s'
            db.executeWithoutCommit(inventoryUpdateQuery, { 'newDiscordId': newDiscordId, 'discordId': self.discordId })
            keyItemsUpdateQuery = 'UPDATE keyitems SET discord_id = %(newDiscordId)s WHERE discord_id = %(discordId)s'
            db.executeWithoutCommit(keyItemsUpdateQuery, { 'newDiscordId': newDiscordId, 'discordId': self.discordId })
            leaderBoardUpdateQuery = 'UPDATE leaderboard SET discord_id = %(newDiscordId)s WHERE discord_id = %(discordId)s'
            db.executeWithoutCommit(leaderBoardUpdateQuery, { 'newDiscordId': newDiscordId, 'discordId': self.discordId })
            pokedexUpdateQuery = 'UPDATE pokedex SET discord_id = %(newDiscordId)s WHERE discord_id = %(discordId)s'
            db.executeWithoutCommit(pokedexUpdateQuery, { 'newDiscordId': newDiscordId, 'discordId': self.discordId })
            db.commit()
            retMsg = "Trainer deleted successfully!"
            self.statuscode = 420
        except:
            self.statuscode = 96
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
            self.statuscode = 96
            self.message = 'Trainer does not exist'
        
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
                if pokemon.statuscode == 96:
                    self.statuscode = 96
                    return
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
                if pokemon.statuscode == 96:
                    self.statuscode = 96

                # BUG:  It is possible for the pokemon to save to the db as one of the
                #       trainers pokemon, but fail to update the trainer with the starter.
                # TODO: Make the all the queries part of one transaction that will rollback
                #       if it fails.
                
                # save starter into
                pokemon.save()
                if pokemon.statuscode == 96:
                    self.statuscode = 96

                starterId = pokemon.trainerId
                
                # set as starter
                updateString = 'UPDATE trainer SET "starterId"=%(starterId)s, "activePokemon"=%(starterId)s WHERE "discord_id"=%(discordId)s'
                db.execute(updateString, { 'starterId': starterId, 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
            raise
        finally:
            # delete and close connection
            del db
            return pokemon

    def addPokemon(self, pokeId: int):
        pokemon = pokeClass(self.discordId, pokeId)
        pokemon.create(STARTER_LEVEL)
        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during pokemon create()"
            return

        pokemon.save()
        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during pokemon save()"
            return
        return pokemon

    def releasePokemon(self, pokemonId):
        """ release a pokemon and get any rewards from it """
        pokemon = pokeClass(self.discordId)
        pokemon.load(pokemonId)
        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during pokemon load()"
            return
        level = pokemon.currentLevel
        pokemon.release()
        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during pokemon release()"
            return
        inventory = inv(self.discordId)
        releaseMoney = level * RELEASE_MONEY_MODIFIER
        inventory.money += releaseMoney
        inventory.save()
        if inventory.statuscode == 96:
            self.statuscode = 96
            self.message = "error occurred during inventory.save()"
            return
        
        # leaderboard stats
        lb = leaderboard(self.discordId)
        lb.released()

    def getPokemon(self, party=False, pc=False):
        """ returns a list of pokemon objects for every pokemon in the database belonging to the trainer """
        pokemonList = []
        try:
            db = dbconn()
            if party:
                queryString = 'SELECT id FROM pokemon WHERE party = True AND discord_id = %(discordId)s'
            elif pc:
                queryString = 'SELECT id FROM pokemon WHERE party = False AND discord_id = %(discordId)s'
            else:
                queryString = 'SELECT id FROM pokemon WHERE discord_id = %(discordId)s order by party desc'
            results = db.queryAll(queryString, { 'discordId': self.discordId })
            for row in results:
                pokemonId = row[0]
                pokemon = pokeClass(self.discordId)
                pokemon.load(pokemonId=pokemonId)
                if pokemon.statuscode == 96:
                    self.statuscode = 96
                    self.message = "error occured during pokemon load()"
                    return
                pokemonList.append(pokemon)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return pokemonList

    def getPokemonById(self, trainerId: int):
        """ returns a single pokemon object belonging to the trainer """
        pokemon = None
        try:
            pokemon = pokeClass(self.discordId)
            pokemon.load(pokemonId=trainerId)

            if pokemon.statuscode == 96:
                self.statuscode = 96
                self.message = "error occured during pokemon load()"
                return
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return pokemon

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
                    if pokemon.statuscode == 96:
                        self.statuscode = 96
                        self.message = "error occured during pokemon load()"
                        return
        except:
            self.statuscode = 96
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
            queryString = 'SELECT "currentHP", "party" FROM pokemon WHERE id=%(trainerId)s'
            result = db.querySingle(queryString, { 'trainerId': trainerId })
            if result:
                currentHP = result[0]
                party = result[1]
                if not party:
                    self.statuscode = 420
                    self.message = "You can only set active a pokemon in your party"
                    return
                if currentHP > 0:
                    updateString = 'UPDATE trainer SET "activePokemon"=%(trainerId)s WHERE "discord_id"=%(discordId)s'
                    db.execute(updateString, { 'trainerId': trainerId, 'discordId' : self.discordId })
                    updateSuccess = True
            
            if updateSuccess:
                retMsg = 'New Active Pokemon Set!'
            else:
                retMsg = 'Cannot set fainted Pokemon as active.'
            self.statuscode = 420
        except:
            self.statuscode = 96 
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return retMsg
    
    def fight(self, pokemon2):
        """ creates a fight encounter """
        pokemon1 = self.getActivePokemon()
        if pokemon1 is None:
            self.statuscode = 96
            self.message = 'You do not have an active Pokemon'        
            return
        enc = encounter(pokemon1, pokemon2)
        retVal = enc.fight()

        # propagate whatever the fight statuscode/message is
        self.statuscode = enc.statuscode
        self.message = enc.message
        return retVal

    def catch(self, pokemon2, item):
        """ creates a catch encounter """
        pokemon1 = self.getActivePokemon()
        if pokemon1 is None:
            self.statuscode = 96
            self.message = 'You do not have an active Pokemon'
            return
        enc = encounter(pokemon1, pokemon2)
        retVal = enc.catch(item)
        if enc.statuscode == 96:
            self.statuscode = 96
            self.message = "error occurred during encounter.catch()"
            return

        self.statuscode = enc.statuscode
        self.message = enc.message
        return retVal

    def runAway(self, pokemon2):
        """ creates a run away encounter """
        pokemon1 = self.getActivePokemon()
        if pokemon1 is None:
            self.statuscode = 96
            self.message = 'You do not have an active Pokemon'        
        enc = encounter(pokemon1, pokemon2)
        retVal = enc.runAway()
        if enc.statuscode == 96:
            self.statuscode = 96
            self.message = "error occurred during encounter.runAway()"
        return retVal

    def encounter(self, method):
        """ handles action  """
        pokemon = None
        try:
            pokemon = self.__getEncounter(method)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return pokemon
    
    def gift(self):
        """ handles a gift action """
        retMsg = ''
        try:
            method = 'gift'
            pokemon = self.__getEncounter(method)
            pokemon.save()
            retMsg = 'You received %s!' %pokemon.pokemonName
            self.statuscode = 420
            self.message = retMsg
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())

    def getPokedex(self):
        """ returns a list of dictionary from the trainers pokedex """
        pokedex = []
        try:
            db = dbconn()
            queryString = '''SELECT "pokemonId", "pokemonName", "mostRecent" 
                FROM pokedex WHERE "discord_id"=%(discordId)s ORDER BY "pokemonId"'''
            results = db.queryAll(queryString, { 'discordId': self.discordId })
            for row in results:
                pokemonId = row[0]
                pokemonName = row[1]
                mostRecent = row[2]
                pokeDict = {'id': pokemonId,
                            'name': pokemonName, 'lastSeen': mostRecent}
                pokedex.append(pokeDict)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return pokedex

    def heal(self, pokeTrainerId, item):
        """ uses a potion to heal a pokemon """
        # this function is only designed to work with potion, super-potion, hyper-potion, max-potion
        if 'potion' not in item and 'revive' not in item:
            self.statuscode = 420
            self.message = 'You cannot use that item like that'
        inventory = inv(self.discordId)
        if item == 'potion':
            inventory.potion -= 1
        elif item == 'super-potion':
            inventory.superpotion -= 1
        elif item == 'hyper-potion':
            inventory.hyperpotion -= 1
        elif item == 'max-potion':
            inventory.maxpotion -= 1
        elif item == 'revive':
            inventory.revive -= 1
        self.__healPokemon(pokeTrainerId, item)
        if self.statuscode == 69:
            inventory.save()
        if inventory.statuscode == 96:
            self.statuscode = 96
            self.message = "error occurred during inventory.save()"
            return

    def healAll(self):
        """ heals all pokemon to max HP """
        location = self.getLocation()
        if not location.pokecenter:
            self.statuscode = 420
            self.message = "There is no Poke Center at your location"
            return
        
        pokeList = self.getPokemon(party=True)
        for pokemon in pokeList:
            trainerId = pokemon.trainerId
            pokemon.load(trainerId)
            statsDict = pokemon.getPokeStats()
            maxHP = statsDict['hp']
            if maxHP != pokemon.currentHP:
                pokemon.currentHP = maxHP
                pokemon.discordId = self.discordId
                pokemon.save()
        self.statuscode = 420
        self.message = "Your pokemon have been healed back to full health!"
        return
    
    def getLocation(self):
        try:
            db = dbconn()
            queryStr = """
            SELECT
                locations.*
            FROM locations
                join trainer on trainer."locationId" = locations."locationId"
            WHERE trainer."discord_id" = %(discordId)s
            """
            result = db.querySingle(queryStr, { 'discordId': self.discordId })
            if result:
                location = Models.LocationModel(result)
                return location
            else:
                self.statuscode = 96
                self.message = 'Location not found'
        except:
            self.statuscode = 96
        finally:
            del db
    
    def setLocation(self, locationId):
        """ updates the trainer table to set the locationId """
        try:
            db = dbconn()
            updateString = """
            UPDATE trainer
                SET "locationId"=%(locationId)s
            WHERE trainer."discord_id" = %(discordId)s
            """
            db.execute(updateString, { 'locationId': locationId, 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
            raise
        finally:
            # delete and close connection
            del db
    
    def getPartySize(self):
        """ returns a count of trainers party size """
        partySize = 0
        try:
            db = dbconn()
            queryString = """
            SELECT COUNT(*)  FROM
                Pokemon WHERE party = True 
                AND "discord_id" = %(discordId)s
            """
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                partySize = result[0]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
            raise
        finally:
            # delete and close connection
            del db
            return partySize

    def withdraw(self, trainerId):
        """ withdraw pokemon  """
        currentPartySize = self.getPartySize()
        if currentPartySize < MAX_PARTY_SIZE:
            self.__withdraw(trainerId)
            self.statuscode = 69
        else:
            self.statuscode = 420
            self.message = "You already have a full party!"
        return
    
    def deposit(self, trainerId):
        """ deposit pokemon """
        currentPartySize = self.getPartySize()
        if currentPartySize > 1:
            self.__deposit(trainerId)
        else:
            self.statuscode = 420
            self.message = "You must keep at least one pokemon in your party!"
        return

    ####
    # Private Class Methods
    ####

    def __withdraw(self, trainerId):
        """ withdraw pokemon """
        try:
            db = dbconn()
            updateString = """
            UPDATE Pokemon SET party = True
                WHERE "id" = %(trainerId)s AND "discord_id" = %(discordId)s
            """
            db.execute(updateString, { 'trainerId': trainerId, 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
            raise
        finally:
            # delete and close connection
            del db
        
    def __deposit(self, trainerId):
        """ deposit pokemon """
        try:
            db = dbconn()
            updateString = """
            UPDATE Pokemon SET party = False
                WHERE "id" = %(trainerId)s AND "discord_id" = %(discordId)s
            """
            db.execute(updateString, { 'trainerId': trainerId, 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
            raise
        finally:
            # delete and close connection
            del db

    def __checkCreateTrainer(self):
        """ this will check if a trainerId exists and if not, insert them into the database """
        try:
            db = dbconn()
            # do this check to see if trainer exists
            queryString = 'SELECT startdate FROM trainer WHERE "discord_id" = %(discordId)s'
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                self.startdate = result[0]
                return
        
            db.executeWithoutCommit('INSERT INTO trainer (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.executeWithoutCommit('INSERT INTO inventory (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.executeWithoutCommit('INSERT INTO keyitems (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.executeWithoutCommit('INSERT INTO leaderboard (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.commit()
            self.trainerExists = True
            # Always use UTC time
            self.startdate = datetime.utcnow().date()
        except:
            self.statuscode = 96
            db.rollback()
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db   
    
    def __getEncounter(self, method):
        """ gets a random encounter in the current area using the selected method """
        pokemon = None
        activePokemon = self.getActivePokemon()
        if activePokemon is None:
            self.statuscode = 420
            self.message = "You do not have an active pokemon!"
        if activePokemon.currentHP == 0:
            self.statuscode = 420
            self.message = "Your active Pokemon has no HP left!"
            return
        loc = LocationClass(self.discordId)
        selectedEncounter = loc.action(method)
        if loc.statuscode == 96:
            self.statuscode =  96
            self.message = "error occurred during loc.generateEncounter"
            return
        keyitems = kitems(self.discordId)
        if method == 'old-rod':
            if not keyitems.old_rod:
                self.statuscode = 420
                self.message = "You do not own the old-rod"
                return
        elif method == 'good-rod':
            if not keyitems.good_rod:
                self.statuscode = 420
                self.message = "You do not own the good-rod"
                return  
        elif method == 'super-rod':
            if not keyitems.super_rod:
                self.statuscode = 420
                self.message = "You do not own the super-rod"
                return  
        elif method == 'surf':
            if not keyitems.HM03:
                self.statuscode = 420
                self.message = "You do not own HM03"
                return  
        elif method == 'pokeflute':
            if not keyitems.pokeflute:
                self.statuscode = 420
                self.message = "You do not own the pokeflute"
                return  
        if selectedEncounter is not None:
            # this means a pokemon was found with the method
            name = selectedEncounter['name']
            min_level = selectedEncounter['min_level']
            max_level = selectedEncounter['max_level']
            level = random.randrange(int(min_level), int(max_level)+1)
            pokemon = pokeClass(None, name)
            pokemon.create(level)
            if pokemon.statuscode == 96:
                self.statuscode = 96
                self.message = "error occured during pokemon create()"
                return
        
        # leaderboard stats
        lb = leaderboard(self.discordId)
        lb.actions()
        return pokemon

    def __healPokemon(self, pokemonId, item):
        """ heals a pokemons currentHP """
        # this function is only designed to work with potion, super-potion, hyper-potion, max-potion
        pokemon = pokeClass(self.discordId)
        pokemon.load(pokemonId)
        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "error occured during pokemon load()"
        statsDict = pokemon.getPokeStats()
        maxHP = statsDict['hp']
        currentHP = pokemon.currentHP
        if item == 'revive':
            newHP = maxHP
        
        # every item below is a potion which cannot be used with fainted pokemon
        if currentHP <= 0:
            self.statuscode = 420
            self.message = "You cannot use a potion on a fainted pokemon"
            return
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
        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "error occurred during pokemon.save()"
            return
