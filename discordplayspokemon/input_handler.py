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

# -----------------------------------------------------------------------
# Passive harvesting: ALL 26 letters map to buttons, distributed by
# English letter frequency so the five primary buttons (a, up, down,
# left, right) each receive ~17-19% of natural text input, while the
# three secondary buttons (b, start, select) receive low input.
#
# Traditional shortcuts are preserved: a→a, b→b, u→up, d→down,
# l→left, r→right, s→start.  Remaining letters are balanced by
# frequency.
#
# Letter frequencies (approximate %):
#   e 12.70  t 9.06  a 8.17  o 7.51  i 6.97  n 6.75  s 6.33
#   h 6.09   r 5.99  d 4.25  l 4.03  c 2.78  u 2.76  m 2.41
#   w 2.36   f 2.23  g 2.02  y 1.97  p 1.93  b 1.29  v 0.98
#   k 0.77   j 0.15  x 0.15  q 0.10  z 0.07
#
# Resulting distribution:
#   BUTTON A  : a, n, w, p        → 19.21%
#   UP        : u, e, m           → 17.87%
#   DOWN      : d, o, h           → 17.85%
#   LEFT      : l, t, f, g        → 17.34%
#   RIGHT     : r, i, c, y        → 17.71%
#   B         : b                  →  1.29%
#   START     : s                  →  6.33%
#   SELECT    : z, q, x, j, k, v  →  2.22%
# -----------------------------------------------------------------------
LETTER_TO_BUTTON: dict[str, str] = {
    "a": "a",       # 8.17%
    "b": "b",       # 1.29%
    "c": "right",   # 2.78%
    "d": "down",    # 4.25%
    "e": "up",      # 12.70%
    "f": "left",    # 2.23%
    "g": "left",    # 2.02%
    "h": "down",    # 6.09%
    "i": "right",   # 6.97%
    "j": "select",  # 0.15%
    "k": "select",  # 0.77%
    "l": "left",    # 4.03%
    "m": "up",      # 2.41%
    "n": "a",       # 6.75%
    "o": "down",    # 7.51%
    "p": "a",       # 1.93%
    "q": "select",  # 0.10%
    "r": "right",   # 5.99%
    "s": "start",   # 6.33%
    "t": "left",    # 9.06%
    "u": "up",      # 2.76%
    "v": "select",  # 0.98%
    "w": "a",       # 2.36%
    "x": "select",  # 0.15%
    "y": "right",   # 1.97%
    "z": "select",  # 0.07%
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

        Supports single inputs ("a"), short combos ("up up a left"),
        and run-together letters ("aaalll" → a, a, a, left, left, left).
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
            else:
                # Token didn't match as a word — try character-by-character
                # using the full letter map so every letter becomes an input
                for char in tok:
                    btn = LETTER_TO_BUTTON.get(char)
                    if btn:
                        buttons.append(btn)
                    if len(buttons) >= max_inputs:
                        break
            if len(buttons) >= max_inputs:
                break
        return buttons

    def harvest_letters(self, text: str, max_inputs: int = 20) -> list[str]:
        """Extract individual letters from arbitrary text that map to buttons.

        Used for passive server-wide harvesting. Every letter in the
        alphabet maps to a button, distributed by English frequency so
        the five primary buttons receive roughly equal input from
        natural conversation.

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
            "Passive mode: ALL letters in any channel\n"
            "are harvested and balanced across buttons.\n"
            "```"
        )