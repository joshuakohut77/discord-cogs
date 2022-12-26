import json
import discord
import json
from discord import embeds
from services.coin_bank_portal import CoinBankPortal


class UserManager:
    def __init__(self, coin_bank_portal=CoinBankPortal()):
        self.coin_bank_portal = coin_bank_portal
    def user_exists(self, target_user: str):
        with open('DB/coin_bank.json', 'r') as openfile:
            coin_bank = json.load(openfile)
            for user in coin_bank:
                if user['name'] == target_user:
                    return True
            return False

    def create_new_user(self, target_user):
        self.coin_bank_portal.create_new_user(target_user)
