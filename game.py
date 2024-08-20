import pygame
import pygame.freetype
import sys
import random
import math
import os
from scripts.entities import *
from scripts.characters import *
from scripts.utilities import *
from scripts.tilemap import *
from scripts.clouds import *
from scripts.particle import *
from scripts.spark import *
import cProfile

class Game:
    def __init__(self):

        #Pygame specific parameters and initialisation
        pygame.init()
        gameVersion = '0.3.0'
        pygame.display.set_caption(f'Hilbert\'s Hotel v{gameVersion}')
        self.text_font = pygame.font.SysFont('Comic Sans MS', 30, bold = True)
        self.clock = pygame.time.Clock()       

        #Define all general game parameters and load in assets
        initialiseMainScreen(self)
        initialiseGameParams(self)
        self.loadGameAssets()
      
        #Initialise player and map 
        self.player = Player(self, (0, 0), (8, 12))
        self.tilemap = tileMap(self, tile_size = 16)
        
    def loadMenu(self):
        self.sfx['ambience'].play(-1)

        inMenu = True
        saveSlots = [0, 1, 2]
        savedDeaths = self.getSavedDeaths()
        hoverSlot = 0
        deleting = 0
        
        selected = (86, 31, 126)
        notSelected = (1, 1, 1)
        
        self.clouds = Clouds(self.assets['clouds'], count = 20)

        background = pygame.transform.scale(self.assets['menuBackgroundHH'], (self.screen_width / 2, self.screen_height / 2))
        foreground = pygame.transform.scale(self.assets['menuBackgroundHHForeground'], (self.screen_width / 2, self.screen_height / 2))
        
        while inMenu:
            
            self.display_outline.blit(background, (0, 0))
            self.HUDdisplay.fill((0, 0, 0, 0))

            self.clouds.update()
            self.clouds.render(self.display_outline, offset = self.render_scroll)

            self.display_outline.blit(foreground, (0, 0))

            #Delete save if held for 5 secs
            if deleting:
                deleting = max(deleting - 1, 0)
                if deleting == 0:
                    self.delete_save(hoverSlot % len(saveSlots))
                    savedDeaths = self.getSavedDeaths()
            
            #Displaying menu HUD:
            displaySlot = (hoverSlot % len(saveSlots))
            self.draw_text('Hilbert\'s Hotel', (self.screen_width * (3/4), 60), self.text_font, selected, (0, 0), scale = 1.5, mode = 'center') 
            self.draw_text('Select: x', (self.screen_width * (3/4), 100), self.text_font, notSelected, (0, 0), scale = 0.5, mode = 'center')  
            self.draw_text('Delete: z (hold)', (self.screen_width * (3/4), 120), self.text_font,notSelected, (0, 0), scale = 0.5, mode = 'center')  
            if deleting:
                self.draw_text('Deleting save ' + str(hoverSlot % len(saveSlots)) + ': ' + str(math.floor(deleting / (self.fps/10)) / 10) + 's', (self.screen_width * (3/4), 140), self.text_font, (200, 0, 0), (0, 0), scale = 0.5, mode = 'center')
            
            self.draw_text('Save 0', (self.screen_width * (3/4) - 160, 170), self.text_font, selected if displaySlot == 0 else notSelected, (0, 0), mode = 'center')
            self.draw_text(str(savedDeaths[0]), (self.screen_width * (3/4) - 160, 200), self.text_font, selected if displaySlot == 0 else notSelected, (0, 0), mode = 'center', scale = 0.75)
            
            self.draw_text('Save 1', (self.screen_width * (3/4), 170), self.text_font, selected if displaySlot == 1 else notSelected, (0, 0), mode = 'center')
            self.draw_text(str(savedDeaths[1]), (self.screen_width * (3/4), 200), self.text_font, selected if displaySlot == 1 else notSelected, (0, 0), mode = 'center', scale = 0.75)
            
            self.draw_text('Save 2', (self.screen_width * (3/4) + 160, 170), self.text_font, selected if displaySlot == 2 else notSelected, (0, 0), mode = 'center') 
            self.draw_text(str(savedDeaths[2]), (self.screen_width * (3/4) + 160, 200), self.text_font, selected if displaySlot == 2 else notSelected, (0, 0), mode = 'center', scale = 0.75) 

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        hoverSlot -= 1
                        if deleting:
                            deleting = 0
                    if event.key == pygame.K_RIGHT:
                        hoverSlot += 1
                        if deleting:
                            deleting = 0
                    if event.key == pygame.K_x:
                        saveSlot = hoverSlot % len(saveSlots)
                        self.run(saveSlot)
                    if event.key == pygame.K_z:
                        deleting = 300
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_z:
                        deleting = 0

            self.display.blit(self.display_outline, (0, 0))
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            self.screen.blit(self.HUDdisplay, (0, 0))
            pygame.display.update()
            self.clock.tick(self.fps)
            self.interractionFrameZ = False
            
            
    def run(self, saveSlot):
        
        self.sfx['music'].play(-1)

        self.saveSlot = saveSlot
        self.load_game(self.saveSlot)

        self.tilemap.load_tilemap('lobby')
        self.load_level()

        #####################################################
        ######################GAME LOOP######################
        #####################################################

        while self.game_running:
            #Camera movement
            self.scroll[0] += (self.player.rect().centerx - self.screen_width / 4 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.screen_height / 4 - self.scroll[1]) / 30
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            #Background
            self.display.blit(self.background, (0, 0))
            self.display_outline.fill((0, 0, 0, 0))
            self.HUDdisplay.fill((0, 0, 0, 0))
            self.darkness_surface.fill((0, 0, 0, self.caveDarkness))
            self.minimapdisplay.fill((0, 0, 0, 0))
            self.screenshake = max(0, self.screenshake - 1)

            #Minimap:
            if self.minimapActive:
                pygame.draw.rect(self.minimapdisplay, (255,100,100, 255), ((self.player.pos[0] - self.render_scroll[0] + self.player.anim_offset[0]) / 16 * 8, (self.player.pos[1] - self.render_scroll[1] + self.player.anim_offset[1]) / 16 * 8, 8, 8))
                for loc in self.minimapList:
                    tile = self.minimapList[loc]
                    pygame.draw.rect(self.minimapdisplay, (255,255,255, 200), (tile[0] * 8, tile[1] * 8, 8, 8))
                self.minimapList = {}
  
            #RENDER AND UPDATE ALL THE THINGS
            for portal in self.portals:
                if not self.paused:
                    portal.update(self.tilemap)
                portal.render(self.display_outline, offset = self.render_scroll)
            
            for enemy in self.enemies.copy():
                enemy.render(self.display_outline, offset = self.render_scroll)
                if not self.paused:
                    if enemy.update(self.tilemap, (0, 0)):
                        self.enemies.remove(enemy)
                        self.player.updateNearestEnemy()

            for spawnPoint in self.spawnPoints:
                spawnPoint.render(self.display_outline, offset = self.render_scroll)
                spawnPoint.update(self.tilemap)
            
            for character in self.characters.copy():
                if not self.paused:
                    character.update(self.tilemap)
                character.render(self.display_outline, offset = self.render_scroll)

            if not self.dead:
                if not self.paused:
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display_outline, offset = self.render_scroll)
            
            for projectile in self.projectiles.copy():
                if projectile.update(self):
                    self.projectiles.remove(projectile)
                
            for rect in self.potplants:
                  if random.random() < 0.01 and not self.paused:
                      pos = (rect.x + rect.width * random.random(), rect.y + rect.height * random.random())
                      self.particles.append(Particle(self, 'leaf', pos, vel = [0, random.uniform(0.2, 0.4)], frame = random.randint(0, 10)))

            for currencyItem in self.currencyEntities.copy():
                if not self.paused:
                    if currencyItem.update(self.tilemap, (0, 0)):
                        self.currencyEntities.remove(currencyItem)
                currencyItem.render(self.display_outline, offset = self.render_scroll)
          
            self.tilemap.render(self.display_outline, offset = self.render_scroll)
  
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display_outline, offset = self.render_scroll)
                if kill:
                    self.sparks.remove(spark)
           
            for extraEntity in self.extraEntities.copy():
                extraEntity.render(self.display_outline, offset = self.render_scroll)
                if not self.paused:
                    if extraEntity.update(self.tilemap):
                        self.extraEntities.remove(extraEntity)
            
            display_outline_mask = pygame.mask.from_surface(self.display_outline)
            display_outline_sillhouette = display_outline_mask.to_surface(setcolor = (0, 0, 0, 180), unsetcolor = (0, 0, 0, 0))

            for offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                self.display.blit(display_outline_sillhouette, offset)

            for particle in self.particles.copy():
                particle.render(self.display_outline, offset = self.render_scroll)
                if not self.paused:
                    kill = particle.update()
                    if particle.type == 'leaf':
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035 + particle.randomness) * 0.2
                    if kill:
                        self.particles.remove(particle)  
           
            #Displaying HUD and text:
            self.displayHUDandText()
                    
            #Level transition
            if self.transition > 30:
                self.tilemap.load_tilemap(self.nextLevel, self.currentLevelSize, self.enemyCountMax)
                self.previousLevel = self.currentLevel
                self.currentLevel = self.nextLevel
                self.load_level()
                self.dead = False

            elif self.transition < 31 and self.transition != 0:
                self.transition += 1
            
            #Remove interaction frame
            self.interractionFrameZ = False
            self.interractionFrameS = False
            self.interractionFrameV = False
                    
            #Event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.floors['infinite'] = 1
                    
                    #Add important items left on ground:
                    for currency in self.currencyEntities:
                        type = str(currency.currencyType) + 's'
                        if type in self.notLostOnDeath:
                            self.wallet[type] += currency.value
                    self.save_game(self.saveSlot)
                    
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        if not self.paused and self.player.jump() and abs(self.player.dashing) < 50:
                            self.sfx['jump'].play()
                        self.movement[2] = True
                    if event.key == pygame.K_DOWN:
                        self.movement[3] = True
                        self.player.gravity = 0.2
                    if event.key == pygame.K_x:
                        if not self.paused:
                            self.player.dash()
                    if event.key == pygame.K_z:
                        self.interractionFrameZ = True
                    if event.key == pygame.K_s:
                        self.interractionFrameS = True
                    if event.key == pygame.K_v:
                        self.interractionFrameV = True
                    if event.key == pygame.K_ESCAPE:
                        if not self.talking and not self.dead:
                            self.paused = not self.paused

                    #DEBUGGING
                    if event.key == pygame.K_r:
                        self.transitionToLevel(self.currentLevel)
                    if event.key == pygame.K_t:
                        for currency in self.wallet:
                            self.wallet[currency] += 20
                    if event.key == pygame.K_d:
                        self.difficulty += 1
                        print('difficulty now at ',self.difficulty)
                    if event.key == pygame.K_f:
                        self.powerLevel += 1
                        print('powerlevel now at ', self.powerLevel)
                    if event.key == pygame.K_k:
                        for e in self.enemies.copy():
                            e.kill()
                            self.enemies.remove(e)
                    if event.key == pygame.K_p:
                        for e in self.enemies.copy():
                            if (e.pos[0] < 0 or e.pos[0] > self.tilemap.mapSize*16) or (e.pos[1] < 0 or e.pos[1] > self.tilemap.mapSize*16):
                                print(e.type, e.pos)
                                print('OUT OF BOUNDS^')
                        print('player: ', self.player.pos)
                        print('bounds: ', 0,0, ",",self.tilemap.mapSize*16, self.tilemap.mapSize*16)
                    if event.key == pygame.K_l:
                        print('player pos: ', self.player.pos[0] // 16, self.player.pos[1] // 16)

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False
                    if event.key == pygame.K_UP:
                        self.movement[2] = False
                    if event.key == pygame.K_DOWN:
                        self.movement[3] = False
                        self.player.gravity = 0.12

            if self.dead:
                self.darkness_surface.fill((0, 0, 0, max(self.minPauseDarkness, self.caveDarkness)))
                self.draw_text('YOU DIED', (self.screen_width / 2, self.screen_height / 2 - 60), self.text_font, (200, 0, 0), self.render_scroll, mode = 'center')

                self.draw_text(self.deathMessage, (self.screen_width / 2, self.screen_height / 2 - 30), self.text_font, (200, 0, 0), self.render_scroll, mode = 'center', scale = 0.5)
                self.draw_text('Deaths: ' + str(self.deathCount), (self.screen_width / 2, self.screen_height / 2 + 30), self.text_font, (200, 0, 0), self.render_scroll, mode = 'center', scale = 0.5)
                self.draw_text('Press z to Alive Yourself', (self.screen_width / 2, self.screen_height / 2 + 50), self.text_font, (200, 0, 0), self.render_scroll, mode = 'center', scale = 0.5)
                
                if self.interractionFrameZ:
                    self.transitionToLevel('lobby')

            #Darkness effect blit:
            if self.caveDarkness or self.paused or self.dead:
                self.display_outline.blit(self.darkness_surface, (0, 0))         
            
            self.display.blit(self.display_outline, (0, 0))
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2) if self.screenshakeOn else (0, 0)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)
            self.screen.blit(self.HUDdisplay, (0, 0))
            self.screen.blit(self.minimapdisplay, (3 * self.screen_width / 4, 3 * self.screen_height / 4))

            #Level transition circle
            if self.transition:
                transition_surface = pygame.Surface(self.screen.get_size())
                pygame.draw.circle(transition_surface, (255, 255, 255), (self.screen.get_width() // 2, self.screen.get_height() // 2), (30 - abs(self.transition)) * (self.screen.get_width() / 30))
                transition_surface.set_colorkey((255, 255, 255))
                self.screen.blit(transition_surface, (0, 0))

            pygame.display.update()
            self.clock.tick(self.fps)

        #####################################################
        ####################GAME LOOP END####################
        #####################################################


    def update_dialogues(self):
        for character in self.characters:
            #Update which dialogue the character is up to.
            dialogue = self.dialogueHistory[str(character.name)]
            character.newDialogue = False

            for index in range(int(len(dialogue) / 2)):
                if dialogue[str(index) + 'said']:
                    character.currentDialogueIndex = index

            #Checks to see if the player has the required currency to unlock new dialogues.
            for index in character.currencyRequirements:
                if index > character.currentDialogueIndex + 1:
                    break
                individualSuccess = True
                success = True

                for i, trade in enumerate(character.currencyRequirements[index]):
                    #To unlock dialogue you need to fulfill requirement/s:
                    individualSuccess = self.checkCurrencyRequirement(trade, self.wallet, index, character.currentDialogueIndex, character)
                    
                    if individualSuccess:
                        character.currentTradeAbility[i] = True
                    else:
                        character.currentTradeAbility[i] = False
                        success = False

                #SPECIAL CASES:
                #e.g. dont unlock dialogue if in wrong floor etc.
                characterMoveToLobby = ['Noether', 'Curie', 'Planck', 'Lorenz', 'Franklin', 'Rubik', 'Cantor', 'Melatos']
                if (character.name in characterMoveToLobby) & (index >= 1) & (self.currentLevel != 'lobby'):
                    success = False         

                if success:
                    self.dialogueHistory[character.name][str(index) + 'available'] = True
                elif index > character.currentDialogueIndex + 1 or not self.dialogueHistory[character.name][str(index) + 'said']:
                    self.dialogueHistory[character.name][str(index) + 'available'] = False

            #Check to see if new dialogue is available:
            for index in range(int(len(dialogue) / 2)):
                if dialogue[str(index) + 'available'] and not dialogue[str(index) + 'said']:
                    character.newDialogue = True


    def checkCurrencyRequirement(self, trade, wallet, index, characterIndex, character):
        #If you havent reached the dialogue, it is not available
        if index > characterIndex + 1:
            return False
            
        #Purchasing things
        if trade[0] == 'purchase':
            if wallet[trade[1]] < trade[2]:
                return False
                
        #Specifically prime num
        elif trade[0] == 'prime':
            if not isPrime(wallet[trade[1]]):
                return False
        
        #Specifically prime num over a value
        elif trade[0] == 'primePurchase':
            if not isPrime(wallet[trade[1]]) or wallet[trade[1]] < trade[3]:
                return False
            
        #Reach a specific floor of a level:
        elif trade[0] == 'floor':
            #Check for maximum infinite floor
            if trade[1] == 'infinite':
                if self.infiniteFloorMax < trade[2]:
                    return False
            #Else check against current floor levels
            elif self.floors[trade[1]] < trade[2]:
                return False
            
        #Specifically prime num floor
        elif trade[0] == 'primeFloor':
            if not isPrime(self.floors[trade[1]]):
                print('returning false for ', self.floors[trade[1]])
                return False
            
        #Also the previous dialogue needs to have been said:
        if index != 0:
            if not self.dialogueHistory[character.name][str(index - 1) + 'said']:
                return False
            
        #You can probably access the dialogue.
        return True


    def display_text(self):
        #Each frame an extra character is added to the displayed text.
        #If the length of a line is larger than self.maxCharactersLine, it creates a new line IF there is a space to not chop words.
        if self.textLength < self.textLengthEnd:
            if self.currentTextList[self.currentTextIndex][self.textLength] == ' ' and len(self.displayTextList[-1]) > self.maxCharactersLine:
                self.displayTextList.append('')
            else:
                self.displayTextList[-1] = self.displayTextList[-1] + self.currentTextList[self.currentTextIndex][self.textLength]
            self.textLength += 1
        if self.textLength == self.textLengthEnd - 1:
            self.sfx['textBlip'].fadeout(50)
        
        #If all text in current chunk is displayed, move to next chunk.
        if self.interractionFrameZ and self.textLength > 1:
            if self.textLength == self.textLengthEnd:
                self.sfx['textBlip'].play(fade_ms = 50)
                self.currentTextIndex += 1
                self.textLength = 0
                #Only shallow copy needed
                self.displayTextList = self.talkingObject[:]
                try:
                    self.textLengthEnd = len(self.currentTextList[self.currentTextIndex])
                except IndexError:
                    pass

            #Fills in current text if the player is impatient
            else:
                #Im sure this while loop will always end, right?
                self.sfx['textBlip'].fadeout(50)
                while self.textLength < self.textLengthEnd:

                    if self.currentTextList[self.currentTextIndex][self.textLength] == ' ' and len(self.displayTextList[-1]) > self.maxCharactersLine:
                        self.displayTextList.append('')
                    else:
                        self.displayTextList[-1] = self.displayTextList[-1] + self.currentTextList[self.currentTextIndex][self.textLength]
                    self.textLength += 1
                    
        #When to end the dialogue:
        if self.currentTextIndex >= self.endTextIndex:
            self.sfx['textBlip'].fadeout(50)
            self.talking = False
            self.paused = False
            self.update_dialogues()
            
        #Actually display the text (and icon):
        for n in range(len(self.displayTextList)):
            self.draw_text(str(self.displayTextList[n]), (2*(self.player.pos[0]-self.render_scroll[0]), 2*(self.player.pos[1]-self.render_scroll[1])-30 + 30*n), self.text_font, (255,255,255), (0, 0), mode = 'center')
        if self.displayIcon:
            icon = self.displayIcons[self.displayIcon]
            icon = pygame.transform.scale(icon, (icon.get_width() * 2, icon.get_height() * 2))
            self.HUDdisplay.blit(icon, (2*(self.player.pos[0]-self.render_scroll[0]) - icon.get_width() / 2, 2*(self.player.pos[1]-self.render_scroll[1]) - 90 - icon.get_height() / 2))


    def check_encounter(self, entity):
        if not self.encountersCheck[entity]:
            self.run_text('New!', entity)
            self.encountersCheck[entity] = True
    

    def load_level(self):
        #Save game:
        self.save_game(self.saveSlot)

        #Add important items left on ground:
        for currency in self.currencyEntities:
            type = str(currency.currencyType) + 's'
            if type in self.notLostOnDeath:
                self.wallet[type] += currency.value

        self.particles = []
        self.projectiles = []
        self.currencyEntities = []
        self.sparks = []
        self.player.dashing = 0
        self.minimapList = {}

        if self.nextLevel != 'infinite':
            self.infiniteFloorMax = max(self.floors['infinite'], self.infiniteFloorMax)
            self.floors['infinite'] = 1
        
        if self.dead:
            self.health = self.maxHealth
            self.infiniteModeActive = False
            for currency in self.wallet:
                self.walletTemp[currency] = 0 if not self.infiniteModeActive else int(self.walletTemp[currency] / 2)
                self.wallet[currency] += self.walletTemp[currency]
                self.walletTemp[currency] = 0

        elif not self.dead and not self.infiniteModeActive:
            for currency in self.wallet:
                self.wallet[currency] += self.walletTemp[currency]
                self.walletTemp[currency] = 0

            if not self.initialisingGame and (self.currentLevel == 'lobby') and self.previousLevel not in ['lobby', 'infinite']:
                self.floors[self.previousLevel] += 1
        
        elif not self.dead and self.infiniteModeActive and self.previousLevel == 'infinite':
            self.floors[self.previousLevel] += 1

        #Spawn in entities
        self.enemies = []
        self.portals = []
        self.characters = []
        self.extraEntities = []
        self.spawnPoints = []
        self.potplants = []

        #Spawn in leaf particle spawners
        self.potplants = []
        for plant in self.tilemap.extract([('potplants', 0), ('potplants', 1), ('potplants', 2), ('potplants', 3), ('large_decor', 1), ('large_decor', 2)], keep = True):
            self.potplants.append(pygame.Rect(plant['pos'][0], plant['pos'][1], self.tilemap.tilesize if plant['type'] == 'potplants' else self.tilemap.tilesize*2, self.tilemap.tilesize))
        
        #Replaces spawn tile with an actual object of the entity:
        for spawner in self.tilemap.extract('spawners'):
            #Player
            if spawner['variant'] == 0:
                #Spawn at spawnpoint if one is active, else default spawn pos.
                if self.spawnPoint and self.currentLevel == 'lobby':
                    self.player.pos[0], self.player.pos[1] = self.spawnPoint[0], self.spawnPoint[1]
                else:
                    self.player.pos = spawner['pos']

                self.player.air_time = 0
                self.player.pos[0] += 4
                self.player.pos[1] += 4    

            #Spawns characters if met OR in their world
            elif self.entityInfo[spawner['variant']]['type'] == 'character':
                if self.charactersMet[self.entityInfo[spawner['variant']]['name']] or self.currentLevel != 'lobby':
                    self.characters.append(self.entityInfo[spawner['variant']]['object'](self, spawner['pos'], (8, 15)))

            #Spawns Enemies
            elif self.entityInfo[spawner['variant']]['type'] == 'enemy':
                self.enemies.append(self.entityInfo[spawner['variant']]['object'](self, spawner['pos'], self.entityInfo[spawner['variant']]['size']))

            #Spawns Entities
            elif self.entityInfo[spawner['variant']]['type'] == 'extraEntity':
                self.extraEntities.append(self.entityInfo[spawner['variant']]['object'](self, spawner['pos'], self.entityInfo[spawner['variant']]['size']))

            #Spawns Spawn Points
            elif self.entityInfo[spawner['variant']]['type'] == 'spawnPoint':
                self.spawnPoints.append(self.entityInfo[spawner['variant']]['object'](self, spawner['pos'], self.entityInfo[spawner['variant']]['size']))

        #Replaces spawn tile with an actual object of the portal:
        for portal in self.tilemap.extract('spawnersPortal'):
            if self.portalsMet[self.portalInfo[portal['variant']]]:
                self.portals.append(Portal(self, portal['pos'], (16, 16), self.portalInfo[portal['variant']]))

        self.dead = False
        self.player.velocity = [0, 0]
        self.player.set_action('idle')
        self.player.updateNearestEnemy()
            
        self.screenshake = 0
        self.transition = -30
        
        self.scroll = [self.player.rect().centerx - self.screen_width / 4,
                       self.player.rect().centery - self.screen_height / 4]

        self.background = pygame.transform.scale(self.assets[f'{self.currentLevel}Background'], (self.screen_width / 2, self.screen_height / 2))
            
        if self.currentLevel == 'lobby':
            self.caveDarkness = self.caveDarknessRange[0]
            self.removeBrokenTunnels()
        elif self.currentLevel == 'normal':
            self.caveDarkness = random.randint(self.caveDarknessRange[0], self.caveDarknessRange[1])
        elif self.currentLevel in ['grass', 'aussie']:
            self.caveDarkness = 0
        elif self.currentLevel in ['spooky', 'space']:
            self.caveDarkness = random.randint(self.caveDarknessRange[1]-50, self.caveDarknessRange[1])
        elif self.currentLevel in ['rubiks']:
            self.caveDarkness = 100

        self.update_dialogues()
        self.initialisingGame = False


    def draw_text(self, text, pos, font, colour = (0, 0, 0), offset = (0, 0), scale = 1, mode = 'topleft'):
        xAdj = 0
        yAdj = 0
       
        img = font.render(str(text), True, colour)
        img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
        if mode == 'center':
            xAdj = img.get_width() / 2
            yAdj = img.get_height() / 2
        elif mode == 'right':
            xAdj = img.get_width()
            yAdj = img.get_height()
        self.HUDdisplay.blit(img, (pos[0] - xAdj, pos[1] - yAdj))


    def displayHUDandText(self):
        textCol = (200, 200, 200) if not self.dead else (200, 0, 0)
        if pygame.time.get_ticks() % 60 == 0:
                self.displayFPS = round(self.clock.get_fps())
        self.draw_text('FPS: ' + str(self.displayFPS), (self.screen_width-35, self.screen_height - 10), self.text_font, textCol, (0, 0), scale = 0.5, mode = 'center')        
        
        if self.currentLevel != 'lobby':
            self.draw_text('Floor: ' + str(self.floors[self.currentLevel]), (self.screen_width - 10, 30), self.text_font, textCol, (0, 0), scale = 0.5, mode = 'right')  
            self.draw_text('Enemies Remaining: ' + str(len(self.enemies)), (self.screen_width / 2, 50), self.text_font, textCol, (0, 0), scale = 0.5, mode = 'center')       
        else:
            self.draw_text('Floor: Lobby', (self.screen_width - 10, 30), self.text_font, textCol, (0, 0), scale = 0.5, mode = 'right') 

        if self.player.total_jumps > 1:
            self.draw_text('Total Jumps: ' + str(self.player.total_jumps), (self.screen_width - 10, 60), self.text_font, textCol, (0, 0), scale = 0.5, mode = 'right')

        if self.powerLevel > 1:
            self.draw_text('Power: ' + str(self.powerLevel), (self.screen_width - 10, 90), self.text_font, textCol, (0, 0), scale = 0.5, mode = 'right')  
              
        depth = 0
        for currency in self.wallet:
            if self.wallet[currency] > 0 or self.walletTemp[currency] > 0:

                if self.infiniteModeActive:
                    extra = (' (' + str(self.walletGainedAmount[currency]) + ' gained)' if (self.dead) else '') 
                else:
                    extra = (' (' + str(self.walletLostAmount[currency]) + ' lost)' if (self.dead and currency not in self.notLostOnDeath) else '') 

                currencyDisplay = str(self.wallet[currency]) + (' + ('+str(self.walletTemp[currency])+')' if (self.currentLevel != 'lobby' and not self.dead and self.walletTemp[currency]) else '') + extra
                
                self.HUDdisplay.blit(self.displayIcons[currency], (10, 10 + depth*30))
                self.draw_text(currencyDisplay, (40, 13 + depth*30), self.text_font, textCol, (0, 0), scale = 0.5)
                depth += 1

        for n in range(self.maxHealth + self.temporaryHealth):
            if n < self.health:
                heartImg = self.assets['heart']
            elif n < self.maxHealth:
                heartImg = self.assets['heartEmpty']
            else:
                heartImg = self.assets['heartTemp']

            self.HUDdisplay.blit(heartImg, (self.screen_width / 2 - ((self.maxHealth + self.temporaryHealth) * 30) / 2 + n * 30, 10))
        
        if self.paused and not self.talking:
            self.draw_text('PAUSED', (self.screen_width / 2, self.screen_height / 2), self.text_font, (200, 200, 200), (0, 0), mode = 'center')
            self.draw_text('Return To Menu: z', (self.screen_width / 2, self.screen_height / 2 + 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'center')
            self.draw_text('Screenshake: ' + ('On' if self.screenshakeOn else 'Off') + ' (s)', (3 * self.screen_width / 4, self.screen_height - 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'center')               
            self.draw_text('Volume: ' + ('On' if self.volumeOn else 'Off') + ' (v)', (self.screen_width / 4, self.screen_height - 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'center')               
            if self.interractionFrameS:
                self.screenshakeOn = not self.screenshakeOn
            if self.interractionFrameV:
                self.volumeOn = not self.volumeOn
                for sound in self.sfxVolumes.keys():
                    self.sfx[sound].set_volume(self.sfxVolumes[sound] if self.volumeOn else 0)
            if self.interractionFrameZ:
                self.paused = False
                self.currentLevel = 'lobby'
                self.floors['infinite'] = 1
                self.sfx['music'].stop()
                self.save_game(self.saveSlot)
                self.__init__()
                self.loadMenu()
            
            self.darkness_surface.fill((0, 0, 0, max(self.minPauseDarkness, self.caveDarkness)))

        if self.talking:
            self.display_text()
            self.darkness_surface.fill((0, 0, 0, max(self.minPauseDarkness, self.caveDarkness)))


    def loadGameAssets(self):
        #one day ill clean this up
        #BASE_PATH = 'data/images/'

        self.assets = {
            'clouds': load_images('clouds'),
            'weapons/gun': load_images('weapons/gun'),
            'weapons/staff': load_images('weapons/staff'),
            'heart': pygame.transform.scale(load_image('misc/heart.png'), (32, 32)),
            'heartEmpty': pygame.transform.scale(load_image('misc/heartEmpty.png'), (32, 32)),
            'heartTemp': pygame.transform.scale(load_image('misc/heartTemp.png'), (32, 32)),

            'player/idle': Animation(load_images('entities/player/idle'), img_dur = 10),
            'player/run': Animation(load_images('entities/player/run'), img_dur = 4),
            'player/jump': Animation(load_images('entities/player/jump'), img_dur = 5),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide'), img_dur = 5),

            'bat/attacking': Animation(load_images('entities/.enemies/bat/attacking'), img_dur = 10),
            'bat/charging': Animation(load_images('entities/.enemies/bat/charging'), img_dur = 20, loop = False),
            'rolypoly/run': Animation(load_images('entities/.enemies/rolypoly/run'), img_dur = 4),
            'spider/run': Animation(load_images('entities/.enemies/spider/run'), img_dur = 4),
            'kangaroo/jumping': Animation(load_images('entities/.enemies/kangaroo/jumping'), img_dur = 4),
            'echidna/walking': Animation(load_images('entities/.enemies/echidna/walking'), img_dur = 6),
            'echidna/charging': Animation(load_images('entities/.enemies/echidna/charging'), img_dur = 30, loop = False),
            'alienship/flying': Animation(load_images('entities/.enemies/alienship/flying'), img_dur = 10),

            'spawnPoint/idle': Animation(load_images('entities/spawnPoint/idle'), img_dur = 4),
            'spawnPoint/active': Animation(load_images('entities/spawnPoint/active'), img_dur = 4),

            'heartAltar/idle': Animation(load_images('entities/heartAltar/idle'), img_dur = 10),
            'heartAltar/active': Animation(load_images('entities/heartAltar/active'), img_dur = 10),

            'meteor/idle': Animation(load_images('entities/meteor/idle'), img_dur = 10, loop = False),
            'meteor/kaboom': Animation(load_images('entities/meteor/kaboom'), img_dur = 5, loop = False),

            'particle/leaf': Animation(load_images('particles/leaf'),img_dur=20, loop = False),
            'glowworm/idle': Animation(load_images('entities/glowworm/idle'),img_dur=15),
            'torch/idle': Animation(load_images('entities/torch/idle'),img_dur=4)}
        
        for idleEnemy in ['bat', 'rolypoly', 'spider', 'kangaroo', 'echidna', 'alienship']:
            self.assets[f'{idleEnemy}/idle'] = Animation(load_images(f'entities/.enemies/{idleEnemy}/idle'), img_dur = 10)

        for graceEnemy in ['bat', 'spider', 'kangaroo', 'echidna']:
            self.assets[f'{graceEnemy}/grace'] = Animation(load_images(f'entities/.enemies/{graceEnemy}/grace'), img_dur = 10)
        
        for tile in ['decor', 'large_decor', 'potplants', 'cacti', 'spawners', 'cracked']:
            self.assets[tile] = load_images(f'tiles/{tile}')

        for misc in ['menuBackground', 'menuBackgroundHH', 'menuBackgroundHHForeground', 'projectile', 'spine', 'light', 'witchHat']:
            self.assets[misc] = load_image(f'misc/{misc}.png')
        
        for cubeState in ['idle', 'white', 'yellow', 'blue', 'green', 'red', 'orange']:
            self.assets[f'rubiksCube/{cubeState}'] = Animation(load_images(f'entities/.enemies/rubiksCube/{cubeState}'), img_dur = 60)

        for gunguyColour in ['', 'Orange', 'Blue', 'Purple']:
            self.assets[f'gunguy{gunguyColour}/idle'] = Animation(load_images(f'entities/.enemies/gunguy{gunguyColour}/idle'), img_dur = 10)
            self.assets[f'gunguy{gunguyColour}/run'] = Animation(load_images(f'entities/.enemies/gunguy{gunguyColour}/run'), img_dur = 4)
            self.assets[f'gunguy{gunguyColour}/grace'] = Animation(load_images(f'entities/.enemies/gunguy{gunguyColour}/grace'), img_dur = 4)
            self.assets[f'gunguy{gunguyColour}/jump'] = Animation(load_images(f'entities/.enemies/gunguy{gunguyColour}/jump'), img_dur = 20)

        for currency in self.wallet.keys():
            self.assets[f'{currency[:-1]}/idle'] = Animation(load_images(f'currencies/{currency[:-1]}/idle'), img_dur = 6)
       
        for levelType in self.portalsMet.keys():
            self.assets[f'portal{levelType}/idle'] = Animation(load_images(f'entities/.portals/portal{levelType}/idle'), img_dur = 6)
            self.assets[f'portal{levelType}/opening'] = Animation(load_images(f'entities/.portals/portal{levelType}/opening'), img_dur = 6, loop = False)
            self.assets[f'portal{levelType}/active'] = Animation(load_images(f'entities/.portals/portal{levelType}/active'), img_dur = 6)
            self.assets[f'{levelType}Background'] = load_image(f'misc/background{levelType}.png')

            if levelType not in ['infinite', 'lobby']:
                self.assets[levelType] = load_images(f'tiles/{levelType}')

        for character in self.charactersMet.keys():
            self.assets[f'{character.lower()}/idle'] = Animation(load_images(f'entities/.characters/{character.lower()}/idle'), img_dur = 10)
            self.assets[f'{character.lower()}/run'] = Animation(load_images(f'entities/.characters/{character.lower()}/run'), img_dur = 4)
            self.assets[f'{character.lower()}/jump'] = Animation(load_images(f'entities/.characters/{character.lower()}/jump'), img_dur = 5)

        for n in range(1,5):
            self.assets[f'particle/particle{n}'] = Animation(load_images(f'particles/particle{n}'), img_dur = 6, loop = False)
            
        self.walletTemp = {}
        self.walletLostAmount = {}
        self.walletGainedAmount = {}
        self.displayIcons = {}
        for currency in self.wallet:
            self.walletTemp[currency] = 0
            self.walletLostAmount[currency] = ''
            self.walletGainedAmount[currency] = ''
            self.displayIcons[currency] = pygame.transform.scale(self.assets[str(currency)[:-1] + '/idle'].images[0], (28,28))
        for floor in self.floors:
            self.displayIcons[floor] = pygame.transform.scale(self.assets['normal' if floor == 'infinite' else floor][0 if floor == 'rubiks' else 1], (28,28))
        self.displayIcons['spawnPoints'] = pygame.transform.scale(self.assets['spawnPoint/active'].images[0], (28,28))
        self.displayIcons['heartAltars'] = pygame.transform.scale(self.assets['heartAltar/active'].images[0], (28,28))
        
        self.sfxVolumes = {
            'music': 0.5,
            'jump': 0.7,
            'dash': 0.2,
            'hit': 0.8,
            'shoot': 0.4,
            'coin': 0.6,
            'ambience': 0.2,
            'textBlip': 0.25,
            'ding': 0.1,
            'dashClick': 0.05
        }

        self.sfx = {}

        for sound in self.sfxVolumes.keys():
            self.sfx[sound] = pygame.mixer.Sound(f'data/sfx/{sound}.wav')
            self.sfx[sound].set_volume(self.sfxVolumes[sound])

        self.windowIcon = load_image('misc/windowIcon.png')
        pygame.display.set_icon(self.windowIcon)

    def run_text(self, character, talkType = 'npc'):
        self.paused = True
        self.talking = True
        self.talkingTo = character
        self.sfx['textBlip'].play(fade_ms = 50)
        if talkType == 'npc':
            convoInfo = character.getConversation()
            self.currentTextList = convoInfo[0]
            character.conversationAction(convoInfo[1])
            self.displayTextList = [str(character.name) + ': ', ' ']
            self.displayIcon = False
        else:
            self.currentTextList = self.encountersCheckText[talkType]
            self.displayTextList = [character, '']
            self.displayIcon = talkType

        self.update_dialogues()
        #Only shallow copy needed
        self.talkingObject = self.displayTextList[:]
        self.currentTextIndex = 0
        self.endTextIndex = len(self.currentTextList)
        self.textLength = 0
        self.textLengthEnd = len(self.currentTextList[0])


    def transitionToLevel(self, newLevel):
        self.nextLevel = newLevel
        self.transition += 1


    def darknessCircle(self, transparency, radius, pos):
        pygame.draw.circle(self.darkness_surface, (0, 0, 0, transparency), pos, radius)
        

    def getSavedDeaths(self):
        deathList = ['No Data', 'No Data', 'No Data']
        for i in range(len(deathList)):
            try:
                f = open('data/saves/' + str(i) + '.json', 'r')
                saveData = json.load(f)
                f.close()

                deathList[i] = 'Deaths: ' + str(saveData['deathCount'])
                
            except FileNotFoundError:
                pass
        try:
            f.close()
        except UnboundLocalError:
            pass
            
        return deathList
    
    def getRandomLevel(self):
        availableFloors = []
        for level in self.floors.keys():
            if self.floors[level] > 1 and level != 'infinite':
                availableFloors.append(level)
        try:
            return random.choice(availableFloors)
        except IndexError:
            return 'normal'
    

    def removeBrokenTunnels(self):
        for tunnel in [e for e in self.tunnelsBroken if self.tunnelsBroken[e] == True]:

            for loc in self.tunnelPositions[tunnel]:
                del self.tilemap.tilemap[str(loc[0]) + ';' + str(loc[1])]


    def delete_save(self, saveSlot):
        try:
            os.remove('data/saves/' + str(saveSlot) + '.json')
        except FileNotFoundError:
            pass


    def save_game(self, saveSlot):
        if self.health <= 0:
            self.health = self.maxHealth
        with open('data/saves/' + str(saveSlot) + '.json', 'w') as f:
            json.dump({'wallet': self.wallet,
                   'maxHealth': self.maxHealth,
                   'powerLevel': self.powerLevel,
                   'difficulty': self.difficulty,
                   'tempHealth': self.temporaryHealth,
                   'totalJumps': self.player.total_jumps,
                   'health': self.health,
                   'tunnelsBroken': self.tunnelsBroken,
                   'deathCount': self.deathCount,
                   'floors': self.floors,
                   'infiniteFloorMax': self.infiniteFloorMax,
                   'spawnPoint': self.spawnPoint,
                   'enemyCountMax': self.enemyCountMax,
                   'mapSize': self.currentLevelSize,
                   'availableEnemyVariants': self.availableEnemyVariants,
                   'screenshakeOn': self.screenshakeOn,
                   'volumeOn': self.volumeOn,
                   'portalsMet': self.portalsMet,
                   'charactersMet': self.charactersMet,
                   'encountersCheck': self.encountersCheck,
                   'dialogue': self.dialogueHistory}, f, indent=4)


    def load_game(self, saveSlot):
        try:
            with open('data/saves/' + str(saveSlot) + '.json', 'r') as f:
                saveData = json.load(f)

                self.wallet = saveData['wallet']
                self.maxHealth = saveData['maxHealth']
                self.powerLevel = saveData['powerLevel']
                self.difficulty = saveData['difficulty']
                self.temporaryHealth = saveData['tempHealth']
                self.player.total_jumps = saveData['totalJumps']
                self.health = saveData['health']
                self.tunnelsBroken = saveData['tunnelsBroken']
                self.deathCount = saveData['deathCount']
                self.floors = saveData['floors']
                self.infiniteFloorMax = saveData['infiniteFloorMax']
                self.spawnPoint = saveData['spawnPoint']
                self.enemyCountMax = saveData['enemyCountMax']
                self.currentLevelSize = saveData['mapSize']
                self.availableEnemyVariants = saveData['availableEnemyVariants']
                self.screenshakeOn = saveData['screenshakeOn']
                self.volumeOn = saveData['volumeOn']
                self.portalsMet = saveData['portalsMet']
                self.charactersMet = saveData['charactersMet']
                self.encountersCheck = saveData['encountersCheck']
                self.dialogueHistory = saveData['dialogue']
            
        except FileNotFoundError:
            f = open('data/saves/' + str(saveSlot) + '.json', 'w')
            json.dump({'floor': self.floors}, f)
            f.close()

        for sound in self.sfxVolumes.keys():
            self.sfx[sound].set_volume(self.sfxVolumes[sound] if self.volumeOn else 0)
        

if __name__ == '__main__':
    Game().loadMenu()
    # cProfile.run('Game().loadMenu()', sort = 'tottime')
