# services/shinyclass.py
import sys
import json
import os
import random
from dbclass import db as dbconn
from loggerclass import logger as log

logger = log()

class ShinyChecker:
    """Handles shiny Pokemon logic and database checks"""
    
    def __init__(self):
        self.statuscode = 69
        self.message = ''
        self.__load_config()
    
    def __load_config(self):
        """Load shiny configuration"""
        configPath = '../configs/shiny.json'
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), configPath)
        with open(p, 'r') as f:
            config = json.load(f)
            self.wild_shiny_chance = config.get('wild_pokemon_shiny_chance', 200)
            self.legendary_shiny_chance = config.get('legendary_shiny_chance', 20)
            self.legendary_pokemon = config.get('legendary_pokemon', [])
    
    def is_shiny_owned(self, pokemon_name: str) -> bool:
        """
        Check if a shiny version of this Pokemon already exists and is not deleted.
        
        Args:
            pokemon_name: The name of the Pokemon to check
            
        Returns:
            True if a shiny exists and is not deleted, False otherwise
        """
        try:
            db = dbconn()
            queryString = '''
                SELECT COUNT(*) 
                FROM pokemon 
                WHERE "pokemonName" = %(pokemonName)s 
                AND is_shiny = TRUE 
                AND (is_deleted = FALSE OR is_deleted IS NULL)
            '''
            result = db.querySingle(queryString, {'pokemonName': pokemon_name})
            return result[0] > 0 if result else False
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
            return True  # Fail safe - if error, assume shiny exists to prevent duplicates
        finally:
            del db
    
    def roll_for_shiny(self, pokemon_name: str) -> bool:
        """
        Roll to determine if this encounter should be shiny.
        
        Args:
            pokemon_name: The name of the Pokemon being encountered
            
        Returns:
            True if the encounter should be shiny, False otherwise
        """
        # Check if shiny already owned
        if self.is_shiny_owned(pokemon_name):
            return False
        
        # Determine shiny chance based on Pokemon type
        if pokemon_name in self.legendary_pokemon:
            chance = self.legendary_shiny_chance
        else:
            chance = self.wild_shiny_chance
        
        # Roll for shiny (1 in chance)
        roll = random.randint(1, chance)
        return roll == 1
    
    def get_shiny_sprite_url(self, pokemon_id: int, is_back: bool = False) -> str:
        """
        Get the sprite URL for a shiny Pokemon.
        
        Args:
            pokemon_id: The Pokedex ID of the Pokemon
            is_back: If True, returns back sprite URL
            
        Returns:
            URL string for the shiny sprite
        """
        if is_back:
            return f"https://pokesprites.joshkohut.com/sprites/pokemon/shiny/back/{pokemon_id}.png"
        else:
            return f"https://pokesprites.joshkohut.com/sprites/pokemon/shiny/{pokemon_id}.png"