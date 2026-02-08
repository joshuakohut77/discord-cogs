"""
Session state models for UI interactions.

These classes track the state of various UI sessions including
wild encounters, bag navigation, item usage, and PokeMart interactions.
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .location import LocationModel
    from ..services.pokeclass import Pokemon as PokemonClass
else:
    # Runtime imports to avoid circular dependencies
    LocationModel = 'LocationModel'
    PokemonClass = 'PokemonClass'


class ActionState:
    """Track wild encounter action state"""

    discordId: str
    location: 'LocationModel'
    channelId: int
    messageId: int
    activePokemon: 'PokemonClass'
    wildPokemon: 'PokemonClass'
    descLog: str

    def __init__(self, discordId: str, channelId: int, messageId: int,
                 location: 'LocationModel', activePokemon: 'PokemonClass',
                 wildPokemon: 'PokemonClass', descLog: str) -> None:
        self.discordId = discordId
        self.location = location
        self.channelId = channelId
        self.messageId = messageId
        self.activePokemon = activePokemon
        self.wildPokemon = wildPokemon
        self.descLog = descLog


class BagState:
    """State for bag menu navigation"""

    discord_id: str
    message_id: int
    channel_id: int
    current_view: str  # 'items', 'keyitems', 'hms', 'party', 'pc', 'pokedex'
    pokedex_index: int  # For paginating through pokedex
    selected_pokemon_id: Optional[str]  # For party view
    pc_selected_pokemon_id: Optional[str]  # For PC view

    def __init__(self, discord_id: str, message_id: int, channel_id: int,
                 current_view: str = 'items'):
        self.discord_id = discord_id
        self.message_id = message_id
        self.channel_id = channel_id
        self.current_view = current_view
        self.pokedex_index = 0
        self.selected_pokemon_id = None
        self.pc_selected_pokemon_id = None


class ItemUsageState:
    """State for item usage flow"""

    discord_id: str
    selected_pokemon_id: Optional[str]
    selected_item: Optional[str]

    def __init__(self, discord_id: str, selected_pokemon_id: str = None,
                 selected_item: str = None):
        self.discord_id = discord_id
        self.selected_pokemon_id = selected_pokemon_id
        self.selected_item = selected_item


class MartState:
    """Track Mart UI state"""

    user_id: str
    message_id: int
    channel_id: int
    location: 'LocationModel'
    store: any  # StoreClass instance
    mode: str  # 'main', 'buy', 'sell'
    selected_item: Optional[str]
    quantity: int

    def __init__(self, user_id: str, message_id: int, channel_id: int,
                 location, store, mode: str = 'main'):
        self.user_id = user_id
        self.message_id = message_id
        self.channel_id = channel_id
        self.location = location
        self.store = store  # StoreClass instance
        self.mode = mode  # 'main', 'buy', 'sell'
        self.selected_item = None
        self.quantity = 1  # Default quantity for purchases


class FlightState:
    """State for flight interface"""
    discordId: str
    current_location_name: str
    selected_destination: str | None
    
    def __init__(self, discordId: str, current_location_name: str):
        self.discordId = discordId
        self.current_location_name = current_location_name
        self.selected_destination = None