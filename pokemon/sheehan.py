# from models.trainerclass import trainer as TrainerClass
from services.locationclass import location as LocationClass

# trainer = TrainerClass('509767223938777108')
# areaId = trainer.getAreaId()

# Location: 88 - Kanto Route 1
# Location Area: 295 - Kanto Route 1 Area
loc = LocationClass()
encounters = loc.getAreaEncounterDetails(295)
methods = loc.getMethods(encounters)
