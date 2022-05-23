from __future__ import annotations
from re import A
from typing import Any, Dict, List, Union, TYPE_CHECKING
import asyncio

import discord
from discord import (Embed, Member)
from discord import message
from discord_components import (
    DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction, component)


if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from models.location import LocationModel
from services.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass
from services.inventoryclass import inventory as InventoryClass


from .abcd import MixinMeta
from services.pokeclass import Pokemon as PokemonClass
from .functions import (createStatsEmbed, getTypeColor,
                        createPokemonAboutEmbed)


class ActionState:
    discordId: str
    location: LocationModel

    channelId: int
    messageId: int

    activePokemon: PokemonClass
    wildPokemon: PokemonClass
    descLog: str

    def __init__(self, discordId: str, channelId: int, messageId: int, location: LocationModel, activePokemon: PokemonClass, wildPokemon: PokemonClass, descLog: str) -> None:
        self.discordId = discordId
        self.location = location

        self.channelId = channelId
        self.messageId = messageId

        self.activePokemon = activePokemon
        self.wildPokemon = wildPokemon
        self.descLog = descLog


class EncountersMixin(MixinMeta):
    """Encounters"""

    __useractions: dict[str, ActionState] = {}

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """

    @_trainer.command(aliases=['enc'])
    async def encounter(self, ctx: commands.Context):
        user = ctx.author
        
        trainer = TrainerClass(str(user.id))
        model = trainer.getLocation()

        location = LocationClass(str(user.id))
        methods = location.getMethods()

        if len(methods) == 0:
            await ctx.send('No encounters available at your location.')
            return

        btns = []
        for method in methods:
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray,
                       label=f"{method}", custom_id=f'{method}'),
                self.__on_action
            ))

        message: discord.Message = await ctx.send(
            content="What do you want to do?",
            components=[btns]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, model, trainer.getActivePokemon(), None, '')


    async def __on_action(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        location = LocationClass(str(user.id))
        methods = location.getMethods()

        btns = []
        for method in methods:
            color = ButtonStyle.gray
            if method == interaction.custom_id:
                color = ButtonStyle.green
            
            btns.append(
                Button(style=color, label=f"{method}", custom_id=f'{method}', disabled=True)
            )

        await interaction.edit_origin(
            content="Walking through tall grass...",
            components=[btns]
        )

        # await interaction.respond(type=5, content="Walking through tall grass...")

        state = self.__useractions[str(user.id)]
        method = interaction.custom_id

        # if method == 'walk':
        trainer = TrainerClass(str(user.id))
        wildPokemon: PokemonClass = trainer.encounter(method)
        if wildPokemon is None:
            if trainer.statuscode == 420:
                await interaction.channel.send(trainer.message)
            else:
                await interaction.channel.send('No pokemon encountered.')
            # await interaction.send('No pokemon encountered.')
            return

        # active = trainer.getActivePokemon()
        active = state.activePokemon
        
        # await interaction.send(f'You encountered a wild {pokemon.pokemonName}!')
        desc = f'''
{user.display_name} encountered a wild {wildPokemon.pokemonName.capitalize()}!
{user.display_name} sent out {active.pokemonName.capitalize()}.
'''

        embed = self.__wildPokemonEncounter(user, wildPokemon, active, desc)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Fight", custom_id='fight'),
            self.__on_fight_click,
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Run away", custom_id='runaway'),
            self.__on_runaway_click,
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Catch", custom_id='catch'),
            self.__on_catch_click,
        ))

        message = await interaction.channel.send(
            # content=f'{user.display_name} encountered a wild {pokemon.pokemonName.capitalize()}!',
            embed=embed,
            components=[btns]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, active, wildPokemon, desc)


    async def __on_fight_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        await interaction.respond(type=5, content="Battling...")

        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))

        # await interaction.edit_origin(
        #     content=f'{trainer.message}',
        #     embed=embed,
        #     components=[]
        # )

        trainer.fight(state.wildPokemon)

        if trainer.statuscode == 96:
            await interaction.send(trainer.message)
            return

        channel: discord.TextChannel = self.bot.get_channel(state.channelId)
        message: discord.Message = await channel.fetch_message(state.messageId)

        desc = state.descLog
        desc += f'''{user.display_name} chose to fight!
{trainer.message}
'''
        active = trainer.getActivePokemon()

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, active, desc)

        await interaction.send(trainer.message)
        # await interaction.channel.send(
        await message.edit(
            content=f'{trainer.message}',
            embed=embed,
            components=[]
        )
        del self.__useractions[str(user.id)]


    async def __on_runaway_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        trainer.runAway(state.wildPokemon)

        if trainer.statuscode == 96:
            interaction.send(trainer.message)
            return

        desc = state.descLog
        desc += f'''{user.display_name} chose to run away.
{trainer.message}
'''

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, state.activePokemon, desc)


        await interaction.edit_origin(
            # content=f'{user.display_name} ran away from a wild {state.pokemon.pokemonName.capitalize()}!',
            embed=embed,
            components=[]
        )
        del self.__useractions[str(user.id)]
        

    async def __on_catch_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return


        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        items = InventoryClass(trainer.discordId)

        ctx = await self.bot.get_context(interaction.message)

        btns = []
        if items.pokeball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.POKEBALL)
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji=emote, label="Poke Ball", custom_id='pokeball'),
                self.__on_throw_pokeball,
            ))
        if items.greatball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.GREATBALL)
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji=emote, label="Great Ball", custom_id='greatball'),
                self.__on_throw_pokeball,
            ))
        if items.ultraball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.ULTRABALL)
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji=emote, label=f"Ultra Ball", custom_id='ultraball'),
                self.__on_throw_pokeball,
            ))
        if items.masterball > 0:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=constant.MASTERBALL)
            btns.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji=emote, label=f"Master Ball", custom_id='masterball'),
                self.__on_throw_pokeball,
            ))

        if len(btns) == 0:
            await interaction.send('You have no balls!')
            return

        secondRow = []
        secondRow.append(self.client.add_callback(
            Button(style=ButtonStyle.gray, label=f"Back", custom_id='back'),
            self.__on_catch_back,
        ))

        desc = state.descLog
        desc += f'''{user.display_name} chose to catch the wild {state.wildPokemon.pokemonName.capitalize()}.
'''

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, state.activePokemon, desc)
        
        message = await interaction.edit_origin(
            # content=f'{user.display_name} encountered a wild {state.pokemon.pokemonName.capitalize()}!',
            embed=embed,
            components=[btns, secondRow]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, state.activePokemon, state.wildPokemon, desc)


    async def __on_catch_back(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        # active = trainer.getActivePokemon()
        state = self.__useractions[str(user.id)]
        wildPokemon = state.wildPokemon
        active = state.activePokemon
        
        # await interaction.send(f'You encountered a wild {pokemon.pokemonName}!')
        desc = f'''
{user.display_name} encountered a wild {wildPokemon.pokemonName.capitalize()}!
{user.display_name} sent out {active.pokemonName.capitalize()}.
'''

        embed = self.__wildPokemonEncounter(user, wildPokemon, active, desc)

        btns = []
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Fight", custom_id='fight'),
            self.__on_fight_click,
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Run away", custom_id='runaway'),
            self.__on_runaway_click,
        ))
        btns.append(self.client.add_callback(
            Button(style=ButtonStyle.green, label="Catch", custom_id='catch'),
            self.__on_catch_click,
        ))

        message = await interaction.edit_origin(
            # content=f'{user.display_name} encountered a wild {pokemon.pokemonName.capitalize()}!',
            embed=embed,
            components=[btns]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, active, wildPokemon, desc)


    async def __on_throw_pokeball(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.send('This is not for you.')
            return


        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        # items = InventoryClass(trainer.discordId)

        if interaction.custom_id == 'pokeball':
            trainer.catch(state.wildPokemon, 'poke-ball')
        elif interaction.custom_id == 'greatball':
            trainer.catch(state.wildPokemon, 'great-ball')
        elif interaction.custom_id == 'ultraball':
            trainer.catch(state.wildPokemon, 'ultra-ball')
        elif interaction.custom_id == 'masterball':
            trainer.catch(state.wildPokemon, 'master-ball')

        desc = state.descLog
        desc += f'''{user.display_name} threw a {interaction.custom_id}!
{trainer.message}
'''

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, state.activePokemon, desc)
        
        await interaction.edit_origin(
            # content=f'{trainer.message}',
            embed=embed,
            components=[]
        )
        del self.__useractions[str(user.id)]
    

    def __wildPokemonEncounter(self, user: discord.User, wildPokemon: PokemonClass, activePokemon: PokemonClass, descLog: str):
        stats = wildPokemon.getPokeStats()
        color = getTypeColor(wildPokemon.type1)
        # Create the embed object
        embed = discord.Embed(
            title=f"Wild {wildPokemon.pokemonName.capitalize()}",
            # description=descLog,
            color=color
        )
        embed.set_author(name=f"{user.display_name}",
                        icon_url=str(user.avatar_url))
        
        types = wildPokemon.type1
        # Pokemon are not guaranteed to have a second type.
        # Check that the second type is not set to None and is not an empty string.
        if wildPokemon.type2 is not None and wildPokemon.type2:
            types += ', ' + wildPokemon.type2

        activeTypes = activePokemon.type1
        if activePokemon.type2 is not None and activePokemon.type2:
            activeTypes += ', ' + activePokemon.type2
            
        # embed.add_field(
        #     name="Type", value=f"{types}", inline=False)
        # embed.add_field(
        #     name="Level", value=f"{pokemon.currentLevel}", inline=True)
        # embed.add_field(
        #     name="HP", value=f"{pokemon.currentHP} / {stats['hp']}", inline=True)

        activeStats = activePokemon.getPokeStats()

        embed.add_field(
            name=f"{activePokemon.pokemonName.capitalize()}",
            value=f'''
Type : {activeTypes}
Level : {activePokemon.currentLevel}
HP    : {activePokemon.currentHP} / {activeStats['hp']}
            ''',
            inline=True
        )

        embed.add_field(
            name=f"{wildPokemon.pokemonName.capitalize()}",
            value=f'''
Type  : {types}
Level : {wildPokemon.currentLevel}
HP    : {wildPokemon.currentHP} / {stats['hp']}
            ''',
            inline=True
        )

        embed.set_thumbnail(url=wildPokemon.frontSpriteURL)
        embed.set_image(url = activePokemon.backSpriteURL)
        
        # activeStats = active.getPokeStats()

        embed.set_footer(text=descLog)
        return embed


#     def __wildPokemonEncounter(self, user: discord.User, pokemon: PokemonClass, active: PokemonClass, descLog: str):
#         stats = pokemon.getPokeStats()
#         color = getTypeColor(pokemon.type1)
#         # Create the embed object
#         embed = discord.Embed(
#             title=f"Wild {pokemon.pokemonName.capitalize()}",
#             description=descLog,
#             color=color
#         )
#         embed.set_author(name=f"{user.display_name}",
#                         icon_url=str(user.avatar_url))
        
#         types = pokemon.type1
#         # Pokemon are not guaranteed to have a second type.
#         # Check that the second type is not set to None and is not an empty string.
#         if pokemon.type2 is not None and pokemon.type2:
#             types += ', ' + pokemon.type2

#         embed.add_field(
#             name="Type", value=f"{types}", inline=False)
#         embed.add_field(
#             name="Level", value=f"{pokemon.currentLevel}", inline=True)
#         embed.add_field(
#             name="HP", value=f"{pokemon.currentHP} / {stats['hp']}", inline=True)

#         embed.set_thumbnail(url=pokemon.frontSpriteURL)
#         embed.set_image(url = active.backSpriteURL)
        
#         activeStats = active.getPokeStats()

#         embed.set_footer(text=f'''
# {active.pokemonName.capitalize()}
# Level: {active.currentLevel}
# HP: {active.currentHP} / {activeStats['hp']}
#         ''')
#         return embed


    def __checkUserActionState(self, user: discord.User, message: discord.Message):
        state: ActionState
        if str(user.id) not in self.__useractions.keys():
            return False
        else:
            state = self.__useractions[str(user.id)]
            if state.messageId != message.id:
                return False
        return True
