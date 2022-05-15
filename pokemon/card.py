from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord import (Embed, Member)
from discord import message
from discord.abc import User
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass

from .abcd import MixinMeta
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class TrainerCardState:
    discordId: str
    pokemonId: int
    messageId: int

    def __init__(self, discordId: str, pokemonId: int, messageId: int) -> None:
        self.discordId = discordId
        self.pokemonId = pokemonId
        self.messageId = messageId


class TrainerCardMixin(MixinMeta):
    """Trainer Card"""

    __cards: dict[str, TrainerCardState] = {}


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    @_trainer.command()
    async def card(self, ctx: commands.Context, user: discord.Member = None) -> None:
        if user is None:
            user = ctx.author

        #  # This will create the trainer if it doesn't exist
        # trainer = TrainerClass(str(user.id))
        # pokemon = trainer.getActivePokemon()

        # btns = []
        # btns.append(self.client.add_callback(
        #     Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
        #     self.on_stats_click,
        # ))
        # btns.append(Button(style=ButtonStyle.green,
        #             label="Pokedex", custom_id='pokedex'))
        # Create the embed object
        embed = discord.Embed(title=f"{user.display_name}",)
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.avatar_url))
        
        # embed.set_thumbnail(url=pokemon.frontSpriteURL)
            # message = await ctx.send(embed=embed, components=[btns])       
        # self.__trainers[str(user.id)] = TrainerState(str(user.id), pokemon.trainerId, message.id)


    async def on_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkTrainerState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        await interaction.send('Not implemented yet')


    def __checkTrainerState(self, user: discord.User, message: discord.Message):
        state: TrainerCardState
        if str(user.id) not in self.__cards.keys():
            return False
        else:
            state = self.__cards[str(user.id)]
            if state.messageId != message.id:
                return False
        return True