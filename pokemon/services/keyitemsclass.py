# keyitems class
import sys
from dbclass import db as dbconn
from loggerclass import logger as log

# Class Logger
logger = log()

class keyitems:
    def __init__(self, discordId):
        self.statuscode = 69
        self.message = ''

        self.discordId = discordId
        # below are all Booleans
        self.HM01 = False
        self.HM02 = False
        self.HM03 = False
        self.HM04 = False
        self.HM05 = False
        self.badge_boulder = False
        self.badge_cascade = False
        self.badge_thunder = False
        self.badge_rainbow = False
        self.badge_soul = False
        self.badge_marsh = False
        self.badge_volcano = False
        self.badge_earth = False
        self.pokeflute = False
        self.silph_scope = False
        self.oaks_parcel = False
        self.ss_ticket = False
        self.bicycle = False
        self.old_rod = False
        self.good_rod = False
        self.super_rod = False
        self.item_finder = False
        # populate keyitems object
        self.__loadKeyItems()

    

    def __loadKeyItems(self):
        """ loads key items from database into object """
        try:
            db = dbconn()
            queryString = '''
                SELECT 
                    "HM01", "HM02", "HM03", "HM04", "HM05", 
                    badge_boulder, badge_cascade, badge_thunder, badge_rainbow, 
                    badge_soul, badge_marsh, badge_volcano, badge_earth, 
                    pokeflute, 
                    silph_scope, 
                    oaks_parcel, 
                    ss_ticket, 
                    bicycle, "old_rod", "good_rod", "super_rod", 
                    item_finder
                    FROM keyitems WHERE discord_id=%(discordId)s
            '''
            result = db.querySingle(queryString, { 'discordId': self.discordId })
            if result:
                self.HM01 = result[0]
                self.HM02 = result[1]
                self.HM03 = result[2]
                self.HM04 = result[3]
                self.HM05 = result[4]
                self.badge_boulder = result[5]
                self.badge_cascade = result[6]
                self.badge_thunder = result[7]
                self.badge_rainbow = result[8]
                self.badge_soul = result[9]
                self.badge_marsh = result[10]
                self.badge_volcano = result[11]
                self.badge_earth = result[12]
                self.pokeflute = result[13]
                self.silph_scope = result[14]
                self.oaks_parcel = result[15]
                self.ss_ticket = result[16]
                self.bicycle = result[17]
                self.old_rod = result[18]
                self.good_rod = result[19]
                self.super_rod = result[20]
                self.item_finder = result[21]
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
    
    def save(self):
        """ saves a users key items """
        try:
            db = dbconn()
            if self.discordId is not None:
                updateString = '''
                UPDATE keyitems
	                SET "HM01"=%(HM01)s, "HM02"=%(HM02)s, "HM03"=%(HM03)s, "HM04"=%(HM04)s, "HM05"=%(HM05)s, 
                    badge_boulder=%(badge_boulder)s, badge_cascade=%(badge_cascade)s, 
                    badge_thunder=%(badge_thunder)s, badge_rainbow=%(badge_rainbow)s, 
                    badge_soul=%(badge_soul)s, badge_marsh=%(badge_marsh)s, 
                    badge_volcano=%(badge_volcano)s, badge_earth=%(badge_earth)s, 
                    pokeflute=%(pokeflute)s, 
                    silph_scope=%(silph_scope)s, 
                    oaks_parcel=%(oaks_parcel)s, 
                    ss_ticket=%(ss_ticket)s, 
                    bicycle=%(bicycle)s, 
                    "old_rod"=%(old_rod)s, "good_rod"=%(good_rod)s, "super_rod"=%(super_rod)s, 
                    item_finder=%(item_finder)s
	                    WHERE discord_id=%(discordId)s;
                '''
                values = { 'HM01':self.HM01, 'HM02': self.HM02, 'HM03':self.HM03, 'HM04':self.HM04, 'HM05':self.HM05,
                            'badge_boulder':self.badge_boulder, 'badge_cascade':self.badge_cascade,
                            'badge_thunder':self.badge_thunder, 'badge_rainbow':self.badge_rainbow,
                            'badge_soul':self.badge_soul, 'badge_marsh':self.badge_marsh,
                            'badge_volcano':self.badge_volcano, 'badge_earth':self.badge_earth,
                            'pokeflute':self.pokeflute, 'silph_scope':self.silph_scope,
                            'oaks_parcel':self.oaks_parcel, 'ss_ticket':self.ss_ticket,
                            'bicycle':self.bicycle, 'item_finder':self.item_finder,
                            'old_rod':self.old_rod, 'good_rod':self.good_rod, 'super_rod':self.super_rod,
                            'discordId':self.discordId }
                db.execute(updateString, values)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
        