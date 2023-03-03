import pytest
from ChodeCoin.Backend.utilities.message_reader import MessageReader, is_leaderboard_command, is_targeted_coin_count_command, find_targeted_dank_hof_user, is_dank_hof_command, find_targeted_permission_data, find_chodekill_data


class TestMessageReader:
    def test_GIVEN_is_leaderboard_command_WHEN_string_contains_leaderboard_command_only_THEN_returns_true(self) -> None:
        # Arrange
        message = "!leaderboard"

        # Act
        result = is_leaderboard_command(message)

        # Assert
        assert result is True

    @pytest.mark.parametrize("message", [("!leaderboard "), ("!leaderboard gibberish"), ("!leaderboard two words"), ("!leaderboard !leaderboard"), ("!leaderboardgibberish"), ("!leaderboard!leaderboard")])
    def test_GIVEN_is_leaderboard_command_WHEN_string_contains_leaderboard_command_then_other_text_THEN_returns_true(self, message) -> None:
        # Arrange Act
        result = is_leaderboard_command(message)

        # Assert
        assert result is True

    @pytest.mark.parametrize("message", [(" !leaderboard "), ("gibberish !leaderboard"), ("A!leaderboard"), ("1!leaderboard")])
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

    @pytest.mark.parametrize("message", [("!coincount "), ("!coincount gibberish"), ("!coincount two words"), ("!coincount !coincount"), ("!coincountgibberish"), ("!coincount!coincount")])
    def test_GIVEN_is_targeted_coin_count_command_WHEN_string_contains_coin_count_command_then_other_text_THEN_returns_true(self, message) -> None:
        # Arrange Act
        result = is_targeted_coin_count_command(message)

        # Assert
        assert result is True

    @pytest.mark.parametrize("message", [(" !coincount "), ("gibberish !coincount"), ("A!coincount"), ("1!coincount")])
    def test_GIVEN_is_targeted_coin_count_command_WHEN_string_does_not_start_with_coin_count_command_THEN_returns_false(self, message) -> None:
        # Arrange Act
        result = is_leaderboard_command(message)

        # Assert
        assert result is False

    @pytest.mark.parametrize("message", [("@q++"), ("@abcdefghijklmnopqrstuvwxyzabcdef++")])
    def test_GIVEN_is_chodecoin_ping_WHEN_plus_plus_string_is_lowercase_between_one_and_thirty_two_characters_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    @pytest.mark.parametrize("message", [("@Q++"), ("@AbcdefGhijklmnoPQRstuvwxyzabCDEf++")])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_valid_mixed_case_non_discord_user_plus_plus_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    @pytest.mark.parametrize("message", [("<@500047678378344449>++"), ("<@1019075447532826726>++"), ("<@10190754475328267269>++")])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_valid_discord_user_plus_plus_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    @pytest.mark.parametrize("message", [("<@500047678378344449>++ gibberish"), ("@first++ then @second--")])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_any_valid_user_plus_plus_with_text_after_THEN_returns_true(self, message) -> None:
        # Arrange
        message_reader = MessageReader()

        # Act
        result = message_reader.is_chodecoin_ping(message)

        # Assert
        assert result is True

    @pytest.mark.parametrize("message", [("<@500047678378344449>++ gibberish"), ("@first++ then @second--")])
    def test_GIVEN_is_chodecoin_ping_WHEN_string_is_any_valid_user_plus_plus_with_text_after_THEN_returns_true(self, message) -> None:
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

    @pytest.mark.parametrize("message", [("!dankhof "), ("!dankhof gibberish"), ("!dankhof two words"), ("!dankhof !dankhof"), ("!dankhofgibberish"), ("!dankhof!dankhof")])
    def test_GIVEN_is_dank_hof_command_WHEN_string_contains_dank_hof_command_then_other_text_THEN_returns_true(self, message) -> None:
        # Arrange Act
        result = is_dank_hof_command(message)

        # Assert
        assert result is True

    @pytest.mark.parametrize("message", [(" !dankhof "), ("gibberish !dankhof"), ("A!dankhof"), ("1!dankhof")])
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

    @pytest.mark.parametrize("message, formatted_user", [("!setpermission 500047678378344449 admin", "<@500047678378344449>"), ("!setpermission 1019075447532826726 admin", "<@1019075447532826726>"), ("!setpermission 10190754475328267269 admin", "<@10190754475328267269>")])
    def test_GIVEN_find_targeted_admin_data_WHEN_valid_un_formatted_admin_request_is_provided_THEN_returns_formatted_user(self, message, formatted_user) -> None:
        # Arrange Act
        target_user, new_admin_level = find_targeted_permission_data(message)

        # Assert
        assert target_user.__contains__(formatted_user) is True

    @pytest.mark.parametrize("message, formatted_user", [("!setpermission <@500047678378344449> admin", "<@500047678378344449>"), ("!setpermission <@1019075447532826726> admin", "<@1019075447532826726>"), ("!setpermission <@10190754475328267269> admin", "<@10190754475328267269>")])
    def test_GIVEN_find_targeted_admin_data_WHEN_valid_un_formatted_admin_request_is_provided_THEN_returns_formatted_user(self, message, formatted_user) -> None:
        # Arrange Act
        target_user, new_admin_level = find_targeted_permission_data(message)

        # Assert
        assert target_user.__contains__(formatted_user) is True

    @pytest.mark.parametrize("message, permission", [("!setpermission 500047678378344449 admin", "admin"), ("!setpermission 1019075447532826726 owner", "owner"), ("!setpermission 10190754475328267269 viewer", "viewer"), ("!setpermission 10190754475328267269 none", "none")])
    def test_GIVEN_find_targeted_admin_data_WHEN_valid_admin_request_is_provided_THEN_returns_provided_permission(self, message, permission) -> None:
        # Arrange Act
        target_user, new_admin_level = find_targeted_permission_data(message)

        # Assert
        assert new_admin_level == permission

    @pytest.mark.parametrize("message", [(" !setpermission 500047678378344449 admin"), ("!setpermission 1019075447532826726"), ("!setpermission viewer"), ("!setpermission"), ("!setpermission asdf admin"), ("!setpermission 1019075447532826726 admin owner")])
    def test_GIVEN_find_targeted_admin_data_WHEN_invalid_request_is_provided_THEN_returns_none_for_target_user(self, message) -> None:
        # Arrange Act
        target_user, new_admin_level = find_targeted_permission_data(message)

        # Assert
        assert target_user is None

    @pytest.mark.parametrize("message", [(" !setpermission 500047678378344449 admin"), ("!setpermission 1019075447532826726"), ("!setpermission viewer"), ("!setpermission"), ("!setpermission asdf admin"), ("!setpermission 1019075447532826726 admin owner")])
    def test_GIVEN_find_targeted_admin_data_WHEN_invalid_request_is_provided_THEN_returns_none_for_new_admin_level(self, message) -> None:
        # Arrange Act
        target_user, new_admin_level = find_targeted_permission_data(message)

        # Assert
        assert new_admin_level is None

    def test_GIVEN_find_chodekill_data_WHEN_valid_all_request_is_provided_THEN_returns_all_keyword(self):
        # Arrange
        message = "!chodekill --all"
        expected = "--all"

        # Act
        actual = find_chodekill_data(message)

        # Assert
        assert expected == actual

    def test_GIVEN_find_chodekill_data_WHEN_valid_prune_request_is_provided_THEN_returns_prune_keyword(self):
        # Arrange
        message = "!chodekill --prune"
        expected = "--prune"

        # Act
        actual = find_chodekill_data(message)

        # Assert
        assert expected == actual

    @pytest.mark.parametrize("message, user_name", [("!chodekill Q", "Q"), ("!chodekill <@500047678378344449>", "<@500047678378344449>"), ("!chodekill AbcdefGhijklmnoPQRstuvwxyzabCDEf", "AbcdefGhijklmnoPQRstuvwxyzabCDEf")])
    def test_GIVEN_find_chodekill_data_WHEN_valid_assassination_request_is_provided_THEN_returns_user_name(self, message, user_name):
        # Arrange
        expected = user_name

        # Act
        actual = find_chodekill_data(message)

        # Assert
        assert expected == actual

    @pytest.mark.parametrize("message", [" !chodekill Q", "!chodekill", "!chodekill AbcdsdfsshhjjedefGhijklmnoPQRstuvwxyzabCDEf"])
    def test_GIVEN_find_chodekill_data_WHEN_message_is_not_a_command_THEN_returns_none(self, message):
        # Arrange
        expected = None

        # Act
        actual = find_chodekill_data(message)

        # Assert
        assert expected == actual
        
    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_with_text_after_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>++ additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_with_three_spaces_after_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>   ++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_with_four_spaces_after_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>    ++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_with_space_between_pluses_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>+ +"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_with_17_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@50004767837834444>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_with_21_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449512>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_as_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@<@500047678378344449>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_with_space_in_front_THEN_returns_false(self) -> None:
        # Arrange
        test_message = " <@500047678378344449>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_discord_user_then_another_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>++ <@611158789489455550>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_numbers_that_emulate_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@500047678378344449++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@q++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_with_text_after_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf++ additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_with_three_spaces_after_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf   ++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_with_four_spaces_after_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdf    ++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_with_space_between_pluses_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdf+ +"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_with_33_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdfasdfasdfasdfasdfasdfasdfasdfa++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_with_0_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_with_space_in_front_THEN_returns_false(self) -> None:
        # Arrange
        test_message = " @asdf++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_plus_plus_command_WHEN_provided_custom_user_then_another_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf++ @hjkl++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_with_text_after_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>++ additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_with_three_spaces_after_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>   ++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_with_four_spaces_after_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449>    ++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_with_space_between_pluses_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449>+ +"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_with_17_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@50004767837834444>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_with_21_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449512>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_as_custom_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "@<@500047678378344449>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_with_space_in_front_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = " <@500047678378344449>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_discord_user_then_another_discord_user_THEN_returns_first_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>++ <@611158789489455550>++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_numbers_that_emulate_discord_user_THEN_returns_non_discord_user(self) -> None:
        # Arrange
        expected = "500047678378344449"
        test_message = "@500047678378344449++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_THEN_returns_custom_user(self) -> None:
        # Arrange
        expected = "q"
        test_message = "@q++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_with_text_after_THEN_returns_cusotm_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf++ additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_with_three_spaces_after_user_THEN_returns_custom_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf   ++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_with_four_spaces_after_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdf    ++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_with_space_between_pluses_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdf+ +"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_with_33_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdfasdfasdfasdfasdfasdfasdfasdfa++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_with_0_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_with_space_in_front_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = " @asdf++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_plus_plus_target_WHEN_provided_custom_user_then_another_custom_user_THEN_returns_first_custom_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf++ @hjkl++"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_plus_plus_target(test_message)

        # Assert
        assert actual == expected
        
    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_with_text_after_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>-- additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_with_three_spaces_after_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>   --"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_with_four_spaces_after_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>    --"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_with_space_between_pluses_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>- -"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_with_17_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@50004767837834444>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_with_21_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449512>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_as_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@<@500047678378344449>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_with_space_in_front_THEN_returns_false(self) -> None:
        # Arrange
        test_message = " <@500047678378344449>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_discord_user_then_another_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>-- <@611158789489455550>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_numbers_that_emulate_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@500047678378344449--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@q--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_with_text_after_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf-- additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_with_three_spaces_after_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf   --"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_with_four_spaces_after_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdf    --"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_with_space_between_pluses_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdf- -"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_with_33_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdfasdfasdfasdfasdfasdfasdfasdfa--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_with_0_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_with_space_in_front_THEN_returns_false(self) -> None:
        # Arrange
        test_message = " @asdf--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_minus_minus_command_WHEN_provided_custom_user_then_another_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf-- @hjkl--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_with_text_after_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>-- additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_with_three_spaces_after_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>   --"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_with_four_spaces_after_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449>    --"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_with_space_between_pluses_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449>- -"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_with_17_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@50004767837834444>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_with_21_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449512>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_as_custom_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "@<@500047678378344449>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_with_space_in_front_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = " <@500047678378344449>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_discord_user_then_another_discord_user_THEN_returns_first_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>-- <@611158789489455550>--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_numbers_that_emulate_discord_user_THEN_returns_non_discord_user(self) -> None:
        # Arrange
        expected = "500047678378344449"
        test_message = "@500047678378344449--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_THEN_returns_custom_user(self) -> None:
        # Arrange
        expected = "q"
        test_message = "@q--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_with_text_after_THEN_returns_cusotm_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf-- additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_with_three_spaces_after_user_THEN_returns_custom_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf   --"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_with_four_spaces_after_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdf    --"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_with_space_between_pluses_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdf- -"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_with_33_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdfasdfasdfasdfasdfasdfasdfasdfa--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_with_0_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_with_space_in_front_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = " @asdf--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_minus_minus_target_WHEN_provided_custom_user_then_another_custom_user_THEN_returns_first_custom_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf-- @hjkl--"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_with_text_after_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>\U0001f346\U0001f346 additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_with_three_spaces_after_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>   \U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_with_four_spaces_after_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>    \U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_with_space_between_pluses_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>\U0001f346 \U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_with_17_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@50004767837834444>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_with_21_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449512>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_as_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@<@500047678378344449>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_with_space_in_front_THEN_returns_false(self) -> None:
        # Arrange
        test_message = " <@500047678378344449>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_discord_user_then_another_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>\U0001f346\U0001f346 <@611158789489455550>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_numbers_that_emulate_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@500047678378344449\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@q\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_with_text_after_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf\U0001f346\U0001f346 additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_with_three_spaces_after_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf   \U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_with_four_spaces_after_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdf    \U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_with_space_between_pluses_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf\U0001f346 \U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_with_33_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdfasdfasdfasdfasdfasdfasdfasdfa\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_with_0_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_with_space_in_front_THEN_returns_false(self) -> None:
        # Arrange
        test_message = " @asdf\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_plus_plus_command_WHEN_provided_custom_user_then_another_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf\U0001f346\U0001f346 @hjkl\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_plus_plus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_with_text_after_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>\U0001f346\U0001f346 additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_with_three_spaces_after_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>   \U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_with_four_spaces_after_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449>    \U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_with_space_between_pluses_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>\U0001f346 \U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_with_17_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@50004767837834444>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_with_21_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449512>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_as_custom_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "@<@500047678378344449>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_with_space_in_front_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = " <@500047678378344449>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_discord_user_then_another_discord_user_THEN_returns_first_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>\U0001f346\U0001f346 <@611158789489455550>\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_numbers_that_emulate_discord_user_THEN_returns_non_discord_user(self) -> None:
        # Arrange
        expected = "500047678378344449"
        test_message = "@500047678378344449\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_THEN_returns_custom_user(self) -> None:
        # Arrange
        expected = "q"
        test_message = "@q\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_with_text_after_THEN_returns_cusotm_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf\U0001f346\U0001f346 additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_with_three_spaces_after_user_THEN_returns_custom_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf   \U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_with_four_spaces_after_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdf    \U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_with_space_between_pluses_THEN_returns_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf\U0001f346 \U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_with_33_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdfasdfasdfasdfasdfasdfasdfasdfa\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_with_0_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_with_space_in_front_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = " @asdf\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_plus_plus_target_WHEN_provided_custom_user_then_another_custom_user_THEN_returns_first_custom_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf\U0001f346\U0001f346 @hjkl\U0001f346\U0001f346"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_plus_plus_target(test_message)

        # Assert
        assert actual == expected
        
    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_with_text_after_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449><:No:1058833719399567460><:No:1058833719399567460> additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_with_three_spaces_after_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>   <:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_with_four_spaces_after_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449>    <:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_with_space_between_pluses_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449><:No:1058833719399567460> <:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_with_17_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@50004767837834444><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_with_21_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "<@500047678378344449512><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_as_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@<@500047678378344449><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_with_space_in_front_THEN_returns_false(self) -> None:
        # Arrange
        test_message = " <@500047678378344449><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_discord_user_then_another_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "<@500047678378344449><:No:1058833719399567460><:No:1058833719399567460> <@611158789489455550><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_numbers_that_emulate_discord_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@500047678378344449<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@q<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_with_text_after_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf<:No:1058833719399567460><:No:1058833719399567460> additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_with_three_spaces_after_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf   <:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_with_four_spaces_after_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdf    <:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_with_space_between_pluses_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf<:No:1058833719399567460> <:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_with_33_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@asdfasdfasdfasdfasdfasdfasdfasdfa<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_with_0_digits_THEN_returns_false(self) -> None:
        # Arrange
        test_message = "@<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_with_space_in_front_THEN_returns_false(self) -> None:
        # Arrange
        test_message = " @asdf<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is False

    def test_GIVEN_is_emoji_minus_minus_command_WHEN_provided_custom_user_then_another_custom_user_THEN_returns_true(self) -> None:
        # Arrange
        test_message = "@asdf<:No:1058833719399567460><:No:1058833719399567460> @hjkl<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.is_emoji_minus_minus_command(test_message)

        # Assert
        assert actual is True

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_with_text_after_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449><:No:1058833719399567460><:No:1058833719399567460> additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_with_three_spaces_after_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449>   <:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_with_four_spaces_after_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449>    <:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_with_space_between_pluses_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449><:No:1058833719399567460> <:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_with_17_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@50004767837834444><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_with_21_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "<@500047678378344449512><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_as_custom_user_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "@<@500047678378344449><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_with_space_in_front_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = " <@500047678378344449><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_discord_user_then_another_discord_user_THEN_returns_first_formatted_discord_user(self) -> None:
        # Arrange
        expected = "<@500047678378344449>"
        test_message = "<@500047678378344449><:No:1058833719399567460><:No:1058833719399567460> <@611158789489455550><:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_numbers_that_emulate_discord_user_THEN_returns_non_discord_user(self) -> None:
        # Arrange
        expected = "500047678378344449"
        test_message = "@500047678378344449<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_THEN_returns_custom_user(self) -> None:
        # Arrange
        expected = "q"
        test_message = "@q<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_with_text_after_THEN_returns_cusotm_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf<:No:1058833719399567460><:No:1058833719399567460> additional text afterward"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_with_three_spaces_after_user_THEN_returns_custom_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf   <:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_with_four_spaces_after_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdf    <:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_with_space_between_pluses_THEN_returns_formatted_discord_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf<:No:1058833719399567460> <:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_with_33_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@asdfasdfasdfasdfasdfasdfasdfasdfa<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_with_0_digits_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = "@<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_with_space_in_front_THEN_returns_none(self) -> None:
        # Arrange
        expected = None
        test_message = " @asdf<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected

    def test_GIVEN_extract_emoji_minus_minus_target_WHEN_provided_custom_user_then_another_custom_user_THEN_returns_first_custom_user(self) -> None:
        # Arrange
        expected = "asdf"
        test_message = "@asdf<:No:1058833719399567460><:No:1058833719399567460> @hjkl<:No:1058833719399567460><:No:1058833719399567460>"
        message_reader = MessageReader()

        # Act
        actual = message_reader.extract_emoji_minus_minus_target(test_message)

        # Assert
        assert actual == expected
