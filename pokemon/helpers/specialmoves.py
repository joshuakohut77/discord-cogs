"""
Special move handlers for Pokemon battle system.

Handles moves with unique effects beyond standard damage calculation:
- rest: Full heal + forced 2-turn sleep
- recover: Heal 50% max HP
- leech_seed: Plant seed, drain 1/8 HP per turn
- drain: Absorb/Mega-Drain/Leech-Life - heal 50% of damage dealt
- night_shade: Fixed damage equal to user's level
- dream_eater: Only works on sleeping targets, drain 50% of damage dealt
"""
import random


# Set of all special function identifiers
SPECIAL_FUNCTIONS = {'rest', 'recover', 'leech_seed', 'drain', 'night_shade', 'dream_eater', 'haze'}

def is_special_move(move_data):
    """Check if a move has a special function that needs handling."""
    return move_data.get('special_function', '') in SPECIAL_FUNCTIONS


def get_special_function(move_data):
    """Get the special_function string from move data, or empty string."""
    return move_data.get('special_function', '')


def handle_rest(current_hp, max_hp):
    """
    Handle Rest: heal to full HP.
    Caller is responsible for setting rest_turns = 2.
    
    Returns: (heal_amount, new_hp)
    """
    heal_amount = max_hp - current_hp
    if heal_amount < 0:
        heal_amount = 0
    return heal_amount, max_hp


def handle_recover(current_hp, max_hp):
    """
    Handle Recover: heal 50% of max HP (rounded down).
    
    Returns: (actual_heal, new_hp)
    """
    heal_amount = max_hp // 2
    new_hp = min(max_hp, current_hp + heal_amount)
    actual_heal = new_hp - current_hp
    if actual_heal < 0:
        actual_heal = 0
    return actual_heal, new_hp


def calculate_drain_heal(damage_dealt):
    """
    Calculate HP restored from drain moves (absorb, mega-drain, leech-life, dream-eater).
    Returns 50% of damage dealt, minimum 1. Returns 0 if no damage dealt.
    """
    if damage_dealt <= 0:
        return 0
    return max(1, damage_dealt // 2)


def calculate_night_shade_damage(attacker_level):
    """Night Shade: damage equals the user's level."""
    return max(1, attacker_level)


def calculate_leech_seed_damage(target_max_hp):
    """
    Leech Seed: drain 1/8 of target's max HP per turn (min 1).
    Returns the drain amount.
    """
    return max(1, target_max_hp // 8)


def check_dream_eater_valid(target_is_asleep):
    """
    Dream Eater only works if the target is asleep.
    Pass in the boolean sleep status of the target.
    """
    return target_is_asleep


def check_accuracy(accuracy):
    """
    Roll accuracy check for special moves that need it.
    Returns True if the move hits.
    """
    if accuracy is None or accuracy >= 100:
        return True
    return random.randint(1, 100) <= accuracy

def handle_haze(attacker_stat_stages, defender_stat_stages):
    """
    Haze: Reset all stat stages for both sides to 0.
    Returns True if any stages were actually changed.
    """
    had_changes = attacker_stat_stages.has_any_changes() or defender_stat_stages.has_any_changes()
    attacker_stat_stages.reset()
    defender_stat_stages.reset()
    return had_changes