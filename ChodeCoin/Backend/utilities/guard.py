from ChodeCoin.Backend.utilities.message_reader import MessageReader


class Guard:
    def __init__(self, message_reader=MessageReader()):
        self.message_reader = message_reader

    # Doesn't work at the moment due to the way message.author differs from the ping'd user's ID
    def against_self_plus_plus(self, target_user, message_author):
        if message_author == target_user:
            return "You silly goose you can't updoot yourself o_O"
        else:
            return target_user
