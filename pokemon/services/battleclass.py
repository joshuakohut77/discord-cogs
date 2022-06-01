# battle class - this class handles battles from both wild enemy trainers and gym trainers and leaders
import os
import sys
import json
import random
from dbclass import db as dbconn
from inventoryclass import inventory as inv
from questclass import quests as qObj
from loggerclass import logger as log
from models.trainer_battle import TrainerBattleModel

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

    def getNextBattle(self):
        """ returns a TrainerBattleModel object to battle against """
        trainerModelList = self.getTrainerList()
        if len(trainerModelList) > 0:
            return trainerModelList[0]
        else:
            return None

    def getTrainerList(self):
        """ returns a list of TrainerBattleModel objects which have not been completed """
        trainerModelList = []
        try:
            db = dbconn()
            queryString = 'SELECT enemy_uuid FROM trainer_battles WHERE "locationId" = %(locationId)s AND discord_id = %(discordId)s'
            results = db.queryAll(queryString, { 'locationId': self.locationId, 'discordId': self.discordId })
            enemyUUIDs = []
            for row in results:
                enemyUUIDs.append(row[0])
            
            if self.enemyType == 'wild':
                configPath = './configs/enemyTrainers.json'
            elif self.enemyType == 'gym':
                configPath = './configs/gyms.json'
            else:
                self.statuscode = 96
                self.message = 'invalid enemyType. use "wild" or "gym"'
                return 
            
            loadedConfig = json.load(open(configPath, 'r'))
            # TODO uncomment 
            # p = os.path.join(os.path.dirname(os.path.realpath(__file__)), configPath)
            # loadedConfig = json.load(open(p, 'r'))
            
            if self.enemyType == 'wild':
                trainerConfigList = loadedConfig[str(self.locationId)]
            else:
                baseConfig = loadedConfig[str(self.locationId)]
                requirements = baseConfig['requirements']
                validRequirements = True
                if requirements != []:
                    questObj = qObj(self.discordId)
                    if not questObj.prerequsitesValid(requirements):
                        trainerConfigList = ['Missing Requirements']
                        validRequirements = False
                if validRequirements:
                    trainerConfigList = baseConfig['trainers']
            
            trainerModelList = self.__returnTrainerList(trainerConfigList)

            # check if trainer has previously beaten trainer and remove trainer from list. 
            for trainer in trainerModelList:

                if trainer.enemy_uuid in enemyUUIDs:
                    trainerModelList.remove(trainer)
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db
            return trainerModelList
    


    def __insertEnemyCompleted(self, enemy_uuid):
        """ inserts and enemy_uuid into the database which indicase complete """
        try:
            db = dbconn()
            insertString = 'INSERT INTO trainer_battles (discord_id, "locationId", enemy_uuid) VALUES(%(discordId)s, %(locationId)s, %(enemy_uuid)s)'
            db.execute(insertString, { 'enemy_uuid': enemy_uuid, 'locationId': self.locationId, 'discordId': self.discordId })
        except:
            self.statuscode = 96
            logger.error(excInfo=sys.exc_info())
        finally:
            # delete and close connection
            del db

    def __checkEnemyCompleted(self, enemy_uuid):
        """ return True if the enemy_uuid is in database which indicates complete """
        enemyCompleted = False
        try:
            db = dbconn()
            queryString = 'SELECT 1 FROM trainer_battles WHERE enemy_uuid = %(enemy_uuid)s AND locationId = %(locationId)s AND discord_id = %(discordId)s'

            result = db.querySingle(queryString, { 'enemy_uuid': enemy_uuid, 'locationId': self.locationId, 'discordId': self.discordId })
            if result:
                enemyCompleted = True
        except:
            self.statuscode = 96
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
            return
        elif trainerList == ['Missing Requirements']:
            self.statuscode = 420
            self.message = "You cannot do that yet!"
            return

        for trainer in trainerList:
            trainerModelList.append(TrainerBattleModel(trainer))

        return trainerModelList
    