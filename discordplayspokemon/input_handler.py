"""Maps Discord messages to Game Boy button presses."""

import re


# PyBoy button names:
#   "a", "b", "start", "select", "up", "down", "left", "right"

# Primary mapping: message content (lowered + stripped) → PyBoy button
INPUT_MAP: dict[str, str] = {
    # Single-character shortcuts
    "a":        "a",
    "b":        "b",
    "u":        "up",
    "d":        "down",
    "l":        "left",
    "r":        "right",
    "st":       "start",

    # Full words
    "up":       "up",
    "down":     "down",
    "left":     "left",
    "right":    "right",
    "start":    "start",
    "select":   "select",
}

# Emoji aliases (people will try these)
EMOJI_MAP: dict[str, str] = {
    "⬆️": "up",
    "⬇️": "down",
    "⬅️": "left",
    "➡️": "right",
    "🅰️": "a",
    "🅱️": "b",
    "▶️": "start",
}

VALID_BUTTONS = {"a", "b", "up", "down", "left", "right", "start", "select"}

# Characters that map to buttons for passive harvesting
LETTER_TO_BUTTON: dict[str, str] = {
    "a": "a",
    "b": "b",
    "u": "up",
    "d": "down",
    "l": "left",
    "r": "right",
}

# Pattern for multi-input strings like "up up a left"
_MULTI_RE = re.compile(r"[a-z]+|[⬆⬇⬅➡🅰🅱▶]\uFE0F?", re.UNICODE)


class InputHandler:
    """Parses a Discord message into one or more Game Boy button names."""

    def parse_single(self, text: str) -> str | None:
        """Return a single button name or None."""
        cleaned = text.strip().lower()
        return INPUT_MAP.get(cleaned) or EMOJI_MAP.get(cleaned)

    def parse(self, text: str, max_inputs: int = 5) -> list[str]:
        """Return up to *max_inputs* button names from a message.

        Supports both single inputs ("a") and short combos ("up up a left").
        The cap prevents someone from pasting a wall of inputs.
        """
        # Fast path: single token
        single = self.parse_single(text)
        if single:
            return [single]

        tokens = _MULTI_RE.findall(text.strip().lower())
        buttons: list[str] = []
        for tok in tokens:
            btn = INPUT_MAP.get(tok) or EMOJI_MAP.get(tok)
            if btn:
                buttons.append(btn)
            if len(buttons) >= max_inputs:
                break
        return buttons

    def harvest_letters(self, text: str, max_inputs: int = 20) -> list[str]:
        """Extract individual letters from arbitrary text that map to buttons.

        Used for passive server-wide harvesting. For example:
        "Hello I am going to school today" → h(skip) e(skip) l(left) l(left)
        o(skip) i(skip) a(a) m(skip) ...

        Returns up to *max_inputs* buttons.
        """
        buttons: list[str] = []
        for char in text.lower():
            btn = LETTER_TO_BUTTON.get(char)
            if btn:
                buttons.append(btn)
            if len(buttons) >= max_inputs:
                break
        return buttons

    @staticmethod
    def get_controls_display() -> str:
        return (
            "```\n"
            "D-Pad\n"
            "  u  / up       — Up\n"
            "  d  / down     — Down\n"
            "  l  / left     — Left\n"
            "  r  / right    — Right\n"
            "\n"
            "Buttons\n"
            "  a             — A\n"
            "  b             — B\n"
            "  start         — Start\n"
            "  select        — Select\n"
            "\n"
            "Emoji shortcuts: ⬆️ ⬇️ ⬅️ ➡️ 🅰️ 🅱️ ▶️\n"
            "Combos: 'up up a left' (max 5 per message)\n"
            "\n"
            "Passive mode: letters in ANY channel are\n"
            "silently harvested (a/b/u/d/l/r)\n"
            "```"
        )