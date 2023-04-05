from ChodeCoin.Backend.objects.command import Command, new_command, convert_command_to_json


class TestCommand:
    def test_GIVEN_new_command_WHEN_new_command_called_THEN_sets_provided_name(self) -> None:
        # Arrange
        expected = "Name"

        # Act
        result = new_command("Name", "Description", True)

        # Assert
        assert result.name == expected

    def test_GIVEN_new_command_WHEN_new_command_called_THEN_sets_provided_description(self) -> None:
        # Arrange
        expected = "Description"

        # Act
        result = new_command("Name", "Description", False)

        # Assert
        assert result.description == expected

    def test_GIVEN_command_WHEN_asserting_equal_on_equal_commands_THEN_returns_true(self) -> None:
        # Arrange
        command1 = Command("Name", "Description")
        command2 = Command("Name", "Description")

        # Act
        result = command1 == command2

        # Assert
        assert result is True

    def test_GIVEN_command_WHEN_asserting_equal_on_commands_with_different_names_THEN_returns_false(self) -> None:
        # Arrange
        command1 = Command("Name1", "Description")
        command2 = Command("Name2", "Description")

        # Act
        result = command1 == command2

        # Assert
        assert result is False

    def test_GIVEN_command_WHEN_asserting_equal_on_commands_with_different_descriptions_THEN_returns_false(self) -> None:
        # Arrange
        command1 = Command("Name", "Description1")
        command2 = Command("Name", "Description2")

        # Act
        result = command1 == command2

        # Assert
        assert result is False

    def test_GIVEN_command_WHEN_asserting_equal_on_non_command_object_THEN_returns_NotImplemented(self) -> None:
        # Arrange
        command1 = Command("Name", "Description")
        command2 = "Command(\"Name\", \"Description\")"

        # Act
        result = command1 == command2

        # Assert
        assert result is False

    def test_GIVEN_convert_command_to_json_WHEN_provided_admin_THEN_returns_correct_json_object(self) -> None:
        # Arrange
        test_command = Command("Test", "Description")
        expected = {"name": "Test", "description": "Description", "is_admin_command": False}

        # Act
        actual = convert_command_to_json(test_command)

        # Assert
        assert expected == actual
