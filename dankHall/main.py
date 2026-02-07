from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABCMeta

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
                reaction_count=0  # Manual certification
            )
            
            await ctx.send(f"✅ Message manually certified and posted to {hall_channel.mention}!")
        else:
            await ctx.send("❌ Failed to post to hall of fame channel.")

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