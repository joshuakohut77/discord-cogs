from ChodeCoin.Backend.utilities.message_reader import MessageReader, is_admin_command, find_targeted_admin_data
from ChodeCoin.Backend.utilities.reply_generator import generate_admin_updated_reply, generate_admin_no_permission_reply, generate_command_error_reply
from ChodeCoin.Backend.utilities.info_manager import InfoManager
from ChodeCoin.Backend.utilities.user_manager import UserManager
from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user
from ChodeCoin.Backend.objects.command import Command


def is_admin_workflow(message):
    return is_admin_command(message)


def get_admin_description():
    return Command("!setpermission [@User] [owner|admin|viewer|none]", "Sets permission")


class AdminWorkflow:
    def __init__(
            self,
            info_manager=InfoManager(),
            user_manager=UserManager(),
            message_reader=MessageReader(),
    ):
        self.info_manager = info_manager
        self.user_manager = user_manager
        self.message_reader = message_reader

    def process_admin_request(self, message, author):
        formatted_message = message.lower()
        target_user, new_admin_level = find_targeted_admin_data(formatted_message)
        if target_user is not None and new_admin_level is not None:
            if self.user_manager.is_admin_user(convert_to_discord_user(author)):
                self.user_manager.set_admin_level(target_user, new_admin_level)
                return generate_admin_updated_reply(target_user)
            else:
                return generate_admin_no_permission_reply()
        else:
            return generate_command_error_reply()