from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
from discord_components import (DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from services.trainerclass import trainer as TrainerClass
from models.pokedex import PokedexModel

from .abcd import MixinMeta


class PokedexState:
    dexList: List[List[str]]
    idx: int

    discordId: int
    messageId: int
    channelId: int


    def __init__(self, discordId: int, messageId: int, channelId: int, dexList: List[List[str]], idx: int):
        self.discordId = discordId
        self.messageId = messageId
        self.channelId = channelId

        self.dexList = dexList
        self.idx = idx


class PokedexMixin(MixinMeta):
    """Pokedex"""


    @commands.group(name="pokedex", aliases=['dex'])
    @commands.guild_only()
    async def __pokedex(self, ctx: commands.Context):
        """Base commmand to manage the pokedex"""
        pass


#     @__pokedex.command()
#     async def show(self, ctx: commands.Context, user: discord.Member = None) -> None:
#         author = ctx.author

#         if user is None:
#             user = author

#         trainer = TrainerClass(str(user.id))

#         pokedex: List[PokedexModel] = trainer.getPokedex()

#         pokedex.sort(key=lambda x: x.pokemonId)

#         # TODO: paginate. single field values are limited to 1024 characters
#         # TODO: make sure things are getting added to the pokedex
#         pm = []
#         page = []
#         pm.append(page)
#         for i in len(pokedex):
#             if i % 15:
#                 page = []
#                 pm.append(page)
#             # emoji = ''
#             # if entry.pokemonId == 69:
#             #     emoji = '<:bellsprout2:979967988826521660>'
#             entry = pokedex[i]
#             page.append(f'`#{str(entry.pokemonId).ljust(4)}{str(entry.pokemonName.capitalize()).ljust(11)}{entry.mostRecent}`')
#             # if entry.pokemonId == 69:
#             #     break

#         await ctx.send(embed=embed)
# 1
#     def __createDexEmbed(self, user: discord.User):
#         # Create the embed object
#         embed = discord.Embed(title=f"Pokédex")
#         embed.set_thumbnail(url=f"https://pokesprites.joshkohut.com/sprites/pokedex.png")
#         embed.set_author(name=f"{user.display_name}",
#                         icon_url=str(user.avatar_url))

#         trainerDex = "\r\n".join(pm) if len(pm) > 0 else 'No Pokémon encountered yet.'
#         embed.add_field(name='Pokémon', value=f"{trainerDex}", inline=False)
