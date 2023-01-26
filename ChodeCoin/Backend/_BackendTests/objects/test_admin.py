from ChodeCoin.Backend.enums.permission_level import PermissionLevel
from ChodeCoin.Backend.objects.admin import Admin, new_admin


class TestAdmin:
    def test_GIVEN_admin_WHEN_created_with_no_date_added_THEN_prepopulates_date_added_to_empty(self) -> None:
        # Arrange
        expected = ""

        # Act
        result = Admin("Test", PermissionLevel.admin)

        # Assert
        assert result.date_added == expected

    def test_GIVEN_admin_WHEN_new_admin_called_THEN_sets_provided_name(self) -> None:
        # Arrange
        expected = "Test"

        # Act
        result = new_admin("Test", PermissionLevel.admin)

        # Assert
        assert result.name == expected

    def test_GIVEN_admin_WHEN_new_admin_called_THEN_sets_provided_permission_level(self) -> None:
        # Arrange
        expected = PermissionLevel.admin

        # Act
        result = new_admin("Test", PermissionLevel.admin)

        # Assert
        assert result.permission_level == expected
