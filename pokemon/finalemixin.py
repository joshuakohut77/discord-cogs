"""
FinaleMixin — Cog mixin for the cinematic finale system.

Provides the ,finale command and wires up the FinaleEngine
with Discord interaction callbacks for dialog, battles, cutscenes,
auto-advance timing, and custom Pokemon from finale config.
"""
from __future__ import annotations
import asyncio
from io import BytesIO
from typing import Dict, Union, TYPE_CHECKING

import discord
from discord import Interaction
from discord.ui import View
from redbot.core import commands

from .abcd import MixinMeta
from .finale.engine import FinaleEngine
from .finale.script import get_finale_script
from .finale.scenes import DialogScene, TransitionScene, BattleStartScene, FinaleScene
from .finale.views import (
    FinaleDialogView, FinaleBattleView,
    FinaleSwitchView, FinaleDefeatView
)
from .finale.custom_pokemon import FinalePokemon, load_finale_pokemon_config

from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass
from services.encounterclass import calculate_battle_damage
from services.pokedexclass import pokedex as PokedexClass
from services.leaderboardclass import leaderboard as LeaderboardClass

if TYPE_CHECKING:
    from redbot.core.bot import Red


DiscordUser = Union[discord.Member, discord.User]


class FinaleMixin(MixinMeta):
    """Cinematic finale battle system."""

    __finale_engines: Dict[str, FinaleEngine] = {}
    __finale_pokemon_config: dict = None

    def _get_finale_pokemon_config(self) -> dict:
        """Load and cache the finale pokemon config."""
        if self.__finale_pokemon_config is None:
            self.__finale_pokemon_config = load_finale_pokemon_config()
        return self.__finale_pokemon_config

    # ------------------------------------------------------------------
    # Command
    # ------------------------------------------------------------------

    @commands.command(name="finale")
    @commands.guild_only()
    async def finale_command(self, ctx: commands.Context) -> None:
        """Begin the cinematic finale — the ultimate battle awaits."""
        user = ctx.author
        user_id = str(user.id)

        if user_id in self.__finale_engines:
            await ctx.send("You're already in the finale! Finish or let it time out first.")
            return

        trainer = TrainerClass(user_id)
        trainer_name = trainer.getTrainerName() if hasattr(trainer, 'getTrainerName') else user.display_name

        party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
            if poke.currentHP > 0:
                alive_party.append(poke)

        if not alive_party:
            await ctx.send("All your Pokemon have fainted! Heal up before attempting the finale.")
            return

        script = get_finale_script()
        engine = FinaleEngine(
            user_id=user_id,
            trainer_name=trainer_name if trainer_name else user.display_name,
            player_party=alive_party,
            script=script
        )
        self.__finale_engines[user_id] = engine

        # Render first frame and send
        buf = engine.render_current()
        file = discord.File(fp=buf, filename="scene.png")

        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url="attachment://scene.png")
        embed.set_footer(text=f"{user.display_name}'s Finale")

        is_auto = engine.get_auto_advance_delay() > 0
        view = FinaleDialogView(engine, self._on_dialog_advance, is_auto=is_auto)
        message = await ctx.send(embed=embed, view=view, file=file)
        engine.message = message

        # Schedule auto-advance if needed
        await self._schedule_auto_advance(engine)

    # ------------------------------------------------------------------
    # Auto-advance scheduling
    # ------------------------------------------------------------------

    async def _schedule_auto_advance(self, engine: FinaleEngine):
        """Schedule an auto-advance task if the current scene supports it."""
        delay = engine.get_auto_advance_delay()
        if delay <= 0 or not engine.message:
            return

        engine._advance_id += 1
        current_id = engine._advance_id

        async def _auto_task():
            await asyncio.sleep(delay)
            # Check if this task is still valid
            if engine._advance_id != current_id:
                return
            if engine.is_complete:
                return

            result = engine.advance_dialog()
            if result == "start_battle":
                await self._auto_start_battle(engine)
            elif result == "complete":
                await self._auto_handle_complete(engine)
            else:
                await self._auto_render_scene(engine)

        engine._auto_task = asyncio.create_task(_auto_task())

    async def _auto_render_scene(self, engine: FinaleEngine):
        """Render scene and edit message directly (no interaction needed)."""
        if not engine.message:
            return

        buf = engine.render_current()
        file = discord.File(fp=buf, filename="scene.png")

        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url="attachment://scene.png")

        is_auto = engine.get_auto_advance_delay() > 0

        if engine.is_in_battle():
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance, is_auto=is_auto)

        try:
            await engine.message.edit(embed=embed, view=view, attachments=[file])
        except Exception:
            pass

        # Chain auto-advances
        await self._schedule_auto_advance(engine)

    async def _auto_start_battle(self, engine: FinaleEngine):
        """Start a battle from auto-advance (no interaction)."""
        engine.start_battle(self._create_finale_enemy_from_config)

        buf = engine.render_current()
        file = discord.File(fp=buf, filename="battle.png")

        embed = discord.Embed(color=discord.Color.red())
        embed.set_image(url="attachment://battle.png")

        bs = engine.battle_state
        if bs:
            alive = sum(1 for p in bs.player_party if p.currentHP > 0)
            embed.set_footer(text=f"Your team: {alive} alive | Turn {bs.turn_number}")

        view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)

        try:
            await engine.message.edit(embed=embed, view=view, attachments=[file])
        except Exception:
            pass

    async def _auto_handle_complete(self, engine: FinaleEngine):
        """Handle finale completion from auto-advance."""
        if not engine.message:
            return
        finale_scene = engine.get_finale_scene()
        if finale_scene:
            text = " ".join(finale_scene.text) if finale_scene.text else "Congratulations!"
            img = engine.renderer.render_finale(
                title=finale_scene.title, text=text,
                background=finale_scene.background, trainer_name=engine.trainer_name
            )
        else:
            img = engine.renderer.render_finale(
                title="Champion", text="Congratulations!",
                trainer_name=engine.trainer_name
            )

        file_buf = engine.renderer.to_discord_file(img, "finale.png")
        file = discord.File(fp=file_buf, filename="finale.png")
        embed = discord.Embed(color=discord.Color.gold())
        embed.set_image(url="attachment://finale.png")

        user_id = engine.user_id
        if user_id in self.__finale_engines:
            del self.__finale_engines[user_id]

        try:
            await engine.message.edit(embed=embed, view=View(), attachments=[file])
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Dialog advance callback (from button press)
    # ------------------------------------------------------------------

    async def _on_dialog_advance(self, interaction: Interaction, result: str):
        """Called by FinaleDialogView when 'Next' or 'Skip' is pressed."""
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine:
            return

        engine.message = interaction.message

        if result == "start_battle":
            await self._start_finale_battle(interaction, engine)
        elif result == "resume_battle":
            await self._render_battle_frame(interaction, engine)
        elif result == "complete":
            await self._handle_finale_complete(interaction, engine)
        else:
            await self._render_scene_frame(interaction, engine)

    # ------------------------------------------------------------------
    # Rendering helpers (interaction-based)
    # ------------------------------------------------------------------

    async def _render_scene_frame(self, interaction: Interaction, engine: FinaleEngine):
        """Re-render current scene and update the message."""
        buf = engine.render_current()
        file = discord.File(fp=buf, filename="scene.png")

        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url="attachment://scene.png")
        embed.set_footer(text=f"{interaction.user.display_name}'s Finale")

        is_auto = engine.get_auto_advance_delay() > 0

        if engine.is_in_cutscene():
            view = FinaleDialogView(engine, self._on_dialog_advance)
        elif engine.is_in_battle():
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance, is_auto=is_auto)

        await interaction.message.edit(embed=embed, view=view, attachments=[file])
        engine.message = interaction.message

        # Schedule auto-advance if needed
        await self._schedule_auto_advance(engine)

    async def _render_battle_frame(self, interaction: Interaction, engine: FinaleEngine,
                                    with_buttons: bool = True):
        """Render battle state and show move buttons."""
        buf = engine.render_current()
        file = discord.File(fp=buf, filename="battle.png")

        embed = discord.Embed(color=discord.Color.red())
        embed.set_image(url="attachment://battle.png")

        bs = engine.battle_state
        if bs:
            alive = sum(1 for p in bs.player_party if p.currentHP > 0)
            enemy_remaining = len(bs.enemy_team_data) - len(bs.defeated_enemies)
            embed.set_footer(text=f"Your team: {alive} alive | Enemy: {enemy_remaining} remaining | Turn {bs.turn_number}")

        if with_buttons:
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        else:
            view = View()

        await interaction.message.edit(embed=embed, view=view, attachments=[file])
        engine.message = interaction.message

    # ------------------------------------------------------------------
    # Battle initialization
    # ------------------------------------------------------------------

    async def _start_finale_battle(self, interaction: Interaction, engine: FinaleEngine):
        """Initialize a battle from a BattleStartScene."""
        engine.start_battle(self._create_finale_enemy_from_config)
        await self._render_battle_frame(interaction, engine)

    def _create_finale_enemy_from_config(self, pokemon_data: dict, player_discord_id: str):
        """Create an enemy Pokemon — checks finale config first, then falls back to standard."""
        name = list(pokemon_data.keys())[0]
        level = pokemon_data[name]

        config = self._get_finale_pokemon_config()
        if name in config:
            poke = FinalePokemon(name, config[name])
            if level:
                poke.currentLevel = level
                stats = poke.getPokeStats()
                poke.currentHP = stats['hp']
            return poke

        # Standard Pokemon fallback
        enemy_pokemon = PokemonClass(player_discord_id, name)
        enemy_pokemon.create(level)
        enemy_pokemon.discordId = None
        PokedexClass(player_discord_id, enemy_pokemon)
        return enemy_pokemon

    # ------------------------------------------------------------------
    # Battle move callback
    # ------------------------------------------------------------------

    async def _on_battle_move(self, interaction: Interaction, move_index: int):
        """Process a player's move selection — multi-step animated turn."""
        user = interaction.user
        user_id = str(user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine or not engine.battle_state:
            return

        engine.cancel_auto_advance()
        engine.message = interaction.message

        bs = engine.battle_state
        player_poke = bs.player_pokemon
        enemy_poke = bs.enemy_pokemon
        msg = interaction.message

        from helpers.pathhelpers import load_json_config
        try:
            moves_config = load_json_config('moves.json')
            type_effectiveness = load_json_config('typeEffectiveness.json')
        except Exception:
            moves_config = {}
            type_effectiveness = {}

        # Inject custom moves from FinalePokemon so calculate_battle_damage finds them
        if hasattr(enemy_poke, 'getMovesConfig'):
            moves_config.update(enemy_poke.getMovesConfig())

        # --- Get player's move ---
        moves = player_poke.getMoves() if hasattr(player_poke, 'getMoves') else []
        if move_index >= len(moves):
            move_index = 0
        player_move_name = moves[move_index]
        display_name = player_move_name.replace('-', ' ').title()

        # --- Calculate player damage ---
        p_damage, p_hit = calculate_battle_damage(
            player_poke, enemy_poke, player_move_name, moves_config, type_effectiveness
        )

        # === STEP 1: Show player attack result (no buttons) ===
        if p_hit and p_damage > 0:
            enemy_poke.currentHP = max(0, enemy_poke.currentHP - p_damage)
            step1_text = f"Your {player_poke.pokemonName.capitalize()} used {display_name}! (-{p_damage} HP)"
        elif p_hit:
            step1_text = f"Your {player_poke.pokemonName.capitalize()} used {display_name}!"
        else:
            step1_text = f"Your {player_poke.pokemonName.capitalize()} used {display_name}... but it missed!"

        bs.battle_log = [step1_text]
        await self._render_battle_frame(interaction, engine, with_buttons=False)

        await asyncio.sleep(3)

        # --- Check if enemy fainted ---
        if enemy_poke.currentHP <= 0:
            bs.defeated_enemies.append(enemy_poke.pokemonName)
            bs.battle_log = [f"{enemy_poke.pokemonName} fainted!"]
            buf = engine.render_current()
            file = discord.File(fp=buf, filename="battle.png")
            embed = discord.Embed(color=discord.Color.red())
            embed.set_image(url="attachment://battle.png")
            await msg.edit(embed=embed, view=View(), attachments=[file])

            await asyncio.sleep(3)

            result = engine.end_battle(victory=True)

            lb = LeaderboardClass(user_id)
            lb.victory()
            lb.actions()

            if result == "complete":
                await self._handle_finale_complete_via_msg(engine)
            else:
                await self._render_scene_via_msg(engine)
            return

        # === STEP 2: Enemy attacks ===
        enemy_moves = enemy_poke.getMoves() if hasattr(enemy_poke, 'getMoves') else []
        enemy_moves = [m for m in enemy_moves if m and m.lower() != 'none']

        status_effect_text = None
        if enemy_moves:
            import random
            e_move_name = random.choice(enemy_moves)

            # Get display name and status effect from custom pokemon data
            e_move_data = {}
            if hasattr(enemy_poke, 'getMoveData'):
                e_move_data = enemy_poke.getMoveData(e_move_name)
            e_display = e_move_data.get('displayName', e_move_name.replace('-', ' ').title())
            status_effect_text = e_move_data.get('statusEffect')

            e_damage, e_hit = calculate_battle_damage(
                enemy_poke, player_poke, e_move_name, moves_config, type_effectiveness
            )

            if e_hit and e_damage > 0:
                player_poke.currentHP = max(0, player_poke.currentHP - e_damage)
                step2_text = f"{enemy_poke.pokemonName} used {e_display}! (-{e_damage} HP)"
            elif e_hit:
                step2_text = f"{enemy_poke.pokemonName} used {e_display}!"
                # Still show status effect even if 0 damage
            else:
                step2_text = f"{enemy_poke.pokemonName}'s {e_display} missed!"
                status_effect_text = None
        else:
            step2_text = f"{enemy_poke.pokemonName} has no moves!"

        bs.battle_log = [step2_text]
        buf = engine.render_current()
        file = discord.File(fp=buf, filename="battle.png")
        embed = discord.Embed(color=discord.Color.red())
        embed.set_image(url="attachment://battle.png")
        await msg.edit(embed=embed, view=View(), attachments=[file])

        await asyncio.sleep(3)

        # === STEP 3: Status effect text ===
        if status_effect_text:
            bs.battle_log = [status_effect_text]
            buf = engine.render_current()
            file = discord.File(fp=buf, filename="battle.png")
            embed = discord.Embed(color=discord.Color.red())
            embed.set_image(url="attachment://battle.png")
            await msg.edit(embed=embed, view=View(), attachments=[file])

            await asyncio.sleep(3)

        bs.turn_number += 1

        # --- Check player fainted ---
        if player_poke.currentHP <= 0:
            player_poke.save()
            next_poke = bs.get_next_player_pokemon()
            if next_poke:
                bs.battle_log = [
                    f"Your {player_poke.pokemonName.capitalize()} fainted!",
                    f"Go, {next_poke.pokemonName.capitalize()}!"
                ]
                buf = engine.render_current()
                file = discord.File(fp=buf, filename="battle.png")
                embed = discord.Embed(color=discord.Color.red())
                embed.set_image(url="attachment://battle.png")
                view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
                await msg.edit(embed=embed, view=view, attachments=[file])
                return
            else:
                bs.battle_log = ["All your Pokemon have fainted!"]
                await self._handle_finale_defeat_via_msg(engine)
                return

        # --- Check cutscene triggers ---
        cutscene = engine.check_cutscene_triggers()
        if cutscene:
            await self._render_scene_via_msg(engine)
            return

        player_poke.save()

        # === STEP 4: Show move buttons again ===
        bs.battle_log = [f"Turn {bs.turn_number} — Choose your move!"]
        buf = engine.render_current()
        file = discord.File(fp=buf, filename="battle.png")
        embed = discord.Embed(color=discord.Color.red())
        embed.set_image(url="attachment://battle.png")
        alive = sum(1 for p in bs.player_party if p.currentHP > 0)
        enemy_remaining = len(bs.enemy_team_data) - len(bs.defeated_enemies)
        embed.set_footer(text=f"Your team: {alive} alive | Enemy: {enemy_remaining} remaining | Turn {bs.turn_number}")
        view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        await msg.edit(embed=embed, view=view, attachments=[file])

    # ------------------------------------------------------------------
    # Message-based rendering (for auto-advance, no interaction needed)
    # ------------------------------------------------------------------

    async def _render_scene_via_msg(self, engine: FinaleEngine):
        """Render scene by editing engine.message directly."""
        if not engine.message:
            return

        buf = engine.render_current()
        file = discord.File(fp=buf, filename="scene.png")
        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url="attachment://scene.png")

        is_auto = engine.get_auto_advance_delay() > 0

        if engine.is_in_cutscene():
            view = FinaleDialogView(engine, self._on_dialog_advance)
        elif engine.is_in_battle():
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance, is_auto=is_auto)

        try:
            await engine.message.edit(embed=embed, view=view, attachments=[file])
        except Exception:
            pass

        await self._schedule_auto_advance(engine)

    async def _handle_finale_complete_via_msg(self, engine: FinaleEngine):
        """Handle finale completion via message edit (no interaction)."""
        if not engine.message:
            return

        finale_scene = engine.get_finale_scene()
        if finale_scene:
            text = " ".join(finale_scene.text) if finale_scene.text else "Congratulations!"
            img = engine.renderer.render_finale(
                title=finale_scene.title, text=text,
                background=finale_scene.background, trainer_name=engine.trainer_name
            )
        else:
            img = engine.renderer.render_finale(
                title="Champion", text="Congratulations!",
                trainer_name=engine.trainer_name
            )

        file_buf = engine.renderer.to_discord_file(img, "finale.png")
        file = discord.File(fp=file_buf, filename="finale.png")
        embed = discord.Embed(color=discord.Color.gold())
        embed.set_image(url="attachment://finale.png")

        user_id = engine.user_id
        if user_id in self.__finale_engines:
            del self.__finale_engines[user_id]

        try:
            await engine.message.edit(embed=embed, view=View(), attachments=[file])
        except Exception:
            pass

    async def _handle_finale_defeat_via_msg(self, engine: FinaleEngine):
        """Handle player defeat via message edit."""
        engine.end_battle(victory=False)

        if not engine.message:
            return

        img = engine.renderer.render_transition(text="You have been defeated...")
        file_buf = engine.renderer.to_discord_file(img, "defeat.png")
        file = discord.File(fp=file_buf, filename="defeat.png")

        embed = discord.Embed(color=discord.Color.dark_red())
        embed.set_image(url="attachment://defeat.png")
        embed.set_footer(text="Don't give up!")

        view = FinaleDefeatView(
            engine,
            retry_callback=self._on_retry,
            quit_callback=self._on_quit
        )

        try:
            await engine.message.edit(embed=embed, view=view, attachments=[file])
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Switch Pokemon
    # ------------------------------------------------------------------

    async def _on_switch_request(self, interaction: Interaction):
        """Show the switch Pokemon selection."""
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine or not engine.battle_state:
            return

        engine.cancel_auto_advance()
        engine.message = interaction.message

        view = FinaleSwitchView(engine, self._on_switch_confirm, self._on_switch_cancel)

        buf = engine.render_current()
        file = discord.File(fp=buf, filename="battle.png")

        embed = discord.Embed(
            title="Switch Pokemon",
            description="Choose a Pokemon to switch to:",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://battle.png")

        await interaction.message.edit(embed=embed, view=view, attachments=[file])

    async def _on_switch_confirm(self, interaction: Interaction, party_index: int):
        """Confirm Pokemon switch during finale battle."""
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine or not engine.battle_state:
            return

        engine.message = interaction.message
        bs = engine.battle_state
        old_name = bs.player_pokemon.pokemonName.capitalize()
        bs.player_current_index = party_index
        bs.player_pokemon = bs.player_party[party_index]
        new_name = bs.player_pokemon.pokemonName.capitalize()

        bs.battle_log = [f"Come back, {old_name}!", f"Go, {new_name}!"]

        # Enemy gets a free attack on switch
        enemy_poke = bs.enemy_pokemon
        if enemy_poke and enemy_poke.currentHP > 0:
            enemy_moves = enemy_poke.getMoves() if hasattr(enemy_poke, 'getMoves') else []
            enemy_moves = [m for m in enemy_moves if m and m.lower() != 'none']
            if enemy_moves:
                import random
                from helpers.pathhelpers import load_json_config
                moves_config = load_json_config('moves.json')
                type_effectiveness = load_json_config('typeEffectiveness.json')
                if hasattr(enemy_poke, 'getMovesConfig'):
                    moves_config.update(enemy_poke.getMovesConfig())

                e_move_name = random.choice(enemy_moves)
                e_move_data = {}
                if hasattr(enemy_poke, 'getMoveData'):
                    e_move_data = enemy_poke.getMoveData(e_move_name)
                e_display = e_move_data.get('displayName', e_move_name.replace('-', ' ').title())

                e_damage, e_hit = calculate_battle_damage(
                    enemy_poke, bs.player_pokemon, e_move_name, moves_config, type_effectiveness
                )
                if e_hit and e_damage > 0:
                    bs.player_pokemon.currentHP = max(0, bs.player_pokemon.currentHP - e_damage)
                    bs.battle_log.append(f"{enemy_poke.pokemonName} used {e_display}! (-{e_damage} HP)")

        bs.turn_number += 1
        await self._render_battle_frame(interaction, engine)

    async def _on_switch_cancel(self, interaction: Interaction):
        """Cancel switch and go back to battle view."""
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if engine:
            engine.message = interaction.message
            await self._render_battle_frame(interaction, engine)

    # ------------------------------------------------------------------
    # Defeat / Victory / Completion (interaction-based)
    # ------------------------------------------------------------------

    async def _handle_finale_defeat(self, interaction: Interaction, engine: FinaleEngine):
        """Handle player losing the finale battle (from interaction)."""
        engine.end_battle(victory=False)

        img = engine.renderer.render_transition(text="You have been defeated...")
        file_buf = engine.renderer.to_discord_file(img, "defeat.png")
        file = discord.File(fp=file_buf, filename="defeat.png")

        embed = discord.Embed(color=discord.Color.dark_red())
        embed.set_image(url="attachment://defeat.png")
        embed.set_footer(text="Don't give up!")

        view = FinaleDefeatView(
            engine,
            retry_callback=self._on_retry,
            quit_callback=self._on_quit
        )
        await interaction.message.edit(embed=embed, view=view, attachments=[file])

    async def _handle_finale_complete(self, interaction: Interaction, engine: FinaleEngine):
        """Handle the finale being completed successfully (from interaction)."""
        user_id = engine.user_id

        finale_scene = engine.get_finale_scene()
        if finale_scene:
            text = " ".join(finale_scene.text) if finale_scene.text else "Congratulations!"
            img = engine.renderer.render_finale(
                title=finale_scene.title, text=text,
                background=finale_scene.background, trainer_name=engine.trainer_name
            )
        else:
            img = engine.renderer.render_finale(
                title="Champion", text="Congratulations!",
                trainer_name=engine.trainer_name
            )

        file_buf = engine.renderer.to_discord_file(img, "finale.png")
        file = discord.File(fp=file_buf, filename="finale.png")

        embed = discord.Embed(color=discord.Color.gold())
        embed.set_image(url="attachment://finale.png")

        if user_id in self.__finale_engines:
            del self.__finale_engines[user_id]

        await interaction.message.edit(embed=embed, view=View(), attachments=[file])

    async def _on_retry(self, interaction: Interaction):
        """Retry the finale from the beginning."""
        user_id = str(interaction.user.id)

        if user_id in self.__finale_engines:
            del self.__finale_engines[user_id]

        trainer = TrainerClass(user_id)
        trainer_name = trainer.getTrainerName() if hasattr(trainer, 'getTrainerName') else interaction.user.display_name

        party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
            if poke.currentHP > 0:
                alive_party.append(poke)

        if not alive_party:
            img = FinaleEngine(user_id, "", [], []).renderer.render_transition(
                text="All your Pokemon have fainted! Heal up first."
            )
            buf = FinaleEngine(user_id, "", [], []).renderer.to_discord_file(img)
            file = discord.File(fp=buf, filename="scene.png")
            embed = discord.Embed(color=discord.Color.dark_red())
            embed.set_image(url="attachment://scene.png")
            await interaction.message.edit(embed=embed, view=View(), attachments=[file])
            return

        script = get_finale_script()
        engine = FinaleEngine(user_id, trainer_name or interaction.user.display_name, alive_party, script)
        self.__finale_engines[user_id] = engine
        engine.message = interaction.message

        buf = engine.render_current()
        file = discord.File(fp=buf, filename="scene.png")
        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url="attachment://scene.png")
        embed.set_footer(text=f"{interaction.user.display_name}'s Finale")

        is_auto = engine.get_auto_advance_delay() > 0
        view = FinaleDialogView(engine, self._on_dialog_advance, is_auto=is_auto)
        await interaction.message.edit(embed=embed, view=view, attachments=[file])

        await self._schedule_auto_advance(engine)

    async def _on_quit(self, interaction: Interaction):
        """Quit the finale."""
        user_id = str(interaction.user.id)
        if user_id in self.__finale_engines:
            self.__finale_engines[user_id].cancel_auto_advance()
            del self.__finale_engines[user_id]

        embed = discord.Embed(
            title="Finale Abandoned",
            description="You can return anytime with `,finale`",
            color=discord.Color.greyple()
        )
        await interaction.message.edit(embed=embed, view=View(), attachments=[])