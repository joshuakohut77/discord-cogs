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

import constant
from services.trainerclass import trainer as TrainerClass
from services.inventoryclass import inventory as InventoryClass
from services.keyitemsclass import keyitems as KeyItemsClass
from services.leaderboardclass import leaderboard as LeaderBoardClass

from .abcd import MixinMeta


class TrainerCardMixin(MixinMeta):
    """Trainer Card"""

    __cards: dict[str, str] = {}


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    @_trainer.command()
    async def card(self, ctx: commands.Context, user: Union[discord.Member,discord.User] = None) -> None:
        if user is None:
            user = ctx.author

        #  # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        inventory = InventoryClass(trainer.discordId)
        keyitems = KeyItemsClass(trainer.discordId)
        
        embed = self.__createAboutEmbed(user, trainer, inventory, keyitems)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.__on_stats_click,
        ))
 
        message: discord.Message = await ctx.send(embed=embed, components=[btns])     
        self.__cards[str(user.id)] = message.id


    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkCardState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        stats = LeaderBoardClass(str(user.id))

        embed = discord.Embed(title=f"Trainer")
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.avatar_url))
        
        embed.add_field(name='Battles', value=f'¥{stats.total_battles}', inline=True)
        embed.add_field(name='Victories', value=f'¥{stats.total_victory}', inline=True)
        embed.add_field(name='Defeats', value=f'¥{stats.total_defeat}', inline=True)
        embed.add_field(name='Pokemon Caught', value=f'¥{stats.total_catch}', inline=True)
        embed.add_field(name='Pokemon Released', value=f'¥{stats.total_released}', inline=True)
        embed.add_field(name='Pokemon Evolved', value=f'¥{stats.total_evolved}', inline=True)
        embed.add_field(name='Pokemon Traded', value=f'¥{stats.total_trades}', inline=True)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="About", custom_id='about'),
            self.__on_about_click,
        ))
 
        message = await interaction.edit_origin(embed=embed, components=[btns])     
        self.__cards[str(user.id)] = message.id

    async def __on_about_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkCardState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        #  # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        inventory = InventoryClass(trainer.discordId)
        keyitems = KeyItemsClass(trainer.discordId)
        
        embed = self.__createAboutEmbed(user, trainer, inventory, keyitems)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.__on_stats_click,
        ))
 
        message = await interaction.edit_origin(embed=embed, components=[btns])     
        self.__cards[str(user.id)] = message.id


    def __createAboutEmbed(self, user: discord.User, trainer: TrainerClass, inventory: InventoryClass, keyitems: KeyItemsClass):
        embed = discord.Embed(title=f"Trainer")
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.avatar_url))
        
        embed.add_field(name='Money', value=f'¥{inventory.money}', inline=False)

        badges = []
        if keyitems.badge_boulder:
            badges.append(constant.BADGE_BOULDER_01)
        if keyitems.badge_cascade:
            badges.append(constant.BADGE_CASCADE_02)
        if keyitems.badge_thunder:
            badges.append(constant.BADGE_THUNDER_03)
        if keyitems.badge_rainbow:
            badges.append(constant.BADGE_RAINBOW_04)
        if keyitems.badge_soul:
            badges.append(constant.BADGE_SOUL_05)
        if keyitems.badge_marsh:
            badges.append(constant.BADGE_MARSH_06)
        if keyitems.badge_volcano:
            badges.append(constant.BADGE_VOLCANO_07)
        if keyitems.badge_earth:
            badges.append(constant.BADGE_EARTH_08)

        badgeText = " ".join(badges) if len(badges) > 0 else "--"
        embed.add_field(name='Badges', value=badgeText, inline=False)

        embed.add_field(name='Pokedex', value='0')
        embed.add_field(name='Started', value=f'{trainer.startdate}')
        return embed


    def __checkCardState(self, user: discord.User, message: discord.Message):
        if str(user.id) not in self.__cards.keys():
            return False
        else:
            originalMessageId = self.__cards[str(user.id)]
            if originalMessageId != message.id:
                return False
        return True