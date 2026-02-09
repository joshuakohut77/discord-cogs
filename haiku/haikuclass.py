import pronouncing
import re
from .dbclass import db as dbconn

"""
Detects accidental haikus in messages and logs them to the database.
A haiku has a 5-7-5 syllable pattern across three lines.
"""

class HaikuDetector:
    
    @staticmethod
    def count_syllables(word):
        """Count syllables in a word using the pronouncing library"""
        # Remove punctuation and convert to lowercase
        word = re.sub(r'[^\w\s]', '', word.lower())
        
        if not word:
            return 0
        
        # Get pronunciation(s) for the word
        phones = pronouncing.phones_for_word(word)
        
        if phones:
            # Use the first pronunciation and count stress markers
            return pronouncing.syllable_count(phones[0])
        else:
            # Fallback: simple vowel counting heuristic
            return HaikuDetector._count_syllables_fallback(word)
    
    @staticmethod
    def _count_syllables_fallback(word):
        """Fallback syllable counter using simple vowel rules"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent 'e' at the end
        if word.endswith('e'):
            syllable_count -= 1
        
        # Every word has at least one syllable
        if syllable_count == 0:
            syllable_count = 1
            
        return syllable_count
    
    @staticmethod
    def split_into_lines(words, target_pattern=[5, 7, 5]):
        """
        Try to split words into lines matching the syllable pattern.
        Returns a list of lines (each line is a list of words) or None if no match.
        """
        lines = []
        current_line = []
        current_syllables = 0
        target_index = 0
        
        for word in words:
            syllables = HaikuDetector.count_syllables(word)
            
            if current_syllables + syllables < target_pattern[target_index]:
                # Add to current line
                current_line.append(word)
                current_syllables += syllables
            elif current_syllables + syllables == target_pattern[target_index]:
                # Perfect match for this line
                current_line.append(word)
                lines.append(current_line)
                current_line = []
                current_syllables = 0
                target_index += 1
                
                # Check if we've completed the haiku
                if target_index >= len(target_pattern):
                    return lines
            else:
                # Would exceed target, haiku not possible with this split
                return None
        
        return None
    
    @staticmethod
    def detect_haiku(text):
        """
        Detect if the text contains a haiku (5-7-5 syllable pattern).
        Returns formatted haiku lines or None if not a haiku.
        """
        # Clean and split text into words
        text = text.strip()
        words = text.split()
        
        # Need at least 3 words for a haiku
        if len(words) < 3:
            return None
        
        # Try to find a 5-7-5 pattern
        lines = HaikuDetector.split_into_lines(words)
        
        if lines and len(lines) == 3:
            # Format as haiku with line breaks
            formatted_lines = [' '.join(line) for line in lines]
            return formatted_lines
        
        return None
    
    @staticmethod
    def insert_haiku(user_id, username, guild_id, channel_id, message_id, original_text, formatted_haiku):
        """Insert a detected haiku into the database"""
        db = dbconn()
        
        queryString = """
            INSERT INTO "haiku"
            ("UserId", "Username", "GuildId", "ChannelId", "MessageId", "OriginalText", "FormattedHaiku") 
            VALUES (%(user_id)s, %(username)s, %(guild_id)s, %(channel_id)s, %(message_id)s, %(original_text)s, %(formatted_haiku)s)
        """
        
        values = {
            'user_id': str(user_id),
            'username': str(username),
            'guild_id': str(guild_id),
            'channel_id': str(channel_id),
            'message_id': str(message_id),
            'original_text': original_text,
            'formatted_haiku': '\n'.join(formatted_haiku)
        }
        
        db.execute(queryString, values)
    
    @staticmethod
    def get_haiku_count():
        """Get the total count of haikus in the database"""
        db = dbconn()
        queryString = 'SELECT COUNT(*) FROM haiku;'
        result = db.querySingle(queryString)
        return result[0] if result else 0
    
    @staticmethod
    def get_user_haiku_count(user_id):
        """Get the count of haikus for a specific user"""
        db = dbconn()
        queryString = 'SELECT COUNT(*) FROM haiku WHERE "UserId" = %(user_id)s;'
        result = db.querySingle(queryString, {'user_id': str(user_id)})
        return result[0] if result else 0
    
    @staticmethod
    def get_top_haiku_users(limit=10):
        """Get the top haiku creators"""
        db = dbconn()
        queryString = """
            SELECT "Username", COUNT(*) as haiku_count 
            FROM haiku 
            GROUP BY "Username" 
            ORDER BY haiku_count DESC 
            LIMIT %(limit)s;
        """
        result = db.queryAll(queryString, {'limit': limit})
        return result