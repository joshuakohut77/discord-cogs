from ChodeCoin.Backend.objects.user import User, new_user, convert_user_to_json


class TestUser:
    def test_GIVEN_new_user_WHEN_new_user_called_THEN_sets_provided_name(self) -> None:
        # Arrange
        expected = "Name"

        # Act
        result = new_user("Name", 14)

        # Assert
        assert result.name == expected

    def test_GIVEN_new_user_WHEN_new_user_called_THEN_sets_provided_coin_count(self) -> None:
        # Arrange
        expected = 14

        # Act
        result = new_user("Name", 14)

        # Assert
        assert result.coin_count == expected

    def test_GIVEN_user_WHEN_asserting_equal_on_equal_users_THEN_returns_true(self) -> None:
        # Arrange
        user1 = User("Name", 14)
        user2 = User("Name", 14)

        # Act
        result = user1 == user2

        # Assert
        assert result is True

    def test_GIVEN_user_WHEN_asserting_equal_on_users_with_different_names_THEN_returns_false(self) -> None:
        # Arrange
        user1 = User("Name1", 14)
        user2 = User("Name2", 14)

        # Act
        result = user1 == user2

        # Assert
        assert result is False

    def test_GIVEN_user_WHEN_asserting_equal_on_users_with_different_descriptions_THEN_returns_false(self) -> None:
        # Arrange
        user1 = User("Name", "Description1")
        user2 = User("Name", "Description2")

        # Act
        result = user1 == user2

        # Assert
        assert result is False

    def test_GIVEN_user_WHEN_asserting_equal_on_non_user_object_THEN_returns_NotImplemented(self) -> None:
        # Arrange
        user1 = User("Name", 14)
        user2 = "User(\"Name\", 14)"

        # Act
        result = user1 == user2

        # Assert
        assert result is False

    def test_GIVEN_convert_user_to_json_WHEN_provided_admin_THEN_returns_correct_json_object(self) -> None:
        # Arrange
        test_user = User("Test", 14)
        expected = {"name": "Test", "coin_count": 14, "last_modified": ""}

        # Act
        actual = convert_user_to_json(test_user)

        # Assert
        assert expected == actual
