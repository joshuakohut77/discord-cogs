from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABCMeta

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from ChodeCoin.core.event import EventMixin


class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class ChodeCoin(EventMixin, commands.Cog, metaclass=CompositeClass):
    """chodecoin"""

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot


from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta

if TYPE_CHECKING:
    from redbot.core.bot import Red

import emojis

import discord
from redbot.core import Config, commands

from .event import EventMixin


class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class ReactEmoji(EventMixin, commands.Cog, metaclass=CompositeClass):
    """React Emojis."""

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, identifier=2091831, force_registration=True)
        default_channel: Dict[str, Any] = {
            "enabled": False,
            "emojis": ["\U0001F44D", "\U0001F44E"],
            "frequency": 1,
            "next_react_time": 0.0,
            "multiplier": 5,
        }
        default_guild: Dict[str, List[str]] = {
            "websites": [],
            "extensions": [],
        }
        self.config.register_channel(**default_channel)
        self.config.register_guild(**default_guild)

    @commands.group(name="list")
    @commands.guild_only()
    async def _list(self, ctx: commands.Context) -> None:
        """List emojis, extensions or websites for the current channel."""
        pass

    @_list.command()
    async def websites(self, ctx: commands.Context) -> None:
        """Get the websites links for the current guild."""
        if not (websites := await self.config.guild(ctx.guild).websites()):
            await ctx.send("There's no website for that channel.")
            return

        await ctx.send(", ".join(f"`{website}`" for website in websites))

    @_list.command(name="extensions")
    async def _extensions(self, ctx: commands.Context) -> None:
        """Get the extensions for the current guild."""
        if not (extensions := await self.config.guild(ctx.guild).extensions()):
            await ctx.send("There's no extension for that channel.")
            return

        await ctx.send(", ".join(f"`{extension}`" for extension in extensions))

    @_list.command(name="emojis")
    async def _emojis(self, ctx: commands.Context) -> None:
        """Get the emojis for the current channel."""
        if not (emojis := await self.config.channel(ctx.channel).emojis()):
            await ctx.send("There's no emoji for that channel.")
            return

        emoji_list = []
        for emoji in emojis:
            if isinstance(emoji, int):
                if not (emoji := self.bot.get_emoji(emoji)):
                    continue
            emoji_list.append(str(emoji))
        await ctx.send(", ".join(emoji_list))

    @commands.group()
    @commands.mod_or_permissions()
    @commands.guild_only()
    async def emojiadmin(self, ctx: commands.Context) -> None:
        """Gets the admin commands for react emojis cog."""
        pass

    @emojiadmin.command()
    async def frequency(self, ctx: commands.Context, frequency: int) -> None:
        """Change the reacting frequency for the current channel."""
        if frequency <= 0:
            await ctx.send("Value must be above 0!")
            return

        await self.config.channel(ctx.channel).set_raw("frequency", value=frequency)
        await ctx.tick()

    @emojiadmin.command()
    async def enable(self, ctx: commands.Context, true_or_false: bool) -> None:
        """Enable / Disable the reaction system."""
        await self.config.channel(ctx.channel).set_raw("enabled", value=true_or_false)
        await ctx.tick()

    @emojiadmin.command()
    async def multiplier(self, ctx: commands.Context, number: int) -> None:
        """Change the multiplier to change the chance a message can be reacted to from the bot."""
        if number <= 0:
            await ctx.send("Please set a number higher than zero!")
            return

        await self.config.channel(ctx.channel).set_raw("multiplier", value=number)
        await ctx.tick()

    @emojiadmin.group()
    async def site(self, ctx: commands.Context) -> None:
        """Add / Remove a website from the checking list."""
        pass

    @site.command(name="add")
    async def _add(self, ctx: commands.Context, website: str) -> None:
        """Add a website to the checking list."""
        website: str = website.lower()
        async with self.config.guild(ctx.guild).websites() as websites:
            if website in websites:
                await ctx.send("That website already exists in the checking list.")
                return
            websites.append(website)
        await ctx.tick()

    @site.command(name="remove")
    async def _remove(self, ctx: commands.Context, website: str) -> None:
        """Remove a website from the checking list."""
        website: str = website.lower()
        async with self.config.guild(ctx.guild).websites() as websites:
            if website not in websites:
                await ctx.send("That website doesn't exists in the checking list.")
                return
            websites.remove(website)
        await ctx.tick()

    @emojiadmin.group()
    async def extensions(self, ctx: commands.Context) -> None:
        """Add / Remove an extension from the checking list."""
        pass

    @extensions.command(name="add")
    async def _add_(self, ctx: commands.Context, extension: str) -> None:
        """Add an extension to the checking list."""
        extension: str = extension.lower()
        async with self.config.guild(ctx.guild).extensions() as extensions:
            if extension in extensions:
                await ctx.send("That extension already exists in the checking list.")
                return
            extensions.append(extension)
        await ctx.tick()

    @extensions.command(name="remove")
    async def _remove_(self, ctx: commands.Context, extension: str) -> None:
        """Remove an extension from the checking list."""
        extension: str = extension.lower()
        async with self.config.guild(ctx.guild).extensions() as extensions:
            if extension not in extensions:
                await ctx.send("That extension doesn't exists in the checking list.")
                return
            extensions.remove(extension)
        await ctx.tick()

    @emojiadmin.group(name="emoji")
    async def _emoji(self, ctx: commands.Context) -> None:
        """Add / Remove an emoji from the emojis list for the current channel."""
        pass

    @_emoji.command()
    async def add(self, ctx: commands.Context, *, emoji: str) -> None:
        """Add an emoji to the emojis list for the current channel."""
        try:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=emoji)
        except:
            if emojis.count(emoji) > 1:
                await ctx.send("Please provide one emoji only.")
                return
            emote: list = list(emojis.get(emoji))

        if not emote or emote is None:
            await ctx.send("Couldn't find any emoji, please retry.")
            return

        async with self.config.channel(ctx.channel).emojis() as emoji:
            if isinstance(emote, discord.Emoji):
                emoji.append(emote.id)
            else:
                emoji.append(emote[0])
        await ctx.tick()

    @_emoji.command()
    async def remove(self, ctx: commands.Context, *, emoji: str) -> None:
        """Remove an emoji from the emojis list for the current channel."""
        try:
            emote: discord.Emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=emoji)
        except:
            if emojis.count(emoji) > 1:
                await ctx.send("Please provide one emoji only.")
                return
            emote: list = list(emojis.get(emoji))

        if not emote or emote is None:
            await ctx.send("Couldn't find any emoji, please retry.")
            return

        async with self.config.channel(ctx.channel).emojis() as emoji:
            try:
                if isinstance(emote, discord.Emoji):
                    emoji.remove(emote.id)
                else:
                    emoji.remove(emote[0])
            except:
                await ctx.send("That emoji is not in the list.")
                return

        await ctx.tick()








