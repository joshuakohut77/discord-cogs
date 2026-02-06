# leaderboard class

import sys
from dbclass import db as dbconn
from loggerclass import logger as log

# Class Logger
logger = log()

class leaderboard:
    def __init__(self, discordId):
        self.statuscode = 69 
        self.message = '' 

        self.discordId = str(discordId)
        self.total_battles = None
        self.total_victory = None
        self.total_defeat = None
        self.total_actions = None
        self.total_balls_thrown = None
        self.total_catch = None
        self.total_run_away = None
        self.total_released = None
        self.total_evolved = None
        self.total_easter_eggs = None
        self.total_completions = None
        self.total_trades = None

    def load(self):
        """ loads and populates the class object """
        try:
            db = dbconn()
            queryString = """
                SELECT total_battles, total_victory, total_defeat, total_actions, 
                    total_balls_thrown, total_catch, total_run_away, total_released, 
                    total_evolved, total_easter_eggs, total_completions, total_trades 
                    FROM leaderboard
                    WHERE discord_id = %(discordId)s
                """
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                self.total_battles = result[0]
                self.total_victory = result[1]
                self.total_defeat = result[2]
                self.total_actions = result[3]
                self.total_balls_thrown = result[4]
                self.total_catch = result[5]
                self.total_run_away = result[6]
                self.total_released = result[7]
                self.total_evolved = result[8]
                self.total_easter_eggs = result[9]
                self.total_completions = result[10]
                self.total_trades = result[11]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db  

    def victory(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_victory = total_victory + 1, total_battles = total_battles + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db   

    def defeat(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_defeat = total_defeat + 1, total_battles = total_battles + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def actions(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_actions = total_actions + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def balls_thrown(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_balls_thrown = total_balls_thrown + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def catch(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_catch = total_catch + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def run_away(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_run_away = total_run_away + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def released(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_released = total_released + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def evolved(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_evolved = total_evolved + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def easter_eggs(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_easter_eggs = total_easter_eggs + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def completions(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_completions = total_completions + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    def trades(self):
        try:
            db = dbconn()
            updateString = "UPDATE leaderboard SET total_trades = total_trades + 1 WHERE discord_id = %(discordId)s"
            db.execute(updateString, { 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db 

    @commands.command()
    async def testegg(self, ctx):
        """Test easter egg tracking"""
        user = ctx.author
        discord_id = str(user.id)
        
        from services.leaderboardclass import leaderboard as LeaderboardClass
        from services.dbclass import db as dbconn
        
        # Step 1: Check if leaderboard row exists
        db = dbconn()
        check_query = "SELECT total_easter_eggs FROM leaderboard WHERE discord_id = %(discordId)s"
        result = db.querySingle(check_query, {'discordId': discord_id})
        
        if result is None:
            await ctx.send(f"❌ **ERROR**: No leaderboard row exists for {user.display_name}!")
            await ctx.send("Creating leaderboard row...")
            
            # Create the row
            insert_query = "INSERT INTO leaderboard (discord_id) VALUES (%(discordId)s) ON CONFLICT DO NOTHING"
            db.execute(insert_query, {'discordId': discord_id})
            
            await ctx.send("✅ Leaderboard row created!")
            result = db.querySingle(check_query, {'discordId': discord_id})
        
        current_count = result[0] if result else 0
        await ctx.send(f"📊 Current easter eggs: **{current_count}**")
        
        # Step 2: Try to increment
        lb = LeaderboardClass(discord_id)
        lb.easter_eggs()
        
        # Check if it worked
        if lb.statuscode == 96:
            await ctx.send(f"❌ **ERROR**: Failed to update! Status code: {lb.statuscode}")
        else:
            await ctx.send("✅ easter_eggs() called successfully!")
        
        # Step 3: Verify the increment
        del db  # Close old connection
        db = dbconn()
        new_result = db.querySingle(check_query, {'discordId': discord_id})
        new_count = new_result[0] if new_result else 0
        
        await ctx.send(f"📊 New easter eggs count: **{new_count}**")
        
        if new_count > current_count:
            await ctx.send("🎉 **SUCCESS!** Easter egg was tracked!")
        else:
            await ctx.send("❌ **FAILED!** Count did not increment.")