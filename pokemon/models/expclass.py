# pokemon experiance class
# this is designed to calculate the experience of the defeated pokemon
import config
import pokebase as pb

# Global Config Variables
OVERALL_EXPERIENCE_MODIFIER = config.overall_experience_modifier

class experiance:
    def __init__(self, pokemon):
        self.faulted = False
        self.pokemon = pokemon

    def getExpGained(self):
        """ calculates the exp gained from defeating the pokemon """
        # 1 if wild, 1.5 if owned by trainer
        if self.pokemon.wildPokemon:
            a = 1
        else:
            a = 1.5
        b = self.pokemon.base_exp  # base exp of fainted pokemon
        L = self.pokemon.currentLevel  # level of fainted pokemon
        s = 1  # number of participating pokemon
        t = 1  # 1 if pokemon is current owner, 1.5 if pokemon was gained in a trade
        exp = (a*t*b*L) / (7 * s)
        return round(exp)

    def getEffortValue(self):
        """ returns dictionary of effort values gained upon defeat """
        effortValueDict = {}
        pokemon = pb.pokemon(self.pokemon.id)
        for stat in pokemon.stats:
            statName = stat.stat.name
            effortValue = stat.effort * OVERALL_EXPERIENCE_MODIFIER
            effortValueDict[statName] = effortValue

        return effortValueDict

