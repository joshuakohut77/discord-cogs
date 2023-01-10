from ChodeCoin.Backend.helpers.array_helper import ArrayHelper
from ChodeCoin.Backend.services.coin_bank_portal import CoinBankPortal
from ChodeCoin.Backend.utilities.user_manager import UserManager
from ChodeCoin.Backend.objects.user import User


class InfoManager:
    def __init__(self, user_manager=UserManager(), coin_bank_portal=CoinBankPortal(), array_helper=ArrayHelper()):
        self.user_manager = user_manager
        self.coin_bank_portal = coin_bank_portal
        self.array_helper = array_helper

    def get_current_balance(self, target_user):
        user_exists = self.user_manager.user_exists(target_user)

        if user_exists:
            return self.coin_bank_portal.get_current_balance(target_user)
        else:
            return None

    def get_wealthiest_users(self, count):
        bank_records = self.coin_bank_portal.get_all_users()
        wealthiest_list = []
        for bank_record in bank_records:
            wealthiest_list = self.array_helper.add_if_in_wealthiest_group(wealthiest_list, User(bank_record["name"], bank_record["coin_count"]), count)
        return wealthiest_list

    def get_targeted_coin_count(self, targeted_user):
        return self.coin_bank_portal.get_current_balance(targeted_user)
