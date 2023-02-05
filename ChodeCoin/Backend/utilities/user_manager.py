import re

from ChodeCoin.Backend.enums.permission_level import PermissionLevel
from ChodeCoin.Backend.services.admin_record_portal import AdminRecordPortal
from ChodeCoin.Backend.services.coin_bank_portal import CoinBankPortal
from ChodeCoin.Backend.helpers.date_helper import DateHelper


class UserManager:
    def __init__(self, coin_bank_portal=CoinBankPortal(), admin_record_portal=AdminRecordPortal(), date_helper=DateHelper(),):
        self.coin_bank_portal = coin_bank_portal
        self.admin_record_portal = admin_record_portal
        self.date_helper = date_helper

    def user_exists(self, target_user: str):
        user_exists = self.coin_bank_portal.user_exists(target_user)
        return user_exists

    def create_new_user(self, target_user):
        self.coin_bank_portal.create_new_user(target_user)

    def is_admin_user(self, target_user):
        return self.admin_record_portal.get_admin_permission(target_user) in ["1", "2"]

    def set_permission_level(self, target_user, permission_level):
        new_permission = PermissionLevel[permission_level]
        if self.admin_record_portal.admin_exists(target_user):
            return self.admin_record_portal.set_permission_level(target_user, new_permission.value)
        else:
            return self.admin_record_portal.create_new_admin(target_user, new_permission.value)

    def delete_all_users(self):
        bank_records = self.coin_bank_portal.get_all_users()
        for bank_record in bank_records:
            self.coin_bank_portal.delete_user(bank_record["name"])

    def prune_users(self):
        bank_records = self.coin_bank_portal.get_all_users()
        for bank_record in bank_records:
            if self.date_helper.is_older_than_six_months(bank_record["last_modified"]):
                self.coin_bank_portal.delete_user(bank_record["name"])

    def delete_user(self, target_user):
        self.coin_bank_portal.delete_user(target_user)
