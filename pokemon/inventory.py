from __future__ import annotations
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


from .abcd import MixinMeta
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class StarterMixin(MixinMeta):
    """Starter"""

    __inventory = {}


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


    async def on_items_click(self, interaction: Interaction):
        user = interaction.user
        messageId = interaction.message.id

        if str(user.id) not in self.__inventory.keys():
            await interaction.send('This is not for you.')
        else:
            originalMessageId = self.__inventory[str(user.id)]
            if originalMessageId != messageId:
                await interaction.send('This is not for you.')
        
        embed, file, btns = self.createItemsEmbed(user)


        await interaction.edit_origin(
            embed=embed,
            file=file,
            components=[btns]
        )
        self.__inventory[str(user.id)] = message.id
    

    async def on_keyitems_click(self, interaction: Interaction):
        user = interaction.user
        messageId = interaction.message.id

        if str(user.id) not in self.__inventory.keys():
            await interaction.send('This is not for you.')
        else:
            originalMessageId = self.__inventory[str(user.id)]
            if originalMessageId != messageId:
                await interaction.send('This is not for you.')
        
        name = uuid.uuid4()
        file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/bag.png", filename=f"{name}.png")
        # Create the embed object
        embed = discord.Embed(title=f"Bag")
        embed.set_thumbnail(url=f"attachment://{name}.png")
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))

        embed.add_field(name='Key Items', value="No key items", inline=False)

        btns = []
        btns.append(Button(style=ButtonStyle.gray, label="← Items", custom_id='items'))

        message = await interaction.edit_origin(embed=embed, file=file, components=[btns])
        self.__inventory[str(user.id)] = message.id


    def createItemsEmbed(user: User):
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
            items.append(f'{constant.POKEBALL} **Pokeballs** — {inv.pokeball}')
        if inv.greatball > 0:
            items.append(f'{constant.GREATBALL} **Greatballs** — {inv.greatball}')
        if inv.ultraball > 0:
            items.append(f'{constant.ULTRABALL} **Ultraball** — {inv.ultraball}')
        if inv.masterball > 0:
            items.append(f'{constant.MASTERBALL} **Masterball** — {inv.masterball}')
        if inv.potion > 0:
            items.append(f'{constant.POTION} **Potion** — {inv.potion}')
        if inv.superpotion > 0:
            items.append(f'{constant.SUPERPOTION} **Superpotion** — {inv.superpotion}')
        if inv.hyperpotion > 0:
            items.append(f'{constant.HYPERPOTION} **Hyperpotion** — {inv.hyperpotion}')
        if inv.maxpotion > 0:
            items.append(f'{constant.MAXPOTION} **Maxpotion** — {inv.maxpotion}')
        if inv.revive > 0:
            items.append(f'{constant.REVIVE} **Revive** — {inv.revive}')
        if inv.fullrestore > 0:
            items.append(f'{constant.FULLRESTORE} **Full Restore** — {inv.fullrestore}')
        if inv.repel > 0:
            items.append(f'{constant.REPEL} **Repel** — {inv.repel}')
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

        trainerItems = "\r\n".join(items)
        embed.add_field(name='Items', value=trainerItems, inline=False)

        btns = []
        btns.append(Button(style=ButtonStyle.gray, label='Key Items →', custom_id='keyitems'))

        return embed, file, btns