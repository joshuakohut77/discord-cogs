import json
import discord
import json
from discord import embeds


class UserManager:
    def user_exists(self, target_user: str):
        with open('coin_bank.json', 'r') as openfile:
            coin_bank = json.load(openfile)
            for user in coin_bank:
                if user['name'] == target_user:
                    return True
            return False

    def create_user(self, target_user):
        print("Creating user")
