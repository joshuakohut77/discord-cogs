import json
from pathlib import Path

from redbot.core.bot import Red

from .buttonpoll import ButtonPoll

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red):
    cog = ButtonPoll(bot)
    await bot.add_cog(cog)
