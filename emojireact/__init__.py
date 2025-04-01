from .emojireact import EmojiReactions


async def setup(bot):
    cog = EmojiReactions(bot)
    await bot.add_cog(cog)
