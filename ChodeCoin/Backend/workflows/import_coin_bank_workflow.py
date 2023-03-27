from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user
from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.utilities.coin_manager import CoinManager
from ChodeCoin.Backend.utilities.message_reader import MessageReader
from ChodeCoin.Backend.utilities.reply_generator import ReplyGenerator
from ChodeCoin.Backend.utilities.user_manager import UserManager


class ImportCoinBankWorkflow:
    def __init__(
            self,
            user_manager=UserManager(),
            message_reader=MessageReader(),
            reply_generator=ReplyGenerator(),
            coin_manager=CoinManager(),
    ):
        self.user_manager = user_manager
        self.message_reader = message_reader
        self.reply_generator = reply_generator
        self.coin_manager = coin_manager

    def get_import_coin_bank_description(self):
        return Command("!import coinbank {attach json file}", "Imports (and overrides!) the previous Coin Bank with the attached json file. Cannot be undone.")

    def is_import_coin_bank_workflow(self, message):
        return self.message_reader.is_import_coin_bank_command(message)

    async def process_import_coin_bank_request(self, author, attachments):
        if self.user_manager.is_admin_user(convert_to_discord_user(author)):
            await self.coin_manager.import_coin_bank(next(iter(attachments), None))
            return self.reply_generator.generate_import_coin_bank_reply()
        else:
            return self.reply_generator.generate_no_permission_reply()
