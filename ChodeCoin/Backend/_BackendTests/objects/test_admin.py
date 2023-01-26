from ChodeCoin.Backend.enums.permission_level import PermissionLevel
from ChodeCoin.Backend.objects.admin import Admin, new_admin, convert_admin_to_json


class TestAdmin:
    def test_GIVEN_admin_WHEN_created_with_no_date_added_THEN_prepopulates_date_added_to_empty(self) -> None:
        # Arrange
        expected = ""

        # Act
        result = Admin("Test", PermissionLevel.admin)

        # Assert
        assert result.date_added == expected

    def test_GIVEN_new_admin_WHEN_new_admin_called_THEN_sets_provided_name(self) -> None:
        # Arrange
        expected = "Test"

        # Act
        result = new_admin("Test", PermissionLevel.admin)

        # Assert
        assert result.name == expected

    def test_GIVEN_new_admin_WHEN_new_admin_called_THEN_sets_provided_permission_level(self) -> None:
        # Arrange
        expected = PermissionLevel.admin

        # Act
        result = new_admin("Test", PermissionLevel.admin)

        # Assert
        assert result.permission_level == expected

    def test_GIVEN_admin_WHEN_asserting_equal_on_equal_admins_THEN_returns_true(self) -> None:
        # Arrange
        admin1 = Admin("Test", PermissionLevel.admin)
        admin2 = Admin("Test", PermissionLevel.admin)

        # Act
        result = admin1 == admin2

        # Assert
        assert result is True

    def test_GIVEN_admin_WHEN_asserting_equal_on_equal_admins_with_different_dates_THEN_returns_true(self) -> None:
        # Arrange
        admin1 = Admin("Test", PermissionLevel.admin, "2022-07-18 02:02:03")
        admin2 = Admin("Test", PermissionLevel.admin, "2021-07-18 02:02:03")

        # Act
        result = admin1 == admin2

        # Assert
        assert result is True

    def test_GIVEN_admin_WHEN_asserting_equal_on_admins_with_different_names_THEN_returns_false(self) -> None:
        # Arrange
        admin1 = Admin("Test1", PermissionLevel.admin)
        admin2 = Admin("Test2", PermissionLevel.admin)

        # Act
        result = admin1 == admin2

        # Assert
        assert result is False

    def test_GIVEN_admin_WHEN_asserting_equal_on_admins_with_different_permission_levels_THEN_returns_false(self) -> None:
        # Arrange
        admin1 = Admin("Test", PermissionLevel.admin)
        admin2 = Admin("Test", PermissionLevel.none)

        # Act
        result = admin1 == admin2

        # Assert
        assert result is False

    def test_GIVEN_admin_WHEN_asserting_equal_on_non_admin_object_THEN_returns_NotImplemented(self) -> None:
        # Arrange
        admin1 = Admin("Test", PermissionLevel.admin)
        admin2 = "Admin(\"Test\", PermissionLevel.admin)"

        # Act
        result = admin1 == admin2

        # Assert
        assert result is False

    def test_GIVEN_convert_admin_to_json_WHEN_provided_admin_THEN_returns_correct_json_object(self) -> None:
        # Arrange
        test_admin = Admin("Test", PermissionLevel.admin, "2022-07-18 02:02:03")
        expected = {"name": "Test", "permission_level": PermissionLevel.admin, "date_added": "2022-07-18 02:02:03"}

        # Act
        actual = convert_admin_to_json(test_admin)

        # Assert
        assert expected == actual
