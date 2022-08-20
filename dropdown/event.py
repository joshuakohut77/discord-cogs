# from __future__ import annotations
# from .abc import MixinMeta
    
# import random
# import discord

# from datetime import datetime, timedelta

# from redbot.core import commands

# class EventMixin(MixinMeta):
#     # __slots__: tuple = ()

#     @commands.Cog.listener()
#     async def on_message(self, message: discord.Message) -> None:
#         if message.author.bot:
#             return
#         elif str(message.author) == "Cacti Twig#2672":
#             return
#         config: dict = await self.config.all_channels()
#         if message.channel.id not in config:
#             return

#         if not config[message.channel.id]["enabled"]:
#             return

#         guild_conf: dict = await self.config.guild(message.guild).get_raw()
#         extensions: list = guild_conf["extensions"]
#         websites: list = guild_conf["websites"]

#         if not extensions and not websites:
#             return

#         msg: str = message.content.lower()
#         if all(
#             (not any((ext for ext in extensions if msg.endswith(ext))),
#             not any((site for site in websites if site.lower() in msg)),
#             len(message.attachments) == 0)):
#             return

#         if datetime.utcnow().timestamp() >= config[message.channel.id]["next_react_time"] and random.randint(1, 100) <= config[message.channel.id]["multiplier"]:
#             emoji: str | int = random.choice(config[message.channel.id]["emojis"])
#             try:
#                 emoji: discord.Emoji = await commands.EmojiConverter().convert(ctx=await self.bot.get_context(message), argument=str(emoji))
#             except:
#                 emoji: str = emoji
#             finally:
#                 try:
#                     await message.add_reaction(emoji)
#                 except discord.Forbidden:
#                     await message.channel.send("I don't have the permissions to add a reaction")
#                 except discord.NotFound:
#                     await message.channel.send("Didn't add the emoji, couldn't find it.")
#                 except discord.HTTPException:
#                     await message.channel.send("Error while trying to add the emoji.")
#                 else:
#                     new_time: datetime = datetime.utcnow() + timedelta(minutes=random.randint(1, config[message.channel.id]["frequency"]))
#                     await self.config.channel(message.channel).set_raw("next_react_time", value=new_time.timestamp())