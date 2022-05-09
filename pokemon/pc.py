from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING
import asyncio

import discord
from discord import (Embed, Member)
from discord import message
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass


from .abcd import MixinMeta
from services.pokeclass import Pokemon as PokemonClass
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class StarterMixin(MixinMeta):
    """Starter"""

    # def __init__(self, bot: Red):
    #     self.client = DiscordComponents(bot)
    #     self.bot: Red = bot
    __trainers = {}

    # @commands.group(name="test")
    # @commands.guild_only()
    # async def _test(self, ctx: commands.Context) -> None:
    #     """Base command to manage the trainer (user).
    #     """
    #     pass
    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    # TODO: Apparently there is a limit of 5 buttons at a time
    @_trainer.command()
    async def pc(self, ctx: commands.Context, user: Union[discord.Member,discord.User] = None):
        author: Union[discord.Member,discord.User] = ctx.author

        if user is None:
            user = ctx.author

        def nextBtnClick():
            return lambda x: x.custom_id == "next" or x.custom_id == 'previous' or x.custom_id == 'stats' or x.custom_id == 'pokedex' or x.custom_id == 'active'

        trainer = TrainerClass(str(user.id))
        pokeList = trainer.getPokemon()

        # TODO: we should just get the ids since that's all we need
        active = trainer.getActivePokemon()
        # starter = trainer.getStarterPokemon()

        interaction: Interaction = None
        pokeLength = len(pokeList)
        i = 0

        if pokeLength == 0:
            await ctx.reply(content=f'{user.display_name} does not have any Pokemon.')
            return

        # TODO: there is a better way to do this that doesn't involve a loop
        #       discord-components gives an example use case
        #       https://github.com/kiki7000/discord.py-components/blob/master/examples/paginator.py
        while True:
            try:
                pokemon: PokemonClass = pokeList[i]
                embed = createPokemonAboutEmbed(user, pokemon)
                
                btns = []
                if i > 0:
                    btns.append(Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'))
                if i < pokeLength - 1:
                    btns.append(Button(style=ButtonStyle.gray, label="Next", custom_id='next'))

                btns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
                btns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))

                activeDisabled = (active is not None) and (pokemon.trainerId == active.trainerId)
                btns.append(Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=activeDisabled))
                
                # TODO: need to add the release button somewhere
                # # releaseDisabled = (active is not None and pokemon.id == active.id) or (starter is not None and pokemon.id == starter.id)
                # btns.append(Button(style=ButtonStyle.red, label="Release", custom_id='release'))

                if interaction is None:
                    await ctx.send(
                        embed=embed,
                        # file=file,
                        components=[btns, [Button(style=ButtonStyle.gray, label='Test', custom_id='test'),Button(style=ButtonStyle.gray, label='Test', custom_id='test2'),Button(style=ButtonStyle.gray, label='Test', custom_id='test3')]]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                else:
                    await interaction.edit_origin(
                        embed=embed,
                        # file=file,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                
                # Users who are not the author cannot click other users buttons
                if interaction.user.id != author.id:
                    await interaction.send('This is not for you.')
                    continue

                if interaction.custom_id == 'next':
                    i = i + 1
                if (interaction.custom_id == 'previous'):
                    i = i - 1
                if interaction.custom_id == 'active':
                    res = trainer.setActivePokemon(pokemon.trainerId)
                    await interaction.send(content=f'{res}')
                    break
                if interaction.custom_id == 'stats':
                    await interaction.send('Not implemented')
                    break
                if interaction.custom_id == 'pokedex':
                    await interaction.send('Not implemented')
                    break
            except asyncio.TimeoutError:
                break
