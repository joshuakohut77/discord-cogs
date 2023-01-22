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
