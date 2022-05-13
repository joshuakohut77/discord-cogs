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

