import pytest
from mock import Mock
from ChodeCoin.Backend.utilities.user_manager import UserManager


class TestUserManager:
    @pytest.mark.parametrize("permission_level", [("1"), ("2")])
    def test_GIVEN_is_admin_user_WHEN_user_is_admin_THEN_returns_true(self, permission_level) -> None:
        # Arrange
        target_user = "AdminUser"
        mock_coinbankportal = Mock()
        mock_adminrecordportal = Mock()
        mock_adminrecordportal.get_admin_permission.return_value = permission_level
        user_manager = UserManager(mock_coinbankportal, mock_adminrecordportal)

        # Act
        result = user_manager.is_admin_user(target_user)

        # Assert
        assert result is True

    @pytest.mark.parametrize("permission_level", [("3"), ("4"), ("5")])
    def test_GIVEN_is_admin_user_WHEN_user_is_not_admin_THEN_returns_false(self, permission_level) -> None:
        # Arrange
        target_user = "NonAdminUser"
        mock_coinbankportal = Mock()
        mock_adminrecordportal = Mock()
        mock_adminrecordportal.get_admin_permission.return_value = permission_level
        user_manager = UserManager(mock_coinbankportal, mock_adminrecordportal)

        # Act
        result = user_manager.is_admin_user(target_user)

        # Assert
        assert result is False

    def test_GIVEN_set_coin_count_WHEN_user_exists_THEN_updates_coin_count_with_provided_value(self) -> None:
        # Arrange
        new_value = 12
        target_user = "UserThatExists"
        mock_coinbankportal = Mock()
        mock_coinbankportal.user_exists.return_value = True
        mock_adminrecordportal = Mock()
        user_manager = UserManager(mock_coinbankportal, mock_adminrecordportal)

        # Act
        user_manager.set_coin_count(target_user, new_value)

        # Assert
        mock_coinbankportal.set_coin_count.assert_called_once_with(target_user, new_value)

    def test_GIVEN_set_coin_count_WHEN_user_exists_THEN_does_not_create_new_user(self) -> None:
        # Arrange
        new_value = 12
        target_user = "UserThatExists"
        mock_coinbankportal = Mock()
        mock_coinbankportal.user_exists.return_value = True
        mock_adminrecordportal = Mock()
        user_manager = UserManager(mock_coinbankportal, mock_adminrecordportal)

        # Act
        user_manager.set_coin_count(target_user, new_value)

        # Assert
        mock_coinbankportal.create_new_user.assert_not_called()

    def test_GIVEN_set_coin_count_WHEN_user_does_not_exist_THEN_updates_coin_count_with_provided_value(self) -> None:
        # Arrange
        new_value = 12
        target_user = "UserThatExists"
        mock_coinbankportal = Mock()
        mock_coinbankportal.user_exists.return_value = False
        mock_adminrecordportal = Mock()
        user_manager = UserManager(mock_coinbankportal, mock_adminrecordportal)

        # Act
        user_manager.set_coin_count(target_user, new_value)

        # Assert
        mock_coinbankportal.set_coin_count.assert_called_once_with(target_user, new_value)

    def test_GIVEN_set_coin_count_WHEN_user_does_not_exist_THEN_creates_a_new_user(self) -> None:
        # Arrange
        new_value = 12
        target_user = "UserThatExists"
        mock_coinbankportal = Mock()
        mock_coinbankportal.user_exists.return_value = False
        mock_adminrecordportal = Mock()
        user_manager = UserManager(mock_coinbankportal, mock_adminrecordportal)

        # Act
        user_manager.set_coin_count(target_user, new_value)

        # Assert
        mock_coinbankportal.create_new_user.assert_called_once_with(target_user)
