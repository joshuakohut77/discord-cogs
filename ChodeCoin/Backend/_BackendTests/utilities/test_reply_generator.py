import pytest
from ChodeCoin.Backend.utilities.reply_generator import generate_dank_hof_reply


class TestReplyGenerator:
    def test_GIVEN_generate_dank_hof_reply_WHEN_given_target_user_THEN_includes_name_in_return_message(self) -> None:
        # Arrange
        target_user = "Target User"

        # Act
        result = generate_dank_hof_reply(target_user)

        # Assert
        assert result.__contains__(target_user)
