
from typing import Any, Dict, List, Union, TYPE_CHECKING
from services.pokeclass2 import Pokemon as PokemonClass

class PokemonState:
    discordId: str
    messageId: int
    pokemon: List[PokemonClass]
    active: int
    idx: int

    def __init__(self, discordId: str, messageId: int, pokemon: List[PokemonClass], active: int, idx: int) -> None:
        self.discordId = discordId
        self.messageId = messageId
        self.pokemon = pokemon
        self.active = active
        self.idx = idx

