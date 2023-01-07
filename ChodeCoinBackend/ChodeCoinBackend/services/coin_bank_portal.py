import json
from ChodeCoinBackend.ChodeCoinBackend.objects.user import User
from ChodeCoinBackend.ChodeCoinBackend.helpers.array_helper import ArrayHelper
from ChodeCoinBackend.ChodeCoinBackend.helpers.date_helper import DateHelper
from pathlib import Path


class CoinBankPortal:
    def __init__(self, date_helper=DateHelper(), array_helper=ArrayHelper()):
        self.date_helper = date_helper
        self.array_helper = array_helper
        self.db_path = f"{Path(__file__).parents[1]}/db/coin_bank.json"

    def change_coin_count(self, target_user, amount):
        with open(self.db_path, "r+") as file:
            bank = json.load(file)
            for bank_record in bank["bank_records"]:
                if bank_record["name"] == target_user:
                    current_coin_balance = bank_record["coin_count"].__int__()
                    new_coin_balance = current_coin_balance + amount
                    bank_record["coin_count"] = new_coin_balance
                    break
        with open(self.db_path, "wt") as file:
            json.dump(bank, file, indent=4)

    def create_new_user(self, target_user):
        new_user = {"name": target_user, "coin_count": 0, "last_modified": self.date_helper.current_timestamp_string()}
        with open(self.db_path, "r+") as file:
            bank = json.load(file)
            bank["bank_records"].append(new_user)
        with open(self.db_path, "wt") as file:
            json.dump(bank, file, indent=4)

    def user_exists(self, target_user):
        with open(self.db_path, "r") as file:
            bank = json.load(file)
            return any(bank_record["name"] == target_user for bank_record in bank["bank_records"])

    def get_current_balance(self, target_user):
        if self.user_exists(target_user):
            with open(self.db_path, "r") as file:
                bank = json.load(file)
                current_balance = ""
                for bank_record in bank["bank_records"]:
                    if bank_record["name"] == target_user:
                        current_balance = bank_record["coin_count"]
            return current_balance.__str__()
        else:
            return "User Does Not Exist"

    def get_wealthiest_users(self, return_count):
        with open(self.db_path, "r") as file:
            bank = json.load(file)
            user_list = []
            for bank_record in bank["bank_records"]:
                user_list = self.array_helper.add_if_in_wealthiest_group(user_list, User(bank_record["name"], bank_record["coin_count"]), return_count)
            return user_list
