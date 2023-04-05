from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user
from ChodeCoin.Backend.utilities.message_reader import is_help_command
from ChodeCoin.Backend.utilities.reply_generator import generate_help_reply
from ChodeCoin.Backend.utilities.user_manager import UserManager
from ChodeCoin.Backend.workflows.dank_hof_workflow import DankHofWorkflow
from ChodeCoin.Backend.workflows.export_coin_bank_workflow import ExportCoinBankWorkflow
from ChodeCoin.Backend.workflows.import_coin_bank_workflow import ImportCoinBankWorkflow
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
            import_coin_bank_workflow=ImportCoinBankWorkflow(),
            user_manager=UserManager(),
            dankhof_workflow=DankHofWorkflow(),
    ):
        self.export_coin_bank_workflow = export_coin_bank_workflow
        self.import_coin_bank_workflow = import_coin_bank_workflow
        self.user_manager = user_manager
        self.dankhof_workflow = dankhof_workflow

    def process_help_request(self, author):
        has_admin_permission = self.user_manager.is_admin_user(convert_to_discord_user(author))
        command_descriptions = [
            get_permission_description(),
            get_leaderboard_description(),
            get_targeted_coin_count_description(),
            get_chodecoin_ping_description(),
            get_set_info_description(),
            get_chodekill_description(),
            self.export_coin_bank_workflow.get_export_coin_bank_description(),
            self.import_coin_bank_workflow.get_import_coin_bank_description(),
            self.dankhof_workflow.get_dankhof_description(),
        ]

        if has_admin_permission is False:
            all_descriptions = command_descriptions[:]
            for description in all_descriptions:
                if description.is_admin_command is True:
                    command_descriptions.remove(description)

        return generate_help_reply(command_descriptions)
