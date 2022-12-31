import json
from pathlib import Path
from ..helpers.date_helper import DateHelper


class CoinBankPortal:
    def __init__(self, date_helper=DateHelper()):
        self.date_helper = date_helper
        self.db_path = f"{Path(__file__).parents[1]}/db/coin_bank.json"

    def change_coin_count(self, target_user, amount):
        with open(self.db_path, "r+") as file:
            bank = json.load(file)
            for bank_record in bank["bank_records"]:
                if target_user in bank_record.keys():
                    current_coin_balance = bank_record["coin_count"]
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
            for bank_record in bank["bank_records"]:
                if target_user in bank_record["name"]:
                    return True
                else:
                    return False
