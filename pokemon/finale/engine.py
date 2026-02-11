"""
FinaleEngine — state machine that drives the cinematic ending sequence.
"""
from __future__ import annotations
import asyncio
from io import BytesIO
from typing import List, Dict, Optional, Any, TYPE_CHECKING

import discord
from discord.ui import View

from .scenes import (
    SceneType, DialogScene, BattleStartScene, BattleCutsceneScene,
    TransitionScene, FinaleScene, CutsceneTrigger
)
from .renderer import FinaleRenderer

if TYPE_CHECKING:
    from services.pokeclass import Pokemon as PokemonClass


class FinaleBattleState:
    """Lightweight battle state for finale battles."""

    def __init__(self, player_party: List['PokemonClass'],
                 enemy_team_data: List[Dict[str, int]],
                 enemy_name: str, battle_id: str):
        self.player_party = player_party
        self.player_current_index = 0
        self.player_pokemon: 'PokemonClass' = player_party[0]

        self.enemy_team_data = enemy_team_data
        self.enemy_current_index = 0
        self.enemy_pokemon = None

        self.enemy_name = enemy_name
        self.battle_id = battle_id
        self.turn_number = 1
        self.battle_log: List[str] = []
        self.defeated_enemies: List[str] = []
        self.battle_mode: str = "normal"
        self._frame_counter = 0
        self.active_view: Optional[View] = None
        # Audio manager (set by finalemixin if user is in voice)
        self.audio_manager = None

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

    def get_next_enemy(self):
        next_idx = self.enemy_current_index + 1
        if next_idx < len(self.enemy_team_data):
            self.enemy_current_index = next_idx
            return self.enemy_team_data[next_idx]
        return None

    def get_next_player_pokemon(self):
        for i in range(self.player_current_index + 1, len(self.player_party)):
            poke = self.player_party[i]
            if poke.currentHP > 0:
                self.player_current_index = i
                self.player_pokemon = poke
                return poke
        return None


class FinaleEngine:
    """Drives the cinematic finale sequence."""

    def __init__(self, user_id: str, trainer_name: str,
                 player_party: List['PokemonClass'],
                 script: List[Any]):
        self.user_id = user_id
        self.trainer_name = trainer_name
        self.player_party = player_party

        self.script = script
        self.scene_index = 0
        self.dialog_page_index = 0

        self.battle_state: Optional[FinaleBattleState] = None
        self.pending_cutscenes: Dict[str, List[BattleCutsceneScene]] = {}
        self.active_cutscene: Optional[BattleCutsceneScene] = None
        self.cutscene_dialog_index = 0
        self.cutscene_page_index = 0

        self.renderer = FinaleRenderer()
        self.is_complete = False
        self.active_view: Optional[View] = None

        # Message tracking for auto-advance
        self.message: Optional[discord.Message] = None
        # Audio manager (set by finalemixin if user is in voice)
        self.audio_manager = None
        self._advance_id = 0
        self._auto_task = None
        self._frame_counter = 0
        self._index_cutscenes()

    def next_frame_name(self, prefix: str = "scene") -> str:
        """Generate a unique filename to bust Discord's image cache."""
        self._frame_counter += 1
        return f"{prefix}_{self._frame_counter}.png"

    def substitute_text(self, text: str) -> str:
        """Replace all placeholders in text."""
        text = text.replace("{trainer_name}", self.trainer_name)
        if self.player_party:
            last_name = self.player_party[-1].pokemonName.capitalize()
            text = text.replace("{last_pokemon}", last_name)
        if self.battle_state and self.battle_state.player_pokemon:
            text = text.replace("{active_pokemon}",
                                self.battle_state.player_pokemon.pokemonName.capitalize())
        return text

    def _index_cutscenes(self):
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

    def cancel_auto_advance(self):
        """Cancel any pending auto-advance task."""
        self._advance_id += 1
        if self._auto_task and not self._auto_task.done():
            self._auto_task.cancel()
        self._auto_task = None

    # ------------------------------------------------------------------
    # Scene access
    # ------------------------------------------------------------------

    def get_current_scene(self):
        if self.scene_index < len(self.script):
            return self.script[self.scene_index]
        return None

    def is_in_battle(self) -> bool:
        return self.battle_state is not None

    def is_in_cutscene(self) -> bool:
        return self.active_cutscene is not None

    def get_auto_advance_delay(self) -> float:
        """Get the auto-advance delay for the current scene, or 0."""
        if self.active_cutscene:
            return 0
        scene = self.get_current_scene()
        if isinstance(scene, DialogScene) and scene.auto_advance > 0:
            return scene.auto_advance
        if isinstance(scene, TransitionScene) and scene.duration > 0:
            return scene.duration
        return 0

    def get_current_scene_audio(self):
        """Get the audio directive for the current scene. Returns (audio, audio_loop) tuple."""
        if self.active_cutscene:
            # Check cutscene-level audio first
            audio = getattr(self.active_cutscene, 'audio', None)
            audio_loop = getattr(self.active_cutscene, 'audio_loop', False)
            # If the specific cutscene dialog has its own audio override, use that
            if self.cutscene_dialog_index < len(self.active_cutscene.dialog):
                dialog = self.active_cutscene.dialog[self.cutscene_dialog_index]
                d_audio = getattr(dialog, 'audio', None)
                if d_audio is not None:
                    audio = d_audio
                    audio_loop = getattr(dialog, 'audio_loop', False)
            return audio, audio_loop

        scene = self.get_current_scene()
        if scene is None:
            return "stop", False
        return getattr(scene, 'audio', None), getattr(scene, 'audio_loop', False)

    def trigger_scene_audio(self):
        """Tell the audio manager to handle the current scene's audio directive."""
        if not self.audio_manager:
            return
        audio, audio_loop = self.get_current_scene_audio()
        self.audio_manager.handle_scene_audio(audio, audio_loop)

    def get_current_scene_audio(self):
        """Get the audio directive for the current scene. Returns (audio, audio_loop) tuple."""
        if self.active_cutscene:
            # Check the cutscene-level audio first
            audio = getattr(self.active_cutscene, 'audio', None)
            audio_loop = getattr(self.active_cutscene, 'audio_loop', False)
            # If cutscene dialog has its own audio, use that instead
            if self.cutscene_dialog_index < len(self.active_cutscene.dialog):
                dialog = self.active_cutscene.dialog[self.cutscene_dialog_index]
                d_audio = getattr(dialog, 'audio', None)
                if d_audio is not None:
                    audio = d_audio
                    audio_loop = getattr(dialog, 'audio_loop', False)
            return audio, audio_loop

        scene = self.get_current_scene()
        if scene is None:
            return "stop", False
        return getattr(scene, 'audio', None), getattr(scene, 'audio_loop', False)

    def trigger_scene_audio(self):
        """Tell the audio manager to handle the current scene's audio."""
        if not self.audio_manager:
            return
        audio, audio_loop = self.get_current_scene_audio()
        self.audio_manager.handle_scene_audio(audio, audio_loop)
    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_current(self) -> BytesIO:
        if self.active_cutscene:
            dialog = self.active_cutscene.dialog[self.cutscene_dialog_index]
            text = dialog.text[self.cutscene_page_index] if self.cutscene_page_index < len(dialog.text) else ""
            img = self.renderer.render_dialog(
                speaker=self.substitute_text(dialog.speaker),
                text=self.substitute_text(text),
                background=dialog.background,
                character_sprite=dialog.character_sprite,
                character_position=dialog.character_position,
                text_box_color=dialog.text_box_color,
                trainer_name=self.trainer_name,
                character_sprite_2=getattr(dialog, 'character_sprite_2', None),
                character_position_2=getattr(dialog, 'character_position_2', 'left'),
            )
            return self.renderer.to_discord_file(img, "cutscene.png")

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

        scene = self.get_current_scene()
        if scene is None:
            img = self.renderer.render_transition(text="...")
            return self.renderer.to_discord_file(img, "scene.png")

        if isinstance(scene, DialogScene):
            text = scene.text[self.dialog_page_index] if self.dialog_page_index < len(scene.text) else ""
            img = self.renderer.render_dialog(
                speaker=self.substitute_text(scene.speaker),
                text=self.substitute_text(text),
                background=scene.background,
                character_sprite=scene.character_sprite,
                character_position=scene.character_position,
                text_box_color=scene.text_box_color,
                trainer_name=self.trainer_name,
                character_sprite_2=getattr(scene, 'character_sprite_2', None),
                character_position_2=getattr(scene, 'character_position_2', 'left'),
            )
            return self.renderer.to_discord_file(img, "dialog.png")

        elif isinstance(scene, BattleStartScene):
            intro = scene.intro_text or f"{scene.enemy_name} wants to battle!"
            img = self.renderer.render_dialog(
                speaker=scene.enemy_name,
                text=self.substitute_text(intro),
                background=scene.battle_background,
                character_sprite=scene.enemy_sprite,
                trainer_name=self.trainer_name
            )
            return self.renderer.to_discord_file(img, "battle_intro.png")

        elif isinstance(scene, TransitionScene):
            txt = self.substitute_text(scene.text) if scene.text else None
            img = self.renderer.render_transition(
                image=scene.image, text=txt, bg_color=scene.bg_color
            )
            return self.renderer.to_discord_file(img, "transition.png")

        elif isinstance(scene, FinaleScene):
            text = scene.text[0] if scene.text else "The end."
            img = self.renderer.render_finale(
                title=scene.title,
                text=self.substitute_text(text),
                background=scene.background, trainer_name=self.trainer_name
            )
            return self.renderer.to_discord_file(img, "finale.png")

        img = self.renderer.render_transition(text="...")
        return self.renderer.to_discord_file(img, "scene.png")

    # ------------------------------------------------------------------
    # Advancing
    # ------------------------------------------------------------------

    def advance_dialog(self) -> str:
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
        cutscene = self.active_cutscene
        current_dialog = cutscene.dialog[self.cutscene_dialog_index]

        self.cutscene_page_index += 1
        if self.cutscene_page_index < len(current_dialog.text):
            return "next_page"

        self.cutscene_dialog_index += 1
        self.cutscene_page_index = 0

        if self.cutscene_dialog_index < len(cutscene.dialog):
            return "next_page"

        self._apply_cutscene_effects(cutscene)
        self.active_cutscene = None
        self.cutscene_dialog_index = 0
        self.cutscene_page_index = 0
        return "resume_battle"

    def _apply_cutscene_effects(self, cutscene):
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
        scene = self.get_current_scene()
        if not isinstance(scene, BattleStartScene):
            raise ValueError("Current scene is not a BattleStartScene")

        alive_party = [p for p in self.player_party if p.currentHP > 0]
        if not alive_party:
            alive_party = self.player_party

        self.battle_state = FinaleBattleState(
            player_party=alive_party,
            enemy_team_data=list(scene.enemy_team),
            enemy_name=scene.enemy_name,
            battle_id=scene.battle_id
        )
        
        self.battle_state.battle_mode = scene.battle_mode
        first_enemy_data = scene.enemy_team[0]
        first_enemy = create_pokemon_func(first_enemy_data, self.user_id)
        self.battle_state.enemy_pokemon = first_enemy

        return self.battle_state

    def check_cutscene_triggers(self):
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
        if not victory:
            self.battle_state = None
            return "defeat"
        self.battle_state = None
        return self._advance_scene()

    def get_finale_scene(self):
        scene = self.get_current_scene()
        if isinstance(scene, FinaleScene):
            return scene
        return None