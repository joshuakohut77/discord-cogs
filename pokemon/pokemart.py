from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING


import discord
from discord import embeds
from discord import emoji
# from discord_components import (ButtonStyle, Button, Interaction)
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

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
    "coin-case": {
        'name': 'Coin Case',
        'desc': ''
    },
    "dome-fossil": {
        'name': 'Dome Fossil',
        'desc': ''
    },
    "helix-fossil": {
        'name': 'Helix Fossil'
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
        'desc': 'A doll that attracts the attention of a Pokémon. It guarantees escape from any battle with wild Pokémon.',
        'emoji': constant.POKEDOLL
    },
    "town-map": {
        'name': 'Town Map',
        'desc': ''
    },
    "fresh-water": {
        'name': 'Fresh Water',
        'desc': 'Water with a high mineral content. It restores the HP of one Pokémon by 50 points.',
        'emoji': constant.FRESHWATER
    },
    "soda-pop": {
        'name': 'Soda Pop',
        'desc': 'A fizzy soda drink. It restores the HP of one Pokémon by 60 points.',
        'emoji': constant.SODAPOP
    },
    "lemonade": {
        'name': 'Lemonade',
        'desc': 'A very sweet drink. It restores the HP of one Pokémon by 80 points.',
        'emoji': constant.LEMONADE
    },
    # Stat Items
    "iron": {
        'name': 'Iron',
        'desc': 'A nutritious drink for Pokémon. It raises the base DEFENSE stat of one Pokémon.',
        'emoji': constant.IRON
    },
    "protein": {
        'name': 'protein',
        'desc': 'A nutritious drink for Pokémon. It raises the base Attack stat of one Pokémon.',
        'emoji': constant.PROTEIN
    },
    "carbos": {
        'name': 'Carbos',
        'desc': 'A nutritious drink for Pokémon. It raises the base SPEED stat of one Pokémon.',
        'emoji': constant.CARBOS
    },
    "calcium": {
        'name': 'Calcium',
        'desc': 'A nutritious drink for Pokémon. It raises the base SP. ATK stat of one Pokémon.',
        'emoji': constant.CALCIUM
    },
    "hp-up": {
        'name': 'HP Up',
        'desc': 'A nutritious drink for Pokémon. It raises the base HP of one Pokémon.',
        'emoji': constant.HPUP
    },
    "x-accuracy": {
        'name': 'X Accuracy',
        'desc': 'Raises accuracy of attack moves during one battle.',
        'emoji': constant.XACCURACY
    },
    "x-attack": {
        'name': 'X Attack',
        'desc': 'Raises the ATTACK stat of Pokémon in battle. Wears off if the Pokémon is withdrawn.',
        'emoji': constant.XATTACK
    },
    "x-defense": {
        'name': 'X Defense',
        'desc': 'Raises the DEFENSE stat of Pokémon in battle. Wears off if the Pokémon is withdrawn.',
        'emoji': constant.XDEFENSE
    },
    "x-speed": {
        'name': 'X Speed',
        'desc': 'Raises the SPEED stat of Pokémon in battle. Wears off if the Pokémon is withdrawn.',
        'emoji': constant.XSPEED
    },
    "x-sp-atk": {
        'name': 'X Sp. Attack',
        'desc': 'Raises the Sp.Atk stat of Pokémon in battle. Wears off if the Pokémon is withdrawn.',
        'emoji': constant.XSPATTACK
    },
    "x-sp-def": {
        'name': 'X Sp. Defense',
        'desc': 'An item that raises the Sp. Def stat of a Pokémon in battle. It wears off if the Pokémon is withdrawn.',
        'emoji': constant.XSPDEFENSE
    },
    "dire-hit": {
        'name': 'Dire Hit',
        'desc': 'Raises the critical-hit ratio of Pokémon in battle. Wears off if the Pokémon is withdrawn.',
        'emoji': constant.DIREHIT
    },
    "pp-up": {
        'name': 'PP Up',
        'desc': 'Slightly raises the maximum PP of a selected move for one Pokémon.',
        'emoji': constant.PPUP
    },
    # Evolution Stones
    "fire-stone": {
        'name': 'Fire Stone',
        'desc': 'A peculiar stone that makes certain species of Pokémon evolve. It is colored orange.',
        'emoji': constant.FIRESTONE
    },
    "water-stone": {
        'name': 'Water Stone',
        'desc': 'A peculiar stone that makes certain species of Pokémon evolve. It is a clear, light blue.',
        'emoji': constant.WATERSTONE
    },
    "thunder-stone": {
        'name': 'Thunder Stone',
        'desc': 'A peculiar stone that makes certain species of Pokémon evolve. It has a thunderbolt pattern.',
        'emoji': constant.THUNDERSTONE
    },
    "leaf-stone": {
        'name': 'Leaf Stone',
        'desc': 'A peculiar stone that makes certain species of Pokémon evolve. It has a leaf pattern.',
        'emoji': constant.LEAFSTONE
    },
    "moon-stone": {
        'name': 'Moon Stone',
        'desc': 'A peculiar stone that makes certain species of Pokémon evolve. It is as black as the night sky.',
        'emoji': constant.MOONSTONE
    },
    "elixir": {
        'name': 'Elixir',
        'desc': ''
    },
    "max-elixir": {
        'name': 'Max Elixir',
        'desc': ''
    },
    # TMs
    "TM01": {'name': 'TM01 Mega Punch', 'desc': 'Teaches Mega Punch to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM02": {'name': 'TM02 Razor Wind', 'desc': 'Teaches Razor Wind to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM03": {'name': 'TM03 Swords Dance', 'desc': 'Teaches Swords Dance to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM04": {'name': 'TM04 Whirlwind', 'desc': 'Teaches Whirlwind to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM05": {'name': 'TM05 Mega Kick', 'desc': 'Teaches Mega Kick to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM06": {'name': 'TM06 Toxic', 'desc': 'Teaches Toxic to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM07": {'name': 'TM07 Horn Drill', 'desc': 'Teaches Horn Drill to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM08": {'name': 'TM08 Body Slam', 'desc': 'Teaches Body Slam to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM09": {'name': 'TM09 Take Down', 'desc': 'Teaches Take Down to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM10": {'name': 'TM10 Double Edge', 'desc': 'Teaches Double-Edge to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM11": {'name': 'TM11 Bubble Beam', 'desc': 'Teaches Bubble Beam to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM12": {'name': 'TM12 Water Gun', 'desc': 'Teaches Water Gun to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM13": {'name': 'TM13 Ice Beam', 'desc': 'Teaches Ice Beam to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM14": {'name': 'TM14 Blizzard', 'desc': 'Teaches Blizzard to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM15": {'name': 'TM15 Hyper Beam', 'desc': 'Teaches Hyper Beam to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM16": {'name': 'TM16 Pay Day', 'desc': 'Teaches Pay Day to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM17": {'name': 'TM17 Submission', 'desc': 'Teaches Submission to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM18": {'name': 'TM18 Counter', 'desc': 'Teaches Counter to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM19": {'name': 'TM19 Seismic Toss', 'desc': 'Teaches Seismic Toss to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM20": {'name': 'TM20 Rage', 'desc': 'Teaches Rage to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM21": {'name': 'TM21 Mega Drain', 'desc': 'Teaches Mega Drain to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM22": {'name': 'TM22 Solar Beam', 'desc': 'Teaches Solar Beam to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM23": {'name': 'TM23 Dragon Rage', 'desc': 'Teaches Dragon Rage to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM24": {'name': 'TM24 Thunderbolt', 'desc': 'Teaches Thunderbolt to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM25": {'name': 'TM25 Thunder', 'desc': 'Teaches Thunder to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM26": {'name': 'TM26 Earthquake', 'desc': 'Teaches Earthquake to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM27": {'name': 'TM27 Fissure', 'desc': 'Teaches Fissure to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM28": {'name': 'TM28 Dig', 'desc': 'Teaches Dig to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM29": {'name': 'TM29 Psychic', 'desc': 'Teaches Psychic to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM30": {'name': 'TM30 Teleport', 'desc': 'Teaches Teleport to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM31": {'name': 'TM31 Mimic', 'desc': 'Teaches Mimic to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM32": {'name': 'TM32 Double Team', 'desc': 'Teaches Double Team to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM33": {'name': 'TM33 Reflect', 'desc': 'Teaches Reflect to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM34": {'name': 'TM34 Bide', 'desc': 'Teaches Bide to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM35": {'name': 'TM35 Metronome', 'desc': 'Teaches Metronome to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM36": {'name': 'TM36 Self Destruct', 'desc': 'Teaches Self-Destruct to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM37": {'name': 'TM37 Egg Bomb', 'desc': 'Teaches Egg Bomb to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM38": {'name': 'TM38 Fire Blast', 'desc': 'Teaches Fire Blast to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM39": {'name': 'TM39 Swift', 'desc': 'Teaches Swift to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM40": {'name': 'TM40 Skull Bash', 'desc': 'Teaches Skull Bash to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM41": {'name': 'TM41 Softboiled', 'desc': 'Teaches Softboiled to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM42": {'name': 'TM42 Dream Eater', 'desc': 'Teaches Dream Eater to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM43": {'name': 'TM43 Sky Attack', 'desc': 'Teaches Sky Attack to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM44": {'name': 'TM44 Rest', 'desc': 'Teaches Rest to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM45": {'name': 'TM45 Thunder Wave', 'desc': 'Teaches Thunder Wave to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM46": {'name': 'TM46 Psywave', 'desc': 'Teaches Psywave to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM47": {'name': 'TM47 Explosion', 'desc': 'Teaches Explosion to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM48": {'name': 'TM48 Rock Slide', 'desc': 'Teaches Rock Slide to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM49": {'name': 'TM49 Tri Attack', 'desc': 'Teaches Tri Attack to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
    "TM50": {'name': 'TM50 Substitute', 'desc': 'Teaches Substitute to a compatible Pokémon.', 'emoji': constant.TM_EMOJI},
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
            view=btns
        )
        state.messageId = message.id
        state.channelId = message.channel.id
        self.__store[str(user.id)] = state

        await ctx.tick()

    def __storePageEmbed(self, user: discord.Member, state: StoreState):
        # Create the embed object
        # file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/items/poke-ball.png", filename="poke-ball.png")
        embed = discord.Embed(
            title=f"Poké Mart - {constant.LOCATION_DISPLAY_NAMES[state.location.name]}")
        embed.set_thumbnail(
            url=f"https://pokesprites.joshkohut.com/sprites/locations/poke_mart.png")
        # embed.set_author(name=f"{user.display_name}",
        #                  icon_url=str(user.display_avatar.url))

        firstList = state.storeList[state.idx]

        for item in firstList:
            key = item.name
            price = item.price

            emoji = itemDisplayNames[key]['emoji']
            description = itemDisplayNames[key]['desc']
            name = itemDisplayNames[key]['name']

            embed.add_field(name=f"{emoji}  {name} — {price}",
                            value=description, inline=False)

        view = View()

        if state.idx > 0:
            button = Button(style=ButtonStyle.gray, label='Previous', custom_id='previous')
            button.callback = self.on_prev_click_pokemart
            view.add_item(button)

        if state.idx < len(state.storeList) - 1:
            button = Button(style=ButtonStyle.gray, label="Next", custom_id='next')
            button.callback = self.on_next_click_pokemart
            view.add_item(button)

        return embed, view

    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()

        if not self.__checkStoreState(user, interaction.message):
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return

        state: StoreState = self.__store[str(user.id)]
        state.idx = state.idx + 1

        embed, btns = self.__storePageEmbed(user, state)
        message = await interaction.message.edit(embed=embed, view=btns)

        state.messageId = message.id
        self.__store[str(user.id)] = state

    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()

        if not self.__checkStoreState(user, interaction.message):
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return

        state: StoreState = self.__store[str(user.id)]
        state.idx = state.idx - 1

        embed, btns = self.__storePageEmbed(user, state)
        message = await interaction.message.edit(embed=embed, view=btns)

        state.messageId = message.id
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

    @discord.ui.button(custom_id='next', label='Next', style=ButtonStyle.gray)
    async def on_next_click_pokemart(self, interaction: discord.Interaction):
        await self.__on_next_click(interaction)

    @discord.ui.button(custom_id='previous', label='Previous', style=ButtonStyle.gray)
    async def on_prev_click_pokemart(self, interaction: discord.Interaction):
        await self.__on_prev_click(interaction)
