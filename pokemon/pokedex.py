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

    __pokedexState = {}


    @commands.group(name="pokedex", aliases=['dex'])
    @commands.guild_only()
    async def __pokedex(self, ctx: commands.Context):
        """Base commmand to manage the pokedex"""
        pass


    @__pokedex.command()
    async def show(self, ctx: commands.Context, user: discord.Member = None) -> None:
        author = ctx.author

        if user is None:
            user = author

        trainer = TrainerClass(str(user.id))

        pokedex: List[PokedexModel] = trainer.getPokedex()

        pokedex.sort(key=lambda x: x.pokemonId)

        dexList = []
        page = []
        for i in range(len(pokedex)):
            if (i % 15) == 0:
                page = []
                dexList.append(page)
            # emoji = ''
            # if entry.pokemonId == 69:
            #     emoji = '<:bellsprout2:979967988826521660>'
            entry = pokedex[i]
            page.append(f'`#{str(entry.pokemonId).ljust(4)}{str(entry.pokemonName.capitalize()).ljust(11)}{entry.mostRecent}`')
            # if entry.pokemonId == 69:
            #     break

        state = PokedexState(user.id, None, None, dexList, 0)

        embed, btns = self.__createDexEmbed(user, state)

        message = await ctx.send(embed=embed, components=btns)
        state.messageId = message.id
        state.channelId = message.channel.id
        self.__pokedexState[str(user.id)] = state


    def __createDexEmbed(self, user: discord.User, state: PokedexState):
        # Create the embed object
        embed = discord.Embed(title=f"Pokédex")
        embed.set_thumbnail(url=f"https://pokesprites.joshkohut.com/sprites/pokedex.png")
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))


        page = state.dexList[state.idx]

        trainerDex = "\r\n".join(page) if len(page) > 0 else 'No Pokémon encountered yet.'
        embed.add_field(name='Pokémon', value=f"{trainerDex}", inline=False)

        firstRowBtns = []

        if state.idx > 0:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray,
                       label='Previous', custom_id='previous'),
                self.__on_prev_click
            ))
        if state.idx < len(state.dexList) - 1:
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
                self.__on_next_click
            ))

        btns = []
        if len(firstRowBtns) > 0:
            btns.append(firstRowBtns)

        return embed, btns


    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPokedexState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state: PokedexState = self.__pokedexState[str(user.id)]
        state.idx = state.idx + 1

        embed, btns = self.__createDexEmbed(user, state)
        message = await interaction.edit_origin(embed=embed, components=btns)

        state.messageId = message.id
        self.__pokedexState[str(user.id)] = state


    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkPokedexState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state: PokedexState = self.__pokedexState[str(user.id)]
        state.idx = state.idx - 1

        embed, btns = self.__createDexEmbed(user, state)
        message = await interaction.edit_origin(embed=embed, components=btns)

        state.messageId = message.id
        self.__pokedexState[str(user.id)] = state


    def __checkPokedexState(self, user: discord.User, message: discord.Message):
        state: PokedexState
        if str(user.id) not in self.__pokedexState.keys():
            return False
        else:
            state = self.__pokedexState[str(user.id)]
            if state.messageId != message.id:
                return False
        return True
