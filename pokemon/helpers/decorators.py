"""
Decorators for encounters and battle handlers.

Provides session validation decorators to reduce code duplication
in Discord interaction handlers.
"""
import discord
from functools import wraps
from typing import Callable


def require_action_state(state_dict_attr: str = '_EncountersMixin__useractions'):
    """
    Decorator to validate ActionState session before handler executes.

    Args:
        state_dict_attr: Name of the state dictionary attribute on self

    Usage:
        @require_action_state()
        async def on_fight_click(self, interaction: discord.Interaction):
            # state validated, proceed with logic
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            user = interaction.user
            state_dict = getattr(self, state_dict_attr, {})

            if str(user.id) not in state_dict:
                await interaction.response.send_message(
                    'No active session found.',
                    ephemeral=True
                )
                return

            state = state_dict[str(user.id)]
            if state.messageId != interaction.message.id:
                await interaction.response.send_message(
                    'This is not for you.',
                    ephemeral=True
                )
                return

            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator


def require_battle_state(state_dict_attr: str = '_EncountersMixin__battle_states'):
    """
    Decorator to validate BattleState session before handler executes.

    Args:
        state_dict_attr: Name of the state dictionary attribute on self

    Usage:
        @require_battle_state()
        async def on_battle_move_click(self, interaction: discord.Interaction):
            # battle state validated, proceed with logic
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            user = interaction.user
            user_id = str(user.id)
            state_dict = getattr(self, state_dict_attr, {})

            if user_id not in state_dict:
                await interaction.response.send_message(
                    'No active battle found.',
                    ephemeral=True
                )
                return

            battle_state = state_dict[user_id]
            if battle_state.message_id != interaction.message.id:
                await interaction.response.send_message(
                    'This is not the current battle.',
                    ephemeral=True
                )
                return

            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator


def require_wild_battle_state(state_dict_attr: str = '_EncountersMixin__wild_battle_states'):
    """
    Decorator to validate WildBattleState session before handler executes.

    Args:
        state_dict_attr: Name of the state dictionary attribute on self

    Usage:
        @require_wild_battle_state()
        async def on_wild_battle_move_click(self, interaction: discord.Interaction):
            # wild battle state validated, proceed with logic
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            user = interaction.user
            user_id = str(user.id)
            state_dict = getattr(self, state_dict_attr, {})

            if user_id not in state_dict:
                await interaction.response.send_message(
                    'No active wild battle found.',
                    ephemeral=True
                )
                return

            battle_state = state_dict[user_id]
            if battle_state.message_id != interaction.message.id:
                await interaction.response.send_message(
                    'This is not the current battle.',
                    ephemeral=True
                )
                return

            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator


def require_bag_state(state_dict_attr: str = '_EncountersMixin__bag_states'):
    """
    Decorator to validate BagState session.

    Args:
        state_dict_attr: Name of the state dictionary attribute on self

    Usage:
        @require_bag_state()
        async def on_bag_items_click(self, interaction: discord.Interaction):
            # bag state validated, proceed with logic
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            user = interaction.user
            state_dict = getattr(self, state_dict_attr, {})

            if str(user.id) not in state_dict:
                await interaction.response.send_message(
                    'Session expired.',
                    ephemeral=True
                )
                return

            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator
