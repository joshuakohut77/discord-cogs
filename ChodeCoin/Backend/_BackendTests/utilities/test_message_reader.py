import unittest
from mock import Mock
from parameterized import parameterized
from ChodeCoin.Backend.utilities.message_reader import MessageReader, is_leaderboard_command, is_targeted_coin_count_command


class TestMessageReader(unittest.TestCase):
    def test_GIVEN_is_leaderboard_command_WHEN_string_contains_leaderboard_command_only_THEN_returns_true(self) -> None:
        # Arrange
        message = "!leaderboard"

        # Act
        result = is_leaderboard_command(message)

        # Assert
        self.assertTrue(result)

    @parameterized.expand([("!leaderboard ",), ("!leaderboard gibberish",), ("!leaderboard two words",), ("!leaderboard !leaderboard",), ("!leaderboardgibberish",), ("!leaderboard!leaderboard",), ])
    def test_GIVEN_is_leaderboard_command_WHEN_string_contains_leaderboard_command_then_other_text_THEN_returns_true(self, message) -> None:
        # Arrange Act
        result = is_leaderboard_command(message)

        # Assert
        self.assertTrue(result)

    @parameterized.expand([(" !leaderboard ",), ("gibberish !leaderboard",), ("A!leaderboard",), ("1!leaderboard",), ])
    def test_GIVEN_is_leaderboard_command_WHEN_string_does_not_start_with_leaderboard_command_THEN_returns_false(self, message) -> None:
        # Arrange Act
        result = is_leaderboard_command(message)

        # Assert
        self.assertFalse(result)

    def test_GIVEN_is_targeted_coin_count_command_WHEN_string_contains_coin_count_command_only_THEN_returns_true(self) -> None:
        # Arrange
        message = "!coincount"

        # Act
        result = is_targeted_coin_count_command(message)

        # Assert
        self.assertTrue(result)

    @parameterized.expand([("!coincount ",), ("!coincount gibberish",), ("!coincount two words",), ("!coincount !coincount",), ("!coincountgibberish",), ("!coincount!coincount",), ])
    def test_GIVEN_is_targeted_coin_count_command_WHEN_string_contains_coin_count_command_then_other_text_THEN_returns_true(self, message) -> None:
        # Arrange Act
        result = is_targeted_coin_count_command(message)

        # Assert
        self.assertTrue(result)

    @parameterized.expand([(" !coincount ",), ("gibberish !coincount",), ("A!coincount",), ("1!coincount",), ])
    def test_GIVEN_is_targeted_coin_count_command_WHEN_string_does_not_start_with_coin_count_command_THEN_returns_false(self, message) -> None:
        # Arrange Act
        result = is_leaderboard_command(message)

        # Assert
        self.assertFalse(result)

    @parameterized.expand([("@aq++",), ("@abcdefghijklmnopqrstuvwxyzabcdef++",), ])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_valid_lowercase_non_discord_user_plus_plus_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        self.assertTrue(result)

    @parameterized.expand([("@aQ++",), ("@AbcdefGhijklmnoPQRstuvwxyzabCDEf++",), ])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_valid_mixed_case_non_discord_user_plus_plus_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        self.assertTrue(result)
