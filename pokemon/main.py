from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING
from abc import ABCMeta
import random

import discord
from discord import (Embed, Member)
from discord_components import (DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction)

from pokebase.loaders import pokedex


if TYPE_CHECKING:
    from redbot.core.bot import Red

# import emojis
from redbot.core import Config, commands
import asyncio

from .functions import (createPokemonAboutEmbed)
from .starter import StarterMixin
from .pokemart import PokemartMixin
# from .event import EventMixin

# import pokebase as pb
# import psycopg as pg
# from .models.helpers import *
from services.trainerclass import trainer as TrainerClass
# from services.pokeclass import Pokemon as PokemonClass
# from services.storeclass import store as StoreClass
from services.inventoryclass import inventory as InventoryClass

import constant
import uuid




class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class Pokemon(StarterMixin, PokemartMixin, commands.Cog, metaclass=CompositeClass):
    """Pokemon"""

    def __init__(self, bot: Red):
        super().__init__()
        self.client = DiscordComponents(bot)
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

        await ctx.send(f'{pokemon.pokemonName} added.')
        pass

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass


    @_trainer.command()
    async def bag(self, ctx: commands.Context, user: discord.Member = None):
        """Show trainer bag"""
        if user is None:
            user = ctx.author

        def nextBtnClick():
            return lambda x: x.custom_id == "items" or x.custom_id == 'keyitems'

        # # guild = self.bot.get_guild(971138995042025494)
        # # \u200b
        # # A device for catching wild Pokémon. It's thrown like a ball, comfortably encapsulating its target.

        inv = InventoryClass(str(user.id))

        interaction: Interaction = None
        state = 'Items'

        while True:
            try:
                name = uuid.uuid4()
                file = discord.File("data/cogs/CogManager/cogs/pokemon/sprites/bag.png", filename=f"{name}.png")
                # Create the embed object
                embed = discord.Embed(title=f"Bag")
                embed.set_thumbnail(url=f"attachment://{name}.png")
                embed.set_author(name=f"{user.display_name}",
                                icon_url=str(user.avatar_url))

                if state == 'Items':
                    items = []

                    if inv.pokeball > 0:
                        items.append(f'{constant.POKEBALL} **Pokeballs** — {inv.pokeball}')
                    if inv.greatball > 0:
                        items.append(f'{constant.GREATBALL} **Greatballs** — {inv.greatball}')
                    if inv.ultraball > 0:
                        items.append(f'{constant.ULTRABALL} **Ultraball** — {inv.ultraball}')
                    if inv.masterball > 0:
                        items.append(f'{constant.MASTERBALL} **Masterball** — {inv.masterball}')
                    if inv.potion > 0:
                        items.append(f'{constant.POTION} **Potion** — {inv.potion}')
                    if inv.superpotion > 0:
                        items.append(f'{constant.SUPERPOTION} **Superpotion** — {inv.superpotion}')
                    if inv.hyperpotion > 0:
                        items.append(f'{constant.HYPERPOTION} **Hyperpotion** — {inv.hyperpotion}')
                    if inv.maxpotion > 0:
                        items.append(f'{constant.MAXPOTION} **Maxpotion** — {inv.maxpotion}')
                    if inv.revive > 0:
                        items.append(f'{constant.REVIVE} **Revive** — {inv.revive}')
                    if inv.fullrestore > 0:
                        items.append(f'{constant.FULLRESTORE} **Full Restore** — {inv.fullrestore}')
                    if inv.repel > 0:
                        items.append(f'{constant.REPEL} **Repel** — {inv.repel}')
                    if inv.maxrepel > 0:
                        items.append(f'{constant.MAXREPEL} **Max Repel** — {inv.maxrepel}')
                    if inv.escaperope > 0:
                        items.append(f'{constant.ESCAPEROPE} **Escape Rope** — {inv.escaperope}')
                    if inv.awakening > 0:
                        items.append(f'{constant.AWAKENING} **Awakening** — {inv.awakening}')
                    if inv.antidote > 0:
                        items.append(f'{constant.ANTIDOTE} **Antidote** — {inv.antidote}')
                    if inv.iceheal > 0:
                        items.append(f'{constant.ICEHEAL} **Iceheal** — {inv.iceheal}')
                    if inv.burnheal > 0:
                        items.append(f'{constant.BURNHEAL} **Burnheal** — {inv.burnheal}')
                    if inv.paralyzeheal > 0:
                        items.append(f'{constant.PARALYZEHEAL} **Paralyzeheal** — {inv.paralyzeheal}')
                    if inv.fullheal > 0:
                        items.append(f'{constant.FULLHEAL} **Fullheal** — {inv.fullheal}')

                    trainerItems = "\r\n".join(items)
                    embed.add_field(name=state, value=trainerItems, inline=False)
                else:
                    embed.add_field(name=state, value="No key items", inline=False)


                # await ctx.send(embed=embed, file=file)
                btns = []
                if state == 'Items':
                    btns.append(Button(style=ButtonStyle.gray, label='Key Items →', custom_id='keyitems'))
                if state == 'Key Items':
                    btns.append(Button(style=ButtonStyle.gray, label="← Items", custom_id='items'))


                if interaction is None:
                    await ctx.send(
                        embed=embed,
                        file=file,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)
                else:
                    await interaction.edit_origin(
                        embed=embed,
                        file=file,
                        components=[btns]
                    )
                    interaction = await self.bot.wait_for("button_click", check=nextBtnClick(), timeout=30)

                if interaction.custom_id == 'keyitems':
                    state = 'Key Items'
                if (interaction.custom_id == 'items'):
                    state = 'Items'
            except asyncio.TimeoutError:
                break

    @_trainer.command()
    async def action(self, ctx: commands.Context):
        user = ctx.author
        
        trainer = TrainerClass(str(user.id))
        areaMethods = trainer.getAreaMethods()

        btns = []
        for method in areaMethods:
            btns.append(Button(style=ButtonStyle.gray, label=f"{method}", custom_id=f'{method}'))

        if len(btns) > 0:
            await ctx.send(
                "What do you want to do?",
                components=[btns]
            )
        else:
            await ctx.send(f'areaId: {trainer.getAreaId()} - No actions available')


    @_trainer.command()
    async def pokedex(self, ctx: commands.Context, user: discord.Member = None):
        if user is None:
            user = ctx.author

        def nextBtnClick():
            return lambda x: x.custom_id == "next" or x.custom_id == 'previous'

        trainer = TrainerClass('456')

        pokedex = trainer.getPokedex()

        interaction: Interaction = None
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

    # @_trainer.command()
    # async def starter(self, ctx: commands.Context, user: discord.Member = None) -> None:
    #     """Show the starter pokemon for the trainer."""
    #     if user is None:
    #         user = ctx.author

    #     # This will create the trainer if it doesn't exist
    #     trainer = TrainerClass(str(user.id))
    #     pokemon = trainer.getStarterPokemon()
    #     active = trainer.getActivePokemon()

    #     embed = createPokemonAboutEmbed(user, pokemon)

    #     btns = []
        
    #     # btns.append(self.client.add_callback(
    #     #     Button(style=ButtonStyle.green, label="Stats", custom_id='stats'),
    #     #     self.on_stats_click,
    #     # ))
    #     btns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
    #     btns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))
        
    #     # Disable the "Set Active" button if the starter is currently the active pokemon
    #     disabled = (active is not None) and (pokemon.trainerId == active.trainerId)
    #     btns.append(Button(style=ButtonStyle.blue, label="Set Active", custom_id='active', disabled=disabled))

    #     await ctx.send(embed=embed, components=[btns])
    #     # await ctx.send(pokemon.frontSpriteURL)

    # async def on_stats_click(self, interaction: Interaction):
    #     await interaction.send('stats clicked')

    # @_trainer.command()
    # async def active(self, ctx: commands.Context, user: discord.Member = None) -> None:
    #     """Show the currect active pokemon for the trainer."""
    #     if user is None:
    #         user = ctx.author

    #      # This will create the trainer if it doesn't exist
    #     trainer = TrainerClass(str(user.id))
    #     pokemon = trainer.getActivePokemon()

    #     btns = []
    #     btns.append(Button(style=ButtonStyle.green, label="Stats", custom_id='stats'))
    #     btns.append(Button(style=ButtonStyle.green, label="Pokedex", custom_id='pokedex'))

    #     embed = createPokemonAboutEmbed(user, pokemon)
    #     await ctx.send(embed=embed)       


    # @_trainer.command()
    # async def pokemon(self, ctx: commands.Context, user: discord.Member = None) -> None:
    #     """Show the starter pokemon for the trainer.
    #     """
    #     if user is None:
    #         user = ctx.author

    #     # TODO: don't store these credentials in source control,
    #     #       eventually just pass them in as part of the cog config
    #     conn = pg.connect(
    #         host="private-db-redbot-nyc3-42069-do-user-1692759-0.b.db.ondigitalocean.com",
    #         dbname="pokemon_db",
    #         user="redbot",
    #         password="AVNS_nUSNiHJE3MlXGmj",
    #         port=25060)

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