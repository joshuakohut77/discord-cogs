from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user
from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.utilities.message_reader import MessageReader
from ChodeCoin.Backend.utilities.reply_generator import ReplyGenerator
from ChodeCoin.Backend.utilities.user_manager import UserManager


class ExportCoinBankWorkflow:
    def __init__(
            self,
            user_manager=UserManager(),
            message_reader=MessageReader(),
            reply_generator=ReplyGenerator(),
    ):
        self.user_manager = user_manager
        self.message_reader = message_reader
        self.reply_generator = reply_generator

    def get_export_coin_bank_description(self):
        return Command("!export coinbank", "Exports the entire coinbank as a json file.", True)

    def is_export_coin_bank_workflow(self, message):
        return self.message_reader.is_export_coin_bank_command(message)

    def process_export_coin_bank_request(self, author):
        if self.user_manager.is_admin_user(convert_to_discord_user(author)):
            return None, None, self.reply_generator.generate_export_coin_bank_reply()
        else:
            return self.reply_generator.generate_permission_no_permission_reply(), None, None
