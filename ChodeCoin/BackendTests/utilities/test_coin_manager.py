import unittest
from mock import Mock
from ChodeCoin.Backend.utilities.coin_manager import CoinManager


class TestCoinManager(unittest.TestCase):
    def test_GIVEN_process_plus_plus_WHEN_target_user_exists_THEN_calls_change_coin_count_with_value_of_one(self) -> None:
        # Arrange
        target_user = "UserThatExists"
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = True
        mock_coinbankportal = Mock()
        coin_manager = CoinManager(mock_usermanager, mock_coinbankportal)

        # Act
        coin_manager.process_plus_plus(target_user)

        # Assert
        mock_coinbankportal.change_coin_count.assert_called_once_with(target_user, 1)

    def test_GIVEN_process_plus_plus_WHEN_target_user_exists_THEN_does_not_create_new_user(
            self) -> None:
        # Arrange
        target_user = "UserThatExists"
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = True
        mock_coinbankportal = Mock()
        coin_manager = CoinManager(mock_usermanager, mock_coinbankportal)

        # Act
        coin_manager.process_plus_plus(target_user)

        # Assert
        mock_usermanager.create_new_user.assert_not_called()

    def test_GIVEN_process_plus_plus_WHEN_target_user_does_not_exist_THEN_calls_create_new_user(self) -> None:
        # Arrange
        target_user = "UserThatDoesntExist"
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = False
        mock_coinbankportal = Mock()
        coin_manager = CoinManager(mock_usermanager, mock_coinbankportal)

        # Act
        coin_manager.process_plus_plus(target_user)

        # Assert
        mock_usermanager.create_new_user.assert_called_once()
