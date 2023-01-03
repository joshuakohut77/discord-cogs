from ChodeCoin.objects.user import User


def translate_user_info_to_display_strings(user_array: []):
    name_array = ""
    value_array = ""
    if len(user_array) > 0:
        for user in user_array:
            name_array = name_array + str(user.name) + "\n"
            value_array = value_array + str(user.coin_count) + "\n"
        name_array = name_array[:len(name_array)-2]
        value_array = value_array[:len(value_array)-2]
    else:
        name_array = "No users yet!"
        value_array = "Type \"!ChodeCoin help\" to learn more <3"
    return name_array, value_array


class ArrayHelper:

    def add_if_valid(self, user_array, user_to_validate: User, return_count):
        for user in user_array:
            if user.coin_count <= user_to_validate.coin_count:
                user_array = self.insert_into_array(user_array, user_to_validate, return_count)
        return user_array

    def insert_into_array(self, user_array: [], user_to_add: User, return_count):
        user_array.add(user_to_add)
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
