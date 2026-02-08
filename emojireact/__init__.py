from .emojireact import EmojiReactions


async def setup(bot):
    """Load the EmojiReactions cog."""
    cog = EmojiReactions(bot)
    await bot.add_cog(cog)