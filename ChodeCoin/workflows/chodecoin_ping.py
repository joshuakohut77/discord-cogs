from ChodeCoin.utilities.coin_manager import CoinManager
from ChodeCoin.utilities.message_reader import MessageManager
from ChodeCoin.utilities.reply_generator import ReplyGenerator


class ChodeCoinPingWorkflow:
    def __init__(
            self,
            message_manager=MessageManager(),
            coin_manager=CoinManager(),
            reply_generator=ReplyGenerator(),
    ):
        self.message_manager = message_manager
        self.coin_manager = coin_manager
        self.reply_generator = reply_generator

    def is_chodecoin_ping(self, message):
        return self.message_manager.is_chodecoin_ping(message)

    def process_chodecoin_ping(self, message):
        targeted_user = self.message_manager.find_plus_plus(message)
        if targeted_user is not None:
            self.coin_manager.process_plus_plus(targeted_user)
            return_message = self.reply_generator.generate_reply(targeted_user, "plus_plus", 1)
            return return_message

        targeted_user = self.message_manager.find_eggplant_eggplant(message)
        if targeted_user is not None:
            self.coin_manager.process_plus_plus(targeted_user)
            return_message = self.reply_generator.generate_reply(targeted_user, "plus_plus", 1)
            return return_message

        targeted_user = self.message_manager.find_minus_minus(message)
        if targeted_user is not None:
            self.coin_manager.process_minus_minus(targeted_user)
            return_message = self.reply_generator.generate_reply(targeted_user, "minus_minus", 1)
            return return_message

        targeted_user = self.message_manager.find_no_no(message)
        if targeted_user is not None:
            self.coin_manager.process_minus_minus(targeted_user)
            return_message = self.reply_generator.generate_reply(targeted_user, "minus_minus", 1)
            return return_message

        return None
