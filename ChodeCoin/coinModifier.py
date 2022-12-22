import requests
import json
from discord import embeds
import discord

class CoinModifier(): 

    # will return the full api response. Needs parse in a separate function to return only desired link
    def addCoin(self):
        userExists = userExists()
        return("Coin added")

    def subtractCoin(self):
        userExists = userExists()
        return("Coin subtracted")

    def userExists(self):
        # if User exists, return true, if not return false
        return False
