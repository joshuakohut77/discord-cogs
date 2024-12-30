from __future__ import annotations
from re import A
from typing import Any, Dict, List, Union, TYPE_CHECKING
import asyncio

import discord
from discord import (Embed, Member)
from discord import message
# from discord_components import (
#     DiscordComponents, ButtonStyle, ComponentsBot, Button, Interaction, component)
# from discord import ui, ButtonStyle, Button, Interaction
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

import constant
from models.location import LocationModel
from models.actionmodel import ActionModel, ActionType
from services.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass
from services.inventoryclass import inventory as InventoryClass
from services.pokeclass import Pokemon as PokemonClass

from .abcd import MixinMeta
from .functions import (getTypeColor)
from .helpers import (getTrainerGivenPokemonName)


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
        methods: list[ActionModel] = location.getMethods()

        if len(methods) == 0:
            await ctx.send('No encounters available at your location.')
            return

        view = View()
        for method in methods:
            button = Button(style=ButtonStyle.gray, label=f"{method.name}", custom_id=f'{method.value}', disabled=False)
            button.callback = self.on_action
            view.add_item(button)

        message: discord.Message = await ctx.send(
            content="What do you want to do?",
            view=view
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, model, trainer.getActivePokemon(), None, '')

    # @discord.ui.button(custom_id='clickNorth', style=ButtonStyle.gray)
    async def on_action(self, interaction: discord.Interaction):
        await self.__on_action(interaction)

    async def __on_action(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        location = LocationClass(str(user.id))
        methods: list[ActionModel] = location.getMethods()

        btns = []
        for method in methods:
            color = ButtonStyle.gray
            if method == interaction.data['custom_id']:
                color = ButtonStyle.green
            
            btns.append(
                Button(style=color, label=f"{method.name}", custom_id=f'{method.value}', disabled=True)
            )

        # Check for the possibility of too many actions
        if len(btns) > 3:
            firstRow = btns[:3]
            secondRow = btns[3:]
            btns = [firstRow, secondRow]
        else:
            btns = [btns]
        

        action: ActionModel
        for method in methods:
            if method.value == interaction.data['custom_id']:
                action = method
                break

        msg = 'Walking through tall grass...'

        if action.value == 'old-rod':
            msg = 'Fishing with an old rod...'
        elif action.value == 'good-rod':
            msg = 'Fishing with a good rod...'
        elif action.value == 'super-rod':
            msg = 'Fishing with a super rod...'
        elif action.value == 'gift':
            msg = 'Waiting to receive a gift...'
        elif action.value == 'pokeflute':
            msg = 'You played the Poké Flute!'

        await interaction.message.edit(
            content=msg,
            view=btns
        )

        # await interaction.respond(type=5, content="Walking through tall grass...")

        state = self.__useractions[str(user.id)]
        method = interaction.data['custom_id']

        # if method == 'walk':
        trainer = TrainerClass(str(user.id))


        if ActionType.GIFT.value == action.type.value:
            trainer.gift()
            await interaction.channel.send(trainer.message)
            return
        
        if ActionType.QUEST.value == action.type.value:
            trainer.quest(interaction.custom_id)
            await interaction.channel.send(trainer.message)
            return


        wildPokemon: PokemonClass
        # Only one can potentially trigger a pokemon encounter
        if ActionType.ONLYONE.value == action.type.value:
            wildPokemon = trainer.onlyone()
            if wildPokemon is None:
                if trainer.statuscode == 420:
                    await interaction.channel.send(trainer.message)
                else:
                    await interaction.channel.send('No pokemon encountered.')
                return


            # await interaction.channel.send(trainer.message)

        # A wild pokemon encounter
        if ActionType.ENCOUNTER.value == action.type.value:
            wildPokemon = trainer.encounter(method)
            if wildPokemon is None:
                if trainer.statuscode == 420:
                    await interaction.channel.send(trainer.message)
                else:
                    await interaction.channel.send('No pokemon encountered.')
                # await interaction.response.send_message('No pokemon encountered.')
                return

        # active = trainer.getActivePokemon()
        active = state.activePokemon
        
        # await interaction.response.send_message(f'You encountered a wild {pokemon.pokemonName}!')
        desc = f'''
{user.display_name} encountered a wild {wildPokemon.pokemonName.capitalize()}!
{user.display_name} sent out {getTrainerGivenPokemonName(active)}.
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
            view=[btns]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, active, wildPokemon, desc)


    async def __on_fight_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        await interaction.respond(type=5, content="Battling...")

        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))

        # await interaction.edit_original_response(
        #     content=f'{trainer.message}',
        #     embed=embed,
        #     view=[]
        # )

        trainer.fight(state.wildPokemon)

        if trainer.statuscode == 96:
            await interaction.response.send_message(trainer.message)
            return

        channel: discord.TextChannel = self.bot.get_channel(state.channelId)
        message: discord.Message = await channel.fetch_message(state.messageId)

        desc = state.descLog
        desc += f'''{user.display_name} chose to fight!
{trainer.message}
'''
        active = trainer.getActivePokemon()

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, active, desc)

        await interaction.response.send_message(trainer.message)
        # await interaction.channel.send(
        await message.edit(
            content=f'{trainer.message}',
            embed=embed,
            view=[]
        )
        del self.__useractions[str(user.id)]


    async def __on_runaway_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        state = self.__useractions[str(user.id)]
        trainer = TrainerClass(str(user.id))
        trainer.runAway(state.wildPokemon)

        if trainer.statuscode == 96:
            interaction.response.send_message(trainer.message)
            return

        desc = state.descLog
        desc += f'''{user.display_name} chose to run away.
{trainer.message}
'''

        embed = self.__wildPokemonEncounter(user, state.wildPokemon, state.activePokemon, desc)


        await interaction.edit_original_response(
            # content=f'{user.display_name} ran away from a wild {state.pokemon.pokemonName.capitalize()}!',
            embed=embed,
            view=[]
        )
        del self.__useractions[str(user.id)]
        

    async def __on_catch_click(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
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
            # TODO: Achievement Unlocked: No Balls
            await interaction.response.send_message('You have no balls!')
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
        
        message = await interaction.edit_original_response(
            embed=embed,
            view=[btns, secondRow]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, state.activePokemon, state.wildPokemon, desc)


    async def __on_catch_back(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
            return

        # active = trainer.getActivePokemon()
        state = self.__useractions[str(user.id)]
        wildPokemon = state.wildPokemon
        active = state.activePokemon
        
        # await interaction.response.send_message(f'You encountered a wild {pokemon.pokemonName}!')
        desc = f'''
{user.display_name} encountered a wild {wildPokemon.pokemonName.capitalize()}!
{user.display_name} sent out {getTrainerGivenPokemonName(active)}.
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

        message = await interaction.edit_original_response(
            # content=f'{user.display_name} encountered a wild {pokemon.pokemonName.capitalize()}!',
            embed=embed,
            view=[btns]
        )
        self.__useractions[str(user.id)] = ActionState(
            str(user.id), message.channel.id, message.id, state.location, active, wildPokemon, desc)


    async def __on_throw_pokeball(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkUserActionState(user, interaction.message):
            await interaction.response.send_message('This is not for you.')
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
        
        await interaction.edit_original_response(
            embed=embed,
            view=[]
        )
        del self.__useractions[str(user.id)]

        # Send to logging channel
        await self.sendToLoggingChannel(None, embed=embed)
    

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
                        icon_url=str(user.display_avatar.url))
        
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
            name=f"{getTrainerGivenPokemonName(activePokemon)}",
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
#                         icon_url=str(user.display_avatar.url))
        
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
