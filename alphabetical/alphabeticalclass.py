import re
import discord
from typing import Optional
import logging

log = logging.getLogger("red.alphabetical")


class AlphabeticalChecker:
    """Checks if messages have words in alphabetical order."""
    
    MIN_WORDS = 5
    EMBED_COLOR = 0x0b1bf4
    
    # Compile regex pattern once for efficiency
    NON_ALPHA_PATTERN = re.compile(r'[^a-zA-Z\s]')
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Remove special characters and convert to lowercase."""
        return AlphabeticalChecker.NON_ALPHA_PATTERN.sub('', text).lower()
    
    @staticmethod
    def get_words(text: str) -> list[str]:
        """Extract words from normalized text."""
        normalized = AlphabeticalChecker.normalize_text(text)
        return normalized.split()
    
    @staticmethod
    def are_first_letters_alphabetical(text: str) -> bool:
        """
        Check if the first letters of words are in alphabetical order.
        Requires at least MIN_WORDS words.
        
        Args:
            text: The text to check
            
        Returns:
            True if first letters are alphabetical and word count >= MIN_WORDS
        """
        words = AlphabeticalChecker.get_words(text)
        
        if len(words) < AlphabeticalChecker.MIN_WORDS:
            return False
        
        # Get first letter of each word
        first_letters = [word[0] for word in words if word]
        
        # Check if sorted
        return first_letters == sorted(first_letters)
    
    @staticmethod
    def are_words_alphabetical(text: str) -> bool:
        """
        Check if entire words are in alphabetical order relative to each other.
        
        Args:
            text: The text to check
            
        Returns:
            True if words are in alphabetical order
        """
        words = AlphabeticalChecker.get_words(text)
        
        if len(words) < 2:
            return False
        
        # Check if each word is <= the next word
        return all(words[i] <= words[i + 1] for i in range(len(words) - 1))
    
    @staticmethod
    def check_message(text: str) -> bool:
        """
        Check if message meets all alphabetical criteria.
        
        Args:
            text: The text to check
            
        Returns:
            True if both first letters and full words are alphabetical
        """
        return (
            AlphabeticalChecker.are_first_letters_alphabetical(text) and
            AlphabeticalChecker.are_words_alphabetical(text)
        )
    
    @staticmethod
    def create_embed() -> discord.Embed:
        """Create the response embed for alphabetical messages."""
        return discord.Embed(
            title="Alphabet Soup!",
            description="All your words are in alphabetical order.",
            color=AlphabeticalChecker.EMBED_COLOR
        )