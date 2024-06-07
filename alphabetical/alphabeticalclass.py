from discord import embeds
import discord

"""
Checks to see if a message is in alphabetical order and returns an embed message saying so.
"""

class Alphabetical(): 

    def are_words_alphabetical_order(sentence):
        # Split the sentence into words
        words = sentence.split()
        if len(words) < 5:
            return False
        # Get the first letter of each word, converted to lowercase for case insensitivity
        first_letters = [word[0].lower() for word in words]
        # Compare the list of first letters with its sorted version
        return first_letters == sorted(first_letters)
