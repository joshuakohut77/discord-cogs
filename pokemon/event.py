from __future__ import annotations
from typing import TYPE_CHECKING
from .abc import MixinMeta

# if TYPE_CHECKING:
#     import discord

import discord
from redbot.core import commands

import pokebase as pb
import psycopg as pg


class EventMixin(MixinMeta):
    __slots__: tuple = ()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user) -> None:
        if self.pokelist is None:
            reaction.message.reply('not found')
            return

        # name = list(self.pokelist.keys())[0]
        # await reaction.message.reply(name)
        # await reaction.message.reply(user.id)

        # pass
        trainerPokemon = self.pokelist[f'{user.id}']

        if trainerPokemon is None:
            return

        if trainerPokemon['message_id'] != reaction.message.id:
            return

        reactionId = reaction.emoji
        if not isinstance(reactionId, str):
            reactionId = reaction.emoji.id

        # print(reactionId)
        # await reaction.message.reply(reactionId)

        arrow_forwards = '▶️'
        arrow_backwards = '◀️'

        if reactionId == arrow_forwards:
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
                'select * from trainer_pokemon where trainer_id = %(trainer)s', {'trainer': trainerPokemon['trainer_id']})

            pokemon = cur.fetchall()

            nextIdx = trainerPokemon['index'] + 1
            if nextIdx <= len(pokemon) - 1:
                nextPokemon = pokemon[nextIdx]

                name = nextPokemon[1]
                pokemon = pb.pokemon(name)
                sprite = pb.SpriteResource('pokemon', pokemon.id)

                embed = discord.Embed(title=f"#{pokemon.id} {pokemon.name}")
                embed.set_author(name=f"{user.display_name}",
                                 icon_url=str(user.avatar_url))
                embed.add_field(
                    name="Weight", value=f"{pokemon.weight}", inline=True)
                embed.add_field(
                    name="Height", value=f"{pokemon.height}", inline=True)
                embed.set_thumbnail(url=f"{sprite.url}")

                trainerPokemon['index'] = nextIdx

                await reaction.message.edit(embed=embed)

        # TODO: copypasta
        if reactionId == arrow_backwards:
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
                'select * from trainer_pokemon where trainer_id = %(trainer)s', {'trainer': trainerPokemon['trainer_id']})

            pokemon = cur.fetchall()

            nextIdx = trainerPokemon['index'] - 1
            if nextIdx <= len(pokemon) - 1:
                nextPokemon = pokemon[nextIdx]

                name = nextPokemon[1]
                pokemon = pb.pokemon(name)
                sprite = pb.SpriteResource('pokemon', pokemon.id)

                embed = discord.Embed(title=f"#{pokemon.id} {pokemon.name}")
                embed.set_author(name=f"{user.display_name}",
                                 icon_url=str(user.avatar_url))
                embed.add_field(
                    name="Weight", value=f"{pokemon.weight}", inline=True)
                embed.add_field(
                    name="Height", value=f"{pokemon.height}", inline=True)
                embed.set_thumbnail(url=f"{sprite.url}")

                trainerPokemon['index'] = nextIdx

                await reaction.message.edit(embed=embed)
