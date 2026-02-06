from .twitchplayspokemon import TwitchPlaysPokemon


async def setup(bot):
    await bot.add_cog(TwitchPlaysPokemon(bot))