from ChodeCoin.utilities.guard import Guard
from ChodeCoin.workflows.chodecoin_ping_workflow import ChodeCoinPingWorkflow
from ChodeCoin.workflows.leaderboard_workflow import LeaderboardWorkflow, is_leaderboard_workflow
from ChodeCoin.workflows.targeted_coin_count_workflow import TargetedCoinCountWorkflow, is_targeted_coin_count_request
from ChodeCoin.enums.request_for import RequestFor


class WorkFlow:
    def __init__(
            self,
            chodecoin_ping_workflow=ChodeCoinPingWorkflow(),
            leaderboard_workflow=LeaderboardWorkflow(),
            targeted_coin_count_workflow=TargetedCoinCountWorkflow(),
            guard=Guard()):
        self.chodecoin_ping_workflow = chodecoin_ping_workflow
        self.leaderboard_workflow = leaderboard_workflow
        self.targeted_coin_count_workflow = targeted_coin_count_workflow
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
            return self.targeted_coin_count_workflow.process_targeted_coin_count_request(message)

        else:
            return None, None

    def identify_request(self, message):
        if self.chodecoin_ping_workflow.is_chodecoin_ping(message):
            return RequestFor.chodecoin_ping
        elif is_leaderboard_workflow(message):
            return RequestFor.leaderboard
        elif is_targeted_coin_count_request(message):
            return RequestFor.targeted_coin_count
        else:
            return None



    def validate_input(self, message, author):
        reply = self.guard.against_self_plusplus(message, author)
        if reply is not None:
            return reply
        else:
            return None
