from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.utilities.info_manager import InfoManager
from ChodeCoin.Backend.utilities.message_reader import MessageReader, is_targeted_coin_count_command
from ChodeCoin.Backend.utilities.reply_generator import generate_targeted_coin_count_reply


def get_targeted_coin_count_description():
    return Command("!coincount [user|<nothing>]", "Displays the ChodeCoin owned by the user specified. Will give your own ChodeCoin amount if no user is provided.")


def is_targeted_coin_count_request(message):
    return is_targeted_coin_count_command(message)


class TargetedCoinCountWorkflow:
    def __init__(
            self,
            info_manager=InfoManager(),
            message_reader=MessageReader(),
    ):
        self.info_manager = info_manager
        self.message_reader = message_reader

    def process_targeted_coin_count_request(self, message, message_author):
        targeted_user_name = self.message_reader.find_targeted_coin_count_user(message, message_author)

        targeted_user_coin_count = self.info_manager.get_current_balance(targeted_user_name)
        # TODO figure out wtf I did here because that seems completely unnecessary
        if targeted_user_coin_count is not None:
            return generate_targeted_coin_count_reply(targeted_user_name, targeted_user_coin_count)
        else:
            return generate_targeted_coin_count_reply(targeted_user_name, None)
