import pokebase as pb
# from .trainerclass import trainer
from trainerclass import trainer
from pokeclass import Pokemon as pokeClass
from encounterclass import encounter
# from .config import *
import random
import math
import psycopg as pg


pg.connect(
    host=(
        params and params.host) or "192.168.5.10",
    dbname=(params and params.dbname) or "pokemon_db",
    user=(params and params.user) or "redbot",
    # todo remove password from source control
    password=(params and params.password) or "bfFLG9tUYPpW7272vzhX52",
    port=(params and params.port) or 5432)



# moveDict = {'scratch': 1, 'leer': 15, 'growl': 1, 'ember': 9, 'flamethrower': 46, 'fire-spin': 55, 'rage': 24, 'slash': 36}

# print(moveDict)
# level = 45
# moveList = []

# # markdict = {"Tom":67, "Tina": 54, "Akbar": 87, "Kane": 43, "Divya":73}
# defaultList = sorted(moveDict.items(), key=lambda x:x[1], reverse=True)
# for move in defaultList:
#     moveLevel = move[1]
#     moveName = move[0]
#     if int(moveLevel) <= level:
#         moveList.append(moveName)

# moveList = ['1','2']
# if len(moveList) < 4:
#     diff = 4-len(moveList)
#     for x in range(diff):
#         x=None
#         moveList.append(x)

# print(moveList)
# print(moveList[0:4])

# trainer = trainer('456')
# print(trainer.getAreaId())

# activePokemonId = trainer.getActivePokemon().trainerId

# pokemon1 = pokeClass()
# pokemon1.attack.base
# pokemon1.load(activePokemonId)

# pokemon2 = pokeClass('pikachu')
# pokemon2.create(6)

# # trainer.healAll()


# encounter = encounter(pokemon1, pokemon2)

# print(encounter.fight())
