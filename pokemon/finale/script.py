"""
Finale script — the story beats for the cinematic ending.

This is a placeholder script to test the engine end-to-end.
Replace with real story content and art assets later.

Scene flow:
  1. Dialog — mysterious figure appears
  2. Dialog — taunts the player
  3. Battle — fight the mystery trainer
  4. Cutscene — triggers mid-battle when enemy HP < 50%
  5. Dialog — post-battle congratulations
  6. Finale — credits / completion
"""
from .scenes import (
    DialogScene,
    BattleStartScene,
    BattleCutsceneScene,
    TransitionScene,
    FinaleScene,
    CutsceneTrigger,
)


def get_finale_script() -> list:
    """
    Returns the full ordered list of scene nodes.
    
    BattleCutsceneScene nodes are included in-line but the engine
    will extract them and index them by battle_id automatically.
    """
    return [
        # --- ACT 1: The Encounter ---

        TransitionScene(
            text="...",
            bg_color=(0, 0, 0),
        ),

        DialogScene(
            speaker="???",
            text=[
                "So... you actually made it.",
                "The Elite Four. The Champion. All of them fell before you.",
            ],
            background="placeholder_bg.png",      # Replace with real art
            character_sprite="placeholder_rival.png",  # Replace with real art
            character_position="right",
        ),

        DialogScene(
            speaker="???",
            text=[
                "But this isn't over yet, {trainer_name}.",
                "There's one more battle you have to face.",
                "The one nobody warned you about.",
            ],
            background="placeholder_bg.png",
            character_sprite="placeholder_rival.png",
            character_position="right",
            use_trainer_name=True,
        ),

        TransitionScene(
            image=None,  # Replace with dramatic flash image/gif
            text="A blinding light fills the room...",
            bg_color=(255, 255, 255),
        ),

        # --- ACT 2: The Battle ---

        BattleStartScene(
            enemy_name="??? The Unknown",
            enemy_team=[
                {"mewtwo": 70},
            ],
            enemy_sprite="placeholder_rival.png",
            battle_background=None,  # Will use default battle bg
            intro_text="??? The Unknown challenges you to a battle!",
            battle_id="final_boss",
        ),

        # This cutscene fires mid-battle when enemy HP drops below 50%
        BattleCutsceneScene(
            battle_id="final_boss",
            trigger=CutsceneTrigger(enemy_hp_pct_below=50),
            dialog=[
                DialogScene(
                    speaker="???",
                    text=[
                        "Impressive... You're stronger than I thought.",
                        "But I'm not done yet!",
                    ],
                    background="placeholder_bg.png",
                    character_sprite="placeholder_rival.png",
                    character_position="center",
                ),
            ],
            post_cutscene_heal_enemy=False,
            post_cutscene_add_enemy=None,
        ),

        # --- ACT 3: The Aftermath ---

        TransitionScene(
            text="The battle is over.",
            bg_color=(0, 0, 0),
        ),

        DialogScene(
            speaker="Professor Oak",
            text=[
                "{trainer_name}... I can't believe it.",
                "You've done what no trainer has ever done before.",
                "You are the true Pokemon Champion!",
            ],
            background="placeholder_bg.png",
            character_sprite="oak.png",  # Falls back to sprites/trainers/oak.png
            character_position="left",
            use_trainer_name=True,
        ),

        # --- FINALE ---

        FinaleScene(
            title="🏆 Pokemon Champion 🏆",
            text=[
                "{trainer_name} defeated the unknown challenger",
                "and became the greatest Pokemon trainer",
                "the world has ever seen!",
            ],
            background=None,
            awards={"champion": True},
        ),
    ]