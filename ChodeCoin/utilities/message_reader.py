import re
from ChodeCoin.utilities.coin_manager import CoinManager
from ChodeCoin.utilities.info_manager import InfoManager
from ChodeCoin.enums.command_type import CommandType


def is_leaderboard_command(message: str):
    standardized_message = message.lower()
    command_search = re.search(r"^!leaderboard", standardized_message)
    if command_search:
        return True
    else:
        return False


def is_targeted_coin_count_command(message: str):
    standardized_message = message.lower()
    command_search = re.search(r"^!coincount", standardized_message)
    if command_search:
        return True
    else:
        return False


class MessageReader:

    def __init__(self, coin_manager=CoinManager(), info_manager=InfoManager()):
        self.coin_manager = coin_manager
        self.info_manager = info_manager

    def is_chodecoin_ping(self, message):
        is_plus_plus = self.find_plus_plus(message)
        if is_plus_plus:
            return True

        is_emoji_plus_plus = self.find_emoji_plus_plus(message)
        if is_emoji_plus_plus:
            return True

        is_minus_minus = self.find_minus_minus(message)
        if is_minus_minus:
            return True

        is_emoji_minus_minus = self.find_emoji_minus_minus(message)
        if is_emoji_minus_minus:
            return True

        return False

    def find_targeted_coin_count_user(self, message):
        command_search_result = ""
        standardized_message = message.lower()
        command_search_user = re.search(r"^!coincount", standardized_message)
        if command_search_user:
            command_search_result = command_search_user.group(0)
        un_formatted_user = command_search_result[10:len(str(command_search_result))].strip()
        if un_formatted_user == "":
            return None
        formatted_user = ""
        if len(un_formatted_user) < 32:
            return un_formatted_user
        else:
            formatted_user = un_formatted_user[:32].strip()
            return formatted_user

    def format_targeted_user(self, targeted_user, process):
        if process == CommandType.text:
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            discord_id_check = re.search(r"\d{18,20}>", formatted_user)
            if discord_id_check:
                discord_user = discord_id_check.group(0)
                formatted_user = f"<@{discord_user[:len(formatted_user) - 1]}>"
        elif process == CommandType.emoji_plus_plus:
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            discord_id_check = re.search(r"\d{18,20}>", formatted_user)
            if discord_id_check:
                discord_user = discord_id_check.group(0)
                formatted_user = f"<@{discord_user[:len(formatted_user) - 1]}>"
        elif process == CommandType.emoji_minus_minus:
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user) - 25].strip()
            formatted_user = formatted_user[:len(formatted_user) - 25].strip()
            discord_id_check = re.search(r"\d{18,20}>", formatted_user)
            if discord_id_check:
                discord_user = discord_id_check.group(0)
                formatted_user = f"<@{discord_user[:len(formatted_user) - 1]}>"
        else:
            raise NameError("Process not defined")

        return formatted_user

    def find_plus_plus(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))[+]{2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.format_targeted_user(targeted_user, CommandType.text)
            return formatted_user
        else:
            return None

    def find_minus_minus(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))-{2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.format_targeted_user(targeted_user, CommandType.text)
            return formatted_user
        else:
            return None

    def find_emoji_plus_plus(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))((🍆)\s*){2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.format_targeted_user(targeted_user, CommandType.emoji_plus_plus)
            return formatted_user
        else:
            return None

    def find_emoji_minus_minus(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))((<:No:1058833719399567460>)\s*){2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.format_targeted_user(targeted_user, CommandType.emoji_minus_minus)
            return formatted_user
        else:
            return None
