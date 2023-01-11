import unittest
from ChodeCoin.Backend.objects.user import User
from parameterized import parameterized

from ChodeCoin.Backend.helpers.array_helper import ArrayHelper, translate_user_info_to_display_strings


def generate_mock_user_array():
    return [
        User("First User Name", 22),
        User("Second User Name", 11),
        User("Third User Name", 33),
        User("Fourth User Name", -44),
        User("Fifth User Name", 34),
    ]


class TestArrayHelper(unittest.TestCase):
    def test_GIVEN_translate_user_info_to_display_strings_WHEN_user_array_has_length_of_zero_THEN_returns_no_users_yet_notification(self) -> None:
        # Arrange
        user_array = []
        expected_name_string = "No users yet!"

        # Act
        actual_name_string, actual_coin_count_string = translate_user_info_to_display_strings(user_array)

        # Assert
        self.assertEqual(expected_name_string, actual_name_string)

    def test_GIVEN_translate_user_info_to_display_strings_WHEN_user_array_has_length_of_zero_THEN_returns_info_for_learning_more(self) -> None:
        # Arrange
        user_array = []
        expected_coin_count_string = "Type \"!ChodeCoin help\" to learn more <3"

        # Act
        actual_name_string, actual_coin_count_string = translate_user_info_to_display_strings(user_array)

        # Assert
        self.assertEqual(expected_coin_count_string, actual_coin_count_string)

    def test_GIVEN_translate_user_info_to_display_strings_WHEN_user_array_has_length_of_one_THEN_returns_numbered_name_string(self) -> None:
        # Arrange
        full_user_array = generate_mock_user_array()
        user_array = []
        user_array.insert(0, full_user_array[0])
        expected_name_string = " 1.) First User Name"

        # Act
        actual_name_string, actual_coin_count_string = translate_user_info_to_display_strings(user_array)

        # Assert
        self.assertEqual(expected_name_string, actual_name_string)

    def test_GIVEN_translate_user_info_to_display_strings_WHEN_user_array_has_length_of_more_than_one_THEN_returns_numbered_name_string(self) -> None:
        # Arrange
        user_array = generate_mock_user_array()
        expected_name_string = " 1.) First User Name \n 2.) Second User Name \n 3.) Third User Name \n 4.) Fourth User Name \n 5.) Fifth User Name"

        # Act
        actual_name_string, actual_coin_count_string = translate_user_info_to_display_strings(user_array)

        # Assert
        self.assertEqual(expected_name_string, actual_name_string)

    def test_GIVEN_translate_user_info_to_display_strings_WHEN_user_array_has_length_of_one_THEN_returns_users_coin_count(self) -> None:
        # Arrange
        full_user_array = generate_mock_user_array()
        user_array = []
        user_array.insert(0, full_user_array[0])
        expected_coin_count_string = " 22"

        # Act
        actual_name_string, actual_coin_count_string = translate_user_info_to_display_strings(user_array)

        # Assert
        self.assertEqual(expected_coin_count_string, actual_coin_count_string)

    def test_GIVEN_translate_user_info_to_display_strings_WHEN_user_array_has_length_of_more_than_one_THEN_returns_all_users_coin_count_string(self) -> None:
        # Arrange
        user_array = generate_mock_user_array()
        expected_coin_count_string = " 22 \n 11 \n 33 \n -44 \n 34"

        # Act
        actual_name_string, actual_coin_count_string = translate_user_info_to_display_strings(user_array)

        # Assert
        self.assertEqual(expected_coin_count_string, actual_coin_count_string)

    @parameterized.expand([(6,), (15,), (26,), (1337,), ])
    def test_GIVEN_add_if_in_wealthiest_group_WHEN_supplied_user_with_array_length_less_than_count_THEN_adds_and_sorts_all_users(self, count) -> None:
        # Arrange
        user_array = generate_mock_user_array()
        user_to_add = User("Sixth User Name", 25)
        array_helper = ArrayHelper()
        expected_user_array = [
            User("Fifth User Name", 34),
            User("Third User Name", 33),
            User("Sixth User Name", 25),
            User("First User Name", 22),
            User("Second User Name", 11),
            User("Fourth User Name", -44),
        ]

        # Act
        actual_user_array = array_helper.add_if_in_wealthiest_group(user_array, user_to_add, count)

        # Assert
        self.assertEqual(expected_user_array, actual_user_array)

    def test_GIVEN_add_if_in_wealthiest_group_WHEN_supplied_user_with_array_length_equal_to_count_THEN_adds_and_sorts_all_users_except_lowest(self) -> None:
        # Arrange
        user_array = generate_mock_user_array()
        user_to_add = User("Sixth User Name", 25)
        count = 5
        array_helper = ArrayHelper()
        expected_user_array = [
            User("Fifth User Name", 34),
            User("Third User Name", 33),
            User("Sixth User Name", 25),
            User("First User Name", 22),
            User("Second User Name", 11),
        ]

        # Act
        actual_user_array = array_helper.add_if_in_wealthiest_group(user_array, user_to_add, count)

        # Assert
        self.assertEqual(expected_user_array, actual_user_array)

    @parameterized.expand([(1,), (4,), ])
    def test_GIVEN_add_if_in_wealthiest_group_WHEN_supplied_user_with_array_length_greater_than_count_THEN_adds_and_sorts_all_users(
            self, count) -> None:
        # Arrange
        user_array = generate_mock_user_array()
        user_to_add = User("Sixth User Name", 25)
        array_helper = ArrayHelper()
        initial_expected_user_array = [
            User("Fifth User Name", 34),
            User("Third User Name", 33),
            User("Sixth User Name", 25),
            User("First User Name", 22),
        ]
        expected_user_array = initial_expected_user_array[0:count]

        # Act
        actual_user_array = array_helper.add_if_in_wealthiest_group(user_array, user_to_add, count)

        # Assert
        self.assertEqual(expected_user_array, actual_user_array)
