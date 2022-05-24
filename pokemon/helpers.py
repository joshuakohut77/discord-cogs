from services.pokeclass import Pokemon as PokemonClass


def getTrainerGivenPokemonName(pokemon: PokemonClass):
    if pokemon.nickName:
        return pokemon.nickName
    return pokemon.pokemonName.capitalize()

