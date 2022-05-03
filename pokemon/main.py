from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from discord.embeds import Embed
from discord.member import Member
import discord_components
import random

from pokebase.loaders import pokedex


if TYPE_CHECKING:
    from redbot.core.bot import Red

# import emojis
import discord
from discord_components import DiscordComponents, ButtonStyle, ComponentsBot, Button
from redbot.core import Config, commands
import asyncio

from .event import EventMixin

import pokebase as pb
import psycopg as pg
# from .models.helpers import *
from models.trainerclass import trainer as TrainerClass
from models.pokeclass import Pokemon as PokemonClass
from models.storeclass import store as StoreClass
from models.inventoryclass import inventory as InventoryClass


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

def createPokemonEmbed(user: Member, pokemon: PokemonClass) -> Embed:
    stats = pokemon.getPokeStats()
    color = getTypeColor(pokemon.type1)

    # Create the embed object
    embed = discord.Embed(title=f"#{pokemon.id}  {pokemon.name.capitalize()}", color=color)
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
    embed.set_thumbnail(url=f"{pokemon.spriteURL}")
    return embed


class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class Pokemon(EventMixin, commands.Cog, metaclass=CompositeClass):
    """Pokemon"""

    def __init__(self, bot: Red):
        DiscordComponents(bot)
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=4206980085, force_registration=True)

        default_channel: Dict[str, Any] = {
            "enabled": True,
        }
        default_guild: Dict[str, Any] = {
            "enabled": True
        }
        self.config.register_channel(**default_channel)
        self.config.register_guild(**default_guild)

        self.pokelist = {}

    async def guild_only_check():
        async def pred(self, ctx: commands.Context):
            if ctx.guild is not None and await self.config.guild(ctx.guild).enabled():
                return True
            else:
                return False

        return commands.check(pred)

    #
    # Commands:
    #
    # [p]trainer pokedex <user> - user is optional
    # [p]trainer pokemon <user> - owned pokemon user optional
    # [p]trainer action - UI provides buttons to interact
    #
    # [p]pokemon stats <id> - unique id of pokemon in db (stats + moves)
    # [p]pokemon wiki <id> - any pokemon general wiki

    @commands.group(name="debug")
    @commands.guild_only()
    async def _debug(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    @_debug.command()
    async def add(self, ctx: commands.Context, user: discord.Member = None) -> None:
        if user is None:
            user = ctx.author

        trainer = TrainerClass(str(user.id))
        ids = range(1, 152)
        id = random.choice(ids)
        pokemon = trainer.addPokemon(id)

        await ctx.send(f'{pokemon.name} added.')
        pass

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    @commands.group(name="pokemart")
    @commands.guild_only()
    async def _pokemart(self, ctx: commands.Context) -> None:
        """Base command to manage the pokemart (store)
        """
        pass

    @_pokemart.command()
    async def list(self, ctx: commands.Context, user: discord.Member = None) -> None:
        
        if user is None:
            user = ctx.author
        
        store = StoreClass(user.id)

        # Create the embed object
        embed = discord.Embed(title=f"Pokemart - TODO: Area Name")
        embed.set_thumbnail(url=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png")
        # embed.set_author(name=f"{user.display_name}",
        #                  icon_url=str(user.avatar_url))

        for item in store.storeList:
            embed.add_field(name=f"▶️  {item['item']} — {item['price']}", value='description of item', inline=False)

        await ctx.send(embed=embed)
        await ctx.tick()

    @_pokemart.command()
    async def buy(self, ctx: commands.Context, item: str, count: int = 1) -> None:
        """List the pokemart items available to you
        """
        user = ctx.author

        store = StoreClass(str(user.id))
        res = store.buyItemEx(item, count)

        await ctx.send(res)
        await ctx.send(f'{user.display_name} bought {count} {item}')
    

    @_trainer.command()
    async def inventory(self, ctx: commands.Context, user: discord.Member = None):
        """Show trainer inventory"""
        if user is None:
            user = ctx.author

        inv = InventoryClass(str(user.id))

        # Create the embed object
        embed = discord.Embed(title=f"Inventory")
        embed.set_thumbnail(url=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png")
        embed.set_author(name=f"{user.display_name}",
                         icon_url=str(user.avatar_url))

        embed.add_field(name=f"▶️  Pokeballs", value=f'{inv.pokeball}', inline=True)
        embed.add_field(name=f"▶️  Potion", value=f'{inv.potion}', inline=True)
        embed.add_field(name=f"▶️  Money", value=f'{inv.money}', inline=True)

        await ctx.send(embed=embed)

    @_trainer.command()
    async def action(self, ctx: commands.Context, user: discord.Member = None):
        if user is None:
            user = ctx.author

        
        trainer = TrainerClass(str(user.id))
        areaMethods = trainer.getAreaMethods()

        btns = []
        for method in areaMethods:
            btns.append(Button(style=ButtonStyle.gray, label=f"{method}", custom_id=f'{method}'))

        await ctx.send(
            content="What do you want to do?",
            components=[btns]
        )

    @_trainer.command()
    async def pc(self, ctx: commands.Context, user: discord.Member = None):
        if user is None:
            user = ctx.author

        def nextBtnClick():
            return lambda x: x.custom_id == "next" or x.custom_id == 'previous' or x.custom_id == 'stats' or x.custom_id == 'pokedex' or x.custom_id == 'active'

        trainer = TrainerClass(str(user.id))
        pokeList = trainer.getPokemon()

        interaction: discord_components.Interaction = None
        pokeLength = len(pokeList)
        i = 0

        if pokeLength == 0:
            await ctx.reply(content=f'{user.display_name} does not have any Pokemon.')
            return

        while True:
            try:
                pokemon: PokemonClass = pokeList[i]
                embed = createPokemonEmbed(user, pokemon)
                
                btns = []
                if i > 0:
                    btns.append(Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'))
                if i < pokeLength - 1:
                    btns.append(Button(style=ButtonStyle.gray, label="Next", custom_id='next'))

                btns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
                btns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))
                btns.append(Button(style=ButtonStyle.blue, label="Set Active", custom_id='active'))

                if interaction is None:
                    await ctx.send(
                        embed=embed,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                    # message = interaction.message
                else:
                    await interaction.edit_origin(
                        embed=embed,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                    # message = interaction.message
                
                if interaction.custom_id == 'next':
                    i = i + 1
                if (interaction.custom_id == 'previous'):
                    i = i - 1
                if interaction.custom_id == 'active':
                    res = trainer.setActivePokemon(pokemon.trainerId)
                    await interaction.send(content=f'{res}')
                    break
                if interaction.custom_id == 'stats':
                    await interaction.send('Not implemented')
                    break
                if interaction.custom_id == 'pokedex':
                    await interaction.send('Not implemented')
                    break
            except asyncio.TimeoutError:
                break

    @_trainer.command()
    async def pokedex(self, ctx: commands.Context, user: discord.Member = None):
        if user is None:
            user = ctx.author

        def nextBtnClick():
            return lambda x: x.custom_id == "next" or x.custom_id == 'previous'

        trainer = TrainerClass('456')

        pokedex = trainer.getPokedex()

        interaction: discord_components.Interaction = None
        i = 0
        while True:
            try:
                embed = discord.Embed(title=f"Index {i}")
                btns = []
                if i > 0:
                    btns.append(Button(style=ButtonStyle.gray, label='Previous', custom_id='previous'))
                if i < 5 - 1:
                    btns.append(Button(style=ButtonStyle.gray, label="Next", custom_id='next'))

                if interaction is None:
                    await ctx.send(
                        embed=embed,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                    # message = interaction.message
                else:
                    await interaction.edit_origin(
                        embed=embed,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                    # message = interaction.message
                
                if interaction.custom_id == 'next':
                    i = i + 1
                if (interaction.custom_id == 'previous'):
                    i = i - 1
            except asyncio.TimeoutError:
                break

        # first = pokedex[0]
        # pokemon = trainer.getPokemon(first['id'])

        # # Create the embed object
        # embed = discord.Embed(title=f"Pokedex")
        # embed.set_thumbnail(url=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png")
        # embed.set_author(name=f"{user.display_name}",
        #                  icon_url=str(user.avatar_url))
        # embed.add_field(name=f"No.", value=f"{pokemon.id}", inline=False)
        # embed.add_field(name=f"Pokemon", value=f"{pokemon.name}", inline=False)
        # embed.add_field(name=f"Last seen", value=f"{first['lastSeen']}", inline=False)
        # embed.set_thumbnail(url=f"{pokemon.spriteURL}")


        # btn = Button(style=ButtonStyle.gray,
        #              label="Next", custom_id='next')


        # await ctx.send(
        #     embed=embed,
        #     components=[[
        #         btn
        #         # self.bot.components_manager.add_callback(b, callback)
        #     ]]
        # )
        
        # interaction = await self.bot.wait_for("button_click", check=nextBtnClick())
        # await ctx.send(embed=embed)

    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the starter pokemon for the trainer.
        """
        if user is None:
            user = ctx.author

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getStarterPokemon()

        embed = createPokemonEmbed(user, pokemon)
        await ctx.send(embed=embed)

    @_trainer.command()
    async def active(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the currect active pokemon for the trainer."""
        if user is None:
            user = ctx.author

         # This will create the trainer if it doesn't exist
        trainer = TrainerClass(str(user.id))
        pokemon = trainer.getActivePokemon()

        embed = createPokemonEmbed(user, pokemon)
        await ctx.send(embed=embed)       


    # @_trainer.command()
    # async def pokemon(self, ctx: commands.Context, user: discord.Member = None) -> None:
    #     """Show the starter pokemon for the trainer.
    #     """
    #     if user is None:
    #         user = ctx.author

    #     # TODO: don't store these credentials in source control,
    #     #       eventually just pass them in as part of the cog config
    #     conn = pg.connect(
    #         host="private-REDACTED_HOST",
    #         dbname="pokemon_db",
    #         user="redbot",
    #         password="REDACTED_PASSWORD",
    #         port=REDACTED_PORT)

    #     # TODO: there is a much better way to do this, still playing
    #     cur = conn.cursor()
    #     cur.execute(
    #         'select * from trainer where discord_id = %(discord)s', {'discord': user.id})

    #     trainer = cur.fetchone()

    #     if trainer is None:
    #         await ctx.send('You haven\'t received your started yet!')

    #     cur.execute(
    #         'select * from trainer_pokemon where trainer_id = %(trainer)s', {'trainer': trainer[0]})

    #     pokemon = cur.fetchall()

    #     if len(pokemon) == 0:
    #         await ctx.send('You haven\'t received your started yet!')

    #     cur.close()
    #     conn.close()

    #     firstPokemon = pokemon[0]
    #     # TODO: replace with pokeclass to calculate unique stats per pokemon
    #     name = firstPokemon[1]
    #     pokemon = pb.pokemon(name)
    #     sprite = pb.SpriteResource('pokemon', pokemon.id)

    #     # Create the embed object
    #     embed = discord.Embed(title=f"#{pokemon.id} {pokemon.name}")
    #     embed.set_author(name=f"{user.display_name}",
    #                      icon_url=str(user.avatar_url))
    #     embed.add_field(name="Weight", value=f"{pokemon.weight}", inline=True)
    #     embed.add_field(name="Height", value=f"{pokemon.height}", inline=True)
    #     embed.set_thumbnail(url=f"{sprite.url}")

    #     msg: discord.Message = await ctx.send(embed=embed)

    #     self.pokelist[f'{user.id}'] = {'message_id': msg.id,
    #                                    'trainer_id': trainer[0], 'index': 0}

    #     # emoji: discord.Emoji = await commands.EmojiConverter().convert(ctx=await self.bot.get_context(msg), argument=':arrow_backward:')
    #     # if emoji is None:
    #     #     await msg.reply('emoji null')
    #     # emoji = self.bot.get_emoji()
    #     await msg.add_reaction('◀️')
    #     await msg.add_reaction('▶️')

    #     # await msg.reply('done')
    #     await ctx.tick()

    # @_trainer.command()
    # async def button(self, ctx: commands.Context, user: discord.Member = None) -> None:
    #     """Test button
    #     """
    #     # await self.ui.components.send(ctx.channel, "Hello World", components=[
    #     #     Button("press me", "my_custom_id", "green"),
    #     # ])

    #     # async def callback(interaction):
    #     #     await interaction.send(content="Yay")

    #     btn = Button(style=ButtonStyle.gray,
    #                  label="Button 1", custom_id='button1')
    #     btn2 = Button(style=ButtonStyle.gray,
    #                   label="Button 2", custom_id='button2')

    #     await ctx.send(
    #         "Buttons",
    #         components=[[
    #             btn, btn2
    #             # self.bot.components_manager.add_callback(b, callback)
    #         ]]
    #     )

    #     interaction = await self.bot.wait_for("button_click", check=lambda i: i.custom_id == "button1")
    #     # await interaction.message.edit('Buttons', components=[])
    #     await interaction.edit_origin('Buttons', components=[])
    #     # await interaction.send('Button 1 clicked')
    #     # await interaction.send('Done')
    #     # await interaction.send(f'{msg.id}')

    #     # msg.edit('Buttons')