from enum import Enum


class PermissionLevel(Enum):
    owner = 1
    admin = 2
    viewer = 3
    none = 4

    def from_str(label):
        if label in ('owner', 'Owner'):
            return PermissionLevel.owner
        elif label in ('admin', 'Admin'):
            return PermissionLevel.admin
        elif label in ('viewer', 'Viewer'):
            return PermissionLevel.viewer
        elif label in ('none', 'None'):
            return PermissionLevel.none
        else:
            raise NotImplementedError
