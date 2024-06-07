from discord import embeds
import discord
import hashlib
from .dbclass import db as dbconn

"""
Saves and checks to see if a message is a duplicate and will respond with when those exact messages have been sent and by whom. 
"""

class Duplicates(): 

    def has_extension(file_name):
        extensions = ('.gif', '.png', '.jpg', '.jpeg', '.mp4', '.webm', '.com')
        return file_name.lower().endswith(extensions)

    def hash_string(input_string):
        # Create a new sha256 hash object
        sha256 = hashlib.sha256()
        
        # Update the hash object with the bytes of the string
        sha256.update(input_string.encode('utf-8'))
        
        # Get the hexadecimal representation of the hash
        hex_hash = sha256.hexdigest()
        
        return hex_hash

    def insert_message(msgHash, username):
        
        db = dbconn()
        
        queryString = """INSERT INTO "duplicate_message"("MessageHash", "Username") VALUES (%(msgHash)s, %(username)s)""" 
        values = {'msgHash': msgHash, 'username': str(username) }
        db.execute(queryString, values)
        return

    def select_duplicates(msgHash):
        
        db = dbconn()
        
        queryString = '''
        SELECT * 
            FROM public."duplicate_message"
            WHERE "MessageHash" = %(msgHash)s'''
        result = db.queryAll(queryString, {'msgHash': msgHash})
        
        duplicateList = []
        
        for row in result:
            username = row[2]
            timestamp = row[3]
            duplicateList.append({'username': username, 'timestamp': timestamp})
        
        return duplicateList

    def get_table_size():
        db = dbconn()
        queryString = '''
            SELECT pg_size_pretty(
                pg_total_relation_size('duplicate_message')) 
                    AS total_size;'''
        result = db.querySingle(queryString)

        return result[0]
    
    def get_message_count():
        db = dbconn()
        queryString = '''
            SELECT COUNT(*) 
                FROM duplicate_message;'''
        result = db.querySingle(queryString)

        return result[0]