from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
# from discord_components import (
#     DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands
from redbot.core.commands.context import Context

import constant
from services.trainerclass import trainer as TrainerClass
from services.inventoryclass import inventory as InventoryClass
from services.keyitemsclass import keyitems as KeyItemsClass
from services.leaderboardclass import leaderboard as LeaderBoardClass

from .abcd import MixinMeta


DiscordUser = Union[discord.Member,discord.User]


class CardState:
    discordId: str
    messageId: int
    channelId: int

    def __init__(self, discordId: str, messageId: int, channelId: int) -> None:
        self.discordId = discordId
        self.messageId = messageId
        self.channelId = channelId


class TrainerCardMixin(MixinMeta):
    """Trainer Card"""

    __cards: dict[str, str] = {}


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()

        if not self.__checkCardState(user, interaction.message):
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return

        state: CardState = self.__cards[str(user.id)]

        # Check if author is trainer
        authorIsTrainer = user.id == state.discordId
        trainerUser: DiscordUser = user
        if not authorIsTrainer:
            ctx: Context = await self.bot.get_context(interaction.message)
            trainerUser = await ctx.guild.fetch_member(int(state.discordId))

        stats = LeaderBoardClass(str(state.discordId))
        stats.load()

        embed = discord.Embed(title=f"Trainer")
        embed.set_author(name=f"{trainerUser.display_name}", icon_url=str(trainerUser.display_avatar.url))

        embed.add_field(name='Battles', value=f'{stats.total_battles}', inline=True)
        embed.add_field(name='Victories', value=f'{stats.total_victory}', inline=True)
        embed.add_field(name='Defeats', value=f'{stats.total_defeat}', inline=True)
        embed.add_field(name='Pokemon Caught', value=f'{stats.total_catch}', inline=True)
        embed.add_field(name='Pokemon Released', value=f'{stats.total_released}', inline=True)
        embed.add_field(name='Pokemon Evolved', value=f'{stats.total_evolved}', inline=True)
        embed.add_field(name='Pokemon Traded', value=f'{stats.total_trades}', inline=True)

        view = View()
        button = Button(style=ButtonStyle.green, label="About", custom_id='about')
        button.callback = self.on_about_click_card
        view.add_item(button)

        message = await interaction.message.edit(embed=embed, view=view)
        self.__cards[str(user.id)] = CardState(state.discordId, message.id, message.channel.id)


    async def __on_about_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()

        if not self.__checkCardState(user, interaction.message):
            await interaction.followup.send('This is not for you.', ephemeral=True)
            return

        state: CardState = self.__cards[str(user.id)]

        # Check if author is trainer
        authorIsTrainer = user.id == state.discordId
        trainerUser: DiscordUser = user
        if not authorIsTrainer:
            ctx: Context = await self.bot.get_context(interaction.message)
            trainerUser = await ctx.guild.fetch_member(int(state.discordId))

        #  # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        inventory = InventoryClass(trainer.discordId)
        keyitems = KeyItemsClass(trainer.discordId)

        embed = self.__createAboutEmbed(trainerUser, trainer, inventory, keyitems)

        view = View()
        button = Button(style=ButtonStyle.green, label="Stats", custom_id='stats')
        button.callback = self.on_stats_click_card
        view.add_item(button)

        message = await interaction.message.edit(embed=embed, view=view)
        self.__cards[str(user.id)] = CardState(state.discordId, message.id, message.channel.id)


    def __createAboutEmbed(self, user: discord.User, trainer: TrainerClass, inventory: InventoryClass, keyitems: KeyItemsClass):
        embed = discord.Embed(title=f"Trainer")
        embed.set_author(name=f"{user.display_name}", icon_url=str(user.display_avatar.url))
        
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

        # FIX: Get actual Pokedex count
        pokedex_list = trainer.getPokedex()
        pokedex_count = len(pokedex_list) if pokedex_list else 0
        embed.add_field(name='Pokédex', value=f'{pokedex_count}')
        
        # FIX: Show actual start date
        embed.add_field(name='Started', value=f'{trainer.startdate}')
        
        return embed


    def __checkCardState(self, user: discord.User, message: discord.Message):
        if str(user.id) not in self.__cards.keys():
            return False
        else:
            state: CardState = self.__cards[str(user.id)]
            if state.messageId != message.id:
                return False
        return True

    @discord.ui.button(custom_id='stats', label='Stats', style=ButtonStyle.green)
    async def on_stats_click_card(self, interaction: discord.Interaction):
        await self.__on_stats_click(interaction)

    @discord.ui.button(custom_id='about', label='About', style=ButtonStyle.green)
    async def on_about_click_card(self, interaction: discord.Interaction):
        await self.__on_about_click(interaction)
