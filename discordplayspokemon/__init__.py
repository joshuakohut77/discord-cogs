from .discordplayspokemon import DiscordPlaysPokemon


async def setup(bot):
    await bot.add_cog(DiscordPlaysPokemon(bot))