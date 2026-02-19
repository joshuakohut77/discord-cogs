from __future__ import annotations
from typing import Union, TYPE_CHECKING

import discord
from discord import Interaction, ButtonStyle, SelectOption
from discord.ui import Button, View, Select, Modal

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands
from redbot.core.commands.context import Context

from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass
from services.pokedexclass import pokedex as PokedexClass
from services.leaderboardclass import leaderboard as LeaderboardClass

from .abcd import MixinMeta
from .functions import get_pokemon_display_name
from .helpers.pathhelpers import load_json_config

DiscordUser = Union[discord.Member, discord.User]

class NicknameModal(Modal, title="Set Pokemon Nickname"):
    def __init__(self, pokemon):
        super().__init__()
        self.pokemon = pokemon
        
        current_nick = pokemon.nickName if pokemon.nickName else ""
        
        self.nickname_input = discord.ui.TextInput(
            label="Nickname",
            placeholder=f"Enter nickname for {pokemon.pokemonName.capitalize()}",
            default=current_nick,
            required=False,
            max_length=20,
            style=discord.TextStyle.short
        )
        self.add_item(self.nickname_input)
        
        self.clear_input = discord.ui.TextInput(
            label='Type "CLEAR" to remove nickname',
            placeholder="Leave blank to set nickname above",
            required=False,
            max_length=5,
            style=discord.TextStyle.short
        )
        self.add_item(self.clear_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        nickname = self.nickname_input.value.strip()
        clear_text = self.clear_input.value.strip().upper()
        
        if clear_text == "CLEAR":
            self.pokemon.nickName = None
            self.pokemon.save()
            
            embed = discord.Embed(
                title="✅ Nickname Cleared",
                description=f"**{self.pokemon.pokemonName.capitalize()}** no longer has a nickname.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if nickname:
            self.pokemon.nickName = nickname
            self.pokemon.save()
            
            embed = discord.Embed(
                title="✅ Nickname Set",
                description=f"**{self.pokemon.pokemonName.capitalize()}** is now nicknamed **{nickname}**!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ No Change",
                description="No nickname entered.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AdminMixin(MixinMeta):
    """Admin-only commands for managing trainers and Pokemon"""

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user)."""
        pass

    @_trainer.command(name="nickname")
    async def trainer_nickname(self, ctx):
        """Set or clear nicknames for your Pokemon"""
        user = ctx.author
        trainer = self._get_trainer(str(user.id))
        
        party = trainer.getPokemon(party=True)
        if not party:
            await ctx.send("You don't have any Pokemon in your party!")
            return
        
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
        
        options = []
        for i, poke in enumerate(party):
            display_name = get_pokemon_display_name(poke)
            current_nickname = f" (nicknamed)" if poke.nickName else ""
            label = f"{display_name} - Lv.{poke.currentLevel}{current_nickname}"
            options.append(SelectOption(
                label=label[:100],
                value=str(poke.trainerId),
                description=f"Species: {poke.pokemonName.capitalize()}"
            ))
        
        select = Select(
            placeholder="Choose a Pokemon to nickname...",
            options=options,
            custom_id="nickname_select"
        )
        
        view = View(timeout=180)
        
        async def select_callback(interaction: discord.Interaction):
            if interaction.user.id != user.id:
                await interaction.response.send_message("This isn't your Pokemon!", ephemeral=True)
                return
            
            selected_trainer_id = int(select.values[0])
            
            selected_poke = None
            for poke in party:
                if poke.trainerId == selected_trainer_id:
                    selected_poke = poke
                    break
            
            if not selected_poke:
                await interaction.response.send_message("Pokemon not found!", ephemeral=True)
                return
            
            await interaction.response.send_modal(NicknameModal(selected_poke))
        
        select.callback = select_callback
        view.add_item(select)
        
        cancel_btn = Button(style=ButtonStyle.secondary, label="❌ Cancel", custom_id="nickname_cancel")
        async def cancel_callback(interaction: discord.Interaction):
            if interaction.user.id != user.id:
                await interaction.response.send_message("This isn't for you!", ephemeral=True)
                return
            await interaction.message.delete()
        
        cancel_btn.callback = cancel_callback
        view.add_item(cancel_btn)
        
        embed = discord.Embed(
            title="🏷️ Pokemon Nickname Manager",
            description="Select a Pokemon from your party to set or change its nickname.",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed, view=view)

    @_trainer.command(name="gift")
    @commands.is_owner()
    async def gift_pokemon(
        self, 
        ctx: commands.Context, 
        user: DiscordUser, 
        pokemon_name: str, 
        level: int = 5
    ) -> None:
        """
        [ADMIN ONLY] Gift a Pokemon to a trainer.
        
        Usage: [p]trainer gift @user <pokemon_name> <level>
        Example: [p]trainer gift @Legend pikachu 25
        
        Args:
            user: The Discord user to gift the Pokemon to
            pokemon_name: Name of the Pokemon (e.g., pikachu, charizard)
            level: Level of the Pokemon (1-100, default: 5)
        """
        # Validate level
        if level < 1 or level > 100:
            await ctx.send("❌ Level must be between 1 and 100.")
            return
        
        # Normalize pokemon name to lowercase
        pokemon_name = pokemon_name.lower()
        
        # Validate Pokemon exists in config
        try:
            pokemon_config = load_json_config('pokemon.json')
            
            # pokemon.json is structured as: {"pokemon_name": {data}, ...}
            if pokemon_name not in pokemon_config:
                await ctx.send(f"❌ Pokemon '{pokemon_name}' not found in database.")
                return
                
        except Exception as e:
            await ctx.send(f"❌ Error loading Pokemon data: {str(e)}")
            return
        
        # Create trainer object to check party size
        trainer = TrainerClass(str(user.id))
        party_count = trainer.getPartySize()
        
        # Create the Pokemon
        try:
            pokemon = PokemonClass(str(user.id), pokemon_name)
            pokemon.create(level)
            
            # Set ownership and party status
            pokemon.discordId = str(user.id)
            pokemon.party = party_count < 6  # Add to party if space, otherwise to PC
            
            # Save the Pokemon
            pokemon.save()
            
            if pokemon.statuscode == 96:
                await ctx.send(f"❌ Error creating Pokemon: {pokemon.message}")
                return
            
            # Register to Pokedex
            PokedexClass(str(user.id), pokemon)
            
            
        except Exception as e:
            await ctx.send(f"❌ Error creating Pokemon: {str(e)}")
            return
        
        # Success message
        location = "party" if party_count < 6 else "PC"
        display_name = pokemon.pokemonName.capitalize()
        
        embed = discord.Embed(
            title="🎁 Pokemon Gifted!",
            description=f"**{display_name}** (Level {level}) has been gifted to {user.mention}!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Location",
            value=f"Added to {location}",
            inline=True
        )
        
        embed.add_field(
            name="Trainer ID",
            value=pokemon.trainerId,
            inline=True
        )
        
        # Add Pokemon sprite if available
        if pokemon.frontSpriteURL:
            embed.set_thumbnail(url=pokemon.frontSpriteURL)
        
        embed.set_footer(text=f"Gifted by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @_trainer.command(name="setlevel")
    @commands.is_owner()
    async def set_level(
        self, 
        ctx: commands.Context, 
        user: DiscordUser, 
        trainer_id: int, 
        new_level: int
    ) -> None:
        """
        [ADMIN ONLY] Set a Pokemon's level for a trainer.
        
        Usage: [p]trainer setlevel @user <trainer_id> <new_level>
        Example: [p]trainer setlevel @Legend 12345 50
        
        Args:
            user: The Discord user who owns the Pokemon
            trainer_id: The trainer ID of the Pokemon (from party/PC)
            new_level: New level to set (1-100)
        """
        # Validate level
        if new_level < 1 or new_level > 100:
            await ctx.send("❌ Level must be between 1 and 100.")
            return
        
        # Get the Pokemon
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getPokemonById(trainer_id)
        
        if not pokemon:
            await ctx.send(f"❌ Pokemon with trainer ID {trainer_id} not found for {user.mention}.")
            return
        
        # Load the Pokemon
        pokemon.load(pokemonId=trainer_id)
        old_level = pokemon.currentLevel
        
        # Set new level (this will recalculate stats)
        pokemon.currentLevel = new_level
        
        # Recalculate stats based on new level
        stats = pokemon.getPokeStats()
        pokemon.currentHP = min(pokemon.currentHP, stats['hp'])  # Don't exceed new max HP
        
        # Save changes
        pokemon.save()
        
        if pokemon.statuscode == 96:
            await ctx.send(f"❌ Error updating Pokemon: {pokemon.message}")
            return
        
        # Success message
        display_name = pokemon.nickName if pokemon.nickName else pokemon.pokemonName.capitalize()
        
        embed = discord.Embed(
            title="📊 Pokemon Level Updated",
            description=f"**{display_name}**'s level has been changed!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Owner",
            value=user.mention,
            inline=True
        )
        
        embed.add_field(
            name="Level Change",
            value=f"{old_level} → {new_level}",
            inline=True
        )
        
        embed.add_field(
            name="Trainer ID",
            value=trainer_id,
            inline=True
        )
        
        # Add Pokemon sprite if available
        if pokemon.frontSpriteURL:
            embed.set_thumbnail(url=pokemon.frontSpriteURL)
        
        embed.set_footer(text=f"Updated by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @_trainer.command(name="givebadge")
    @commands.is_owner()
    async def give_badge(
        self, 
        ctx: commands.Context, 
        user: DiscordUser, 
        badge_name: str
    ) -> None:
        """
        [ADMIN ONLY] Give a gym badge to a trainer.
        
        Usage: [p]trainer givebadge @user <badge_name>
        Example: [p]trainer givebadge @Legend boulder
        
        Valid badges: boulder, cascade, thunder, rainbow, soul, marsh, volcano, earth
        
        Args:
            user: The Discord user to give the badge to
            badge_name: Name of the badge (case-insensitive)
        """
        # Normalize badge name
        badge_name = badge_name.lower()
        
        # Valid badge list
        valid_badges = [
            'boulder', 'cascade', 'thunder', 'rainbow', 
            'soul', 'marsh', 'volcano', 'earth'
        ]
        
        if badge_name not in valid_badges:
            await ctx.send(f"❌ Invalid badge name. Valid badges: {', '.join(valid_badges)}")
            return
        
        # Load trainer
        trainer = TrainerClass(str(user.id))
        
        # Check if already has badge
        badge_attr = f'{badge_name}badge'
        if getattr(trainer, badge_attr, False):
            await ctx.send(f"ℹ️ {user.mention} already has the {badge_name.capitalize()} Badge.")
            return
        
        # Give the badge
        setattr(trainer, badge_attr, True)
        trainer.save()
        
        if trainer.statuscode == 96:
            await ctx.send(f"❌ Error giving badge: {trainer.message}")
            return
        
        # Success message
        embed = discord.Embed(
            title="🏆 Badge Awarded!",
            description=f"{user.mention} has been awarded the **{badge_name.capitalize()} Badge**!",
            color=discord.Color.gold()
        )
        
        # Count total badges
        badge_count = sum([
            getattr(trainer, f'{b}badge', False) 
            for b in valid_badges
        ])
        
        embed.add_field(
            name="Total Badges",
            value=f"{badge_count}/8",
            inline=True
        )
        
        embed.set_footer(text=f"Awarded by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @gift_pokemon.error
    async def gift_pokemon_error(self, ctx: commands.Context, error):
        """Error handler for gift command"""
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ This command can only be used by the bot owner.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}\n\n"
                          f"Usage: `{ctx.prefix}trainer gift @user <pokemon_name> <level>`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {str(error)}")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")

    @set_level.error
    async def set_level_error(self, ctx: commands.Context, error):
        """Error handler for setlevel command"""
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ This command can only be used by the bot owner.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}\n\n"
                          f"Usage: `{ctx.prefix}trainer setlevel @user <trainer_id> <new_level>`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {str(error)}")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")

    @give_badge.error
    async def give_badge_error(self, ctx: commands.Context, error):
        """Error handler for givebadge command"""
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ This command can only be used by the bot owner.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}\n\n"
                          f"Usage: `{ctx.prefix}trainer givebadge @user <badge_name>`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {str(error)}")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
    
    @_trainer.command(name="seterrorlog")
    @commands.is_owner()
    async def set_error_log_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """
        [ADMIN ONLY] Set or clear the channel for error log output.
        
        Usage: ,trainer seterrorlog #channel
        Usage: ,trainer seterrorlog  (no channel = clear)
        """
        if channel:
            await self.config.guild(ctx.guild).error_log_channel.set(channel.id)
            await ctx.send(f"✅ Error logs will be sent to {channel.mention}")
        else:
            await self.config.guild(ctx.guild).error_log_channel.set(None)
            await ctx.send("✅ Error log channel cleared.")
    
    @_trainer.command()
    @commands.admin_or_permissions(manage_roles=True)
    async def setrole(self, ctx: commands.Context, role: discord.Role = None) -> None:
        """Set the role to auto-assign when a new trainer picks their starter.
        
        Usage: [p]trainer setrole @Role
        Use without a role to clear the setting: [p]trainer setrole
        """
        if role is None:
            await self.config.guild(ctx.guild).trainer_role.set(None)
            await ctx.send("✅ Trainer role cleared. No role will be assigned to new trainers.")
            return

        # Check if the bot can assign this role
        if role >= ctx.guild.me.top_role:
            await ctx.send("❌ I can't assign that role — it's higher than or equal to my highest role.")
            return

        await self.config.guild(ctx.guild).trainer_role.set(role.id)
        await ctx.send(f"✅ New trainers will now receive the **{role.name}** role when they pick their starter.")