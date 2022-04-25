# pokemon experiance class
import pokebase as pb
import config

class experiance:
    def __init__(self, pokemon):
        self.pokemon = pokemon
    



    def expGain(self, baseExp, level):
        a = 1  # 1 if wild, 1.5 if owned by trainer
        b = baseExp  # base exp of fainted pokemon
        L = level  # level of fainted pokemon
        s = 1  # number of participating pokemon
        t = 1  # 1 if pokemon is current owner, 1.5 if pokemon was gained in a trade
        exp = (a*t*b*L) / (7 * s)
        return exp

    def getEffortValue(self, id_or_name):
        """ returns dictionary of effort values gained upon defeat """
        effortValueDict = {}
        pokemon = pb.pokemon(id_or_name)
        for stat in pokemon.stats:
            statName = stat.stat.name
            effortValue = stat.effort * config.overallExperienceModifier
            effortValueDict[statName] = effortValue

        return effortValueDict