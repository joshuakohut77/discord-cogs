from ChodeCoin.utilities.coin_manager import CoinManager
from ChodeCoin.utilities.message_reader import MessageReader, is_leaderboard_command
from ChodeCoin.utilities.reply_generator import ReplyGenerator, generate_leaderboard_reply
from ChodeCoin.utilities.info_manager import InfoManager


def is_leaderboard_workflow(message):
    return is_leaderboard_command(message)


class LeaderboardWorkflow:
    def __init__(
            self,
            message_reader=MessageReader(),
            coin_manager=CoinManager(),
            reply_generator=ReplyGenerator(),
            info_manager=InfoManager(),
    ):
        self.message_reader = message_reader
        self.coin_manager = coin_manager
        self.reply_generator = reply_generator
        self.info_manager = info_manager

    def process_leaderboard_request(self):
        users = self.info_manager.get_wealthiest_users(10)
        return generate_leaderboard_reply(users)