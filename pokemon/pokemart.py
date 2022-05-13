from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
from discord import (Embed, Member)
from discord import message
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from services.storeclass import store as StoreClass


from .abcd import MixinMeta
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)
import constant


class PokemartMixin(MixinMeta):
    """Pokemart"""

    # __trainers = {}


    @commands.group(name="pokemart")
    @commands.guild_only()
    async def _pokemart(self, ctx: commands.Context) -> None:
        """Base command to manage the pokemart (store)
        """
        pass

    @_pokemart.command()
    async def shop(self, ctx: commands.Context, user: discord.Member = None) -> None:
        
        if user is None:
            user = ctx.author
        
        trainer = TrainerClass(user.id)
        location = trainer.getLocation()
        store = StoreClass(str(user.id), location.locationId)

        if store.statuscode == 420:
            await ctx.send(store.message)
            return

        # Create the embed object
        file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/items/poke-ball.png", filename="poke-ball.png")
        embed = discord.Embed(title=f"Pokemart - {location.name}")
        embed.set_thumbnail(url=f"attachment://poke-ball.png")
        # embed.set_author(name=f"{user.display_name}",
        #                  icon_url=str(user.avatar_url))

        # poke-ball,200,
        # great-ball,600,
        # ultra-ball,1200
        # potion,300
        # super-potion,700
        # hyper-potion,1500
        # max-potion,2500

        # antidote,100
        # awakening,200
        # burn-heal,250
        # paralyze-heal,200
        # ice-heal,250
        # full-heal,600

        # escape-rope,550
        # repel,350
        # revive,1500
        # super-repel,500
        # max-repel,700
        # full-restore,3000

        for item in store.storeList:
            emoji = '▶️'
            description = 'description here'

            if item['item'] == 'poke-ball':
                emoji = constant.POKEBALL
            elif item['item'] == 'great-ball':
                emoji = constant.GREATBALL
            elif item['item'] == 'ultra-ball':
                emoji = constant.ULTRABALL
            elif item['item'] == 'master-ball':
                emoji = constant.MASTERBALL
            elif item['item'] == 'potion':
                emoji = constant.POTION
            elif item['item'] == 'superpotion':
                emoji = constant.SUPERPOTION
            elif item['item'] == 'hyperpotion':
                emoji = constant.HYPERPOTION
            elif item['item'] == 'maxpotion':
                emoji = constant.MAXPOTION
            elif item['item'] == 'revive':
                emoji = constant.REVIVE
            elif item['item'] == 'full-restore':
                emoji = constant.FULLRESTORE
            elif item['item'] == 'repel':
                emoji = constant.REPEL
            elif item['item'] == 'max-repel':
                emoji = constant.MAXREPEL
            elif item['item'] == 'escape-rope':
                emoji = constant.ESCAPEROPE
            elif item['item'] == 'awakening':
                emoji = constant.AWAKENING
            elif item['item'] == 'antidote':
                emoji = constant.ANTIDOTE
            elif item['item'] == 'antidote':
                emoji = constant.ANTIDOTE
            elif item['item'] == 'iceheal':
                emoji = constant.ICEHEAL
            elif item['item'] == 'burnheal':
                emoji = constant.BURNHEAL
            elif item['item'] == 'paralyze-heal':
                emoji = constant.PARALYZEHEAL
            elif item['item'] == 'full-heal':
                emoji = constant.FULLHEAL
            
            embed.add_field(name=f"{emoji}  {item['item']} — {item['price']}", value=description, inline=False)

        await ctx.send(file=file, embed=embed)
        await ctx.tick()

    @_pokemart.command()
    async def buy(self, ctx: commands.Context, item: str, count: int = 1) -> None:
        """List the pokemart items available to you
        """
        user = ctx.author

        trainer = TrainerClass(user.id)
        location = trainer.getLocation()
        store = StoreClass(str(user.id), location.locationId)

        if store.statuscode == 420:
            await ctx.send(store.message)
            return

        store.buyItem(item, count)

        if store.statuscode == 69 or store.statuscode == 420:
            await ctx.send(store.message)

        # await ctx.send(res)
        # await ctx.send(f'{user.display_name} bought {count} {item}')
