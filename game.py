import pygame
import pygame.freetype
import sys
import random
import math
import os
from scripts.entities import *
from scripts.utilities import *
from scripts.tilemap import *
from scripts.clouds import *
from scripts.particle import *
from scripts.spark import *

class Game:
    def __init__(self):

        #Pygame specific parameters and initialisation
        pygame.init()
        pygame.display.set_caption('Hilbert\'s Hotel v0.1.2')

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
        self.interractionFrame = False
        self.caveDarknessRange = (50,250)
        self.caveDarkness = True
        self.minimapActive = False
        self.minimapList = {}

        self.currentTextList = []
        self.maxTextCooldown = 30
        self.textCooldown = self.maxTextCooldown
        self.talkingTo = ''

        self.currentLevel = 'lobby'
        self.nextLevel = 'lobby'
        self.floor = 1

        #Format: variant: difficulty
        #Begins just with gunguy
        self.availableEnemyVariants = {
            '3': 1
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
        
        self.currentDifficulty = 1
        self.currentLevelSize = 15

        
        self.wallet = {
            'cogs': 0,
            'heartFragments': 0,
            'wings': 0
        }

        #(this one doesnt save)
        self.walletTemp = {}
        for currency in self.wallet:
            self.walletTemp[currency] = 0

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
                    '4said': False},

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
                    '4said': False}


        }

        self.charactersMet = {
            'Hilbert': True,
            'Noether': False,
            'Curie': False
        }
        
       

        #Import assets, this could be cleaned up immensely
            #BASE_PATH = 'data/images/'
        self.assets = {
            'player': load_image('entities/player.png'),
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'potplants': load_images('tiles/potplants'),
            'stone': load_images('tiles/stone'),
            'walls': load_images('tiles/walls'),
            'menuBackground': load_image('menuBackground.png'),
            'menuBackgroundHH': load_image('menuBackgroundHH.png'),
            'menuBackgroundHHForeground': load_image('menuBackgroundHHForeground.png'),
            'caveBackground': load_image('caveBackground.png'),
            'clouds': load_images('clouds'),
            'spawners': load_images('tiles/spawners'),
            'weapons/gun': load_images('weapons/gun'),
            'weapons/staff': load_images('weapons/staff'),
            'projectile': load_image('projectile.png'),
            'heart': load_image('heart.png'),
            'heartEmpty': load_image('heartEmpty.png'),
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
            'hilbert/idle': Animation(load_images('entities/hilbert/idle'), img_dur = 10),
            'hilbert/run': Animation(load_images('entities/hilbert/run'), img_dur = 4),
            'hilbert/jump': Animation(load_images('entities/hilbert/jump'), img_dur = 5),
            'noether/idle': Animation(load_images('entities/noether/idle'), img_dur = 10),
            'noether/run': Animation(load_images('entities/noether/run'), img_dur = 4),
            'noether/jump': Animation(load_images('entities/noether/jump'), img_dur = 5),
            'curie/idle': Animation(load_images('entities/curie/idle'), img_dur = 10),
            'curie/run': Animation(load_images('entities/curie/run'), img_dur = 4),
            'curie/jump': Animation(load_images('entities/curie/jump'), img_dur = 5),
            'portal/idle': Animation(load_images('entities/portal/idle'), img_dur = 6),
            'portal/opening': Animation(load_images('entities/portal/opening'), img_dur = 6, loop = False),
            'portal/active': Animation(load_images('entities/portal/active'), img_dur = 6),
            'particle/leaf': Animation(load_images('particles/leaf'),img_dur=20, loop = False),
            'particle/particle': Animation(load_images('particles/particle'),img_dur=6, loop = False),
            'cog/idle': Animation(load_images('entities/cog/idle'),img_dur=6),
            'wing/idle': Animation(load_images('entities/wing/idle'),img_dur=6),
            'heartFragment/idle': Animation(load_images('entities/heartFragment/idle'),img_dur=10),
            'glowworm/idle': Animation(load_images('entities/glowworm/idle'),img_dur=15)

        }
       
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
        self.player = Player(self, (50, 50), (8, 15))
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

        self.tilemap.load_tilemap('lobby')
        self.load_level()

        while self.game_running:
            #Camera movement
            self.scroll[0] += (self.player.rect().centerx - self.screen_width / 4 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.screen_height / 4 - self.scroll[1]) / 30
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            #Background
            background = pygame.transform.scale(self.assets['caveBackground'], (self.screen_width / 2, self.screen_height / 2))
            self.display.blit(background, (0, 0))
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
            
            for character in self.characters.copy():
                if not self.paused:
                    character.update(self.tilemap)
                character.render(self.display_outline, offset = self.render_scroll)

            if not self.dead:
                if not self.paused:
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display_outline, offset = self.render_scroll)
            
            for projectile in self.projectiles.copy():
                if not self.paused:
                    if projectile.update(self):
                        self.projectiles.remove(projectile)

            
            for rect in self.potplants:
                  if random.random() < 0.01 and not self.paused:
                      pos = (rect.x + rect.width / 2, rect.y + rect.height)
                      self.particles.append(Particle(self, 'leaf', pos, vel = [0, 0.3], frame = random.randint(0, 20)))

            for cog in self.cogs:
                if not self.paused:
                    if cog.update(self.tilemap, (0, 0)):
                        self.cogs.remove(cog)
                cog.render(self.display_outline, offset = self.render_scroll)
            for fragment in self.heartFragments:
                if not self.paused:
                    if fragment.update(self.tilemap, (0, 0)):
                        self.heartFragments.remove(fragment)
                fragment.render(self.display_outline, offset = self.render_scroll)
            for wing in self.wings:
                
                if not self.paused:
                    if wing.update(self.tilemap, (0, 0)):
                        self.wings.remove(wing)
                wing.render(self.display_outline, offset = self.render_scroll)
           
          
            
            
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
                self.draw_text('Floor: ' + str(self.floor), (self.screen_width - 10, 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right')  
                self.draw_text('Enemies Remaining: ' + str(len(self.enemies)), (self.screen_width - 10, 60), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right')       
            else:
                self.draw_text('Floor: Lobby', (self.screen_width - 10, 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right') 
                
            depth = 0
            for currency in self.wallet:
                if self.wallet[currency] > 0 or self.walletTemp[currency] > 0:
                   
                    currencyDisplay = str(self.wallet[currency]) + (' + ('+str(self.walletTemp[currency])+')' if self.currentLevel != 'lobby' else '')
                    self.HUDdisplay.blit(pygame.transform.scale(self.assets[str(currency)[:-1] + '/idle'].images[0], (28,28)), (10, 10 + depth*30))
                    self.draw_text(currencyDisplay, (40, 13 + depth*30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5)
                    depth += 1
  

            for n in range(self.maxHealth):
                if n < self.health:
                    heartImg = pygame.transform.scale(self.assets['heart'], (32, 32))
                else:
                    heartImg = pygame.transform.scale(self.assets['heartEmpty'], (32, 32))
                self.HUDdisplay.blit(heartImg, (self.screen_width / 2 - (self.maxHealth * 30) / 2 + n * 30, 10))
            
            if self.paused and not self.talking:
                self.draw_text('PAUSED', (self.screen_width / 2, self.screen_height / 2), self.text_font, (200, 200, 200), (0, 0), mode = 'center')
                self.draw_text('Return To Menu: z', (self.screen_width / 2, self.screen_height / 2 + 30), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'center')        
                if self.interractionFrame:
                    self.paused = False
                    self.currentLevel = 'lobby'
                    self.save_game(self.saveSlot)
                    self.__init__()
                    self.loadMenu()


            #Talking mechanics:
            if self.talking:
                if self.textLength < self.textLengthEnd:
                    self.textLength += 1

                if self.interractionFrame and self.textLength > 1:
                    if self.textLength == self.textLengthEnd:
                        self.currentTextIndex += 1
                        self.textCooldown = self.maxTextCooldown
                        self.textLength = 0
                        try:
                            self.textLengthEnd = len(self.currentTextList[self.currentTextIndex])
                        except IndexError:
                            pass
                    else:
                        self.textLength = self.textLengthEnd
                   
                if self.currentTextIndex >= self.endTextIndex:
                    self.talking = False
                    self.paused = False
                    self.update_dialogues()
                    self.checkNewDialogue()

                try:
                    text = str(self.talkingTo.name) +': ' + self.currentTextList[self.currentTextIndex][:self.textLength]
                except IndexError:
                        pass
                self.draw_text(text, (2*(self.player.pos[0]-self.render_scroll[0]), 2*(self.player.pos[1]-self.render_scroll[1])-30), self.text_font, (255,255,255), (0, 0), mode = 'center')
                
                    
    
            #Level transition
            if self.transition > 30:
                self.tilemap.load_tilemap(self.nextLevel, self.currentLevelSize, self.currentDifficulty)
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
                            self.wallet[currency] += 1
                    if event.key == pygame.K_k:
                        for e in self.enemies.copy():
                            e.kill()
                            self.enemies.remove(e)
                    if event.key == pygame.K_p:
                        horBuffer = 720 // (16 * 4) + 4
                        vertBuffer = 1080 // (16 * 4) + 4
                        mapHeight = int(self.currentLevelSize + 2 * vertBuffer) 
                        mapWidth = int(self.currentLevelSize + 2 * horBuffer) 
                        for e in self.enemies.copy():
                            print(e.type, e.pos)
                        print('bounds: ', horBuffer * 16,vertBuffer * 16, ",",(mapWidth - horBuffer)*16,( mapHeight - vertBuffer)*16)
                        
                            
                    
                    

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
                self.dead = min(self.dead + 1, 90)
                self.draw_text('You Died!', (self.screen_width / 2, self.screen_height / 2), self.text_font, (200, 0, 0), self.render_scroll, mode = 'center')
                
                if self.dead == 90:
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
            (self.clock.get_fps())


    def update_dialogues(self):
        #Need both conditions with the previous text so you cant spend more money than you have.
        #Hilbert:
        if self.wallet['cogs'] >= 5:
            self.dialogueHistory['Hilbert']['2available'] = True
        elif not self.dialogueHistory['Hilbert']['2said']:
            self.dialogueHistory['Hilbert']['2available'] = False

        if self.wallet['cogs'] >= 50:
            self.dialogueHistory['Hilbert']['3available'] = True
        elif not self.dialogueHistory['Hilbert']['3said']:
            self.dialogueHistory['Hilbert']['3available'] = False
       
        if self.wallet['cogs'] >= 100:
            self.dialogueHistory['Hilbert']['4available'] = True
        elif not self.dialogueHistory['Hilbert']['4said']:
            self.dialogueHistory['Hilbert']['4available'] = False
        

        #Noether:
        if self.currentLevel == 'lobby' and self.charactersMet['Noether']:
            self.dialogueHistory['Noether']['1available'] = True
        elif not self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['1available'] = False
        
        if self.wallet['heartFragments'] >= 5 and self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['2available'] = True
        elif not self.dialogueHistory['Noether']['2said']:
            self.dialogueHistory['Noether']['2available'] = False
        
        if self.wallet['heartFragments'] >= 20 and self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['3available'] = True
        elif not self.dialogueHistory['Noether']['3said']:
            self.dialogueHistory['Noether']['3available'] = False

        if self.wallet['heartFragments'] >= 50 and self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['4available'] = True
        elif not self.dialogueHistory['Noether']['4said']:
            self.dialogueHistory['Noether']['4available'] = False
    
        if self.wallet['heartFragments'] >= 100 and self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['5available'] = True
        elif not self.dialogueHistory['Noether']['5said']:
            self.dialogueHistory['Noether']['5available'] = False

        #Curie:
        if self.currentLevel == 'lobby' and self.charactersMet['Curie']:
            self.dialogueHistory['Curie']['1available'] = True
        elif not self.dialogueHistory['Curie']['1said']:
            self.dialogueHistory['Curie']['1available'] = False
        
        if self.wallet['wings'] >= 5 and self.dialogueHistory['Curie']['1said']:
            self.dialogueHistory['Curie']['2available'] = True
        elif not self.dialogueHistory['Curie']['2said']:
            self.dialogueHistory['Curie']['2available'] = False
        
        if self.wallet['wings'] >= 50 and self.dialogueHistory['Curie']['1said']:
            self.dialogueHistory['Curie']['3available'] = True
        elif not self.dialogueHistory['Curie']['3said']:
            self.dialogueHistory['Curie']['3available'] = False

        if self.wallet['wings'] >= 100 and self.dialogueHistory['Curie']['1said']:
            self.dialogueHistory['Curie']['4available'] = True
        elif not self.dialogueHistory['Curie']['4said']:
            self.dialogueHistory['Curie']['4available'] = False

    
    def load_level(self):
        
        #Save game:
        self.save_game(self.saveSlot)

        self.particles = []
        self.projectiles = []
        self.cogs = []
        self.heartFragments = []
        self.wings = []
        self.sparks = []
        self.player.dashing = 0
        self.minimapList = {}
        
        if self.dead:
            self.health = self.maxHealth
            for currency in self.wallet:
                self.wallet[currency] = int((self.wallet[currency] + 1) / 2)
                self.walletTemp[currency] = 0
        elif not self.dead:
            for currency in self.wallet:
                self.wallet[currency] += self.walletTemp[currency]
                self.walletTemp[currency] = 0
            if not self.initialisingGame and self.currentLevel == 'lobby':
                self.floor += 1
              
        

        #Spawn in leaf particle spawners
        self.potplants = []
        for plant in self.tilemap.extract([('potplants', 0), ('potplants', 1), ('potplants', 2), ('potplants', 3)], keep = True):
            self.potplants.append(pygame.Rect(plant['pos'][0],plant['pos'][1], 16, 16))

        #Spawn in entities
        self.enemies = []
        self.portals = []
        self.characters = []
        self.glowworms = []
        self.spawner_list = [
            ('spawners', 0), #player
            ('spawners', 1), #hilbert
            ('spawners', 2), #portal
            ('spawners', 3), #gunguy
            ('spawners', 4), #bat
            ('spawners', 5), #glowworm
            ('spawners', 6), #noether
            ('spawners', 7) #curie
        ]
        for spawner in self.tilemap.extract(self.spawner_list):
           
            #Player
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            
            #Character - Hilbert
            elif spawner['variant'] == 1 and self.charactersMet['Hilbert']:
                self.characters.append(Hilbert(self, spawner['pos'], (8,15)))
               
            #Character - Noether
            elif spawner['variant'] == 6 and (self.charactersMet['Noether'] or self.currentLevel != 'lobby'):
                self.characters.append(Noether(self, spawner['pos'], (8,15)))

            #Character - Noether
            elif spawner['variant'] == 7 and (self.charactersMet['Curie'] or self.currentLevel != 'lobby'):
                self.characters.append(Curie(self, spawner['pos'], (8,15)))


            #Portal
            elif spawner['variant'] == 2:
                if self.currentLevel == 'lobby':
                    portalDest = 'random'
                else:
                    portalDest = 'lobby'
                self.portals.append(Portal(self, spawner['pos'], (16,16), portalDest))

            #GlowWorm
            elif spawner['variant'] == 5:
                self.glowworms.append(Glowworm(self, spawner['pos'], (5, 5)))

            #GunGuy
            elif spawner['variant'] == 3:
                self.enemies.append(GunGuy(self, spawner['pos'], (8, 15)))
                
            #Bat
            elif spawner['variant'] == 4:
                self.enemies.append(Bat(self, spawner['pos'], (10, 10)))
            

        self.dead = False
        self.player.velocity = [0, 0]
        self.player.set_action('idle')
        self.player.updateNearestEnemy()

        self.screenshake = 0
        self.transition = -30
        
        self.scroll = [self.player.rect().centerx - self.screen_width / 4,
                       self.player.rect().centery - self.screen_height / 4]
        
        

        if self.currentLevel == 'lobby':
            self.caveDarkness = self.caveDarknessRange[0]
        else:
            self.caveDarkness = random.randint(self.caveDarknessRange[0], self.caveDarknessRange[1])

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

    def run_text(self, character):
        self.paused = True
        self.talking = True
        self.talkingTo = character
        convoInfo = character.getConversation()
        self.update_dialogues()
        self.checkNewDialogue()
        self.currentTextList = convoInfo[0]
        character.conversationAction(convoInfo[1])
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
       

    def darknessCircle(self, transparency, radius, pos):
        pygame.draw.circle(self.darkness_surface, (0, 0, 0, transparency), pos, radius)


    def save_game(self, saveSlot):
        f = open('data/saves/' + str(saveSlot) + '.json', 'w')
        json.dump({'wallet': self.wallet,
                   'maxHealth': self.maxHealth,
                   'totalJumps': self.player.total_jumps,
                   'health': self.health,
                   'floor': self.floor,
                   'dialogue': self.dialogueHistory,
                   'difficulty': self.currentDifficulty,
                   'mapSize': self.currentLevelSize,
                   'availableEnemyVariants': self.availableEnemyVariants,
                   'charactersMet': self.charactersMet}, f)
        f.close()

    def getSavedFloors(self):
        floorList = ['No Data', 'No Data', 'No Data']
        for i in range(len(floorList)):
            try:
                f = open('data/saves/' + str(i) + '.json', 'r')
                saveData = json.load(f)
                f.close()

                floorList[i] = 'Floor: ' + str(saveData['floor'])
                
        
            except FileNotFoundError:
                pass
        try:
            f.close()
        except UnboundLocalError:
            pass
            
        return floorList

    def delete_save(self, saveSlot):
        try:
            os.remove('data/saves/' + str(saveSlot) + '.json')
        except FileNotFoundError:
            pass

    def load_game(self, saveSlot):
        try:
            f = open('data/saves/' + str(saveSlot) + '.json', 'r')
            saveData = json.load(f)
            f.close()

            self.wallet = saveData['wallet']
            self.maxHealth = saveData['maxHealth']
            self.player.total_jumps = saveData['totalJumps']
            self.health = saveData['health']
            self.floor = saveData['floor']
            self.dialogueHistory = saveData['dialogue']
            self.currentDifficulty = saveData['difficulty']
            self.currentLevelSize = saveData['mapSize']
            self.availableEnemyVariants = saveData['availableEnemyVariants']
            self.charactersMet = saveData['charactersMet']
            

        except FileNotFoundError:
            f = open('data/saves/' + str(saveSlot) + '.json', 'w')
            json.dump({'floor': self.floor}, f)
            f.close()
        

            


Game().loadMenu()