import requests
import discord
from typing import Tuple, Optional
import logging

log = logging.getLogger("red.keanuReeves")

class Whoa:
    """Handles fetching and processing Keanu Reeves 'Whoa' clips from the API."""
    
    API_URL = "https://whoa.onrender.com/whoas/random"
    TEMP_FILE_PATH = "/tempfiles/whoaclip.mp4"
    TIMEOUT = 10  # seconds
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
    
    def _fetch_random_whoa(self) -> Optional[dict]:
        """Fetch a random whoa from the API."""
        try:
            response = self.session.get(self.API_URL, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response.json()[0]
        except (requests.RequestException, IndexError, KeyError) as e:
            log.error(f"Failed to fetch whoa data: {e}")
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
        """Create Discord embed from whoa data."""
        embed = discord.Embed(
            title="Keanu Reeves",
            url="https://www.tomorrowtides.com/keanu-reeves-movies.html",
            color=0x0b1bf4
        )
        embed.set_thumbnail(url=data.get("poster", ""))
        embed.add_field(name="Movie", value=data.get("movie", "Unknown"), inline=True)
        embed.add_field(name="Year", value=str(data.get("year", "N/A")), inline=True)
        embed.add_field(name="Character", value=data.get("character", "Unknown"), inline=True)
        embed.add_field(
            name="Whoa in Movie",
            value=f"{data.get('current_whoa_in_movie', 0)}/{data.get('total_whoas_in_movie', 0)}",
            inline=True
        )
        embed.add_field(name="Full Line", value=data.get("full_line", "..."), inline=False)
        return embed
    
    def get_whoa(self) -> Optional[Tuple[discord.Embed, discord.File]]:
        """
        Fetch a random Keanu Reeves 'Whoa' clip and return embed with video file.
        
        Returns:
            Tuple of (embed, file) or None if failed
        """
        data = self._fetch_random_whoa()
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