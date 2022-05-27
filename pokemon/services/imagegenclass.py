# this class is used to generate images 

import os
import discord
import requests
from io import BytesIO
from pokeclass import Pokemon as PokemonClass
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from models.trainer_battle import TrainerBattleModel

baseBattlePath = "./sprites/battle/"

class imagegen:
    def __init__(self):
        self.statuscode = 69
        self.message = ""

        self.baseUrl = "https://pokesprites.joshkohut.com/sprites/"
        self.fontPath = "./fonts/pokemon_generation_1.ttf"
        self.battlePath = './sprites/battle/'
        self.trainersPath = './sprites/trainers/'

    def battle_trainer_victory(self, enemyTrainer: TrainerBattleModel):
        """ generate an image for the start of a wild pokemon battle  """
        battleBackground = self.battlePath + 'pokebattle_trainer_start.png'
        partypokeballFainted = self.battlePath + '/party_pokeball_fainted.png'
        trainerSprite = self.trainersPath + enemyTrainer.filename
        enemyTrainerParty = len(enemyTrainer.pokemon)
        
        backgroundImg = Image.open(battleBackground)
        partypokeballFaintedImg = Image.open(partypokeballFainted)
        trainerSpriteImg = Image.open(trainerSprite)

         # create font sizes
        font = ImageFont.truetype(self.fontPath, 35)

        draw = ImageDraw.Draw(backgroundImg)

        draw.text((40, 553), 'You defeated ' + enemyTrainer.name + '!', (29, 17, 17), font=font)
        draw.text((40, 635), 'You earned ' + str(enemyTrainer.money), (29, 17, 17), font=font)

        trainerSpriteImg = self.__removeBackground(trainerSpriteImg).resize((250,250))

        # add the sprites into the background image
        back_im = backgroundImg.copy()
        back_im.paste(trainerSpriteImg, (500, 30), trainerSpriteImg)

        if enemyTrainerParty > 1:
            for count in range(enemyTrainerParty):
                x = 137 + (34* count)
                back_im.paste(partypokeballFaintedImg, (x, 85), partypokeballFaintedImg)
        # back_im.save('C:/Users/legend/Downloads/sample2.png')
        return back_im
 
    def battle_trainer_start(self, enemyTrainer: TrainerBattleModel, playerPartySize=1, playerPartyFainted=0):
        """ generate an image for the start of a wild pokemon battle  """
        battleBackground = self.battlePath + 'pokebattle_trainer_start.png'
        partypokeball = self.battlePath + 'party_pokeball.png'
        partypokeballFainted = self.battlePath + 'party_pokeball_fainted.png'
        trainerSprite = self.trainersPath + enemyTrainer.filename
        enemyTrainerParty = len(enemyTrainer.pokemon)

        backgroundImg = Image.open(battleBackground)
        partypokeballImg = Image.open(partypokeball)
        partypokeballFaintedImg = Image.open(partypokeballFainted)
        trainerSpriteImg = Image.open(trainerSprite)

         # create font sizes
        font = ImageFont.truetype(self.fontPath, 35)

        draw = ImageDraw.Draw(backgroundImg)

        draw.text((40, 553), enemyTrainer.name + ' wants', (29, 17, 17), font=font)
        draw.text((40, 635), 'to battle!', (29, 17, 17), font=font)

        trainerSpriteImg = self.__removeBackground(trainerSpriteImg).resize((250,250))

        # add the sprites into the background image
        back_im = backgroundImg.copy()
        back_im.paste(trainerSpriteImg, (500, 30), trainerSpriteImg)

        if enemyTrainerParty > 1:
            for count in range(enemyTrainerParty):
                x = 138 + (34* count)
                back_im.paste(partypokeballImg, (x, 86), partypokeballImg)

        if playerPartySize > 1:
            for count in range(playerPartySize):
                x = 464 + (34* count)
                back_im.paste(partypokeballImg, (x, 396), partypokeballImg)
        
        if playerPartyFainted > 0:
            for count in range(playerPartyFainted):
                x = 463 + (34* count)
                back_im.paste(partypokeballFaintedImg, (x, 395), partypokeballFaintedImg)

        return back_im
        
 
    def battle_wild_start(self, pokemon: PokemonClass, playerPartySize=1, playerPartyFainted=0):
        """ generate an image for the start of a wild pokemon battle  """
        battleBackground = self.battlePath + 'pokebattle_wild_start.png'
        partypokeball = self.battlePath + 'party_pokeball.png'
        partypokeballFainted = self.battlePath + 'party_pokeball_fainted.png'

        backgroundImg = Image.open(battleBackground)
        partypokeballImg = Image.open(partypokeball)
        partypokeballFaintedImg = Image.open(partypokeballFainted)
        textLine1 = "Wild %s" %(pokemon.pokemonName.upper())
        textLine2 = 'appeared!'

        pokemonSprite = self.__getImageFromURL(pokemon.frontSpriteURL)

         # create font sizes
        font = ImageFont.truetype(self.fontPath, 35)

        draw = ImageDraw.Draw(backgroundImg)

        draw.text((40, 553), textLine1, (29, 17, 17), font=font)
        draw.text((40, 635), textLine2, (29, 17, 17), font=font)

        pokemonSprite = self.__removeBackground(pokemonSprite).resize((250,250))

        # add the sprites into the background image
        back_im = backgroundImg.copy()
        back_im.paste(pokemonSprite, (500, 0), pokemonSprite)

        if playerPartySize > 1:
            for count in range(playerPartySize):
                x = 464 + (34* count)
                back_im.paste(partypokeballImg, (x, 396), partypokeballImg)

        if playerPartyFainted > 0:
            for count in range(playerPartyFainted):
                x = 463 + (34* count)
                back_im.paste(partypokeballFaintedImg, (x, 395), partypokeballFaintedImg)

        return back_im

    def battle_fight(self, active: PokemonClass, pokemon: PokemonClass):
        """ generates an image for a pokemon battle """
        self.active = active
        self.pokemon = pokemon

        # create font sizes
        font = ImageFont.truetype(self.fontPath, 35)
        smallfont = ImageFont.truetype(self.fontPath, 20)

        imgActiveHealth, imgPokemonHealth = self.__getHealthSprite(active, pokemon)
        battleBackground = self.battlePath + 'pokebattle.png'
        activeSprite = self.__getImageFromURL(self.active.backSpriteURL)
        pokemonSprite = self.__getImageFromURL(self.pokemon.frontSpriteURL)
        
        img = Image.open(battleBackground)
        draw = ImageDraw.Draw(img)

        activeMaxHP = active.getPokeStats()['hp']
        activeHP = active.currentHP
        

        # specifying coordinates and colour of text
        draw.text((43, 1), pokemon.pokemonName.upper(), (29, 17, 17), font=font)
        draw.text((168, 47), ":L" + str(pokemon.currentLevel), (29, 17, 17), font=font)
        draw.text((440, 280), active.pokemonName.upper(), (29, 17, 17), font=font)
        draw.text((570, 325), str(active.currentLevel), (29, 17, 17), font=font)
        draw.text((440, 403), str(activeHP)+ '/' + str(activeMaxHP), (29, 17, 17), font=font)

        # static draw textures
        draw.text((90, 93), "HP:", (29, 17, 17), font=smallfont)
        draw.text((410, 373), "HP:", (29, 17, 17), font=smallfont)
        draw.text((400, 560), "FIGHT", (29, 17, 17), font=font)
        draw.text((615, 560), "PKMN", (29, 17, 17), font=font)
        draw.text((400, 640), "ITEM", (29, 17, 17), font=font)
        draw.text((615, 640), "RUN", (29, 17, 17), font=font)


        # remove sprite backgrounds
        activeSprite = self.__removeBackground(activeSprite).resize((250,250))
        pokemonSprite = self.__removeBackground(pokemonSprite).resize((250,250))

        # add the sprites into the background image
        back_im = img.copy()
        back_im.paste(activeSprite, (40, 200), activeSprite)
        back_im.paste(pokemonSprite, (500, 0), pokemonSprite)

        back_im.paste(imgActiveHealth, (470, 373), imgActiveHealth)
        back_im.paste(imgPokemonHealth, (145, 93), imgPokemonHealth)

        return back_im

    
    def __removeBackground(self, img):
        """ removes background of pokemon sprite """
        rgba = img.convert("RGBA")
        datas = rgba.getdata()
        
        newData = []
        for item in datas:
            if item[0] == 0 and item[1] == 0 and item[2] == 0 and item[3] == 0:  # finding black colour by its RGB value
                # storing a transparent value when we find a black colour
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)  # other colours remain unchanged
        
        rgba.putdata(newData)
        return rgba


    def __getHealthSprite(self, active: PokemonClass, pokemon: PokemonClass):
        """ returns correct health sprite for both pokemon """
        activeMaxHP = active.getPokeStats()['hp']
        activeHP = active.currentHP
        pokemonMaxHP = pokemon.getPokeStats()['hp']
        pokemonHP = pokemon.currentHP
        
        # determine which health threshold is needed
        activePercentHP = round(activeHP/activeMaxHP * 100)
        pokemonPercentHP = round(pokemonHP/pokemonMaxHP * 100)
        
        healthFileList = []
        for hpPercent in [activePercentHP, pokemonPercentHP]:
            if hpPercent == 100:
                healthFileList.append('Health_100')
            elif hpPercent >= 75 and hpPercent < 100:
                healthFileList.append('Health_75')
            elif hpPercent >= 50 and hpPercent < 75:
                healthFileList.append('Health_50')
            elif hpPercent < 50:
                healthFileList.append('Health_25')
            elif hpPercent == 0:
                healthFileList.append('Health_0')
        
        sameFile = False
        if healthFileList[0] == healthFileList[1]:
            sameFile = True
        
        imgActiveHealth = self.__getImageFromDisk(healthFileList[0])
        if sameFile:
            imgPokemonHealth = imgActiveHealth
        else:
            imgPokemonHealth = self.__getImageFromDisk(healthFileList[1])
        
        return imgActiveHealth, imgPokemonHealth

    def __getImageFromURL(self, url):
        """ returns data of image from url """
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img

    def __getImageFromDisk(self, filename):
        """ returns data of image from url """
        # TODO update to use discord.File()
        
        file = baseBattlePath + filename + '.png'
        img = Image.open(file)
        return img