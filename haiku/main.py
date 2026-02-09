from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING
from abc import ABCMeta
from .haikuclass import HaikuDetector
from .dbclass import DatabasePool

if TYPE_CHECKING:
    from redbot.core.bot import Red

import discord
from redbot.core import Config, commands

from .event import EventMixin

class CompositeClass(commands.CogMeta, ABCMeta):
    __slots__: tuple = ()
    pass

class Haiku(EventMixin, commands.Cog, metaclass=CompositeClass):
    """Detects and logs accidental haikus in messages"""
    
    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.db_pool = DatabasePool()
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        
        # Default settings
        default_guild = {
            "enabled": True
        }
        self.config.register_guild(**default_guild)

    async def initialize(self):
        """Initialize database pool and create table if needed"""
        self.db_pool.initialize()
        await self._create_table()

    async def _create_table(self):
        """Create the haiku table if it doesn't exist"""
        from .dbclass import db
        database = db()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS haiku (
            "Id" SERIAL PRIMARY KEY,
            "UserId" VARCHAR(255) NOT NULL,
            "Username" VARCHAR(255) NOT NULL,
            "GuildId" VARCHAR(255),
            "ChannelId" VARCHAR(255) NOT NULL,
            "MessageId" VARCHAR(255) NOT NULL,
            "OriginalText" TEXT NOT NULL,
            "FormattedHaiku" TEXT NOT NULL,
            "Timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            database.execute(create_table_query)
            
            # Create indexes for better query performance
            index_queries = [
                'CREATE INDEX IF NOT EXISTS idx_haiku_user ON haiku("UserId");',
                'CREATE INDEX IF NOT EXISTS idx_haiku_guild ON haiku("GuildId");',
                'CREATE INDEX IF NOT EXISTS idx_haiku_timestamp ON haiku("Timestamp");'
            ]
            
            for index_query in index_queries:
                database.execute(index_query)
                
        except Exception as e:
            print(f"Error creating haiku table: {e}")

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.db_pool.close()

    @commands.group()
    @commands.guild_only()
    async def haiku(self, ctx: commands.Context) -> None:
        """Haiku detection commands"""
        pass
    
    @haiku.command()
    async def count(self, ctx: commands.Context) -> None:
        """Get the total count of haikus detected"""
        try:
            count = HaikuDetector.get_haiku_count()
            await ctx.send(f"Total haikus detected: **{count}**")
        except Exception as e:
            await ctx.send(f"Error getting haiku count: {e}")
    
    @haiku.command()
    async def mycount(self, ctx: commands.Context) -> None:
        """Get your personal haiku count"""
        try:
            count = HaikuDetector.get_user_haiku_count(ctx.author.id)
            await ctx.send(f"{ctx.author.mention}, you have created **{count}** accidental haikus!")
        except Exception as e:
            await ctx.send(f"Error getting your haiku count: {e}")
    
    @haiku.command()
    async def leaderboard(self, ctx: commands.Context, limit: int = 10) -> None:
        """Show the top haiku creators
        
        Args:
            limit: Number of users to show (default: 10, max: 25)
        """
        if limit > 25:
            limit = 25
        
        try:
            top_users = HaikuDetector.get_top_haiku_users(limit)
            
            if not top_users:
                await ctx.send("No haikus have been detected yet!")
                return
            
            embed = discord.Embed(
                title="🍃 Haiku Leaderboard 🍃",
                color=0x90EE90
            )
            
            description = ""
            for i, (username, count) in enumerate(top_users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                description += f"{medal} **{username}**: {count} haiku{'s' if count != 1 else ''}\n"
            
            embed.description = description
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error getting leaderboard: {e}")
    
    @haiku.command()
    async def channels(self, ctx: commands.Context, limit: int = 10) -> None:
        """Show the top channels with most haikus
        
        Args:
            limit: Number of channels to show (default: 10, max: 25)
        """
        if limit > 25:
            limit = 25
        
        try:
            top_channels = HaikuDetector.get_top_haiku_channels(
                guild_id=ctx.guild.id if ctx.guild else None,
                limit=limit
            )
            
            if not top_channels:
                await ctx.send("No haikus have been detected yet!")
                return
            
            embed = discord.Embed(
                title="🍃 Top Haiku Channels 🍃",
                color=0x90EE90
            )
            
            description = ""
            for i, (channel_id, count) in enumerate(top_channels, 1):
                # Try to get the channel object
                channel = self.bot.get_channel(int(channel_id))
                channel_name = channel.mention if channel else f"Unknown Channel ({channel_id})"
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                description += f"{medal} {channel_name}: {count} haiku{'s' if count != 1 else ''}\n"
            
            embed.description = description
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error getting channel stats: {e}")
    
    @haiku.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def toggle(self, ctx: commands.Context) -> None:
        """Toggle haiku detection for this server"""
        current = await self.config.guild(ctx.guild).enabled()
        await self.config.guild(ctx.guild).enabled.set(not current)
        
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Haiku detection has been **{status}** for this server.")
    
    @haiku.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def backfill(self, ctx: commands.Context, limit: int = None) -> None:
        """Backfill the database with old haiku embeds from the bot
        
        This will search through all channels for messages from the bot
        with the title "Accidental Haiku?" and add them to the database.
        
        Args:
            limit: Optional limit on messages to check per channel (default: all)
        """
        await ctx.send("Starting backfill process... This may take a while.")
        
        total_found = 0
        total_added = 0
        total_skipped = 0
        channels_processed = 0
        
        # Get all text channels in the guild
        text_channels = [c for c in ctx.guild.channels if isinstance(c, discord.TextChannel)]
        
        status_msg = await ctx.send(f"Processing 0/{len(text_channels)} channels...")
        
        for channel in text_channels:
            try:
                # Check if bot has permission to read history
                if not channel.permissions_for(ctx.guild.me).read_message_history:
                    continue
                
                channels_processed += 1
                
                # Search through channel history
                async for message in channel.history(limit=limit, oldest_first=False):
                    # Check if message is from the bot and has embeds
                    if message.author.id != self.bot.user.id:
                        continue
                    
                    if not message.embeds:
                        continue
                    
                    embed = message.embeds[0]
                    
                    # Check if it's an old haiku embed
                    if embed.title and "Accidental Haiku?" in embed.title:
                        total_found += 1
                        
                        # Get the previous message to find the original author
                        try:
                            # Fetch messages before this one
                            messages_before = [m async for m in channel.history(
                                limit=10, 
                                before=message.created_at
                            )]
                            
                            # Find the first non-bot message
                            original_author = None
                            original_message = None
                            for prev_msg in messages_before:
                                if not prev_msg.author.bot:
                                    original_author = prev_msg.author
                                    original_message = prev_msg
                                    break
                            
                            if not original_author:
                                total_skipped += 1
                                continue
                            
                            # Extract haiku text from embed
                            haiku_text = embed.description
                            
                            if not haiku_text:
                                total_skipped += 1
                                continue
                            
                            # Check if this haiku already exists in database
                            from .dbclass import db
                            database = db()
                            check_query = 'SELECT COUNT(*) FROM haiku WHERE "MessageId" = %(msg_id)s;'
                            result = database.querySingle(check_query, {'msg_id': str(message.id)})
                            
                            if result and result[0] > 0:
                                total_skipped += 1
                                continue
                            
                            # Split haiku back into lines
                            haiku_lines = haiku_text.strip().split('\n')
                            
                            # Insert into database
                            HaikuDetector.insert_haiku(
                                user_id=original_author.id,
                                username=original_author.name,
                                guild_id=ctx.guild.id,
                                channel_id=channel.id,
                                message_id=message.id,  # Use the haiku bot message ID
                                original_text=original_message.content if original_message else haiku_text,
                                formatted_haiku=haiku_lines
                            )
                            
                            total_added += 1
                            
                        except Exception as e:
                            print(f"Error processing haiku message {message.id}: {e}")
                            total_skipped += 1
                            continue
                
                # Update status every few channels
                if channels_processed % 5 == 0:
                    await status_msg.edit(
                        content=f"Processing {channels_processed}/{len(text_channels)} channels... "
                                f"Found: {total_found}, Added: {total_added}, Skipped: {total_skipped}"
                    )
                    
            except discord.Forbidden:
                # Skip channels we can't access
                continue
            except Exception as e:
                print(f"Error processing channel {channel.name}: {e}")
                continue
        
        # Final summary
        embed = discord.Embed(
            title="🍃 Backfill Complete 🍃",
            color=0x90EE90
        )
        embed.add_field(name="Channels Processed", value=str(channels_processed), inline=True)
        embed.add_field(name="Haikus Found", value=str(total_found), inline=True)
        embed.add_field(name="Added to Database", value=str(total_added), inline=True)
        embed.add_field(name="Skipped/Duplicates", value=str(total_skipped), inline=True)
        
        await status_msg.edit(content="Backfill process complete!", embed=embed)