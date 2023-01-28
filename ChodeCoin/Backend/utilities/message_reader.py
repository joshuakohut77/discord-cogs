import re
from ChodeCoin.Backend.utilities.coin_manager import CoinManager
from ChodeCoin.Backend.utilities.info_manager import InfoManager
from ChodeCoin.Backend.enums.command_type import CommandType
from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user


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


def is_dank_hof_command(message):
    search_result = re.search(r"^!dankhof", message)
    if search_result:
        return True
    else:
        return False


def is_admin_command(message):
    search_result = re.search(r"^!setpermission", message)
    if search_result:
        return True
    else:
        return False


def find_targeted_dank_hof_user(message):
    dank_user = ""

    dank_user_result = re.search(r"^.{8,11}(.{1,32})", message)

    if dank_user_result:
        dank_user = dank_user_result.group(0)
        un_formatted_user = dank_user[8:len(str(dank_user))].strip()
        if len(un_formatted_user) < 1:
            return None
        user_name_check = re.search(r"\d{18,20}", un_formatted_user)
        if user_name_check:
            user_discord_id = user_name_check.group(0)
            formatted_user = f"<@{user_discord_id}>"
            return formatted_user
        else:
            return un_formatted_user
    else:
        return None


def find_targeted_admin_data(message):
    target_user = ""
    new_admin_level = ""
    command_result = re.search(r"^![Ss][Ee][Tt][Pp][Ee][Rr][Mm][Ii][Ss][Ss][Ii][Oo][Nn]\s{1,3}(\d{18,20}|<@\d{18,20}>)\s{1,3}([Oo][Ww][Nn][Ee][Rr]|[Aa][Dd][Mm][Ii][Nn]|[Vv][Ii][Ee][Ww][Ee][Rr]|[Nn][Oo][Nn][Ee])$", message)
    if command_result:
        result = command_result.group(0)
        segments = re.split(r"\s{1,3}", result)
        target_user = convert_to_discord_user(segments[1])
        new_admin_level = segments[2].lower()
        return target_user, new_admin_level
    else:
        return None, None


def is_chodekill_command(message):
    search_result = re.search(r"^!chodekill", message)
    if search_result:
        return True
    else:
        return False


def is_help_command(message):
    identifying_string = message.lower()
    search_result = re.search(r"^!chodecoin\s{1,3}help", identifying_string)
    alternate_search_result = re.search(r"^!chodecoin$", identifying_string)
    if search_result or alternate_search_result:
        return True
    else:
        return False


def find_chodekill_data(message):
    command_result = re.search(r"^![Cc][Hh][Oo][Dd][Ee][Kk][Ii][Ll][Ll]\s{1,3}(--all|--[Pp][Rr][Uu][Nn][Ee]|.{1,32})$", message)
    if command_result:
        result = command_result.group(0)
        key = result[10:len(str(result))].strip()
        return key
    else:
        return None


class MessageReader:

    def __init__(self, coin_manager=CoinManager(), info_manager=InfoManager()):
        self.coin_manager = coin_manager
        self.info_manager = info_manager

    def is_chodecoin_ping(self, message):
        if self.is_plus_plus_command(message):
            return True

        if self.is_minus_minus_command(message):
            return True

        if self.is_emoji_plus_plus_command(message):
            return True

        if self.is_emoji_minus_minus_command(message):
            return True

        return False

    def find_targeted_coin_count_user(self, message, message_author):
        command_search_result = ""

        command_search_user = re.search(r"^.{10,13}(.{1,32})", message)

        if command_search_user:
            command_search_result = command_search_user.group(0)

        un_formatted_user = command_search_result[10:len(str(command_search_result))].strip()

        if len(un_formatted_user) < 1:
            return f"<@{message_author}>"

        user_name_check = re.search(r"\d{18,20}", un_formatted_user)

        if user_name_check:
            user_discord_id = user_name_check.group(0)
            formatted_user = f"<@{user_discord_id}>"
            return formatted_user

        else:
            return un_formatted_user

    def is_plus_plus_command(self, message):
        search_result = re.search(r"^((@.{1,32}?)|(<\d{18,20}>\s{1,3}?))[+]{2}", message)
        return search_result

    def extract_plus_plus_target(self, message):
        search_result = re.search(r"^((@.{1,32}?)|(<\d{18,20}>\s{1,3}?))[+]{2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = convert_to_discord_user(formatted_user)
            return formatted_user

    def is_minus_minus_command(self, message):
        search_result = re.search(r"^((@.{1,32}?)|(<\d{18,20}>\s{1,3}?))-{2}", message)
        return search_result

    def extract_minus_minus_target(self, message):
        search_result = re.search(r"^((@.{1,32}?)|(<\d{18,20}>\s{1,3}?))-{2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = convert_to_discord_user(formatted_user)
            return formatted_user

    def is_emoji_plus_plus_command(self, message):
        search_result = re.search(r"((@.{1,32}?)|(<\d{18,20}>\s{1,3}?))((🍆)\s*){2}", message)
        return search_result

    def extract_emoji_plus_plus_target(self, message):
        search_result = re.search(r"((@.{1,32}?)|(<\d{18,20}>\s{1,3}?))((🍆)\s*){2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = convert_to_discord_user(formatted_user)
            return formatted_user

    def is_emoji_minus_minus_command(self, message):
        search_result = re.search(r"((@.{1,32}?)|(<\d{18,20}>\s{1,3}?))((<:No:1058833719399567460>)\s*){2}", message)
        return search_result

    def extract_emoji_minus_minus_target(self, message):
        search_result = re.search(r"((@.{1,32}?)|(<\d{18,20}>\s{1,3}?))((<:No:1058833719399567460>)\s*){2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user) - 25].strip()
            formatted_user = formatted_user[:len(formatted_user) - 25].strip()
            formatted_user = convert_to_discord_user(formatted_user)
            return formatted_user
