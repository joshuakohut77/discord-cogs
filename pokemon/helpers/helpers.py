from services.pokeclass import Pokemon as PokemonClass


def getTrainerGivenPokemonName(pokemon: PokemonClass):
    if pokemon.nickName:
        return pokemon.nickName
    return pokemon.pokemonName.capitalize()


def check_hm_usable(discord_id: str, hm_name: str) -> tuple[bool, list[str]]:
    """
    Check if trainer has a Pokemon in their party that can use the specified HM.
    
    Args:
        discord_id: Discord user ID
        hm_name: HM identifier (e.g., 'HM01', 'HM02')
    
    Returns:
        tuple: (can_use: bool, compatible_pokemon_names: list[str])
    """
    from helpers.pathhelpers import load_json_config
    from services.trainerclass import trainer as TrainerClass
    
    # Load HMs config
    hms_config = load_json_config('HMs.json')
    
    # Get list of Pokemon that can learn this HM
    hm_compatible_pokemon = hms_config.get(hm_name, [])
    if not hm_compatible_pokemon:
        return False, []
    
    # Get compatible Pokemon IDs and names (lowercase for matching)
    compatible_ids = {poke['ID'] for poke in hm_compatible_pokemon}
    compatible_names = {poke['Name'].lower() for poke in hm_compatible_pokemon}
    
    # Get trainer's party
    trainer = TrainerClass(discord_id)
    party = trainer.getPokemon(party=True)
    
    # Check if any party Pokemon can use this HM
    usable_pokemon = []
    for pokemon in party:
        pokemon.load(pokemonId=pokemon.trainerId)
        # Check by both ID and name (lowercase)
        if pokemon.pokedexId in compatible_ids or pokemon.pokemonName.lower() in compatible_names:
            usable_pokemon.append(pokemon.pokemonName.capitalize())
    
    return len(usable_pokemon) > 0, usable_pokemon