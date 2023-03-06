import pytest
from mock import Mock

from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.workflows.chodecoin_ping_workflow import ChodeCoinPingWorkflow, get_chodecoin_ping_description


class TestChodeCoinPingWorkflow:
    def test_GIVEN_is_chodecoin_ping_WHEN_request_is_chodecoin_ping_request_THEN_returns_true(self) -> None:
        # Arrange
        mock_messagereader = Mock()
        mock_messagereader.is_chodecoin_ping.return_value = True
        mock_coinmanager = Mock()
        mock_replygenerator = Mock()
        mock_guard = Mock()

        chodecoin_ping_workflow = ChodeCoinPingWorkflow(mock_messagereader, mock_coinmanager, mock_replygenerator, mock_guard)

        # Act
        actual = chodecoin_ping_workflow.is_chodecoin_ping("should_return_true")

        # Assert
        assert actual is True

    def test_GIVEN_is_chodecoin_ping_WHEN_request_is_not_chodecoin_ping_request_THEN_returns_false(self) -> None:
        # Arrange
        mock_messagereader = Mock()
        mock_messagereader.is_chodecoin_ping.return_value = False
        mock_coinmanager = Mock()
        mock_replygenerator = Mock()
        mock_guard = Mock()

        chodecoin_ping_workflow = ChodeCoinPingWorkflow(mock_messagereader, mock_coinmanager, mock_replygenerator, mock_guard)

        # Act
        actual = chodecoin_ping_workflow.is_chodecoin_ping("should_return_false")

        # Assert
        assert actual is False

    def test_GIVEN_get_chodecoin_ping_description_WHEN_called_THEN_returns_command_object(self) -> None:
        # Arrange Act
        actual = get_chodecoin_ping_description()

        # Assert
        assert type(actual) is Command
