from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red
    from discord import SelectMenu

import discord

from discord import Button, ActionRow
from redbot.core import Config, commands

from .selectmenu import Select

class v2Books(commands.Cog):
    """
    A components cog with selectable options.
    """
    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config: Config = Config.get_conf(self, identifier=9382473289424, force_registration=True)
        self.select: ActionRow = Select.create()
        self.booksdata: dict = self.select.data
        default_channel: dict = {}
        self.config.register_channel(**default_channel)

    @commands.Cog.listener()
    async def on_raw_selection_select(self, i: discord.Interaction, select_menu: SelectMenu) -> None:
        await i.defer()

        if select_menu.custom_id != "bookselector":
            return

        embed: discord.Embed = i.message.embeds[0]

        async with self.config.channel(i.message.channel)() as channel:
            channel[str(i.message.id)]["selected_menu"] = select_menu.values[0]

        select_menu.placeholder = select_menu.values[0]

        buttons: list[Button] = []
        for book in self.booksdata[select_menu.values[0]]:
            buttons.append(Button(label=book["name"], custom_id=f"book-{book['name']}"))
        buttons: ActionRow = ActionRow(*buttons)

        await i.message.edit(embed=embed, components=[select_menu, buttons])

    @commands.Cog.listener()
    async def on_raw_button_click(self, i: discord.Interaction, button: Button) -> None:
        await i.defer()

        if not any((button.custom_id.startswith("book-"), button.custom_id.startswith("but-"),)):
            return

        embed: discord.Embed = i.message.embeds[0]
        components: list[ActionRow] = [i.message.components[0], i.message.components[1]]
        
        async with self.config.channel(i.message.channel)() as channel:
            if button.custom_id not in ("but-prev", "but-next",):
                channel[str(i.message.id)]["selected_book"] = button.custom_id.split("-", 1)[1]
                channel[str(i.message.id)]["page"] = 0

        selected_menu: str = channel[str(i.message.id)]["selected_menu"]
        selected_book: str = channel[str(i.message.id)]["selected_book"]
        
        book_index: int = [i for (i, d,) in enumerate(self.booksdata[selected_menu]) if d["name"] == selected_book][0]
        page: int = channel[str(i.message.id)]["page"]

        if len(self.booksdata[selected_menu][book_index]["data"]) > 1:
            previous_next: ActionRow = ActionRow(*[Button(label="\U00002B05", custom_id="but-prev"), Button(label="\U000027A1", custom_id="but-next")])

            if button.custom_id == "but-prev":
                page -= 1
                
            if button.custom_id == "but-next":
                page += 1

            if page <= 0:
                page = 0
                previous_next[0].disabled = True
            
            if page >= len(self.booksdata[selected_menu][book_index]["data"]) - 1:
                page = len(self.booksdata[selected_menu][book_index]["data"]) - 1
                previous_next[1].disabled = True

            components.append(previous_next)

        embed.set_field_at(0, name='Book', value=self.booksdata[selected_menu][book_index]['name'])
        # embed.add_field(name='Book', value=self.booksdata[selected_menu][book_index]['name'])
        embed.description = self.booksdata[selected_menu][book_index]["data"][page]["text"]
        embed.set_image(url=self.booksdata[selected_menu][book_index]["data"][page]["image"])

        async with self.config.channel(i.message.channel)() as channel:
            channel[str(i.message.id)]["page"] = page

        await i.message.edit(embed=embed, components=components)
    
    @commands.command()
    async def v2(self, ctx: commands.Context) -> None:
        embed: discord.Embed = discord.Embed()
        embed.description = "Please select a map first"

        msg: discord.Message = await ctx.send(embed=embed, components=self.select)
        
        async with self.config.channel(ctx.channel)() as channel:
            channel[msg.id] = {}
