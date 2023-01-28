from ChodeCoin.Backend.enums.command_type import CommandType
from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user
from ChodeCoin.Backend.utilities.message_reader import MessageReader


class Guard:
    def __init__(self, message_reader=MessageReader()):
        self.message_reader = message_reader

    # Doesn't work at the moment due to the way message.author differs from the ping'd user's ID
    def against_self_plusplus(self, message, message_author):
        text_targeted_user = convert_to_discord_user(self.message_reader.format_targeted_user(message, CommandType.text))
        emoji_targeted_user = convert_to_discord_user(self.message_reader.format_targeted_user(message, CommandType.emoji_plus_plus))
        if message_author == text_targeted_user or message_author == emoji_targeted_user:
            return "You silly goose you can't updoot yourself o_O"
        else:
            return text_targeted_user
