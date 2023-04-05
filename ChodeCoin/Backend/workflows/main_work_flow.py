from ChodeCoin.Backend.utilities.guard import Guard
from ChodeCoin.Backend.workflows.import_coin_bank_workflow import ImportCoinBankWorkflow
from ChodeCoin.Backend.workflows.permission_workflow import PermissionWorkflow, is_permission_workflow
from ChodeCoin.Backend.workflows.chodecoin_ping_workflow import ChodeCoinPingWorkflow
from ChodeCoin.Backend.workflows.help_workflow import is_help_workflow, HelpWorkflow
from ChodeCoin.Backend.workflows.leaderboard_workflow import LeaderboardWorkflow, is_leaderboard_workflow
from ChodeCoin.Backend.workflows.set_info_workflow import SetInfoWorkflow, is_set_info_workflow
from ChodeCoin.Backend.workflows.targeted_coin_count_workflow import TargetedCoinCountWorkflow, is_targeted_coin_count_request
from ChodeCoin.Backend.workflows.dank_hof_workflow import DankHofWorkflow, is_dank_hof_workflow
from ChodeCoin.Backend.workflows.chodekill_workflow import ChodeKillWorkflow, is_chodekill_workflow
from ChodeCoin.Backend.workflows.export_coin_bank_workflow import ExportCoinBankWorkflow
from ChodeCoin.Backend.enums.request_for import RequestFor


class WorkFlow:
    def __init__(
            self,
            chodecoin_ping_workflow=ChodeCoinPingWorkflow(),
            leaderboard_workflow=LeaderboardWorkflow(),
            targeted_coin_count_workflow=TargetedCoinCountWorkflow(),
            dank_hof_workflow=DankHofWorkflow(),
            admin_workflow=PermissionWorkflow(),
            chodekill_workflow=ChodeKillWorkflow(),
            help_workflow=HelpWorkflow(),
            set_info_workflow=SetInfoWorkflow(),
            export_coin_bank_workflow=ExportCoinBankWorkflow(),
            import_coin_bank_workflow=ImportCoinBankWorkflow(),
            guard=Guard()):
        self.chodecoin_ping_workflow = chodecoin_ping_workflow
        self.leaderboard_workflow = leaderboard_workflow
        self.targeted_coin_count_workflow = targeted_coin_count_workflow
        self.dank_hof_workflow = dank_hof_workflow
        self.admin_workflow = admin_workflow
        self.chodekill_workflow = chodekill_workflow
        self.help_workflow = help_workflow
        self.set_info_workflow = set_info_workflow
        self.export_coin_bank_workflow = export_coin_bank_workflow
        self.import_coin_bank_workflow = import_coin_bank_workflow
        self.guard = guard

    async def process_message(self, message, author, attachments):
        process = self.identify_request(message)

        if process == RequestFor.chodecoin_ping:
            reply = self.chodecoin_ping_workflow.process_chodecoin_ping_request(message, author)
            return reply, None, None

        elif process == RequestFor.leaderboard:
            return None, self.leaderboard_workflow.process_leaderboard_request(), None, None

        elif process == RequestFor.targeted_coin_count:
            return self.targeted_coin_count_workflow.process_targeted_coin_count_request(message, author), None, None

        elif process == RequestFor.dank_hof:
            return self.dank_hof_workflow.process_dank_hof_request(message, author), None, None

        elif process == RequestFor.permission:
            return self.admin_workflow.process_permission_request(message, author), None, None

        elif process == RequestFor.chodekill:
            return self.chodekill_workflow.process_chodekill_request(message, author), None, None

        elif process == RequestFor.help:
            return self.help_workflow.process_help_request(), None, None

        elif process == RequestFor.set_info:
            return self.set_info_workflow.process_set_info_request(message, author), None, None

        elif process == RequestFor.export_coin_bank:
            return self.export_coin_bank_workflow.process_export_coin_bank_request(author)

        elif process == RequestFor.import_coin_bank:
            return await self.import_coin_bank_workflow.process_import_coin_bank_request(author, attachments), None, None

        else:
            return None, None, None

    def identify_request(self, message):
        if self.chodecoin_ping_workflow.is_chodecoin_ping(message):
            return RequestFor.chodecoin_ping
        elif is_leaderboard_workflow(message):
            return RequestFor.leaderboard
        elif is_targeted_coin_count_request(message):
            return RequestFor.targeted_coin_count
        elif is_dank_hof_workflow(message):
            return RequestFor.dank_hof
        elif is_permission_workflow(message):
            return RequestFor.permission
        elif is_chodekill_workflow(message):
            return RequestFor.chodekill
        elif is_help_workflow(message):
            return RequestFor.help
        elif is_set_info_workflow(message):
            return RequestFor.set_info
        elif self.export_coin_bank_workflow.is_export_coin_bank_workflow(message):
            return RequestFor.export_coin_bank
        elif self.import_coin_bank_workflow.is_import_coin_bank_workflow(message):
            return RequestFor.import_coin_bank
        else:
            return None
