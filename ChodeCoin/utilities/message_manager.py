import re
from ChodeCoin.utilities.coin_manager import CoinManager


class MessageFormatter:

    def __init__(self, coin_manager=CoinManager()):
        self.coin_manager = coin_manager

    def process_message(self, message):
        is_plus_plus, targeted_user = self.find_plus_plus(message)
        if is_plus_plus:
            self.coin_manager.process_plus_plus(targeted_user)
            return

        is_eggplant_eggplant, targeted_user = self.find_eggplant_eggplant(message)
        if is_eggplant_eggplant:
            self.coin_manager.process_plus_plus(targeted_user)
            return

        is_minus_minus, targeted_user = self.find_minus_minus(message)
        if is_minus_minus:
            self.coin_manager.process_minus_minus(targeted_user)
            return

        is_no_no, targeted_user = self.find_no_no(message)
        if is_no_no:
            self.coin_manager.process_minus_minus(targeted_user)
            return

    def extract_targeted_user(self, targeted_user, process):
        if process == "Text":
            preformat = re.search("@.{2,32}?[+-]", targeted_user)
            formatted_user = preformat[:len(str(targeted_user))-1].strip()
        elif process == "Eggplant":
            preformat = re.search("@.{2,32}?:", targeted_user)
            formatted_user = preformat[:len(str(targeted_user))-1].strip()
        elif process == "No":
            preformat = re.search("@.{2,32}?:", targeted_user)
            formatted_user = preformat[:len(str(targeted_user))-1].strip()
        else:
            raise NameError("Process not defined")

        return formatted_user

    def find_plus_plus(self, message):
        targeted_user = ""
        targeted_user = re.search("@.{2,32}?[+]{2}", message)
        if targeted_user != "":
            formatted_user = self.extract_targeted_user(targeted_user, "Text")
            return True, formatted_user
        else:
            return False, message

    def find_minus_minus(self, message):
        targeted_user = ""
        targeted_user = re.search("@.{2,32}?-{2}", message)
        if targeted_user != "":
            formatted_user = self.extract_targeted_user(targeted_user, "Text")
            return True, formatted_user
        else:
            return False, message

    def find_eggplant_eggplant(self, message):
        targeted_user = ""
        targeted_user = re.search("@.{2,32}?((:eggplant:)\s*){2}", message)
        if targeted_user != "":
            formatted_user = self.extract_targeted_user(targeted_user, "Text")
            return True, formatted_user
        else:
            return False, message

    def find_no_no(self, message):
        targeted_user = ""
        targeted_user = re.search("@.{2,32}?((:No:)\s*){2}", message)
        if targeted_user != "":
            formatted_user = self.extract_targeted_user(targeted_user, "Text")
            return True, formatted_user
        else:
            return False, message

