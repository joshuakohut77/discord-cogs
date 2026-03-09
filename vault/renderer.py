"""
vault/renderer.py — PIL-based card image renderer

Composites pixel art onto the card background template, then renders
four text fields into fixed zones:
  1. Category prefix  ("Power:", "Item:", "Ally:", etc.)
  2. Card name        ("Levitation", "Deity of Sand", etc.)
  3. Explanation       (one-sentence summary)
  4. Blurb            (detailed description/limitations)

Font file is configurable — swap FONT_PATH to your own .ttf/.otf.
All zone coordinates are hardcoded from the 504×392 background template.

Usage:
    from .renderer import render_card
    img_bytes = render_card(
        category="superpower",
        name="Levitation",
        explanation="You have the ability to levitate straight up and down.",
        blurb="While levitating, will prevent movement in any other direction...",
        art_path="cards/art/levitation.png",
    )
"""
from __future__ import annotations

import io
import os
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------
# PATHS — adjust to match your cog's data directory layout
# ---------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent

# Background template (504×392 PNG)
BACKGROUND_PATH = _THIS_DIR / "assets" / "card_background.png"

# Font file — swap this to your own pixel art .ttf
FONT_PATH = _THIS_DIR / "assets" / "font.ttf"

# Fallback font if the custom one isn't found
_FALLBACK_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FALLBACK_FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Directory where rendered card images are cached
RENDER_CACHE_DIR = _THIS_DIR / "rendered"

# ---------------------------------------------------------------
# LAYOUT CONSTANTS (measured from the 504×392 template)
# ---------------------------------------------------------------

# Card dimensions
CARD_WIDTH = 504
CARD_HEIGHT = 392

# Art zone — the black square where pixel art is composited
ART_LEFT = 17
ART_TOP = 17
ART_RIGHT = 190
ART_BOTTOM = 190
ART_WIDTH = ART_RIGHT - ART_LEFT + 1   # 174
ART_HEIGHT = ART_BOTTOM - ART_TOP + 1  # 174

# Text color — dark brown, sampled from the example cards
TEXT_COLOR = (34, 31, 22)

# --- Zone 1: Category prefix (e.g. "Power:") ---
# Right of art, top. Bold, larger font. Left-aligned.
CATEGORY_X = 204
CATEGORY_Y = 30
CATEGORY_MAX_W = 482     # right boundary ~486 minus CATEGORY_X
CATEGORY_FONT_SIZE = 40  # starting size, auto-shrinks to fit

# --- Zone 2: Card name (e.g. "Levitation") ---
# Below the category prefix, slightly indented. Bold, larger font.
# Y position is dynamic (below the rendered category text).
NAME_X = 240              # indented from category
NAME_MAX_W = 446           # right boundary ~486 minus NAME_X
NAME_FONT_SIZE = 40        # starting size, auto-shrinks to fit
NAME_Y_OFFSET = 5          # gap below the category text

# --- Zone 3: Explanation (one-sentence summary) ---
# Right of art, below the name block. Smaller font.
EXPL_X = 204
EXPL_Y_MIN = 120           # earliest Y the explanation can start
EXPL_MAX_W = 440           # same right boundary as category
EXPL_MAX_H = 70            # max height before we shrink the font
EXPL_FONT_SIZE = 36        # starting size

# --- Zone 4: Blurb (detailed description) ---
# Full width below the art zone. Medium font.
BLURB_X = 24
BLURB_Y = 210
BLURB_MAX_W = 730          # right boundary ~482 minus BLURB_X
BLURB_MAX_H = 165          # bottom boundary ~375 minus BLURB_Y
BLURB_FONT_SIZE = 36       # starting size (DejaVu placeholder is wider than pixel fonts)

# ---------------------------------------------------------------
# CATEGORY DISPLAY LABELS
# ---------------------------------------------------------------
CATEGORY_LABELS = {
    "superpower": "Power:",
    "ally": "Ally:",
    "companion": "Companion:",
    "item": "Item:",
    "weapon": "Weapon:",
    "armor": "Armor:",
}


# ---------------------------------------------------------------
# FONT LOADING
# ---------------------------------------------------------------

def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load the configured font at a given size, falling back to system fonts."""
    if FONT_PATH.exists():
        return ImageFont.truetype(str(FONT_PATH), size)

    fallback = _FALLBACK_FONT if bold else _FALLBACK_FONT_REGULAR
    if os.path.exists(fallback):
        return ImageFont.truetype(fallback, size)

    # Last resort — Pillow's built-in bitmap font
    return ImageFont.load_default()


# ---------------------------------------------------------------
# TEXT RENDERING HELPERS
# ---------------------------------------------------------------

def _wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Word-wrap text to fit within max_width pixels.

    Uses a binary-ish approach: starts with textwrap at a generous
    character width, then verifies each line fits pixel-wise and
    re-wraps tighter if needed.
    """
    if not text:
        return []

    # Estimate characters per line from average character width
    avg_char_w = font.getlength("M")
    if avg_char_w <= 0:
        avg_char_w = 10
    chars_per_line = max(1, int(max_width / avg_char_w))

    # Start generous, tighten if lines overflow
    for attempt in range(10):
        lines = textwrap.wrap(text, width=chars_per_line)
        all_fit = True
        for line in lines:
            line_w = font.getlength(line)
            if line_w > max_width:
                all_fit = False
                break
        if all_fit:
            return lines
        chars_per_line = max(1, chars_per_line - 2)

    # If we still can't fit, just wrap very tightly
    return textwrap.wrap(text, width=max(1, chars_per_line))


def _get_line_height(font: ImageFont.FreeTypeFont) -> int:
    """Get the line height for a font (ascent + descent + small gap)."""
    bbox = font.getbbox("Ag")  # chars with ascenders and descenders
    return int((bbox[3] - bbox[1]) * 1.35)  # 35% leading


def _fit_text_in_zone(
    text: str,
    max_width: int,
    max_height: int,
    start_size: int,
    bold: bool = True,
    min_size: int = 8,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Find the largest font size where wrapped text fits in the zone.

    Returns (font, wrapped_lines).
    """
    for size in range(start_size, min_size - 1, -1):
        font = _load_font(size, bold=bold)
        lines = _wrap_text(text, font, max_width)
        line_h = _get_line_height(font)
        total_h = line_h * len(lines)
        if total_h <= max_height:
            return font, lines

    # At minimum size, just return whatever we get
    font = _load_font(min_size, bold=bold)
    lines = _wrap_text(text, font, max_width)
    return font, lines


def _draw_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    x: int,
    y: int,
    color: tuple = TEXT_COLOR,
) -> int:
    """Draw wrapped text lines and return the Y position after the last line."""
    line_h = _get_line_height(font)
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += line_h
    return y


# ---------------------------------------------------------------
# MAIN RENDERER
# ---------------------------------------------------------------

def render_card(
    category: str,
    name: str,
    explanation: str,
    blurb: str,
    art_path: Optional[str] = None,
    background_path: Optional[str] = None,
) -> bytes:
    """Render a complete card image and return it as PNG bytes.

    Parameters
    ----------
    category : str
        Card category key (e.g. "superpower", "item").
    name : str
        Card name (e.g. "Levitation").
    explanation : str
        One-sentence card summary.
    blurb : str
        Detailed description/limitations text.
    art_path : str, optional
        Path to the pixel art PNG. If None or missing, the art zone
        stays as whatever the background has (black by default).
    background_path : str, optional
        Override the background template path.

    Returns
    -------
    bytes
        PNG image data.
    """
    # Load background
    bg_path = Path(background_path) if background_path else BACKGROUND_PATH
    card = Image.open(bg_path).convert("RGBA")

    # Composite pixel art into the art zone
    if art_path and os.path.exists(art_path):
        art = Image.open(art_path).convert("RGBA")
        # Resize art to fit the art zone exactly
        art = art.resize((ART_WIDTH, ART_HEIGHT), Image.NEAREST)
        card.paste(art, (ART_LEFT, ART_TOP), art)

    draw = ImageDraw.Draw(card)

    # --- Zone 1: Category prefix ---
    cat_label = CATEGORY_LABELS.get(category.lower(), f"{category.title()}:")
    cat_font = _load_font(CATEGORY_FONT_SIZE, bold=True)

    # Auto-shrink if the label is too wide (shouldn't happen for short labels)
    while cat_font.getlength(cat_label) > CATEGORY_MAX_W and CATEGORY_FONT_SIZE > 10:
        cat_font = _load_font(CATEGORY_FONT_SIZE - 2, bold=True)

    draw.text((CATEGORY_X, CATEGORY_Y), cat_label, font=cat_font, fill=TEXT_COLOR)
    cat_line_h = _get_line_height(cat_font)

    # --- Zone 2: Card name ---
    name_y = CATEGORY_Y + cat_line_h + NAME_Y_OFFSET
    name_font, name_lines = _fit_text_in_zone(
        name,
        max_width=NAME_MAX_W,
        max_height=ART_BOTTOM - name_y,  # can't go below the art zone bottom
        start_size=NAME_FONT_SIZE,
        bold=True,
    )
    name_bottom = _draw_text_block(draw, name_lines, name_font, NAME_X, name_y)

    # --- Zone 3: Explanation ---
    # Position dynamically: below the name, but not above EXPL_Y_MIN
    expl_y = max(name_bottom + 10, EXPL_Y_MIN)
    expl_max_h = ART_BOTTOM - expl_y  # constrain to the right-of-art zone

    if expl_max_h < 20:
        # If the name is really long, just put explanation at min position
        expl_y = EXPL_Y_MIN
        expl_max_h = ART_BOTTOM - expl_y

    expl_font, expl_lines = _fit_text_in_zone(
        explanation,
        max_width=EXPL_MAX_W,
        max_height=expl_max_h,
        start_size=EXPL_FONT_SIZE,
        bold=False,
        min_size=8,
    )
    _draw_text_block(draw, expl_lines, expl_font, EXPL_X, expl_y)

    # --- Zone 4: Blurb ---
    blurb_font, blurb_lines = _fit_text_in_zone(
        blurb,
        max_width=BLURB_MAX_W,
        max_height=BLURB_MAX_H,
        start_size=BLURB_FONT_SIZE,
        bold=False,
    )
    _draw_text_block(draw, blurb_lines, blurb_font, BLURB_X, BLURB_Y)

    # Convert to RGB (Discord doesn't need alpha) and return PNG bytes
    final = card.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="PNG")
    return buf.getvalue()


def render_card_to_file(
    category: str,
    name: str,
    explanation: str,
    blurb: str,
    art_path: Optional[str] = None,
    output_path: Optional[str] = None,
    background_path: Optional[str] = None,
) -> str:
    """Render a card and save to disk. Returns the output file path.

    If output_path is None, saves to RENDER_CACHE_DIR with a
    filename derived from category and name.
    """
    png_bytes = render_card(
        category=category,
        name=name,
        explanation=explanation,
        blurb=blurb,
        art_path=art_path,
        background_path=background_path,
    )

    if output_path is None:
        RENDER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = name.lower().replace(" ", "_").replace("'", "")
        output_path = str(RENDER_CACHE_DIR / f"{category}_{safe_name}.png")

    with open(output_path, "wb") as f:
        f.write(png_bytes)

    return output_path