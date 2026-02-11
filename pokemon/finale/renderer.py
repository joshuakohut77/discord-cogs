"""
PIL-based renderer for the finale system.

Generates complete scene frames as images — dialog boxes, battle scenes,
transitions, and cutscenes. Each method returns a PIL Image that gets
converted to a discord.File for sending.
"""
import os
import requests
from io import BytesIO
from typing import Optional, Tuple, TYPE_CHECKING

from PIL import Image, ImageFont, ImageDraw

if TYPE_CHECKING:
    from services.pokeclass import Pokemon as PokemonClass

# Base dimensions for all rendered frames
FRAME_WIDTH = 800
FRAME_HEIGHT = 480

# Dialog box dimensions and positioning
DIALOG_BOX_HEIGHT = 140
DIALOG_BOX_MARGIN = 16
DIALOG_BOX_PADDING = 20
DIALOG_BOX_Y = FRAME_HEIGHT - DIALOG_BOX_HEIGHT - DIALOG_BOX_MARGIN

# Speaker name tag
SPEAKER_TAG_HEIGHT = 30
SPEAKER_TAG_WIDTH = 200
SPEAKER_TAG_Y = DIALOG_BOX_Y - SPEAKER_TAG_HEIGHT

# HP bar rendering
HP_BAR_WIDTH = 120
HP_BAR_HEIGHT = 10

# Character sprite sizing
CHARACTER_SPRITE_SIZE = (250, 250)
POKEMON_SPRITE_SIZE = (200, 200)


class FinaleRenderer:
    """Renders cinematic frames for the finale system using PIL."""

    def __init__(self):
        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._font_path = os.path.join(self._base_dir, 'fonts', 'pokemon_generation_1.ttf')
        self._finale_dir = os.path.join(self._base_dir, 'sprites', 'finale')
        self._bg_dir = os.path.join(self._finale_dir, 'backgrounds')
        self._char_dir = os.path.join(self._finale_dir, 'characters')
        self._effects_dir = os.path.join(self._finale_dir, 'effects')

        # Pre-load fonts at common sizes
        self._fonts = {}
        for size in [18, 24, 30, 36, 48]:
            try:
                self._fonts[size] = ImageFont.truetype(self._font_path, size)
            except Exception:
                self._fonts[size] = ImageFont.load_default()

    def get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font at the requested size, loading if needed."""
        if size not in self._fonts:
            try:
                self._fonts[size] = ImageFont.truetype(self._font_path, size)
            except Exception:
                self._fonts[size] = ImageFont.load_default()
        return self._fonts[size]

    # ------------------------------------------------------------------
    # Public render methods
    # ------------------------------------------------------------------

    def render_dialog(self, speaker: str, text: str,
                      background: Optional[str] = None,
                      character_sprite: Optional[str] = None,
                      character_position: str = "right",
                      text_box_color: tuple = (0, 0, 0, 180),
                      trainer_name: Optional[str] = None,
                      character_sprite_2: Optional[str] = None,
                      character_position_2: str = "left") -> Image.Image:
        """
        Render a dialog scene frame.
        Supports up to two character sprites for dual-character scenes.
        """
        frame = self._load_background(background)

        if character_sprite:
            frame = self._composite_character(frame, character_sprite, character_position)

        if character_sprite_2:
            frame = self._composite_character(frame, character_sprite_2, character_position_2)

        if trainer_name:
            text = text.replace("{trainer_name}", trainer_name)
            speaker = speaker.replace("{trainer_name}", trainer_name)

        frame = self._draw_dialog_box(frame, speaker, text, text_box_color)
        return frame


    def render_battle(self, player_pokemon: 'PokemonClass',
                      enemy_pokemon: 'PokemonClass',
                      enemy_name: str = "???",
                      turn_number: int = 1,
                      battle_log: Optional[str] = None,
                      battle_background: Optional[str] = None) -> Image.Image:
        """
        Render a battle scene frame with both Pokemon, HP bars, and status.
        """
        # Background
        if battle_background:
            frame = self._load_background(battle_background)
        else:
            frame = self._load_background("battle_default.png")

        draw = ImageDraw.Draw(frame)
        font = self.get_font(24)
        small_font = self.get_font(18)
        
        # -- Enemy Pokemon (top-right area) --
        enemy_sprite = self._get_pokemon_sprite(enemy_pokemon, front=True)
        if enemy_sprite:
            enemy_sprite = self._remove_background(enemy_sprite).resize(POKEMON_SPRITE_SIZE)
            frame.paste(enemy_sprite, (520, 20), enemy_sprite)

        # Enemy info box (top-left)
        self._draw_info_box(draw, 20, 20, enemy_pokemon, font, small_font,
                            label=enemy_pokemon.pokemonName.upper())

        # -- Player Pokemon (bottom-left area) --
        player_sprite = self._get_pokemon_sprite(player_pokemon, front=False)
        if player_sprite:
            player_sprite = self._remove_background(player_sprite).resize(POKEMON_SPRITE_SIZE)
            frame.paste(player_sprite, (80, 180), player_sprite)

        # Player info box (bottom-right)
        self._draw_info_box(draw, 460, 220, player_pokemon, font, small_font,
                            label=player_pokemon.pokemonName.upper(), show_current_hp=True)

        # -- Battle log / text area at bottom --
        log_text = battle_log if battle_log else f"Turn {turn_number} - Choose your move!"
        frame = self._draw_dialog_box(frame, enemy_name, log_text,
                                       text_box_color=(0, 0, 0, 200))

        return frame

    def render_transition(self, image: Optional[str] = None,
                          text: Optional[str] = None,
                          bg_color: tuple = (0, 0, 0)) -> Image.Image:
        """Render a transition frame — dramatic pause or effect."""
        if image:
            frame = self._load_effect(image)
        else:
            frame = Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), bg_color + (255,))

        if text:
            draw = ImageDraw.Draw(frame)
            font = self.get_font(36)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = (FRAME_WIDTH - tw) // 2
            y = (FRAME_HEIGHT - th) // 2

            # Draw text shadow then text
            draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 200), font=font)
            draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

        return frame

    def render_finale(self, title: str, text: str,
                      background: Optional[str] = None,
                      trainer_name: Optional[str] = None) -> Image.Image:
        """Render the ending/credits frame."""
        frame = self._load_background(background) if background else \
            Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), (10, 10, 30, 255))

        if trainer_name:
            title = title.replace("{trainer_name}", trainer_name)
            text = text.replace("{trainer_name}", trainer_name)

        draw = ImageDraw.Draw(frame)
        title_font = self.get_font(48)
        body_font = self.get_font(24)

        # Title centered near top
        bbox = draw.textbbox((0, 0), title, font=title_font)
        tw = bbox[2] - bbox[0]
        x = (FRAME_WIDTH - tw) // 2
        draw.text((x + 2, 42), title, fill=(0, 0, 0, 180), font=title_font)
        draw.text((x, 40), title, fill=(255, 215, 0, 255), font=title_font)

        # Body text centered
        lines = self._wrap_text(text, body_font, FRAME_WIDTH - 80)
        y = 140
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=body_font)
            lw = bbox[2] - bbox[0]
            lx = (FRAME_WIDTH - lw) // 2
            draw.text((lx, y), line, fill=(255, 255, 255, 255), font=body_font)
            y += 34

        return frame

    # ------------------------------------------------------------------
    # Conversion helper
    # ------------------------------------------------------------------

    def to_discord_file(self, img: Image.Image, filename: str = "scene.png") -> 'BytesIO':
        """Convert a PIL Image to a BytesIO buffer suitable for discord.File."""
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_background(self, filename: Optional[str]) -> Image.Image:
        """Load a background image or create a default dark one."""
        if filename:
            path = os.path.join(self._bg_dir, filename)
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                return img.resize((FRAME_WIDTH, FRAME_HEIGHT))
        # Default dark background
        return Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), (20, 20, 40, 255))

    def _load_character(self, filename: str) -> Optional[Image.Image]:
        """Load a character sprite from the finale characters directory."""
        path = os.path.join(self._char_dir, filename)
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
        # Fallback: try the global trainers directory
        fallback = os.path.join(self._base_dir, 'sprites', 'trainers', filename)
        if os.path.exists(fallback):
            return Image.open(fallback).convert("RGBA")
        return None

    def _load_effect(self, filename: str) -> Image.Image:
        """Load an effect/transition image."""
        path = os.path.join(self._effects_dir, filename)
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
            return img.resize((FRAME_WIDTH, FRAME_HEIGHT))
        return Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0, 255))

    def _composite_character(self, frame: Image.Image, sprite_filename: str,
                             position: str = "right") -> Image.Image:
        """Paste a character sprite onto the frame at the given position."""
        sprite = self._load_character(sprite_filename)
        if not sprite:
            return frame

        sprite = self._remove_background(sprite).resize(CHARACTER_SPRITE_SIZE)
        result = frame.copy()

        if position == "left":
            x = 30
        elif position == "center":
            x = (FRAME_WIDTH - CHARACTER_SPRITE_SIZE[0]) // 2
        else:  # right
            x = FRAME_WIDTH - CHARACTER_SPRITE_SIZE[0] - 30

        # Position character above the dialog box
        y = DIALOG_BOX_Y - CHARACTER_SPRITE_SIZE[1] + 20
        if y < 0:
            y = 10

        result.paste(sprite, (x, y), sprite)
        return result

    def _draw_dialog_box(self, frame: Image.Image, speaker: str, text: str,
                         text_box_color: tuple = (0, 0, 0, 180)) -> Image.Image:
        """Draw a translucent dialog box with speaker name and wrapped text."""
        result = frame.copy()
        overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Dialog box background
        box_x1 = DIALOG_BOX_MARGIN
        box_y1 = DIALOG_BOX_Y
        box_x2 = FRAME_WIDTH - DIALOG_BOX_MARGIN
        box_y2 = FRAME_HEIGHT - DIALOG_BOX_MARGIN

        overlay_draw.rounded_rectangle(
            [box_x1, box_y1, box_x2, box_y2],
            radius=12,
            fill=text_box_color
        )

        # Speaker name tag
        if speaker:
            tag_x1 = box_x1 + 10
            tag_y1 = box_y1 - SPEAKER_TAG_HEIGHT + 4
            tag_x2 = tag_x1 + SPEAKER_TAG_WIDTH
            tag_y2 = box_y1 + 4

            overlay_draw.rounded_rectangle(
                [tag_x1, tag_y1, tag_x2, tag_y2],
                radius=8,
                fill=(40, 40, 80, 220)
            )

            speaker_font = self.get_font(18)
            overlay_draw.text(
                (tag_x1 + 12, tag_y1 + 5),
                speaker,
                fill=(255, 255, 255, 255),
                font=speaker_font
            )

        # Composite overlay onto frame
        result = Image.alpha_composite(result, overlay)

        # Now draw the actual text on top
        draw = ImageDraw.Draw(result)
        text_font = self.get_font(24)
        wrapped = self._wrap_text(text, text_font,
                                   (box_x2 - box_x1) - (DIALOG_BOX_PADDING * 2))
        text_y = box_y1 + DIALOG_BOX_PADDING
        for line in wrapped:
            draw.text((box_x1 + DIALOG_BOX_PADDING, text_y),
                      line, fill=(255, 255, 255, 255), font=text_font)
            text_y += 30

        return result

    def _draw_info_box(self, draw: ImageDraw.Draw, x: int, y: int,
                       pokemon: 'PokemonClass', font, small_font,
                       label: str = "", show_current_hp: bool = False):
        """Draw a Pokemon info box (name, level, HP bar) at position."""
        stats = pokemon.getPokeStats()
        max_hp = stats['hp']
        current_hp = pokemon.currentHP
        hp_pct = (current_hp / max_hp * 100) if max_hp > 0 else 0

        # Semi-transparent background for readability
        # (drawn by caller since ImageDraw can't do alpha rects directly — 
        #  we just draw the text content here)

        # Name and level
        draw.text((x, y), label, fill=(255, 255, 255), font=font)
        draw.text((x + 10, y + 28), f"Lv.{pokemon.currentLevel}", fill=(200, 200, 200), font=small_font)

        # HP bar background
        bar_x = x + 10
        bar_y = y + 52
        draw.rectangle([bar_x, bar_y, bar_x + HP_BAR_WIDTH, bar_y + HP_BAR_HEIGHT],
                        fill=(60, 60, 60))

        # HP bar fill
        fill_width = int(HP_BAR_WIDTH * (hp_pct / 100))
        if hp_pct > 50:
            bar_color = (34, 197, 94)   # green
        elif hp_pct > 25:
            bar_color = (234, 179, 8)   # yellow
        else:
            bar_color = (239, 68, 68)   # red

        if fill_width > 0:
            draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + HP_BAR_HEIGHT],
                            fill=bar_color)

        # HP text
        if show_current_hp:
            draw.text((bar_x, bar_y + 14), f"{current_hp}/{max_hp}",
                      fill=(255, 255, 255), font=small_font)

    def _get_pokemon_sprite(self, pokemon, front: bool = True):
        """Get a Pokemon sprite — checks local finale sprites first, then URL."""
        img = None

        # Check for FinalePokemon with local sprite
        if front and hasattr(pokemon, '_front_sprite') and pokemon._front_sprite:
            path = os.path.join(self._char_dir, pokemon._front_sprite)
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGBA")
                except Exception:
                    pass

        # Fall back to URL
        if img is None:
            try:
                url = pokemon.frontSpriteURL if front else pokemon.backSpriteURL
                if url:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content)).convert("RGBA")
            except Exception:
                pass

        # Remove white/black backgrounds from all sprites
        if img is not None:
            img = self._remove_white_background(img)

        return img

    def _remove_background(self, img: Image.Image) -> Image.Image:
        """Remove transparent/black background from sprite. Reused from imagegenclass."""
        rgba = img.convert("RGBA")
        pixel_data = rgba.load()
        width, height = rgba.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixel_data[x, y]
                if r == 0 and g == 0 and b == 0 and a == 0:
                    pixel_data[x, y] = (255, 255, 255, 0)
        return rgba

    def _remove_white_background(self, img: Image.Image, threshold: int = 240) -> Image.Image:
        """Remove white background from sprites."""
        rgba = img.convert("RGBA")
        pixel_data = rgba.load()
        width, height = rgba.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixel_data[x, y]
                if r >= threshold and g >= threshold and b >= threshold:
                    pixel_data[x, y] = (255, 255, 255, 0)
                elif r == 0 and g == 0 and b == 0 and a == 0:
                    pixel_data[x, y] = (255, 255, 255, 0)
        return rgba

    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """Word-wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [""]