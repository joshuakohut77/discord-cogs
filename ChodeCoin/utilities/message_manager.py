import re
from ChodeCoin.utilities.coin_manager import CoinManager
from ChodeCoin.utilities.info_manager import InfoManager


class MessageManager:

    def __init__(self, coin_manager=CoinManager(), info_manager=InfoManager()):
        self.coin_manager = coin_manager
        self.info_manager = info_manager

    def process_message(self, message):
        is_plus_plus, targeted_user = self.find_plus_plus(message)
        if is_plus_plus:
            self.coin_manager.process_plus_plus(targeted_user)
            return_message = self.generate_reply(targeted_user, "plus_plus", 1)
            return True, return_message

        is_eggplant_eggplant, targeted_user = self.find_eggplant_eggplant(message)
        if is_eggplant_eggplant:
            self.coin_manager.process_plus_plus(targeted_user)
            return_message = self.generate_reply(targeted_user, "plus_plus", 1)
            return True, return_message

        is_minus_minus, targeted_user = self.find_minus_minus(message)
        if is_minus_minus:
            self.coin_manager.process_minus_minus(targeted_user)
            return_message = self.generate_reply(targeted_user, "minus_minus", 1)
            return True, return_message

        is_no_no, targeted_user = self.find_no_no(message)
        if is_no_no:
            self.coin_manager.process_minus_minus(targeted_user)
            return_message = self.generate_reply(targeted_user, "minus_minus", 1)
            return True, return_message

        return False, ""

    def generate_reply(self, targeted_user, process, amount):
        if amount == 1:
            amount = "a"
        current_balance = self.info_manager.get_current_balance(targeted_user)
        if process == "plus_plus":
            return f"Gave {targeted_user} {amount} ChodeCoin! {targeted_user} now has {current_balance} in the bank."
        elif process == "minus_minus":
            return f"{targeted_user} lost {amount} ChodeCoin! {targeted_user} now has {current_balance} in the bank."

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
            return True, formatted_user
        else:
            return False, message

    def find_minus_minus(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))-{2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.extract_targeted_user(targeted_user, "Text")
            return True, formatted_user
        else:
            return False, message

    def find_eggplant_eggplant(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))((🍆)\s*){2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.extract_targeted_user(targeted_user, "Eggplant")
            return True, formatted_user
        else:
            return False, message

    def find_no_no(self, message):
        search_result = re.search(r"((@.{2,32}?)|(<\d{18,20}>\s{1,3}?))((<:no:1058833719399567460>)\s*){2}", message)
        if search_result:
            targeted_user = search_result.group(0)
            formatted_user = self.extract_targeted_user(targeted_user, "No")
            return True, formatted_user
        else:
            return False, message
