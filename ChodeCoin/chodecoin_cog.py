import re
import asyncio
from typing import Optional
import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, pagify


class ChodeCoin(commands.Cog):
    """A cog for tracking ChodeCoin points with @user++ and @user-- syntax"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)

        # Default settings
        default_guild = {
            "scores": {},  # {"user_id": score}
            "enabled": True
        }

        self.config.register_guild(**default_guild)

        # Regex pattern to match @username++ or @username--
        self.point_pattern = re.compile(r'@(\w+)(\+\+|--)')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for @user++ or @user-- patterns in messages"""

        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return

        # Check if the cog is enabled for this guild
        if not await self.config.guild(message.guild).enabled():
            return

        # Find all matches in the message
        matches = self.point_pattern.findall(message.content)

        if not matches:
            return

        # Process each match
        for username, operation in matches:
            await self._process_point_change(message, username, operation)

    async def _process_point_change(self, message: discord.Message, username: str, operation: str):
        """Process a point change for a user"""

        # Don't let people give points to themselves
        if username.lower() == message.author.name.lower() or username.lower() == message.author.display_name.lower():
            return

        # Get current scores
        scores = await self.config.guild(message.guild).scores()

        # Initialize user if not exists
        if username not in scores:
            scores[username] = 0

        # Apply point change
        if operation == "++":
            scores[username] += 1
            change = "+1"
        else:  # operation == "--"
            scores[username] -= 1
            change = "-1"

        # Save updated scores
        await self.config.guild(message.guild).scores.set(scores)

        # React to the message to show it was processed
        try:
            if operation == "++":
                await message.add_reaction("⬆️")
            else:
                await message.add_reaction("⬇️")
        except discord.HTTPException:
            pass  # Ignore if we can't react

    @commands.command(name="chodecoin", aliases=["cc", "coins"])
    async def show_score(self, ctx, user: Optional[str] = None):
        """Show ChodeCoin score for a user (defaults to yourself)"""

        if user is None:
            # Show sender's score
            target_name = ctx.author.name
        else:
            # Clean up the user input (remove @ if present)
            target_name = user.lstrip('@')

        scores = await self.config.guild(ctx.guild).scores()
        score = scores.get(target_name, 0)

        await ctx.send(f"**{target_name}** has **{score}** ChodeCoins! 🪙")

    @commands.command(name="chodeboards", aliases=["ccleaderboard", "cctop"])
    async def leaderboard(self, ctx, limit: int = 10):
        """Show the ChodeCoin leaderboard"""

        if limit > 25:
            limit = 25
        elif limit < 1:
            limit = 10

        scores = await self.config.guild(ctx.guild).scores()

        if not scores:
            await ctx.send("No ChodeCoin scores yet! Start giving out points with @user++ or @user--")
            return

        # Sort by score (descending)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build leaderboard message
        leaderboard_text = "🏆 **ChodeCoin Leaderboard** 🪙\n\n"

        for i, (username, score) in enumerate(sorted_scores[:limit], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard_text += f"{medal} **{username}**: {score} coins\n"

        # Handle long messages
        for page in pagify(leaderboard_text):
            await ctx.send(page)

    @commands.command(name="chodereset")
    @checks.admin_or_permissions(manage_guild=True)
    async def reset_scores(self, ctx, user: Optional[str] = None):
        """Reset ChodeCoin scores (admin only)"""

        if user is None:
            # Reset all scores
            await self.config.guild(ctx.guild).scores.set({})
            await ctx.send("All ChodeCoin scores have been reset! 🗑️")
        else:
            # Reset specific user
            target_name = user.lstrip('@')
            scores = await self.config.guild(ctx.guild).scores()

            if target_name in scores:
                del scores[target_name]
                await self.config.guild(ctx.guild).scores.set(scores)
                await ctx.send(f"**{target_name}**'s ChodeCoin score has been reset! 🗑️")
            else:
                await ctx.send(f"**{target_name}** doesn't have any ChodeCoins to reset.")

    @commands.command(name="chodetoggle")
    @checks.admin_or_permissions(manage_guild=True)
    async def toggle_cog(self, ctx):
        """Enable or disable ChodeCoin tracking (admin only)"""

        current = await self.config.guild(ctx.guild).enabled()
        new_state = not current

        await self.config.guild(ctx.guild).enabled.set(new_state)

        status = "enabled" if new_state else "disabled"
        await ctx.send(f"ChodeCoin tracking has been **{status}**!")

    @commands.command(name="chodehelp")
    async def help_command(self, ctx):
        """Show help for ChodeCoin commands"""

        help_text = """
**ChodeCoin Help** 🪙

**Usage:**
• `@username++` - Give a ChodeCoin to someone
• `@username--` - Take away a ChodeCoin from someone

**Commands:**
• `{prefix}chodecoin [user]` - Check ChodeCoin balance
• `{prefix}chodeboards [limit]` - Show leaderboard
• `{prefix}chodereset [user]` - Reset scores (admin only)
• `{prefix}chodetoggle` - Enable/disable tracking (admin only)

**Examples:**
• `@Cacti++` - Gives Cacti +1 ChodeCoin
• `@longmeetings--` - Takes away 1 ChodeCoin from longmeetings
        """.format(prefix=ctx.clean_prefix)

        await ctx.send(box(help_text, lang="md"))


def setup(bot: Red):
    """Setup function for the cog"""
    bot.add_cog(ChodeCoin(bot))