import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'models'))
sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'services'))

from services.trainerclass import trainer as TrainerClass
from services.locationclass2 import location as LocationClass
from services.storeclass import store as StoreClass
from services.inventoryclass import inventory as InventoryClass


trainer = TrainerClass('509767223938777108')
loc = trainer.getLocation()
# active = trainer.getPokemonById(9)


# wild = trainer.encounter('walk')
# msg = trainer.fight(wild)

# inv = InventoryClass(trainer.discordId)

store = StoreClass(trainer.discordId, 154)
store.sellItem('ligma', 1)
# store.buyItem('super-potion', 1)
# pokemon = trainer.encounter('walk')
# areaId = trainer.getAreaId()

# # Location: 88 - Kanto Route 1
# # Location Area: 295 - Kanto Route 1 Area
# loc = LocationClass(trainer.discordId)
# methods = loc.getMethods()
# direction = loc.getLocationByName('kanto-route-3')


# encounters = loc.getAreaEncounterDetails(295)
# methods = loc.getMethods(encounters)
