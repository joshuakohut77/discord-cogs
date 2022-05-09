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


from .abcd import MixinMeta
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class StarterMixin(MixinMeta):
    """Starter"""

    # def __init__(self, bot: Red):
    #     self.client = DiscordComponents(bot)
    #     self.bot: Red = bot
    __trainers = {}

    # @commands.group(name="test")
    # @commands.guild_only()
    # async def _test(self, ctx: commands.Context) -> None:
    #     """Base command to manage the trainer (user).
    #     """
    #     pass
    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    @_trainer.command()
    async def active(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the currect active pokemon for the trainer."""
        if user is None:
            user = ctx.author

         # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getActivePokemon()

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.on_stats_click,
        ))
        btns.append(Button(style=ButtonStyle.green,
                    label="Pokedex", custom_id='pokedex'))
        # btns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
        # btns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))

        embed = createPokemonAboutEmbed(user, pokemon)
        message = await ctx.send(embed=embed, components=[btns])       
        self.__trainers[str(user.id)] = message.id


    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the starter pokemon for the trainer."""
        if user is None:
            user = ctx.author

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()
        active = trainer.getActivePokemon()

        embed = createPokemonAboutEmbed(user, pokemon)

        btns = []

        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.on_stats_click,
        ))
        # btns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
        btns.append(Button(style=ButtonStyle.green,
                    label="Pokedex", custom_id='pokedex'))

        # Disable the "Set Active" button if the starter is currently the active pokemon
        disabled = (active is not None) and (
            pokemon.trainerId == active.trainerId)
        btns.append(Button(style=ButtonStyle.blue, label="Set Active",
                    custom_id='active', disabled=disabled))

        message: discord.Message = await ctx.send(embed=embed, components=[btns])
        self.__trainers[str(user.id)] = message.id

    async def on_about_click(self, interaction: Interaction):
        user = interaction.user
        messageId = interaction.message.id

        if str(user.id) not in self.__trainers.keys():
            await interaction.send('This is not for you.')
        else:
            originalMessageId = self.__trainers[str(user.id)]
            if originalMessageId != messageId:
                await interaction.send('This is not for you.')

        # author = interaction.message.author

        # if user.id != author.id:
        #     await interaction.send('This is not for you.')

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()
        # TODO: all i need is the active id, get that when the trainer is first loaded
        active = trainer.getActivePokemon()

        embed = createPokemonAboutEmbed(user, pokemon)

        btns = []

        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.on_stats_click,
        ))
        btns.append(Button(style=ButtonStyle.green,
                    label="Pokedex", custom_id='pokedex'))

        # Disable the "Set Active" button if the starter is currently the active pokemon
        disabled = (active is not None) and (
            pokemon.trainerId == active.trainerId)
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.blue, label="Set Active",
                   custom_id='active', disabled=disabled),
            self.on_set_active_click,
        ))

        message = await interaction.edit_origin(embed=embed, components=[btns])
        self.__trainers[str(user.id)] = message.id

    async def on_set_active_click(self, interaction: Interaction):
        user = interaction.user
        messageId = interaction.message.id

        if str(user.id) not in self.__trainers.keys():
            await interaction.send('This is not for you.')
        else:
            originalMessageId = self.__trainers[str(user.id)]
            if originalMessageId != messageId:
                await interaction.send('This is not for you.')
        
        # author = interaction.message.author

        # if user.id != author.id:
        #     await interaction.send('This is not for you.')

        trainer = TrainerClass(str(user.id))

        pokemon = trainer.getStarterPokemon()
        trainer.setActivePokemon(pokemon.trainerId)

        await self.on_about_click(interaction)

    async def on_stats_click(self, interaction: Interaction):
        user = interaction.user
        messageId = interaction.message.id

        if str(user.id) not in self.__trainers.keys():
            await interaction.send('This is not for you.')
        else:
            originalMessageId = self.__trainers[str(user.id)]
            if originalMessageId != messageId:
                await interaction.send('This is not for you.')
        
        # author = interaction.message.author

        # if user.id != author.id:
        #     await interaction.send(f'{user.id} :: {author.id}')

        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()

        embed = createStatsEmbed(user, pokemon)

        btns = []

        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="About", custom_id='about'),
            self.on_about_click,
        ))
        # btns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
        btns.append(Button(style=ButtonStyle.green,
                    label="Pokedex", custom_id='pokedex'))

        message = await interaction.edit_origin(embed=embed, components=[btns])
        self.__trainers[str(user.id)] = message.id

    async def on_pokedex_click(self, interaction: Interaction):
        user = interaction.user
        messageId = interaction.message.id

        if str(user.id) not in self.__trainers.keys():
            await interaction.send('This is not for you.')
        else:
            originalMessageId = self.__trainers[str(user.id)]
            if originalMessageId != messageId:
                await interaction.send('This is not for you.')
        
        # author = interaction.message.author

        # if user.id != author.id:
        #     await interaction.send('This is not for you.')

        # TODO: all i need is the active id, get that when the trainer is first loaded
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()

        embed = createStatsEmbed(user, pokemon)

        btns = []

        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="About", custom_id='about'),
            self.on_about_click,
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.on_stats_click,
        ))

        await interaction.edit_origin(embed=embed, components=[btns])
