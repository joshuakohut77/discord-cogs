from ChodeCoin.utilities.message_reader import MessageReader


class Guard:
    def __init__(self, message_reader=MessageReader()):
        self.message_reader = message_reader

    # Doesn't work at the moment due to the way message.author differs from the ping'd user's ID
    def against_self_plusplus(self, message, message_author):
        targeted_user = self.message_reader.format_targeted_user(message, "Text")
        if message_author == targeted_user:
            return "You silly goose you can't updoot yourself o_O"
        else:
            return None
