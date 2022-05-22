from __future__ import annotations
from typing import TYPE_CHECKING

from redbot.core.commands.commands import command

if TYPE_CHECKING:
    from redbot.core import Config
    from redbot.core.bot import Red

from redbot.core import commands

from abc import ABC, abstractmethod

import discord
from discord_components.client import DiscordComponents
from models.state import PokemonState


class MixinMeta(ABC):

    __pokemonState: dict[str, PokemonState] = {}

    def __init__(self, *args):
        self.bot: Red
        self.config: Config
        self.client: DiscordComponents


    def setPokemonState(self, user: discord.User, state: PokemonState):
        self.__pokemonState[str(user.id)] = state

    def getPokemonState(self, user: discord.User):
        state = self.__pokemonState[str(user.id)]
        return state

    def checkPokemonState(self, user: discord.User, message: discord.Message):
        state: PokemonState
        if str(user.id) not in self.__pokemonState.keys():
            return False
        else:
            state = self.__pokemonState[str(user.id)]
            if state.messageId != message.id:
                return False
        return True

    # @abstractmethod
    # @commands.group(name="trainer")
    # @commands.guild_only()
    # async def _trainer(self, ctx: commands.Context):
    #     raise NotImplementedError
