# battle class - this class handles battles from both wild enemy trainers and gym trainers and leaders
import os
import sys
import json
import random
from dbclass import db as dbconn
from inventoryclass import inventory as inv
from .keyitemsclass import keyitems as kitems
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
        try:
            logger.info(f"[BATTLE] getTrainerList called: locationId={self.locationId}, enemyType={self.enemyType}, gymLeader={gymLeader}")
            
            db = dbconn()
            queryString = 'SELECT enemy_uuid FROM trainer_battles WHERE "locationId" = %(locationId)s AND discord_id = %(discordId)s'
            results = db.queryAll(queryString, { 'locationId': self.locationId, 'discordId': self.discordId })
            enemyUUIDs = []
            for row in results:
                enemyUUIDs.append(row[0])
            
            logger.info(f"[BATTLE] Defeated enemy UUIDs from DB: {enemyUUIDs}")
            
            if self.enemyType == 'wild':
                configPath = '../configs/enemyTrainers.json'
            elif self.enemyType == 'gym':
                configPath = '../configs/gyms.json'
            else:
                self.statuscode = 96
                self.message = 'invalid enemyType. use "wild" or "gym"'
                logger.error(f"[BATTLE] Invalid enemyType: {self.enemyType}")
                return []  # Return empty list instead of None

            # Use absolute path relative to this file's location
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), configPath)
            logger.info(f"[BATTLE] Loading config from: {p}")
            loadedConfig = json.load(open(p, 'r'))
            
            if self.enemyType == 'wild':
                trainerConfigList = loadedConfig.get(str(self.locationId), [])
                logger.info(f"[BATTLE] Loaded {len(trainerConfigList)} trainers from enemyTrainers.json for location {self.locationId}")
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
                logger.info(f"[BATTLE] Creating gym leader model")
                trainerModelList.append(GymLeaderModel(trainerConfigList))
            else:
                logger.info(f"[BATTLE] Calling __returnTrainerList with {len(trainerConfigList) if isinstance(trainerConfigList, list) else 'non-list'} trainers")
                trainerModelList = self.__returnTrainerList(trainerConfigList)
                
                logger.info(f"[BATTLE] __returnTrainerList returned: {trainerModelList}")
                logger.info(f"[BATTLE] Type: {type(trainerModelList)}, Length: {len(trainerModelList) if trainerModelList else 'None/0'}")
                
                # FIX: Check if __returnTrainerList returned None or a valid list
                if trainerModelList is None:
                    logger.error(f"[BATTLE] __returnTrainerList returned None!")
                    return []  # Return empty list if there was an error
                
                # Log each trainer before filtering
                for i, trainer in enumerate(trainerModelList):
                    logger.info(f"[BATTLE]   Trainer {i} BEFORE filter: {trainer.name} (UUID: {trainer.enemy_uuid})")
                
                # Filter out previously defeated trainers
                # Using list comprehension to avoid modifying list during iteration
                trainerModelList = [trainer for trainer in trainerModelList if trainer.enemy_uuid not in enemyUUIDs]
                
                logger.info(f"[BATTLE] AFTER filtering: {len(trainerModelList)} trainers remain")
                for i, trainer in enumerate(trainerModelList):
                    logger.info(f"[BATTLE]   Trainer {i} AFTER filter: {trainer.name} (UUID: {trainer.enemy_uuid})")

        except Exception as e:
            self.statuscode = 96
            self.message = f'Error loading trainer list: {str(e)}'
            logger.error(f"[BATTLE] Exception in getTrainerList: {e}", exc_info=True)
            return []  # Return empty list on error
        finally:
            # delete and close connection
            del db
            logger.info(f"[BATTLE] getTrainerList returning {len(trainerModelList)} trainers")
            return trainerModelList
    


    def __insertEnemyCompleted(self, enemy_uuid):
        """ inserts and enemy_uuid into the database which indicase complete """
        # do not lock out if trainer is elite-4 to allow multiple battles
        if enemy_uuid == "elite-4":
            return
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
    