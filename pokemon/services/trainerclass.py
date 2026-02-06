# trainer class
import os
import sys
from typing import final
# import config
import json
import random

from dbclass import db as dbconn
from inventoryclass import inventory as inv
from keyitemsclass import keyitems as kitems
from leaderboardclass import leaderboard
from pokedexclass import pokedex
from locationclass import location as LocationClass
from loggerclass import logger as log
from pokeclass import Pokemon as pokeClass
from questclass import quests
from uniqueencounters import uniqueEncounters as uEnc
from datetime import datetime
from time import time
from models.location import LocationModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .encounterclass import encounter


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
        self.lastGiftPokemon = None
        # check create trainer if exists or not
        self.__checkCreateTrainer()

    def deleteTrainer(self):
        """soft deletes a trainer and all of their pokemon """
        retMsg = ''
        db = None
        try:
            db = dbconn()
            # use a shorter timestamp to avoid exceeding varchar limits
            # Unix timestamp in seconds is only 10 digits
            milliString = str(int(time()))
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
            
            trainerBattlesUpdateQuery = 'UPDATE trainer_battles SET discord_id = %(newDiscordId)s WHERE discord_id = %(discordId)s'
            db.executeWithoutCommit(trainerBattlesUpdateQuery, { 'newDiscordId': newDiscordId, 'discordId': self.discordId })
            
            uniqueEncountersUpdateQuery = 'UPDATE "unique-encounters" SET discord_id = %(newDiscordId)s WHERE discord_id = %(discordId)s'
            db.executeWithoutCommit(uniqueEncountersUpdateQuery, { 'newDiscordId': newDiscordId, 'discordId': self.discordId })
            
            db.commit()
            retMsg = "Trainer deleted successfully!"
            self.statuscode = 420
        except Exception as e:
            self.statuscode = 96
            retMsg = f"Error occurred while trying to delete trainer: {str(e)}"
            if db:
                db.rollback()
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            if db:
                del db
            return retMsg

    def setTrainerName(self, trainerName: str):
        """Set the trainer's name"""
        if not self.trainerExists:
            self.statuscode = 96
            self.message = 'Trainer does not exist'
            return
        
        try:
            db = dbconn()
            updateString = 'UPDATE trainer SET "trainerName"=%(trainerName)s WHERE "discord_id"=%(discordId)s'
            db.execute(updateString, {'trainerName': trainerName, 'discordId': self.discordId})
            self.statuscode = 420
        except:
            self.statuscode = 96
            self.message = "Error occurred while setting trainer name"
            logger.error(excInfo=sys.exc_info())
            db.rollback()
        finally:
            del db

    # TODO: This needs to update the trainers pokedex
    def getStarterPokemon(self):
        """Returns a random starter pokemon dictionary {pokemon: id} """
        from pokedexclass import pokedex as PokedexClass
        
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

                pokemon.discordId = self.discordId
                pokemon.party = True

                # save starter into
                pokemon.save()
                if pokemon.statuscode == 96:
                    self.statuscode = 96

                starterId = pokemon.trainerId
                starterName = pokemon.pokemonName
                
                # set as starter
                updateString = 'UPDATE trainer SET "starterName"=%(starterName)s, "starterId"=%(starterId)s, "activePokemon"=%(starterId)s WHERE "discord_id"=%(discordId)s'
                db.execute(updateString, { 'starterName': starterName, 'starterId': starterId, 'discordId': self.discordId })
                
                # Register starter Pokemon to player's Pokedex
                PokedexClass(self.discordId, pokemon)
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

        self.statuscode = 420
        self.message = f"You gained ¥{releaseMoney}!"
        
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
                pokemon.trainerId = pokemonId
                # pokemon.load(pokemonId=pokemonId)
                # if pokemon.statuscode == 96:
                #     self.statuscode = 96
                #     self.message = "error occured during pokemon load()"
                #     return
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
        self.statuscode = 69
        updateSuccess = False
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
                # The frontend will send back it's own customized message
                self.statuscode = 69
            else:
                self.message = 'Cannot set fainted Pokemon as active.'
                self.statuscode = 420
        except:
            self.statuscode = 96 
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return self.message
    

    def loadPartyView(self):
        """ returns a list of pokemon data that are in the trainers party for a pillow party view"""
        pokeList = self.getPokemon(party=True)
        partyList = []
        for pokemon in pokeList:
            partyDict = {}
            trainerId = pokemon.trainerId
            pokemon.load(trainerId)
            statsDict = pokemon.getPokeStats()
            maxHP = statsDict['hp']
            partyDict['PokemonName'] = pokemon.pokemonName
            partyDict['NickName'] = pokemon.nickName
            partyDict['CurrentLevel'] = pokemon.currentLevel
            partyDict['CurrentHP'] = pokemon.currentHP
            partyDict['MaxHP'] = maxHP
            partyDict['PartySprite'] = pokemon.getPartySprite()
            partyList.append(partyDict)

        return partyList

    def fight(self, pokemon2):
        """ creates a fight encounter """
        from .encounterclass import encounter
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
        from .encounterclass import encounter
        pokemon1 = self.getActivePokemon()
        if pokemon1 is None:
            self.statuscode = 96
            self.message = 'You do not have an active Pokemon'
            return
        enc = encounter(pokemon1, pokemon2)
        retVal = enc.catch(item)

        self.statuscode = enc.statuscode
        self.message = enc.message
        return retVal

    def runAway(self, pokemon2):
        """ creates a run away encounter """
        from .encounterclass import encounter
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
    
    def quest(self, questName):
        """ handles quest action  """
        qclass = quests(str(self.discordId))

        qclass.questHandler(questName)

        self.statuscode = qclass.statuscode
        self.message = qclass.message
        return 
    
    def gift(self, method='gift'):
        """ handles a gift action """
        retMsg = ''
        giftCompleted = False
        pokemon = None  # Add this to track the pokemon
        try:
            location = self.getLocation()
            locationId = location.locationId
            if locationId in [67, 86, 120, 234, 2347]:
                uEncObj = uEnc(str(self.discordId))
                if locationId == 67:
                    if uEncObj.eevee:
                        giftCompleted = True
                elif locationId == 86:
                    if uEncObj.squirtle or uEncObj.charmander or uEncObj.bulbasaur:
                        giftCompleted = True
                elif locationId == 120:
                    if uEncObj.magikarp:
                        giftCompleted = True
                elif locationId == 2347:
                    if uEncObj.lapras:
                        giftCompleted = True
                elif locationId == 234:
                    if uEncObj.hitmonchan or uEncObj.hitmonlee:
                        giftCompleted = True
                
                if giftCompleted:
                    self.statuscode = 420
                    self.message = "You have already received the gift in this location"
                    return

            if not giftCompleted:
                method = 'gift'
                pokemon = self.__getEncounter(method)
                if pokemon is None:
                    return
                
                # Check party size before saving (same as catch logic)
                party_count = self.getPartySize()
                
                # Set ownership and party status
                pokemon.discordId = self.discordId
                pokemon.party = party_count < 6
                
                # Save the pokemon
                pokemon.save()
                
                if pokemon.statuscode == 96:
                    self.statuscode = 96
                    self.message = "error occurred during pokemon.save()"
                    return
                
                # Add to pokedex
                pokedex(self.discordId, pokemon)
                
                retMsg = 'You received %s!' % pokemon.pokemonName
                self.statuscode = 420
                self.message = retMsg
                self.lastGiftPokemon = pokemon  # ADD THIS LINE to store the pokemon
        except:
            self.statuscode = 96
            self.message = 'error in receiving gift'
            logger.error(excInfo=sys.exc_info())

    def onlyone(self, method='only-one'):
        """ handles a gift action """
        pokemon = None
        try:
            location: LocationModel = self.getLocation()
            locationId = location.locationId
            
            # Check if this is a tracked unique encounter location
            if locationId in [1364, 147, 158, 159, 91, 95]:
                uEncObj = uEnc(self.discordId)
                onlyoneCompleted = False
                
                if locationId == 136:
                    if uEncObj.articuno:
                        onlyoneCompleted = True
                elif locationId == 158:
                    if uEncObj.zapdos:
                        onlyoneCompleted = True
                elif locationId == 159:
                    if uEncObj.moltres:
                        onlyoneCompleted = True
                elif locationId == 147:
                    if uEncObj.mewtwo:
                        onlyoneCompleted = True
                elif locationId == 91 or locationId == 95:
                    if uEncObj.snorlax:
                        onlyoneCompleted = True
                
                if onlyoneCompleted:
                    self.statuscode = 420
                    self.message = "You have already completed that action in this location"
                    return pokemon  # Return early - don't continue!
            
            # Only reach here if not completed or not a tracked location
            method = 'only-one'
            pokemon = self.__getEncounter(method)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            return pokemon

    def useItem(self, pokeTrainerId, item):
        """ tries to use an item and calls the respective helper function """
        
        # TODO Update to see if them item is a "use on pokemon" type of item rather than just "use"
        if pokeTrainerId is not None:
            pokemon = pokeClass(self.discordId)
            pokemon.load(pokeTrainerId)
            if pokemon.statuscode == 96:
                self.statuscode = 96
                self.message = "error occured during pokemon load()"
                return
        
            if item in ['potion', 'super-potion', 'hyper-potion', 'max-potion', 'revive', 'full-restore']:
                return self.heal(pokemon, item)
            elif item in ['moon-stone', 'leaf-stone', 'fire-stone', 'water-stone', 'thunder-stone']:
                return self.evolveItem(pokemon, item)
            else:
                self.statuscode = 420
                self.message = "Use of that item is not supported yet"
        
        else:
            self.statuscode = 420
            self.message = "Use of that item is not supported yet"

    def heal(self, pokemon, item):
        """ uses a potion to heal a pokemon """
        # this function is only designed to work with potion, super-potion, hyper-potion, max-potion

        # only use revive on fainted pokemon
        if item == 'revive' and pokemon.currentHP > 0:
            self.statuscode = 420
            self.message = "You cannot use revive on this pokemon"
            return

        inventory = inv(self.discordId)
        invalidQty = False
        if item == 'potion':
            if inventory.potion <= 0:
                invalidQty = True
            else:
                inventory.potion -= 1
        elif item == 'super-potion':
            if inventory.superpotion <= 0:
                invalidQty = True
            else:
                inventory.superpotion -= 1
        elif item == 'hyper-potion':
            if inventory.hyperpotion <= 0:
                invalidQty = True
            else:
                inventory.hyperpotion -= 1
        elif item == 'max-potion':
            if inventory.maxpotion <= 0:
                invalidQty = True
            else:
                inventory.maxpotion -= 1
        elif item == 'revive':
            if inventory.revive <= 0:
                invalidQty = True
            else:
                inventory.revive -= 1
        elif item == 'full-restore':
            if inventory.fullrestore <= 0:
                invalidQty = True
            else:
                inventory.fullrestore -= 1
        
        if invalidQty:
            self.statuscode = 420
            self.message = "You do not have enough of that item"
            return

        self.__healPokemon(pokemon, item)

        if inventory.statuscode == 96:
            self.statuscode = 96
            self.message = "error occurred during inventory updates"
            return
        else:
            inventory.save()

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
    
    def evolveItem(self, pokemon, item):
        """ handles use of the *-stone tiems for evolving pokemon"""

        inventory = inv(self.discordId)
        invalidQty = False
        if item == 'water-stone':
            if inventory.waterstone <= 0:
                invalidQty = True
            else:
                inventory.waterstone -= 1
        elif item == 'fire-stone':
            if inventory.firestone <= 0:
                invalidQty = True
            else:
                inventory.firestone -= 1
        elif item == 'thunder-stone':
            if inventory.thunderstone <= 0:
                invalidQty = True
            else:
                inventory.thunderstone -= 1
        elif item == 'moon-stone':
            if inventory.moonstone <= 0:
                invalidQty = True
            else:
                inventory.moonstone -= 1
        elif item == 'leaf-stone':
            if inventory.leafstone <= 0:
                invalidQty = True
            else:
                inventory.leafstone -= 1
        else:
            self.statuscode = 96
            self.message = 'Invalid item passed to evolveItem method (%s)' %item
            return 

        newPokemon = ''
        if item == 'water-stone' and pokemon.pokemonName in ['poliwhirl', 'shellder', 'staryu', 'eevee']:
            if pokemon.pokemonName == 'poliwhirl':
                newPokemon = 'poliwrath'
            elif pokemon.pokemonName == 'shellder':
                newPokemon = 'cloyster'
            elif pokemon.pokemonName == 'staryu':
                newPokemon = 'starmie'
            elif pokemon.pokemonName == 'eevee':
                newPokemon = 'vaporeon'
        elif item == 'fire-stone' and pokemon.pokemonName in ['vulpix', 'eevee', 'growlithe']:
            if pokemon.pokemonName == 'vulpix':
                newPokemon = 'ninetales'
            elif pokemon.pokemonName == 'eevee':
                newPokemon = 'flareon'
            elif pokemon.pokemonName == 'growlithe':
                newPokemon = 'arcanine'
        elif item == 'thunder-stone' and pokemon.pokemonName in ['pikachu', 'eevee']:
            if pokemon.pokemonName == 'pikachu':
                newPokemon = 'raichu'
            elif pokemon.pokemonName == 'eevee':
                newPokemon = 'jolteon'
        elif item == 'moon-stone' and pokemon.pokemonName in ['nidorina', 'nidorino', 'clefairy', 'jigglypuff']:
            if pokemon.pokemonName == 'nidorina':
                newPokemon = 'nidoqueen'
            elif pokemon.pokemonName == 'nidorino':
                newPokemon = 'nidoking'
            elif pokemon.pokemonName == 'clefairy':
                newPokemon = 'clefable'
            elif pokemon.pokemonName == 'jigglypuff':
                newPokemon = 'wifflytuff'
        elif item == 'leaf-stone' and pokemon.pokemonName in ['gloom', 'weepinbell', 'exeggcute']:
            if pokemon.pokemonName == 'gloom':
                newPokemon = 'vileplume'
            elif pokemon.pokemonName == 'weepinbell':
                newPokemon = 'victreebell'
            elif pokemon.pokemonName == 'exeggcute':
                newPokemon = 'exeggutor'
        else:
            self.statuscode = 420
            self.message = 'You cannot use %s on that pokemon' %item
            return

        # check if pokemon evolved
        if newPokemon != '' and not invalidQty:
            evolvedPokemon = pokeClass(newPokemon)
            evolvedPokemon.create(pokemon.currentLevel)
            evolvedPokemon.discordId = self.discordId
            pokemon.release()
            evolvedPokemon.save()
        
        self.message = "Someting's happening... Your pokemon evolved into %s!" %pokemon.pokemonName

        # save new inventory
        inventory.save()
        return 

    def getLocation(self):
        try:
            db = dbconn()
            queryStr = """
            SELECT "locationId"
                FROM trainer 
                WHERE "discord_id" = %(discordId)s
            """
            result = db.querySingle(queryStr, { 'discordId': self.discordId })
            if result:
                # TODO replace this load with object in memory
                p = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/locations.json')
                locationsConfig = json.load(open(p, 'r'))
                # locationsConfig = json.load(open('./configs/locations.json', 'r'))
                locResult = locationsConfig[str(result[0])]
                loc = LocationModel(locResult)
                return loc
            else:
                self.statuscode = 96
                self.message = 'Location not found'
        except:
            self.statuscode = 96
        finally:
            del db
    
    def setLocation(self, locationId):
        """ updates the trainer table to set the locationId """
        locObj = LocationClass(self.discordId)
        locObj.setLocation(locationId)
        if locObj.statuscode != 69:
            self.statuscode = locObj.statuscode
            self.message = locObj.message
    
    def getPokedex(self):
        """ returns a trainers pokedex """
        trainersPokedex = pokedex(self.discordId, None)
        return trainersPokedex.getPokedex()

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
        db = dbconn()
        
        try:
            db = dbconn()
            # Check if trainer exists and load startdate
            queryString = 'SELECT startdate FROM trainer WHERE "discord_id" = %(discordId)s'
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                self.startdate = result[0]
                self.trainerExists = True
                return
        
            # If trainer doesn't exist, create them
            db.executeWithoutCommit('INSERT INTO trainer (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.executeWithoutCommit('INSERT INTO inventory (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.executeWithoutCommit('INSERT INTO keyitems (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.executeWithoutCommit('INSERT INTO leaderboard (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.executeWithoutCommit('INSERT INTO "unique-encounters" (discord_id) VALUES(%(discordId)s) ON CONFLICT DO NOTHING;', { 'discordId': self.discordId })
            db.commit()
            
            # After creating trainer, load the startdate (which will be today's date for new trainers)
            queryString = 'SELECT startdate FROM trainer WHERE "discord_id" = %(discordId)s'
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                self.startdate = result[0]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            del db
    
    def __getEncounter(self, method):
        """ gets a random encounter in the current area using the selected method """
        from .encounterclass import encounter
        pokemon = None
        activePokemon = self.getActivePokemon()
        if activePokemon is None:
            self.statuscode = 420
            self.message = "You do not have an active pokemon!"
            return
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
            if method == 'gift' or method == 'only-one':
                pokemon.uniqueEncounter = True
            if method == 'gift':
                from .encounterclass import encounter
                activePokemon = self.getActivePokemon()  # Get the trainer's active pokemon
                enc = encounter(activePokemon, pokemon)  # Pass active pokemon as pokemon1, gift as pokemon2
                enc.updateUniqueEncounters()
            if pokemon.statuscode == 96:
                self.statuscode = 96
                self.message = "error occured during pokemon create()"
                return
        
        # leaderboard stats
        lb = leaderboard(self.discordId)
        lb.actions()
        return pokemon

    def __healPokemon(self, pokemon: pokeClass, item: str):
        """ heals a pokemons currentHP """
        # this function is only designed to work with healing items
        # update to remove status ailments later      
        statsDict = pokemon.getPokeStats()
        maxHP = statsDict['hp']
        currentHP = pokemon.currentHP
        newHP = currentHP
        if item == 'revive':
            if currentHP > 0:
                self.statuscode = 420
                self.message = "You cannot use revive on this pokemon"
                return
            else:
                newHP = round(maxHP/2)
        
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
        elif item == 'full-restore':
            newHP = maxHP
            # TODO update to remove status effects
        
        if newHP > maxHP:
            newHP = maxHP

        pokemon.currentHP = newHP
        pokemon.discordId = self.discordId
        pokemon.save()

        if pokemon.statuscode == 96:
            self.statuscode = 96
            self.message = "error occurred during pokemon.save()"
            return
        
        diff = newHP - currentHP
        self.statuscode = 420
        self.message = f'Your {pokemon.pokemonName.capitalize()} restored {diff} hp!'
