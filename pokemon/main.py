from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING
from abc import ABCMeta

import discord
from discord import (Embed, Member)
from discord_components import (DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)


if TYPE_CHECKING:
    from redbot.core.bot import Red

# import emojis
from redbot.core import Config, commands
import asyncio

from .starter import StarterMixin
from .pokemart import PokemartMixin
from .pokecenter import PokecenterMixin
from .pc import PcMixin
from .party import PartyMixin
from .inventory import InventoryMixin
from .map import MapMixin
from .encounters import EncountersMixin
from .debug import DebugMixin
from .card import TrainerCardMixin

from services.trainerclass import trainer as TrainerClass


# Things left to do
# one state mapping instead of multiple
# pretty up location names
# pretty up item names
# - [low] Clean up item names
# - [low] User nickname everywhere where pokemonname would be
# - [low] update party and starter up to parity with pc
# - [med] Pokedex
# - [med] Test evolutions in discord
# - [med] key item blockers
# - [low] Flesh out the *debug module to help us test the game


class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class Pokemon(StarterMixin, PcMixin, PartyMixin, PokemartMixin, PokecenterMixin, InventoryMixin, MapMixin, TrainerCardMixin, EncountersMixin, commands.Cog, DebugMixin, metaclass=CompositeClass):
    """Pokemon"""

    def __init__(self, bot: Red):
        super().__init__()
        self.client = DiscordComponents(bot)
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


    #
    # Commands:
    #
    # [p]trainer pokedex <user> - user is optional
    # [p]trainer action - UI provides buttons to interact
    #
    # [p]pokemon stats <id> - unique id of pokemon in db (stats + moves)
    # [p]pokemon wiki <id> - any pokemon general wiki


    @commands.group(name="trainer", aliases=['t'])
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass       


    @_trainer.command()
    async def pokedex(self, ctx: commands.Context, user: discord.Member = None):
        if user is None:
            user = ctx.author

        def nextBtnClick():
            return lambda x: x.custom_id == "next" or x.custom_id == 'previous'

        trainer = TrainerClass('456')

        pokedex = trainer.getPokedex()

        interaction: Interaction = None
        i = 0
        while True:
            try:
                embed = discord.Embed(title=f"Index {i}")
                btns = []
                if i > 0:
                    btns.append(Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'))
                if i < 5 - 1:
                    btns.append(Button(style=ButtonStyle.gray, label="Next", custom_id='next'))

                if interaction is None:
                    await ctx.send(
                        embed=embed,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                    # message = interaction.message
                else:
                    await interaction.edit_origin(
                        embed=embed,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                    # message = interaction.message
                
                if interaction.custom_id == 'next':
                    i = i + 1
                if (interaction.custom_id == 'previous'):
                    i = i - 1
            except asyncio.TimeoutError:
                break

        # first = pokedex[0]
        # pokemon = trainer.getPokemon(first['id'])

        # # Create the embed object
        # embed = discord.Embed(title=f"Pokedex")
        # embed.set_thumbnail(url=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png")
        # embed.set_author(name=f"{user.display_name}",
        #                  icon_url=str(user.avatar_url))
        # embed.add_field(name=f"No.", value=f"{pokemon.id}", inline=False)
        # embed.add_field(name=f"Pokemon", value=f"{pokemon.name}", inline=False)
        # embed.add_field(name=f"Last seen", value=f"{first['lastSeen']}", inline=False)
        # embed.set_thumbnail(url=f"{pokemon.spriteURL}")


        # btn = Button(style=ButtonStyle.gray,
        #              label="Next", custom_id='next')


        # await ctx.send(
        #     embed=embed,
        #     components=[[
        #         btn
        #         # self.bot.components_manager.add_callback(b, callback)
        #     ]]
        # )
        
        # interaction = await self.bot.wait_for("button_click", check=nextBtnClick())
        # await ctx.send(embed=embed)
