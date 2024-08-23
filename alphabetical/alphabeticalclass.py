from discord import embeds
import discord

"""
Checks to see if a message is in alphabetical order and returns an embed message saying so.
"""
import re
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

    def check_sentence(sentence):
        """Check if all words in the sentence are in alphabetical order, 
        and if letters in each word are in alphabetical order."""
        
        # Normalize the sentence: remove special characters and convert to lowercase
        normalized_sentence = re.sub(r'[^a-zA-Z\s]', '', sentence).lower()
        
        # Split the sentence into words
        words = normalized_sentence.split()
        
        # Check each word if it is in alphabetical order
        for word in words:
            if not all(word[i] <= word[i+1] for i in range(len(word) - 1)):
                return False
        
        return True