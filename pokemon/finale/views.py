"""
Discord UI Views for the finale system.

FinaleDialogView — "Next" button for advancing dialog/transitions.
FinaleBattleView — Move buttons for battle sequences.

Both views call back into the FinaleEngine to advance state,
then re-render and update the message.
"""
from __future__ import annotations
import asyncio
from typing import Optional, Callable, Awaitable, TYPE_CHECKING

import discord
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

if TYPE_CHECKING:
    from .engine import FinaleEngine


class FinaleDialogView(View):
    """View with a 'Next' button for dialog scenes and transitions."""

    def __init__(self, engine: 'FinaleEngine', update_callback: Callable[..., Awaitable],
                 is_auto: bool = False, timeout: float = 600):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.update_callback = update_callback

        label = "Skip ▶▶" if is_auto else "Next ▶"
        self.next_btn = Button(
            style=ButtonStyle.secondary if is_auto else ButtonStyle.primary,
            label=label,
            custom_id="finale_next"
        )
        self.next_btn.callback = self.on_next
        self.add_item(self.next_btn)

    async def on_next(self, interaction: Interaction):
        if str(interaction.user.id) != self.engine.user_id:
            await interaction.response.send_message("This isn't your story.", ephemeral=True)
            return

        try:
            await interaction.response.defer()
        except Exception:
            return

        try:
            self.engine.cancel_auto_advance()
            result = self.engine.advance_dialog()
            await self.update_callback(interaction, result)
        except Exception as e:
            print(f"[Finale] on_next callback error: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send(f"Something went wrong. Use `,finale` to restart.", ephemeral=True)
            except Exception:
                pass

class FinaleBattleView(View):
    """View with move buttons during a finale battle."""

    def __init__(self, engine: 'FinaleEngine',
                 attack_callback: Callable[..., Awaitable],
                 switch_callback: Optional[Callable[..., Awaitable]] = None,
                 timeout: float = 600):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.attack_callback = attack_callback
        self.switch_callback = switch_callback

        if not engine.battle_state or not engine.battle_state.player_pokemon:
            return

        pokemon = engine.battle_state.player_pokemon
        moves = pokemon.getMoves() if hasattr(pokemon, 'getMoves') else []

        # Load move config for display info
        try:
            from helpers.pathhelpers import load_json_config
            moves_config = load_json_config('moves.json')
        except Exception:
            moves_config = {}

        # Add move buttons (up to 4) — getMoves() returns a list of move name strings
        for i, move_name in enumerate(moves[:4]):
            if not move_name or move_name.lower() == 'none':
                continue
            move_data = moves_config.get(move_name, {})
            move_type = move_data.get('moveType', 'normal')
            display_name = move_name.replace('-', ' ').title()
            btn = Button(
                style=self._type_button_style(move_type),
                label=display_name,
                custom_id=f"finale_move_{i}",
                row=0 if i < 2 else 1
            )
            btn.callback = self._make_move_callback(i)
            self.add_item(btn)

        # Switch Pokemon button (row 2) — disabled for scripted battle modes
        no_switch_modes = ("unwinnable", "rigged_win", "final_skippy", "melkor")
        battle_mode = getattr(engine.battle_state, 'battle_mode', 'normal') if engine.battle_state else 'normal'
        if engine.battle_state and len(engine.battle_state.player_party) > 1 and battle_mode not in no_switch_modes:
            alive_count = sum(1 for p in engine.battle_state.player_party if p.currentHP > 0)
            if alive_count > 1 and switch_callback:
                switch_btn = Button(
                    style=ButtonStyle.secondary,
                    label="🔄 Switch",
                    custom_id="finale_switch",
                    row=2
                )
                switch_btn.callback = self.on_switch
                self.add_item(switch_btn)

    def _make_move_callback(self, move_index: int):
        async def callback(interaction: Interaction):
            if str(interaction.user.id) != self.engine.user_id:
                await interaction.response.send_message("This isn't your battle.", ephemeral=True)
                return
            try:
                await interaction.response.defer()
            except Exception:
                return
            try:
                await self.attack_callback(interaction, move_index)
            except Exception as e:
                print(f"[Finale] move callback error: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await interaction.followup.send("Something went wrong. Use `,finale` to restart.", ephemeral=True)
                except Exception:
                    pass
        return callback

    async def on_switch(self, interaction: Interaction):
        if str(interaction.user.id) != self.engine.user_id:
            await interaction.response.send_message("This isn't your battle.", ephemeral=True)
            return
        await interaction.response.defer()
        if self.switch_callback:
            await self.switch_callback(interaction)

    def _type_button_style(self, move_type: str) -> ButtonStyle:
        """Pick a button color based on move type."""
        type_styles = {
            'fire': ButtonStyle.danger,
            'water': ButtonStyle.primary,
            'grass': ButtonStyle.success,
            'electric': ButtonStyle.primary,
            'psychic': ButtonStyle.secondary,
            'fighting': ButtonStyle.danger,
            'poison': ButtonStyle.secondary,
            'ground': ButtonStyle.secondary,
            'rock': ButtonStyle.secondary,
            'ice': ButtonStyle.primary,
            'dragon': ButtonStyle.danger,
            'dark': ButtonStyle.secondary,
            'ghost': ButtonStyle.secondary,
            'flying': ButtonStyle.primary,
            'bug': ButtonStyle.success,
            'normal': ButtonStyle.secondary,
        }
        return type_styles.get(move_type.lower(), ButtonStyle.secondary)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class FinaleSwitchView(View):
    """View for selecting which Pokemon to switch to during finale battle."""

    def __init__(self, engine: 'FinaleEngine',
                 switch_confirm_callback: Callable[..., Awaitable],
                 cancel_callback: Callable[..., Awaitable],
                 timeout: float = 120):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.switch_confirm_callback = switch_confirm_callback
        self.cancel_callback = cancel_callback

        if not engine.battle_state:
            return

        for i, poke in enumerate(engine.battle_state.player_party):
            if poke.currentHP <= 0:
                continue
            if i == engine.battle_state.player_current_index:
                continue  # skip current pokemon

            stats = poke.getPokeStats()
            label = f"{poke.pokemonName.capitalize()} Lv.{poke.currentLevel} ({poke.currentHP}/{stats['hp']})"
            btn = Button(
                style=ButtonStyle.success,
                label=label[:80],
                custom_id=f"finale_switch_{i}",
                row=i // 2
            )
            btn.callback = self._make_switch_callback(i)
            self.add_item(btn)

        cancel_btn = Button(
            style=ButtonStyle.danger,
            label="Cancel",
            custom_id="finale_switch_cancel",
            row=4
        )
        cancel_btn.callback = self.on_cancel
        self.add_item(cancel_btn)

    def _make_switch_callback(self, party_index: int):
        async def callback(interaction: Interaction):
            if str(interaction.user.id) != self.engine.user_id:
                await interaction.response.send_message("This isn't your battle.", ephemeral=True)
                return
            await interaction.response.defer()
            await self.switch_confirm_callback(interaction, party_index)
        return callback

    async def on_cancel(self, interaction: Interaction):
        if str(interaction.user.id) != self.engine.user_id:
            await interaction.response.send_message("This isn't your battle.", ephemeral=True)
            return
        await interaction.response.defer()
        await self.cancel_callback(interaction)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class FinaleDefeatView(View):
    """View shown when the player loses the finale battle."""

    def __init__(self, engine: 'FinaleEngine',
                 retry_callback: Callable[..., Awaitable],
                 quit_callback: Callable[..., Awaitable],
                 timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine

        retry_btn = Button(
            style=ButtonStyle.success,
            label="⚔️ Try Again",
            custom_id="finale_retry"
        )
        retry_btn.callback = self._wrap(retry_callback)
        self.add_item(retry_btn)

        quit_btn = Button(
            style=ButtonStyle.danger,
            label="🚪 Leave",
            custom_id="finale_quit"
        )
        quit_btn.callback = self._wrap(quit_callback)
        self.add_item(quit_btn)

    def _wrap(self, cb):
        engine = self.engine
        async def wrapper(interaction: Interaction):
            if str(interaction.user.id) != engine.user_id:
                await interaction.response.send_message("This isn't for you.", ephemeral=True)
                return
            await interaction.response.defer()
            await cb(interaction)
        return wrapper

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True