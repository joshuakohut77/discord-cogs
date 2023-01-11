def convert_user_to_json(user):
    return {"name": user.name, "coin_count": user.coin_count, "last_modified": user.last_modified}


class User(object):
    name = ""
    coin_count = 0
    last_modified = ""

    def __init__(self, name, coin_count, last_modified=""):
        self.name = name
        self.coin_count = coin_count
        self.last_modified = last_modified

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.name == other.name and self.coin_count == other.coin_count


def new_user(name, coin_count):
    user = User(name, coin_count, "")
    return user


