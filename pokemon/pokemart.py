from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
from discord_components import (ButtonStyle, Button, Interaction)
from models.location import LocationModel

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from services.trainerclass import trainer as TrainerClass
from services.storeclass import StoreItem, store as StoreClass

from .abcd import MixinMeta


itemDisplayNames = {
    "poke-ball": {
        'name': 'Poké Ball',
        'desc': 'A device for catching wild Pokémon. It\'s thrown like a ball, comfortably encapsulating its target.',
        'emoji': constant.POKEBALL
    },
    "great-ball": {
        'name': 'Great Ball',
        'desc': 'A high-performance Ball with a higher catch rate than a standard Poké Ball.',
        'emoji': constant.GREATBALL
    },
    "ultra-ball": {
        'name': 'Ultra Ball',
        'desc': 'An ultra-performance Ball with a higher catch rate than a Great Ball.',
        'emoji': constant.ULTRABALL
    },
    "master-ball": {
        'name': 'Master Ball',
        'desc': 'The best Poké Ball with the ultimate level of performance. With it, you will catch any wild Pokémon without fail.',
        'emoji': constant.MASTERBALL
    },
    "potion": {
        'name': 'Potion',
        'desc': 'Restores HP that have been lost in battle by 20 HP.',
        'emoji': constant.POTION
    },
    "super-potion": {
        'name': 'Super Potion',
        'desc': 'Restores HP that have been lost in battle by 50 HP.',
        'emoji': constant.SUPERPOTION
    },
    "hyper-potion": {
        'name': 'Hyper Potion',
        'desc': 'Restores HP that have been lost in battle by 200 HP.',
        'emoji': constant.HYPERPOTION
    },
    "max-potion": {
        'name': 'Max Potion',
        'desc': 'Fully restores HP that have been lost in battle.',
        'emoji': constant.MAXPOTION
    },
    "revive": {
        'name': 'Revive',
        'desc': 'Revives a fainted Pokémon and restores half its maximum HP.',
        'emoji': constant.REVIVE
    },
    "full-restore": {
        'name': 'Full Restore',
        'desc': 'Fully restores HP and cures all ailments, such as poisoning.',
        'emoji': constant.FULLRESTORE
    },
    "repel": {
        'name': 'Repel',
        'desc': 'An aerosol spray that keeps wild Pokémon away.',
        'emoji': constant.REPEL
    },
    "super-repel": {
        'name': 'Super Repel',
        'desc': 'Keeps wild Pokémon away. Longer lasting than Repel.',
        'emoji': constant.SUPERREPEL
    },
    "max-repel": {
        'name': 'Max Repel',
        'desc': 'Keeps wild Pokémon away. Longer lasting than Super Repel.',
        'emoji': constant.MAXREPEL
    },
    "awakening": {
        'name': 'Awakening',
        'desc': 'Awakens a Pokémon that has fallen asleep.',
        'emoji': constant.AWAKENING
    },
    "escape-rope": {
        'name': 'Escape Rope',
        'desc': 'When in a place like a cave, this returns you to the last Pokémon Center visited.',
        'emoji': constant.ESCAPEROPE
    },
    "full-heal": {
        'name': 'Full Heal',
        'desc': 'Cures a Pokémon of any ailment except for fainting.',
        'emoji': constant.FULLHEAL
    },
    "ice-heal": {
        'name': 'Ice Heal',
        'desc': 'Thaws out a Pokémon that has been frozen solid.',
        'emoji': constant.ICEHEAL
    },
    "burn-heal": {
        'name': 'Burn Heal',
        'desc': 'Medicine for curing a Pokémon that is suffering from burn.',
        'emoji': constant.BURNHEAL
    },
    "paralyze-heal": {
        'name': 'Paralyze Heal',
        'desc': 'Cures a Pokémon that is suffering from paralysis.',
        'emoji': constant.PARALYZEHEAL
    },
    "antidote": {
        'name': 'Antidote',
        'desc': 'An antidote for curing a poisoned Pokémon.',
        'emoji': constant.ANTIDOTE
    },
    "calcium": {
        'name': 'Calcium',
        'desc': ''
    },
    "carbos": {
        'name': 'Carbos',
        'desc': ''
    },
    "coin-case": {
        'name': 'Coin Case',
        'desc': ''
    },
    "dire-hit": {
        'name': 'Dire Hit',
        'desc': ''
    },
    "dome-fossil": {
        'name': 'Dome Fossil',
        'desc': ''
    },
    "fresh-water": {
        'name': 'Fresh Water',
        'desc': ''
    },
    "helix-fossil": {
        'name': 'Helix Fossil'
    },
    "hp-up": {
        'name': 'HP Up',
        'desc': ''
    },
    "lemonade": {
        'name': 'Lemonade',
        'desc': ''
    },
    "max-ether": {
        'name': 'Max Ether',
        'desc': ''
    },
    "ether": {
        'name': 'Ether',
        'desc': ''
    },
    "nugget": {
        'name': 'Nugget',
        'desc': ''
    },
    "old-amber": {
        'name': 'Old Amber',
        'desc': ''
    },
    "poke-doll": {
        'name': 'Poké Doll',
        'desc': ''
    },
    "pp-up": {
        'name': 'PP Up',
        'desc': ''
    },
    "soda-pop": {
        'name': 'Soda Pop',
        'desc': ''
    },
    "town-map": {
        'name': 'Town Map',
        'desc': ''
    },
    "x-accuracy": {
        'name': 'X Accuracy',
        'desc': ''
    },
    "x-attack": {
        'name': 'X Attack',
        'desc': ''
    },
    "x-defense": {
        'name': 'X Defense',
        'desc': ''
    },
    "x-speed": {
        'name': 'X Speed',
        'desc': ''
    },
    "fire-stone": {
        'name': 'Fire Stone',
        'desc': ''
    },
    "water-stone": {
        'name': 'Water Stone',
        'desc': ''
    },
    "thunder-stone": {
        'name': 'Thunder Stone',
        'desc': ''
    },
    "leaf-stone": {
        'name': 'Leaf Stone',
        'desc': ''
    },
    "moon-stone": {
        'name': 'Moon Stone',
        'desc': ''
    },
    "elixir": {
        'name': 'Elixir',
        'desc': ''
    },
    "max-elixir": {
        'name': 'Max Elixir',
        'desc': ''
    },
    "x-sp-atk": {
        'name': 'X Sp. Attack',
        'desc': ''
    },
    "x-sp-def": {
        'name': 'X Sp. Defense',
        'desc': ''
    },
    # Special Items
    "link-cable": {
        "name": "Link Cable",
        "desc": "A string exuding a mysterious energy that makes you feel a strange sense of connection. It’s loved by certain Pokémon.",
        "emoji": constant.LINKCABLE
    }
}


class StoreState:
    storeList: List[List[StoreItem]]
    idx: int
    location: LocationModel

    discordId: int
    messageId: int
    channelId: int

    def __init__(self, discordId: int, messageId: int, channelId: int, location: LocationModel, storeList: List[List[StoreItem]], idx: int):
        self.discordId = discordId
        self.messageId = messageId
        self.channelId = channelId

        self.location = location
        self.storeList = storeList
        self.idx = idx


class PokemartMixin(MixinMeta):
    """Pokemart"""

    __store = {}


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

        state = StoreState(user.id, None, None, location, store.storeList, 0)

        embed, btns = self.__storePageEmbed(user, state)


        message = await ctx.send(
            embed=embed,
            components=btns
        )
        self.__store[str(user.id)] = state

        await ctx.tick()


    def __storePageEmbed(self, user: discord.Member, state: StoreState):
        # Create the embed object
        # file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/items/poke-ball.png", filename="poke-ball.png")
        embed = discord.Embed(title=f"Poké Mart - {constant.LOCATION_DISPLAY_NAMES[state.location.name]}")
        embed.set_thumbnail(url=f"https://pokesprites.joshkohut.com/sprites/locations/poke_mart.png")
        # embed.set_author(name=f"{user.display_name}",
        #                  icon_url=str(user.avatar_url))

        firstList = state.storeList[state.idx]

        for item in firstList:
            key = item.name
            price = item.price

            emoji = itemDisplayNames[key]['emoji']
            description = itemDisplayNames[key]['desc']
            name = itemDisplayNames[key]['name']

            embed.add_field(name=f"{emoji}  {name} — {price}", value=description, inline=False)


        btns = []

        if state.idx > 0:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'),
                self.__on_prev_click
            ))
        if state.idx < len(state.storeList) - 1:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
                self.__on_next_click
            ))

        return embed, [btns]


    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkStoreState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state: StoreState = self.__store[str(user.id)]
        state.idx = state.idx + 1

        embed, btns = await self.__storePageEmbed(user, state)
        message = await interaction.edit_origin(embed=embed, components=btns)
        
        state.messageId = message
        self.__store[str(user.id)] = state     
    

    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkStoreState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state: StoreState = self.__store[str(user.id)]
        state.idx = state.idx - 1

        embed, btns = await self.__storePageEmbed(user, state)
        message = await interaction.edit_origin(embed=embed, components=btns)
        
        state.messageId = message
        self.__store[str(user.id)] = state              


    def __checkStoreState(self, user: discord.User, message: discord.Message):
        state: StoreState
        if str(user.id) not in self.__store.keys():
            return False
        else:
            state = self.__store[str(user.id)]
            if state.messageId != message.id:
                return False
        return True
    


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

            # Send to logging channel
            await self.sendToLoggingChannel(store.message)
        else:
            # Send to logging channel
            await self.sendToLoggingChannel(store.message)

        # await ctx.send(res)
        # await ctx.send(f'{user.display_name} bought {count} {item}')


    @_pokemart.command()
    async def sell(self, ctx: commands.Context, item: str, count: int = 1) -> None:
        user = ctx.author

        trainer = TrainerClass(user.id)
        location = trainer.getLocation()
        store = StoreClass(trainer.discordId, location.locationId)

        if store.statuscode == 420:
            await ctx.send(store.message)
            return

        store.sellItem(item, count)

        await ctx.send(store.message)

        # Send to logging channel
        await self.sendToLoggingChannel(store.message)

