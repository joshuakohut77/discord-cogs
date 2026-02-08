import re
import logging

import discord
from redbot.core import Config, checks, commands
from redbot.core.i18n import Translator, cog_i18n

from .unicode_codes import UNICODE_EMOJI

_ = Translator("EmojiReactions", __file__)
log = logging.getLogger("red.emojireact")

# Match custom Discord emojis
EMOJI = re.compile(r"<(a)?:([0-9a-zA-Z_]+):([0-9]+)>")

# Build unicode emoji regex - sort by length (longest first) to match composite emojis properly
UNICODE_RE = re.compile(
    "|".join(re.escape(emoji) for emoji in sorted(UNICODE_EMOJI.keys(), key=len, reverse=True))
)


@cog_i18n(_)
class EmojiReactions(commands.Cog):
    """Automatically react to messages with emojis in them with the emoji"""

    def __init__(self, bot):
        self.bot = bot
        default_guild = {"unicode": False, "guild": False}
        self.config = Config.get_conf(self, 35677998656)
        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    @commands.group()
    @checks.admin_or_permissions(manage_messages=True)
    async def emojireact(self, ctx):
        """Automatically react to messages with emojis in them with the emoji"""
        if ctx.invoked_subcommand is not None:
            return

        guild = ctx.guild
        guild_emoji = await self.config.guild(guild).guild()
        unicode_emoji = await self.config.guild(guild).unicode()
        
        if ctx.channel.permissions_for(ctx.me).embed_links:
            em = discord.Embed(
                colour=discord.Colour.blue(),
                title=_("Emojireact settings for ") + guild.name
            )
            if guild_emoji:
                em.add_field(name=_("Server Emojis"), value=str(guild_emoji))
            if unicode_emoji:
                em.add_field(name=_("Unicode Emojis"), value=str(unicode_emoji))
            
            if em.fields:
                await ctx.send(embed=em)
        else:
            msg = _("Emojireact settings for ") + guild.name + "\n"
            if guild_emoji:
                msg += _("Server Emojis: ") + str(guild_emoji) + "\n"
            if unicode_emoji:
                msg += _("Unicode Emojis: ") + str(unicode_emoji) + "\n"
            await ctx.send(msg)

    @emojireact.command(name="unicode")
    async def _unicode(self, ctx):
        """Toggle unicode emoji reactions"""
        current = await self.config.guild(ctx.guild).unicode()
        await self.config.guild(ctx.guild).unicode.set(not current)
        
        if current:
            msg = _("Okay, I will not react to messages containing unicode emojis!")
        else:
            msg = _("Okay, I will react to messages containing unicode emojis!")
        
        await ctx.send(msg)

    @emojireact.command(name="guild")
    async def _guild(self, ctx):
        """Toggle guild emoji reactions"""
        current = await self.config.guild(ctx.guild).guild()
        await self.config.guild(ctx.guild).guild.set(not current)
        
        if current:
            msg = _("Okay, I will not react to messages containing server emojis!")
        else:
            msg = _("Okay, I will react to messages containing server emojis!")
        
        await ctx.send(msg)

    @emojireact.command(name="all")
    async def _all(self, ctx):
        """Toggle all emoji reactions"""
        guild_emoji = await self.config.guild(ctx.guild).guild()
        unicode_emoji = await self.config.guild(ctx.guild).unicode()
        
        # If either is enabled, disable both; otherwise enable both
        enable = not (guild_emoji or unicode_emoji)
        
        await self.config.guild(ctx.guild).guild.set(enable)
        await self.config.guild(ctx.guild).unicode.set(enable)
        
        if enable:
            msg = _("Okay, I will react to messages containing all emojis!")
        else:
            msg = _("Okay, I will not react to messages containing all emojis!")
        
        await ctx.send(msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Skip if not in a guild
        if message.guild is None:
            return
        
        # Skip if bot doesn't have permission to add reactions
        if not message.channel.permissions_for(message.guild.me).add_reactions:
            return
        
        # Skip bot messages
        if message.author.bot:
            return
        
        emoji_list = []
        
        # Check for custom guild emojis
        if await self.config.guild(message.guild).guild():
            for match in EMOJI.finditer(message.content):
                animated = match.group(1)  # 'a' if animated, None otherwise
                name = match.group(2)
                emoji_id = match.group(3)
                
                # Construct the emoji object
                emoji = discord.utils.get(self.bot.emojis, id=int(emoji_id))
                if emoji:
                    emoji_list.append(emoji)
        
        # Check for unicode emojis
        if await self.config.guild(message.guild).unicode():
            for emoji in UNICODE_RE.findall(message.content):
                if emoji and emoji not in emoji_list:
                    emoji_list.append(emoji)
        
        # Add reactions
        if emoji_list:
            for emoji in emoji_list:
                try:
                    await message.add_reaction(emoji)
                except discord.errors.Forbidden:
                    log.debug(f"Missing permissions to add reaction in {message.guild}")
                    return
                except discord.errors.HTTPException as e:
                    log.debug(f"Failed to add reaction: {e}")
                    continue
                except Exception as e:
                    log.error(f"Unexpected error adding reaction: {e}")
                    continue