from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABCMeta
import re
import sys

if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands

from .events import EventMixin
from .database import DankDatabase


class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass


class DankHall(EventMixin, commands.Cog, metaclass=CompositeClass):
    """
    A Hall of Fame system that tracks and celebrates the dankest messages.
    
    When a message receives enough reactions, it gets certified as dank
    and immortalized in a hall of fame channel with full statistics tracking.
    """

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=2091831420, force_registration=True
        )
        
        # Default guild settings
        default_guild = {
            "enabled": True,
            "default_threshold": 5,
            "default_hall_channel": None,
            "blacklisted_channels": [],
            "responses": [
                "🎉 Certified Dank!",
                "⭐ This is peak content!",
                "🏆 Hall of Fame worthy!",
                "💯 Absolutely legendary!",
            ],
            "allowed_emojis": [],  # Empty = all emojis allowed
        }
        
        # Channel-specific overrides
        default_channel = {
            "threshold": None,  # None = use guild default
            "hall_channel": None,  # None = use guild default
        }
        
        self.config.register_guild(**default_guild)
        self.config.register_channel(**default_channel)
        
        # Database connection
        self.db: DankDatabase = None

    async def initialize(self):
        """Initialize the database connection and create tables if needed."""
        self.db = DankDatabase()
        await self.db.create_tables()

    def cog_unload(self):
        """Cleanup when cog is unloaded."""
        if self.db:
            self.db.close()

    # ==================== Configuration Commands ====================

    @commands.group(name="dankhall")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def dankhall(self, ctx: commands.Context):
        """Configure the Dank Hall of Fame system."""
        pass

    @dankhall.command(name="enable")
    async def dh_enable(self, ctx: commands.Context, enabled: bool):
        """Enable or disable the Dank Hall system for this server."""
        await self.config.guild(ctx.guild).enabled.set(enabled)
        status = "enabled" if enabled else "disabled"
        await ctx.send(f"✅ Dank Hall system has been {status}.")

    @dankhall.command(name="threshold")
    async def dh_threshold(self, ctx: commands.Context, count: int):
        """
        Set the default number of reactions needed for certification.
        
        This applies globally unless overridden per-channel.
        """
        if count < 1:
            await ctx.send("❌ Threshold must be at least 1.")
            return
        
        await self.config.guild(ctx.guild).default_threshold.set(count)
        await ctx.send(f"✅ Default threshold set to **{count}** reactions.")

    @dankhall.command(name="channel")
    async def dh_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the default Hall of Fame channel for this server."""
        await self.config.guild(ctx.guild).default_hall_channel.set(channel.id)
        await ctx.send(f"✅ Default Hall of Fame channel set to {channel.mention}.")

    @dankhall.command(name="setchannel")
    async def dh_set_channel(
        self, 
        ctx: commands.Context, 
        source_channel: discord.TextChannel,
        threshold: int = None,
        hall_channel: discord.TextChannel = None
    ):
        """
        Override settings for a specific channel.
        
        Examples:
        - `[p]dankhall setchannel #memes 10` - Set threshold to 10 for #memes
        - `[p]dankhall setchannel #memes 3 #elite-hall` - Set threshold and custom hall
        """
        if threshold is not None and threshold < 1:
            await ctx.send("❌ Threshold must be at least 1.")
            return
        
        await self.config.channel(source_channel).threshold.set(threshold)
        await self.config.channel(source_channel).hall_channel.set(
            hall_channel.id if hall_channel else None
        )
        
        msg = f"✅ Channel override set for {source_channel.mention}:\n"
        if threshold:
            msg += f"  • Threshold: **{threshold}** reactions\n"
        else:
            msg += f"  • Threshold: *Using server default*\n"
        
        if hall_channel:
            msg += f"  • Hall: {hall_channel.mention}"
        else:
            msg += f"  • Hall: *Using server default*"
        
        await ctx.send(msg)

    @dankhall.command(name="resetchannel")
    async def dh_reset_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Remove all overrides for a specific channel."""
        await self.config.channel(channel).clear()
        await ctx.send(f"✅ Removed all overrides for {channel.mention}.")

    @dankhall.command(name="blacklist")
    async def dh_blacklist(self, ctx: commands.Context, channel: discord.TextChannel):
        """Add a channel to the blacklist (prevents certification)."""
        async with self.config.guild(ctx.guild).blacklisted_channels() as blacklist:
            if channel.id in blacklist:
                await ctx.send(f"❌ {channel.mention} is already blacklisted.")
                return
            blacklist.append(channel.id)
        
        await ctx.send(f"✅ {channel.mention} has been blacklisted.")

    @dankhall.command(name="unblacklist")
    async def dh_unblacklist(self, ctx: commands.Context, channel: discord.TextChannel):
        """Remove a channel from the blacklist."""
        async with self.config.guild(ctx.guild).blacklisted_channels() as blacklist:
            if channel.id not in blacklist:
                await ctx.send(f"❌ {channel.mention} is not blacklisted.")
                return
            blacklist.remove(channel.id)
        
        await ctx.send(f"✅ {channel.mention} has been removed from the blacklist.")

    @dankhall.command(name="addemoji")
    async def dh_add_emoji(self, ctx: commands.Context, emoji: str):
        """
        Add an emoji to the allowed list.
        
        If the allowed list is empty, all emojis are accepted.
        Once you add emojis here, ONLY these emojis will trigger certification.
        """
        # Try to parse as custom emoji first
        try:
            custom_emoji = await commands.EmojiConverter().convert(ctx, emoji)
            emoji_id = str(custom_emoji.id)
        except:
            # It's a unicode emoji
            emoji_id = emoji
        
        async with self.config.guild(ctx.guild).allowed_emojis() as emojis:
            if emoji_id in emojis:
                await ctx.send(f"❌ {emoji} is already in the allowed list.")
                return
            emojis.append(emoji_id)
        
        await ctx.send(f"✅ Added {emoji} to the allowed emoji list.")

    @dankhall.command(name="removeemoji")
    async def dh_remove_emoji(self, ctx: commands.Context, emoji: str):
        """Remove an emoji from the allowed list."""
        try:
            custom_emoji = await commands.EmojiConverter().convert(ctx, emoji)
            emoji_id = str(custom_emoji.id)
        except:
            emoji_id = emoji
        
        async with self.config.guild(ctx.guild).allowed_emojis() as emojis:
            if emoji_id not in emojis:
                await ctx.send(f"❌ {emoji} is not in the allowed list.")
                return
            emojis.remove(emoji_id)
        
        await ctx.send(f"✅ Removed {emoji} from the allowed emoji list.")

    @dankhall.command(name="addresponse")
    async def dh_add_response(self, ctx: commands.Context, *, response: str):
        """Add a response message when a post gets certified."""
        async with self.config.guild(ctx.guild).responses() as responses:
            if response in responses:
                await ctx.send("❌ That response already exists.")
                return
            responses.append(response)
        
        await ctx.send(f"✅ Added response: {response}")

    @dankhall.command(name="removeresponse")
    async def dh_remove_response(self, ctx: commands.Context, *, response: str):
        """Remove a response message."""
        async with self.config.guild(ctx.guild).responses() as responses:
            if response not in responses:
                await ctx.send("❌ That response doesn't exist.")
                return
            responses.remove(response)
        
        await ctx.send(f"✅ Removed response: {response}")

    @dankhall.command(name="settings")
    async def dh_settings(self, ctx: commands.Context):
        """View current Dank Hall settings for this server."""
        guild_config = await self.config.guild(ctx.guild).all()
        
        embed = discord.Embed(
            title="🏆 Dank Hall Settings",
            color=discord.Color.gold()
        )
        
        # Status
        status = "✅ Enabled" if guild_config["enabled"] else "❌ Disabled"
        embed.add_field(name="Status", value=status, inline=True)
        
        # Threshold
        embed.add_field(
            name="Default Threshold",
            value=f"{guild_config['default_threshold']} reactions",
            inline=True
        )
        
        # Hall Channel
        hall_id = guild_config["default_hall_channel"]
        if hall_id:
            channel = ctx.guild.get_channel(hall_id)
            hall_text = channel.mention if channel else "*Channel not found*"
        else:
            hall_text = "*Not set*"
        embed.add_field(name="Default Hall Channel", value=hall_text, inline=True)
        
        # Blacklisted Channels
        blacklist = guild_config["blacklisted_channels"]
        if blacklist:
            blacklist_text = ", ".join(
                f"<#{ch_id}>" for ch_id in blacklist[:5]
            )
            if len(blacklist) > 5:
                blacklist_text += f" *+{len(blacklist) - 5} more*"
        else:
            blacklist_text = "*None*"
        embed.add_field(name="Blacklisted Channels", value=blacklist_text, inline=False)
        
        # Allowed Emojis
        emojis = guild_config["allowed_emojis"]
        if emojis:
            emoji_text = " ".join(emojis[:10])
            if len(emojis) > 10:
                emoji_text += f" *+{len(emojis) - 10} more*"
        else:
            emoji_text = "*All emojis allowed*"
        embed.add_field(name="Allowed Emojis", value=emoji_text, inline=False)
        
        # Responses
        responses = guild_config["responses"]
        embed.add_field(
            name="Responses",
            value=f"{len(responses)} configured",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @dankhall.command(name="channelinfo")
    async def dh_channel_info(self, ctx: commands.Context, channel: discord.TextChannel):
        """View override settings for a specific channel."""
        channel_config = await self.config.channel(channel).all()
        guild_config = await self.config.guild(ctx.guild).all()
        
        embed = discord.Embed(
            title=f"⚙️ Settings for {channel.name}",
            color=discord.Color.blue()
        )
        
        # Threshold
        if channel_config["threshold"] is not None:
            threshold_text = f"**{channel_config['threshold']}** reactions (Override)"
        else:
            threshold_text = f"{guild_config['default_threshold']} reactions (Using default)"
        embed.add_field(name="Threshold", value=threshold_text, inline=False)
        
        # Hall Channel
        if channel_config["hall_channel"] is not None:
            hall_ch = ctx.guild.get_channel(channel_config["hall_channel"])
            hall_text = f"{hall_ch.mention} (Override)" if hall_ch else "*Channel not found*"
        else:
            default_hall = ctx.guild.get_channel(guild_config["default_hall_channel"])
            hall_text = f"{default_hall.mention} (Using default)" if default_hall else "*Not set*"
        embed.add_field(name="Hall Channel", value=hall_text, inline=False)
        
        # Blacklisted?
        is_blacklisted = channel.id in guild_config["blacklisted_channels"]
        blacklist_text = "⚠️ **YES - This channel is blacklisted!**" if is_blacklisted else "No"
        embed.add_field(name="Blacklisted", value=blacklist_text, inline=False)
        
        await ctx.send(embed=embed)

    # ==================== Manual Certification ====================

    @dankhall.command(name="certify")
    async def dh_certify(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        message_id: int,
        emoji: str
    ):
        """
        Manually certify a message.
        
        Example: `[p]dankhall certify #memes 123456789 🔥`
        """
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("❌ Message not found.")
            return
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to access that channel.")
            return
        
        # Check if already certified
        if await self.db.is_certified(message.id):
            await ctx.send("❌ This message is already certified.")
            return
        
        # Parse emoji
        try:
            custom_emoji = await commands.EmojiConverter().convert(ctx, emoji)
            emoji_str = str(custom_emoji)
            emoji_id = str(custom_emoji.id)
        except:
            emoji_str = emoji
            emoji_id = emoji
        
        # Get hall channel
        hall_channel_id = await self._get_hall_channel(channel)
        if not hall_channel_id:
            await ctx.send("❌ No hall of fame channel configured.")
            return
        
        hall_channel = ctx.guild.get_channel(hall_channel_id)
        if not hall_channel:
            await ctx.send("❌ Hall of fame channel not found.")
            return
        
        # Create and send the hall message
        embed = await self._create_hall_embed(message, emoji_str, "Manual")
        hall_msg = await self._send_hall_message(hall_channel, message, embed)
        
        if hall_msg:
            # Record in database
            await self.db.add_certified_message(
                message_id=message.id,
                guild_id=ctx.guild.id,
                channel_id=channel.id,
                user_id=message.author.id,
                emoji=emoji_id,
                hall_message_id=hall_msg.id,
                reaction_count=0,  # Manual certification
                hall_channel_id=hall_channel.id
            )
            
            await ctx.send(f"✅ Message manually certified and posted to {hall_channel.mention}!")
        else:
            await ctx.send("❌ Failed to post to hall of fame channel.")

    @dankhall.command(name="backfill")
    async def dh_backfill(
        self,
        ctx: commands.Context,
        hall_channel: discord.TextChannel,
        limit: int = 100,
        after_message_id: int = None
    ):
        """
        Backfill the database from existing hall of fame messages.
        
        Scans the hall channel for old certification embeds and adds them to stats.
        
        Examples:
        - `[p]dankhall backfill #hall-of-fame 100` - Scan last 100 messages
        - `[p]dankhall backfill #hall-of-fame 1000` - Scan last 1000 messages
        - `[p]dankhall backfill #hall-of-fame 500 123456789` - Scan 500 messages after message ID
        
        To scan everything: use a very large limit like 10000
        """
        if limit < 1:
            await ctx.send("❌ Limit must be at least 1.")
            return
        
        async with ctx.typing():
            added = 0
            skipped = 0
            errors = 0
            
            if after_message_id:
                status_msg = await ctx.send(f"🔄 Scanning {hall_channel.mention} for certifications after message {after_message_id}...")
            else:
                status_msg = await ctx.send(f"🔄 Scanning {hall_channel.mention} for certifications (last {limit} messages)...")
            
            # Fetch messages from the hall channel
            try:
                if after_message_id:
                    # Get a message object to use as 'after' parameter
                    try:
                        after_msg = await hall_channel.fetch_message(after_message_id)
                        history = hall_channel.history(limit=limit, after=after_msg, oldest_first=True)
                    except discord.NotFound:
                        await status_msg.edit(content="❌ Starting message not found.")
                        return
                else:
                    # Default: get most recent messages
                    history = hall_channel.history(limit=limit)
                
                async for message in history:
                    # Skip messages not from the bot
                    if message.author.id != self.bot.user.id:
                        continue
                    
                    # Skip messages without embeds
                    if not message.embeds:
                        continue
                    
                    embed = message.embeds[0]
                    
                    # Check if it's a certification embed (has "Certified Dank" title)
                    if not embed.title or "Certified Dank" not in embed.title:
                        continue
                    
                    try:
                        # Parse the embed to extract data
                        result = await self._parse_hall_embed(message, embed)
                        
                        if not result:
                            errors += 1
                            continue
                        
                        # Check if already in database
                        if await self.db.is_certified(result["message_id"]):
                            skipped += 1
                            continue
                        
                        # Add to database
                        success = await self.db.add_certified_message(
                            message_id=result["message_id"],
                            guild_id=ctx.guild.id,
                            channel_id=result["channel_id"],
                            user_id=result["user_id"],
                            emoji=result["emoji"],
                            hall_message_id=message.id,
                            reaction_count=result["reaction_count"]
                        )
                        
                        if success:
                            added += 1
                        else:
                            errors += 1
                    
                    except Exception as e:
                        print(f"Error parsing hall message {message.id}: {e}", file=sys.stderr)
                        errors += 1
                        continue
            
            except Exception as e:
                await status_msg.edit(content=f"❌ Error during backfill: {e}")
                return
            
            # Send results
            embed = discord.Embed(
                title="✅ Backfill Complete",
                color=discord.Color.green()
            )
            embed.add_field(name="Added to Database", value=str(added), inline=True)
            embed.add_field(name="Already Existed", value=str(skipped), inline=True)
            embed.add_field(name="Errors", value=str(errors), inline=True)
            
            await status_msg.edit(content=None, embed=embed)

    @dankhall.command(name="register")
    async def dh_register(
        self,
        ctx: commands.Context,
        hall_message_link: str
    ):
        """
        Register a single hall of fame message to the database for stats.
        
        Provide the message link from the hall of fame channel.
        
        Example: `[p]dankhall register https://discord.com/channels/123/456/789`
        """
        # Parse the message link
        try:
            # Expected format: https://discord.com/channels/guild_id/channel_id/message_id
            parts = hall_message_link.split('/')
            if len(parts) < 3:
                await ctx.send("❌ Invalid message link format.")
                return
            
            message_id = int(parts[-1])
            channel_id = int(parts[-2])
            guild_id = int(parts[-3])
            
            if guild_id != ctx.guild.id:
                await ctx.send("❌ That message is from a different server.")
                return
            
            hall_channel = ctx.guild.get_channel(channel_id)
            if not hall_channel:
                await ctx.send("❌ Hall channel not found.")
                return
            
            # Fetch the message
            try:
                message = await hall_channel.fetch_message(message_id)
            except discord.NotFound:
                await ctx.send("❌ Message not found.")
                return
            except discord.Forbidden:
                await ctx.send("❌ I don't have permission to access that channel.")
                return
            
            # Check if message is from the bot and has an embed
            if message.author.id != self.bot.user.id:
                await ctx.send("❌ That message isn't a certification from me.")
                return
            
            if not message.embeds:
                await ctx.send("❌ That message doesn't have an embed.")
                return
            
            embed = message.embeds[0]
            
            # Check if it's a certification embed
            if not embed.title or "Certified Dank" not in embed.title:
                await ctx.send("❌ That doesn't look like a certification embed.")
                return
            
            # Parse the embed
            result = await self._parse_hall_embed(message, embed)
            
            if not result:
                await ctx.send("❌ Failed to parse the certification embed.")
                return
            
            # Check if already registered
            if await self.db.is_certified(result["message_id"]):
                await ctx.send("❌ This certification is already registered in the database.")
                return
            
            # Try to fetch the original message to get current reaction count
            current_reaction_count = result["reaction_count"]  # Default from embed
            
            try:
                orig_channel = ctx.guild.get_channel(result["channel_id"])
                if orig_channel:
                    orig_message = await orig_channel.fetch_message(result["message_id"])
                    
                    # Find the highest reaction count on the message
                    if orig_message.reactions:
                        max_count = max(reaction.count for reaction in orig_message.reactions)
                        current_reaction_count = max_count
            except (discord.NotFound, discord.Forbidden):
                pass  # Original message deleted or no access, use embed count
            
            # Add to database
            success = await self.db.add_certified_message(
                message_id=result["message_id"],
                guild_id=ctx.guild.id,
                channel_id=result["channel_id"],
                user_id=result["user_id"],
                emoji=result["emoji"],
                hall_message_id=message.id,
                reaction_count=current_reaction_count,  # Use current count
                hall_channel_id=hall_channel.id
            )
            
            if success:
                await ctx.send("✅ Certification registered successfully! Stats have been updated.")
            else:
                await ctx.send("❌ Failed to register certification to database.")
        
        except (ValueError, IndexError):
            await ctx.send("❌ Invalid message link format. Use a Discord message link.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
            print(f"Error registering certification: {e}", file=sys.stderr)

    # ==================== Statistics Commands ====================

    @dankhall.group(name="stats")
    async def dh_stats(self, ctx: commands.Context):
        """View Dank Hall statistics."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @dh_stats.command(name="user")
    async def dh_stats_user(
        self, 
        ctx: commands.Context, 
        user: discord.Member = None
    ):
        """View certification stats for a user."""
        user = user or ctx.author
        
        stats = await self.db.get_user_stats(ctx.guild.id, user.id)
        
        if stats["total"] == 0:
            await ctx.send(f"{user.mention} hasn't been certified yet!")
            return
        
        embed = discord.Embed(
            title=f"🏆 {user.display_name}'s Dank Stats",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(
            name="Total Certifications",
            value=f"**{stats['total']}**",
            inline=True
        )
        
        # Top emojis
        if stats["by_emoji"]:
            emoji_text = "\n".join(
                f"{emoji}: {count}" for emoji, count in stats["by_emoji"][:5]
            )
            embed.add_field(name="Top Emojis", value=emoji_text, inline=True)
        
        # Server rank
        rank = await self.db.get_user_rank(ctx.guild.id, user.id)
        embed.add_field(name="Server Rank", value=f"#{rank}", inline=True)
        
        await ctx.send(embed=embed)

    @dh_stats.command(name="leaderboard", aliases=["top", "lb"])
    async def dh_stats_leaderboard(self, ctx: commands.Context, limit: int = 10):
        """View the top certified users in this server."""
        if limit < 1 or limit > 25:
            await ctx.send("❌ Limit must be between 1 and 25.")
            return
        
        leaders = await self.db.get_leaderboard(ctx.guild.id, limit)
        
        if not leaders:
            await ctx.send("No certifications yet in this server!")
            return
        
        embed = discord.Embed(
            title="🏆 Dank Hall Leaderboard",
            description="Top certified users",
            color=discord.Color.gold()
        )
        
        leaderboard_text = ""
        for rank, (user_id, count) in enumerate(leaders, 1):
            user = ctx.guild.get_member(user_id)
            name = user.display_name if user else f"User {user_id}"
            
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "")
            leaderboard_text += f"{medal} **#{rank}** {name}: {count}\n"
        
        embed.description = leaderboard_text
        await ctx.send(embed=embed)

    @dh_stats.command(name="channels")
    async def dh_stats_channels(self, ctx: commands.Context, limit: int = 10):
        """View the channels with the most certifications."""
        if limit < 1 or limit > 25:
            await ctx.send("❌ Limit must be between 1 and 25.")
            return
        
        channels = await self.db.get_top_channels(ctx.guild.id, limit)
        
        if not channels:
            await ctx.send("No certifications yet in this server!")
            return
        
        embed = discord.Embed(
            title="📊 Top Channels",
            description="Channels with the most certified posts",
            color=discord.Color.blue()
        )
        
        channel_text = ""
        for rank, (channel_id, count) in enumerate(channels, 1):
            channel = ctx.guild.get_channel(channel_id)
            name = channel.mention if channel else f"Channel {channel_id}"
            channel_text += f"**#{rank}** {name}: {count}\n"
        
        embed.description = channel_text
        await ctx.send(embed=embed)

    @dh_stats.command(name="emojis")
    async def dh_stats_emojis(self, ctx: commands.Context, limit: int = 10):
        """View the most popular certification emojis."""
        if limit < 1 or limit > 25:
            await ctx.send("❌ Limit must be between 1 and 25.")
            return
        
        emojis = await self.db.get_top_emojis(ctx.guild.id, limit)
        
        if not emojis:
            await ctx.send("No certifications yet in this server!")
            return
        
        embed = discord.Embed(
            title="😀 Popular Emojis",
            description="Most used certification emojis",
            color=discord.Color.purple()
        )
        
        emoji_text = ""
        for rank, (emoji, count) in enumerate(emojis, 1):
            emoji_text += f"**#{rank}** {emoji}: {count}\n"
        
        embed.description = emoji_text
        await ctx.send(embed=embed)

    @dh_stats.command(name="server")
    async def dh_stats_server(self, ctx: commands.Context):
        """View overall server statistics."""
        total = await self.db.get_total_certifications(ctx.guild.id)
        
        if total == 0:
            await ctx.send("No certifications yet in this server!")
            return
        
        embed = discord.Embed(
            title=f"📊 {ctx.guild.name} Dank Stats",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Total Certifications",
            value=f"**{total}**",
            inline=True
        )
        
        # Top user
        leaders = await self.db.get_leaderboard(ctx.guild.id, 1)
        if leaders:
            top_user_id, top_count = leaders[0]
            top_user = ctx.guild.get_member(top_user_id)
            top_name = top_user.display_name if top_user else f"User {top_user_id}"
            embed.add_field(
                name="Top User",
                value=f"{top_name} ({top_count})",
                inline=True
            )
        
        # Top emoji
        emojis = await self.db.get_top_emojis(ctx.guild.id, 1)
        if emojis:
            top_emoji, emoji_count = emojis[0]
            embed.add_field(
                name="Top Emoji",
                value=f"{top_emoji} ({emoji_count})",
                inline=True
            )
        
        await ctx.send(embed=embed)

    @dankhall.command(name="random")
    async def dh_random(self, ctx: commands.Context):
        """Show a random certified dank post from any hall of fame."""
        # Get a random certification from ANY hall
        random_cert = await self.db.get_random_certification(ctx.guild.id)
        
        if not random_cert:
            await ctx.send("No certifications yet in this server!")
            return
        
        # Try to fetch the original message to get the link
        channel = ctx.guild.get_channel(random_cert["channel_id"])
        
        if not channel:
            await ctx.send("❌ Could not find the channel for this certification.")
            return
        
        # Get user info
        user = ctx.guild.get_member(random_cert["user_id"])
        user_name = user.display_name if user else f"User {random_cert['user_id']}"
        user_avatar = user.display_avatar.url if user else None
        
        # Create the hall of fame style embed
        embed = discord.Embed(
            title="🎲 Random Certified Dank",
            color=discord.Color.gold(),
            timestamp=random_cert["certified_at"]
        )
        
        if user_avatar:
            embed.set_author(name=user_name, icon_url=user_avatar)
        else:
            embed.set_author(name=user_name)
        
        embed.add_field(
            name="Channel",
            value=channel.mention,
            inline=True
        )
        
        embed.add_field(
            name="Emoji",
            value=random_cert["emoji"],
            inline=True
        )
        
        embed.add_field(
            name="Reactions",
            value=str(random_cert["reaction_count"]),
            inline=True
        )
        
        # Create the jump link
        message_link = f"https://discord.com/channels/{ctx.guild.id}/{random_cert['channel_id']}/{random_cert['message_id']}"
        
        embed.add_field(
            name="Jump to Message",
            value=f"[Click here]({message_link})",
            inline=False
        )
        
        embed.set_footer(text="Content hidden - click the link to view if you have access")
        
        # Send only the embed, no content
        await ctx.send(embed=embed)

    # ==================== Helper Methods ====================

    async def _get_threshold(self, channel: discord.TextChannel) -> int:
        """Get the threshold for a channel (channel override or guild default)."""
        channel_threshold = await self.config.channel(channel).threshold()
        if channel_threshold is not None:
            return channel_threshold
        return await self.config.guild(channel.guild).default_threshold()

    async def _get_hall_channel(self, channel: discord.TextChannel) -> int:
        """Get the hall of fame channel ID for a channel."""
        channel_hall = await self.config.channel(channel).hall_channel()
        if channel_hall is not None:
            return channel_hall
        return await self.config.guild(channel.guild).default_hall_channel()

    async def _create_hall_embed(
        self, 
        message: discord.Message, 
        emoji: str,
        reaction_count: int | str
    ) -> discord.Embed:
        """Create the embed for the hall of fame post."""
        embed = discord.Embed(
            title="🏆 Certified Dank",
            color=discord.Color.gold(),
            timestamp=message.created_at
        )
        
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )
        
        embed.add_field(
            name="Channel",
            value=message.channel.mention,
            inline=True
        )
        
        embed.add_field(
            name="Emoji",
            value=emoji,
            inline=True
        )
        
        embed.add_field(
            name="Reactions",
            value=str(reaction_count),
            inline=True
        )
        
        embed.add_field(
            name="Jump to Message",
            value=f"[Click here]({message.jump_url})",
            inline=False
        )
        
        # Add message content if it's not too long
        if message.content:
            content = message.content[:1024]
            if len(message.content) > 1024:
                content += "..."
            embed.add_field(
                name="Content",
                value=content,
                inline=False
            )
        
        return embed

    async def _send_hall_message(
        self,
        hall_channel: discord.TextChannel,
        original_message: discord.Message,
        embed: discord.Embed
    ) -> discord.Message:
        """Send the hall of fame message with media."""
        try:
            # Send the embed with info
            hall_msg = await hall_channel.send(embed=embed)
            
            # If there's any media (attachments or embeds), post it separately
            if original_message.attachments:
                # Post all attachments as separate messages for native Discord rendering
                for attachment in original_message.attachments:
                    await hall_channel.send(attachment.url)
            
            elif original_message.embeds:
                # If the original message had an embed (like a link preview), send that URL
                orig_embed = original_message.embeds[0]
                if orig_embed.url:
                    await hall_channel.send(orig_embed.url)
            
            return hall_msg
        
        except Exception as e:
            print(f"Error sending hall message: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return None

    async def _parse_hall_embed(
        self,
        hall_message: discord.Message,
        embed: discord.Embed
    ) -> dict:
        """
        Parse a hall of fame embed to extract certification data.
        
        Returns dict with: message_id, channel_id, user_id, emoji, reaction_count
        """
        try:
            # Extract user ID from embed author icon URL
            user_id = None
            if embed.author and embed.author.icon_url:
                # Icon URL format: https://cdn.discordapp.com/avatars/USER_ID/hash.png
                # Try to extract user ID from the URL
                icon_url = str(embed.author.icon_url)
                
                # Pattern 1: Custom avatar - /avatars/USER_ID/hash.png
                match = re.search(r'/avatars/(\d+)/', icon_url)
                if match:
                    user_id = int(match.group(1))
                
                # Pattern 2: If that fails, try embed-/avatars/USER_ID/hash
                if not user_id:
                    match = re.search(r'avatars/(\d+)/', icon_url)
                    if match:
                        try:
                            user_id = int(match.group(1))
                        except ValueError:
                            pass
            
            # If we still don't have user_id, we'll need to get it from the original message
            # We'll set it to None and try to get it later from fetching the original message
            
            # Extract channel ID from embed fields
            channel_id = None
            emoji = None
            reaction_count = 0
            message_id = None
            message_url = None
            
            for field in embed.fields:
                # Channel field contains channel mention
                if field.name == "Channel" and field.value:
                    # Try multiple formats
                    # Format 1: <#CHANNEL_ID>
                    channel_match = re.search(r'<#(\d+)>', field.value)
                    if channel_match:
                        channel_id = int(channel_match.group(1))
                    else:
                        # Format 2: Plain channel name (fallback, won't work but let's try)
                        # We'll try to extract from the message URL later
                        pass
                
                # Emoji field
                if field.name == "Emoji" and field.value:
                    emoji = field.value.strip()
                
                # Reactions field
                if field.name == "Reactions" and field.value:
                    try:
                        reaction_count = int(field.value) if field.value != "Manual" else 0
                    except ValueError:
                        reaction_count = 0
                
                # Jump to Message / Content field contains the original message link
                if field.name in ["Jump to Message", "Content"] and field.value:
                    # Extract full URL from markdown link or plain URL
                    # Format: [Click here](URL) or just URL
                    url_match = re.search(r'https://(?:discord\.com|discordapp\.com)/channels/(\d+)/(\d+)/(\d+)', field.value)
                    if url_match:
                        message_url = url_match.group(0)
                        # Extract IDs from URL
                        guild_id = int(url_match.group(1))
                        url_channel_id = int(url_match.group(2))
                        message_id = int(url_match.group(3))
                        
                        # Use channel_id from URL if we didn't get it from Channel field
                        if not channel_id:
                            channel_id = url_channel_id
                        
                        
            
            # If we still don't have channel_id but have message_url, try one more time
            if not channel_id and message_url:
                url_match = re.search(r'/channels/\d+/(\d+)/\d+', message_url)
                if url_match:
                    channel_id = int(url_match.group(1))
            
            # If we don't have user_id, try to fetch the original message to get it
            if not user_id and message_id and channel_id:
                try:
                    channel = hall_message.guild.get_channel(channel_id)
                    if channel:
                        original_msg = await channel.fetch_message(message_id)
                        user_id = original_msg.author.id
                except:
                    pass  # If we can't fetch, we'll fail validation below
            
            # Validate we got all required data
            if not all([user_id, channel_id, emoji, message_id]):
                print(f"Missing data - user_id: {user_id}, channel_id: {channel_id}, emoji: {emoji}, message_id: {message_id}", file=sys.stderr)
                print(f"Embed fields: {[(f.name, f.value) for f in embed.fields]}", file=sys.stderr)
                if embed.author:
                    print(f"Author icon URL: {embed.author.icon_url}", file=sys.stderr)
                return None
            
            return {
                "message_id": message_id,
                "channel_id": channel_id,
                "user_id": user_id,
                "emoji": emoji,
                "reaction_count": reaction_count
            }
        
        except Exception as e:
            print(f"Error parsing embed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return None