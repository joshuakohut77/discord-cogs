import requests
import discord
from typing import Tuple, Optional
import logging

log = logging.getLogger("red.owenWilson")

class Wow:
    """Handles fetching and processing Owen Wilson 'Wow' clips from the API."""
    
    API_URL = "https://owen-wilson-wow-api.onrender.com/wows/random"
    TEMP_FILE_PATH = "/tempfiles/wowclip.mp4"
    TIMEOUT = 10  # seconds
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
    
    def _fetch_random_wow(self) -> Optional[dict]:
        """Fetch a random wow from the API."""
        try:
            response = self.session.get(self.API_URL, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response.json()[0]
        except (requests.RequestException, IndexError, KeyError) as e:
            log.error(f"Failed to fetch wow data: {e}")
            return None
    
    def _download_video(self, video_url: str) -> bool:
        """Download video file to temporary location."""
        try:
            response = self.session.get(video_url, timeout=self.TIMEOUT)
            response.raise_for_status()
            with open(self.TEMP_FILE_PATH, 'wb') as f:
                f.write(response.content)
            return True
        except (requests.RequestException, IOError) as e:
            log.error(f"Failed to download video: {e}")
            return False
    
    def _create_embed(self, data: dict) -> discord.Embed:
        """Create Discord embed from wow data."""
        embed = discord.Embed(
            title="Owen Wilson",
            url="https://www.tomorrowtides.com/owen-wilson-movies.html",
            color=0x0b1bf4
        )
        embed.set_thumbnail(url=data.get("poster", ""))
        embed.add_field(name="Movie", value=data.get("movie", "Unknown"), inline=True)
        embed.add_field(name="Year", value=str(data.get("year", "N/A")), inline=True)
        embed.add_field(name="Character", value=data.get("character", "Unknown"), inline=True)
        embed.add_field(
            name="Wow in Movie",
            value=f"{data.get('current_wow_in_movie', 0)}/{data.get('total_wows_in_movie', 0)}",
            inline=True
        )
        embed.add_field(name="Full Line", value=data.get("full_line", "..."), inline=False)
        return embed
    
    def get_wow(self) -> Optional[Tuple[discord.Embed, discord.File]]:
        """
        Fetch a random Owen Wilson 'Wow' clip and return embed with video file.
        
        Returns:
            Tuple of (embed, file) or None if failed
        """
        data = self._fetch_random_wow()
        if not data:
            return None
        
        # Get highest quality video URL
        video_dict = data.get("video", {})
        if not video_dict:
            log.error("No video URLs in API response")
            return None
        
        video_url = next(iter(video_dict.values()))
        
        # Download video
        if not self._download_video(video_url):
            return None
        
        # Create embed and file objects
        embed = self._create_embed(data)
        file = discord.File(self.TEMP_FILE_PATH)
        
        return embed, file
    
    def close(self):
        """Close the requests session."""
        self.session.close()