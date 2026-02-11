"""
FinaleMixin — Cog mixin for the cinematic finale system.
"""
from __future__ import annotations
import asyncio
import random
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
from .finale.audio import FinaleAudioManager
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


class FinaleReadyView(View):
    """Pre-finale confirmation view."""
    def __init__(self, mixin: 'FinaleMixin', user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.mixin = mixin
        self.user_id = user_id

        yes_btn = discord.ui.Button(style=discord.ButtonStyle.success, label="Yes, I'm ready!", custom_id="finale_ready_yes")
        yes_btn.callback = self.on_yes
        self.add_item(yes_btn)

        later_btn = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Maybe later", custom_id="finale_ready_later")
        later_btn.callback = self.on_later
        self.add_item(later_btn)

    async def on_yes(self, interaction: Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't for you.", ephemeral=True)
            return

        # Check if user is in a voice channel
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not member.voice or not member.voice.channel:
            await interaction.response.send_message(
                "I see you're not in a voice channel. Please join one before starting the finale!",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        await self.mixin._begin_finale(interaction)

    async def on_later(self, interaction: Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't for you.", ephemeral=True)
            return
        await interaction.response.defer()
        embed = discord.Embed(
            title="No worries!",
            description="Come back anytime with `,finale` when you're ready.",
            color=discord.Color.greyple()
        )
        await interaction.message.edit(embed=embed, view=View(), attachments=[])

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class FinaleMixin(MixinMeta):
    """Cinematic finale battle system."""

    __finale_engines: Dict[str, FinaleEngine] = {}
    __finale_pokemon_config: dict = None

    def _get_finale_pokemon_config(self) -> dict:
        if self.__finale_pokemon_config is None:
            self.__finale_pokemon_config = load_finale_pokemon_config()
        return self.__finale_pokemon_config

    async def _safe_edit(self, message: discord.Message, **kwargs) -> bool:
        for attempt in range(3):
            try:
                await message.edit(**kwargs)
                return True
            except discord.DiscordServerError:
                if attempt < 2:
                    await asyncio.sleep(1 + attempt)
                else:
                    print("[Finale] Message edit failed after 3 attempts")
                    return False
            except discord.NotFound:
                return False
            except Exception as e:
                print(f"[Finale] Unexpected edit error: {e}")
                return False
        return False

    # ------------------------------------------------------------------
    # Command
    # ------------------------------------------------------------------

    @commands.command(name="finale")
    @commands.guild_only()
    async def finale_command(self, ctx: commands.Context) -> None:
        """Begin the cinematic finale."""
        user = ctx.author
        user_id = str(user.id)

        if user_id in self.__finale_engines:
            await ctx.send("You're already in the finale! Finish or let it time out first.")
            return

        embed = discord.Embed(
            title="The Finale Awaits...",
            description=(
                "Before we begin, a few things to know:\n\n"
                "**Estimated Time:** 10-15 minutes\n\n"
                "**Voice Channel Required:** Please be at a computer and "
                "join a Voice Channel before starting.\n\n"
                "**Stay Active:** Don't delay too long between actions "
                "or the session may time out.\n\n"
                "**Battle Ready:** There is no need to heal "
                "all your pokemon are in fighting shape.\n\n"
                "When you're ready, the ultimate challenge begins."
            ),
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text="Are you ready to begin?")

        view = FinaleReadyView(self, user_id)
        await ctx.send(embed=embed, view=view)


    @commands.command(name="finaleact")
    @commands.guild_only()
    @commands.is_owner()
    async def finale_act_command(self, ctx: commands.Context, act: int = 1) -> None:
        """[ADMIN] Start finale at a specific act number.
        
        Acts: 1=Encounter, 2=Vaporeon, 3=DragonDeez, 4=TittyPussy,
        5=AngelHernandez, 6=AbigailShapiro, 7=Unwinnable, 8=RiggedWin,
        9=SkippyRage, 10=FinalSkippy, 11=PostSkippy, 12=Melkor, 13=Ending
        """
        user = ctx.author
        user_id = str(user.id)

        if user_id in self.__finale_engines:
            self.__finale_engines[user_id].cancel_auto_advance()
            del self.__finale_engines[user_id]

        # Clear config cache so changes are picked up
        self.__finale_pokemon_config = None

        trainer = TrainerClass(user_id)
        trainer_name = trainer.getTrainerName() if hasattr(trainer, 'getTrainerName') else user.display_name

        party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
            stats = poke.getPokeStats()
            poke.currentHP = stats['hp']
            poke.discordId = str(user.id)
            poke.save()
            alive_party.append(poke)

        if not alive_party:
            await ctx.send("You don't have any Pokemon!")
            return

        alive_party.sort(key=lambda p: p.currentLevel)

        script = get_finale_script()
        engine = FinaleEngine(
            user_id=user_id,
            trainer_name=trainer_name if trainer_name else user.display_name,
            player_party=alive_party,
            script=script
        )

        # Map act numbers to scene indices
        act_map = self._get_act_map(engine.script)
        if act not in act_map:
            acts_list = ", ".join(f"{k}={v}" for k, v in sorted(act_map.items()))
            await ctx.send(f"Invalid act number. Available: {acts_list}")
            return

        engine.scene_index = act_map[act]
        engine.dialog_page_index = 0
        self.__finale_engines[user_id] = engine

        fname = engine.next_frame_name("scene")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url=f"attachment://{fname}")
        embed.set_footer(text=f"{user.display_name}'s Finale (Act {act})")

        if engine.get_auto_advance_delay() > 0:
            view = View()
        else:
            scene = engine.get_current_scene()
            if isinstance(scene, BattleStartScene):
                engine.start_battle(self._create_finale_enemy_from_config)
                self._setup_battle_party(engine)
                view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
            else:
                view = FinaleDialogView(engine, self._on_dialog_advance)

        message = await ctx.send(embed=embed, view=view, file=file)
        engine.message = message

        await self._try_connect_finale_audio(ctx.author, engine)
        engine.trigger_scene_audio()

        await self._schedule_auto_advance(engine)

    async def _begin_finale(self, interaction: Interaction):
        """Actually start the finale after the player confirms."""
        user = interaction.user
        user_id = str(user.id)

        # Audio will be connected after engine is created

        trainer = TrainerClass(user_id)
        trainer_name = trainer.getTrainerName() if hasattr(trainer, 'getTrainerName') else user.display_name

        party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
            stats = poke.getPokeStats()
            poke.currentHP = stats['hp']
            poke.discordId = str(user.id)
            poke.save()
            alive_party.append(poke)

        if not alive_party:
            await interaction.followup.send("You don't have any Pokemon!")
            return

        alive_party.sort(key=lambda p: p.currentLevel)

        script = get_finale_script()
        engine = FinaleEngine(
            user_id=user_id,
            trainer_name=trainer_name if trainer_name else user.display_name,
            player_party=alive_party,
            script=script
        )
        self.__finale_engines[user_id] = engine

        fname = engine.next_frame_name("scene")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url=f"attachment://{fname}")
        embed.set_footer(text=f"{user.display_name}'s Finale")

        if engine.get_auto_advance_delay() > 0:
            view = View()
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance)

        message = await interaction.message.edit(embed=embed, view=view, attachments=[file])
        engine.message = interaction.message
        await self._try_connect_finale_audio(interaction.guild.get_member(user.id), engine)
        engine.trigger_scene_audio()

    async def _leave_voice(self, engine: FinaleEngine):
        """Disconnect bot from voice channel."""
        try:
            if engine.message and engine.message.guild and engine.message.guild.voice_client:
                await engine.message.guild.voice_client.disconnect()
        except Exception:
            pass

    def _get_act_map(self, script) -> dict:
        """Build a mapping of act numbers to scene indices by scanning comments/structure."""
        # We define acts by hand to match the script structure
        act_map = {1: 0}  # Act 1 always starts at 0
        
        act_markers = {
            "Vaporeon": 2,
            "DragonDeez": 3,
            "Titty Pussy": 4,
            "Angel Hernandez": 5,
            "Abigail Shapiro": 6,
            "skippy_unwinnable": 7,
            "skippy_rigged": 8,
            "Whhaaa": 9,
            "skippy_final": 10,
            "This is outrageous": 11,
            "melkor": 12,
            "Wow you": 13,
        }

        for i, scene in enumerate(script):
            for marker, act_num in act_markers.items():
                if act_num in act_map:
                    continue
                    
                # Check dialog text
                if hasattr(scene, 'text') and scene.text:
                    for t in (scene.text if isinstance(scene.text, list) else [scene.text]):
                        if marker in str(t):
                            act_map[act_num] = i
                            break

                # Check battle_id
                if hasattr(scene, 'battle_id') and marker == scene.battle_id:
                    act_map[act_num] = i

                # Check speaker
                if hasattr(scene, 'speaker') and marker in str(getattr(scene, 'speaker', '')):
                    act_map[act_num] = i

        return act_map

    # ------------------------------------------------------------------
    # Auto-advance
    # ------------------------------------------------------------------

    async def _schedule_auto_advance(self, engine: FinaleEngine):
        delay = engine.get_auto_advance_delay()
        if delay <= 0 or not engine.message:
            return
        engine._advance_id += 1
        current_id = engine._advance_id

        async def _auto_task():
            await asyncio.sleep(delay)
            if engine._advance_id != current_id or engine.is_complete:
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
        if not engine.message:
            return
        engine.trigger_scene_audio()
        fname = engine.next_frame_name("scene")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url=f"attachment://{fname}")

        if engine.is_in_battle():
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        elif engine.get_auto_advance_delay() > 0:
            view = View()
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance)

        try:
            await engine.message.edit(embed=embed, view=view, attachments=[file])
        except Exception as e:
            print(f"[Finale] auto_render_scene edit failed: {e}")
        await self._schedule_auto_advance(engine)

    async def _auto_start_battle(self, engine: FinaleEngine):
        engine.start_battle(self._create_finale_enemy_from_config)
        self._setup_battle_party(engine)
        engine.trigger_scene_audio()
        if not engine.message:
            return
        fname = engine.next_frame_name("battle")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.red())
        embed.set_image(url=f"attachment://{fname}")
        view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        try:
            await engine.message.edit(embed=embed, view=view, attachments=[file])
        except Exception as e:
            print(f"[Finale] auto_start_battle edit failed: {e}")

    async def _auto_handle_complete(self, engine: FinaleEngine):
        await self._handle_finale_complete_via_msg(engine)

    # ------------------------------------------------------------------
    # Dialog advance callback
    # ------------------------------------------------------------------

    async def _on_dialog_advance(self, interaction: Interaction, result: str):
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine:
            try:
                await interaction.followup.send("Finale session expired. Use `,finale` to restart.", ephemeral=True)
            except Exception:
                pass
            return
        engine.message = interaction.message

        try:
            if result == "start_battle":
                await self._start_finale_battle(interaction, engine)
            elif result == "resume_battle":
                await self._render_battle_frame(interaction, engine)
            elif result == "complete":
                await self._handle_finale_complete(interaction, engine)
            else:
                await self._render_scene_frame(interaction, engine)
        except Exception as e:
            print(f"[Finale] Error in _on_dialog_advance: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: try to render via message directly
            try:
                await self._render_scene_via_msg(engine)
            except Exception:
                try:
                    await interaction.followup.send("Something went wrong. Use `,finale` to restart.", ephemeral=True)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    async def _render_scene_frame(self, interaction: Interaction, engine: FinaleEngine):
        try:
            engine.trigger_scene_audio()
        except Exception:
            pass

        fname = engine.next_frame_name("scene")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url=f"attachment://{fname}")
        embed.set_footer(text=f"{interaction.user.display_name}'s Finale")

        if engine.is_in_cutscene():
            view = FinaleDialogView(engine, self._on_dialog_advance)
        elif engine.is_in_battle():
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        elif engine.get_auto_advance_delay() > 0:
            view = View()
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance)

        # Try editing the interaction message first
        edited = False
        try:
            await interaction.message.edit(embed=embed, view=view, attachments=[file])
            engine.message = interaction.message
            edited = True
        except Exception as e:
            print(f"[Finale] interaction.message.edit failed: {e}")

        # Fallback: try editing engine.message if different
        if not edited and engine.message and engine.message.id != interaction.message.id:
            try:
                buf2 = engine.render_current()
                fname2 = engine.next_frame_name("scene")
                file2 = discord.File(fp=buf2, filename=fname2)
                embed2 = discord.Embed(color=discord.Color.dark_purple())
                embed2.set_image(url=f"attachment://{fname2}")
                await engine.message.edit(embed=embed2, view=view, attachments=[file2])
                edited = True
            except Exception as e:
                print(f"[Finale] engine.message.edit fallback failed: {e}")

        # Last resort: send a brand new message
        if not edited:
            try:
                buf3 = engine.render_current()
                fname3 = engine.next_frame_name("scene")
                file3 = discord.File(fp=buf3, filename=fname3)
                embed3 = discord.Embed(color=discord.Color.dark_purple())
                embed3.set_image(url=f"attachment://{fname3}")
                channel = interaction.channel
                new_msg = await channel.send(embed=embed3, view=view, file=file3)
                try:
                    await interaction.message.delete()
                except Exception:
                    pass
                engine.message = new_msg
            except Exception as e:
                print(f"[Finale] new message fallback also failed: {e}")

        await self._schedule_auto_advance(engine)

    async def _render_battle_frame(self, interaction: Interaction, engine: FinaleEngine, with_buttons: bool = True):
        fname = engine.next_frame_name("battle")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.red())
        embed.set_image(url=f"attachment://{fname}")
        bs = engine.battle_state
        if bs:
            alive = sum(1 for p in bs.player_party if p.currentHP > 0)
            embed.set_footer(text=f"Your team: {alive} alive | Turn {bs.turn_number}")
        if with_buttons:
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        else:
            view = View()
        await interaction.message.edit(embed=embed, view=view, attachments=[file])
        engine.message = interaction.message

    async def _render_scene_via_msg(self, engine: FinaleEngine):
        if not engine.message:
            return

        try:
            engine.trigger_scene_audio()
        except Exception:
            pass

        fname = engine.next_frame_name("scene")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url=f"attachment://{fname}")

        if engine.is_in_cutscene():
            view = FinaleDialogView(engine, self._on_dialog_advance)
        elif engine.is_in_battle():
            view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
        elif engine.get_auto_advance_delay() > 0:
            view = View()
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance)

        edited = False
        try:
            await engine.message.edit(embed=embed, view=view, attachments=[file])
            edited = True
        except Exception as e:
            print(f"[Finale] _render_scene_via_msg edit failed: {e}")

        if not edited:
            try:
                buf2 = engine.render_current()
                fname2 = engine.next_frame_name("scene")
                file2 = discord.File(fp=buf2, filename=fname2)
                embed2 = discord.Embed(color=discord.Color.dark_purple())
                embed2.set_image(url=f"attachment://{fname2}")
                channel = engine.message.channel
                new_msg = await channel.send(embed=embed2, view=view, file=file2)
                try:
                    await engine.message.delete()
                except Exception:
                    pass
                engine.message = new_msg
            except Exception as e:
                print(f"[Finale] _render_scene_via_msg fallback also failed: {e}")

        await self._schedule_auto_advance(engine)

    # ------------------------------------------------------------------
    # Battle initialization
    # ------------------------------------------------------------------

    async def _start_finale_battle(self, interaction: Interaction, engine: FinaleEngine):
        engine.start_battle(self._create_finale_enemy_from_config)
        self._setup_battle_party(engine)
        engine.trigger_scene_audio()
        await self._render_battle_frame(interaction, engine)

    def _setup_battle_party(self, engine: FinaleEngine):
        """Adjust the battle state party based on battle_mode."""
        bs = engine.battle_state
        if not bs:
            return

        if bs.battle_mode == "unwinnable":
            # Use all pokemon except the last (highest level, saved for later)
            if len(engine.player_party) > 1:
                bs.player_party = list(engine.player_party[:-1])
            else:
                bs.player_party = list(engine.player_party)
            bs.player_pokemon = bs.player_party[0]
            bs.player_current_index = 0

        elif bs.battle_mode in ("rigged_win", "final_skippy", "melkor"):
            # Use only the last pokemon (highest level), fully healed
            last_poke = engine.player_party[-1]
            stats = last_poke.getPokeStats()
            last_poke.currentHP = stats['hp']
            bs.player_party = [last_poke]
            bs.player_pokemon = last_poke
            bs.player_current_index = 0

    def _create_finale_enemy_from_config(self, pokemon_data: dict, player_discord_id: str):
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
        enemy_pokemon = PokemonClass(player_discord_id, name)
        enemy_pokemon.create(level)
        enemy_pokemon.discordId = None
        PokedexClass(player_discord_id, enemy_pokemon)
        return enemy_pokemon

    # ------------------------------------------------------------------
    # Battle move — dispatch by mode
    # ------------------------------------------------------------------

    async def _on_battle_move(self, interaction: Interaction, move_index: int):
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine:
            try:
                await interaction.followup.send("Finale session expired.", ephemeral=True)
            except Exception:
                pass
            return
        if not engine.battle_state:
            # Battle ended but old view is still showing — re-render current scene
            engine.message = interaction.message
            try:
                await self._render_scene_frame(interaction, engine)
            except Exception:
                pass
            return

        engine.cancel_auto_advance()
        engine.message = interaction.message
        mode = engine.battle_state.battle_mode

        if mode == "unwinnable":
            await self._handle_unwinnable_turn(interaction, engine, move_index)
        elif mode == "rigged_win":
            await self._handle_rigged_win_turn(interaction, engine, move_index)
        elif mode == "final_skippy":
            await self._handle_final_skippy_turn(interaction, engine, move_index)
        elif mode == "melkor":
            await self._handle_melkor_turn(interaction, engine, move_index)
        else:
            await self._handle_normal_turn(interaction, engine, move_index)

    # ------------------------------------------------------------------
    # UNWINNABLE: Player attacks do nothing, Skippy one-shots
    # ------------------------------------------------------------------

    async def _handle_unwinnable_turn(self, interaction: Interaction, engine: FinaleEngine, move_index: int):
        bs = engine.battle_state
        player_poke = bs.player_pokemon
        enemy_poke = bs.enemy_pokemon
        msg = interaction.message

        moves = player_poke.getMoves() if hasattr(player_poke, 'getMoves') else []
        if move_index < len(moves):
            move_name = moves[move_index].replace('-', ' ').title()
        else:
            move_name = "Attack"

        # Step 1: Player attack does nothing
        bs.battle_log = [f"Your {player_poke.pokemonName.capitalize()} used {move_name}!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        bs.battle_log = ["This attack cannot hurt Skippy!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        # Step 2: Skippy attacks and one-shots
        enemy_moves = enemy_poke.getMoves() if hasattr(enemy_poke, 'getMoves') else []
        e_move_name = random.choice(enemy_moves) if enemy_moves else "Attack"
        e_move_data = enemy_poke.getMoveData(e_move_name) if hasattr(enemy_poke, 'getMoveData') else {}
        e_display = e_move_data.get('displayName', e_move_name.replace('-', ' ').title())
        status = e_move_data.get('statusEffect')

        bs.battle_log = [f"Skippy uses {e_display}!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        if status:
            bs.battle_log = [status]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

        # One-shot the player's pokemon
        player_poke.currentHP = 0
        player_poke.save()

        bs.battle_log = [f"Your {player_poke.pokemonName.capitalize()} fainted!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        # Check for next pokemon (excluding last/highest)
        next_poke = bs.get_next_player_pokemon()
        if next_poke:
            bs.battle_log = [f"Go, {next_poke.pokemonName.capitalize()}!"]
            bs.turn_number += 1
            await self._safe_edit_battle_with_buttons(msg, engine)
        else:
            # All sacrificial pokemon down — end battle, advance to dialog
            engine.end_battle(victory=True)
            try:
                engine.trigger_scene_audio()
            except Exception:
                pass
            await self._render_scene_via_msg(engine)

    # ------------------------------------------------------------------
    # RIGGED WIN: Player does 10% per hit, Skippy can't hurt you
    # At 50% HP, battle ends automatically
    # ------------------------------------------------------------------

    async def _handle_rigged_win_turn(self, interaction: Interaction, engine: FinaleEngine, move_index: int):
        bs = engine.battle_state
        player_poke = bs.player_pokemon
        enemy_poke = bs.enemy_pokemon
        msg = interaction.message

        moves = player_poke.getMoves() if hasattr(player_poke, 'getMoves') else []
        if move_index < len(moves):
            move_name = moves[move_index].replace('-', ' ').title()
        else:
            move_name = "Attack"

        # Player does 10% of enemy max HP
        enemy_stats = enemy_poke.getPokeStats()
        enemy_max_hp = enemy_stats['hp']
        damage = max(1, int(enemy_max_hp * 0.10))
        enemy_poke.currentHP = max(0, enemy_poke.currentHP - damage)

        bs.battle_log = [f"Your {player_poke.pokemonName.capitalize()} used {move_name}!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        bs.battle_log = ["It's super effective!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        # Enemy attacks but is "resisted"
        enemy_moves = enemy_poke.getMoves() if hasattr(enemy_poke, 'getMoves') else []
        e_move_name = random.choice(enemy_moves) if enemy_moves else "Attack"
        e_move_data = enemy_poke.getMoveData(e_move_name) if hasattr(enemy_poke, 'getMoveData') else {}
        e_display = e_move_data.get('displayName', e_move_name.replace('-', ' ').title())

        bs.battle_log = [f"Skippy uses {e_display}!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        bs.battle_log = [f"Your last pokemon resists Skippy's attack!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        bs.turn_number += 1

        # Check HP threshold: at 50% or below, end battle
        hp_pct = (enemy_poke.currentHP / enemy_max_hp * 100) if enemy_max_hp > 0 else 0
        if hp_pct <= 50:
            engine.end_battle(victory=True)
            try:
                engine.trigger_scene_audio()
            except Exception:
                pass
            await self._render_scene_via_msg(engine)
            return

        # Check cutscene triggers (70% dialog)
        cutscene = engine.check_cutscene_triggers()
        if cutscene:
            await self._render_scene_via_msg(engine)
            return

        # Continue battle
        bs.battle_log = [f"Turn {bs.turn_number} - Choose your move!"]
        await self._safe_edit_battle_with_buttons(msg, engine)

    # ------------------------------------------------------------------
    # FINAL SKIPPY: Player does 15-30%, Skippy does 40-70%, can't die
    # ------------------------------------------------------------------

    async def _handle_final_skippy_turn(self, interaction: Interaction, engine: FinaleEngine, move_index: int):
        bs = engine.battle_state
        player_poke = bs.player_pokemon
        enemy_poke = bs.enemy_pokemon
        msg = interaction.message

        moves = player_poke.getMoves() if hasattr(player_poke, 'getMoves') else []
        if move_index < len(moves):
            move_name = moves[move_index].replace('-', ' ').title()
        else:
            move_name = "Attack"

        # Player does 15-30% of enemy max HP
        enemy_stats = enemy_poke.getPokeStats()
        enemy_max_hp = enemy_stats['hp']
        pct = random.randint(15, 30) / 100.0
        damage = max(1, int(enemy_max_hp * pct))
        enemy_poke.currentHP = max(0, enemy_poke.currentHP - damage)

        bs.battle_log = [f"Your {player_poke.pokemonName.capitalize()} used {move_name}!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        # Check enemy fainted
        if enemy_poke.currentHP <= 0:
            bs.battle_log = [f"Skippy the Magnificent fainted!"]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

            engine.end_battle(victory=True)
            lb = LeaderboardClass(str(interaction.user.id))
            lb.victory()
            lb.actions()
            try:
                engine.trigger_scene_audio()
            except Exception:
                pass
            await self._render_scene_via_msg(engine)
            return

        # Enemy does 40-70% of player max HP
        player_stats = player_poke.getPokeStats()
        player_max_hp = player_stats['hp']
        e_pct = random.randint(40, 70) / 100.0
        e_damage = max(1, int(player_max_hp * e_pct))

        enemy_moves = enemy_poke.getMoves() if hasattr(enemy_poke, 'getMoves') else []
        e_move_name = random.choice(enemy_moves) if enemy_moves else "Attack"
        e_move_data = enemy_poke.getMoveData(e_move_name) if hasattr(enemy_poke, 'getMoveData') else {}
        e_display = e_move_data.get('displayName', e_move_name.replace('-', ' ').title())
        status = e_move_data.get('statusEffect')

        player_poke.currentHP = max(0, player_poke.currentHP - e_damage)

        bs.battle_log = [f"Skippy uses {e_display}!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        if status:
            bs.battle_log = [status]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

        # If player would faint — Chodethulu heals
        if player_poke.currentHP <= 0:
            bs.battle_log = [f"Your {player_poke.pokemonName.capitalize()} is about to faint..."]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

            player_poke.currentHP = player_max_hp
            bs.battle_log = ["Chodethulu healed your Pokemon back to full health!"]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

        player_poke.save()
        bs.turn_number += 1

        bs.battle_log = [f"Turn {bs.turn_number} - Choose your move!"]
        await self._safe_edit_battle_with_buttons(msg, engine)

    # ------------------------------------------------------------------
    # MELKOR: 4 turns, small damage, then one-shot
    # ------------------------------------------------------------------

    async def _handle_melkor_turn(self, interaction: Interaction, engine: FinaleEngine, move_index: int):
        bs = engine.battle_state
        player_poke = bs.player_pokemon
        enemy_poke = bs.enemy_pokemon
        msg = interaction.message

        moves = player_poke.getMoves() if hasattr(player_poke, 'getMoves') else []
        if move_index < len(moves):
            move_name = moves[move_index].replace('-', ' ').title()
        else:
            move_name = "Attack"

        # Player does small damage (5% of max HP)
        enemy_stats = enemy_poke.getPokeStats()
        enemy_max_hp = enemy_stats['hp']
        damage = max(1, int(enemy_max_hp * 0.05))
        enemy_poke.currentHP = max(0, enemy_poke.currentHP - damage)

        bs.battle_log = [f"Your {player_poke.pokemonName.capitalize()} used {move_name}!"]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        if bs.turn_number < 4:
            # Melkor watches
            bs.battle_log = ["Melkor watches in amusement."]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

            bs.turn_number += 1
            bs.battle_log = [f"Turn {bs.turn_number} - Choose your move!"]
            await self._safe_edit_battle_with_buttons(msg, engine)
        else:
            # Turn 4: Melkor one-shots
            bs.battle_log = ["Melkor uses The Power of Chode!"]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

            bs.battle_log = ["The overwhelming power of the chode engulfs the battlefield!"]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

            player_poke.currentHP = 0
            bs.battle_log = [f"Your {player_poke.pokemonName.capitalize()} fainted!"]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

            # Heal the pokemon back so they're not stuck fainted after finale
            player_stats = player_poke.getPokeStats()
            player_poke.currentHP = player_stats['hp']
            player_poke.save()

            engine.end_battle(victory=True)
            try:
                engine.trigger_scene_audio()
            except Exception:
                pass
            await self._render_scene_via_msg(engine)

    # ------------------------------------------------------------------
    # NORMAL: Standard battle (used for DragonDeez, TittyPussy, etc.)
    # ------------------------------------------------------------------

    async def _handle_normal_turn(self, interaction: Interaction, engine: FinaleEngine, move_index: int):
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

        if hasattr(enemy_poke, 'getMovesConfig'):
            moves_config.update(enemy_poke.getMovesConfig())

        moves = player_poke.getMoves() if hasattr(player_poke, 'getMoves') else []
        if move_index >= len(moves):
            move_index = 0
        player_move_name = moves[move_index]
        display_name = player_move_name.replace('-', ' ').title()

        p_damage, p_hit = calculate_battle_damage(
            player_poke, enemy_poke, player_move_name, moves_config, type_effectiveness
        )

        # Step 1: Player attack
        if p_hit and p_damage > 0:
            enemy_poke.currentHP = max(0, enemy_poke.currentHP - p_damage)
            step1_text = f"Your {player_poke.pokemonName.capitalize()} used {display_name}!"
        elif p_hit:
            step1_text = f"Your {player_poke.pokemonName.capitalize()} used {display_name}!"
        else:
            step1_text = f"Your {player_poke.pokemonName.capitalize()} used {display_name}... but it missed!"

        bs.battle_log = [step1_text]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        # Check enemy fainted
        if enemy_poke.currentHP <= 0:
            bs.defeated_enemies.append(enemy_poke.pokemonName)
            bs.battle_log = [f"{enemy_poke.pokemonName} fainted!"]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

            next_data = bs.get_next_enemy()
            if next_data:
                next_enemy = self._create_finale_enemy_from_config(next_data, engine.user_id)
                bs.enemy_pokemon = next_enemy
                bs.battle_log = [f"Skippy sent out {next_enemy.pokemonName}!"]
                await self._safe_edit_battle_with_buttons(msg, engine)
            else:
                result = engine.end_battle(victory=True)
                lb = LeaderboardClass(engine.user_id)
                lb.victory()
                lb.actions()
                if result == "complete":
                    await self._handle_finale_complete_via_msg(engine)
                else:
                    await self._render_scene_via_msg(engine)
            return

        # Step 2: Enemy attacks
        enemy_moves = enemy_poke.getMoves() if hasattr(enemy_poke, 'getMoves') else []
        enemy_moves = [m for m in enemy_moves if m and m.lower() != 'none']
        status_effect_text = None

        if enemy_moves:
            e_move_name = random.choice(enemy_moves)
            e_move_data = enemy_poke.getMoveData(e_move_name) if hasattr(enemy_poke, 'getMoveData') else {}
            e_display = e_move_data.get('displayName', e_move_name.replace('-', ' ').title())
            status_effect_text = e_move_data.get('statusEffect')

            e_damage, e_hit = calculate_battle_damage(
                enemy_poke, player_poke, e_move_name, moves_config, type_effectiveness
            )
            if e_hit and e_damage > 0:
                player_poke.currentHP = max(0, player_poke.currentHP - e_damage)
                step2_text = f"{enemy_poke.pokemonName} used {e_display}!"
            elif e_hit:
                step2_text = f"{enemy_poke.pokemonName} used {e_display}!"
            else:
                step2_text = f"{enemy_poke.pokemonName}'s {e_display} missed!"
                status_effect_text = None
        else:
            step2_text = f"{enemy_poke.pokemonName} has no moves!"

        bs.battle_log = [step2_text]
        await self._safe_edit_battle(msg, engine)
        await asyncio.sleep(3)

        if status_effect_text:
            bs.battle_log = [status_effect_text]
            await self._safe_edit_battle(msg, engine)
            await asyncio.sleep(3)

        bs.turn_number += 1

        # Check player fainted
        if player_poke.currentHP <= 0:
            player_poke.save()
            next_poke = bs.get_next_player_pokemon()
            if next_poke:
                bs.battle_log = [f"Your {player_poke.pokemonName.capitalize()} fainted!"]
                await self._safe_edit_battle(msg, engine)
                await asyncio.sleep(3)

                bs.battle_log = [f"Go, {next_poke.pokemonName.capitalize()}!"]
                bs.turn_number += 1
                await self._safe_edit_battle_with_buttons(msg, engine)
                return
            else:
                bs.battle_log = ["All your Pokemon have fainted!"]
                await self._handle_finale_defeat_via_msg(engine)
                return

        cutscene = engine.check_cutscene_triggers()
        if cutscene:
            await self._render_scene_via_msg(engine)
            return

        player_poke.save()

        bs.battle_log = [f"Turn {bs.turn_number} - Choose your move!"]
        await self._safe_edit_battle_with_buttons(msg, engine)

    # ------------------------------------------------------------------
    # Battle edit helpers
    # ------------------------------------------------------------------

    async def _safe_edit_battle(self, msg, engine):
        """Render battle state and edit message with no buttons."""
        fname = engine.next_frame_name("battle")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.red())
        embed.set_image(url=f"attachment://{fname}")
        await self._safe_edit(msg, embed=embed, view=View(), attachments=[file])

    async def _safe_edit_battle_with_buttons(self, msg, engine):
        """Render battle state and edit message WITH move buttons (retries)."""
        for retry in range(3):
            try:
                fname = engine.next_frame_name("battle")
                buf = engine.render_current()
                file = discord.File(fp=buf, filename=fname)
                embed = discord.Embed(color=discord.Color.red())
                embed.set_image(url=f"attachment://{fname}")
                bs = engine.battle_state
                if bs:
                    alive = sum(1 for p in bs.player_party if p.currentHP > 0)
                    embed.set_footer(text=f"Your team: {alive} alive | Turn {bs.turn_number}")
                view = FinaleBattleView(engine, self._on_battle_move, self._on_switch_request)
                await msg.edit(embed=embed, view=view, attachments=[file])
                break
            except Exception as e:
                print(f"[Finale] Button edit failed (attempt {retry+1}): {e}")
                if retry < 2:
                    await asyncio.sleep(1.5)

    async def _try_connect_finale_audio(self, member: discord.Member, engine: FinaleEngine):
        """Attempt to connect audio for the finale. Non-fatal if it fails."""
        try:
            audio_mgr = FinaleAudioManager()
            connected = await audio_mgr.connect(member)
            if connected:
                engine.audio_manager = audio_mgr
                print(f"[Finale] Audio connected for {member.display_name}")
            else:
                print(f"[Finale] Audio not available (user not in voice or bot already in voice)")
        except Exception as e:
            print(f"[Finale] Audio setup failed (non-fatal): {e}")

    async def _disconnect_finale_audio(self, engine: FinaleEngine):
        """Disconnect audio for a finale engine."""
        if engine.audio_manager:
            try:
                await engine.audio_manager.disconnect()
            except Exception as e:
                print(f"[Finale] Audio disconnect error: {e}")
            engine.audio_manager = None

    # ------------------------------------------------------------------
    # Switch Pokemon
    # ------------------------------------------------------------------

    async def _on_switch_request(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if not engine or not engine.battle_state:
            return
        engine.cancel_auto_advance()
        engine.message = interaction.message

        view = FinaleSwitchView(engine, self._on_switch_confirm, self._on_switch_cancel)
        fname = engine.next_frame_name("battle")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(title="Switch Pokemon", description="Choose a Pokemon to switch to:", color=discord.Color.blue())
        embed.set_image(url=f"attachment://{fname}")
        await interaction.message.edit(embed=embed, view=view, attachments=[file])

    async def _on_switch_confirm(self, interaction: Interaction, party_index: int):
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

        enemy_poke = bs.enemy_pokemon
        if enemy_poke and enemy_poke.currentHP > 0:
            enemy_moves = enemy_poke.getMoves() if hasattr(enemy_poke, 'getMoves') else []
            enemy_moves = [m for m in enemy_moves if m and m.lower() != 'none']
            if enemy_moves:
                from helpers.pathhelpers import load_json_config
                moves_config = load_json_config('moves.json')
                type_effectiveness = load_json_config('typeEffectiveness.json')
                if hasattr(enemy_poke, 'getMovesConfig'):
                    moves_config.update(enemy_poke.getMovesConfig())
                e_move_name = random.choice(enemy_moves)
                e_move_data = enemy_poke.getMoveData(e_move_name) if hasattr(enemy_poke, 'getMoveData') else {}
                e_display = e_move_data.get('displayName', e_move_name.replace('-', ' ').title())
                e_damage, e_hit = calculate_battle_damage(
                    enemy_poke, bs.player_pokemon, e_move_name, moves_config, type_effectiveness
                )
                if e_hit and e_damage > 0:
                    bs.player_pokemon.currentHP = max(0, bs.player_pokemon.currentHP - e_damage)
                    bs.battle_log.append(f"{enemy_poke.pokemonName} used {e_display}!")
        bs.turn_number += 1
        await self._render_battle_frame(interaction, engine)

    async def _on_switch_cancel(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        engine = self.__finale_engines.get(user_id)
        if engine:
            engine.message = interaction.message
            await self._render_battle_frame(interaction, engine)

    # ------------------------------------------------------------------
    # Defeat / Victory / Completion
    # ------------------------------------------------------------------

    async def _handle_finale_defeat(self, interaction: Interaction, engine: FinaleEngine):
        engine.end_battle(victory=False)
        img = engine.renderer.render_transition(text="You have been defeated...")
        file_buf = engine.renderer.to_discord_file(img, "defeat.png")
        fname = engine.next_frame_name("defeat")
        file = discord.File(fp=file_buf, filename=fname)
        embed = discord.Embed(color=discord.Color.dark_red())
        embed.set_image(url=f"attachment://{fname}")
        embed.set_footer(text="Don't give up!")
        view = FinaleDefeatView(engine, retry_callback=self._on_retry, quit_callback=self._on_quit)
        await interaction.message.edit(embed=embed, view=view, attachments=[file])

    async def _handle_finale_defeat_via_msg(self, engine: FinaleEngine):
        engine.end_battle(victory=False)
        if not engine.message:
            return
        img = engine.renderer.render_transition(text="You have been defeated...")
        file_buf = engine.renderer.to_discord_file(img, "defeat.png")
        fname = engine.next_frame_name("defeat")
        file = discord.File(fp=file_buf, filename=fname)
        embed = discord.Embed(color=discord.Color.dark_red())
        embed.set_image(url=f"attachment://{fname}")
        embed.set_footer(text="Don't give up!")
        view = FinaleDefeatView(engine, retry_callback=self._on_retry, quit_callback=self._on_quit)
        try:
            await engine.message.edit(embed=embed, view=view, attachments=[file])
        except Exception:
            pass

    async def _handle_finale_complete(self, interaction: Interaction, engine: FinaleEngine):
        user_id = engine.user_id
        finale_scene = engine.get_finale_scene()
        if finale_scene:
            text = " ".join(finale_scene.text) if finale_scene.text else "Congratulations!"
            img = engine.renderer.render_finale(
                title=finale_scene.title, text=engine.substitute_text(text),
                background=finale_scene.background, trainer_name=engine.trainer_name
            )
        else:
            img = engine.renderer.render_finale(title="Champion", text="Congratulations!", trainer_name=engine.trainer_name)
        file_buf = engine.renderer.to_discord_file(img, "finale.png")
        fname = engine.next_frame_name("finale")
        file = discord.File(fp=file_buf, filename=fname)
        embed = discord.Embed(color=discord.Color.gold())
        embed.set_image(url=f"attachment://{fname}")
        if user_id in self.__finale_engines:
            await self._disconnect_finale_audio(self.__finale_engines[user_id])
            await self._leave_voice(engine)
            del self.__finale_engines[user_id]
        await interaction.message.edit(embed=embed, view=View(), attachments=[file])

    async def _handle_finale_complete_via_msg(self, engine: FinaleEngine):
        if not engine.message:
            return
        user_id = engine.user_id
        finale_scene = engine.get_finale_scene()
        if finale_scene:
            text = " ".join(finale_scene.text) if finale_scene.text else "Congratulations!"
            img = engine.renderer.render_finale(
                title=finale_scene.title, text=engine.substitute_text(text),
                background=finale_scene.background, trainer_name=engine.trainer_name
            )
        else:
            img = engine.renderer.render_finale(title="Champion", text="Congratulations!", trainer_name=engine.trainer_name)
        file_buf = engine.renderer.to_discord_file(img, "finale.png")
        fname = engine.next_frame_name("finale")
        file = discord.File(fp=file_buf, filename=fname)
        embed = discord.Embed(color=discord.Color.gold())
        embed.set_image(url=f"attachment://{fname}")
        if user_id in self.__finale_engines:
            await self._disconnect_finale_audio(self.__finale_engines[user_id])
            await self._leave_voice(engine)
            del self.__finale_engines[user_id]
        try:
            await engine.message.edit(embed=embed, view=View(), attachments=[file])
        except Exception:
            pass

    async def _on_retry(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if user_id in self.__finale_engines:
            self.__finale_engines[user_id].cancel_auto_advance()
            del self.__finale_engines[user_id]

        trainer = TrainerClass(user_id)
        trainer_name = trainer.getTrainerName() if hasattr(trainer, 'getTrainerName') else interaction.user.display_name
        party = trainer.getPokemon(party=True)
        alive_party = []
        for poke in party:
            poke.load(pokemonId=poke.trainerId)
            stats = poke.getPokeStats()
            poke.currentHP = stats['hp']
            poke.discordId = user_id
            poke.save()
            alive_party.append(poke)

        if not alive_party:
            img = FinaleEngine(user_id, "", [], []).renderer.render_transition(text="You don't have any Pokemon!")
            buf = FinaleEngine(user_id, "", [], []).renderer.to_discord_file(img)
            file = discord.File(fp=buf, filename="scene.png")
            embed = discord.Embed(color=discord.Color.dark_red())
            embed.set_image(url="attachment://scene.png")
            await interaction.message.edit(embed=embed, view=View(), attachments=[file])
            return

        alive_party.sort(key=lambda p: p.currentLevel)
        script = get_finale_script()
        engine = FinaleEngine(user_id, trainer_name or interaction.user.display_name, alive_party, script)
        self.__finale_engines[user_id] = engine
        engine.message = interaction.message

        fname = engine.next_frame_name("scene")
        buf = engine.render_current()
        file = discord.File(fp=buf, filename=fname)
        embed = discord.Embed(color=discord.Color.dark_purple())
        embed.set_image(url=f"attachment://{fname}")
        embed.set_footer(text=f"{interaction.user.display_name}'s Finale")

        if engine.get_auto_advance_delay() > 0:
            view = View()
        else:
            view = FinaleDialogView(engine, self._on_dialog_advance)
        await interaction.message.edit(embed=embed, view=view, attachments=[file])
        await self._schedule_auto_advance(engine)

    async def _on_quit(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if user_id in self.__finale_engines:
            self.__finale_engines[user_id].cancel_auto_advance()
            await self._leave_voice(self.__finale_engines[user_id])
            del self.__finale_engines[user_id]
        embed = discord.Embed(title="Finale Abandoned", description="You can return anytime with `,finale`", color=discord.Color.greyple())
        await interaction.message.edit(embed=embed, view=View(), attachments=[])