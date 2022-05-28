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



class PokedexMixin(MixinMeta):
    """Pokedex"""


    @commands.group(name="pokedex", aliases=['dex'])
    @commands.guild_only()
    async def __pokedex(self, ctx: commands.Context):
        """Base commmand to manage the pokedex"""
        pass


    @__pokedex.command()
    async def show(self, ctx: commands.Context, user: discord.Member) -> None:
        author = ctx.author

        if user is None:
            user = author

        def nextBtnClick():
            return lambda x: x.custom_id == "next" or x.custom_id == 'previous'

        trainer = TrainerClass(str(user.id))

        pokedex: List[PokedexModel] = trainer.getPokedex()

        pm = []

        for entry in pokedex:
            pm.append(f'{entry.pokemonId} {entry.pokemonName} - {entry.mostRecent}')


        # Create the embed object
        embed = discord.Embed(title=f"Pokédex")
        embed.set_thumbnail(url=f"https://pokesprites.joshkohut.com/sprites/pokedex.png")
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))

        trainerDex = "\r\n".join(pm) if len(pm) > 0 else 'No Pokémon encountered yet.'
        embed.add_field(name='Pokémon', value=trainerDex, inline=False)

        

        # interaction: Interaction = None
        # i = 0
        # while True:
        #     try:
        #         embed = discord.Embed(title=f"Index {i}")
        #         btns = []
        #         if i > 0:
        #             btns.append(Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'))
        #         if i < 5 - 1:
        #             btns.append(Button(style=ButtonStyle.gray, label="Next", custom_id='next'))

        #         if interaction is None:
        #             await ctx.send(
        #                 embed=embed,
        #                 components=[btns]
        #             )
        #             interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
        #         else:
        #             await interaction.edit_origin(
        #                 embed=embed,
        #                 components=[btns]
        #             )
        #             interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                
        #         if interaction.custom_id == 'next':
        #             i = i + 1
        #         if (interaction.custom_id == 'previous'):
        #             i = i - 1
        #     except asyncio.TimeoutError:
        #         break

