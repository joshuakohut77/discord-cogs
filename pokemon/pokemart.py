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


    @commands.group(name="pokemart", aliases=['mart'])
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
        # file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/items/poke-ball.png", filename="poke-ball.png")
        embed = discord.Embed(title=f"Pokemart - {location.name}")
        embed.set_thumbnail(url=f"https://pokesprites.joshkohut.com/sprites/locations/poke_mart.png")
        # embed.set_author(name=f"{user.display_name}",
        #                  icon_url=str(user.avatar_url))

        for item in store.storeList:
            emoji = '▶️'
            description = ''

            if item['item'] == 'poke-ball':
                emoji = constant.POKEBALL
                description = "A device for catching wild Pokémon. It's thrown like a ball, comfortably encapsulating its target."
            elif item['item'] == 'great-ball':
                emoji = constant.GREATBALL
                description = "A high-performance Ball with a higher catch rate than a standard Poké Ball."
            elif item['item'] == 'ultra-ball':
                emoji = constant.ULTRABALL
                description = "An ultra-performance Ball with a higher catch rate than a Great Ball."
            elif item['item'] == 'master-ball':
                emoji = constant.MASTERBALL
                description = "The best Poké Ball with the ultimate level of performance. With it, you will catch any wild Pokémon without fail."
            elif item['item'] == 'potion':
                emoji = constant.POTION
                description = "Restores HP that have been lost in battle by 20 HP."
            elif item['item'] == 'super-potion':
                emoji = constant.SUPERPOTION
                description = "Restores HP that have been lost in battle by 50 HP."
            elif item['item'] == 'hyper-potion':
                emoji = constant.HYPERPOTION
                description = "Restores HP that have been lost in battle by 200 HP."
            elif item['item'] == 'max-potion':
                emoji = constant.MAXPOTION
                description = "Fully restores HP that have been lost in battle."
            elif item['item'] == 'revive':
                emoji = constant.REVIVE
                description = "Revives a fainted Pokémon and restores half its maximum HP."
            elif item['item'] == 'full-restore':
                emoji = constant.FULLRESTORE
                description = "Fully restores HP and cures all ailments, such as poisoning."
            elif item['item'] == 'repel':
                emoji = constant.REPEL
                description = "An aerosol spray that keeps wild Pokémon away."
            elif item['item'] == 'super-repel':
                emoji = constant.SUPERREPEL
                description = "Keeps wild Pokémon away. Longer lasting than Repel."
            elif item['item'] == 'max-repel':
                emoji = constant.MAXREPEL
                description = "Keeps wild Pokémon away. Longer lasting than Super Repel."
            elif item['item'] == 'escape-rope':
                emoji = constant.ESCAPEROPE
                description = "When in a place like a cave, this returns you to the last Pokémon Center visited."
            elif item['item'] == 'awakening':
                emoji = constant.AWAKENING
                description = "Awakens a Pokémon that has fallen asleep."
            elif item['item'] == 'antidote':
                emoji = constant.ANTIDOTE
                description = "An antidote for curing a poisoned Pokémon."
            elif item['item'] == 'ice-heal':
                emoji = constant.ICEHEAL
                description = "Thaws out a Pokémon that has been frozen solid."
            elif item['item'] == 'burn-heal':
                emoji = constant.BURNHEAL
                description = "Medicine for curing a Pokémon that is suffering from burn."
            elif item['item'] == 'paralyze-heal':
                emoji = constant.PARALYZEHEAL
                description = "Cures a Pokémon that is suffering from paralysis."
            elif item['item'] == 'full-heal':
                emoji = constant.FULLHEAL
                description = "Cures a Pokémon of any ailment except for fainting."
            
            embed.add_field(name=f"{emoji}  {item['item']} — {item['price']}", value=description, inline=False)

        await ctx.send(embed=embed)
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


    async def sell(self, ctx: commands.Context, item: str, count: int = 1) -> Non:
        user = ctx.author

        trainer = TrainerClass(user.id)
        location = trainer.getLocation()
        store = StoreClass(trainer.discordId, location.locationId)

        if store.statuscode == 420:
            await ctx.send(store.message)
            return

        store.sellItem(item, count)

        await ctx.send(store.message)

