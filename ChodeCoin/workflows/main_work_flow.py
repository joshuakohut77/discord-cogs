from ChodeCoin.utilities.guard import Guard
from ChodeCoin.workflows.chodecoin_ping_workflow import ChodeCoinPingWorkflow
from ChodeCoin.workflows.leaderboard_workflow import LeaderboardWorkflow, is_leaderboard_workflow


class WorkFlow:
    def __init__(
            self,
            chodecoin_ping_workflow=ChodeCoinPingWorkflow(),
            leaderboard_workflow=LeaderboardWorkflow(),
            guard=Guard()):
        self.chodecoin_ping_workflow = chodecoin_ping_workflow
        self.leaderboard_workflow = leaderboard_workflow
        self.guard = guard

    def process_message(self, message, author):
        process = self.identify_request(message)

        if process == "chodecoin_ping_workflow":
            reply = self.validate_input(message, author)
            if reply is None:
                reply = self.chodecoin_ping_workflow.process_chodecoin_ping(message)
            return reply, None
        elif process == "leaderboard_workflow":
            return self.leaderboard_workflow.process_leaderboard_request()
        else:
            return None, None

    def identify_request(self, message):
        if self.chodecoin_ping_workflow.is_chodecoin_ping(message):
            return "chodecoin_ping_workflow"
        elif is_leaderboard_workflow(message):
            return "leaderboard_workflow"
        else:
            return None



    def validate_input(self, message, author):
        reply = self.guard.against_self_plusplus(message, author)
        if reply is not None:
            return reply
        else:
            return None
