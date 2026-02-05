"""
File path utilities for Pokemon cog.

Provides centralized file path construction and config loading
to replace repetitive os.path.join patterns throughout the codebase.
"""
import os
import json
from typing import Any, Dict


# Cache the base directory for the pokemon module
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cache for loaded JSON configs to avoid repeated file reads
_config_cache: Dict[str, Any] = {}


def get_config_path(filename: str) -> str:
    """
    Get absolute path to a config file in the configs/ directory.

    Args:
        filename: Name of the config file (e.g., 'moves.json')

    Returns:
        Absolute path to the config file

    Example:
        >>> path = get_config_path('moves.json')
        >>> # Returns: '/path/to/pokemon/configs/moves.json'
    """
    return os.path.join(_BASE_DIR, 'configs', filename)


def get_sprite_path(sprite_path: str) -> str:
    """
    Convert relative sprite path to absolute path.

    Args:
        sprite_path: Relative sprite path (may have leading slash)

    Returns:
        Absolute path to the sprite file

    Example:
        >>> path = get_sprite_path('/sprites/pokemon/pikachu.png')
        >>> # Returns: '/path/to/pokemon/sprites/pokemon/pikachu.png'
    """
    return os.path.join(_BASE_DIR, sprite_path.lstrip('/'))


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to any resource file relative to pokemon directory.

    Args:
        relative_path: Relative path from pokemon directory

    Returns:
        Absolute path to the resource

    Example:
        >>> path = get_resource_path('fonts/arial.ttf')
        >>> # Returns: '/path/to/pokemon/fonts/arial.ttf'
    """
    return os.path.join(_BASE_DIR, relative_path.lstrip('/'))


def load_json_config(filename: str, use_cache: bool = True) -> Dict:
    """
    Load JSON config file from configs/ directory with optional caching.

    Args:
        filename: Name of the config file (e.g., 'moves.json')
        use_cache: Whether to use cached version (default: True)

    Returns:
        Dictionary containing the JSON data

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON

    Example:
        >>> moves = load_json_config('moves.json')
        >>> move_data = moves['thunderbolt']
    """
    # Return cached version if available
    if use_cache and filename in _config_cache:
        return _config_cache[filename]

    config_path = get_config_path(filename)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Cache the loaded data
        if use_cache:
            _config_cache[filename] = data

        return data

    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in config file {filename}: {e.msg}",
            e.doc,
            e.pos
        )


def clear_config_cache(filename: str = None):
    """
    Clear the config cache for a specific file or all files.

    Args:
        filename: Specific config file to clear, or None to clear all

    Example:
        >>> clear_config_cache('moves.json')  # Clear specific file
        >>> clear_config_cache()  # Clear all cached configs
    """
    if filename:
        _config_cache.pop(filename, None)
    else:
        _config_cache.clear()
