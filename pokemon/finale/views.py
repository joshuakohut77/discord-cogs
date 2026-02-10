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
                 timeout: float = 600):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.update_callback = update_callback

        self.next_btn = Button(
            style=ButtonStyle.primary,
            label="Next ▶",
            custom_id="finale_next"
        )
        self.next_btn.callback = self.on_next
        self.add_item(self.next_btn)

    async def on_next(self, interaction: Interaction):
        if str(interaction.user.id) != self.engine.user_id:
            await interaction.response.send_message("This isn't your story.", ephemeral=True)
            return

        await interaction.response.defer()
        result = self.engine.advance_dialog()
        await self.update_callback(interaction, result)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


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

        # Add move buttons (up to 4)
        for i, move in enumerate(moves[:4]):
            move_name = move.get('name', move.get('moveName', f'Move {i+1}'))
            move_type = move.get('type', 'normal')
            btn = Button(
                style=self._type_button_style(move_type),
                label=move_name.capitalize(),
                custom_id=f"finale_move_{i}",
                row=0 if i < 2 else 1
            )
            btn.callback = self._make_move_callback(i)
            self.add_item(btn)

        # Switch Pokemon button (row 2)
        if engine.battle_state and len(engine.battle_state.player_party) > 1:
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
            await interaction.response.defer()
            await self.attack_callback(interaction, move_index)
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