# ailments class
import sys
import random
from dbclass import db as dbconn
from loggerclass import logger as log
from datetime import datetime

# Class Logger
logger = log()

class ailment:
    def __init__(self, pokemonId):
        self.statuscode = 69
        self.message = ''

        self.pokemonId = pokemonId
        self.sleep = False
        self.poison = False
        self.burn = False
        self.freeze = False
        self.paralysis = False
        self.trap = False
        self.confusion = False
        self.disable = False
        self.turnCounter = 0
        self.mostRecent = datetime.now()
        self.recordExists = False
    

    def load(self):
        """ returns populated ailment object"""
        try:
            db = dbconn()
            queryString = '''SELECT "mostRecent", sleep, 
                            poison, burn, "freeze", paralysis,
                            "trap", "confusion", "disable"
	                        FROM ailments WHERE "pokemonId"=%(pokemonId)s'''
            result = db.querySingle(queryString, { 'pokemonId': self.pokemonId })
            if result is not None:
                if len(result) > 0:
                    self.mostRecent = result[0]
                    self.sleep = result[1]
                    self.poison = result[2]
                    self.burn = result[3]
                    self.freeze = result[4]
                    self.paralysis = result[5]
                    self.trap = result[6]
                    self.confusion = result[7]
                    self.disable = result[8]
                    self.recordExists = True
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return
        
    def save(self):
        """ saves an ailment object to the database"""
        if self.pokemonId is None:
            self.statuscode = 96
            self.message = "pokemonId has a Null value"
            return
        try:
            # check if a recordExists meaning it has a database entry already
            db = dbconn()
            query = None
            if self.recordExists:
                # updateQuery or deleteQuery depending on the object status
                if not self.sleep and not self.poison \
                    and not self.burn and not self.freeze and not self.paralysis \
                    and not self.trap and not self.confusion and not self.disable:
                    # delete row from database
                    query = 'DELETE FROM ailments WHERE "pokemonId"=%(pokemonId)s'
                    values =  { "pokemonId": self.pokemonId }
                else:
                    # update row in database
                    query = '''UPDATE ailments SET "mostRecent"=%(mostRecent)s, 
                                sleep=%(sleep)s, poison=%(poison)s, 
                                burn=%(burn)s, "freeze"=%(freeze)s, paralysis=%(paralysis)s,
                                "trap"=%(trap)s, "confusion"=%(confusion)s, "disable"=%(disable)s 
                                WHERE "pokemonId"=%(pokemonId)s'''
                    values = { "mostRecent":self.mostRecent, "sleep":self.sleep, "poison":self.poison, 
                                "burn":self.burn, "freeze":self.freeze, "paralysis":self.paralysis, 
                                "trap":self.trap, "confusion":self.confusion, "disable":self.disable, 
                                "pokemonId":self.pokemonId}
            else:
                query = '''INSERT INTO ailments ("mostRecent", sleep, poison, 
                            burn, "freeze", paralysis, "trap", "confusion", "disable")
                            VALUES(%(mostRecent)s, %(sleep)s, %(poison)s, 
                            %(burn)s, %(freeze)s, %(paralysis)s,
                            %(trap)s, %(confusion)s, %(disable)s)'''
                            
                values = { "mostRecent":self.mostRecent, "sleep":self.sleep, "poison":self.poison, 
                            "burn":self.burn, "freeze":self.freeze, "paralysis":self.paralysis, 
                            "trap":self.trap, "confusion":self.confusion, "disable":self.disable, 
                            "pokemonId":self.pokemonId}
            db.execute(query, values)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db


    def rollAilmentChance(self, move):
        """ checks the ailment chance and rolls to determine if effected """
        chance = move['ailment_chance']
        print(move)
        if chance == 0:
            return False
        
        randomChance = random.randrange(1, 100+1)
        print('rolling ailment chance')
        if randomChance > 100 - chance:
            return True
        else:
            return False
        
    def setAilment(self, ailment):
        print('Setting Ailment %s' %ailment)
        """ sets a pokemons ailment """
        if ailment == 'sleep':
            self.resetAilments()
            self.sleep = True
        elif ailment == 'poison':
            self.resetAilments()
            self.poison = True
        elif ailment == 'burn':
            self.resetAilments()
            self.burn = True
        elif ailment == 'freeze':
            self.resetAilments()
            self.freeze = True
        elif ailment == 'paralysis':
            self.resetAilments()
            self.paralysis = True
        elif ailment == 'trap':
            self.resetAilments()
            self.trap = True
        elif ailment == 'confusion':
            self.resetAilments()
            self.confusion = True
        elif ailment == 'disable':
            self.resetAilments()
            self.disable = True
        self.mostRecent = datetime.now()
    
    def resetAilments(self):
        """ sets all ailment status to False """
        self.sleep = False
        self.poison = False
        self.burn = False
        self.freeze = False
        self.paralysis = False
        self.trap = False
        self.confusion = False
        self.disable = False

    def calculateAilmentDamage(self, pokemon):
        """ calculates ailment damage for pokemon and sets pokemons HP """
        # This method returns two values, second the pokemon object and a boolean if they can do their move or not because of the ailment
        # eg: if the pokemon is asleep, they cannot use a move and therefore will return False as a second return value
        if self.sleep:
            if self.turnCounter >= 7 or random.randrange(1, 7+1) == 1:
                self.sleep = False
                self.turnCounter = 0
                return pokemon, False
            else:
                self.turnCounter = self.turnCounter + 1
                return pokemon, True
        elif self.poison:
            statsDict = pokemon.getPokeStats()
            pokemon.currentHP = round(pokemon.currentHP - statsDict['hp']*(1/16))
            return pokemon, False
        elif self.burn:
            statsDict = pokemon.getPokeStats()
            pokemon.currentHP = round(pokemon.currentHP - statsDict['hp']*(1/16))
            return pokemon, False
        elif self.freeze: # TODO update this to make things able to Thaw from fire attacks
            return pokemon, True
        elif self.paralysis:
            if random.randrange(1, 4+1) == 1:
                print('%s is no longer paralyzed and cannot attack' % str(pokemon.pokemonName))
                return pokemon, True
            else:
                return pokemon, False
        elif self.trap: # damage calculated from move
            if self.turnCounter >= 5:
                self.trap = False
                self.turnCounter = 0
                print('%s is no longer trapped' % str(pokemon.pokemonName))
                return pokemon, False
            elif self.turnCounter >= 0 and self.turnCounter <= 2:
                self.turnCounter = self.turnCounter + 1
                return pokemon, True
            elif self.turnCounter > 2:
                if random.randrange(1, 3+1) == 1:
                    self.trap = False
                    self.turnCounter = 0
                    print('%s is no longer trapped' % str(pokemon.pokemonName))
                    return pokemon, False
                else:
                    self.turnCounter = self.turnCounter + 1
                    return pokemon, True
            else:
                self.turnCounter = self.turnCounter + 1
                return pokemon, True
        elif self.confusion: # damage calculated from normal power 40 damage attack (typeless)
            if self.turnCounter >= 5:
                self.turnCounter = 0
                self.confusion = False
                return pokemon, False
            elif self.turnCounter >= 0 and self.turnCounter <= 2:
                self.turnCounter = self.turnCounter + 1
                return pokemon, True
            elif self.turnCounter > 2:
                if random.randrange(1, 3+1) == 1:
                    self.confusion = False
                    self.confusion = False
                    self.turnCounter = 0
                    return pokemon, False
                else:
                    self.turnCounter = self.turnCounter + 1
                    return pokemon, True
        else:
            return pokemon, False


    """
    Sleep (SLP) - unable to use moves. Lasts 1 to 7 turns randomly. 
    Poison (PSN) - Inflicts 1/16 of max HP every turn. Damage is dealt after the move is complete but negated if enemy faints. Pokemon will lose 1HP for every 4 steps taken outside of battle
    Burn (BRN) - Inflicts 1/16 of max HP every turn and halves damage dealt by a Pokemon's physical moves. Damage is dealt after the move is complete but negated if enemy faints
    Freeze (FRZ) - Pokemon is unable to move. Pokemon is thawed if hit by fire-type move. Pokemon will never natrually thaw in Gen1
    Paralysis (PAR) - Reduces the Speed stat and causes it to have a 25% chance it's unable to use a move.     
    Trap - Bind/Bound this lasts 2-5 turns. 37.5% will last 2 turns, 37.5% change will last 3 turns 12.5% chance will last 4 turns. 12.5% chance will last 5 turns (calculate damage from move)
    Confusion - 50% chance to hurt itself. Damage determined as if attacked by a 40-power typeless physical attack (without possibility of critical hit) Lasts 2-5 turns
    """

