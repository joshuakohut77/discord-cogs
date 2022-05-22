

class PokemonState:
    discordId: str
    messageId: int
    pokemon: list
    active: int
    idx: int

    def __init__(self, discordId: str, messageId: int, pokemon: list, active: int, idx: int) -> None:
        self.discordId = discordId
        self.messageId = messageId
        self.pokemon = pokemon
        self.active = active
        self.idx = idx

