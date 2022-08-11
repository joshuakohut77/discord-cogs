import requests
import json
from discord import embeds
import discord

"""
Utilizes the Wow api as found here: https://owen-wilson-wow-api.herokuapp.com/

Example api response for a random "wow" request
[
  {
    "movie": "Father Figures",
    "year": 2017,
    "release_date": "2017-12-13",
    "director": "Lawrence Sher",
    "character": "Kyle Reynolds",
    "movie_duration": "01:52:50",
    "timestamp": "00:06:46",
    "full_line": "There's a saying in Hawaii that goes a little something like this: 'Ohana makawao hihi Wailuku ukulele aloha adios.'",
    "current_wow_in_movie": 1,
    "total_wows_in_movie": 1,
    "poster": "https://images.ctfassets.net/bs8ntwkklfua/4FLpI0gdI6hgH3ZJEKOOgf/6c8a48542a67d8728fa0769368d9e16a/Father_Figures_Poster.jpg",
    "video": {
      "1080p": "https://videos.ctfassets.net/bs8ntwkklfua/2xYriI4IEehecWGtlZ8kXf/d2cdc17514c8674a14007e34d05609ec/Father_Figures_Wow_1080p.mp4",
      "720p": "https://videos.ctfassets.net/bs8ntwkklfua/3NA6JsOi7f4XFYRT6Mib69/3f8aba6f0718dfa917e9b92c0993259c/Father_Figures_Wow_720p.mp4",
      "480p": "https://videos.ctfassets.net/bs8ntwkklfua/01AEKYe9fuy5dDvtqcGEee/3884ada8f930c59329ca09431446dd18/Father_Figures_Wow_480p.mp4",
      "360p": "https://videos.ctfassets.net/bs8ntwkklfua/7Lw9MOxSuUmOKjhDIUBsG3/e645af7ee5043211d2103eca7188f2f2/Father_Figures_Wow_360p.mp4"
    },
    "audio": "https://assets.ctfassets.net/bs8ntwkklfua/6a4q7B0EwLknSOoN4vAOQU/564fe702d4ed75a6868fd092552a5120/Father_Figures_Wow.mp3"
  }
]
"""

class Wow(): 

    # will return the full api response. Needs parse in a separate function to return only desired link
    def getRandomWow(self):
        url = "https://owen-wilson-wow-api.herokuapp.com/wows/random"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        jsonResponse = json.loads(response.text)[0]
        return(jsonResponse)

    def getWowVideo(self):
        # Call the function to get the JSON response, then return the video link for the highest quality URL
        jsonResponse = Wow.getRandomWow()
        highestQuality = list(jsonResponse['video'].keys())[0]
        videoLink = jsonResponse['video'][highestQuality]
        return videoLink

    def getWow(self):
        url = "https://owen-wilson-wow-api.herokuapp.com/wows/random"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        jsonResponse = json.loads(response.text)[0]
        highestQuality = list(jsonResponse['video'].keys())[0]
        headerCard = "```"
        headerCard += "\n"
        headerCard += "Movie: "
        headerCard += jsonResponse['movie']
        headerCard += "\n"
        headerCard += "Year: "
        headerCard += str(jsonResponse['year'])
        headerCard += "\n"
        headerCard += "Character: "
        headerCard += jsonResponse['character']
        headerCard += "\n"
        headerCard += "Full Line: "
        headerCard += jsonResponse['full_line']
        headerCard += "\n"
        headerCard += "```"
        headerCard += "\n"
        videoLink = jsonResponse['video'][highestQuality]
        
        embed = discord.Embed()
        embed=discord.Embed(title="Owen Wilson", color=0x0b1bf4)
        embed.set_thumbnail(url=jsonResponse["poster"])
        embed.add_field(name="Movie", value=jsonResponse["movie"], inline=True)
        embed.add_field(name="Year", value=str(jsonResponse['year']), inline=True)
        embed.add_field(name="Character", value=jsonResponse['character'], inline=True)
        embed.add_field(name="Full Line", value=jsonResponse['full_line'], inline=True)
        return embed, videoLink

        # return headerCard, videoLink