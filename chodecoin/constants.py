# ---------------------------------------------------------------
# ChodeCoin display constants
# Swap COIN_EMOJI between the two options to test in embeds.
# ---------------------------------------------------------------
import re
COIN_EMOJI = "<:ChodeCoin:1479593199554269318>"

# Auto-derive the CDN image URL from whichever emoji is active.
# Used for embed thumbnails where Discord needs an image URL, not an emoji string.
_emoji_id_match = re.search(r"(\d+)>$", COIN_EMOJI)
COIN_EMOJI_URL = f"https://cdn.discordapp.com/emojis/{_emoji_id_match.group(1)}.png?size=128" if _emoji_id_match else None

EMBED_COLOR = 0xffa72e  # gold