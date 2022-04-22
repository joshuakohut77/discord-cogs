import pokebase as pb

def getPokemonLevelMoves(id_or_name):
    """ returns a dictionary of {move: level} for a pokemons base move set"""
    moveDict = {}
    if id_or_name is not None:
        pokemon = pb.pokemon(id_or_name)
        for move in pokemon.moves:
            for version in move.version_group_details:
                    if version.version_group.name != 'red-blue':
                        continue
                    elif version.move_learn_method.name != 'level-up':
                        continue
                    else:
                        moveName = move.move.name
                        moveLevel = version.level_learned_at
                        moveDict[moveName] = moveLevel
    return moveDict

def getPokemonSpriteUrl(id_or_name, sprite_type='pokemon'):
    """ returns a pokemons base sprite url.png """
    if id_or_name is not None:
        if type(id_or_name) == int:
            pokemonId = id_or_name
        else:
            try:
                pokemon = pb.pokemon(id_or_name)
                pokemonId = pokemon.id
            except:
                return None
        return pb.SpriteResource(sprite_type, pokemonId).url

def getPokemonType(id_or_name):
    """ returns string of pokemons base type """
    if id_or_name is not None:
        pokemon = pb.pokemon(id_or_name)
        return pokemon.types[0].type.name

def getPokemonBaseStats(id_or_name):
    """ returns dictionary of {stat: value} for a pokemons base stats """
    baseStatDict = {}
    if id_or_name is not None:
        pokemon = pb.pokemon(id_or_name)
        for stat in pokemon.stats:
            statName = stat.stat.name
            statVal = stat.base_stat
            baseStatDict[statName] = statVal
    return baseStatDict



