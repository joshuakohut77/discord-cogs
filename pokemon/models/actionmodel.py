from enum import Enum


class ActionType(Enum):
    ENCOUNTER = 1
    QUEST = 2
    GIFT = 3
    ONLYONE = 4


class ActionModel:
    name: str
    type: ActionType
    value: str

    def __init__(self, name: str, type: ActionType, value: str) -> None:
        self.name = name
        self.type = type
        self.value = value
        