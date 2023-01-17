from ChodeCoin.Backend.utilities.guard import Guard
from ChodeCoin.Backend.workflows.chodecoin_ping_workflow import ChodeCoinPingWorkflow
from ChodeCoin.Backend.workflows.leaderboard_workflow import LeaderboardWorkflow, is_leaderboard_workflow
from ChodeCoin.Backend.workflows.targeted_coin_count_workflow import TargetedCoinCountWorkflow, \
    is_targeted_coin_count_request
from ChodeCoin.Backend.workflows.dank_hof_workflow import DankHofWorkflow, is_dank_hof_workflow
from ChodeCoin.Backend.enums.request_for import RequestFor


class WorkFlow:
    def __init__(
            self,
            chodecoin_ping_workflow=ChodeCoinPingWorkflow(),
            leaderboard_workflow=LeaderboardWorkflow(),
            targeted_coin_count_workflow=TargetedCoinCountWorkflow(),
            dank_hof_workflow=DankHofWorkflow(),
            guard=Guard()):
        self.chodecoin_ping_workflow = chodecoin_ping_workflow
        self.leaderboard_workflow = leaderboard_workflow
        self.targeted_coin_count_workflow = targeted_coin_count_workflow
        self.dank_hof_workflow = dank_hof_workflow
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
        else:
            return None

    def validate_input(self, message, author):
        reply = self.guard.against_self_plusplus(message, author)
        if reply is not None:
            return reply
        else:
            return None
