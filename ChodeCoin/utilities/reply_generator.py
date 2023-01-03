import discord
from ChodeCoin.helpers.array_helper import translate_user_info_to_display_strings
from ChodeCoin.utilities.info_manager import InfoManager


def generate_leaderboard_reply(user_array: []):
    names, coin_counts = translate_user_info_to_display_strings(user_array)
    embed = discord.Embed()
    embed = discord.Embed(title="ChodeCoin Leaderboard", color=0x0b1bf4)
    embed.add_field(name="Name", value=names, inline=True)
    embed.add_field(name="ChodeCoin", value=coin_counts, inline=True)
    return "", embed


class ReplyGenerator:
    def __init__(self, info_manager=InfoManager()):
        self.info_manager = info_manager

    def generate_chodecoin_ping_reply(self, targeted_user, process, amount):
        if amount == 1:
            amount = "a"
        current_balance = self.info_manager.get_current_balance(targeted_user)
        if process == "plus_plus":
            return f"Gave {targeted_user} {amount} ChodeCoin! {targeted_user} now has {current_balance} in the bank."
        elif process == "minus_minus":
            return f"{targeted_user} lost {amount} ChodeCoin! {targeted_user} now has {current_balance} in the bank."
