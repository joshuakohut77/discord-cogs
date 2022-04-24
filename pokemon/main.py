from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta

if TYPE_CHECKING:
    from redbot.core.bot import Red

# import emojis
import discord
from redbot.core import Config, commands

from .event import EventMixin

import pokebase as pb
import psycopg as pg
from helpers import *


class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class Pokemon(EventMixin, commands.Cog, metaclass=CompositeClass):
    """Pokemon"""

    def __init__(self, bot: Red):
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

    async def guild_only_check():
        async def pred(self, ctx: commands.Context):
            if ctx.guild is not None and await self.config.guild(ctx.guild).enabled():
                return True
            else:
                return False

        return commands.check(pred)

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """
        pass

    @_trainer.command()
    async def starter(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """Show the starter pokemon for the trainer.
        """
        if user is None:
            user = ctx.author

        # TODO: don't store these credentials in source control,
        #       eventually just pass them in as part of the cog config
        conn = pg.connect(
            host="db-redbot-nyc3-42069-do-user-1692759-0.b.db.ondigitalocean.com",
            dbname="pokemon_db",
            user="redbot",
            password="AVNS_nUSNiHJE3MlXGmj",
            port=25060)

        # TODO: there is a much better way to do this, still playing
        cur = conn.cursor()
        cur.execute(
            'select * from trainer where discord_id = 509767223938777108')

        trainer = cur.fetchone()

        if trainer is None:
            cur.execute(
                'insert into trainer (id, discord_id) values (default, %(discord)s)', {'discord': 900000000000000000})
            conn.commit()
            cur.execute(
                'select * from trainer where discord_id = 900000000000000000')
            trainer = cur.fetchone()

        cur.execute(
            'select * from trainer_pokemon where trainer_id = %(trainer)s', {'trainer': 1})

        starter = cur.fetchone()

        if starter is None:
            gen1Starter = getStarterPokemon(user.display_name)
            name = gen1Starter.keys()[0]
            cur.execute('insert into "trainer_pokemon" values (%(trainer)s, %(name)s)', {
                        'trainer': 1, 'pokemon': name})
            conn.commit()
            cur.execute(
                'select * from trainer_pokemon where trainer_id = %(trainer)s', {'trainer': 1})
            pokemon = cur.fetchone()

        # TODO: replace with pokeclass to calculate unique stats per pokemon
        pokemon = pb.pokemon(name)
        sprite = pb.SpriteResource('pokemon', pokemon.id)

        # Create the embed object
        embed = discord.Embed(title=f"Your starter is {pokemon.name}")
        embed.set_author(name=f"{user.display_name}",
                         icon_url=str(user.avatar_url))
        embed.add_field(name="Weight", value=f"{pokemon.weight}", inline=True)
        embed.add_field(name="Height", value=f"{pokemon.height}", inline=True)
        embed.set_thumbnail(url=f"{sprite.url}")

        await ctx.send(embed=embed)
