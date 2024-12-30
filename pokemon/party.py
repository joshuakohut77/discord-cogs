from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

from redbot.core.commands.context import Context


if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from services.trainerclass import trainer as TrainerClass
from services.pokedexclass import pokedex as PokedexClass
from services.pokeclass import Pokemon as PokemonClass
from services.inventoryclass import inventory as InventoryClass
from models.state import PokemonState, DisplayCard

from .abcd import MixinMeta
from .functions import (createStatsEmbed, createPokedexEntryEmbed,
                        createPokemonAboutEmbed)
from .helpers import (getTrainerGivenPokemonName)


DiscordUser = Union[discord.Member,discord.User]


class PartyMixin(MixinMeta):
    """Party"""


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    # TODO: Apparently there is a limit of 5 buttons at a time
    @_trainer.command()
    async def party(self, ctx: commands.Context, user: Union[discord.Member,discord.User] = None):
        author: DiscordUser = ctx.author

        if user is None:
            user = ctx.author

        trainer = TrainerClass(str(user.id))
        pokeList = trainer.getPokemon(party=True)
        # TODO: we should just get the ids since that's all we need
        active = trainer.getActivePokemon()

        pokeLength = len(pokeList)
        i = 0

        if pokeLength == 0:
            await ctx.reply(content=f'{user.display_name} does not have any Pokemon.')
            return

        state = PokemonState(str(user.id), None, DisplayCard.STATS, pokeList, active.trainerId, i)
        embed, btns = self.__pokemonPcCard(user, state, DisplayCard.STATS, author.id == user.id)

        message = await ctx.send(
            embed=embed,
            view=btns
        )
        self.setPokemonState(author, PokemonState(str(user.id), message.id, DisplayCard.STATS, pokeList, active.trainerId, i))

    
    async def __on_set_active(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)
        pokemon: PokemonClass = state.pokemon[state.idx]

        trainer = TrainerClass(str(user.id))
        trainer.setActivePokemon(pokemon.trainerId)

        await interaction.channel.send(f'{user.display_name} set their active pokemon to {getTrainerGivenPokemonName(pokemon)}.')
        
        state.active = pokemon.trainerId
        embed, components = self.__pokemonPcCard(user, state, state.card)

        message = await interaction.edit_original_response(embed=embed, view=components)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
        

    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)
        state.idx = state.idx + 1

        if DisplayCard.ITEMS.value == state.card.value:
            ctx = await self.bot.get_context(interaction.message)
            embed, btns = await self.__pokemonItemsCard(user, state, DisplayCard.ITEMS, ctx)
            message = await interaction.edit_original_response(embed=embed, view=btns)
            self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
        else:
            authorIsTrainer = str(user.id) == state.discordId

            trainerUser: DiscordUser = user
            if not authorIsTrainer:
                ctx: Context = await self.bot.get_context(interaction.message)
                trainerUser = await ctx.guild.fetch_member(int(state.discordId))

            embed, btns = self.__pokemonPcCard(trainerUser, state, state.card, authorIsTrainer)
            message = await interaction.edit_original_response(embed=embed, view=btns)
            self.setPokemonState(user, PokemonState(state.discordId, message.id, state.card, state.pokemon, state.active, state.idx))
    
    

    async def __on_prev_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)
        state.idx = state.idx - 1

        if DisplayCard.ITEMS.value == state.card.value:
            ctx = await self.bot.get_context(interaction.message)
            embed, btns = await self.__pokemonItemsCard(user, state, DisplayCard.ITEMS, ctx)
            message = await interaction.edit_original_response(embed=embed, view=btns)
            self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
        else:
            authorIsTrainer = str(user.id) == state.discordId

            trainerUser: DiscordUser = user
            if not authorIsTrainer:
                ctx: Context = await self.bot.get_context(interaction.message)
                trainerUser = await ctx.guild.fetch_member(int(state.discordId))

            embed, btns = self.__pokemonPcCard(trainerUser, state, state.card, authorIsTrainer)
            message = await interaction.edit_original_response(embed=embed, view=btns)
            self.setPokemonState(user, PokemonState(state.discordId, message.id, state.card, state.pokemon, state.active, state.idx))


    async def __on_moves_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, firstRow, secondRow = self.__pokemonPcCard(user, state, DisplayCard.MOVES)

        message = await interaction.edit_original_response(embed=embed, view=[firstRow, secondRow])
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.MOVES, state.pokemon, state.active, state.idx))


    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, components = self.__pokemonPcCard(user, state, DisplayCard.STATS)

        message = await interaction.edit_original_response(embed=embed, view=components)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.STATS, state.pokemon, state.active, state.idx))


    async def __on_pokemon_deposit(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return
        
        state = self.getPokemonState(user)

        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx

        pokemon: PokemonClass = pokeList[i]

        trainer = TrainerClass(str(user.id))
        trainer.deposit(pokemon.trainerId)

        if trainer.statuscode == 420:
            await interaction.response.send_message(trainer.message)
            return
        
        if trainer.statuscode == 69:
            await interaction.channel.send(f'{user.display_name} returned {getTrainerGivenPokemonName(pokemon)} to their pc.')

            pokeList = trainer.getPokemon(party=True)
            pokeLength = len(pokeList)
            self.setPokemonState(user, PokemonState(str(user.id), state.messageId, state.card, pokeList, state.active, state.idx))

            if pokeLength == 1:
                state.pokemon = pokeList
                state.idx = 0

                embed, components = self.__pokemonPcCard(user, state, state.card)
                message = await interaction.edit_original_response(embed=embed, view=components)
                
                self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
            elif i < pokeLength - 1:
                await self.__on_next_click(interaction)
            else:
                await self.__on_prev_click(interaction)
        

    
    async def __on_pokedex_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonPcCard(user, state, DisplayCard.DEX)

        message = await interaction.edit_original_response(embed=embed, view=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.DEX, state.pokemon, state.active, state.idx))



    async def __on_release_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return
        
        state = self.getPokemonState(user)

        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx
        activeId = state.active

        pokemon: PokemonClass = pokeList[i]

        if pokemon.trainerId == activeId:
            await interaction.response.send_message('You cannot release your active pokemon.')
            return

        trainer = TrainerClass(str(user.id))
        starter = trainer.getStarterPokemon()

        if pokemon.trainerId == starter.trainerId:
            await interaction.response.send_message('You cannot release your starter pokemon.')
            return

        # pokemon.release()
        trainer.releasePokemon(pokemon.trainerId)

        # Send to logging channel
        await self.sendToLoggingChannel(f'{user.display_name} released {getTrainerGivenPokemonName(pokemon)}')

        # Send to message channel
        await interaction.channel.send(f'{user.display_name} released {getTrainerGivenPokemonName(pokemon)}. {trainer.message}', delete_after=5)
        pokeList = trainer.getPokemon()
        pokeLength = len(pokeList)
        self.setPokemonState(user, PokemonState(str(user.id), state.messageId, state.card, pokeList, state.active, state.idx))

        if i < pokeLength - 1:
            await self.__on_next_click(interaction)
        else:
            await self.__on_prev_click(interaction)


    async def __on_use_item(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return
        
        state = self.getPokemonState(user)
        pokemon = state.pokemon[state.idx]

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
            message = await interaction.edit_original_response(embed=embed, view=btns)
            self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
    
            await interaction.channel.send(f'{user.display_name}, {trainer.message}')
        else:
            await interaction.response.send_message('Could not use the item.')


    async def __on_items_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)

        ctx = await self.bot.get_context(interaction.message)

        embed, btns = await self.__pokemonItemsCard(user, state, DisplayCard.ITEMS, ctx)

        message = await interaction.edit_original_response(embed=embed, view=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.ITEMS, state.pokemon, state.active, state.idx))


    async def __on_items_back(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonPcCard(user, state, DisplayCard.STATS)

        message = await interaction.edit_original_response(embed=embed, view=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.STATS, state.pokemon, state.active, state.idx))



    async def __pokemonItemsCard(self, user: discord.User, state: PokemonState, card: DisplayCard, ctx: Context):
        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx

        pokemon: PokemonClass = pokeList[i]

        # Kind of a hack, but if the property is still set to None,
        # then we probably haven't loaded this pokemon yet.
        if pokemon.pokemonName is None:
            pokemon.load(pokemonId=pokemon.trainerId)


        embed: discord.Embed

        if DisplayCard.STATS.value == card.value or DisplayCard.ITEMS.value == card.value:
            embed = createStatsEmbed(user, pokemon)
        elif DisplayCard.MOVES.value == card.value:
            embed = createPokemonAboutEmbed(user, pokemon)
        else:
            dex = PokedexClass.getPokedexEntry(pokemon)
            embed = createPokedexEntryEmbed(user, pokemon, dex)

        embed.set_footer(text=f'''
--------------------
{i + 1} / {pokeLength}
        ''')
        
        
        inv = InventoryClass(str(user.id))
        
        view = View()
        if i > 0:
            button = Button(style=ButtonStyle.gray, label="Previous", custom_id='previous')
            button.callback = self.on_prev_click
            view.add_item(button, row=0)
        if i < pokeLength - 1:
            button = Button(style=ButtonStyle.gray, label="Next", custom_id='next')
            button.callback = self.on_next_click
            view.add_item(button, row=0)

        if inv.potion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.POTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Potion", custom_id='potion')
            button.callback = self.on_use_item
            view.add_item(button, row=1)
        if inv.superpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.SUPERPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Super Potion", custom_id='superpotion')
            button.callback = self.on_use_item
            view.add_item(button, row=1)
        if inv.hyperpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.HYPERPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Hyper Potion", custom_id='hyperpotion')
            button.callback = self.on_use_item
            view.add_item(button, row=1)
        if inv.maxpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.MAXPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Max Potion", custom_id='maxpotion')
            button.callback = self.on_use_item
            view.add_item(button, row=1)
        if inv.revive > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.REVIVE)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Revive", custom_id='revive')
            button.callback = self.on_use_item
            view.add_item(button, row=1)

        button = Button(style=ButtonStyle.gray, label="Back", custom_id='back')
        button.callback = self.on_items_back
        view.add_item(button, row=2)

        return embed, view

    @discord.ui.button(custom_id='previous', label='Previous', style=ButtonStyle.gray)
    async def on_prev_click(self, interaction: discord.Interaction):
        await self.__on_prev_click(interaction)
    
    @discord.ui.button(custom_id='next', label='Next', style=ButtonStyle.gray)
    async def on_next_click(self, interaction: discord.Interaction):
        await self.__on_next_click(interaction)
    
    @discord.ui.button(custom_id='potion', label='Potion', style=ButtonStyle.gray)
    async def on_use_item(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)
    
    @discord.ui.button(custom_id='superpotion', label='Super Potion', style=ButtonStyle.gray)
    async def on_use_item(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)

    @discord.ui.button(custom_id='hyperpotion', label='Hyper Potion', style=ButtonStyle.gray)
    async def on_use_item(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)

    @discord.ui.button(custom_id='maxpotion', label='Max Potion', style=ButtonStyle.gray)
    async def on_use_item(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)

    @discord.ui.button(custom_id='revive', label='Revive', style=ButtonStyle.gray)
    async def on_use_item(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)

    def __pokemonPcCard(self, user: discord.User, state: PokemonState, card: DisplayCard, authorIsTrainer: bool = True):
        pokeList = state.pokemon
        pokeLength = len(pokeList)
        i = state.idx
        activeId = state.active

        pokemon: PokemonClass = pokeList[i]

        # Kind of a hack, but if the property is still set to None,
        # then we probably haven't loaded this pokemon yet.
        if pokemon.pokemonName is None:
            pokemon.load(pokemonId=pokemon.trainerId)


        embed: discord.Embed

        if DisplayCard.STATS.value == card.value:
            embed = createStatsEmbed(user, pokemon)
        elif DisplayCard.MOVES.value == card.value:
            embed = createPokemonAboutEmbed(user, pokemon)
        else:
            dex = PokedexClass.getPokedexEntry(pokemon)
            embed = createPokedexEntryEmbed(user, pokemon, dex)

        embed.set_footer(text=f'''
--------------------
{i + 1} / {pokeLength}
        ''')
        
        view = View()
        if i > 0:
            button = Button(style=ButtonStyle.gray, label="Previous", custom_id='previous')
            button.callback = self.on_prev_click
            view.add_item(button, row=0)

        if i < pokeLength - 1:
            button = Button(style=ButtonStyle.gray, label="Next", custom_id='next')
            button.callback = self.on_next_click
            view.add_item(button, row=0)

        if authorIsTrainer:
            if DisplayCard.MOVES.value != card.value:
                button = Button(style=ButtonStyle.green, label="Moves", custom_id='moves')
                button.callback = self.on_moves_click
                view.add_item(button, row=1)
            if DisplayCard.STATS.value != card.value:
                button = Button(style=ButtonStyle.green, label="Stats", custom_id='stats')
                button.callback = self.on_stats_click
                view.add_item(button, row=1)
            if DisplayCard.DEX.value != card.value:
                button = Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex')
                button.callback = self.on_pokedex_click
                view.add_item(button, row=1)
            
            activeDisabled = (activeId is not None) and (pokemon.trainerId == activeId)

            button = Button(style=ButtonStyle.primary, label="Set Active", custom_id='active', disabled=activeDisabled)
            button.callback = self.on_set_active
            view.add_item(button, row=1)

            button = Button(style=ButtonStyle.red, label="Release", custom_id='release', disabled=activeDisabled)
            button.callback = self.on_release_click
            view.add_item(button, row=1)

        if authorIsTrainer:
            button = Button(style=ButtonStyle.green, label="Deposit", custom_id='deposit')
            button.callback = self.on_pokemon_deposit
            view.add_item(button, row=2)

            button = Button(style=ButtonStyle.primary, label="Items", custom_id='items')
            button.callback = self.on_items_click
            view.add_item(button, row=2)

        return embed, view

    @discord.ui.button(custom_id='moves', label='Moves', style=ButtonStyle.green)
    async def on_moves_click(self, interaction: discord.Interaction):
        await self.__on_moves_click(interaction)

    @discord.ui.button(custom_id='stats', label='Stats', style=ButtonStyle.green)
    async def on_stats_click(self, interaction: discord.Interaction):
        await self.__on_stats_click(interaction)

    @discord.ui.button(custom_id='pokedex', label='Pokedex', style=ButtonStyle.green)
    async def on_pokedex_click(self, interaction: discord.Interaction):
        await self.__on_pokedex_click(interaction)

    @discord.ui.button(custom_id='active', label='Set Active', style=ButtonStyle.primary)
    async def on_set_active(self, interaction: discord.Interaction):
        await self.__on_set_active(interaction)

    @discord.ui.button(custom_id='release', label='Release', style=ButtonStyle.red)
    async def on_release_click(self, interaction: discord.Interaction):
        await self.__on_release_click(interaction)

    @discord.ui.button(custom_id='deposit', label='Deposit', style=ButtonStyle.green)
    async def on_pokemon_deposit(self, interaction: discord.Interaction):
        await self.__on_pokemon_deposit(interaction)

    @discord.ui.button(custom_id='items', label='Items', style=ButtonStyle.primary)
    async def on_items_click(self, interaction: discord.Interaction):
        await self.__on_items_click(interaction)                