from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from .abc import MixinMeta
from discord import embeds

from discord_components import Select, SelectOption, Button,ButtonStyle
from discord_components.client import DiscordComponents

if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands

# from .event import EventMixin

class CompositeClass(commands.CogMeta, MixinMeta):
    __slots__: tuple = ()
    pass

# bot = discord.Bot()

class v2Books(discord.ui.View):
        # client: DiscordComponents
        def __init__(self, bot: Red):
            # self.client: DiscordComponents   
            self.client = DiscordComponents(bot) 
            self.bot: Red = bot
            self.config: Config = Config.get_conf(self, identifier=2091831, force_registration=True)
    
        @discord.ui.select( # the decorator that lets you specify the properties of the select menu
        placeholder = "Choose a Flavor!", # the placeholder text that will be displayed if nothing is selected
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
        options = [ # the list of options from which users can choose, a required field
            discord.SelectOption(
                label="Vanilla",
                description="Pick this if you like vanilla!"
            ),
            discord.SelectOption(
                label="Chocolate",
                description="Pick this if you like chocolate!"
            ),
            discord.SelectOption(
                label="Strawberry",
                description="Pick this if you like strawberry!"
            )
        ]
    )
    async def select_callback(self, select, interaction): # the function called when the user is done selecting options
        await interaction.response.send_message(f"Awesome! I like {select.values[0]} too!")

@bot.command()
async def flavor(ctx):
    await ctx.send("Choose a flavor!", view=MyView())

bot.run("TOKEN")



# class v2Books(commands.Cog, metaclass=CompositeClass):
# # class v2Books(commands.Cog):
#     """Warhammer Books."""
#     # client: DiscordComponents
#     def __init__(self, bot: Red):
#         # self.client: DiscordComponents   
#         self.client = DiscordComponents(bot) 
#         self.bot: Red = bot
#         self.config: Config = Config.get_conf(self, identifier=2091831, force_registration=True)
        
#         # DiscordComponents(bot, change_discord_methods=True)


#     @commands.group(name="v2", aliases=['dex'])
#     # @commands.group()
#     async def __v2(self, ctx: commands.Context) -> None:
#         # """Gets the admin commands for react emojis cog."""
#         # await ctx.send("Received map %s" %map)
#         pass


#     @__v2.command()
#     async def button(self, ctx: commands.Context):
        
#         embed = discord.Embed()
#         embed=discord.Embed(title="Owen Wilson", url="https://www.tomorrowtides.com/owen-wilson-movies.html", color=0x0b1bf4)
#         embed.add_field(name="Movie", value='test movie', inline=True)


#         firstRowBtns = []
#         firstRowBtns.append(self.client.add_callback(
#             Button(style=ButtonStyle.gray, label="Next", custom_id='next'),
#             self.__on_use_item
#         ))
        
#         btns = []
#         if len(firstRowBtns) > 0:
#             btns.append(firstRowBtns)
#         message = await ctx.send(embed=embed, components=btns)
    



#     @__v2.command()
#     async def books(self, ctx: commands.Context) -> None:
#         """Takes a map name and returns books."""
     
#         await ctx.send("message = it kinda worked?")
#         return

#         # await self.config.channel(ctx.channel).set_raw("frequency", value=frequency)
#         # await ctx.tick()
#     # async def __on_use_item(self, ctx: commands.Context):
#     async def __on_use_item(self, ctx):
#         await ctx.send("clicked button")
#         return

#     # @v2Books.group()
#     # async def v2Book(self, ctx: commands.Context) -> None:
#     #     """Add / Remove a website from the checking list."""
#     #     await ctx.send("Received your v2Book command!")
#     #     return
