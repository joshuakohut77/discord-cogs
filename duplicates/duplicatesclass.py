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
        queryString = """INSERT INTO public."duplicateMessage"("MessageHash", "Username") VALUES ('abc123', ' + str(username) + ')"""
        values = (msgHash, username)
        db.execute(queryString)
        return
