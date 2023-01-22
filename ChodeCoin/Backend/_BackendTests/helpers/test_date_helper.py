import pytest
from mock import Mock

from ChodeCoin.Backend.helpers.date_helper import DateHelper


class TestDateHelper:
    @pytest.mark.parametrize("date_string", [("2023-01-17 02:02:03"), ("2022-07-19 02:02:04"), ("2022-07-19 02:02:04")])
    def test_GIVEN_is_older_than_six_months_WHEN_date_is_less_than_six_months_ago_THEN_returns_false(self, date_string) -> None:
        # Arrange
        mock_timestamp_helper = Mock()
        mock_timestamp_helper.current_timestamp_string.return_value = "2023-01-17 02:02:04"
        date_helper = DateHelper(mock_timestamp_helper)

        # Act
        actual = date_helper.is_older_than_six_months(date_string)

        # Assert
        assert actual is False

    def test_GIVEN_is_older_than_six_months_WHEN_date_is_exactly_six_months_ago_THEN_returns_true(self) -> None:
        # Arrange
        date_string = "2022-07-18 02:02:04"
        mock_timestamp_helper = Mock()
        mock_timestamp_helper.current_timestamp_string.return_value = "2023-01-17 02:02:04"
        date_helper = DateHelper(mock_timestamp_helper)

        # Act
        actual = date_helper.is_older_than_six_months(date_string)

        # Assert
        assert actual is True

    @pytest.mark.parametrize("date_string", [("2021-01-17 02:02:05"), ("2022-07-18 02:02:03")])
    def test_GIVEN_is_older_than_six_months_WHEN_date_is_more_than_six_months_ago_THEN_returns_true(self, date_string) -> None:
        # Arrange
        mock_timestamp_helper = Mock()
        mock_timestamp_helper.current_timestamp_string.return_value = "2023-01-17 02:02:04"
        date_helper = DateHelper(mock_timestamp_helper)

        # Act
        actual = date_helper.is_older_than_six_months(date_string)

        # Assert
        assert actual is True
