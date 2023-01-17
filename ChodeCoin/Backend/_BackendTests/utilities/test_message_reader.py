from mock import Mock
import pytest
from parameterized import parameterized
from ChodeCoin.Backend.utilities.message_reader import MessageReader, is_leaderboard_command, \
    is_targeted_coin_count_command, find_targeted_dank_hof_user, is_dank_hof_command


class TestMessageReader:
    def test_GIVEN_is_leaderboard_command_WHEN_string_contains_leaderboard_command_only_THEN_returns_true(self) -> None:
        # Arrange
        message = "!leaderboard"

        # Act
        result = is_leaderboard_command(message)

        # Assert
        assert result is True

    @parameterized.expand([("!leaderboard ",), ("!leaderboard gibberish",), ("!leaderboard two words",), ("!leaderboard !leaderboard",), ("!leaderboardgibberish",), ("!leaderboard!leaderboard",), ])
    def test_GIVEN_is_leaderboard_command_WHEN_string_contains_leaderboard_command_then_other_text_THEN_returns_true(self, message) -> None:
        # Arrange Act
        result = is_leaderboard_command(message)

        # Assert
        assert result is True

    @parameterized.expand([(" !leaderboard ",), ("gibberish !leaderboard",), ("A!leaderboard",), ("1!leaderboard",), ])
    def test_GIVEN_is_leaderboard_command_WHEN_string_does_not_start_with_leaderboard_command_THEN_returns_false(self, message) -> None:
        # Arrange Act
        result = is_leaderboard_command(message)

        # Assert
        assert result is False

    def test_GIVEN_is_targeted_coin_count_command_WHEN_string_contains_coin_count_command_only_THEN_returns_true(self) -> None:
        # Arrange
        message = "!coincount"

        # Act
        result = is_targeted_coin_count_command(message)

        # Assert
        assert result is True

    @parameterized.expand([("!coincount ",), ("!coincount gibberish",), ("!coincount two words",), ("!coincount !coincount",), ("!coincountgibberish",), ("!coincount!coincount",), ])
    def test_GIVEN_is_targeted_coin_count_command_WHEN_string_contains_coin_count_command_then_other_text_THEN_returns_true(self, message) -> None:
        # Arrange Act
        result = is_targeted_coin_count_command(message)

        # Assert
        assert result is True

    @parameterized.expand([(" !coincount ",), ("gibberish !coincount",), ("A!coincount",), ("1!coincount",), ])
    def test_GIVEN_is_targeted_coin_count_command_WHEN_string_does_not_start_with_coin_count_command_THEN_returns_false(self, message) -> None:
        # Arrange Act
        result = is_leaderboard_command(message)

        # Assert
        assert result is False

    @parameterized.expand([("@q++",), ("@abcdefghijklmnopqrstuvwxyzabcdef++",), ])
    def test_GIVEN_is_chodecoin_ping_WHEN_plus_plus_string_is_lowercase_between_one_and_thirty_two_characters_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    @parameterized.expand([("@Q++",), ("@AbcdefGhijklmnoPQRstuvwxyzabCDEf++",), ])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_valid_mixed_case_non_discord_user_plus_plus_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    @parameterized.expand([("@<500047678378344449>++",), ("@<1019075447532826726>++",), ("@<10190754475328267269>++",), ])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_valid_discord_user_plus_plus_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    @parameterized.expand([("@<500047678378344449>++ gibberish",), ("@first++ then @second--",), ])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_any_valid_user_plus_plus_with_text_after_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    @parameterized.expand([("@<500047678378344449>++ gibberish",), ("@first++ then @second--",), ])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_any_valid_user_plus_plus_with_text_after_THEN_returns_true(self,
                                                                                                               message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    def test_GIVEN_is_chodecoin_ping_WHEN_plus_plus_user_has_fewer_than_one_character_THEN_returns_false(self) -> None:
        # Arrange
        message = "@++"
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is False

    def test_GIVEN_is_chodecoin_ping_WHEN_plus_plus_user_has_more_than_thirty_two_characters_THEN_returns_false(self) -> None:
        # Arrange
        message = "@abcdefghijklmnopqrstuvwxyzabcdefg++"
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is False

    def test_GIVEN_is_dank_hof_command_WHEN_string_contains_dank_hof_command_only_THEN_returns_true(self) -> None:
        # Arrange
        message = "!dankhof"

        # Act
        result = is_dank_hof_command(message)

        # Assert
        assert result is True

    @parameterized.expand([("!dankhof ",), ("!dankhof gibberish",), ("!dankhof two words",), ("!dankhof !dankhof",), ("!dankhofgibberish",), ("!dankhof!dankhof",), ])
    def test_GIVEN_is_dank_hof_command_WHEN_string_contains_dank_hof_command_then_other_text_THEN_returns_true(self, message) -> None:
        # Arrange Act
        result = is_dank_hof_command(message)

        # Assert
        assert result is True

    @parameterized.expand([(" !dankhof ",), ("gibberish !dankhof",), ("A!dankhof",), ("1!dankhof",), ])
    def test_GIVEN_is_dank_hof_command_WHEN_string_does_not_start_with_dank_hof_command_THEN_returns_false(self, message) -> None:
        # Arrange Act
        result = is_dank_hof_command(message)

        # Assert
        assert result is False

    def test_GIVEN_find_targeted_dank_hof_user_WHEN_user_is_not_provided_THEN_returns_none(self) -> None:
        # Arrange
        message = "!dankhof"
        expected = None

        # Act
        actual = find_targeted_dank_hof_user(message)

        # Assert
        assert expected == actual

    @pytest.mark.parametrize("message, user", [("!dankhof q", "q"), ("!dankhof abcdefghijklmnopqrstuvwxyzabcdef", "abcdefghijklmnopqrstuvwxyzabcdef")])
    def test_GIVEN_find_targeted_dank_hof_user_WHEN_valid_user_is_provided_THEN_returns_user(self, message, user) -> None:
        # Arrange
        expected = user

        # Act
        actual = find_targeted_dank_hof_user(message)

        # Assert
        assert expected == actual

    @pytest.mark.parametrize("message, user", [("!dankhof 500047678378344449", "<@500047678378344449>"), ("!dankhof 1019075447532826726", "<@1019075447532826726>"), ("!dankhof 10190754475328267269", "<@10190754475328267269>")])
    def test_GIVEN_find_targeted_dank_hof_user_WHEN_valid_discord_user_is_provided_THEN_returns_formatted_user(self, message, user) -> None:
        # Arrange
        expected = user

        # Act
        actual = find_targeted_dank_hof_user(message)

        # Assert
        assert expected == actual

    def test_GIVEN_find_targeted_dank_hof_user_WHEN_invalid_string_is_provided_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        message = "!dankhof"

        # Act
        actual = find_targeted_dank_hof_user(message)

        # Assert
        assert expected == actual
