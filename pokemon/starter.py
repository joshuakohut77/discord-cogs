from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING
from abc import ABCMeta
# import random

import discord
from discord import (Embed, Member)
from discord_components import (DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

from pokebase.loaders import pokedex


if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import Config, commands
from .abcd import MixinMeta

from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass


NORMAL_GREY = 0xa8a77d
GRASS_GREEN = 0x77bb41
BUG_GREEN = 0xabb642
WATER_BLUE = 0x6f91e9
FIRE_RED = 0xe28544
ELECTRIC_YELLOW = 0xf2ca54
ROCK_BROWN = 0xb5a04b
GROUND_BROWN = 0xdbc075
PSYCHIC_PINK = 0xe66488
GHOST_PURPLE = 0x6c5a94
FIGHTING_RED = 0xb13c31
POISON_PURPLE = 0x94499b
FLYING_PURPLE = 0xa393ea
STEEL_GREY = 0xb8b8ce
ICE_BLUE = 0xa5d6d7
DRAGON_PURPLE = 0x6745ef
DARK_BROWN = 0x6c594a
FAIRY_PINK = 0xe29dac

def getTypeColor(type: str) -> discord.Colours:
    color = discord.colour.Color.dark_gray()

    if 'normal' in type:
        color = discord.Colour(NORMAL_GREY)
    elif 'grass' in type:
        color = discord.Colour(GRASS_GREEN)
        pass
    elif 'bug' in type:
        color = discord.Colour(BUG_GREEN)
    elif 'water' in type:
        color = discord.Colour(WATER_BLUE)
    elif 'fire' in type:
        color = discord.Colour(FIRE_RED)
    elif 'electric' in type:
        color = discord.Colour(ELECTRIC_YELLOW)
    elif 'rock' in type:
        color = discord.Colour(ROCK_BROWN)
    elif 'ground' in type:
        color = discord.Colour(GROUND_BROWN)
    elif 'psychic' in type:
        color = discord.Colour(PSYCHIC_PINK)
    elif 'ghost' in type:
        color = discord.Colour(GHOST_PURPLE)
    elif 'fighting' in type:
        color = discord.Colour(FIGHTING_RED)
    elif 'poison' in type:
        color = discord.Colour(POISON_PURPLE)
    elif 'flying' in type:
        color = discord.Colour(FLYING_PURPLE)
    elif 'steel' in type:
        color = discord.Colour(STEEL_GREY)
    elif 'ice' in type:
        color = discord.Colour(ICE_BLUE)
    elif 'dragon' in type:
        color = discord.Colour(DRAGON_PURPLE)
    elif 'dark' in type:
        color = discord.Colour(DARK_BROWN)
    elif 'fairy' in type:
        color = discord.Colour(FAIRY_PINK)
    return color

def createPokemonEmbedWithUrl(user: Member, pokemon: PokemonClass) -> Embed:
    stats = pokemon.getPokeStats()
    color = getTypeColor(pokemon.type1)

    # Create the embed object
    embed = discord.Embed(title=f"#{pokemon.trainerId}  {pokemon.pokemonName.capitalize()}", color=color)
    embed.set_author(name=f"{user.display_name}",
                    icon_url=str(user.avatar_url))
    
    types = pokemon.type1
    if pokemon.type2 is not None:
        types += ', ' + pokemon.type2
        
    embed.add_field(
        name="Type", value=f"{types}", inline=True)
    
    if pokemon.nickName is not None:
        embed.add_field(
            name="Nickname", value=f"{pokemon.nickName}", inline=False)
    
    embed.add_field(
        name="Level", value=f"{pokemon.currentLevel}", inline=False)
    embed.add_field(
        name="HP", value=f"{pokemon.currentHP} / {stats['hp']}", inline=False)
    embed.add_field(
        name="Attack", value=f"{stats['attack']}", inline=True)
    embed.add_field(
        name="Defense", value=f"{stats['defense']}", inline=True)

    embed.set_thumbnail(url=pokemon.frontSpriteURL)
    return embed



class StarterMixin(MixinMeta):
    """Starter"""

    # def __init__(self, bot: Red):
    #     self.client = DiscordComponents(bot)
    #     self.bot: Red = bot

    @commands.group(name="test")
    @commands.guild_only()
    async def _test(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    @commands.command()
    async def stats(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the starter pokemon for the trainer."""
        if user is None:
            user = ctx.author

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()
        active = trainer.getActivePokemon()

        embed = createPokemonEmbedWithUrl(user, pokemon)

        btns = []
        
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
            self.on_stats_click,
        ))
        # btns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
        btns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))
        
        # Disable the "Set Active" button if the starter is currently the active pokemon
        disabled = (active is not None) and (pokemon.trainerId == active.trainerId)
        btns.append(Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=disabled))

        await ctx.send(embed=embed, components=[btns])
        # await ctx.send(pokemon.frontSpriteURL)


    async def on_stats_click(self, interaction: Interaction):
        user = interaction.user

        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()

        stats = pokemon.getPokeStats()
        color = getTypeColor(pokemon.type1)

        # Create the embed object
        embed = discord.Embed(title=f"#{pokemon.trainerId}  {pokemon.pokemonName.capitalize()}", color=color)
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))
        
        types = pokemon.type1
        if pokemon.type2 is not None:
            types += ', ' + pokemon.type2
            
        embed.add_field(
            name="Type", value=f"{types}", inline=True)
        
        if pokemon.nickName is not None:
            embed.add_field(
                name="Nickname", value=f"{pokemon.nickName}", inline=False)
        
        embed.add_field(
            name="Level", value=f"{pokemon.currentLevel}", inline=False)
        embed.add_field(
            name="HP", value=f"{pokemon.currentHP} / {stats['hp']}", inline=False)
        embed.add_field(
            name="Attack", value=f"{stats['attack']}", inline=True)
        embed.add_field(
            name="Defense", value=f"{stats['defense']}", inline=True)
        embed.add_field(
            name="Special Attack", value=f"{stats['special-attack']}", inline=True)
        embed.add_field(
            name="Special Defense", value=f"{stats['special-defense']}", inline=True)
        embed.add_field(
            name="Speed", value=f"{stats['speed']}", inline=True)

        embed.set_thumbnail(url=pokemon.frontSpriteURL)

        await interaction.edit_origin(embed=embed)

