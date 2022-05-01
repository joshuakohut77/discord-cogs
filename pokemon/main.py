from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta

from pokebase.loaders import pokedex


if TYPE_CHECKING:
    from redbot.core.bot import Red

# import emojis
import discord
from discord_components import DiscordComponents, ButtonStyle, ComponentsBot, Button
from redbot.core import Config, commands

from .event import EventMixin

import pokebase as pb
import psycopg as pg
# from .models.helpers import *
from models.trainerclass import trainer as TrainerClass
from models.storeclass import store as StoreClass
from models.inventoryclass import inventory as InventoryClass


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
    # [p]trainer setactive <id> - unique id of pokemon in db (validate it's their id)
    # [p]trainer action - UI provides buttons to interact
    #
    # [p]pokemon stats <id> - unique id of pokemon in db (stats + moves)
    # [p]pokemon wiki <id> - any pokemon general wiki
    #

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
    async def pokedex(self, ctx: commands.Context, user: discord.Member = None):
        if user is None:
            user = ctx.author

        trainer = TrainerClass('456')
        
        # Create the embed object
        embed = discord.Embed(title=f"Pokedex")
        embed.set_thumbnail(url=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png")
        embed.set_author(name=f"{user.display_name}",
                         icon_url=str(user.avatar_url))

        pokedex = trainer.getPokedex()

        first = pokedex[0]
        pokemon = trainer.getPokemon(first['id'])

        embed.add_field(name=f"No.", value=f"{pokemon.id}", inline=False)
        embed.add_field(name=f"Pokemon", value=f"{pokemon.name}", inline=False)
        embed.add_field(name=f"Last seen", value=f"{first['lastSeen']}", inline=False)
        embed.set_thumbnail(url=f"{pokemon.spriteURL}")


        btn = Button(style=ButtonStyle.gray,
                     label="Next", custom_id='next')

        def nextBtnClick(ev):
            print(ev)
            return ev.custom_id == 'next'

        await ctx.send(
            embed=embed,
            components=[[
                btn
                # self.bot.components_manager.add_callback(b, callback)
            ]]
        )
        
        interaction = await self.bot.wait_for("button_click", check=nextBtnClick)
        # await ctx.send(embed=embed)

    @_trainer.command()
    async def button(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Test button
        """
        # await self.ui.components.send(ctx.channel, "Hello World", components=[
        #     Button("press me", "my_custom_id", "green"),
        # ])

        # async def callback(interaction):
        #     await interaction.send(content="Yay")

        btn = Button(style=ButtonStyle.gray,
                     label="Button 1", custom_id='button1')
        btn2 = Button(style=ButtonStyle.gray,
                      label="Button 2", custom_id='button2')

        await ctx.send(
            "Buttons",
            components=[[
                btn, btn2
                # self.bot.components_manager.add_callback(b, callback)
            ]]
        )

        interaction = await self.bot.wait_for("button_click", check=lambda i: i.custom_id == "button1")
        await interaction.message.edit('Buttons', components=[])
        await interaction.send('Button 1 clicked')
        # await interaction.send('Done')
        # await interaction.send(f'{msg.id}')

        # msg.edit('Buttons')

    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the starter pokemon for the trainer.
        """
        if user is None:
            user = ctx.author

        # This will create the trainer if it doesn't exist
        trainer = TrainerClass(user.id)
        pokemon = trainer.getStarterPokemon()
        stats = pokemon.getPokeStats()

        # Create the embed object
        embed = discord.Embed(title=f"Your starter is {pokemon.name}")
        embed.set_author(name=f"{user.display_name}",
                         icon_url=str(user.avatar_url))
        embed.add_field(
            name="Level", value=f"{pokemon.currentLevel}", inline=True)
        embed.add_field(
            name="Attack", value=f"{stats['attack']}", inline=True)
        embed.add_field(
            name="Defense", value=f"{stats['defense']}", inline=True)
        embed.set_thumbnail(url=f"{pokemon.spriteURL}")

        await ctx.send(embed=embed)

        # # TODO: don't store these credentials in source control,
        # #       eventually just pass them in as part of the cog config
        # conn = pg.connect(
        #     host="private-db-redbot-nyc3-42069-do-user-1692759-0.b.db.ondigitalocean.com",
        #     dbname="pokemon_db",
        #     user="redbot",
        #     password="AVNS_nUSNiHJE3MlXGmj",
        #     port=25060)

        # # TODO: there is a much better way to do this, still playing
        # cur = conn.cursor()
        # cur.execute(
        #     'select * from trainer where discord_id = %(discord)s', {'discord': user.id})

        # trainer = cur.fetchone()

        # if trainer is None:
        #     cur.execute(
        #         'insert into trainer (id, discord_id) values (default, %(discord)s)', {'discord': user.id})
        #     conn.commit()
        #     cur.execute(
        #         'select * from trainer where discord_id = %(discord)s', {'discord': user.id})
        #     trainer = cur.fetchone()

        # cur.execute(
        #     'select * from trainer_pokemon where trainer_id = %(trainer)s', {'trainer': trainer[0]})

        # starter = cur.fetchone()

        # if starter is None:
        #     gen1Starter = getStarterPokemon(user.display_name)
        #     name = list(gen1Starter.keys())[0]
        #     cur.execute('insert into "trainer_pokemon" values (%(trainer)s, %(name)s)', {
        #                 'trainer': trainer[0], 'name': name})
        #     conn.commit()
        #     cur.execute(
        #         'select * from trainer_pokemon where trainer_id = %(trainer)s', {'trainer': trainer[0]})
        #     starter = cur.fetchone()

        # # TODO: replace with pokeclass to calculate unique stats per pokemon
        # name = starter[1]
        # pokemon = pb.pokemon(name)
        # sprite = pb.SpriteResource('pokemon', pokemon.id)

        # # Create the embed object
        # embed = discord.Embed(title=f"Your starter is {pokemon.name}")
        # embed.set_author(name=f"{user.display_name}",
        #                  icon_url=str(user.avatar_url))
        # embed.add_field(name="Weight", value=f"{pokemon.weight}", inline=True)
        # embed.add_field(name="Height", value=f"{pokemon.height}", inline=True)
        # embed.set_thumbnail(url=f"{sprite.url}")

        # await ctx.send(embed=embed)

        # cur.close()
        # conn.close()

    @_trainer.command()
    async def pokemon(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the starter pokemon for the trainer.
        """
        if user is None:
            user = ctx.author

        # TODO: don't store these credentials in source control,
        #       eventually just pass them in as part of the cog config
        conn = pg.connect(
            host="private-db-redbot-nyc3-42069-do-user-1692759-0.b.db.ondigitalocean.com",
            dbname="pokemon_db",
            user="redbot",
            password="AVNS_nUSNiHJE3MlXGmj",
            port=25060)

        # TODO: there is a much better way to do this, still playing
        cur = conn.cursor()
        cur.execute(
            'select * from trainer where discord_id = %(discord)s', {'discord': user.id})

        trainer = cur.fetchone()

        if trainer is None:
            await ctx.send('You haven\'t received your started yet!')

        cur.execute(
            'select * from trainer_pokemon where trainer_id = %(trainer)s', {'trainer': trainer[0]})

        pokemon = cur.fetchall()

        if len(pokemon) == 0:
            await ctx.send('You haven\'t received your started yet!')

        cur.close()
        conn.close()

        firstPokemon = pokemon[0]
        # TODO: replace with pokeclass to calculate unique stats per pokemon
        name = firstPokemon[1]
        pokemon = pb.pokemon(name)
        sprite = pb.SpriteResource('pokemon', pokemon.id)

        # Create the embed object
        embed = discord.Embed(title=f"#{pokemon.id} {pokemon.name}")
        embed.set_author(name=f"{user.display_name}",
                         icon_url=str(user.avatar_url))
        embed.add_field(name="Weight", value=f"{pokemon.weight}", inline=True)
        embed.add_field(name="Height", value=f"{pokemon.height}", inline=True)
        embed.set_thumbnail(url=f"{sprite.url}")

        msg: discord.Message = await ctx.send(embed=embed)

        self.pokelist[f'{user.id}'] = {'message_id': msg.id,
                                       'trainer_id': trainer[0], 'index': 0}

        # emoji: discord.Emoji = await commands.EmojiConverter().convert(ctx=await self.bot.get_context(msg), argument=':arrow_backward:')
        # if emoji is None:
        #     await msg.reply('emoji null')
        # emoji = self.bot.get_emoji()
        await msg.add_reaction('◀️')
        await msg.add_reaction('▶️')

        # await msg.reply('done')
        await ctx.tick()
