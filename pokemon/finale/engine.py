"""
FinaleEngine — state machine that drives the cinematic ending sequence.

Processes a list of scene nodes, managing transitions between dialog,
battles, cutscenes, and the finale. Each scene type has its own
handling logic. The engine maintains all state needed to pause, resume,
and branch the sequence.
"""
from __future__ import annotations
import asyncio
from io import BytesIO
from typing import List, Dict, Optional, Any, TYPE_CHECKING

import discord

from .scenes import (
    SceneType, DialogScene, BattleStartScene, BattleCutsceneScene,
    TransitionScene, FinaleScene, CutsceneTrigger
)
from .renderer import FinaleRenderer

if TYPE_CHECKING:
    from services.pokeclass import Pokemon as PokemonClass


class FinaleBattleState:
    """Lightweight battle state for finale battles (no gym/wild baggage)."""

    def __init__(self, player_party: List['PokemonClass'],
                 enemy_team_data: List[Dict[str, int]],
                 enemy_name: str, battle_id: str):
        self.player_party = player_party
        self.player_current_index = 0
        self.player_pokemon: 'PokemonClass' = player_party[0]

        self.enemy_team_data = enemy_team_data
        self.enemy_current_index = 0
        self.enemy_pokemon: Optional['PokemonClass'] = None

        self.enemy_name = enemy_name
        self.battle_id = battle_id
        self.turn_number = 1
        self.battle_log: List[str] = []
        self.defeated_enemies: List[str] = []

    @property
    def enemy_hp_pct(self) -> float:
        if not self.enemy_pokemon:
            return 100.0
        stats = self.enemy_pokemon.getPokeStats()
        max_hp = stats['hp']
        if max_hp <= 0:
            return 0.0
        return (self.enemy_pokemon.currentHP / max_hp) * 100.0

    @property
    def player_hp_pct(self) -> float:
        if not self.player_pokemon:
            return 100.0
        stats = self.player_pokemon.getPokeStats()
        max_hp = stats['hp']
        if max_hp <= 0:
            return 0.0
        return (self.player_pokemon.currentHP / max_hp) * 100.0

    def get_next_enemy(self) -> Optional[Dict[str, int]]:
        """Get the next enemy Pokemon data dict, or None if all defeated."""
        next_idx = self.enemy_current_index + 1
        if next_idx < len(self.enemy_team_data):
            self.enemy_current_index = next_idx
            return self.enemy_team_data[next_idx]
        return None

    def get_next_player_pokemon(self) -> Optional['PokemonClass']:
        """Get the next alive player Pokemon, or None."""
        for i in range(self.player_current_index + 1, len(self.player_party)):
            poke = self.player_party[i]
            if poke.currentHP > 0:
                self.player_current_index = i
                self.player_pokemon = poke
                return poke
        return None


class FinaleEngine:
    """
    Drives the cinematic finale sequence.
    
    The engine holds the full script, current position, battle state,
    and renderer. The Views call engine methods to advance the story.
    """

    def __init__(self, user_id: str, trainer_name: str,
                 player_party: List['PokemonClass'],
                 script: List[Any]):
        self.user_id = user_id
        self.trainer_name = trainer_name
        self.player_party = player_party

        # Flatten the script — top-level scenes
        self.script = script
        self.scene_index = 0

        # For dialog scenes with multiple text pages
        self.dialog_page_index = 0

        # Active battle state (None when not in battle)
        self.battle_state: Optional[FinaleBattleState] = None

        # Cutscenes that haven't fired yet, keyed by battle_id
        self.pending_cutscenes: Dict[str, List[BattleCutsceneScene]] = {}

        # Active cutscene dialog being played
        self.active_cutscene: Optional[BattleCutsceneScene] = None
        self.cutscene_dialog_index = 0
        self.cutscene_page_index = 0

        # Renderer
        self.renderer = FinaleRenderer()

        # Track completion
        self.is_complete = False

        # Pre-process: extract cutscenes from script and index them
        self._index_cutscenes()

    def _index_cutscenes(self):
        """Pull BattleCutsceneScene nodes out of the main script and index by battle_id."""
        cleaned_script = []
        for scene in self.script:
            if isinstance(scene, BattleCutsceneScene):
                bid = scene.battle_id
                if bid not in self.pending_cutscenes:
                    self.pending_cutscenes[bid] = []
                self.pending_cutscenes[bid].append(scene)
            else:
                cleaned_script.append(scene)
        self.script = cleaned_script

    # ------------------------------------------------------------------
    # Scene access
    # ------------------------------------------------------------------

    def get_current_scene(self) -> Optional[Any]:
        """Get the current scene node."""
        if self.scene_index < len(self.script):
            return self.script[self.scene_index]
        return None

    def is_in_battle(self) -> bool:
        return self.battle_state is not None

    def is_in_cutscene(self) -> bool:
        return self.active_cutscene is not None

    # ------------------------------------------------------------------
    # Rendering current state
    # ------------------------------------------------------------------

    def render_current(self) -> BytesIO:
        """Render the current scene/state into a PNG buffer."""
        # If we're in a cutscene dialog, render that
        if self.active_cutscene:
            dialog = self.active_cutscene.dialog[self.cutscene_dialog_index]
            text = dialog.text[self.cutscene_page_index] if self.cutscene_page_index < len(dialog.text) else ""
            img = self.renderer.render_dialog(
                speaker=dialog.speaker,
                text=text,
                background=dialog.background,
                character_sprite=dialog.character_sprite,
                character_position=dialog.character_position,
                text_box_color=dialog.text_box_color,
                trainer_name=self.trainer_name
            )
            return self.renderer.to_discord_file(img, "cutscene.png")

        # If we're in a battle, render battle frame
        if self.battle_state:
            log_text = "\n".join(self.battle_state.battle_log[-3:]) if self.battle_state.battle_log else None
            img = self.renderer.render_battle(
                player_pokemon=self.battle_state.player_pokemon,
                enemy_pokemon=self.battle_state.enemy_pokemon,
                enemy_name=self.battle_state.enemy_name,
                turn_number=self.battle_state.turn_number,
                battle_log=log_text
            )
            return self.renderer.to_discord_file(img, "battle.png")

        # Otherwise render the current script scene
        scene = self.get_current_scene()
        if scene is None:
            img = self.renderer.render_transition(text="...")
            return self.renderer.to_discord_file(img, "scene.png")

        if isinstance(scene, DialogScene):
            text = scene.text[self.dialog_page_index] if self.dialog_page_index < len(scene.text) else ""
            img = self.renderer.render_dialog(
                speaker=scene.speaker,
                text=text,
                background=scene.background,
                character_sprite=scene.character_sprite,
                character_position=scene.character_position,
                text_box_color=scene.text_box_color,
                trainer_name=self.trainer_name
            )
            return self.renderer.to_discord_file(img, "dialog.png")

        elif isinstance(scene, BattleStartScene):
            # Render the "battle is about to begin" frame
            intro = scene.intro_text or f"{scene.enemy_name} wants to battle!"
            img = self.renderer.render_dialog(
                speaker=scene.enemy_name,
                text=intro,
                background=scene.battle_background,
                character_sprite=scene.enemy_sprite,
                trainer_name=self.trainer_name
            )
            return self.renderer.to_discord_file(img, "battle_intro.png")

        elif isinstance(scene, TransitionScene):
            img = self.renderer.render_transition(
                image=scene.image,
                text=scene.text,
                bg_color=scene.bg_color
            )
            return self.renderer.to_discord_file(img, "transition.png")

        elif isinstance(scene, FinaleScene):
            text = scene.text[0] if scene.text else "The end."
            img = self.renderer.render_finale(
                title=scene.title,
                text=text,
                background=scene.background,
                trainer_name=self.trainer_name
            )
            return self.renderer.to_discord_file(img, "finale.png")

        # Fallback
        img = self.renderer.render_transition(text="...")
        return self.renderer.to_discord_file(img, "scene.png")

    # ------------------------------------------------------------------
    # Advancing the story
    # ------------------------------------------------------------------

    def advance_dialog(self) -> str:
        """
        Advance dialog by one page. Returns a status string:
        - "next_page" — more pages in this dialog
        - "next_scene" — dialog finished, moved to next scene
        - "start_battle" — next scene is a battle, needs initialization
        - "complete" — script is finished
        """
        # If in cutscene dialog
        if self.active_cutscene:
            return self._advance_cutscene_dialog()

        scene = self.get_current_scene()
        if scene is None:
            self.is_complete = True
            return "complete"

        if isinstance(scene, DialogScene):
            self.dialog_page_index += 1
            if self.dialog_page_index < len(scene.text):
                return "next_page"
            else:
                return self._advance_scene()

        elif isinstance(scene, TransitionScene):
            return self._advance_scene()

        elif isinstance(scene, BattleStartScene):
            return "start_battle"

        elif isinstance(scene, FinaleScene):
            self.is_complete = True
            return "complete"

        return self._advance_scene()

    def _advance_scene(self) -> str:
        """Move to the next scene in the script."""
        self.scene_index += 1
        self.dialog_page_index = 0

        scene = self.get_current_scene()
        if scene is None:
            self.is_complete = True
            return "complete"

        if isinstance(scene, BattleStartScene):
            return "start_battle"

        return "next_scene"

    def _advance_cutscene_dialog(self) -> str:
        """Advance within a cutscene's dialog sequences."""
        cutscene = self.active_cutscene
        current_dialog = cutscene.dialog[self.cutscene_dialog_index]

        self.cutscene_page_index += 1
        if self.cutscene_page_index < len(current_dialog.text):
            return "next_page"

        # Move to next dialog in the cutscene
        self.cutscene_dialog_index += 1
        self.cutscene_page_index = 0

        if self.cutscene_dialog_index < len(cutscene.dialog):
            return "next_page"

        # Cutscene is done — apply post-cutscene effects and resume battle
        self._apply_cutscene_effects(cutscene)
        self.active_cutscene = None
        self.cutscene_dialog_index = 0
        self.cutscene_page_index = 0
        return "resume_battle"

    def _apply_cutscene_effects(self, cutscene: BattleCutsceneScene):
        """Apply any post-cutscene effects (healing, adding Pokemon, etc.)."""
        if not self.battle_state:
            return

        if cutscene.post_cutscene_heal_enemy and self.battle_state.enemy_pokemon:
            stats = self.battle_state.enemy_pokemon.getPokeStats()
            self.battle_state.enemy_pokemon.currentHP = stats['hp']

        if cutscene.post_cutscene_add_enemy:
            self.battle_state.enemy_team_data.append(cutscene.post_cutscene_add_enemy)

    # ------------------------------------------------------------------
    # Battle management
    # ------------------------------------------------------------------

    def start_battle(self, create_pokemon_func) -> 'FinaleBattleState':
        """
        Initialize a battle from the current BattleStartScene.
        
        create_pokemon_func: callable(pokemon_data_dict, discord_id) -> PokemonClass
            Function to create an enemy Pokemon instance from a dict like {"mewtwo": 70}
        """
        scene = self.get_current_scene()
        if not isinstance(scene, BattleStartScene):
            raise ValueError("Current scene is not a BattleStartScene")

        # Refresh player party HP from actual objects
        alive_party = [p for p in self.player_party if p.currentHP > 0]
        if not alive_party:
            alive_party = self.player_party  # fallback

        self.battle_state = FinaleBattleState(
            player_party=alive_party,
            enemy_team_data=list(scene.enemy_team),  # copy so cutscenes can modify
            enemy_name=scene.enemy_name,
            battle_id=scene.battle_id
        )

        # Create first enemy Pokemon
        first_enemy_data = scene.enemy_team[0]
        first_enemy = create_pokemon_func(first_enemy_data, self.user_id)
        self.battle_state.enemy_pokemon = first_enemy

        return self.battle_state

    def check_cutscene_triggers(self) -> Optional[BattleCutsceneScene]:
        """
        Check if any pending cutscenes should trigger based on current battle state.
        Returns the cutscene to play, or None.
        """
        if not self.battle_state:
            return None

        bid = self.battle_state.battle_id
        if bid not in self.pending_cutscenes:
            return None

        for cutscene in self.pending_cutscenes[bid]:
            if cutscene.fired:
                continue
            if cutscene.trigger.check(
                enemy_hp_pct=self.battle_state.enemy_hp_pct,
                enemy_fainted=self.battle_state.defeated_enemies,
                turn_number=self.battle_state.turn_number,
                player_hp_pct=self.battle_state.player_hp_pct
            ):
                cutscene.fired = True
                self.active_cutscene = cutscene
                self.cutscene_dialog_index = 0
                self.cutscene_page_index = 0
                return cutscene

        return None

    def end_battle(self, victory: bool) -> str:
        """
        End the current battle and advance the script.
        
        Returns:
        - "next_scene" — more scenes to go
        - "complete" — script is done
        - "defeat" — player lost
        """
        if not victory:
            self.battle_state = None
            return "defeat"

        self.battle_state = None
        # Move past the BattleStartScene
        return self._advance_scene()

    def get_finale_scene(self) -> Optional[FinaleScene]:
        """Get the FinaleScene if we're at one."""
        scene = self.get_current_scene()
        if isinstance(scene, FinaleScene):
            return scene
        return None