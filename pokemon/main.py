from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING
from abc import ABCMeta

import discord
# from discord_components import (DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)
from discord import ui, ButtonStyle, Button, Interaction

if TYPE_CHECKING:
    from redbot.core.bot import Red

# import emojis
from redbot.core import Config, commands
import asyncio

from .starter import StarterMixin
from .pokemart import PokemartMixin
# from .pokecenter import PokecenterMixin # DEPRECATED - functionality moved to EncountersMixin
# from .pc import PcMixin # DEPRECATED - functionality moved to EncountersMixin
# from .party import PartyMixin # DEPRECATED - functionality moved to EncountersMixin
# from .inventory import InventoryMixin # DEPRECATED - functionality moved to EncountersMixin
# from .map import MapMixin  # DEPRECATED - functionality moved to EncountersMixin
from .encounters import EncountersMixin
from .debug import DebugMixin
from .card import TrainerCardMixin
from .pokedex import PokedexMixin
from .trade import TradeMixin
from .leaderboard import LeaderboardMixin
from .admin import AdminMixin
from .finalemixin import FinaleMixin

# Things left to do
# one state mapping instead of multiple
# - [x][low] Clean up item names
# - [x][low] User nickname everywhere where pokemonname would be
# - [x][med] Update party and starter up to parity with pc
# - [x][med] Trading with other users
# - [x][low] call other release method
# - [x][low] fix fns where u pass in a user

# - [low] better use of logging channel
# - [med] db tightening
# - [low] Flesh out the *debug module to help us test the game

# - [x][low] Celadon City department store (special left/right handler)
# - [med] Trades need a little reworked
# - [x][med] Integrate Pokedex
# - [med] Integrate Trainer / Gym battles

# - [med] support evolution stones
# - [med] support x-accuracy items, etc

# - [low] dismiss/ephemeral messages
# - [med] Test evolutions in discord
# - [med] key item blockers

# things to test
# - What happens if you release all your pokemon?
# - What happens if you trade your active pokemon?
# - What happens if you trade your starter pokemon?

class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class Pokemon(FinaleMixin, StarterMixin, PokemartMixin, TradeMixin, AdminMixin, TrainerCardMixin, EncountersMixin, PokedexMixin, LeaderboardMixin, commands.Cog, DebugMixin, metaclass=CompositeClass):
    """Pokemon"""

    def __init__(self, bot: Red):
        super().__init__()
        # self.client = DiscordComponents(bot)
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=4206980085, force_registration=True)

        default_channel: Dict[str, Any] = {
            "enabled": True,
        }
        default_guild: Dict[str, Any] = {
            "enabled": True
        }
        self.config.register_channel(**default_channel)
        self.config.register_guild(**default_guild)

        self.pokelist = {}


    async def guild_only_check():
        async def pred(self, ctx: commands.Context):
            if ctx.guild is not None and await self.config.guild(ctx.guild).enabled():
                return True
            else:
                return False

        return commands.check(pred)



    @commands.group(name="trainer", aliases=['t'])
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass       

