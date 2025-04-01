import requests
import json
from discord import embeds
import discord

"""
Utilizes the Wow api found here: https://owen-wilson-wow-api.onrender.com/
"""

class Wow(): 

    # will return the full api response. Needs parse in a separate function to return only desired link
    def getRandomWow(self):
        url = "https://owen-wilson-wow-api.onrender.com/wows/random"
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
        url = "https://owen-wilson-wow-api.onrender.com/wows/random"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        jsonResponse = json.loads(response.text)[0]
        highestQuality = list(jsonResponse['video'].keys())[0]
        videoLink = jsonResponse['video'][highestQuality]
        
        r = requests.get(videoLink)
        with open("/tempfiles/wowclip.mp4", 'wb') as f:
            f.write(r.content) 
        file = discord.File('/tempfiles/wowclip.mp4')

        embed = discord.Embed()
        embed=discord.Embed(title="Owen Wilson", url="https://www.tomorrowtides.com/owen-wilson-movies.html", color=0x0b1bf4)
        embed.set_thumbnail(url=jsonResponse["poster"])
        embed.add_field(name="Movie", value=jsonResponse["movie"], inline=True)
        embed.add_field(name="Year", value=str(jsonResponse['year']), inline=True)
        embed.add_field(name="Character", value=jsonResponse['character'], inline=True)
        embed.add_field(name="Wow in Movie", value=str(jsonResponse['current_wow_in_movie']) + "/" + str(jsonResponse['total_wows_in_movie']), inline=True)
        embed.add_field(name="Full Line", value=jsonResponse['full_line'], inline=False)
        return embed, file
