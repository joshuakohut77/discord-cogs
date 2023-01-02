from ChodeCoin.utilities.coin_manager import CoinManager
from ChodeCoin.utilities.info_manager import InfoManager
from ChodeCoin.utilities.message_reader import MessageManager
from ChodeCoin.utilities.reply_generator import ReplyGenerator


class WorkFlow:
    def __init__(self, coin_manager=CoinManager(), info_manager=InfoManager(), message_manager=MessageManager(), reply_generator=ReplyGenerator()):
        self.coin_manager = coin_manager
        self.info_manager = info_manager
        self.message_manager = message_manager
        self.reply_generator = reply_generator

    def process_message(self, message):
        process = self.identify_request(message)

        if process == "chodecoin_ping":
            self.process_chodecoin_ping(message)
        else:
            return None

    def identify_request(self, message):
        is_chodecoin_ping = self.message_manager.is_chodecoin_ping(message)
        if is_chodecoin_ping:
            return "chodecoin_ping"
        else:
            return None

    def process_chodecoin_ping(self, message):
        targeted_user = self.message_manager.find_plus_plus(message)
        if targeted_user is not None:
            self.coin_manager.process_plus_plus(targeted_user)
            return_message = self.reply_generator.generate_reply(targeted_user, "plus_plus", 1)
            return True, return_message

        targeted_user = self.message_manager.find_eggplant_eggplant(message)
        if targeted_user is not None:
            self.coin_manager.process_plus_plus(targeted_user)
            return_message = self.reply_generator.generate_reply(targeted_user, "plus_plus", 1)
            return True, return_message

        targeted_user = self.message_manager.find_minus_minus(message)
        if targeted_user is not None:
            self.coin_manager.process_minus_minus(targeted_user)
            return_message = self.reply_generator.generate_reply(targeted_user, "minus_minus", 1)
            return True, return_message

        targeted_user = self.message_manager.find_no_no(message)
        if targeted_user is not None:
            self.coin_manager.process_minus_minus(targeted_user)
            return_message = self.reply_generator.generate_reply(targeted_user, "minus_minus", 1)
            return True, return_message

        return None
