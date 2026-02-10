"""
FinaleMixin — Cog mixin for the cinematic finale system.

Provides the ,finale command and wires up the FinaleEngine
with Discord interaction callbacks for dialog, battles, and cutscenes.
"""
from __future__ import annotations
import asyncio
from io import BytesIO
from typing import Dict, Union, TYPE_CHECKING

import discord
from discord import Interaction
from redbot.core import commands

from .abcd import MixinMeta
from .finale.engine import FinaleEngine
from .finale.script import get_finale_script
from .finale.views import (
    FinaleDialogView, FinaleBattleView,
    FinaleSwitchView, FinaleDefeatView
)
from .finale.scenes import BattleStartScene, FinaleScene

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

    # Active finale sessions keyed by user_id string
    __finale_engines: Dict[str, FinaleEngine] = {}

    # ------------------------------------------------------------------
    # Command
    # ------------------------------------------------------------------

    @commands.command(name="finale")
    @commands.guild_only()
    async def finale_command(self, ctx: commands.Context) -> None:
        """Begin the cinematic finale — the ultimate battle awaits."""
        user = ctx.author
        user_id = str(user.id)

        # Prevent double-start
        if user_id in self.__finale_engines:
            await ctx.send("You're already in the finale! Finish or let it time out first.", ephemeral=True)
            return

        # Load trainer and party
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

        # Create the engine
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

        view = FinaleDialogView(engine, self._on_dialog_advance)
        message = await ctx.send(embed=embed, view=view, file=file)

    # ------------------------------------------------------------------
    # Dialog advance callback
    # ------------------------------------------------------------------

    async def _on_dialog_advance(self, interaction: Interaction, result: str):
        """Called by FinaleDialogView when 'Next' is pressed."""
        user = interaction.user
        user_id = str(user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine:
            return

        if result == "start_battle":
            await self._start_finale_battle(interaction, engine)
        elif result == "resume_battle":
            await self._render_battle_frame(interaction, engine)
        elif result == "complete":
            await self._handle_finale_complete(interaction, engine)
        else:
            # next_page or next_scene — just re-render
            await self._render_scene_frame(interaction, engine)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    async def _render_scene_frame(self, interaction: Interaction, engine: FinaleEngine):
        """Re-render current scene and update the message."""
        buf = engine.render_current()
        file = discord.File(fp=buf, filename="scene.png")

        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url="attachment://scene.png")
        embed.set_footer(text=f"{interaction.user.display_name}'s Finale")

        # Pick the right view based on engine state
        if engine.is_in_cutscene():
            view = FinaleDialogView(engine, self._on_dialog_advance)
        elif engine.is_in_battle():
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance)

        await interaction.edit_original_response(embed=embed, view=view, attachments=[file])

    async def _render_battle_frame(self, interaction: Interaction, engine: FinaleEngine):
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

        view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        await interaction.edit_original_response(embed=embed, view=view, attachments=[file])

    # ------------------------------------------------------------------
    # Battle initialization
    # ------------------------------------------------------------------

    async def _start_finale_battle(self, interaction: Interaction, engine: FinaleEngine):
        """Initialize a battle from a BattleStartScene."""
        engine.start_battle(self._create_finale_enemy)
        await self._render_battle_frame(interaction, engine)

    def _create_finale_enemy(self, pokemon_data: dict, player_discord_id: str) -> PokemonClass:
        """Create an enemy Pokemon for a finale battle. Same pattern as encounters."""
        enemy_name = list(pokemon_data.keys())[0]
        enemy_level = pokemon_data[enemy_name]

        enemy_pokemon = PokemonClass(player_discord_id, enemy_name)
        enemy_pokemon.create(enemy_level)
        enemy_pokemon.discordId = None  # Don't save to player's DB

        # Register in pokedex
        PokedexClass(player_discord_id, enemy_pokemon)

        return enemy_pokemon

    # ------------------------------------------------------------------
    # Battle move callback
    # ------------------------------------------------------------------

    async def _on_battle_move(self, interaction: Interaction, move_index: int):
        """Process a player's move selection during finale battle."""
        user = interaction.user
        user_id = str(user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine or not engine.battle_state:
            return

        bs = engine.battle_state
        player_poke = bs.player_pokemon
        enemy_poke = bs.enemy_pokemon
        log_lines = []

        # Load move configs
        from helpers.pathhelpers import load_json_config
        try:
            moves_config = load_json_config('moves.json')
        except Exception:
            moves_config = {}

        # getMoves() returns list of move name strings
        moves = player_poke.getMoves() if hasattr(player_poke, 'getMoves') else []
        if move_index >= len(moves):
            move_index = 0

        player_move_name = moves[move_index]
        player_move_data = moves_config.get(player_move_name, {})
        display_name = player_move_name.replace('-', ' ').title()

        # --- Player attacks ---
        p_damage, p_hit = calculate_battle_damage(player_poke, enemy_poke, player_move_data)

        if p_hit:
            enemy_poke.currentHP = max(0, enemy_poke.currentHP - p_damage)
            log_lines.append(f"Your {player_poke.pokemonName.capitalize()} used {display_name}! (-{p_damage} HP)")
        else:
            log_lines.append(f"Your {player_poke.pokemonName.capitalize()} used {display_name}... but it missed!")

        # Check if enemy fainted
        if enemy_poke.currentHP <= 0:
            bs.defeated_enemies.append(enemy_poke.pokemonName)
            log_lines.append(f"Enemy {enemy_poke.pokemonName.capitalize()} fainted!")

            # Check for next enemy Pokemon
            next_data = bs.get_next_enemy()
            if next_data:
                next_enemy = self._create_finale_enemy(next_data, user_id)
                bs.enemy_pokemon = next_enemy
                log_lines.append(f"{bs.enemy_name} sent out {next_enemy.pokemonName.capitalize()}!")
            else:
                # Battle won!
                bs.battle_log = log_lines
                result = engine.end_battle(victory=True)

                lb = LeaderboardClass(user_id)
                lb.victory()
                lb.actions()

                if result == "complete":
                    await self._handle_finale_complete(interaction, engine)
                else:
                    await self._render_scene_frame(interaction, engine)
                return

        # --- Enemy attacks (if still alive) ---
        if enemy_poke.currentHP > 0:
            enemy_moves = enemy_poke.getMoves() if hasattr(enemy_poke, 'getMoves') else []
            # Filter out None/empty moves
            enemy_moves = [m for m in enemy_moves if m and m.lower() != 'none']
            if enemy_moves:
                import random
                e_move_name = random.choice(enemy_moves)
                e_move_data = moves_config.get(e_move_name, {})
                e_display = e_move_name.replace('-', ' ').title()
                e_damage, e_hit = calculate_battle_damage(enemy_poke, player_poke, e_move_data)

                if e_hit:
                    player_poke.currentHP = max(0, player_poke.currentHP - e_damage)
                    log_lines.append(f"Enemy {enemy_poke.pokemonName.capitalize()} used {e_display}! (-{e_damage} HP)")
                else:
                    log_lines.append(f"Enemy {enemy_poke.pokemonName.capitalize()}'s {e_display} missed!")

        bs.battle_log = log_lines
        bs.turn_number += 1

        # Check player fainted
        if player_poke.currentHP <= 0:
            player_poke.save()
            next_poke = bs.get_next_player_pokemon()
            if next_poke:
                log_lines.append(f"Your {player_poke.pokemonName.capitalize()} fainted!")
                log_lines.append(f"Go, {next_poke.pokemonName.capitalize()}!")
                bs.battle_log = log_lines
                await self._render_battle_frame(interaction, engine)
                return
            else:
                bs.battle_log = log_lines
                await self._handle_finale_defeat(interaction, engine)
                return

        # Check cutscene triggers
        cutscene = engine.check_cutscene_triggers()
        if cutscene:
            await self._render_scene_frame(interaction, engine)
            return

        player_poke.save()
        await self._render_battle_frame(interaction, engine)

    # ------------------------------------------------------------------
    # Switch Pokemon
    # ------------------------------------------------------------------

    async def _on_switch_request(self, interaction: Interaction):
        """Show the switch Pokemon selection."""
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine or not engine.battle_state:
            return

        view = FinaleSwitchView(engine, self._on_switch_confirm, self._on_switch_cancel)

        buf = engine.render_current()
        file = discord.File(fp=buf, filename="battle.png")

        embed = discord.Embed(
            title="Switch Pokemon",
            description="Choose a Pokemon to switch to:",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://battle.png")

        await interaction.edit_original_response(embed=embed, view=view, attachments=[file])

    async def _on_switch_confirm(self, interaction: Interaction, party_index: int):
        """Confirm Pokemon switch during finale battle."""
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine or not engine.battle_state:
            return

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
            if enemy_moves:
                import random
                e_move = random.choice(enemy_moves)
                e_damage, e_hit = calculate_battle_damage(enemy_poke, bs.player_pokemon, e_move)
                e_move_name = e_move.get('name', e_move.get('moveName', 'Attack'))
                if e_hit:
                    bs.player_pokemon.currentHP = max(0, bs.player_pokemon.currentHP - e_damage)
                    bs.battle_log.append(f"Enemy {enemy_poke.pokemonName.capitalize()} used {e_move_name.capitalize()}! (-{e_damage} HP)")

        bs.turn_number += 1
        await self._render_battle_frame(interaction, engine)

    async def _on_switch_cancel(self, interaction: Interaction):
        """Cancel switch and go back to battle view."""
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if engine:
            await self._render_battle_frame(interaction, engine)

    # ------------------------------------------------------------------
    # Defeat / Victory / Completion
    # ------------------------------------------------------------------

    async def _handle_finale_defeat(self, interaction: Interaction, engine: FinaleEngine):
        """Handle player losing the finale battle."""
        engine.end_battle(victory=False)

        buf = engine.renderer.render_transition(text="You have been defeated...")
        file = discord.File(fp=BytesIO(buf.read() if hasattr(buf, 'read') else buf), filename="defeat.png")
        # Re-render properly
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
        await interaction.edit_original_response(embed=embed, view=view, attachments=[file])

    async def _handle_finale_complete(self, interaction: Interaction, engine: FinaleEngine):
        """Handle the finale being completed successfully."""
        user_id = engine.user_id

        # Render the finale scene
        finale_scene = engine.get_finale_scene()
        if finale_scene:
            text = " ".join(finale_scene.text) if finale_scene.text else "Congratulations!"
            img = engine.renderer.render_finale(
                title=finale_scene.title,
                text=text,
                background=finale_scene.background,
                trainer_name=engine.trainer_name
            )
        else:
            img = engine.renderer.render_finale(
                title="🏆 Champion 🏆",
                text="Congratulations!",
                trainer_name=engine.trainer_name
            )

        file_buf = engine.renderer.to_discord_file(img, "finale.png")
        file = discord.File(fp=file_buf, filename="finale.png")

        embed = discord.Embed(color=discord.Color.gold())
        embed.set_image(url="attachment://finale.png")

        # TODO: Apply awards to database (badges, key items, etc.)
        # if finale_scene and finale_scene.awards:
        #     self._apply_awards(user_id, finale_scene.awards)

        # Clean up
        if user_id in self.__finale_engines:
            del self.__finale_engines[user_id]

        # Disable all buttons
        view = View()
        await interaction.edit_original_response(embed=embed, view=view, attachments=[file])

    async def _on_retry(self, interaction: Interaction):
        """Retry the finale from the beginning."""
        user_id = str(interaction.user.id)

        # Clean up old engine
        if user_id in self.__finale_engines:
            del self.__finale_engines[user_id]

        # Restart — rebuild engine with fresh script
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
            await interaction.edit_original_response(embed=embed, view=View(), attachments=[file])
            return

        script = get_finale_script()
        engine = FinaleEngine(user_id, trainer_name or interaction.user.display_name, alive_party, script)
        self.__finale_engines[user_id] = engine

        buf = engine.render_current()
        file = discord.File(fp=buf, filename="scene.png")

        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url="attachment://scene.png")
        embed.set_footer(text=f"{interaction.user.display_name}'s Finale")

        view = FinaleDialogView(engine, self._on_dialog_advance)
        await interaction.edit_original_response(embed=embed, view=view, attachments=[file])

    async def _on_quit(self, interaction: Interaction):
        """Quit the finale."""
        user_id = str(interaction.user.id)
        if user_id in self.__finale_engines:
            del self.__finale_engines[user_id]

        embed = discord.Embed(
            title="Finale Abandoned",
            description="You can return anytime with `,finale`",
            color=discord.Color.greyple()
        )
        await interaction.edit_original_response(embed=embed, view=View(), attachments=[])