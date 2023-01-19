from enum import Enum


class PermissionLevel(Enum):
    owner = 1
    admin = 2
    viewer = 3
    none = 4
