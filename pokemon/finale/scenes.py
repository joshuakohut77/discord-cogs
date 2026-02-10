"""
Scene data classes for the finale system.

Each scene type represents a different kind of moment in the cinematic ending.
The FinaleEngine processes these in order, handling transitions between them.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


class SceneType(Enum):
    DIALOG = "dialog"
    BATTLE_START = "battle_start"
    BATTLE_CUTSCENE = "battle_cutscene"
    TRANSITION = "transition"
    FINALE = "finale"


@dataclass
class CutsceneTrigger:
    """Defines when a battle cutscene should fire."""
    # Trigger when enemy HP drops below this percentage
    enemy_hp_pct_below: Optional[int] = None
    # Trigger when a specific enemy Pokemon faints
    enemy_pokemon_fainted: Optional[str] = None
    # Trigger after N turns
    after_turn: Optional[int] = None
    # Trigger when player Pokemon HP drops below this percentage
    player_hp_pct_below: Optional[int] = None

    def check(self, enemy_hp_pct: float, enemy_fainted: List[str],
              turn_number: int, player_hp_pct: float) -> bool:
        """Check if this trigger condition is met."""
        if self.enemy_hp_pct_below is not None:
            if enemy_hp_pct <= self.enemy_hp_pct_below:
                return True
        if self.enemy_pokemon_fainted is not None:
            if self.enemy_pokemon_fainted.lower() in [n.lower() for n in enemy_fainted]:
                return True
        if self.after_turn is not None:
            if turn_number >= self.after_turn:
                return True
        if self.player_hp_pct_below is not None:
            if player_hp_pct <= self.player_hp_pct_below:
                return True
        return False


@dataclass
class DialogScene:
    """A dialog/narrative scene with PIL-rendered imagery."""
    type: SceneType = field(default=SceneType.DIALOG, init=False)

    # Who is speaking (displayed in the text box)
    speaker: str = ""
    # The dialog text lines (each string is one "page" the player advances through)
    text: List[str] = field(default_factory=list)
    # Background image filename (looked up in sprites/finale/backgrounds/)
    background: Optional[str] = None
    # Character sprite filename (looked up in sprites/finale/characters/)
    character_sprite: Optional[str] = None
    # Character sprite position: "left", "right", "center"
    character_position: str = "right"
    # Optional override for text box color (R, G, B, A)
    text_box_color: tuple = (0, 0, 0, 180)
    # Use trainer name placeholder {trainer_name} in text
    use_trainer_name: bool = False
    # Auto-advance after this many seconds (0 = wait for button press)
    auto_advance: float = 0


@dataclass
class BattleStartScene:
    """Initiates a battle sequence against a scripted opponent."""
    type: SceneType = field(default=SceneType.BATTLE_START, init=False)

    # Enemy trainer display name
    enemy_name: str = "???"
    # Enemy team: list of dicts like [{"mewtwo": 70}, {"dragonite": 65}]
    enemy_team: List[Dict[str, int]] = field(default_factory=list)
    # Enemy trainer sprite for the battle scene (in sprites/finale/characters/)
    enemy_sprite: Optional[str] = None
    # Custom battle background (in sprites/finale/backgrounds/)
    battle_background: Optional[str] = None
    # Optional intro dialog before battle starts
    intro_text: Optional[str] = None
    # Tag to identify this battle (for cutscene triggers)
    battle_id: str = "default"


@dataclass
class BattleCutsceneScene:
    """A cutscene that interrupts an active battle when trigger conditions are met."""
    type: SceneType = field(default=SceneType.BATTLE_CUTSCENE, init=False)

    # Which battle this cutscene belongs to
    battle_id: str = "default"
    # When to trigger this cutscene
    trigger: CutsceneTrigger = field(default_factory=CutsceneTrigger)
    # Dialog scenes to play during the cutscene
    dialog: List[DialogScene] = field(default_factory=list)
    # Whether the enemy gets a new Pokemon or heals after cutscene
    post_cutscene_heal_enemy: bool = False
    post_cutscene_add_enemy: Optional[Dict[str, int]] = None
    # If True, this cutscene has already fired and won't fire again
    fired: bool = False


@dataclass
class TransitionScene:
    """A dramatic pause, image, or GIF between scenes."""
    type: SceneType = field(default=SceneType.TRANSITION, init=False)

    # Image or GIF filename (in sprites/finale/effects/)
    image: Optional[str] = None
    # Text overlay on the transition
    text: Optional[str] = None
    # Duration in seconds before auto-advancing (0 = wait for button press)
    duration: float = 0
    # Background color if no image (R, G, B)
    bg_color: tuple = (0, 0, 0)


@dataclass
class FinaleScene:
    """The ending — credits, awards, database updates."""
    type: SceneType = field(default=SceneType.FINALE, init=False)

    # Title text for the ending
    title: str = "Congratulations!"
    # Ending narrative text
    text: List[str] = field(default_factory=list)
    # Background image
    background: Optional[str] = None
    # Awards/flags to set in the database
    awards: Dict[str, Any] = field(default_factory=dict)