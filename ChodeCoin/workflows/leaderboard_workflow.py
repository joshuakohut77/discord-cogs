from ChodeCoin.utilities.message_reader import is_leaderboard_command
from ChodeCoin.utilities.reply_generator import generate_leaderboard_reply
from ChodeCoin.utilities.info_manager import InfoManager


def is_leaderboard_workflow(message):
    return is_leaderboard_command(message)


class LeaderboardWorkflow:
    def __init__(
            self,
            info_manager=InfoManager(),
    ):
        self.info_manager = info_manager

    def process_leaderboard_request(self):
        users = self.info_manager.get_wealthiest_users(10)
        return generate_leaderboard_reply(users)
