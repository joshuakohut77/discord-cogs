from ChodeCoin.Backend.utilities.guard import Guard
from ChodeCoin.Backend.workflows.admin_workflow import AdminWorkflow, is_admin_workflow
from ChodeCoin.Backend.workflows.chodecoin_ping_workflow import ChodeCoinPingWorkflow
from ChodeCoin.Backend.workflows.help_workflow import is_help_workflow, HelpWorkflow
from ChodeCoin.Backend.workflows.leaderboard_workflow import LeaderboardWorkflow, is_leaderboard_workflow
from ChodeCoin.Backend.workflows.targeted_coin_count_workflow import TargetedCoinCountWorkflow, is_targeted_coin_count_request
from ChodeCoin.Backend.workflows.dank_hof_workflow import DankHofWorkflow, is_dank_hof_workflow
from ChodeCoin.Backend.workflows.chodekill_workflow import ChodeKillWorkflow, is_chodekill_workflow
from ChodeCoin.Backend.enums.request_for import RequestFor


class WorkFlow:
    def __init__(
            self,
            chodecoin_ping_workflow=ChodeCoinPingWorkflow(),
            leaderboard_workflow=LeaderboardWorkflow(),
            targeted_coin_count_workflow=TargetedCoinCountWorkflow(),
            dank_hof_workflow=DankHofWorkflow(),
            admin_workflow=AdminWorkflow(),
            chodekill_workflow=ChodeKillWorkflow(),
            help_workflow=HelpWorkflow(),
            guard=Guard()):
        self.chodecoin_ping_workflow = chodecoin_ping_workflow
        self.leaderboard_workflow = leaderboard_workflow
        self.targeted_coin_count_workflow = targeted_coin_count_workflow
        self.dank_hof_workflow = dank_hof_workflow
        self.admin_workflow = admin_workflow
        self.chodekill_workflow = chodekill_workflow
        self.help_workflow = help_workflow
        self.guard = guard

    def process_message(self, message, author):
        process = self.identify_request(message)

        if process == RequestFor.chodecoin_ping:
            reply = self.validate_input(message, author)
            if reply is None:
                reply = self.chodecoin_ping_workflow.process_chodecoin_ping_request(message)
            return reply, None

        elif process == RequestFor.leaderboard:
            return self.leaderboard_workflow.process_leaderboard_request()

        elif process == RequestFor.targeted_coin_count:
            return self.targeted_coin_count_workflow.process_targeted_coin_count_request(message, author)

        elif process == RequestFor.dank_hof:
            return self.dank_hof_workflow.process_dank_hof_request(message, author), None

        elif process == RequestFor.admin:
            return self.admin_workflow.process_admin_request(message, author), None

        elif process == RequestFor.chodekill:
            return self.chodekill_workflow.process_chodekill_request(message, author), None

        elif process == RequestFor.help:
            return self.help_workflow.process_help_request()

        else:
            return None, None

    def identify_request(self, message):
        if self.chodecoin_ping_workflow.is_chodecoin_ping(message):
            return RequestFor.chodecoin_ping
        elif is_leaderboard_workflow(message):
            return RequestFor.leaderboard
        elif is_targeted_coin_count_request(message):
            return RequestFor.targeted_coin_count
        elif is_dank_hof_workflow(message):
            return RequestFor.dank_hof
        elif is_admin_workflow(message):
            return RequestFor.admin
        elif is_chodekill_workflow(message):
            return RequestFor.chodekill
        elif is_help_workflow(message):
            return RequestFor.help
        else:
            return None

    def validate_input(self, message, author):
        reply = self.guard.against_self_plusplus(message, author)
        if reply is not None:
            return reply
        else:
            return None
