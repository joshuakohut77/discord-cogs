from ChodeCoin.Backend.services.admin_record_portal import AdminRecordPortal
from ChodeCoin.Backend.services.coin_bank_portal import CoinBankPortal


class UserManager:
    def __init__(self, coin_bank_portal=CoinBankPortal(), admin_record_portal=AdminRecordPortal(),):
        self.coin_bank_portal = coin_bank_portal
        self.admin_record_portal = admin_record_portal

    def user_exists(self, target_user: str):
        user_exists = self.coin_bank_portal.user_exists(target_user)
        return user_exists

    def create_new_user(self, target_user):
        self.coin_bank_portal.create_new_user(target_user)

    def is_admin_user(self, target_user):
        return self.admin_record_portal.get_admin_permission(target_user) == 1
