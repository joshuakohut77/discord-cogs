from ChodeCoin.Backend.utilities.message_reader import MessageReader, is_set_info_command, find_targeted_permission_data, find_set_info_data
from ChodeCoin.Backend.utilities.reply_generator import generate_coin_count_updated_reply, generate_permission_no_permission_reply, generate_command_error_reply
from ChodeCoin.Backend.utilities.info_manager import InfoManager
from ChodeCoin.Backend.utilities.user_manager import UserManager
from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user
from ChodeCoin.Backend.objects.command import Command


def is_set_info_workflow(message):
    return is_set_info_command(message)


def get_set_info_description():
    return Command("!setinfo [@User] coincount [new value]", "Sets provided user's coin count to the provided value.", True)


class SetInfoWorkflow:
    def __init__(
            self,
            info_manager=InfoManager(),
            user_manager=UserManager(),
            message_reader=MessageReader(),
    ):
        self.info_manager = info_manager
        self.user_manager = user_manager
        self.message_reader = message_reader

    def process_set_info_request(self, message, author):
        target_user, new_value = find_set_info_data(message)
        if target_user is not None and new_value is not None:
            if self.user_manager.is_admin_user(convert_to_discord_user(author)):
                self.user_manager.set_coin_count(target_user, new_value)
                return generate_coin_count_updated_reply(target_user, new_value)
            else:
                return generate_permission_no_permission_reply()
        else:
            return generate_command_error_reply()
