import unittest
from mock import Mock
from ChodeCoin.ChodeCoinBackend.utilities.coin_manager import CoinManager


class TestCoinManager(unittest.TestCase):
    def test_Given_process_plus_plus_When_target_user_exists_Then_calls_change_coin_count_with_value_of_one(self) -> None:
        target_user = "UserThatExists"
        mock_usermanager = Mock()
        mock_usermanager.user_exists.return_value = True
        mock_coinbankportal = Mock()
        coin_manager = CoinManager(mock_usermanager, mock_coinbankportal)

        coin_manager.process_plus_plus(target_user)

        self.assertTrue(mock_coinbankportal.mockSetExpecation("change_coin_count", mock_coinbankportal.change_coin_count, 0, 2))
        self.assertTrue(mock_usermanager.mockSetExpectation("create_new_user", mock_usermanager.create_new_user, 0, 0))
