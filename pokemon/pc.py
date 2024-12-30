from __future__ import annotations
from re import L
import asyncio
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
from services.pokeclass import Pokemon as PokemonClass
from services.pokedexclass import pokedex as PokedexClass
from services.inventoryclass import inventory as InventoryClass
from models.state import PokemonState, DisplayCard

from .abcd import MixinMeta
from .functions import (createPokedexEntryEmbed, createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)
from .helpers import (getTrainerGivenPokemonName)


DiscordUser = Union[discord.Member,discord.User]


class PcMixin(MixinMeta):
    """PC"""


    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    # TODO: Apparently there is a limit of 5 buttons at a time
    @_trainer.command()
    async def pc(self, ctx: commands.Context, user: DiscordUser = None):
        author: DiscordUser = ctx.author

        if user is None:
            user = ctx.author

        trainer = TrainerClass(str(user.id))
        pokeList = trainer.getPokemon()
        # TODO: we should just get the ids since that's all we need
        active = trainer.getActivePokemon()

        pokeLength = len(pokeList)
        i = 0

        if pokeLength == 0:
            await ctx.reply(content=f'{user.display_name} does not have any Pokemon.')
            return

        state = PokemonState(str(user.id), None, DisplayCard.STATS, pokeList, active.trainerId, i)
        embed, btns = self.__pokemonPcCard(user, state, DisplayCard.STATS, author.id == user.id)

        # if interaction is None:
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

        if trainer.statuscode == 420:
            await interaction.response.send_message(trainer.message)
            return

        if trainer.statuscode == 96:
            await interaction.response.send_message('Something went wrong. Active pokemon not set.')
            return

        await interaction.channel.send(f'{user.display_name} set their active pokemon to {getTrainerGivenPokemonName(pokemon)}.')
        
        state.active = pokemon.trainerId
        embed, btns = self.__pokemonPcCard(user, state, state.card)

        message = await interaction.edit_original_response(embed=embed, view=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
        

    async def __on_next_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            msg = await interaction.response.send_message('This is not for you.', ephemeral=False)
            await asyncio.sleep(2)
            await msg.delete()
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

        embed, btns = self.__pokemonPcCard(user, state, DisplayCard.MOVES)

        message = await interaction.edit_original_response(embed=embed, view=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.MOVES, state.pokemon, state.active, state.idx))


    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonPcCard(user, state, DisplayCard.STATS)

        message = await interaction.edit_original_response(embed=embed, view=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.STATS, state.pokemon, state.active, state.idx))


    async def __on_pokemon_withdraw(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return
        
        state = self.getPokemonState(user)

        pokeList = state.pokemon
        idx = state.idx

        pokemon: PokemonClass = pokeList[idx]

        trainer = TrainerClass(str(user.id))
        trainer.withdraw(pokemon.trainerId)

        if trainer.statuscode == 420:
            await interaction.response.send_message(trainer.message)
            return
        
        if trainer.statuscode == 69:
            await interaction.response.send_message(f'{getTrainerGivenPokemonName(pokemon)} is now in your party.')
            return


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

        trainer.releasePokemon(pokemon.trainerId)

        # Send to logging channel
        await self.sendToLoggingChannel(f'{user.display_name} released {getTrainerGivenPokemonName(pokemon)}. {trainer.message}')

        # Send to message channel
        await interaction.channel.send(f'{user.display_name} released {getTrainerGivenPokemonName(pokemon)}. {trainer.message}', delete_after=5)
        pokeList = trainer.getPokemon()
        pokeLength = len(pokeList)

        state = PokemonState(str(user.id), state.messageId, state.card, pokeList, state.active, state.idx)
        self.setPokemonState(user, state)

        if i < pokeLength - 1:
            embed, btns = self.__pokemonPcCard(user, state, state.card)

            message = await interaction.edit_original_response(embed=embed, view=btns)
            
            self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, state.idx))
        else:
            await self.__on_prev_click(interaction)


    async def __on_items_back(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonPcCard(user, state, DisplayCard.STATS)

        message = await interaction.edit_original_response(embed=embed, view=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.STATS, state.pokemon, state.active, state.idx))


    
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
            button = Button(style=ButtonStyle.gray, label="Previous", custom_id='previous', row=0)
            button.callback = self.on_prev_click
            view.add_item(button)
        if i < pokeLength - 1:
            button = Button(style=ButtonStyle.gray, label="Next", custom_id='next', row=0)
            button.callback = self.on_next_click
            view.add_item(button)

        if inv.potion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.POTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Potion", custom_id='potion', row=1)
            button.callback = self.on_use_item
            view.add_item(button)
        if inv.superpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.SUPERPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Super Potion", custom_id='superpotion', row=1)
            button.callback = self.on_use_item
            view.add_item(button)
        if inv.hyperpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.HYPERPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Hyper Potion", custom_id='hyperpotion', row=1)
            button.callback = self.on_use_item
            view.add_item(button)
        if inv.maxpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.MAXPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Max Potion", custom_id='maxpotion', row=1)
            button.callback = self.on_use_item
            view.add_item(button)
        if inv.revive > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.REVIVE)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Revive", custom_id='revive', row=1)
            button.callback = self.on_use_item
            view.add_item(button)

        button = Button(style=ButtonStyle.gray, label="Back", custom_id='back', row=2)
        button.callback = self.on_items_back
        view.add_item(button)

        return embed, view


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
            button = Button(style=ButtonStyle.gray, label="Previous", custom_id='previous', row=0)
            button.callback = self.on_prev_click
            view.add_item(button)

        if i < pokeLength - 1:
            button = Button(style=ButtonStyle.gray, label="Next", custom_id='next', row=0)
            button.callback = self.on_next_click
            view.add_item(button)

        if authorIsTrainer:
            if DisplayCard.MOVES.value != card.value:
                button = Button(style=ButtonStyle.green, label="Moves", custom_id='moves', row=1)
                button.callback = self.on_moves_click
                view.add_item(button)
            if DisplayCard.STATS.value != card.value:
                button = Button(style=ButtonStyle.green, label="Stats", custom_id='stats', row=1)
                button.callback = self.on_stats_click
                view.add_item(button)
            if DisplayCard.DEX.value != card.value:
                button = Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex', row=1)
                button.callback = self.on_pokedex_click
                view.add_item(button)
            
            activeDisabled = (activeId is not None) and (pokemon.trainerId == activeId)

            button = Button(style=ButtonStyle.primary, label="Set Active", custom_id='active', disabled=activeDisabled, row=1)
            button.callback = self.on_set_active
            view.add_item(button)

            button = Button(style=ButtonStyle.red, label="Release", custom_id='release', disabled=activeDisabled, row=1)
            button.callback = self.on_release_click
            view.add_item(button)

        if authorIsTrainer:
            button = Button(style=ButtonStyle.green, label="Withdraw", custom_id='withdraw', row=2)
            button.callback = self.on_pokemon_withdraw
            view.add_item(button)

            button = Button(style=ButtonStyle.primary, label="Items", custom_id='items', row=2)
            button.callback = self.on_items_click
            view.add_item(button)

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

    @discord.ui.button(custom_id='withdraw', label='Withdraw', style=ButtonStyle.green)
    async def on_pokemon_withdraw(self, interaction: discord.Interaction):
        await self.__on_pokemon_withdraw(interaction)

    @discord.ui.button(custom_id='items', label='Items', style=ButtonStyle.primary)
    async def on_items_click(self, interaction: discord.Interaction):
        await self.__on_items_click(interaction)    

    # # TODO: Apparently there is a limit of 5 buttons at a time
    # @_trainer.command()
    # async def pc(self, ctx: commands.Context, user: Union[discord.Member,discord.User] = None):
    #     author: Union[discord.Member,discord.User] = ctx.author

    #     if user is None:
    #         user = ctx.author

    #     def nextBtnClick():
    #         return lambda x: x.custom_id == "next" or x.custom_id == 'previous' or x.custom_id == 'stats' or x.custom_id == 'pokedex' or x.custom_id == 'active'

    #     trainer = TrainerClass(str(user.id))
    #     pokeList = trainer.getPokemon()

    #     # TODO: we should just get the ids since that's all we need
    #     active = trainer.getActivePokemon()
    #     # starter = trainer.getStarterPokemon()

    #     interaction: Interaction = None
    #     pokeLength = len(pokeList)
    #     i = 0

    #     if pokeLength == 0:
    #         await ctx.reply(content=f'{user.display_name} does not have any Pokemon.')
    #         return

    #     # TODO: there is a better way to do this that doesn't involve a loop
    #     #       discord-components gives an example use case
    #     #       https://github.com/kiki7000/discord.py-components/blob/master/examples/paginator.py
    #     while True:
    #         try:
    #             pokemon: PokemonClass = pokeList[i]
    #             embed = createPokemonAboutEmbed(user, pokemon)
                
    #             firstRowBtns = []
    #             if i > 0:
    #                 firstRowBtns.append(Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'))
    #             if i < pokeLength - 1:
    #                 firstRowBtns.append(Button(style=ButtonStyle.gray, label="Next", custom_id='next'))

    #             secondRowBtns = []
    #             secondRowBtns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
    #             secondRowBtns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))

    #             activeDisabled = (active is not None) and (pokemon.trainerId == active.trainerId)
    #             secondRowBtns.append(Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=activeDisabled))
                
    #             # TODO: need to add the release button somewhere
    #             # # releaseDisabled = (active is not None and pokemon.id == active.id) or (starter is not None and pokemon.id == starter.id)
    #             # btns.append(Button(style=ButtonStyle.red, label="Release", custom_id='release'))

    #             if interaction is None:
    #                 await ctx.send(
    #                     embed=embed,
    #                     # file=file,
    #                     view=[firstRowBtns, secondRowBtns]
    #                 )
    #                 interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
    #             else:
    #                 await interaction.edit_original_response(
    #                     embed=embed,
    #                     # file=file,
    #                     view=[firstRowBtns, secondRowBtns]
    #                 )
    #                 interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                
    #             # Users who are not the author cannot click other users buttons
    #             if interaction.user.id != author.id:
    #                 await interaction.response.send_message('This is not for you.')
    #                 continue

    #             if interaction.custom_id == 'next':
    #                 i = i + 1
    #             if (interaction.custom_id == 'previous'):
    #                 i = i - 1
    #             if interaction.custom_id == 'active':
    #                 res = trainer.setActivePokemon(pokemon.trainerId)
    #                 await interaction.response.send_message(content=f'{res}')
    #                 break
    #             if interaction.custom_id == 'stats':
    #                 await interaction.response.send_message('Not implemented')
    #                 break
    #             if interaction.custom_id == 'pokedex':
    #                 await interaction.response.send_message('Not implemented')
    #                 break
    #         except asyncio.TimeoutError:
    #             break
