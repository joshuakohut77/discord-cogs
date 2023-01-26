import pytest
from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user


class TestStringHelper:
    def test_GIVEN_convert_to_discord_user_WHEN_provided_un_formatted_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        user = "500047678378344449"
        expected = "<@500047678378344449>"

        # Act
        actual = convert_to_discord_user(user)

        # Assert
        assert expected == actual

    def test_GIVEN_convert_to_discord_user_WHEN_provided_formatted_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        user = "<@500047678378344449>"
        expected = "<@500047678378344449>"

        # Act
        actual = convert_to_discord_user(user)

        # Assert
        assert expected == actual

    def test_GIVEN_convert_to_discord_user_WHEN_provided_un_formatted_user_as_int_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        user = 500047678378344449
        expected = "<@500047678378344449>"

        # Act
        actual = convert_to_discord_user(user)

        # Assert
        assert expected == actual

    def test_GIVEN_convert_to_discord_user_WHEN_provided_non_discord_user_THEN_returns_unchanged_user_name(self) -> None:
        # Arrange
        user = "Non Discord Username"
        expected = user

        # Act
        actual = convert_to_discord_user(user)

        # Assert
        assert expected == actual
