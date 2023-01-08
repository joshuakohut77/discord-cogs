from ChodeCoin.Backend.objects.user import User


def translate_user_info_to_display_strings(user_array: []):
    name_string = ""
    coin_count_string = ""
    counter = 1
    if len(user_array) > 0:
        for user in user_array:
            name_string = f"{name_string} {counter}.) {user.name} \n"
            coin_count_string = f"{coin_count_string} {user.coin_count} \n"
            counter += 1
        name_string = name_string[:len(name_string)-2]
        coin_count_string = coin_count_string[:len(coin_count_string)-2]
    else:
        name_string = "No users yet!"
        coin_count_string = "Type \"!ChodeCoin help\" to learn more <3"
    return name_string, coin_count_string


class ArrayHelper:

    def add_if_in_wealthiest_group(self, user_array, user_to_validate: User, return_count):
        return self.insert_into_array_if_wealthy_enough(user_array, user_to_validate, return_count)

    def insert_into_array_if_wealthy_enough(self, user_array: [User], user_to_add: User, return_count):
        user_array.insert(0, user_to_add)
        if len(user_array) > return_count:
            user_array = self.sort_array(user_array)
            user_array = user_array[:-1]
        else:
            user_array = self.sort_array(user_array)
        return user_array

    def get_coin_count(self, user: User):
        return user.coin_count

    def sort_array(self, user_array):
        user_array.sort(key=self.get_coin_count, reverse=True)
        return user_array
