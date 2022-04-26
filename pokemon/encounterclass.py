# encounter class

from dbclass import db as dbconn
from pokeclass import Pokemon as pokeClass
import config

# this class is to handle encounters with pokemon.

class encounter:
    def __init__(self, pokemon1, pokemon2):
        self.pokemon1 = pokemon1
        self.pokemon2 = pokemon2


    def fight(self):
        return

    def victory(self):
        return
    
    def defeat(self):
        return

    def runAway(self):
        return
    
    def catch(self, item):
        return


