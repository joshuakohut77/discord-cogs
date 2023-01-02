from ChodeCoin.objects.user import User


def translate_user_info_to_array(user_array: [], value):
    new_array = []
    if value == "Name":
        for user in user_array:
            new_array.insert(len(new_array), user.name.__str__())
    elif value == "Coin_Count":
        for user in user_array:
            new_array.insert(len(new_array), user.coin_count.__str__())
    return new_array


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
