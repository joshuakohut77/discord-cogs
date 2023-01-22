import json
from ChodeCoin.Backend.objects.user import User, convert_user_to_json
from ChodeCoin.Backend.helpers.array_helper import ArrayHelper
from ChodeCoin.Backend.helpers.timestamp_helper import TimestampHelper
from pathlib import Path


class CoinBankPortal:
    def __init__(self, timestamp_helper=TimestampHelper(), array_helper=ArrayHelper()):
        self.timestamp_helper = timestamp_helper
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
        user_to_add = User(target_user, 0, self.timestamp_helper.current_timestamp_string())
        new_user_entry = convert_user_to_json(user_to_add)
        with open(self.db_path, "r+") as file:
            bank = json.load(file)
            bank["bank_records"].append(new_user_entry)
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

    def get_all_users(self):
        with open(self.db_path, "r") as file:
            bank = json.load(file)
            return bank["bank_records"]

    def delete_user(self, target_user):
        with open(self.db_path, "r") as file:
            bank = json.load(file)
            for i in range(len(bank)):
                if bank[i]["name"] == target_user:
                    bank.pop(i)
                    break
        with open(self.db_path, "wt") as file:
            json.dump(bank, file, indent=4)
