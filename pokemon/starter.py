from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord

from discord import ButtonStyle, Interaction
from discord.ui import Button, View

from redbot.core.commands.context import Context

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import os
import constant
from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass
from services.pokedexclass import pokedex as PokedexClass
from services.inventoryclass import inventory as InventoryClass
from models.state import PokemonState, DisplayCard
from .ui.intro_scene import start_intro_scene

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

        message: discord.Message = await ctx.send(embed=embed, view=btns)
        self.setPokemonState(author, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, None))

    @_trainer.command()
    async def delete(self, ctx: commands.Context) -> None:
        """Delete your trainer and all associated data. This action cannot be undone!"""
        user = ctx.author
        
        # Create confirmation embed
        embed = discord.Embed(
            title="⚠️ Delete Trainer Account",
            description=f"**{user.display_name}**, are you sure you want to delete your trainer account?\n\n"
                        f"This will permanently delete:\n"
                        f"• All your Pokémon\n"
                        f"• Your entire inventory\n"
                        f"• Your Pokédex progress\n"
                        f"• All trainer data\n\n"
                        f"**This action CANNOT be undone!**",
            color=discord.Color.red()
        )
        
        # Create view with Yes/No buttons
        view = View(timeout=60)  # 60 second timeout
        
        # Yes button (danger style)
        yes_button = Button(style=ButtonStyle.danger, label="Yes, Delete Everything", custom_id="confirm_delete")
        yes_button.callback = self._on_delete_confirm
        view.add_item(yes_button)
        
        # No button (secondary style)
        no_button = Button(style=ButtonStyle.secondary, label="No, Keep My Account", custom_id="cancel_delete")
        no_button.callback = self._on_delete_cancel
        view.add_item(no_button)
        
        # Send confirmation message
        message = await ctx.send(embed=embed, view=view)
        
        # Store message info for callbacks
        self._delete_confirmation_users = getattr(self, '_delete_confirmation_users', {})
        self._delete_confirmation_users[user.id] = message.id

    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: DiscordUser = None) -> None:
        """Show the starter pokemon for the trainer."""
        author = ctx.author

        if user is None:
            user = ctx.author

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))

        # Check if trainer already has a starter (check database directly, don't call getStarterPokemon yet)
        has_starter = False
        try:
            from services.dbclass import db as dbconn
            db = dbconn()
            queryString = 'SELECT "starterId" FROM trainer WHERE discord_id = %(discordId)s'
            result = db.querySingle(queryString, {'discordId': str(user.id)})
            if result and result[0] is not None:
                has_starter = True
            del db
        except:
            has_starter = False

        # If no starter yet, show intro scene
        if not has_starter:
            await self._show_intro_scene(ctx, user, trainer)
            return

        # If they have a starter, get it and display
        pokemon = trainer.getStarterPokemon()
        active = trainer.getActivePokemon()
        state = PokemonState(str(user.id), None, DisplayCard.STATS, [pokemon], active.trainerId, None)
        authorIsTrainer = user.id == state.discordId

        embed, btns = self.__pokemonSingleCard(user, state, state.card, authorIsTrainer)
        message: discord.Message = await ctx.send(embed=embed, view=btns)
        self.setPokemonState(author, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, None))

    async def _show_intro_scene(self, ctx: commands.Context, user: DiscordUser, trainer: TrainerClass):
        """Show the intro scene for new trainers"""
        
        # Define intro scenes - you can edit this easily!
        intro_scenes = [
            {
                'title': 'Welcome to the World of Pokémon!',
                'text': 'Hello there! Welcome to the wonderful world of Pokémon!\n\nMy name is Oak. People call me the Pokémon Professor.',
                'color': discord.Color.green(),
                'sprite_path': '/sprites/trainers/oak.png'
            },
            {
                'title': 'About Pokémon',
                'text': 'This world is inhabited by creatures called Pokémon.\n\nFor some people, Pokémon are pets. Others use them for battles.',
                'color': discord.Color.green(),
                'sprite_path': '/sprites/trainers/oak.png'
            },
            {
                'title': 'Your Journey Begins',
                'text': 'Certain Pokémon are of particular interest these days.\n\nYes. Vaporeon. No further questions.',
                'color': discord.Color.green(),
                'sprite_path': '/sprites/trainers/oak.png'
            },
            {
                'title': 'First things first',
                'text': 'What is your name?\n\nTry not to mess it up. This is permanent. Probably.',
                'color': discord.Color.green(),
                'prompt_name': True,
                'sprite_path': '/sprites/trainers/oak.png'
            },
            {
                'title': 'Not this guy',
                'text': 'This is your rival, Blue. He picked the starter\n\nthat\’s strong against yours. On purpose.',
                'color': discord.Color.green(),
                'sprite_path': '/sprites/trainers/blue.png'
            },
            {
                'title': 'Your journey begins now!',
                'text': 'Catch monsters. Beat your rival.\n\nDon\’t ask Oak about Vaporeon again.',
                'color': discord.Color.gold(),
                'sprite_path': '/sprites/trainers/oak.png'
            }
        ]
        
        
        # Start the intro scene
        await start_intro_scene(
            ctx, 
            user.id, 
            intro_scenes, 
            self._on_intro_complete
        )

    async def _on_intro_complete(self, interaction: Interaction, trainer_name: str):
        """Called when intro scene is complete"""
        user = interaction.user
        
        # Save trainer name to database
        trainer = TrainerClass(str(user.id))
        trainer.setTrainerName(trainer_name)
        
        # Get starter pokemon (this creates it if it doesn't exist)
        pokemon = trainer.getStarterPokemon()
        active = trainer.getActivePokemon()
        
        # Create the completion embed with pokemon sprite
        completion_embed = discord.Embed(
            title='🎉 You received your first Pokémon! 🎉',
            description=f'Congratulations, {trainer_name}! You received a **{pokemon.pokemonName.capitalize()}**!\n\nType `,play` or `,m` to begin your adventure!',
            color=discord.Color.gold()
        )
        
        # Add the pokemon sprite to the embed
        sprite_file = None
        try:
            from helpers.pathhelpers import get_sprite_path
            sprite_path = f"/sprites/pokemon/{pokemon.pokemonName}.png"
            full_sprite_path = get_sprite_path(sprite_path)
            
            if os.path.exists(full_sprite_path):
                filename = f"{pokemon.pokemonName}.png"
                sprite_file = discord.File(full_sprite_path, filename=filename)
                completion_embed.set_image(url=f"attachment://{filename}")
            else:
                # Fallback to URL
                sprite_url = f"https://pokesprites.joshkohut.com/sprites/pokemon/{pokemon.pokemonName}.png"
                completion_embed.set_image(url=sprite_url)
        except Exception as e:
            print(f"Error loading pokemon sprite: {e}")
            # Fallback to URL
            try:
                sprite_url = f"https://pokesprites.joshkohut.com/sprites/pokemon/{pokemon.pokemonName}.png"
                completion_embed.set_image(url=sprite_url)
            except:
                pass
        
        # Send completion message with sprite
        if sprite_file:
            await interaction.message.edit(embed=completion_embed, view=None, attachments=[sprite_file])
        else:
            await interaction.message.edit(embed=completion_embed, view=None)

    async def __on_moves_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()
        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.getPokemonState(user)

        # Check if author is trainer
        authorIsTrainer = user.id == state.discordId
        trainerUser: DiscordUser = user
        if not authorIsTrainer:
            ctx: Context = await self.bot.get_context(interaction.message)
            trainerUser = await ctx.guild.fetch_member(int(state.discordId))

        embed, btns = self.__pokemonSingleCard(trainerUser, state, DisplayCard.MOVES, authorIsTrainer)

        message = await interaction.message.edit(embed=embed, view=btns)


        self.setPokemonState(user, PokemonState(state.discordId, message.id, DisplayCard.MOVES, state.pokemon, state.active, None))
    

    async def __on_pokedex_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()
        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.getPokemonState(user)

        # Check if author is trainer
        authorIsTrainer = user.id == state.discordId
        trainerUser: DiscordUser = user
        if not authorIsTrainer:
            ctx: Context = await self.bot.get_context(interaction.message)
            trainerUser = await ctx.guild.fetch_member(int(state.discordId))

        embed, btns = self.__pokemonSingleCard(trainerUser, state, DisplayCard.DEX, authorIsTrainer)

        message = await interaction.message.edit(embed=embed, view=btns)
        self.setPokemonState(user, PokemonState(state.discordId, message.id, DisplayCard.DEX, state.pokemon, state.active, None))
    
    async def _on_delete_confirm(self, interaction: Interaction):
        """Handle confirmation of trainer deletion"""
        user = interaction.user
        
        # Check if this user has a pending deletion
        if not hasattr(self, '_delete_confirmation_users') or user.id not in self._delete_confirmation_users:
            await interaction.response.send_message("This confirmation is not for you or has expired.", ephemeral=True)
            return
        
        # Check if this is the right message
        if interaction.message.id != self._delete_confirmation_users[user.id]:
            await interaction.response.send_message("This confirmation is not for you or has expired.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Delete the trainer
        trainer = TrainerClass(str(user.id))
        result_message = trainer.deleteTrainer()
        
        # Create result embed
        if trainer.statuscode == 420:
            embed = discord.Embed(
                title="✅ Trainer Deleted",
                description=f"{result_message}\n\nYou can start fresh anytime by using `,trainer starter`!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Deletion Failed",
                description=f"An error occurred: {result_message}",
                color=discord.Color.red()
            )
        
        # Update the message
        await interaction.message.edit(embed=embed, view=None)
        
        # Clean up
        del self._delete_confirmation_users[user.id]

    async def _on_delete_cancel(self, interaction: Interaction):
        """Handle cancellation of trainer deletion"""
        user = interaction.user
        
        # Check if this user has a pending deletion
        if not hasattr(self, '_delete_confirmation_users') or user.id not in self._delete_confirmation_users:
            await interaction.response.send_message("This confirmation is not for you or has expired.", ephemeral=True)
            return
        
        # Check if this is the right message
        if interaction.message.id != self._delete_confirmation_users[user.id]:
            await interaction.response.send_message("This confirmation is not for you or has expired.", ephemeral=True)
            return
        
        # Create cancellation embed
        embed = discord.Embed(
            title="✅ Deletion Cancelled",
            description=f"{user.display_name}, your trainer account is safe!",
            color=discord.Color.blue()
        )
        
        # Update the message
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Clean up
        del self._delete_confirmation_users[user.id]

    async def __on_stats_click(self, interaction: Interaction):
        user = interaction.user
        await interaction.response.defer()
        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.getPokemonState(user)

        # Check if author is trainer
        authorIsTrainer = user.id == state.discordId
        trainerUser: DiscordUser = user
        if not authorIsTrainer:
            ctx: Context = await self.bot.get_context(interaction.message)
            trainerUser = await ctx.guild.fetch_member(int(state.discordId))

        embed, btns = self.__pokemonSingleCard(trainerUser, state, DisplayCard.STATS, authorIsTrainer)

        message = await interaction.message.edit(embed=embed, view=btns)


        self.setPokemonState(user, PokemonState(state.discordId, message.id, DisplayCard.STATS, state.pokemon, state.active, None))
    

    async def __on_set_active_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
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
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.getPokemonState(user)

        embed, btns = self.__pokemonSingleCard(user, state, DisplayCard.STATS)

        message = await interaction.message.edit(embed=embed, view=btns)
        
        self.setPokemonState(user, PokemonState(str(user.id), message.id, DisplayCard.STATS, state.pokemon, state.active, None))


    
    async def __on_use_item(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return
        
        state = self.getPokemonState(user)
        pokemon = state.pokemon[0]

        item = ''
        if interaction.data['custom_id'] == 'potion':
            item = 'potion'
        elif interaction.data['custom_id'] == 'superpotion':
            item = 'super-potion'
        elif interaction.data['custom_id'] == 'hyperpotion':
            item = 'hyper-potion'
        elif interaction.data['custom_id'] == 'maxpotion':
            item = 'max-potion'
        elif interaction.data['custom_id'] == 'revive':
            item = 'revive'

        trainer = TrainerClass(str(user.id))
        trainer.heal(pokemon.trainerId, item)

        if trainer.message:
            ctx = await self.bot.get_context(interaction.message)
            embed, btns = await self.__pokemonItemsCard(user, state, state.card, ctx)
            message = await interaction.message.edit(embed=embed, view=btns)
            self.setPokemonState(user, PokemonState(str(user.id), message.id, state.card, state.pokemon, state.active, None))
    
            await interaction.channel.send(f'{user.display_name}, {trainer.message}')
        else:
            await interaction.response.send_message('Could not use the item.')


    async def __on_items_click(self, interaction: Interaction):
        user = interaction.user

        if not self.checkPokemonState(user, interaction.message):
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return

        state = self.getPokemonState(user)

        ctx = await self.bot.get_context(interaction.message)

        embed, btns = await self.__pokemonItemsCard(user, state, DisplayCard.ITEMS, ctx)

        message = await interaction.message.edit(embed=embed, view=btns)
        
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

        view = View()
        if inv.potion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.POTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Potion", custom_id='potion', row=0)
            button.callback = self.on_use_item_starter
            view.add_item(button)
        if inv.superpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.SUPERPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Super Potion", custom_id='superpotion', row=0)
            button.callback = self.on_use_item_starter
            view.add_item(button)
        if inv.hyperpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.HYPERPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Hyper Potion", custom_id='hyperpotion', row=0)
            button.callback = self.on_use_item_starter
            view.add_item(button)
        if inv.maxpotion > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.MAXPOTION)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Max Potion", custom_id='maxpotion', row=0)
            button.callback = self.on_use_item_starter
            view.add_item(button)
        if inv.revive > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.REVIVE)
            button = Button(style=ButtonStyle.gray, emoji=emote, label="Revive", custom_id='revive', row=0)
            button.callback = self.on_use_item_starter
            view.add_item(button)

        button = Button(style=ButtonStyle.gray, label="Back", custom_id='back', row=1)
        button.callback = self.on_items_back_starter
        view.add_item(button)

        return embed, view


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

        if DisplayCard.MOVES.value != card.value:
            button = Button(style=ButtonStyle.green, label="Moves", custom_id='moves')
            button.callback = self.on_moves_click_starter
            firstRowBtns.append(button)
        if DisplayCard.STATS.value != card.value:
            button = Button(style=ButtonStyle.green, label="Stats", custom_id='stats')
            button.callback = self.on_stats_click_starter
            firstRowBtns.append(button)
        if DisplayCard.DEX.value != card.value:
            button = Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex')
            button.callback = self.on_pokedex_click_starter
            firstRowBtns.append(button)
        if authorIsTrainer:
            firstRowBtns.append(Button(style=ButtonStyle.blurple, label="Items", custom_id='items'))


            # Disable the "Set Active" button if the starter is currently the active pokemon
            disabled = (activeId is not None) and (
                pokemon.trainerId == activeId)

            button = Button(style=ButtonStyle.blurple, label="Set Active", custom_id='setactive', disabled=disabled)
            button.callback = self.on_set_active_click_starter
            firstRowBtns.append(button)

        btns = []
        if len(firstRowBtns) > 0:
            btns.append(firstRowBtns)
        
        view = View()
        for button in firstRowBtns:
            view.add_item(button)

        return embed, view

    @discord.ui.button(custom_id='moves', label='Moves', style=ButtonStyle.green)
    async def on_moves_click_starter(self, interaction: discord.Interaction):
        await self.__on_moves_click(interaction)

    @discord.ui.button(custom_id='stats', label='Stats', style=ButtonStyle.green)
    async def on_stats_click_starter(self, interaction: discord.Interaction):
        await self.__on_stats_click(interaction)

    @discord.ui.button(custom_id='pokedex', label='Pokedex', style=ButtonStyle.green)
    async def on_pokedex_click_starter(self, interaction: discord.Interaction):
        await self.__on_pokedex_click(interaction)

    @discord.ui.button(custom_id='items', label='Items', style=ButtonStyle.blurple)
    async def on_items_click_starter(self, interaction: discord.Interaction):
        await self.__on_items_click(interaction)

    @discord.ui.button(custom_id='setactive', label='Set Active', style=ButtonStyle.blurple)
    async def on_set_active_click_starter(self, interaction: discord.Interaction):
        await self.__on_set_active_click(interaction)

    @discord.ui.button(custom_id='back', label='Back', style=ButtonStyle.gray)
    async def on_items_back_starter(self, interaction: discord.Interaction):
        await self.__on_items_back(interaction)   

    @discord.ui.button(custom_id='potion', label='Potion', style=ButtonStyle.gray)
    async def on_use_item_starter(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)
    
    @discord.ui.button(custom_id='superpotion', label='Super Potion', style=ButtonStyle.gray)
    async def on_use_item_starter(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)

    @discord.ui.button(custom_id='hyperpotion', label='Hyper Potion', style=ButtonStyle.gray)
    async def on_use_item_starter(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)

    @discord.ui.button(custom_id='maxpotion', label='Max Potion', style=ButtonStyle.gray)
    async def on_use_item_starter(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)

    @discord.ui.button(custom_id='revive', label='Revive', style=ButtonStyle.gray)
    async def on_use_item_starter(self, interaction: discord.Interaction):
        await self.__on_use_item(interaction)