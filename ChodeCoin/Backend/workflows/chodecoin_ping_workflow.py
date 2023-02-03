from ChodeCoin.Backend.enums.command_type import CommandType
from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.utilities.coin_manager import CoinManager
from ChodeCoin.Backend.utilities.guard import Guard
from ChodeCoin.Backend.utilities.message_reader import MessageReader
from ChodeCoin.Backend.utilities.reply_generator import ReplyGenerator


def get_chodecoin_ping_description():
    return Command("@[username] [++|--]", "Gives or takes away one ChodeCoin from the user specified.")


class ChodeCoinPingWorkflow:
    def __init__(
            self,
            message_reader=MessageReader(),
            coin_manager=CoinManager(),
            reply_generator=ReplyGenerator(),
            guard=Guard(),
    ):
        self.message_reader = message_reader
        self.coin_manager = coin_manager
        self.reply_generator = reply_generator
        self.guard = guard

    def is_chodecoin_ping(self, message):
        return self.message_reader.is_chodecoin_ping(message)

    def process_chodecoin_ping_request(self, message, author):
        if self.message_reader.is_plus_plus_command(message):
            targeted_user = self.message_reader.extract_plus_plus_target(message)
            return_message = self.guard.against_self_plus_plus(targeted_user, author)
            if return_message is None:
                self.coin_manager.process_plus_plus(targeted_user)
                # return_message = self.reply_generator.generate_chodecoin_ping_reply(targeted_user, 1)
                return_message = f"{message[:5], message[5:]}"
            return return_message

        if self.message_reader.is_emoji_plus_plus_command(message):
            targeted_user = self.message_reader.extract_emoji_plus_plus_target(message)
            return_message = self.guard.against_self_plus_plus(targeted_user, author)
            if return_message is None:
                self.coin_manager.process_plus_plus(targeted_user)
                return_message = self.reply_generator.generate_chodecoin_ping_reply(targeted_user, 1)
            return return_message

        if self.message_reader.is_minus_minus_command(message):
            targeted_user = self.message_reader.extract_minus_minus_target(message)
            self.coin_manager.process_minus_minus(targeted_user)
            return self.reply_generator.generate_chodecoin_ping_reply(targeted_user, -1)

        if self.message_reader.is_emoji_minus_minus_command(message):
            targeted_user = self.message_reader.extract_emoji_minus_minus_target(message)
            self.coin_manager.process_minus_minus(targeted_user)
            return self.reply_generator.generate_chodecoin_ping_reply(targeted_user, -1)

        return None
