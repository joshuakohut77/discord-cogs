"""
Stat stage modifier system for Pokemon battles.

Implements the Gen 1 stat stage multiplier system (-6 to +6).
Each stage modifies the base stat by a multiplier during damage calculation.

Usage:
    stages = StatStages()
    stages.modify('attack', -1)  # Growl lowers attack by 1 stage
    multiplier = stages.get_multiplier('attack')  # Returns 0.667
    stages.reset()  # Clear all stages (on faint/switch)
"""
import random


# Stage multiplier lookup table
# Stage 0 = 1.0, each positive stage adds 0.5, each negative stage reduces proportionally
STAGE_MULTIPLIERS = {
    -6: 2/8,   # 0.25
    -5: 2/7,   # 0.286
    -4: 2/6,   # 0.333
    -3: 2/5,   # 0.4
    -2: 2/4,   # 0.5
    -1: 2/3,   # 0.667
     0: 1.0,
     1: 3/2,   # 1.5
     2: 4/2,   # 2.0
     3: 5/2,   # 2.5
     4: 6/2,   # 3.0
     5: 7/2,   # 3.5
     6: 8/2,   # 4.0
}

# Stat display names for battle log messages
STAT_DISPLAY_NAMES = {
    'attack': 'Attack',
    'defense': 'Defense',
    'speed': 'Speed',
    'special-attack': 'Sp. Atk',
    'special-defense': 'Sp. Def',
}

# Emojis for stat changes in battle log
STAT_CHANGE_EMOJIS = {
    'raise': '🔺',
    'lower': '🔻',
    'max': '⚠️',
    'min': '⚠️',
}


class StatStages:
    """Tracks in-battle stat stage modifiers for one Pokemon."""

    def __init__(self):
        self.stages = {
            'attack': 0,
            'defense': 0,
            'speed': 0,
            'special-attack': 0,
            'special-defense': 0,
        }

    def modify(self, stat, amount):
        """
        Modify a stat stage by the given amount.
        Clamps to [-6, +6].

        Returns: (new_stage, actually_changed)
            - new_stage: the stage value after modification
            - actually_changed: bool, False if already at min/max
        """
        if stat not in self.stages:
            return 0, False

        old_stage = self.stages[stat]
        new_stage = max(-6, min(6, old_stage + amount))
        actually_changed = (new_stage != old_stage)
        self.stages[stat] = new_stage
        return new_stage, actually_changed

    def get_multiplier(self, stat):
        """Get the current multiplier for a stat based on its stage."""
        stage = self.stages.get(stat, 0)
        return STAGE_MULTIPLIERS.get(stage, 1.0)

    def get_stage(self, stat):
        """Get the raw stage value for a stat."""
        return self.stages.get(stat, 0)

    def reset(self):
        """Reset all stages to 0 (on faint, switch, or Haze)."""
        for stat in self.stages:
            self.stages[stat] = 0

    def has_any_changes(self):
        """Check if any stat has been modified from 0."""
        return any(v != 0 for v in self.stages.values())

    def get_summary(self):
        """Get a summary string of all non-zero stages for display."""
        parts = []
        for stat, stage in self.stages.items():
            if stage != 0:
                name = STAT_DISPLAY_NAMES.get(stat, stat)
                sign = '+' if stage > 0 else ''
                parts.append(f"{name} {sign}{stage}")
        return ', '.join(parts) if parts else None


def apply_stat_change(move_data, attacker_stages, defender_stages, log_lines,
                      attacker_name, defender_name, hit=True):
    """
    Apply stat_change from a status move (always applies on use).

    Args:
        move_data: The move's config dict from moves.json
        attacker_stages: StatStages for the attacker
        defender_stages: StatStages for the defender
        log_lines: List to append log messages to
        attacker_name: Display name of attacker (e.g. "Pikachu")
        defender_name: Display name of defender (e.g. "Enemy Geodude")
        hit: Whether the move hit (for accuracy-based stat moves)

    Returns: True if a stat change was applied, False otherwise
    """
    stat_change = move_data.get('stat_change')
    if not stat_change:
        return False

    if not hit:
        return False

    target = stat_change['target']
    stat = stat_change['stat']
    stages = stat_change['stages']

    if stat not in STAT_DISPLAY_NAMES:
        return False

    if target == 'self':
        target_stages = attacker_stages
        target_name = attacker_name
    else:
        target_stages = defender_stages
        target_name = defender_name

    new_stage, changed = target_stages.modify(stat, stages)
    stat_display = STAT_DISPLAY_NAMES[stat]

    if changed:
        if stages > 0:
            if stages >= 2:
                log_lines.append(f"{STAT_CHANGE_EMOJIS['raise']} {target_name}'s {stat_display} sharply rose!")
            else:
                log_lines.append(f"{STAT_CHANGE_EMOJIS['raise']} {target_name}'s {stat_display} rose!")
        else:
            if stages <= -2:
                log_lines.append(f"{STAT_CHANGE_EMOJIS['lower']} {target_name}'s {stat_display} sharply fell!")
            else:
                log_lines.append(f"{STAT_CHANGE_EMOJIS['lower']} {target_name}'s {stat_display} fell!")
        return True
    else:
        if stages > 0:
            log_lines.append(f"{STAT_CHANGE_EMOJIS['max']} {target_name}'s {stat_display} can't go any higher!")
        else:
            log_lines.append(f"{STAT_CHANGE_EMOJIS['min']} {target_name}'s {stat_display} can't go any lower!")
        return False


def apply_secondary_stat_change(move_data, attacker_stages, defender_stages,
                                log_lines, attacker_name, defender_name):
    """
    Roll and apply stat_change_secondary from a damaging move.
    Only rolls if the move already hit and dealt damage.

    Args: Same as apply_stat_change

    Returns: True if a stat change was applied
    """
    secondary = move_data.get('stat_change_secondary')
    if not secondary:
        return False

    chance = secondary.get('chance', 0)
    if chance <= 0:
        return False

    if random.randint(1, 100) > chance:
        return False

    target = secondary['target']
    stat = secondary['stat']
    stages = secondary['stages']

    if stat not in STAT_DISPLAY_NAMES:
        return False

    if target == 'self':
        target_stages = attacker_stages
        target_name = attacker_name
    else:
        target_stages = defender_stages
        target_name = defender_name

    new_stage, changed = target_stages.modify(stat, stages)
    stat_display = STAT_DISPLAY_NAMES[stat]

    if changed:
        if stages > 0:
            log_lines.append(f"{STAT_CHANGE_EMOJIS['raise']} {target_name}'s {stat_display} rose!")
        else:
            log_lines.append(f"{STAT_CHANGE_EMOJIS['lower']} {target_name}'s {stat_display} fell!")
        return True
    return False


def get_modified_stat(base_stat, stat_name, stat_stages):
    """
    Apply stage multiplier to a base stat value.

    Args:
        base_stat: The raw stat value from getPokeStats()
        stat_name: The stat key ('attack', 'defense', etc.)
        stat_stages: StatStages object for this Pokemon

    Returns: Modified stat value (int, minimum 1)
    """
    if stat_stages is None:
        return base_stat
    multiplier = stat_stages.get_multiplier(stat_name)
    return max(1, int(base_stat * multiplier))