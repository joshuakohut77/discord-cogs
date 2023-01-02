class User(object):
    name = ""
    coin_count = 0
    last_modified = ""

    def __init__(self, name, coin_count, last_modified=""):
        self.name = name
        self.coin_count = coin_count
        self.last_modified = last_modified


def new_user(name, coin_count):
    user = User(name, coin_count, "")
    return user
