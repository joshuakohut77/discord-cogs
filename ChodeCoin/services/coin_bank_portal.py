import json
from ..helpers.date_helper import DateHelper


class CoinBankPortal:
    def __init__(self, date_helper=DateHelper()):
        self.date_helper = date_helper
    def change_coin_count(self, target_user, amount):
        with open("ChodeCoin/db/coin_bank.json", "r+") as file:
            bank_records = json.load(file)
            for user in bank_records:
                if user["name"] == target_user:
                    current_coin_balance = user["coin_count"]
                    new_coin_balance = current_coin_balance + amount
                    user["coin_count"] = new_coin_balance
                    break
            json.dump(bank_records, file)

    def create_new_user(self, target_user):
        new_user = {"name": target_user, "coin_count": 0, "last_modified": self.date_helper.current_timestamp_string()}
        with open("ChodeCoin/db/coin_bank.json", "r+") as file:
            file_data = json.load(file)
            file_data["bank_records"].append(new_user)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    def user_exists(self, target_user):
        with open("ChodeCoin/db/coin_bank.json", "r") as file:
            bank_records = json.load(file)
            for user in bank_records:
                if user["name"] == target_user:
                    return True
            return False
