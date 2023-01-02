from ChodeCoin.utilities.message_reader import MessageReader


class Guard:
    def __init__(self, message_reader=MessageReader()):
        self.message_reader = message_reader

    def against_self_plusplus(self, message_author, message):
        msg: str = message.content
        targeted_user = self.message_reader.extract_targeted_user(str, "Text")
        if message_author == targeted_user:
            return "You silly goose you can't updoot yourself o_O"
        else:
            return None
