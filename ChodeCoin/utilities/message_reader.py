import re
from ChodeCoin.utilities.coin_manager import CoinManager
from ChodeCoin.utilities.info_manager import InfoManager


class MessageManager:

    def __init__(self, coin_manager=CoinManager(), info_manager=InfoManager()):
        self.coin_manager = coin_manager
        self.info_manager = info_manager

    def is_chodecoin_ping(self, message):
        is_plus_plus = self.find_plus_plus(message)
        if is_plus_plus:
            return True

        is_eggplant_eggplant = self.find_eggplant_eggplant(message)
        if is_eggplant_eggplant:
            return True

        is_minus_minus = self.find_minus_minus(message)
        if is_minus_minus:
            return True

        is_no_no = self.find_no_no(message)
        if is_no_no:
            return True

        return False

    def extract_targeted_user(self, targeted_user, process):
        if process == "Text":
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user)-1].strip()
            formatted_user = formatted_user[:len(formatted_user)-1].strip()
            discord_id_check = re.search(r"\d{18,20}>", formatted_user)
            if discord_id_check:
                discord_user = discord_id_check.group(0)
                formatted_user = f"<@{discord_user[:len(formatted_user)-1]}>"
        elif process == "Eggplant":
            formatted_user = targeted_user[1:len(str(targeted_user))].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            formatted_user = formatted_user[:len(formatted_user) - 1].strip()
            discord_id_check = re.search(r"\d{18,20}>", formatted_user)
            if discord_id_check:
                discord_user = discord_id_check.group(0)
                formatted_user = f"<@{discord_user[:len(formatted_user) - 1]}>"
        elif process == "No":
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
            formatted_user = self.extract_targeted_user(targeted_user, "Text")
            return formatted_user
        else:
            return None

    def find_minus_minus(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))-{2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.extract_targeted_user(targeted_user, "Text")
            return formatted_user
        else:
            return None

    def find_eggplant_eggplant(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))((🍆)\s*){2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.extract_targeted_user(targeted_user, "Eggplant")
            return formatted_user
        else:
            return None

    def find_no_no(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))((<:No:1058833719399567460>)\s*){2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.extract_targeted_user(targeted_user, "No")
            return formatted_user
        else:
            return None
