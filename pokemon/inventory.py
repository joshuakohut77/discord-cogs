from __future__ import annotations
from re import S
from typing import Any, Dict, List, Union, TYPE_CHECKING

from discord.abc import User
import constant
import uuid
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
from services.inventoryclass import inventory as InventoryClass
from services.keyitemsclass import keyitems as KeyItemClass


from .abcd import MixinMeta
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class InventoryMixin(MixinMeta):
    """Starter"""

    __inventory = {}


    def __checkInventoryState(self, user: discord.User, message: discord.Message):
        if str(user.id) not in self.__inventory.keys():
            return False
        else:
            originalMessageId = self.__inventory[str(user.id)]
            if originalMessageId != message.id:
                return False
        return True


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    @_trainer.command()
    async def bag(self, ctx: commands.Context, user: discord.Member = None):
        """Show trainer bag"""
        if user is None:
            user = ctx.author

        # # guild = self.bot.get_guild(971138995042025494)
        # # \u200b
        # # A device for catching wild Pokémon. It's thrown like a ball, comfortably encapsulating its target.

        embed, file, btns = self.createItemsEmbed(user)

        message = await ctx.send(
            embed=embed,
            file=file,
            components=[btns]
        )
        self.__inventory[str(user.id)] = message.id


    async def on_hm_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkInventoryState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        name = uuid.uuid4()
        file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/bag.png", filename=f"{name}.png")
        # Create the embed object
        embed = discord.Embed(title=f"Bag")
        embed.set_thumbnail(url=f"attachment://{name}.png")
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))
        
        embed.add_field(name='HMs', value='HMs are not implemented yet.', inline=False)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.gray, label="← Key Items", custom_id='keyitems'),
            self.on_keyitems_click,
        ))

        message = await interaction.edit_origin(embed=embed, file=file, components=[btns])
        self.__inventory[str(user.id)] = message.id


    async def on_items_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkInventoryState(user, interaction.message):
            await interaction.send('This is not for you.')
            return
        
        
        embed, file, btns = self.createItemsEmbed(user)

        await interaction.edit_origin(
            embed=embed,
            file=file,
            components=[btns]
        )
        self.__inventory[str(user.id)] = message.id
    

    async def on_keyitems_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkInventoryState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        inv = KeyItemClass(str(user.id))

        name = uuid.uuid4()
        file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/bag.png", filename=f"{name}.png")
        # Create the embed object
        embed = discord.Embed(title=f"Bag")
        embed.set_thumbnail(url=f"attachment://{name}.png")
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))

        items = []

        if inv.pokeflute:
            items.append(f'{constant.POKEFLUTE} **Pokeflute**')
        if inv.silph_scope:
            items.append(f'{constant.SILPH_SCOPE} **Silph Scope**')
        if inv.oaks_parcel:
            items.append(f'{constant.OAK_PARCEL} **Oak Parcel**')
        if inv.ss_ticket:
            items.append(f'{constant.SS_TICKET} **SS Ticket**')
        if inv.bicycle:
            items.append(f'{constant.BICYCLE} **Bicycle**')
        if inv.old_rod:
            items.append(f'{constant.OLD_ROD} **Old Rod**')
        if inv.good_rod:
            items.append(f'{constant.GOODROD} **Good Rod**')
        if inv.super_rod:
            items.append(f'{constant.SUPER_ROD} **Super Rod**')
        if inv.item_finder:
            items.append(f'{constant.ITEM_FINDER} **Item Finder**')

        embed.add_field(name='Key Items', value="No key items", inline=False)

        trainerItems = "\r\n".join(items) if len(items) > 0 else 'No key items yet.'
        embed.add_field(name='Key Items', value=trainerItems, inline=False)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.gray, label="← Items", custom_id='items'),
            self.on_items_click,
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.gray, label='HMs →', custom_id='hms'),
            self.on_hm_click,
        ))

        message = await interaction.edit_origin(embed=embed, file=file, components=[btns])
        self.__inventory[str(user.id)] = message.id


    def createItemsEmbed(self, user: User):
        inv = InventoryClass(str(user.id))

        name = uuid.uuid4()
        file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/bag.png", filename=f"{name}.png")
        # Create the embed object
        embed = discord.Embed(title=f"Bag")
        embed.set_thumbnail(url=f"attachment://{name}.png")
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))

        items = []

        if inv.pokeball > 0:
            items.append(f'{constant.POKEBALL} **Poke balls** — {inv.pokeball}')
        if inv.greatball > 0:
            items.append(f'{constant.GREATBALL} **Great balls** — {inv.greatball}')
        if inv.ultraball > 0:
            items.append(f'{constant.ULTRABALL} **Ultra balls** — {inv.ultraball}')
        if inv.masterball > 0:
            items.append(f'{constant.MASTERBALL} **Master ball** — {inv.masterball}')
        if inv.potion > 0:
            items.append(f'{constant.POTION} **Potion** — {inv.potion}')
        if inv.superpotion > 0:
            items.append(f'{constant.SUPERPOTION} **Super potion** — {inv.superpotion}')
        if inv.hyperpotion > 0:
            items.append(f'{constant.HYPERPOTION} **Hyper potion** — {inv.hyperpotion}')
        if inv.maxpotion > 0:
            items.append(f'{constant.MAXPOTION} **Max potion** — {inv.maxpotion}')
        if inv.revive > 0:
            items.append(f'{constant.REVIVE} **Revive** — {inv.revive}')
        if inv.fullrestore > 0:
            items.append(f'{constant.FULLRESTORE} **Full Restore** — {inv.fullrestore}')
        if inv.repel > 0:
            items.append(f'{constant.REPEL} **Repel** — {inv.repel}')
        if inv.superrepel > 0:
            items.append(f'{constant.REPEL} **Super Repel** — {inv.superrepel}')
        if inv.maxrepel > 0:
            items.append(f'{constant.MAXREPEL} **Max Repel** — {inv.maxrepel}')
        if inv.escaperope > 0:
            items.append(f'{constant.ESCAPEROPE} **Escape Rope** — {inv.escaperope}')
        if inv.awakening > 0:
            items.append(f'{constant.AWAKENING} **Awakening** — {inv.awakening}')
        if inv.antidote > 0:
            items.append(f'{constant.ANTIDOTE} **Antidote** — {inv.antidote}')
        if inv.iceheal > 0:
            items.append(f'{constant.ICEHEAL} **Iceheal** — {inv.iceheal}')
        if inv.burnheal > 0:
            items.append(f'{constant.BURNHEAL} **Burnheal** — {inv.burnheal}')
        if inv.paralyzeheal > 0:
            items.append(f'{constant.PARALYZEHEAL} **Paralyzeheal** — {inv.paralyzeheal}')
        if inv.fullheal > 0:
            items.append(f'{constant.FULLHEAL} **Fullheal** — {inv.fullheal}')
        if inv.calcium > 0:
            items.append(f'{constant.CALCIUM} **Calcium** — {inv.calcium}')
        if inv.carbos > 0:
            items.append(f'{constant.CARBOS} **Carbos** — {inv.carbos}')
        if inv.coincase > 0:
            items.append(f'{constant.COINCASE} **Coin Case** — {inv.coincase}')
        if inv.direhit > 0:
            items.append(f'{constant.DIREHIT} **Direhit** — {inv.direhit}')
        if inv.domefossil > 0:
            items.append(f'{constant.DOMEFOSSIL} **Dome Fossil** — {inv.domefossil}')
        if inv.helixfossil > 0:
            items.append(f'{constant.HELIXFOSSIL} **Helix Fossil** — {inv.helixfossil}')
        if inv.freshwater > 0:
            items.append(f'{constant.FRESHWATER} **Freshwater** — {inv.freshwater}')
        if inv.hpup > 0:
            items.append(f'{constant.HPUP} **HP Up** — {inv.hpup}')
        if inv.lemonade > 0:
            items.append(f'{constant.LEMONADE} **Lemonade** — {inv.lemonade}')
        if inv.elixer > 0:
            items.append(f'{constant.ELIXIR} **Elixir** — {inv.elixer}')
        if inv.maxelixer > 0:
            items.append(f'{constant.MAXELIXIR} **Max Elixir** — {inv.maxelixer}')
        if inv.maxether > 0:
            items.append(f'{constant.MAXETHER} **Max Ether** — {inv.maxether}')
        if inv.ether > 0:
            items.append(f'{constant.ETHER} **Ether** — {inv.ether}')
        if inv.nugget > 0:
            items.append(f'{constant.NUGGET} **Nugget** — {inv.nugget}')
        if inv.oldamber > 0:
            items.append(f'{constant.OLDAMBER} **Old Amber** — {inv.oldamber}')
        if inv.pokedoll > 0:
            items.append(f'{constant.POKEDOLL} **Poke Doll** — {inv.pokedoll}')
        if inv.ppup > 0:
            items.append(f'{constant.PPUP} **PP Up** — {inv.ppup}')
        if inv.sodapop > 0:
            items.append(f'{constant.SODAPOP} **Soda Pop** — {inv.sodapop}')
        if inv.townmap > 0:
            items.append(f'{constant.TOWNMAP} **Town Map** — {inv.townmap}')
        if inv.xaccuracy > 0:
            items.append(f'{constant.XACCURACY} **X Accuracy** — {inv.xaccuracy}')
        if inv.xdefense > 0:
            items.append(f'{constant.XDEFENSE} **X Defense** — {inv.xdefense}')
        if inv.xspatk > 0:
            items.append(f'{constant.XSPATTACK} **X Sp. Attack** — {inv.xspatk}')
        if inv.xspeed > 0:
            items.append(f'{constant.XSPEED} **X Speed** — {inv.xspeed}')
        if inv.xattack > 0:
            items.append(f'{constant.XATTACK} **X Attack** — {inv.xattack}')
        if inv.firestone > 0:
            items.append(f'{constant.FIRESTONE} **Firestone** — {inv.firestone}')
        if inv.waterstone > 0:
            items.append(f'{constant.WATERSTONE} **Waterstone** — {inv.waterstone}')
        if inv.thunderstone > 0:
            items.append(f'{constant.THUNDERSTONE} **Thunderstone** — {inv.thunderstone}')
        if inv.leafstone > 0:
            items.append(f'{constant.LEAFSTONE} **Leafstone** — {inv.leafstone}')
        if inv.moonstone > 0:
            items.append(f'{constant.MOONSTONE} **Moonstone** — {inv.moonstone}')


        trainerItems = "\r\n".join(items) if len(items) > 0 else 'No items yet.'
        embed.add_field(name='Items', value=trainerItems, inline=False)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.gray, label='Key Items →', custom_id='keyitems'),
            self.on_keyitems_click,
        ))

        return embed, file, btns