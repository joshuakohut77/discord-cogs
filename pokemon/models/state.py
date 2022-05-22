
from typing import List
from services.pokeclass import Pokemon as PokemonClass

from enum import Enum


class DisplayCard(Enum):
    STATS = 1
    MOVES = 2
    DEX = 3


class PokemonState:
    discordId: str
    messageId: int
    card: DisplayCard
    pokemon: List[PokemonClass]
    active: int
    idx: int

    def __init__(self, discordId: str, messageId: int, card: DisplayCard, pokemon: List[PokemonClass], active: int, idx: int) -> None:
        self.discordId = discordId
        self.messageId = messageId
        self.card = card
        self.pokemon = pokemon
        self.active = active
        self.idx = idx

