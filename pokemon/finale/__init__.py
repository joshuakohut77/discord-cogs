"""Finale system - Cinematic ending battle sequence."""

from .engine import FinaleEngine
from .renderer import FinaleRenderer
from .audio import FinaleAudioManager
from .scenes import (
    SceneType, DialogScene, BattleStartScene, BattleCutsceneScene,
    TransitionScene, FinaleScene, CutsceneTrigger
)

__all__ = [
    'FinaleEngine',
    'FinaleRenderer',
    'FinaleAudioManager',
    'SceneType',
    'DialogScene',
    'BattleStartScene',
    'BattleCutsceneScene',
    'TransitionScene',
    'FinaleScene',
    'CutsceneTrigger',
]