from ChodeCoin.services.coin_bank_portal import CoinBankPortal
from ChodeCoin.utilities.user_manager import UserManager


class InfoManager:
    def __init__(self, user_manager=UserManager(), coin_bank_portal=CoinBankPortal()):
        self.user_manager = user_manager
        self.coin_bank_portal = coin_bank_portal

    def get_current_balance(self, target_user):
        user_exists = self.user_manager.user_exists(target_user)

        if user_exists:
            return self.coin_bank_portal.get_current_balance(target_user)
        else:
            return "User Does Not Exist"