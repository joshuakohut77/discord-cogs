from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
# from discord_components import (DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

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
            
            entry = pokedex[i]
            page.append(f'`#{str(entry.pokemonId).ljust(4)}{str(entry.pokemonName.capitalize()).ljust(11)}{entry.mostRecent}`')

        state = PokedexState(user.id, None, None, dexList, 0)

        embed, btns = self.__createDexEmbed(user, state)

        message = await ctx.send(embed=embed, view=btns)
        state.messageId = message.id
        state.channelId = message.channel.id
        self.__pokedexState[str(user.id)] = state


    def __createDexEmbed(self, user: discord.User, state: PokedexState):
        # Create the embed object
        embed = discord.Embed(title=f"Pokédex")
        embed.set_thumbnail(url=f"https://pokesprites.joshkohut.com/sprites/pokedex.png")
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.display_avatar.url))


        page = state.dexList[state.idx]

        trainerDex = "\r\n".join(page) if len(page) > 0 else 'No Pokémon encountered yet.'
        embed.add_field(name='Pokémon', value=f"{trainerDex}", inline=False)

        view = View()

        if state.idx > 0:
            button = Button(style=ButtonStyle.gray, label='Previous', custom_id='previous')
            button.callback = self.on_prev_click_pokedex
            view.add_item(button)

        if state.idx < len(state.dexList) - 1:
            button = Button(style=ButtonStyle.gray, label="Next", custom_id='next')
            button.callback = self.on_next_click_pokedex
            view.add_item(button)

        return embed, view


    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()

        if not self.__checkPokedexState(user, interaction.message):
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return

        state: PokedexState = self.__pokedexState[str(user.id)]
        state.idx = state.idx + 1

        embed, btns = self.__createDexEmbed(user, state)
        message = await interaction.message.edit(embed=embed, view=btns)

        state.messageId = message.id
        self.__pokedexState[str(user.id)] = state


    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()

        if not self.__checkPokedexState(user, interaction.message):
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return

        state: PokedexState = self.__pokedexState[str(user.id)]
        state.idx = state.idx - 1

        embed, btns = self.__createDexEmbed(user, state)
        message = await interaction.message.edit(embed=embed, view=btns)

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

    @discord.ui.button(custom_id='next', label='Next', style=ButtonStyle.gray)
    async def on_next_click_pokedex(self, interaction: discord.Interaction):
        await self.__on_next_click(interaction)

    @discord.ui.button(custom_id='previous', label='Previous', style=ButtonStyle.gray)
    async def on_prev_click_pokedex(self, interaction: discord.Interaction):
        await self.__on_prev_click(interaction)
