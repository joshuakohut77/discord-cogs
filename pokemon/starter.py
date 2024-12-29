from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
# from discord_components import (ButtonStyle, Button, Interaction)
# from discord import ButtonStyle, Button, Interaction

from discord import ButtonStyle, Interaction
from discord.ui import Button, View

from redbot.core.commands.context import Context

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass
from services.pokedexclass import pokedex as PokedexClass
from services.inventoryclass import inventory as InventoryClass
from models.state import PokemonState, DisplayCard

from .abcd import MixinMeta
from .functions import (createStatsEmbed, createPokedexEntryEmbed,
                        createPokemonAboutEmbed)
from .helpers import (getTrainerGivenPokemonName)


DiscordUser = Union[discord.Member,discord.User]


class StarterMixin(MixinMeta):
    """Starter"""


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    @_trainer.command(name='nickname', aliases=['nn'])
    async def nickName(self, ctx: commands.Context, id: int, name: str):
        user = ctx.author

        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getPokemonById(id)

        if pokemon is not None:
            pokemon.nickName = name
            pokemon.save()
            await ctx.send(f'You changed {pokemon.pokemonName.capitalize()} nickname to {name}')
        else:
            await ctx.send(f'That pokemon does not exist')
        


    @_trainer.command()
    async def active(self, ctx: commands.Context, user: DiscordUser = None) -> None:
        """Show the currect active pokemon for the trainer."""
        author = ctx.author

        if user is None:
            user = ctx.author

         # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getActivePokemon()

        state = PokemonState(str(user.id), None, DisplayCard.STATS, [pokemon], pokemon.trainerId, None)

        authorIsTrainer = user.id == state.discordId

        embed, btns = self.__pokemonSingleCard(user, state, state.card, authorIsTrainer)

        message: discord.Message = await ctx.send(embed=embed, components=btns)
        self.setPokemonState(author, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, None))


    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: DiscordUser = None) -> None:
        """Show the starter pokemon for the trainer."""
        author = ctx.author

        if user is None:
            user = ctx.author

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()
        active = trainer.getActivePokemon()

        state = PokemonState(str(user.id), None, DisplayCard.STATS, [pokemon], active.trainerId, None)

        authorIsTrainer = user.id == state.discordId

        embed, btns = self.__pokemonSingleCard(user, state, state.card, authorIsTrainer)

        message: discord.Message = await ctx.send(embed=embed, view=btns)
        self.setPokemonState(author, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, None))


    async def __on_moves_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        # Check if author is trainer
        authorIsTrainer = user.id == state.discordId
        trainerUser: DiscordUser = user
        if not authorIsTrainer:
            ctx: Context = await self.bot.get_context(interaction.message)
            trainerUser = await ctx.guild.fetch_member(int(state.discordId))

        embed, btns = self.__pokemonSingleCard(trainerUser, state, DisplayCard.MOVES, authorIsTrainer)

        message = await interaction.edit_origin(embed=embed, components=btns)
        self.setPokemonState(user, PokemonState(state.discordId, message.id, DisplayCard.MOVES, state.pokemon, state.active, None))
    

    async def __on_pokedex_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        # Check if author is trainer
        authorIsTrainer = user.id == state.discordId
        trainerUser: DiscordUser = user
        if not authorIsTrainer:
            ctx: Context = await self.bot.get_context(interaction.message)
            trainerUser = await ctx.guild.fetch_member(int(state.discordId))

        embed, btns = self.__pokemonSingleCard(trainerUser, state, DisplayCard.DEX, authorIsTrainer)

        message = await interaction.edit_origin(embed=embed, components=btns)
        self.setPokemonState(user, PokemonState(state.discordId, message.id, DisplayCard.DEX, state.pokemon, state.active, None))
    

    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        # Check if author is trainer
        authorIsTrainer = user.id == state.discordId
        trainerUser: DiscordUser = user
        if not authorIsTrainer:
            ctx: Context = await self.bot.get_context(interaction.message)
            trainerUser = await ctx.guild.fetch_member(int(state.discordId))

        embed, btns = self.__pokemonSingleCard(trainerUser, state, DisplayCard.STATS, authorIsTrainer)

        message = await interaction.edit_origin(embed=embed, components=btns)
        self.setPokemonState(user, PokemonState(state.discordId, message.id, DisplayCard.STATS, state.pokemon, state.active, None))
    

    async def __on_set_active_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)
        pokemon = state.pokemon[0]

        trainer = TrainerClass(str(user.id))
        trainer.setActivePokemon(pokemon.trainerId)

        await interaction.channel.send(f'{user.display_name} set their active pokemon to {getTrainerGivenPokemonName(pokemon)}.')

        await self.__on_stats_click(interaction)


    async def __on_items_back(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonSingleCard(user, state, DisplayCard.STATS)

        message = await interaction.edit_origin(embed=embed, components=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.STATS, state.pokemon, state.active, None))


    
    async def __on_use_item(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return
        
        state = self.getPokemonState(user)
        pokemon = state.pokemon[0]

        item = ''
        if interaction.custom_id == 'potion':
            item = 'potion'
        elif interaction.custom_id == 'superpotion':
            item = 'super-potion'
        elif interaction.custom_id == 'hyperpotion':
            item = 'hyper-potion'
        elif interaction.custom_id == 'maxpotion':
            item = 'max-potion'
        elif interaction.custom_id == 'revive':
            item = 'revive'

        trainer = TrainerClass(str(user.id))
        trainer.heal(pokemon.trainerId, item)

        if trainer.message:
            ctx = await self.bot.get_context(interaction.message)
            embed, btns = await self.__pokemonItemsCard(user, state, state.card, ctx)
            message = await interaction.edit_origin(embed=embed, components=btns)
            self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, None))
    
            await interaction.channel.send(f'{user.display_name}, {trainer.message}')
        else:
            await interaction.send('Could not use the item.')


    async def __on_items_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.getPokemonState(user)

        ctx = await self.bot.get_context(interaction.message)

        embed, btns = await self.__pokemonItemsCard(user, state, DisplayCard.ITEMS, ctx)

        message = await interaction.edit_origin(embed=embed, components=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.ITEMS, state.pokemon, state.active, state.idx))



    async def __pokemonItemsCard(self, user: discord.User, state: PokemonState, card: DisplayCard, ctx: Context):
        pokemon = state.pokemon[0]
        activeId = state.active

        if DisplayCard.STATS.value == card.value:
            embed = createStatsEmbed(user, pokemon)
        elif DisplayCard.MOVES.value == card.value:
            embed = createPokemonAboutEmbed(user, pokemon)
        else:
            dex = PokedexClass.getPokedexEntry(pokemon)
            embed = createPokedexEntryEmbed(user, pokemon, dex)


        inv = InventoryClass(str(user.id))


        firstRowBtns = []
        if inv.potion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.POTION)
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.grey, emoji=emote, label="Potion", custom_id='potion'),
                self.__on_use_item
            ))
        if inv.superpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.SUPERPOTION)
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.grey, emoji=emote, label="Super Potion", custom_id='superpotion'),
                self.__on_use_item
            ))
        if inv.hyperpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.HYPERPOTION)
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.grey, emoji=emote, label="Hyper Potion", custom_id='hyperpotion'),
                self.__on_use_item
            ))
        if inv.maxpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.MAXPOTION)
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.grey, emoji=emote, label="Max Potion", custom_id='maxpotion'),
                self.__on_use_item
            ))
        if inv.revive > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.REVIVE)
            firstRowBtns.append(self.client.add_callback(
                Button(style=ButtonStyle.grey, emoji=emote, label="Revive", custom_id='revive'),
                self.__on_use_item
            ))

        secondRowBtns = []
        secondRowBtns.append(self.client.add_callback(
            Button(style=ButtonStyle.grey, label="Back", custom_id='back'),
            self.__on_items_back
        ))

        btns = []
        if len(firstRowBtns) > 0:
            btns.append(firstRowBtns)
        if len(secondRowBtns) > 0:
            btns.append(secondRowBtns)

        return embed, btns


    def __pokemonSingleCard(self, user: discord.User, state: PokemonState, card: DisplayCard, authorIsTrainer = True):
        pokemon = state.pokemon[0]
        activeId = state.active

        if DisplayCard.STATS.value == card.value:
            embed = createStatsEmbed(user, pokemon)
        elif DisplayCard.MOVES.value == card.value:
            embed = createPokemonAboutEmbed(user, pokemon)
        else:
            dex = PokedexClass.getPokedexEntry(pokemon)
            embed = createPokedexEntryEmbed(user, pokemon, dex)


        firstRowBtns = []

        # if DisplayCard.MOVES.value != card.value:
        #     firstRowBtns.append(self.client.add_callback(
        #         Button(style=ButtonStyle.green, label="Moves", custom_id='moves'),
        #         self.__on_moves_click
        #     ))

        # if DisplayCard.STATS.value != card.value:
        #     firstRowBtns.append(self.client.add_callback(
        #         Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
        #         self.__on_stats_click,
        #     ))
        # if DisplayCard.DEX.value != card.value:
        #     firstRowBtns.append(self.client.add_callback(
        #         Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'),
        #         self.__on_pokedex_click
        #     ))

        # if authorIsTrainer:
        #     firstRowBtns.append(self.client.add_callback(
        #         Button(style=ButtonStyle.blue, label="Items", custom_id='items'),
        #         self.__on_items_click
        #     ))
        if DisplayCard.MOVES.value != card.value:
            firstRowBtns.append(Button(style=ButtonStyle.green, label="Moves", custom_id='moves'))
        if DisplayCard.STATS.value != card.value:
            firstRowBtns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
        if DisplayCard.DEX.value != card.value:
            firstRowBtns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))
        if authorIsTrainer:
            firstRowBtns.append(Button(style=ButtonStyle.blurple, label="Items", custom_id='items'))


            # Disable the "Set Active" button if the starter is currently the active pokemon
            # Disable the "Set Active" button if the starter is currently the active pokemon
            disabled = (activeId is not None) and (
                pokemon.trainerId == activeId)
            # firstRowBtns.append(self.client.add_callback(
            #     Button(style=ButtonStyle.blue, label="Set Active",
            #         custom_id='setactive', disabled=disabled),
            #     self.__on_set_active_click,
            # ))
            firstRowBtns.append(Button(style=ButtonStyle.blurple, label="Set Active", custom_id='setactive', disabled=disabled))

        btns = []
        if len(firstRowBtns) > 0:
            btns.append(firstRowBtns)

        return embed, btns

    @discord.ui.button(custom_id='moves', label='Moves', style=ButtonStyle.green)
    async def on_moves_click(self, interaction: discord.Interaction, button: Button):
        await self.__on_moves_click(interaction)

    @discord.ui.button(custom_id='stats', label='Stats', style=ButtonStyle.green)
    async def on_stats_click(self, interaction: discord.Interaction, button: Button):
        await self.__on_stats_click(interaction)

    @discord.ui.button(custom_id='pokedex', label='Pokedex', style=ButtonStyle.green)
    async def on_pokedex_click(self, interaction: discord.Interaction, button: Button):
        await self.__on_pokedex_click(interaction)

    @discord.ui.button(custom_id='items', label='Items', style=ButtonStyle.blurple)
    async def on_items_click(self, interaction: discord.Interaction, button: Button):
        await self.__on_items_click(interaction)

    @discord.ui.button(custom_id='setactive', label='Set Active', style=ButtonStyle.blurple)
    async def on_set_active_click(self, interaction: discord.Interaction, button: Button):
        await self.__on_set_active_click(interaction)