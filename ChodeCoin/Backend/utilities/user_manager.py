from ChodeCoin.Backend.services.coin_bank_portal import CoinBankPortal


class UserManager:
    def __init__(self, coin_bank_portal=CoinBankPortal()):
        self.coin_bank_portal = coin_bank_portal

    def user_exists(self, target_user: str):
        user_exists = self.coin_bank_portal.user_exists(target_user)
        return user_exists

    def create_new_user(self, target_user):
        self.coin_bank_portal.create_new_user(target_user)
