from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING

import discord
from discord_components import (ButtonStyle, Button, Interaction)

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from models.location import LocationModel
from services.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass

from .abcd import MixinMeta


locationDisplayNames = {
    "digletts-cave": 'Digletts Cave',
    "mt-moon": 'Mt. Moon',
    "pallet-town": 'Pallet Town',
    "rock-tunnel": 'Rock Tunnel',
    "kanto-route-1": 'Route 1',
    "kanto-route-11": 'Route 11',
    "kanto-route-12": 'Route 12',
    "kanto-route-13": 'Route 13',
    "kanto-route-14": 'Route 14',
    "kanto-route-15": 'Route 15',
    "kanto-route-16": 'Route 16',
    "kanto-route-17": 'Route 17',
    "kanto-route-18": 'Route 18',
    "kanto-sea-route-19": 'Sea Route 19',
    "kanto-route-2": 'Route 2',
    "kanto-sea-route-20": 'Sea Route 20',
    "kanto-sea-route-21": 'Sea Route 21',
    "kanto-route-22": 'Route 22',
    "kanto-route-24": 'Route 24',
    "kanto-route-25": 'Route 25',
    "kanto-route-3": 'Route 3',
    "kanto-route-5": 'Route 5',
    "kanto-route-6": 'Route 6',
    "kanto-route-7": 'Route 7',
    "kanto-route-8": 'Route 8',
    "kanto-route-9": 'Route 9',
    "seafoam-islands": 'Seafoam Islands',
    "cerulean-cave": 'Cerulean Cave',
    "kanto-victory-road-1": 'Victory Road 1',
    "viridian-forest": 'Viridian Forest',
    "kanto-route-23": 'Route 23',
    "power-plant": 'Power Plant',
    "kanto-victory-road-2": 'Victory Road 2',
    "pokemon-tower": 'Pokémon Tower',
    "pokemon-mansion": 'Pokémon Mansion',
    "kanto-safari-zone": 'Safari Zone',
    "ss-anne": 'S.S. Anne',
    "celadon-city": 'Celadon City',
    "kanto-route-10": 'Route 10',
    "kanto-route-4": 'Route 4',
    "indigo-plateau": 'Indigo Plateau',
    "vermilion-city": 'Vermilion City',
    "pewter-city": 'Pewter City',
    "lavender-town": 'Lavender Town',
    "cerulean-city": 'Cerulean City',
    "cinnabar-island": 'Cinnabar Island',
    "fuchsia-city": 'Fuchsia City',
    "saffron-city": 'Saffron City',
    "viridian-city": 'Viridian City',
    "underground-path": 'Underground Path'
}


class LocationState:
    discordId: str
    location: LocationModel
    messageId: int

    def __init__(self, discordId: str, location: LocationModel, messageId: int) -> None:
        self.discordId = discordId
        self.location = location
        self.messageId = messageId


class MapMixin(MixinMeta):
    """Map"""

    __locations: dict[str, LocationState] = {}

    @commands.group(name="trainer")
    @commands.guild_only()
    async def _trainer(self, ctx: commands.Context) -> None:
        """Base command to manage the trainer (user).
        """

    @_trainer.command()
    async def map(self, ctx: commands.Context, user: discord.User = None):
        if user is None:
            user = ctx.author

        
        trainer = TrainerClass(str(user.id))
        location = trainer.getLocation()

        file, btns = self.__createMapCard(location)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} is at {location.name}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = locationDisplayNames[location.name]
        embed = discord.Embed(title = f'{name}', description = f'You are at {name}.')
        embed.set_image(url = attachment.url)

        message = await ctx.send(
            embed=embed,
            components=btns
        )
        # message = await ctx.send(
        #     content=location.name,
        #     file=file,
        #     components=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), location, message.id)
    

    def __createMapCard(self, location: LocationModel, disabled = False):
        file = discord.File(f"{location.spritePath}", filename=f"{location.name}.png")

        ne = []
        sw = []
        if location.north is not None:
            north = locationDisplayNames[location.north]
            ne.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬆', label=f"{north}", disabled=disabled),
                self.__on_north,
            ))
        else:
            ne.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬆', label=f"--", disabled=disabled),
                self.__on_north,
            ))
        if location.east is not None:
            east = locationDisplayNames[location.east]
            ne.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='➡', label=f"{east}", disabled=disabled),
                self.__on_east,
            ))
        else:
            ne.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='➡', label=f"--", disabled=disabled),
                self.__on_east,
            ))
        if location.south is not None:
            south = locationDisplayNames[location.south]
            sw.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬇', label=f"{south}", disabled=disabled),
                self.__on_south,
            ))
        else:
            sw.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬇', label=f"--", disabled=disabled),
                self.__on_south,
            ))
        if location.west is not None:
            west = locationDisplayNames[location.west]
            sw.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬅', label=f"{west}", disabled=disabled),
                self.__on_west,
            ))
        else:
            sw.append(self.client.add_callback(
                Button(style=ButtonStyle.gray, emoji='⬅', label=f"--", disabled=disabled),
                self.__on_west,
            ))

        btns = [ne, sw]

        return file, btns


    async def __on_north(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        north = state.location.north

        if north is None:
            await interaction.send('You can not travel North from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(north)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.send(f'You walked North to {north}.')

        file, btns = self.__createMapCard(direction, disabled=False)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} walked North to {north}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = locationDisplayNames[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked North to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.edit_origin(
            embed=embed,
            components=btns
        )
        # message = await interaction.edit_origin(
        #     content=f'You walked North to {north}.',
        #     file=file,
        #     components=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)
        

    async def __on_south(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        south = state.location.south

        if south is None:
            await interaction.send('You can not travel South from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(south)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.send(f'You walked South to {south}.')

        file, btns = self.__createMapCard(direction)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} walked South to {south}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = locationDisplayNames[direction.name]
        
        embed = discord.Embed(title = f'{name}', description = f'You walked South to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.edit_origin(
            embed=embed,
            components=btns
        )

        # message = await interaction.edit_origin(
        #     content=f'You walked South to {south}.',
        #     file=file,
        #     components=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)


    async def __on_east(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        east = state.location.east

        if east is None:
            await interaction.send('You can not travel East from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(east)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.send(f'You walked East to {east}.')

        file, btns = self.__createMapCard(direction)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} walked East to {east}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = locationDisplayNames[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked East to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.edit_origin(
            embed=embed,
            components=btns
        )
        # message = await interaction.edit_origin(
        #     content=f'You walked East to {east}.',
        #     file=file,
        #     components=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)


    async def __on_west(self, interaction: Interaction):
        user = interaction.user

        if not self.__checkMapState(user, interaction.message):
            await interaction.send('This is not for you.')
            return

        state = self.__locations[str(user.id)]
        west = state.location.west

        if west is None:
            await interaction.send('You can not travel West from here.')
            return

        loc = LocationClass()
        direction = loc.getLocationByName(west)
        if loc.statuscode == 96:
            await interaction.send(loc.message)
            return

        trainer = TrainerClass(str(user.id))
        trainer.setLocation(direction.locationId)
        # await interaction.send(f'You walked West to {west}.')

        file, btns = self.__createMapCard(direction)

        log_channel: discord.TextChannel = self.bot.get_channel(971280525312557157)
        temp_message = await log_channel.send(
            content=f'{user.display_name} walked West to {west}',
            file = file
        )
        attachment: discord.Attachment = temp_message.attachments[0]

        name = locationDisplayNames[direction.name]

        embed = discord.Embed(title = f'{name}', description = f'You walked West to {name}.')
        embed.set_image(url = attachment.url)

        message = await interaction.edit_origin(
            embed=embed,
            components=btns
        )
        # message = await interaction.edit_origin(
        #     content=f'You walked West to {west}.',
        #     file=file,
        #     components=btns
        # )
        self.__locations[str(user.id)] = LocationState(str(user.id), direction, message.id)


    def __checkMapState(self, user: discord.User, message: discord.Message):
        state: LocationState
        if str(user.id) not in self.__locations.keys():
            return False
        else:
            state = self.__locations[str(user.id)]
            if state.messageId != message.id:
                return False
        return True