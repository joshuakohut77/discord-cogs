from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.utilities.message_reader import is_leaderboard_command
from ChodeCoin.Backend.utilities.reply_generator import generate_leaderboard_reply
from ChodeCoin.Backend.utilities.info_manager import InfoManager


def get_leaderboard_description():
    return Command("!leaderboard", "Displays the top 10 ChodeCoin owners in the server.")


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
