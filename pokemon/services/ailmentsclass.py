# ailments class
import sys
from dbclass import db as dbconn
from loggerclass import logger as log
from datetime import datetime

# Class Logger
logger = log()

class inventory:
    def __init__(self, discordId):
        self.statuscode = 69
        self.message = ''

        self.pokemonId = None
        self.sleep = False
        self.poison = False
        self.burn = False
        self.freeze = False
        self.paralyze = False
        self.mostRecent = datetime.now()