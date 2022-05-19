
import json



class QuestModel:
    
    def __init__(self, quest: json):
        self.locationId = quest['locationId']
        self.prerequsites = quest['pre-requsites']
        self.questName = quest['quest']
        self.blockers = quest['blockers']
