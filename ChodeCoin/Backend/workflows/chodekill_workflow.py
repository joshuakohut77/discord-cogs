from ChodeCoin.Backend.objects.command import Command
from ChodeCoin.Backend.utilities.message_reader import MessageReader, is_admin_command, find_targeted_permission_data, find_chodekill_data, is_chodekill_command
from ChodeCoin.Backend.utilities.reply_generator import generate_permission_updated_reply, generate_permission_no_permission_reply, generate_command_error_reply, generate_chodekill_all_reply, generate_chodekill_prune_reply, generate_chodekill_assassinate_reply
from ChodeCoin.Backend.utilities.info_manager import InfoManager
from ChodeCoin.Backend.utilities.user_manager import UserManager
from ChodeCoin.Backend.helpers.string_helper import convert_to_discord_user


def is_chodekill_workflow(message):
    return is_chodekill_command(message)


def get_chodekill_description():
    return Command("!chodekill [user|--prune|--all]", "Deletes the user specified. | Prunes users who haven't been updated for the last 6 months | Deletes all users")


class ChodeKillWorkflow:
    def __init__(
            self,
            info_manager=InfoManager(),
            user_manager=UserManager(),
            message_reader=MessageReader(),
    ):
        self.info_manager = info_manager
        self.user_manager = user_manager
        self.message_reader = message_reader

    def process_chodekill_request(self, message, author):
        if self.user_manager.is_admin_user(convert_to_discord_user(author)):
            key = find_chodekill_data(message)
            if key is None:
                return generate_command_error_reply()
            else:
                if key == "--all":
                    self.user_manager.delete_all_users()
                    return generate_chodekill_all_reply()
                elif key == "--prune":
                    self.user_manager.prune_users()
                    return generate_chodekill_prune_reply()
                else:
                    target_user = convert_to_discord_user(key)
                    if self.user_manager.user_exists(target_user):
                        self.user_manager.delete_user(target_user)
                    return generate_chodekill_assassinate_reply(target_user)
        else:
            return generate_permission_no_permission_reply()
