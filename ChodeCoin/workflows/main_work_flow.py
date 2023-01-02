from ChodeCoin.utilities.guard import Guard
from ChodeCoin.workflows.chodecoin_ping_workflow import ChodeCoinPingWorkflow


class WorkFlow:
    def __init__(self, chodecoin_ping_workflow=ChodeCoinPingWorkflow(), guard=Guard()):
        self.chodecoin_ping_workflow = chodecoin_ping_workflow
        self.guard = guard

    def process_message(self, message, author):
        process = self.identify_request(message)

        if process == "chodecoin_ping":
            reply = self.validate_input(message, author)
            if reply is None:
                reply = self.chodecoin_ping_workflow.process_chodecoin_ping(message)
            return reply
        else:
            return None

    def identify_request(self, message):
        is_chodecoin_ping = self.chodecoin_ping_workflow.is_chodecoin_ping(message)
        if is_chodecoin_ping:
            return "chodecoin_ping"
        else:
            return None

    def validate_input(self, message, author):
        reply = self.guard.against_self_plusplus(message, author)
        if reply is not None:
            return reply
        else:
            return None
