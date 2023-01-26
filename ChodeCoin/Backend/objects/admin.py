def convert_admin_to_json(admin):
    return {"name": admin.name, "permission_level": admin.permission_level, "date_added": admin.date_added}


class Admin(object):
    name = ""
    permission_level = ""
    date_added = ""

    def __init__(self, name, permission_level, date_added=""):
        self.name = name
        self.permission_level = permission_level
        self.date_added = date_added

    def __eq__(self, other):
        if not isinstance(other, Admin):
            return NotImplemented
        return self.name == other.name and self.permission_level == other.permission_level


def new_admin(name, permission_level):
    admin = Admin(name, permission_level)
    return admin


