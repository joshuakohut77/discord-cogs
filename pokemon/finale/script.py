"""
Finale script — Full storyboard: Skippy's Challenge & Chodethulu
"""
from .scenes import (
    DialogScene, BattleStartScene, BattleCutsceneScene,
    TransitionScene, FinaleScene, CutsceneTrigger,
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
            audio='intro.mp3',
            audio_loop=True,
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
            use_trainer_name=True,
            character_sprite="shrouded_figure.png",
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
            use_trainer_name=True,
            character_position="left",
        ),
        DialogScene(
            speaker="???",
            text=["You're in my game now. Not that crap game KlapPapa coded. Of course it's cinematic!"],
            background="finale_bg.png",
            character_sprite="shrouded_figure.png",
        ),
        DialogScene(
            speaker="???",
            text=["It is I, Skippy the Magnificent! Master of Pokemon. The almighty and undefeated one!"],
            background="finale_bg.png",
            character_sprite="shrouded_figure.png",
        ),

        # --- Screen flash / Skippy reveal ---
        TransitionScene(text="A blinding light fills the room", bg_color=(255, 255, 255), duration=1.5),
        TransitionScene(text="A blinding light fills the room", bg_color=(200, 200, 220), duration=1.5),

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
            speaker="", text=["{trainer_name} sends out their Pokemon!"],
            background="finale_battle_bg.png", character_sprite="trainer.png",
            character_position="left", use_trainer_name=True, auto_advance=3,
        ),
        DialogScene(
            speaker="Skippy", text=["Skippy sends out Vaporeon!"],
            background="finale_battle_bg.png", character_sprite="vaporeon.png",
            auto_advance=3,
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["Ha! A Vaporeon. Professor Oak told me about them..."],
            background="finale_battle_bg.png", character_sprite="vaporeon.png",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="", text=["Vaporeon looks mildly concerned from hearing the name"],
            background="finale_battle_bg.png", character_sprite="vaporeon.png",
            
        ),
        DialogScene(
            speaker="", text=["Vaporeon ran away!"],
            background="finale_battle_bg.png",
        ),
        DialogScene(
            speaker="Skippy",
            text=["Ugghhhh! That stupid Pokemon always was squirmish around pesky humans."],
            background="finale_battle_bg.png", character_sprite="skippy.png",
        ),
        DialogScene(
            speaker="Skippy", text=["No matter, the real battle starts now!"],
            background="finale_battle_bg.png", character_sprite="skippy.png",
            
        ),

        # ============================================================
        # BATTLE 1: DRAGONDEEZ
        # ============================================================
        DialogScene(
            speaker="Skippy", text=["Skippy sends out DragonDeez!"],
            background="finale_battle_bg.png", character_sprite="dragon_deez.png",
            auto_advance=3,
            audio='battle_theme.mp3',
            
        ),
        BattleStartScene(
            enemy_name="Skippy", enemy_team=[{"DragonDeez": 64}],
            enemy_sprite="dragon_deez.png", battle_background="finale_battle_bg.png",
            intro_text="DragonDeez enters the battle!", battle_id="dragondeez",
        ),
        DialogScene(
            speaker="Skippy", text=["How dare you! You think you're better than me???"],
            background="finale_battle_bg.png", character_sprite="skippy.png",
        ),

        # ============================================================
        # BATTLE 2: TITTY PUSSY
        # ============================================================
        DialogScene(
            speaker="Skippy", text=["Skippy sends out Titty Pussy!"],
            background="finale_battle_bg.png", character_sprite="titty_pussy.png",
            auto_advance=3,
        ),
        BattleStartScene(
            enemy_name="Skippy", enemy_team=[{"TittyPussy": 66}],
            enemy_sprite="titty_pussy.png", battle_background="finale_battle_bg.png",
            intro_text="Titty Pussy enters the battle!", battle_id="tittypussy",
        ),
        DialogScene(
            speaker="Skippy",
            text=["How can this be? You are not ready for what's coming next!"],
            background="finale_battle_bg.png", character_sprite="skippy.png",
        ),

        # ============================================================
        # BATTLE 3: ANGEL HERNANDEZ
        # ============================================================
        DialogScene(
            speaker="Skippy", text=["Skippy sends out Angel Hernandez!"],
            background="finale_battle_bg.png", character_sprite="angel_hernandez.png",
            auto_advance=3,
        ),
        BattleStartScene(
            enemy_name="Skippy", enemy_team=[{"AngelHernandez": 64}],
            enemy_sprite="angel_hernandez.png", battle_background="finale_battle_bg.png",
            intro_text="Angel Hernandez enters the battle!", battle_id="angelhernandez",
        ),
        DialogScene(
            speaker="Skippy",
            text=["I'm actually not surprised. He was never good at his job. This one is the real show-stopper!"],
            background="finale_battle_bg.png", character_sprite="skippy.png",
        ),

        # ============================================================
        # BATTLE 4: ABIGAIL SHAPIRO
        # ============================================================
        DialogScene(
            speaker="Skippy", text=["Skippy sends out Abigail Shapiro!"],
            background="finale_battle_bg.png", character_sprite="abigail_shapiro.png",
            auto_advance=3,
        ),
        BattleStartScene(
            enemy_name="Skippy", enemy_team=[{"AbigailShapiro": 69}],
            enemy_sprite="abigail_shapiro.png", battle_background="finale_battle_bg.png",
            intro_text="Abigail Shapiro enters the battle!", battle_id="abigailshapiro",
        ),
        DialogScene(
            speaker="Skippy",
            text=["You are a formidable foe, {trainer_name}."],
            background="finale_battle_bg.png", character_sprite="skippy.png",
            use_trainer_name=True,
            audio="wind.mp3",
            audio_loop=True,
        ),
        DialogScene(
            speaker="Skippy",
            text=["However, do you think you have what it takes to defeat..."],
            background="finale_battle_bg.png", character_sprite="skippy.png",
            audio='stop'
        ),
        DialogScene(
            speaker="Skippy",
            text=["Skippy the Magnificent!"],
            background="finale_battle_bg.png", character_sprite="skippy.png",
            auto_advance=3,
            audio="skippy_battle.mp3",
        ),

        # ============================================================
        # ACT 3: UNWINNABLE BATTLE — Skippy annihilates your team
        # ============================================================
        BattleStartScene(
            enemy_name="Skippy",
            enemy_team=[{"Skippy": 100}],
            enemy_sprite="skippy.png",
            battle_background="finale_battle_bg.png",
            intro_text="Skippy the Magnificent enters the battle!",
            battle_id="skippy_unwinnable",
            battle_mode="unwinnable",
        ),

        # --- Dialog before last pokemon ---
        DialogScene(
            speaker="",
            text=[""],
            background="finale_battle_bg.png", character_sprite="",
            auto_advance=2,
            audio='stop',
        ),
        DialogScene(
            speaker="Skippy",
            text=["Can't you see this is futile. I cannot be beat!"],
            background="finale_battle_bg.png", character_sprite="skippy.png", 
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["He's so strong we can't even hurt him."],
            background="finale_battle_bg.png", character_sprite="trainer.png",
            character_position="left", use_trainer_name=True,
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["My mom, Professor Oak, Gary... They're all counting on me."],
            background="finale_battle_bg.png", character_sprite="trainer.png",
            character_position="left", use_trainer_name=True,
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["This is my moment. This is my destiny."],
            background="finale_battle_bg.png", character_sprite="trainer.png",
            character_position="left", use_trainer_name=True,
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["I don't know how I can win... But I must try."],
            background="finale_battle_bg.png", character_sprite="trainer.png",
            character_position="left", use_trainer_name=True,
            audio="zanarkand.mp3",
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["This is it. This is my last pokemon...\nGo... {last_pokemon}!"],
            background="finale_battle_bg.png", character_sprite="trainer.png",
            character_position="left", use_trainer_name=True,
            
        ),

        # ============================================================
        # ACT 4: RIGGED WIN — Last pokemon fights back
        # Player does 10% per hit, Skippy's attacks are "resisted"
        # ============================================================
        BattleStartScene(
            enemy_name="Skippy",
            enemy_team=[{"Skippy": 100}],
            enemy_sprite="skippy.png",
            battle_background="finale_battle_bg.png",
            intro_text="{last_pokemon} stands tall against Skippy!",
            battle_id="skippy_rigged",
            battle_mode="rigged_win",
        ),

        # Cutscene at 70% HP
        BattleCutsceneScene(
            battle_id="skippy_rigged",
            trigger=CutsceneTrigger(enemy_hp_pct_below=70),
            dialog=[
                DialogScene(
                    speaker="Skippy",
                    text=["Unbelievable! That's not possible!"],
                    background="finale_battle_bg.png",
                    character_sprite="skippy.png",
                    
                ),
            ],
        ),

        # (At 50%, battle_mode logic ends the battle and advances here)

        # ============================================================
        # ACT 5: SKIPPY RAGE — Chodethulu appears
        # ============================================================
        DialogScene(
            speaker="",
            text=[""],
            background="finale_battle_bg.png", character_sprite="",
            audio="whoosh_short.mp3",
            auto_advance=1,
        ),
        DialogScene(
            speaker="Skippy",
            text=["THAT'S ENOUGH! This is my game and I will not allow it!"],
            background="finale_battle_bg.png", character_sprite="skippy.png",
            audio="eerie.mp3",
        ),

        # Blinding light transition
        TransitionScene(text="A blinding light fills the room", bg_color=(255, 255, 255), duration=1.5),

        DialogScene(
            speaker="",
            text=["...your pokemon vanishes into thin air."],
            background="finale_bg.png",
        ),

        DialogScene(
            speaker="Skippy",
            text=["You really pissed me off, {trainer_name}."],
            background="finale_bg.png", character_sprite="skippy.png",
            character_position="left", use_trainer_name=True,
        ),
        DialogScene(
            speaker="Skippy",
            text=["I cannot allow you to leave. I'm sorry but it must be done..."],
            background="finale_bg.png", character_sprite="skippy.png",
            character_position="left",
        ),
        DialogScene(
            speaker="Skippy",
            text=["Wait a minute, what's going on???"],
            background="finale_bg.png", character_sprite="",
            character_position="left",
        ),

        # Flash — Chodethulu teleports in
        TransitionScene(text="", bg_color=(255, 255, 255), duration=1.0,audio="teleport.mp3"),

        # Dual character scene: Skippy left, Chodethulu right
        DialogScene(
            speaker="Skippy",
            text=["Whhaaa!!! Wha wha what are you doing here???"],
            background="finale_bg.png",
            character_sprite="skippy.png", character_position="left",
            character_sprite_2="chodethulu.png", character_position_2="right",
            audio="wind.mp3",
            audio_loop=True,
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["I warned you Skippy. Play by the rules or else you will play by mine."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),
        DialogScene(
            speaker="Skippy",
            text=["But it's not fair. I am the champion. I can't let a mere mortal defeat me."],
            background="finale_bg.png",
            character_sprite="skippy.png", character_position="left",
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["Young {trainer_name}, you fought well and have shown true love for your Pokemon."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["Now show Skippy the power of a true Pokemon Master."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),
        DialogScene(
            speaker="",
            text=["...suddenly your final Pokemon appears at your side."],
            background="finale_bg.png",
            character_sprite="trainer.png", character_position="left",
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["Okay {last_pokemon}, let's do this!"],
            background="finale_bg.png",
            character_sprite="trainer.png", character_position="left",
            use_trainer_name=True,
            audio="champion_battle.mp3",
        ),

        # ============================================================
        # ACT 6: FINAL SKIPPY BATTLE — Player can't lose
        # Player does 15-30%, Skippy does 40-70%, Chodethulu heals
        # ============================================================
        BattleStartScene(
            enemy_name="Skippy",
            enemy_team=[{"Skippy": 100}],
            enemy_sprite="skippy.png",
            battle_background="finale_battle_bg.png",
            intro_text="The true battle begins!",
            battle_id="skippy_final",
            battle_mode="final_skippy",
        ),

        # ============================================================
        # ACT 7: POST-SKIPPY — Chodethulu banishes Skippy
        # ============================================================
        DialogScene(
            speaker="Skippy",
            text=["This is outrageous! I will not be defeated by some pesky human!"],
            background="finale_bg.png",
            character_sprite="skippy.png", character_position="left",
            character_sprite_2="chodethulu.png", character_position_2="right",
            audio="stop",
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["Your time ruling as Pokemon Champion is finished, Skippy."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),
        DialogScene(
            speaker="Skippy",
            text=["I will not stand for this. I am Skippy the Magnificent! You have no power ov..."],
            background="finale_bg.png",
            character_sprite="skippy.png", character_position="left",
            character_sprite_2="chodethulu.png", character_position_2="right",
        ),

        TransitionScene(text="Begone, Skippy.", bg_color=(255, 255, 255), duration=2.0,audio="hymn.mp3"),

        DialogScene(
            speaker="{trainer_name}",
            text=["What happened, where did he go?"],
            background="finale_bg.png",
            character_sprite="trainer.png", character_position="left",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["I sent him back to his home. He won't be bothering you anymore."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["Thank you for helping me... but sir please tell me.\nWho are you?"],
            background="finale_bg.png",
            character_sprite="trainer.png", character_position="left",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["There are some things you are simply not ready to learn."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["You must continue your journey of becoming a Pokemon Master."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["Who knows, maybe one day you'll be able to defeat me."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),
        DialogScene(
            speaker="{trainer_name}",
            text=["How about a duel then? Let's see how much I need to improve."],
            background="finale_bg.png",
            character_sprite="trainer.png", character_position="left",
            use_trainer_name=True,
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["I suppose it has been a while. A duel would be good for me."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),

        # ============================================================
        # ACT 8: MELKOR BATTLE — 4 turns, then one-shot
        # ============================================================
        DialogScene(
            speaker="",
            text=["{trainer_name} VS. Chodethulu"],
            background="finale_bg.png",
            auto_advance=3,
            use_trainer_name=True,
            audio="otherworld.mp3"
        ),
        DialogScene(
            speaker="",
            text=["{trainer_name} sends out {last_pokemon}!"],
            background="finale_battle_bg.png",
            character_sprite="trainer.png", character_position="left",
            auto_advance=3, use_trainer_name=True,
        ),
        DialogScene(
            speaker="",
            text=["Chodethulu sends out Melkor!"],
            background="finale_battle_bg.png",
            character_sprite="melkor.png",
            auto_advance=4,
        ),

        BattleStartScene(
            enemy_name="Chodethulu",
            enemy_team=[{"Melkor": 100}],
            enemy_sprite="melkor.png",
            battle_background="finale_battle_bg.png",
            intro_text="Melkor enters the battlefield!",
            battle_id="melkor",
            battle_mode="melkor",
        ),

        # ============================================================
        # ACT 9: ENDING DIALOG & CREDITS
        # ============================================================
        DialogScene(
            speaker="{trainer_name}",
            text=["Wow you're tough. I need to improve a lot before I can take you on."],
            background="finale_bg.png",
            character_sprite="trainer.png", character_position="left",
            use_trainer_name=True,
            audio="stop",
        ),
        DialogScene(
            speaker="Chodethulu",
            text=["Until you embrace the power of the chode, you can never achieve this level of power."],
            background="finale_bg.png",
            character_sprite="chodethulu.png", character_position="right",
        ),

        FinaleScene(
            title="The End",
            text=[
                "{trainer_name} completed the Pokemon challenge.",
                "But the journey is far from over...",
                "Train hard. Catch them all. Embrace the chode.",
            ],
            background="finale_bg.png",
            awards={"champion": True},
        ),
    ]