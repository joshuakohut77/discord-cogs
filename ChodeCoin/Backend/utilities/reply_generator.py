import discord
from ChodeCoin.Backend.helpers.array_helper import translate_user_info_to_display_strings, translate_command_array_to_display_strings
from ChodeCoin.Backend.utilities.info_manager import InfoManager


def generate_leaderboard_reply(user_array: []):
    names, coin_counts = translate_user_info_to_display_strings(user_array)
    embed = discord.Embed()
    embed = discord.Embed(title="ChodeCoin Leaderboard", color=0x0b1bf4)
    embed.add_field(name="Name", value=str(names), inline=True)
    embed.add_field(name="ChodeCoin", value=str(coin_counts), inline=True)
    return "", embed


def generate_help_reply(command_descriptions: []):
    commands, descriptions = translate_command_array_to_display_strings(command_descriptions)
    embed = discord.Embed()
    embed = discord.Embed(title="ChodeCoin Commands", color=0x0b1bf4)
    embed.add_field(name="Command", value=str(commands), inline=True)
    embed.add_field(name="Description", value=str(descriptions), inline=True)
    return "", embed


def generate_targeted_coin_count_reply(user_name, user_coin_count):
    if user_coin_count is not None:
        return f"{user_name} has {user_coin_count} ChodeCoin in the bank", None
    else:
        return f"{user_name} isn't set up in the bank and therefore has zero ChodeCoin", None


def generate_admin_updated_reply(target_user):
    return f"Updated permission for {target_user}!"


def generate_admin_no_permission_reply():
    return "You don't have permission to manage users. Please reach out to the server admin if you believe you should have such access."


def generate_command_error_reply():
    return "Either you or I did something wrong with that command, double check the syntax and/or bother Mark about it."


def generate_dank_hof_reply(target_user):
    return f"Because of the dankness of your dank af post, by the power invested in me I hereby bestow upon {target_user} ten ChodeCoin! Dilly Dilly"


def generate_chodekill_all_reply():
    return "It as been done. All bank accounts have been deleted."


def generate_chodekill_prune_reply():
    return "Anyone without activity within the last 6 months are now deleted."


def generate_chodekill_assassinate_reply(target_user):
    return f"{target_user} has been assassinated, and is no longer registered in the bank."


class ReplyGenerator:
    def __init__(self, info_manager=InfoManager()):
        self.info_manager = info_manager

    def generate_chodecoin_ping_reply(self, targeted_user, process, amount):
        if amount == 1:
            amount = "a"
        current_balance = self.info_manager.get_current_balance(targeted_user)
        if targeted_user is not None:
            if process == "plus_plus":
                return f"Gave {targeted_user} {amount} ChodeCoin! {targeted_user} now has {current_balance} in the bank."
            elif process == "minus_minus":
                return f"{targeted_user} lost {amount} ChodeCoin! {targeted_user} now has {current_balance} in the bank."
