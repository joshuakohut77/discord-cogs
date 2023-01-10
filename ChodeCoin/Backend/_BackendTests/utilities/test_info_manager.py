import unittest

import mock
from mock import Mock
from parameterized import parameterized, param
from ChodeCoin.Backend.utilities.info_manager import InfoManager


def generate_mock_db_result():
    return [{"name": "Mock Name", "coin_count": 143, "last_modified": "2023-01-10 02:01:22.608934"}]


class TestInfoManager(unittest.TestCase):

    def test_GIVEN_get_current_balance_WHEN_user_does_not_exist_THEN_does_not_make_db_call(self) -> None:
        # Arrange
        target_user = "UserThatDoesNotExist"
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = False
        mock_coinbankportal = Mock()
        mock_arrayhelper = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal, mock_arrayhelper)

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
        mock_arrayhelper = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal, mock_arrayhelper)
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
        mock_arrayhelper = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal, mock_arrayhelper)

        # Act
        info_manager.get_current_balance(target_user)

        # Assert
        mock_coinbankportal.get_current_balance.assert_called_once_with(target_user)

    @parameterized.expand([(-1,), (-15,), (-109,), (-1337,), ])
    def test_GIVEN_get_wealthiest_users_WHEN_count_is_negative_THEN_raises_value_error(self, count) -> None:
        # Arrange
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = True
        mock_coinbankportal = Mock()
        mock_arrayhelper = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal, mock_arrayhelper)

        # Act Assert
        self.assertRaises(ValueError, info_manager.get_wealthiest_users, count)

    def test_GIVEN_get_wealthiest_users_WHEN_count_is_zero_THEN_raises_value_error(self) -> None:
        # Arrange
        count = 0
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = True
        mock_coinbankportal = Mock()
        mock_arrayhelper = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal, mock_arrayhelper)

        # Act Assert
        self.assertRaises(ValueError, info_manager.get_wealthiest_users, count)

    @parameterized.expand([(1,), (15,), (109,), (1337,), ])
    def test_GIVEN_get_wealthiest_users_WHEN_count_is_positive_THEN_calls_add_if_in_wealthiest_group_with_count(self, count) -> None:
        # Arrange
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = True
        mock_coinbankportal = Mock()
        mock_coinbankportal.get_all_users.return_value = generate_mock_db_result()
        mock_arrayhelper = Mock()
        info_manager = InfoManager(mock_usermanager, mock_coinbankportal, mock_arrayhelper)

        # Act
        info_manager.get_wealthiest_users(count)

        # Assert
        mock_arrayhelper.add_if_in_wealthiest_group.assert_called_once_with(mock.ANY, mock.ANY, count)
