from ChodeCoin.utilities.info_manager import InfoManager
from ChodeCoin.utilities.message_reader import MessageReader, is_targeted_coin_count_command


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
        targeted_user = self.message_reader.find_targeted_coin_count_user(message)
        if targeted_user == "":
            targeted_user = message_author
        return self.info_manager.get_current_balance(targeted_user)
