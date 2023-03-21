from ChodeCoin.Backend.utilities.message_reader import is_help_command
from ChodeCoin.Backend.utilities.reply_generator import generate_help_reply
from ChodeCoin.Backend.workflows.export_coin_bank_workflow import ExportCoinBankWorkflow
from ChodeCoin.Backend.workflows.permission_workflow import get_permission_description
from ChodeCoin.Backend.workflows.chodekill_workflow import get_chodekill_description
from ChodeCoin.Backend.workflows.leaderboard_workflow import get_leaderboard_description
from ChodeCoin.Backend.workflows.set_info_workflow import get_set_info_description
from ChodeCoin.Backend.workflows.targeted_coin_count_workflow import get_targeted_coin_count_description
from ChodeCoin.Backend.workflows.chodecoin_ping_workflow import get_chodecoin_ping_description


def is_help_workflow(message):
    return is_help_command(message)


class HelpWorkflow:
    def __init__(
            self,
            export_coin_bank_workflow=ExportCoinBankWorkflow(),
    ):
        self.export_coin_bank_workflow = export_coin_bank_workflow

    def process_help_request(self):
        command_descriptions = [
            get_permission_description(),
            get_chodekill_description(),
            get_leaderboard_description(),
            get_targeted_coin_count_description(),
            get_chodecoin_ping_description(),
            get_set_info_description(),
            self.export_coin_bank_workflow.get_export_coin_bank_description(),
        ]
        return generate_help_reply(command_descriptions)
