import json
import discord
import json
from discord import embeds
from user_manager import UserManager


class CoinManager:
    def process_plus_plus(self, target_user):
        user_manager = UserManager()
        user_exists = user_manager.user_exists(target_user)

        if user_exists:
            self.change_coin_count(target_user, 1)
        else:
            user_manager.create_user(target_user)
            self.change_coin_count(target_user, 1)

    def process_minus_minus(self, target_user):
        user_manager = UserManager()
        user_exists = user_manager.user_exists(target_user)

        if user_exists:
            self.change_coin_count(target_user, -1)
        else:
            user_manager.create_user(target_user)
            self.change_coin_count(target_user, -1)

    def change_coin_count(self, target_user, amount):
        print(f"adding {amount} to {target_user}'s ChodeCoin count.")
        # Get User Value
        # Add amount to User Value
        # Set User's Value to new Value