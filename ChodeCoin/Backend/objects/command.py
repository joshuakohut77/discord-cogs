def convert_command_to_json(command):
    return {"name": command.name, "description": command.description}


class Command(object):
    name = ""
    description = ""

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __eq__(self, other):
        if not isinstance(other, Command):
            return NotImplemented
        return self.name == other.name and self.description == other.description


def new_command(name, description):
    command = Command(name, description)
    return command
