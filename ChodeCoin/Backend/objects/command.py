def convert_command_to_json(command):
    return {"name": command.name, "description": command.description, "is_admin_command": command.is_admin_command}


class Command(object):
    name = ""
    description = ""
    is_admin_command = False

    def __init__(self, name, description, is_admin_command=False):
        self.name = name
        self.description = description
        self.is_admin_command = is_admin_command

    def __eq__(self, other):
        if not isinstance(other, Command):
            return NotImplemented
        return self.name == other.name and self.description == other.description and self.is_admin_command == other.is_admin_command


def new_command(name, description, is_admin_command):
    command = Command(name, description, is_admin_command)
    return command
