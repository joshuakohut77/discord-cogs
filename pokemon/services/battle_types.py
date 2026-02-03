"""Shared types and base classes for battle system"""
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .encounterclass import encounter
    from .trainerclass import trainer

class BattleType(Enum):
    WILD = "wild"
    TRAINER = "trainer"
    GYM = "gym"

# Any other shared constants or base classes