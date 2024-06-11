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
        pygame.display.set_caption('Hilbert\'s Hotel v0.2.1')

        self.text_font = pygame.font.SysFont('Comic Sans MS', 30, bold = True)
        self.clock = pygame.time.Clock()


        #General game parameters
        self.game_running = True
        self.fps = 60
        self.displayFPS = self.fps
        self.initialisingGame = True

        self.movement = [False, False, False, False]
        self.paused = False
        self.talking = False
        self.dead = False
        self.deathCount = 0
        self.interractionFrame = False
        self.caveDarknessRange = (50,250)
        self.caveDarkness = True
        self.minimapActive = False
        self.minimapList = {}

        self.currentTextList = []
        self.maxCharactersLine = 55
        self.talkingTo = ''

        self.currentLevel = 'lobby'
        self.nextLevel = 'lobby'
        self.floors = {
            'normal': 1,
            'grass': 1}

        self.availableEnemyVariants = {
            'normal': [3],
            'normalWeights': [2],
            'grass': [3, 9],
            'grassWeights': [1, 0.5]
        }
        #Screen and display
        self.screen_width = 1080
        self.screen_height = 720
            #main screen
        self.screen = pygame.display.set_mode((self.screen_width,self.screen_height))
            #overlay displays
        self.display_outline = pygame.Surface((self.screen_width / 2, self.screen_height / 2), pygame.SRCALPHA)
        self.display = pygame.Surface((self.screen_width / 2, self.screen_height / 2))
        self.HUDdisplay = pygame.Surface((self.screen_width, self.screen_height))
        self.HUDdisplay.set_colorkey((0, 0, 0))
        self.minimapdisplay = pygame.Surface((self.screen_width / 4, self.screen_height / 4), pygame.SRCALPHA)
        self.darkness_surface = pygame.Surface(self.display_outline.get_size(), pygame.SRCALPHA)

        #VALUES THAT SAVE
        self.maxHealth = 1
        self.health = self.maxHealth
        self.temporaryHealth = 0
        
        self.currentDifficulty = 1
        self.currentLevelSize = 15

        self.spawnPoint = False

        
        self.wallet = {
            'cogs': 0,
            'heartFragments': 0,
            'wings': 0,
            'eyes': 0,
            'hammers': 0
        }

        #Prep dialogue management.
        self.dialogueHistory = {
            'Hilbert': {'0available': True,
                    '0said': False,
                    '1available': False,
                    '1said': False,
                    '2available': False,
                    '2said': False,
                    '3available': False,
                    '3said': False,
                    '4available': False,
                    '4said': False,
                    '5available': False,
                    '5said': False,
                    '6available': False,
                    '6said': False},

            'Noether': {'0available': True,
                    '0said': False,
                    '1available': False,
                    '1said': False,
                    '2available': False,
                    '2said': False,
                    '3available': False,
                    '3said': False,
                    '4available': False,
                    '4said': False,
                    '5available': False,
                    '5said': False},

            'Curie': {'0available': True,
                    '0said': False,
                    '1available': False,
                    '1said': False,
                    '2available': False,
                    '2said': False,
                    '3available': False,
                    '3said': False,
                    '4available': False,
                    '4said': False},

            'Planck': {'0available': True,
                    '0said': False,
                    '1available': False,
                    '1said': False,
                    '2available': False,
                    '2said': False},

            'Faraday': {'0available': True,
                    '0said': False,
                    '1available': False,
                    '1said': False,
                    '2available': False,
                    '2said': False,
                    '3available': False,
                    '3said': False}


        }

        self.charactersMet = {
            'Hilbert': True,
            'Noether': False,
            'Curie': False,
            'Planck': False,
            'Faraday': True
        }
        self.portalsMet = {
            'lobby': True,
            'normal': True,
            'grass': False
        }

        self.encountersCheck = {
            'spawnPoints': False,
            'cogs': False,
            'heartFragments': False,
            'wings': False,
            'eyes': False,
            'hammers': False
        }

        self.encountersCheckText = {
            'spawnPoints': ['TEST TEXT SPAWN'],
            'cogs': ['TEST TEXT COG'],
            'heartFragments': ['TEST TEXT HEART'],
            'wings': ['TEST TEXT WING'],
            'eyes': ['TEST TEXT EYE'],
            'hammers': ['TEST TEXT HAMMER']
        }

        self.tunnelStates = {
            'tunnel1': {'broken': False, 'posList': [[x, y] for x in range(36, 54) for y in range(-1,1)]}
        }
        
       

        #Import assets, this could be cleaned up immensely
            #BASE_PATH = 'data/images/'
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'potplants': load_images('tiles/potplants'),
            'stone': load_images('tiles/stone'),
            'walls': load_images('tiles/walls'),
            'cracked': load_images('tiles/cracked'),
            'menuBackground': load_image('misc/menuBackground.png'),
            'menuBackgroundHH': load_image('misc/menuBackgroundHH.png'),
            'menuBackgroundHHForeground': load_image('misc/menuBackgroundHHForeground.png'),
            'lobbyBackground': load_image('misc/lobbyBackground.png'),
            'caveBackground': load_image('misc/caveBackground.png'),
            'grassBackground': load_image('misc/backgroundGrass.png'),
            'clouds': load_images('clouds'),
            'spawners': load_images('tiles/spawners'),
            'weapons/gun': load_images('weapons/gun'),
            'weapons/staff': load_images('weapons/staff'),
            'projectile': load_image('misc/projectile.png'),
            'heart': load_image('misc/heart.png'),
            'light': load_image('misc/light.png'),
            'heartEmpty': load_image('misc/heartEmpty.png'),
            'heartTemp': load_image('misc/heartTemp.png'),

            'player/idle': Animation(load_images('entities/player/idle'), img_dur = 10),
            'player/run': Animation(load_images('entities/player/run'), img_dur = 4),
            'player/jump': Animation(load_images('entities/player/jump'), img_dur = 5),
            'player/slide': Animation(load_images('entities/player/slide'), img_dur = 5),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide'), img_dur = 5),

            'gunguy/idle': Animation(load_images('entities/gunguy/idle'), img_dur = 10),
            'gunguy/run': Animation(load_images('entities/gunguy/run'), img_dur = 4,),
            'gunguy/grace': Animation(load_images('entities/gunguy/grace'), img_dur = 4),
            'gunguy/jump': Animation(load_images('entities/gunguy/jump'), img_dur = 20),
            'bat/idle': Animation(load_images('entities/bat/idle'), img_dur = 10),
            'bat/grace': Animation(load_images('entities/bat/grace'), img_dur = 10),
            'bat/attacking': Animation(load_images('entities/bat/attacking'), img_dur = 10),
            'bat/charging': Animation(load_images('entities/bat/charging'), img_dur = 20, loop = False),
            'rolypoly/idle': Animation(load_images('entities/rolypoly/idle'), img_dur = 10),
            'rolypoly/run': Animation(load_images('entities/rolypoly/run'), img_dur = 4),

            'spawnPoint/idle': Animation(load_images('entities/spawnPoint/idle'), img_dur = 4),
            'spawnPoint/active': Animation(load_images('entities/spawnPoint/active'), img_dur = 4),

            'particle/leaf': Animation(load_images('particles/leaf'),img_dur=20, loop = False),
            'particle/particle': Animation(load_images('particles/particle'),img_dur=6, loop = False),
            'cog/idle': Animation(load_images('currencies/cog/idle'),img_dur=6),
            'wing/idle': Animation(load_images('currencies/wing/idle'),img_dur=6),
            'heartFragment/idle': Animation(load_images('currencies/heartFragment/idle'),img_dur=10),
            'eye/idle': Animation(load_images('currencies/eye/idle'),img_dur=6),
            'hammer/idle': Animation(load_images('currencies/hammer/idle'),img_dur=6),
            'glowworm/idle': Animation(load_images('entities/glowworm/idle'),img_dur=15)}

       
        for portal in ['lobby', 'normal', 'grass']:
            self.assets[f'portal{portal}/idle'] = Animation(load_images(f'entities/portal{portal}/idle'), img_dur = 6)
            self.assets[f'portal{portal}/opening'] = Animation(load_images(f'entities/portal{portal}/opening'), img_dur = 6, loop = False)
            self.assets[f'portal{portal}/active'] = Animation(load_images(f'entities/portal{portal}/active'), img_dur = 6)

        for character in ['hilbert', 'noether', 'curie', 'planck', 'faraday']:
            self.assets[f'{character}/idle'] = Animation(load_images(f'entities/{character}/idle'), img_dur = 10)
            self.assets[f'{character}/run'] = Animation(load_images(f'entities/{character}/run'), img_dur = 4)
            self.assets[f'{character}/jump'] = Animation(load_images(f'entities/{character}/jump'), img_dur = 5)


        self.walletTemp = {}
        self.displayIcons = {}
        for currency in self.wallet:
            self.walletTemp[currency] = 0
            self.displayIcons[currency] = pygame.transform.scale(self.assets[str(currency)[:-1] + '/idle'].images[0], (28,28))
        self.displayIcons['spawnPoints'] = pygame.transform.scale(self.assets['spawnPoint/active'].images[0], (28,28))
        
   

        
       
        self.sfx = {
           'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
           'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
           'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
           'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
           'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
           'coin': pygame.mixer.Sound('data/sfx/coin.wav')
       }
        
        self.sfx['jump'].set_volume(0.7)
        self.sfx['dash'].set_volume(0.2)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['coin'].set_volume(0.6)
        self.sfx['ambience'].set_volume(0.2)

        #Initialise map 
        self.player = Player(self, (0, 0), (8, 12))
        self.tilemap = tileMap(self, tile_size = 16)
        
    def loadMenu(self):
        self.sfx['ambience'].play(-1)

        inMenu = True
        self.scroll = [0, 0]

        saveSlots = [0, 1, 2]
        hoverSlot = 0
        deleting = 0

        selected = (86, 31, 126)
        notSelected = (1, 1, 1)
        savedFloors = self.getSavedFloors()

        self.clouds = Clouds(self.assets['clouds'], count = 20)
        
        while inMenu:
           

            self.scroll[0] += (self.screen_width / 2)
            self.scroll[1] += (self.screen_height / 2)
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))


            background = pygame.transform.scale(self.assets['menuBackgroundHH'], (self.screen_width / 2, self.screen_height / 2))
            self.display_outline.blit(background, (0, 0))
            self.HUDdisplay.fill((0, 0, 0, 0))
            

            self.clouds.update()
            self.clouds.render(self.display_outline, offset = self.render_scroll)

            foreground = pygame.transform.scale(self.assets['menuBackgroundHHForeground'], (self.screen_width / 2, self.screen_height / 2))
            self.display_outline.blit(foreground, (0, 0))

            #Delete save if held for 5 secs
            if deleting:
                deleting = max(deleting - 1, 0)
                if deleting == 0:
                    self.delete_save(hoverSlot % len(saveSlots))
                    savedFloors = self.getSavedFloors()
            

            #Displaying HUD:
            displaySlot = (hoverSlot % len(saveSlots))
            self.draw_text('Hilbert\'s Hotel', (self.screen_width * (3/4), 60), self.text_font, selected, (0, 0), scale = 1.5, mode = 'center') 
            self.draw_text('Select: x', (self.screen_width * (3/4), 100), self.text_font, notSelected, (0, 0), scale = 0.5, mode = 'center')  
            self.draw_text('Delete: z (hold)', (self.screen_width * (3/4), 120), self.text_font,notSelected, (0, 0), scale = 0.5, mode = 'center')  
            if deleting:
                self.draw_text('Deleting save ' + str(hoverSlot % len(saveSlots)) + ': ' + str(math.floor(deleting / (self.fps/10)) / 10) + 's', (self.screen_width * (3/4), 140), self.text_font, (200, 0, 0), (0, 0), scale = 0.5, mode = 'center')
            
            self.draw_text('Save 0', (self.screen_width * (3/4) - 120, 170), self.text_font, selected if displaySlot == 0 else notSelected, (0, 0), mode = 'center')
            self.draw_text(str(savedFloors[0]), (self.screen_width * (3/4) - 120, 200), self.text_font, selected if displaySlot == 0 else notSelected, (0, 0), mode = 'center', scale = 0.75)
            
            self.draw_text('Save 1', (self.screen_width * (3/4), 170), self.text_font, selected if displaySlot == 1 else notSelected, (0, 0), mode = 'center')
            self.draw_text(str(savedFloors[1]), (self.screen_width * (3/4), 200), self.text_font, selected if displaySlot == 1 else notSelected, (0, 0), mode = 'center', scale = 0.75)
            
            self.draw_text('Save 2', (self.screen_width * (3/4) + 120, 170), self.text_font, selected if displaySlot == 2 else notSelected, (0, 0), mode = 'center') 
            self.draw_text(str(savedFloors[2]), (self.screen_width * (3/4) + 120, 200), self.text_font, selected if displaySlot == 2 else notSelected, (0, 0), mode = 'center', scale = 0.75) 


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
            self.interractionFrame = False
            


    def run(self, saveSlot):
        

        self.saveSlot = saveSlot
        self.load_game(self.saveSlot)
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.background = pygame.transform.scale(self.assets['caveBackground'], (self.screen_width / 2, self.screen_height / 2))

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
                      pos = (rect.x + rect.width / 2, rect.y + rect.height)
                      self.particles.append(Particle(self, 'leaf', pos, vel = [0, 0.3], frame = random.randint(0, 20)))

            for currencyItem in self.currencyEntities:
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
           
            for glowworm in self.glowworms:
                if not self.paused:
                    glowworm.update(self.tilemap)
                glowworm.render(self.display_outline, offset = self.render_scroll)
            
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
            if pygame.time.get_ticks() % 60 == 0:
                self.displayFPS = round(self.clock.get_fps())
            self.draw_text('FPS: ' + str(self.displayFPS), (self.screen_width-35, self.screen_height - 10), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'center')        
            
            if self.currentLevel != 'lobby':
                self.draw_text('Floor: ' + str(self.floors[self.currentLevel]), (self.screen_width - 10, 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right')  
                self.draw_text('Enemies Remaining: ' + str(len(self.enemies)), (self.screen_width - 10, 60), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right')       
            else:
                self.draw_text('Floor: Lobby', (self.screen_width - 10, 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right') 
                
            depth = 0
            for currency in self.wallet:
                if self.wallet[currency] > 0 or self.walletTemp[currency] > 0:
                   
                    currencyDisplay = str(self.wallet[currency]) + (' + ('+str(self.walletTemp[currency])+')' if self.currentLevel != 'lobby' else '')
                    self.HUDdisplay.blit(self.displayIcons[currency], (10, 10 + depth*30))
                    self.draw_text(currencyDisplay, (40, 13 + depth*30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5)
                    depth += 1
  

            for n in range(self.maxHealth + self.temporaryHealth):
                if n < self.health:
                    heartImg = pygame.transform.scale(self.assets['heart'], (32, 32))
                elif n < self.maxHealth:
                    heartImg = pygame.transform.scale(self.assets['heartEmpty'], (32, 32))
                else:
                    heartImg = pygame.transform.scale(self.assets['heartTemp'], (32, 32))

                self.HUDdisplay.blit(heartImg, (self.screen_width / 2 - ((self.maxHealth + self.temporaryHealth) * 30) / 2 + n * 30, 10))
            
            if self.paused and not self.talking:
                self.draw_text('PAUSED', (self.screen_width / 2, self.screen_height / 2), self.text_font, (200, 200, 200), (0, 0), mode = 'center')
                self.draw_text('Return To Menu: z', (self.screen_width / 2, self.screen_height / 2 + 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'center')        
                if self.interractionFrame:
                    self.paused = False
                    self.currentLevel = 'lobby'
                    self.save_game(self.saveSlot)
                    self.__init__()
                    self.loadMenu()
                self.darkness_surface.fill((0, 0, 0, 150))


            
            if self.talking:
                self.display_text()
                self.darkness_surface.fill((0, 0, 0, 150))
                    
    
            #Level transition
            if self.transition > 30:
                self.tilemap.load_tilemap(self.nextLevel, self.currentLevelSize, self.currentDifficulty)
                self.previousLevel = self.currentLevel
                self.currentLevel = self.nextLevel
                self.load_level()
                self.dead = False

            elif self.transition < 31 and self.transition != 0:
                self.transition += 1
            
          
            #Remove interaction frame
            if self.interractionFrame:
                self.interractionFrame = False
                    
            #Event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
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
                    if event.key == pygame.K_x:
                        if not self.paused:
                            self.player.dash()
                    if event.key == pygame.K_z:
                        self.interractionFrame = True
                    if event.key == pygame.K_ESCAPE:
                        if not self.talking:
                            self.paused = not self.paused

                    #DEBUGGING
                    if event.key == pygame.K_r:
                        self.transitionToLevel(self.currentLevel)
                    if event.key == pygame.K_t:
                        for currency in self.wallet:
                            self.wallet[currency] += 20
                    if event.key == pygame.K_k:
                        for e in self.enemies.copy():
                            e.kill()
                            self.enemies.remove(e)
                    if event.key == pygame.K_p:
                        for e in self.enemies.copy():
                            if (e.pos[0] < 0 or e.pos[0] > self.mapHeight*16) or (e.pos[1] < 0 or e.pos[1] > self.mapWidth*16):
                                print(e.type, e.pos)
                                print('OUT OF BOUNDS^')
                        print('player: ', self.player.pos)
                        print('bounds: ', 0,0, ",",self.mapWidth*16, self.mapHeight*16)

                                            

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False
                    if event.key == pygame.K_UP:
                        self.movement[2] = False
                    if event.key == pygame.K_DOWN:
                        self.movement[3] = False

            if self.dead:
                self.dead = min(self.dead + 1, 120)
                self.draw_text('You Died!', (self.screen_width / 2, self.screen_height / 2), self.text_font, (200, 0, 0), self.render_scroll, mode = 'center')
                self.draw_text('Deaths: ' + str(self.deathCount), (self.screen_width / 2, self.screen_height / 2 + 30), self.text_font, (200, 0, 0), self.render_scroll, mode = 'center', scale = 0.5)
                
                if self.dead == 120:
                    self.transitionToLevel('lobby')

            

            #Darkness effect blit:
            if self.caveDarkness:
                self.display_outline.blit(self.darkness_surface, (0, 0))         
            

            self.display.blit(self.display_outline, (0, 0))
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2) 
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
            # self.clock.tick()
        #####################################################
        ####################GAME LOOP END####################
        #####################################################
            




    def update_dialogues(self):
        #Checks to see if the player has the required currency to unlock new dialogues.
        for character in self.characters:
            for index in character.currencyRequirements:
                success = True

                for trade in character.currencyRequirements[index]:
                    #To unlock dialogue you need required currency (sometimes 0)
                    if self.wallet[trade[0]] < trade[1] or index > character.currentDialogueIndex + 1:
                        success = False
                #Also the previous dialogue needs to have been said:
                if index != 0:
                    if not self.dialogueHistory[character.name][str(index - 1) + 'said']:
                        success = False

                #SPECIAL CASES:
                #e.g. dont unlock dialogue if in wrong floor etc.
                
                if (character.name == 'Noether') & (index == 1) & (self.currentLevel != 'lobby'):
                    success = False

                if (character.name == 'Curie') & (index == 1) & (self.currentLevel != 'lobby'):
                    success = False
                
                if (character.name == 'Planck') & (index == 1) & (self.currentLevel != 'lobby'):
                    success = False

                

                if success:
                    self.dialogueHistory[character.name][str(index) + 'available'] = True
                elif not self.dialogueHistory[character.name][str(index) + 'said']:
                    self.dialogueHistory[character.name][str(index) + 'available'] = False

    def display_text(self):
        #Each frame an extra character is added to the displayed text.
        #If the length of a line is larger than self.maxCharactersLine, it creates a new line IF there is a space to not chop words.
        if self.textLength < self.textLengthEnd:
            if self.currentTextList[self.currentTextIndex][self.textLength] == ' ' and len(self.displayTextList[-1]) > self.maxCharactersLine:
                self.displayTextList.append('')
            else:
                self.displayTextList[-1] = self.displayTextList[-1] + self.currentTextList[self.currentTextIndex][self.textLength]
            self.textLength += 1

        #If all text in current chunk is displayed, move to next chunk.
        if self.interractionFrame and self.textLength > 1:
            if self.textLength == self.textLengthEnd:
                self.currentTextIndex += 1
                self.textLength = 0
                self.displayTextList = self.talkingObject[:]
                try:
                    self.textLengthEnd = len(self.currentTextList[self.currentTextIndex])
                except IndexError:
                    pass

            #Fills in current text if the player is impatient
            else:
                #Im sure this while loop will always end, right?
                while self.textLength < self.textLengthEnd:

                    if self.currentTextList[self.currentTextIndex][self.textLength] == ' ' and len(self.displayTextList[-1]) > self.maxCharactersLine:
                        self.displayTextList.append('')
                    else:
                        self.displayTextList[-1] = self.displayTextList[-1] + self.currentTextList[self.currentTextIndex][self.textLength]
                    self.textLength += 1
                    

        #When to end the dialogue:
        if self.currentTextIndex >= self.endTextIndex:
            self.talking = False
            self.paused = False
            self.update_dialogues()
            self.checkNewDialogue()

        #Actually display the text (and icon):
        for n in range(len(self.displayTextList)):
            self.draw_text(str(self.displayTextList[n]), (2*(self.player.pos[0]-self.render_scroll[0]), 2*(self.player.pos[1]-self.render_scroll[1])-30 + 30*n), self.text_font, (255,255,255), (0, 0), mode = 'center')
        if self.displayIcon:
            icon = self.displayIcons[self.displayIcon]
            icon = pygame.transform.scale(icon, (icon.get_width() * 2, icon.get_height() * 2))
            self.HUDdisplay.blit(icon, (2*(self.player.pos[0]-self.render_scroll[0]) - icon.get_width() / 2, 2*(self.player.pos[1]-self.render_scroll[1]) - 90 - icon.get_height() / 2))



    def check_encounter(self, entity):
        if not self.encountersCheck[entity]:
            self.run_text('Information', entity)
            self.encountersCheck[entity] = True
    
    def load_level(self):
        
        #Save game:
        self.save_game(self.saveSlot)

        self.particles = []
        self.projectiles = []
        self.currencyEntities = []
        self.sparks = []
        self.player.dashing = 0
        self.minimapList = {}
        
        if self.dead:
            self.health = self.maxHealth
            for currency in self.wallet:
                self.walletTemp[currency] = 0

        elif not self.dead:
            for currency in self.wallet:
                self.wallet[currency] += self.walletTemp[currency]
                self.walletTemp[currency] = 0
            if not self.initialisingGame and self.currentLevel == 'lobby':
                self.floors[self.previousLevel] += 1
                
              
        

        #Spawn in leaf particle spawners
        self.potplants = []
        for plant in self.tilemap.extract([('potplants', 0), ('potplants', 1), ('potplants', 2), ('potplants', 3)], keep = True):
            self.potplants.append(pygame.Rect(plant['pos'][0],plant['pos'][1], 16, 16))

        #Spawn in entities
        self.enemies = []
        self.portals = []
        self.characters = []
        self.glowworms = []
        self.spawnPoints = []
        self.spawner_list = [
            ('spawners', 0), #player
            ('spawners', 1), #hilbert
            ('spawners', 3), #gunguy
            ('spawners', 4), #bat
            ('spawners', 5), #glowworm
            ('spawners', 6), #noether
            ('spawners', 7), #curie
            ('spawners', 8), #planck
            ('spawners', 2), #faraday
            ('spawners', 9), #rolypoly
            ('spawners', 10) #spawnPoint
        ]
        for spawner in self.tilemap.extract(self.spawner_list):
           
            #Player
            if spawner['variant'] == 0:
                
                #Spawn at spawnpoint if one is active, else default spawn pos.
                if self.spawnPoint and self.currentLevel == 'lobby':
                    self.player.pos = self.spawnPoint[:]
                else:
                    self.player.pos = spawner['pos']

                self.player.air_time = 0
                self.player.pos[0] += 4
                self.player.pos[1] += 4
                    
            
            #Character - Hilbert
            elif spawner['variant'] == 1 and self.charactersMet['Hilbert']:
                self.characters.append(Hilbert(self, spawner['pos'], (8,15)))
               
            #Character - Noether
            elif spawner['variant'] == 6 and (self.charactersMet['Noether'] or self.currentLevel != 'lobby'):
                self.characters.append(Noether(self, spawner['pos'], (8,15)))

            #Character - Curie
            elif spawner['variant'] == 7 and (self.charactersMet['Curie'] or self.currentLevel != 'lobby'):
                self.characters.append(Curie(self, spawner['pos'], (8,15)))

            #Character - Planck
            elif spawner['variant'] == 8 and (self.charactersMet['Planck'] or self.currentLevel != 'lobby'):
                self.characters.append(Planck(self, spawner['pos'], (8,15)))

            #Character - Faraday
            elif spawner['variant'] == 2 and (self.charactersMet['Faraday'] or self.currentLevel != 'lobby'):
                self.characters.append(Faraday(self, spawner['pos'], (8,15)))

            #GlowWorm
            elif spawner['variant'] == 5:
                self.glowworms.append(Glowworm(self, spawner['pos'], (5, 5)))

            #GunGuy
            elif spawner['variant'] == 3:
                self.enemies.append(GunGuy(self, spawner['pos'], (8, 15)))
                
            #Bat
            elif spawner['variant'] == 4:
                self.enemies.append(Bat(self, spawner['pos'], (10, 10)))

            #Rolypoly
            elif spawner['variant'] == 9:
                self.enemies.append(RolyPoly(self, spawner['pos'], (12, 12)))

            #SpawnPoint
            elif spawner['variant'] == 10:
                setAction = 'active' if spawner['pos'] == self.spawnPoint else 'idle'
                self.spawnPoints.append(SpawnPoint(self, spawner['pos'], (16, 16), action = setAction))
            

        self.portal_list = [
            ('spawnersPortal', 0), #To Lobby
            ('spawnersPortal', 1), #To Normal
            ('spawnersPortal', 2)
        ]

        for portal in self.tilemap.extract(self.portal_list):

            #To Lobby
            if portal['variant'] == 0 and self.portalsMet['lobby']:
                self.portals.append(Portal(self, portal['pos'], (16,16), 'lobby'))

            #To normal
            elif portal['variant'] == 1 and self.portalsMet['normal']:
                self.portals.append(Portal(self, portal['pos'], (16,16), 'normal'))

            #To grass
            elif portal['variant'] == 2 and self.portalsMet['grass']:
                self.portals.append(Portal(self, portal['pos'], (16,16), 'grass'))
                

        self.dead = False
        self.player.velocity = [0, 0]
        self.player.set_action('idle')
        self.player.updateNearestEnemy()
            

        self.screenshake = 0
        self.transition = -30
        
        self.scroll = [self.player.rect().centerx - self.screen_width / 4,
                       self.player.rect().centery - self.screen_height / 4]
        
        self.horBuffer = self.screen_height // (self.tilemap.tilesize * 4) + 4
        self.vertBuffer = self.screen_width // (self.tilemap.tilesize * 4) + 4
        self.mapHeight = int(self.currentLevelSize + 2 * self.vertBuffer) 
        self.mapWidth = int(self.currentLevelSize + 2 * self.horBuffer) 

        if self.currentLevel == 'lobby':
            self.background = pygame.transform.scale(self.assets['lobbyBackground'], (self.screen_width / 2, self.screen_height / 2))
            self.caveDarkness = self.caveDarknessRange[0]
            self.removeBrokenTunnels()
        elif self.currentLevel == 'normal':
            self.background = pygame.transform.scale(self.assets['caveBackground'], (self.screen_width / 2, self.screen_height / 2))
            self.caveDarkness = random.randint(self.caveDarknessRange[0], self.caveDarknessRange[1])
        elif self.currentLevel == 'grass':
            self.background = pygame.transform.scale(self.assets['grassBackground'], (self.screen_width / 2, self.screen_height / 2))
            self.caveDarkness = 0

        self.update_dialogues()
        self.checkNewDialogue()
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

    def run_text(self, character, talkType = 'npc'):
        self.paused = True
        self.talking = True
        self.talkingTo = character
        if talkType == 'npc':
            convoInfo = character.getConversation()
            self.currentTextList = convoInfo[0]
            character.conversationAction(convoInfo[1])
            self.displayTextList = [str(character.name) + ': ', ' ']
            self.displayIcon = False
        else:
            self.currentTextList = self.encountersCheckText[talkType]
            self.displayTextList = [character + ': ', '']
            self.displayIcon = talkType

        self.update_dialogues()
        self.checkNewDialogue()
        
        self.talkingObject = self.displayTextList[:]
        self.currentTextIndex = 0
        self.endTextIndex = len(self.currentTextList)
        self.textLength = 0
        self.textLengthEnd = len(self.currentTextList[0])
        

            
    def transitionToLevel(self, newLevel):
        
        self.nextLevel = newLevel
        self.transition += 1

    def checkNewDialogue(self):

        for character in self.characters:
            dialogue = self.dialogueHistory[str(character.name)]
            character.newDialogue = False
           
            
            for index in range(int(len(dialogue) / 2)):
                if dialogue[str(index) + 'available'] and not dialogue[str(index) + 'said']:
                    character.newDialogue = True
                elif dialogue[str(index) + 'said']:
                    character.currentDialogueIndex = index
       

    def darknessCircle(self, transparency, radius, pos):
        pygame.draw.circle(self.darkness_surface, (0, 0, 0, transparency), pos, radius)
        

    def save_game(self, saveSlot):
        if self.health <= 0:
            self.health = self.maxHealth
        with open('data/saves/' + str(saveSlot) + '.json', 'w') as f:
            json.dump({'wallet': self.wallet,
                   'maxHealth': self.maxHealth,
                   'tempHealth': self.temporaryHealth,
                   'totalJumps': self.player.total_jumps,
                   'health': self.health,
                   'tunnelStates': self.tunnelStates,
                   'deathCount': self.deathCount,
                   'floors': self.floors,
                   'spawnPoint': self.spawnPoint,
                   'dialogue': self.dialogueHistory,
                   'difficulty': self.currentDifficulty,
                   'mapSize': self.currentLevelSize,
                   'availableEnemyVariants': self.availableEnemyVariants,
                   'portalsMet': self.portalsMet,
                   'charactersMet': self.charactersMet,
                   'encountersCheck': self.encountersCheck}, f)

    def getSavedFloors(self):
        floorList = ['No Data', 'No Data', 'No Data']
        for i in range(len(floorList)):
            try:
                f = open('data/saves/' + str(i) + '.json', 'r')
                saveData = json.load(f)
                f.close()

                floorList[i] = 'Floor: ' + str(saveData['floors']['normal'])
                
        
            except FileNotFoundError:
                pass
        try:
            f.close()
        except UnboundLocalError:
            pass
            
        return floorList
    
    def removeBrokenTunnels(self):
        for tunnel in self.tunnelStates:
            if self.tunnelStates[tunnel]['broken'] == True:

                for loc in self.tunnelStates[tunnel]['posList']:
                    del self.tilemap.tilemap[str(loc[0]) + ';' + str(loc[1])]

    def delete_save(self, saveSlot):
        try:
            os.remove('data/saves/' + str(saveSlot) + '.json')
        except FileNotFoundError:
            pass

    def load_game(self, saveSlot):
        try:
            with open('data/saves/' + str(saveSlot) + '.json', 'r') as f:
                saveData = json.load(f)
                

                self.wallet = saveData['wallet']
                self.maxHealth = saveData['maxHealth']
                self.temporaryHealth = saveData['tempHealth']
                self.player.total_jumps = saveData['totalJumps']
                self.health = saveData['health']
                self.tunnelStates = saveData['tunnelStates']
                self.deathCount = saveData['deathCount']
                self.floors = saveData['floors']
                self.spawnPoint = saveData['spawnPoint']
                self.dialogueHistory = saveData['dialogue']
                self.currentDifficulty = saveData['difficulty']
                self.currentLevelSize = saveData['mapSize']
                self.availableEnemyVariants = saveData['availableEnemyVariants']
                self.portalsMet = saveData['portalsMet']
                self.charactersMet = saveData['charactersMet']
                self.encountersCheck = saveData['encountersCheck']
            

        except FileNotFoundError:
            f = open('data/saves/' + str(saveSlot) + '.json', 'w')
            json.dump({'floor': self.floors}, f)
            f.close()
        

if __name__ == '__main__':
    Game().loadMenu()
    # cProfile.run('Game().loadMenu()', sort = 'tottime')