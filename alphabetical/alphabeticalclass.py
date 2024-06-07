from discord import embeds
import discord

"""
Checks to see if a message is in alphabetical order and returns an embed message saying so.
"""

class Alphabetical(): 

    def are_words_alphabetical_order(sentence):
        # Split the sentence into words
        words = sentence.split()
        # Get the first letter of each word, converted to lowercase for case insensitivity
        first_letters = [word[0].lower() for word in words]
        # Compare the list of first letters with its sorted version
        return first_letters == sorted(first_letters)

    def postAlphabeticalMessage(self):
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
