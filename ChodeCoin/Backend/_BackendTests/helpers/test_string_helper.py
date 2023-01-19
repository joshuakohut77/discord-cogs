import pytest
from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user


class TestStringHelper:
    def test_GIVEN_convert_to_discord_user_WHEN_provided_un_formatted_user_THEN_returns_formatted_discord_user(self) -> None:
        user = "500047678378344449"
        expected = "<@500047678378344449>"
        actual = convert_to_discord_user(user)
        assert expected == actual

    def test_GIVEN_convert_to_discord_user_WHEN_provided_formatted_user_THEN_returns_formatted_discord_user(self) -> None:
        user = "<@500047678378344449>"
        expected = "<@500047678378344449>"
        actual = convert_to_discord_user(user)
        assert expected == actual
