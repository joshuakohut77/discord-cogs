from .user_manager import UserManager
from ..services.coin_bank_portal import CoinBankPortal


class CoinManager:
    def __init__(self, user_manager=UserManager(), coin_bank_portal=CoinBankPortal()):
        self.user_manager = user_manager
        self.coin_bank_portal = coin_bank_portal

    def process_plus_plus(self, target_user):
        user_exists = self.user_manager.user_exists(target_user)

        if user_exists:
            self.coin_bank_portal.change_coin_count(target_user, 1)
        else:
            self.user_manager.create_new_user(target_user)
            self.coin_bank_portal.change_coin_count(target_user, 1)

    def process_minus_minus(self, target_user):
        user_exists = self.user_manager.user_exists(target_user)

        if user_exists:
            self.coin_bank_portal.change_coin_count(target_user, -1)
        else:
            self.user_manager.create_new_user(target_user)
            self.coin_bank_portal.change_coin_count(target_user, -1)
