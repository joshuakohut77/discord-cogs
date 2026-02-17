# battle class - this class handles battles from both wild enemy trainers and gym trainers and leaders
import os
import sys
import json
import random
from dbclass import db as dbconn
from inventoryclass import inventory as inv
from keyitemsclass import keyitems as kitems
from questclass import quests as qObj
from loggerclass import logger as log
from models.trainerBattle import TrainerBattleModel
from models.gymLeader import GymLeaderModel

# Class Logger
logger = log()

# this class is to handle encounters with pokemon.
class battle:
    def __init__(self, discordId, locationId, enemyType="wild"):
        # pokemon1 for PvE will always be the discord trainers pokemon
        self.statuscode = 69
        self.message = ''
        self.finale_unlocked = False

        self.discordId = discordId
        self.locationId = locationId
        self.enemyType = enemyType # can be "wild" or "gym"
    
    def battleVictory(self, enemyTrainer: TrainerBattleModel):
        """ handles enemy trainer victory resolution """
        moneyReward = enemyTrainer.money
        
        # update enemy UUID tracker in db
        enemy_uuid = enemyTrainer.enemy_uuid
        self.__insertEnemyCompleted(enemy_uuid)

        # update player reward
        playerInventory = inv(self.discordId)
        playerInventory.money += moneyReward
        playerInventory.save()

        # If player defeated the Champion (elite-4-5), grant elite_four keyitem
        if enemy_uuid == "elite-4-5":
            self.finale_unlocked = True
            playerKeyItems = kitems(self.discordId)
            if not playerKeyItems.elite_four:
                playerKeyItems.elite_four = True
                playerKeyItems.save()

        return

    def gymLeaderVictory(self, gymLeader: GymLeaderModel):
        """ handles gym leader victory resolution """
        moneyReward = gymLeader.money
        keyItem = gymLeader.keyitem
        
        # update enemy UUID tracker in db
        enemy_uuid = gymLeader.enemy_uuid
        self.__insertEnemyCompleted(enemy_uuid)

        # update player reward
        playerInventory = inv(self.discordId)
        playerInventory.money += moneyReward
        playerInventory.save()

        playerKeyItems = kitems(self.discordId)
        if keyItem == "boulder_badge":
            playerKeyItems.badge_boulder = True
        elif keyItem == "rainbow_badge":
            playerKeyItems.badge_rainbow = True
        elif keyItem == "cascade_badge":
            playerKeyItems.badge_cascade = True
        elif keyItem == "volcano_badge":
            playerKeyItems.badge_volcano = True
        elif keyItem == "soul_badge":
            playerKeyItems.badge_soul = True
        elif keyItem == "thunder_badge":
            playerKeyItems.badge_thunder = True
        elif keyItem == "earth_badge":
            playerKeyItems.badge_earth = True
        elif keyItem == "marsh_badge":
            playerKeyItems.badge_marsh = True
        playerKeyItems.save()

    @staticmethod
    def resetEliteFour(discordId):
        """ Removes all elite-4 entries from trainer_battles so the player can retry """
        try:
            db = dbconn()
            deleteString = "DELETE FROM trainer_battles WHERE discord_id = %(discordId)s AND enemy_uuid LIKE 'elite-4-%%'"
            db.execute(deleteString, { 'discordId': discordId })
        except Exception as e:
            logger.error(excInfo=sys.exc_info())
        finally:
            del db

    def getRemainingTrainerCount(self):
        """ returns a count of remaining trainers in the area """
        trainerModelList = self.getTrainerList()
        return len(trainerModelList)

    def getNextTrainer(self):
        """ returns a TrainerBattleModel object to battle against """
        trainerModelList = self.getTrainerList()
        if len(trainerModelList) > 0:
            return trainerModelList[0]
        else:
            return None

    def getGymLeader(self):
        """ returns a TrainerBattleModel of a gym leader """
        gymLeaderObj = None
        remainingTrainers = self.getRemainingTrainerCount()
        if remainingTrainers > 0:
            self.statuscode = 420
            self.message = "You must defeat all Gym Trainers before battling the Gym Leader."
            return
        trainerList = self.getTrainerList(gymLeader=True)
        print(trainerList)
        if trainerList != []:
            gymLeaderObj = trainerList[0]
            enemy_uuid = gymLeaderObj.enemy_uuid
            if self.__checkEnemyCompleted(enemy_uuid):
                self.statuscode = 420
                self.message = "You have already completed this Gym Leader."
                return

        return gymLeaderObj

    def getTrainerList(self, gymLeader=False):
        """ returns a list of TrainerBattleModel objects which have not been completed """
        trainerModelList = []
        db = None
        try:
            db = dbconn()
            queryString = 'SELECT enemy_uuid FROM trainer_battles WHERE "locationId" = %(locationId)s AND discord_id = %(discordId)s'
            results = db.queryAll(queryString, { 'locationId': self.locationId, 'discordId': self.discordId })
            enemyUUIDs = []
            for row in results:
                enemyUUIDs.append(row[0])
            
            if self.enemyType == 'wild':
                configPath = '../configs/enemyTrainers.json'
            elif self.enemyType == 'gym':
                configPath = '../configs/gyms.json'
            else:
                self.statuscode = 96
                self.message = 'invalid enemyType. use "wild" or "gym"'
                return []

            # Use absolute path relative to this file's location
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), configPath)
            loadedConfig = json.load(open(p, 'r'))
            
            if self.enemyType == 'wild':
                trainerConfigList = loadedConfig.get(str(self.locationId), [])
            else:
                baseConfig = loadedConfig[str(self.locationId)]
                requirements = baseConfig['leader']['requirements']
                validRequirements = True
                if requirements != []:
                    questObj = qObj(self.discordId)
                    if not questObj.prerequsitesValid(requirements):
                        trainerConfigList = ['Missing Requirements']
                        validRequirements = False
                if validRequirements:
                    if gymLeader:
                        trainerConfigList = baseConfig['leader']
                    else:
                        trainerConfigList = baseConfig['trainers']
            
            if gymLeader:
                trainerModelList.append(GymLeaderModel(trainerConfigList))
            else:
                trainerModelList = self.__returnTrainerList(trainerConfigList)
                
                if trainerModelList is None:
                    return []
                
                # Filter out previously defeated trainers
                trainerModelList = [trainer for trainer in trainerModelList if trainer.enemy_uuid not in enemyUUIDs]

        except Exception as e:
            self.statuscode = 96
            self.message = f'Error loading trainer list: {str(e)}'
            logger.error(excInfo=sys.exc_info())
            return []
        finally:
            if db is not None:
                del db
            return trainerModelList
    


    def __insertEnemyCompleted(self, enemy_uuid):
        """ inserts and enemy_uuid into the database which indicates complete """
        try:
            db = dbconn()
            insertString = 'INSERT INTO trainer_battles (discord_id, "locationId", enemy_uuid) VALUES(%(discordId)s, %(locationId)s, %(enemy_uuid)s)'
            db.execute(insertString, { 'enemy_uuid': enemy_uuid, 'locationId': self.locationId, 'discordId': self.discordId })
        except Exception as e:
            self.statuscode = 96
            self.message = f'Error loading trainer list: {str(e)}'
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db

    def __checkEnemyCompleted(self, enemy_uuid):
        """ return True if the enemy_uuid is in database which indicates complete """
        enemyCompleted = False
        try:
            db = dbconn()
            queryString = 'SELECT 1 FROM trainer_battles WHERE enemy_uuid = %(enemy_uuid)s AND "locationId" = %(locationId)s AND discord_id = %(discordId)s'

            result = db.querySingle(queryString, { 'enemy_uuid': enemy_uuid, 'locationId': self.locationId, 'discordId': self.discordId })
            if result:
                enemyCompleted = True
        except Exception as e:
            self.statuscode = 96
            self.message = f'Error loading trainer list: {str(e)}'
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return enemyCompleted

    def __returnTrainerList(self, trainerList):
        """ returns a model list of trainers from config file """
        trainerModelList = []
        if trainerList == []:
            # list is empty return error
            self.statuscode = 96
            self.message = "empty trainer list"
            return []  # Return empty list instead of None
        elif trainerList == ['Missing Requirements']:
            self.statuscode = 420
            self.message = "You cannot do that yet!"
            return []  # Return empty list instead of None

        for trainer in trainerList:
            trainerModelList.append(TrainerBattleModel(trainer))

        return trainerModelList
    