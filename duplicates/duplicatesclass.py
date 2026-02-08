from discord import embeds
import discord
import hashlib
from .dbclass import db as dbconn

"""
Saves and checks to see if a message is a duplicate and will respond with when those exact messages have been sent and by whom. 
"""

class Duplicates(): 

    @staticmethod
    def has_extension(file_name):
        """Check if the message contains common media file extensions or media links"""
        extensions = ('.gif', '.png', '.jpg', '.jpeg', '.mp4', '.webm')
        media_domains = ('tenor.com', 'giphy.com', 'imgur.com', 'gfycat.com')
        
        file_lower = file_name.lower()
        
        # Check for file extensions
        if any(file_lower.endswith(ext) for ext in extensions):
            return True
        
        # Check for media domain links
        if any(domain in file_lower for domain in media_domains):
            return True
        
        return False

    @staticmethod
    def hash_string(input_string):
        """Create SHA256 hash of the input string"""
        # Create a new sha256 hash object
        sha256 = hashlib.sha256()
        
        # Update the hash object with the bytes of the string
        sha256.update(input_string.encode('utf-8'))
        
        # Get the hexadecimal representation of the hash
        hex_hash = sha256.hexdigest()
        
        return hex_hash

    @staticmethod
    def insert_message(msgHash, username):
        """Insert a new message hash into the database"""
        db = dbconn()
        
        queryString = """INSERT INTO "duplicate_message"("MessageHash", "Username") VALUES (%(msgHash)s, %(username)s)""" 
        values = {'msgHash': msgHash, 'username': str(username) }
        db.execute(queryString, values)
        return

    @staticmethod
    def select_duplicates(msgHash):
        """Select all duplicate messages for a given hash"""
        db = dbconn()
        
        queryString = '''
        SELECT * 
            FROM public."duplicate_message"
            WHERE "MessageHash" = %(msgHash)s
            ORDER BY "Timestamp" ASC'''
        result = db.queryAll(queryString, {'msgHash': msgHash})
        
        duplicateList = []
        
        for row in result:
            username = row[2]
            timestamp = row[3]
            duplicateList.append({'username': username, 'timestamp': timestamp})
        
        return duplicateList

    @staticmethod
    def get_table_size():
        """Get the total size of the duplicate_message table"""
        db = dbconn()
        queryString = '''
            SELECT pg_size_pretty(
                pg_total_relation_size('duplicate_message')) 
                    AS total_size;'''
        result = db.querySingle(queryString)

        return result[0]
    
    @staticmethod
    def get_message_count():
        """Get the total count of messages in the database"""
        db = dbconn()
        queryString = '''
            SELECT COUNT(*) 
                FROM duplicate_message;'''
        result = db.querySingle(queryString)

        return result[0]
    
    @staticmethod
    def get_query_time():
        """Get the execution time for a sample duplicate query"""
        db = dbconn()
        queryString = '''
            EXPLAIN ANALYZE 
                SELECT * 
                    FROM duplicate_message 
                        WHERE "MessageHash" = 'e8d3572ceef0e6b188ba8e84205e5a248afe4c5374cba769d392f9ba99021cd1';'''
        result = db.queryAll(queryString)
        for value in result:
            if 'Execution Time' in value[0]:
                return value[0]
        return "Query time not found"

    @staticmethod
    def cleanup_old_messages(days=180):
        """Delete messages older than the specified number of days
        
        Args:
            days: Number of days to keep (default: 180)
            
        Returns:
            Number of rows deleted
        """
        db = dbconn()
        
        # First get the count of rows that will be deleted
        count_query = '''
            SELECT COUNT(*) 
                FROM duplicate_message 
                WHERE "Timestamp" < NOW() - INTERVAL '%s days'
        '''
        count_result = db.querySingle(count_query % days)
        rows_to_delete = count_result[0] if count_result else 0
        
        # Delete old messages
        delete_query = '''
            DELETE FROM duplicate_message 
            WHERE "Timestamp" < NOW() - INTERVAL '%s days'
        '''
        db.execute(delete_query % days)
        
        return rows_to_delete