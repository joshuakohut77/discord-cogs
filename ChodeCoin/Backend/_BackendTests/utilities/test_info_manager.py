import unittest
from mock import Mock
from ChodeCoin.Backend.utilities.info_manager import InfoManager


class TestInfoManager(unittest.TestCase):

    def test_GIVEN_get_current_balance_WHEN_user_does_not_exist_THEN_does_not_make_db_call(self) -> None:
        # Arrange
        target_user = "UserThatDoesNotExist"
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = False
        mock_coinbankportal = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal)

        # Act
        info_manager.get_current_balance(target_user)

        # Assert
        mock_coinbankportal.get_current_balance.assert_not_called()

    def test_GIVEN_get_current_balance_WHEN_user_does_not_exist_THEN_returns_none(self) -> None:
        # Arrange
        target_user = "UserThatDoesNotExist"
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = False
        mock_coinbankportal = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal)
        expected_result = None

        # Act
        actual_result = info_manager.get_current_balance(target_user)

        # Assert
        self.assertEqual(expected_result, actual_result)

    def test_GIVEN_get_current_balance_WHEN_user_exists_THEN_makes_db_call_with_user(self) -> None:
        # Arrange
        target_user = "UserThatExists"
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = True
        mock_coinbankportal = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal)

        # Act
        info_manager.get_current_balance(target_user)

        # Assert
        mock_coinbankportal.get_current_balance.assert_called_once_with(target_user)
