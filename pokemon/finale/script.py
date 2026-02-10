"""
Finale script — Part 1: Skippy's Challenge

Scene flow through the first 4 custom Pokemon battles,
ending at the Skippy reveal.
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
    return [
        # ============================================================
        # ACT 1: THE ENCOUNTER
        # ============================================================

        DialogScene(
            speaker="???",
            text=["So... you actually made it."],
            background="finale_bg.png",
            character_sprite="shrouded_figure.png",
        ),
        DialogScene(
            speaker="???",
            text=["The Elite Four. The Champion. All of them fell before you."],
            background="finale_bg.png",
            character_sprite="shrouded_figure.png",
        ),
        DialogScene(
            speaker="???",
            text=["But this isn't over yet, {trainer_name}."],
            background="finale_bg.png",
            character_sprite="shrouded_figure.png",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="???",
            text=["There's one more battle you have to face. One that you can't possibly win."],
            background="finale_bg.png",
            character_sprite="shrouded_figure.png",
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["Who are you and why is this so cinematic?"],
            background="finale_bg.png",
            character_sprite="trainer.png",
            character_position="left",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="???",
            text=["It is I, Skippy the Magnificent! Master of Pokemon. The almighty and undefeated one!"],
            background="finale_bg.png",
            character_sprite="shrouded_figure.png",
        ),

        # --- Screen flash / Skippy reveal ---
        TransitionScene(
            text="",
            bg_color=(255, 255, 255),
            duration=1.5,
        ),
        TransitionScene(
            text="",
            bg_color=(200, 200, 220),
            duration=1.5,
        ),

        DialogScene(
            speaker="Skippy",
            text=["Prepare thyself, {trainer_name}, for you shall learn to fear my superior Pokemon!"],
            background="finale_bg.png",
            character_sprite="skippy.png",
            use_trainer_name=True,
        ),

        # ============================================================
        # ACT 2: VAPOREON INCIDENT
        # ============================================================

        DialogScene(
            speaker="",
            text=["{trainer_name} sends out their Pokemon!"],
            background="finale_battle_bg.png",
            character_sprite="trainer.png",
            character_position="left",
            use_trainer_name=True,
            auto_advance=3,
        ),
        DialogScene(
            speaker="Skippy",
            text=["Skippy sends out Vaporeon!"],
            background="finale_battle_bg.png",
            character_sprite="vaporeon.png",
            auto_advance=3,
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["Ha! A Vaporeon. Professor Oak told me about them..."],
            background="finale_battle_bg.png",
            character_sprite="vaporeon.png",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="",
            text=["...Vaporeon looks mildly concerned from hearing the name, Professor Oak."],
            background="finale_battle_bg.png",
            character_sprite="vaporeon.png",
        ),
        DialogScene(
            speaker="",
            text=["Vaporeon ran away!"],
            background="finale_battle_bg.png",
        ),
        DialogScene(
            speaker="Skippy",
            text=["Ugghhhh! That stupid Pokemon always was squirmish around pesky humans."],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
        ),
        DialogScene(
            speaker="Skippy",
            text=["No matter, the real battle starts now!"],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
        ),

        # ============================================================
        # BATTLE 1: DRAGONDEEZ
        # ============================================================

        DialogScene(
            speaker="Skippy",
            text=["Skippy sends out DragonDeez!"],
            background="finale_battle_bg.png",
            character_sprite="dragon_deez.png",
            auto_advance=3,
        ),

        BattleStartScene(
            enemy_name="Skippy",
            enemy_team=[{"DragonDeez": 64}],
            enemy_sprite="dragon_deez.png",
            battle_background="finale_battle_bg.png",
            intro_text="DragonDeez enters the battle!",
            battle_id="dragondeez",
        ),

        # --- Post DragonDeez ---

        DialogScene(
            speaker="Skippy",
            text=["How dare you! You think you're better than me???"],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
        ),

        # ============================================================
        # BATTLE 2: TITTY PUSSY
        # ============================================================

        DialogScene(
            speaker="Skippy",
            text=["Skippy sends out Titty Pussy!"],
            background="finale_battle_bg.png",
            character_sprite="titty_pussy.png",
            auto_advance=3,
        ),

        BattleStartScene(
            enemy_name="Skippy",
            enemy_team=[{"TittyPussy": 66}],
            enemy_sprite="titty_pussy.png",
            battle_background="finale_battle_bg.png",
            intro_text="Titty Pussy enters the battle!",
            battle_id="tittypussy",
        ),

        # --- Post Titty Pussy ---

        DialogScene(
            speaker="Skippy",
            text=["How can this be? You are not ready for what's coming next!"],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
        ),

        # ============================================================
        # BATTLE 3: ANGEL HERNANDEZ
        # ============================================================

        DialogScene(
            speaker="Skippy",
            text=["Skippy sends out Angel Hernandez!"],
            background="finale_battle_bg.png",
            character_sprite="angel_hernandez.png",
            auto_advance=3,
        ),

        BattleStartScene(
            enemy_name="Skippy",
            enemy_team=[{"AngelHernandez": 64}],
            enemy_sprite="angel_hernandez.png",
            battle_background="finale_battle_bg.png",
            intro_text="Angel Hernandez enters the battle!",
            battle_id="angelhernandez",
        ),

        # --- Post Angel Hernandez ---

        DialogScene(
            speaker="Skippy",
            text=["I'm actually not surprised. He was never good at his job. This one is the real show-stopper!"],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
        ),

        # ============================================================
        # BATTLE 4: ABIGAIL SHAPIRO
        # ============================================================

        DialogScene(
            speaker="Skippy",
            text=["Skippy sends out Abigail Shapiro!"],
            background="finale_battle_bg.png",
            character_sprite="abigail_shapiro.png",
            auto_advance=3,
        ),

        BattleStartScene(
            enemy_name="Skippy",
            enemy_team=[{"AbigailShapiro": 69}],
            enemy_sprite="abigail_shapiro.png",
            battle_background="finale_battle_bg.png",
            intro_text="Abigail Shapiro enters the battle!",
            battle_id="abigailshapiro",
        ),

        # --- Post Abigail Shapiro ---

        DialogScene(
            speaker="Skippy",
            text=["You are a formidable foe, {trainer_name}."],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="Skippy",
            text=["However, do you think you have what it takes to defeat..."],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
        ),
        DialogScene(
            speaker="Skippy",
            text=["Skippy the Magnificent!"],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
        ),
        DialogScene(
            speaker="Skippy",
            text=["Skippy sends our himself!"],
            background="finale_battle_bg.png",
            character_sprite="skippy.png",
        ),

        # ============================================================
        # PLACEHOLDER STOP — Part 2 goes here
        # ============================================================

        FinaleScene(
            title="To Be Continued...",
            text=[
                "The battle with Skippy the Magnificent",
                "is just beginning...",
                "Stay tuned, {trainer_name}!",
            ],
            background="finale_bg.png",
            awards={},
        ),
    ]