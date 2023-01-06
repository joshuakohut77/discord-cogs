from ChodeCoin.utilities.info_manager import InfoManager
from ChodeCoin.utilities.message_reader import MessageReader, is_targeted_coin_count_command
from ChodeCoin.utilities.reply_generator import generate_targeted_coin_count_reply


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
        targeted_user_name = self.message_reader.find_targeted_coin_count_user(message)
        return targeted_user_name, None
        # if targeted_user_name is None:
        #     targeted_user_name = message_author
        # targeted_user_coin_count = self.info_manager.get_current_balance(targeted_user_name)
        # if targeted_user_coin_count is not None:
        #     return generate_targeted_coin_count_reply(targeted_user_name, targeted_user_coin_count)
        # else:
        #     return generate_targeted_coin_count_reply(None, None)
