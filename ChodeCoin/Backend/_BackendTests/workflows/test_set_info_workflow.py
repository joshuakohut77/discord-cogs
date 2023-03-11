import pytest
from mock import Mock

from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.workflows.chodecoin_ping_workflow import ChodeCoinPingWorkflow, get_chodecoin_ping_description


class TestChodeCoinPingWorkflow:
    def GIVEN_process_set_info_request_WHEN_author_is_not_an_admin_THEN_returns_no_permission_reply(self) -> None:
        return None
