from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user
from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.utilities.message_reader import MessageReader, is_dank_hof_command, find_targeted_dank_hof_user
from ChodeCoin.Backend.utilities.reply_generator import generate_dank_hof_reply
from ChodeCoin.Backend.utilities.info_manager import InfoManager
from ChodeCoin.Backend.utilities.reply_generator import generate_dank_hof_reply
from ChodeCoin.Backend.utilities.coin_manager import CoinManager
from ChodeCoin.Backend.utilities.user_manager import UserManager


def is_dank_hof_workflow(channel):
    return is_dank_hof_command(channel)


class DankHofWorkflow:
    def __init__(
            self,
            info_manager=InfoManager(),
            user_manager=UserManager(),
            message_reader=MessageReader(),
            coin_manager=CoinManager(),
    ):
        self.info_manager = info_manager
        self.user_manager = user_manager
        self.message_reader = message_reader
        self.coin_manager = coin_manager

    def get_dankhof_description(self):
        return Command("!dankhof [user]", "Bestows Dank Hall Of Fame honors upon target user.", True)

    def process_dank_hof_request(self, message, author):
        if self.user_manager.is_admin_user(convert_to_discord_user(author)):
            target_user = find_targeted_dank_hof_user(message)
            self.coin_manager.process_dank_hof_entry(target_user)
            response = generate_dank_hof_reply(target_user)
            return response
        else:
            return "You don't have permission to bestow Dank Hall of Fame honors. Please reach out to the server admin if you believe you should have such access."
