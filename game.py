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
        self.game_running = True
        self.fps = 60
        self.displayFPS = self.fps
        self.screen_width = 1080
        self.screen_height = 720

        pygame.init()
        pygame.display.set_caption('Hilbert''s Hotel')

        self.text_font = pygame.font.SysFont('Comic Sans MS', 30, bold = True)
        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode((self.screen_width,self.screen_height))
        self.display_outline = pygame.Surface((self.screen_width / 2, self.screen_height / 2), pygame.SRCALPHA)
        self.display = pygame.Surface((self.screen_width / 2, self.screen_height / 2))
        self.HUDdisplay = pygame.Surface((self.screen_width, self.screen_height))
        self.HUDdisplay.set_colorkey((0, 0, 0))
        self.darkness_surface = pygame.Surface(self.display_outline.get_size(), pygame.SRCALPHA)

        self.currentLevel = 'lobby'
        self.nextLevel = 'lobby'

        self.currentDifficulty = 1
        self.currentLevelSize = 15

        self.moneyThisRun = 0
        self.floor = 0

        self.movement = [False, False, False, False]
        self.paused = False
        self.caveDarknessRange = (50,250)
        self.caveDarkness = True

        self.interractionFrame = False
        self.talking = False
        self.currentTextList = []
        self.maxTextCooldown = 30
        self.textCooldown = self.maxTextCooldown
        self.talkingTo = ''


        self.availableEnemyVariants = {
            '3': 1, #Gunguy
            # '4': 3  #Bat
        }



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
                    '5said': False}


        }

        self.charactersMet = {
            'Hilbert': True,
            'Noether': False
        }
        
       

        #Import assets
        #BASE_PATH = 'data/images/'
        self.assets = {
            'player': load_image('entities/player.png'),
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'menuBackground': load_image('menuBackground.png'),
            'menuBackgroundHH': load_image('menuBackgroundHH.png'),
            'menuBackgroundHHForeground': load_image('menuBackgroundHHForeground.png'),
            'caveBackground': load_image('caveBackground.png'),
            'clouds': load_images('clouds'),
            'spawners': load_images('tiles/spawners'),
            'guns': load_images('guns'),
            'projectile': load_image('projectile.png'),
            'heart': load_image('heart.png'),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur = 10),
            'player/run': Animation(load_images('entities/player/run'), img_dur = 4),
            'player/jump': Animation(load_images('entities/player/jump'), img_dur = 5),
            'player/slide': Animation(load_images('entities/player/slide'), img_dur = 5),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide'), img_dur = 5),
            'gunguy/idle': Animation(load_images('entities/gunguy/idle'), img_dur = 10),
            'gunguy/run': Animation(load_images('entities/gunguy/run'), img_dur = 4,),
            'gunguy/grace': Animation(load_images('entities/gunguy/grace'), img_dur = 4),
            'gunguy/shooting': Animation(load_images('entities/gunguy/shooting'), img_dur = 20, loop = False),
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
            'portal/idle': Animation(load_images('entities/portal/idle'), img_dur = 6),
            'portal/opening': Animation(load_images('entities/portal/opening'), img_dur = 6, loop = False),
            'portal/active': Animation(load_images('entities/portal/active'), img_dur = 6),
            'particle/dust': Animation(load_images('particles/dust'),img_dur=20, loop = False),
            'particle/particle': Animation(load_images('particles/particle'),img_dur=6, loop = False),
            'cog/idle': Animation(load_images('entities/cog/idle'),img_dur=6),
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
        
        #Set player values:
        self.money = 0
        self.maxHealth = 1

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

        selected = (200, 100, 100)
        selected = (86, 31, 126)
        notSelected = (255, 255, 255)
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
            self.draw_text('Hilbert\'s Hotel', (self.screen_width * (3/4), 60), self.text_font, selected, (0, 0), mode = 'center') 
            self.draw_text('Select: x', (self.screen_width * (3/4), 100), self.text_font, notSelected, (0, 0), scale = 0.5, mode = 'center')  
            self.draw_text('Delete: z (hold)', (self.screen_width * (3/4), 120), self.text_font,notSelected, (0, 0), scale = 0.5, mode = 'center')  
            if deleting:
                self.draw_text('Deleting save ' + str(hoverSlot % len(saveSlots)) + ': ' + str(math.floor(deleting / (self.fps/10)) / 10) + 's', (self.screen_width * (3/4), 140), self.text_font, (200, 0, 0), (0, 0), scale = 0.5, mode = 'center')
            # self.draw_text('Please Select Your Room', (self.screen_width / 2, self.screen_height / 2 - 60), self.text_font, notSelected, (0, 0), mode = 'center')   
            # self.draw_text('Select Save with Arrow Keys and x', (self.screen_width * (3/4), 100), self.text_font, notSelected, (0, 0), scale = 0.75, mode = 'center')
            
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
            

        
            self.screenshake = max(0, self.screenshake - 1)

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

            for rect in self.dust_spawners:
                  if random.random() < 0.01:
                      pos = (rect.x + rect.width / 2, rect.y + rect.height)
                      self.particles.append(Particle(self, 'dust', pos, vel = [0, 0.3], frame = random.randint(0, 20)))

            for cog in self.cogs:
                if not self.paused:
                    if cog.update(self.tilemap, (0, 0)):
                        self.cogs.remove(cog)
                cog.render(self.display_outline, offset = self.render_scroll)
            
            
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
                kill = particle.update()
                particle.render(self.display_outline, offset = self.render_scroll)
                if particle.type == 'dust':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035 + particle.randomness) * 0.2
                if kill:
                    self.particles.remove(particle)  
           
            
            #Displaying HUD and text:
            if pygame.time.get_ticks() % 60 == 0:
                self.displayFPS = round(self.clock.get_fps())
            self.draw_text('FPS: ' + str(self.displayFPS), (self.screen_width-35, self.screen_height - 10), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'center')        
            
            
            if self.currentLevel != 'lobby':
                self.draw_text('Floor: ' + str(self.floor), (self.screen_width - 10, 20), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right')  
                self.draw_text('Enemies Remaining: ' + str(len(self.enemies)), (self.screen_width - 10, 40), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right')       
            else:
                self.draw_text('Floor: Lobby', (self.screen_width - 10, 20), self.text_font, (200, 200, 200), (0, 0), scale = 0.5, mode = 'right') 
                

            
            moneyDisplay = str(self.money) + (' + ('+str(self.moneyThisRun)+')' if self.currentLevel != 'lobby' else '')
            if self.money > 0 or self.moneyThisRun > 0:
                self.HUDdisplay.blit(pygame.transform.scale(self.assets['cog/idle'].images[0], (28,28)), (0, 10))
                self.draw_text(moneyDisplay, (30, 13), self.text_font, (200, 200, 200), (0, 0), scale = 0.5)        
            
            for _ in range(self.health):
                self.HUDdisplay.blit(pygame.transform.scale(self.assets['heart'], (32, 32)), (self.screen_width / 2 - (self.health * 30) / 2 + _ * 30, 10))
            # self.draw_text('Health: ' + str(self.health), (20, 60), self.text_font, (200, 200, 200), (0, 0), scale = 0.5)               
            
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
                if self.textCooldown > 0:
                    self.textCooldown -= 1

                text = str(self.talkingTo.name) +': ' + self.currentTextList[self.currentTextIndex]
                self.draw_text(text, (2*(self.player.pos[0]-self.render_scroll[0]), 2*(self.player.pos[1]-self.render_scroll[1])-30), self.text_font, (255,255,255), (0, 0), mode = 'center')
                
                if self.interractionFrame and not self.textCooldown:
                    self.currentTextIndex += 1
                    self.textCooldown = self.maxTextCooldown
                   
                
                if self.currentTextIndex >= self.endTextIndex:
                    self.talking = False
                    self.paused = False
                    
                    
                    self.checkNewDialogue()
                    
                    
                    



            #level transition
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

                    if event.key == pygame.K_r:
                        self.transitionToLevel(self.currentLevel)
                    

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
                self.dead += 1
                self.draw_text('You Died!', (self.screen_width / 2, self.screen_height / 2), self.text_font, (200, 0, 0), self.render_scroll, mode = 'center')
                
                if self.dead == 90:
                    self.transitionToLevel('lobby')

            

            #Darkness effect blit:
            if self.caveDarkness:
                # self.darkness_surface.convert_alpha()
                # self.darkness_surface.set_colorkey((255, 255, 255))
                self.display_outline.blit(self.darkness_surface, (0, 0))         
            


            self.display.blit(self.display_outline, (0, 0))
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2) 
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)
         
            self.screen.blit(self.HUDdisplay, (0, 0))

            #Level transition circle
            if self.transition:
                transition_surface = pygame.Surface(self.screen.get_size())
                pygame.draw.circle(transition_surface, (255, 255, 255), (self.screen.get_width() // 2, self.screen.get_height() // 2), (30 - abs(self.transition)) * (self.screen.get_width() / 30))
                transition_surface.set_colorkey((255, 255, 255))
                self.screen.blit(transition_surface, (0, 0))



            pygame.display.update()
            self.clock.tick(self.fps)
            (self.clock.get_fps())



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
        self.currentTextList = convoInfo[0]
        character.conversationAction(convoInfo[1])
        self.currentTextIndex = 0
        self.endTextIndex = len(self.currentTextList)

    def save_game(self, saveSlot):

        f = open('data/saves/' + str(saveSlot) + '.json', 'w')
        json.dump({'totalMoney': self.money,
                   'maxHealth': self.maxHealth,
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

            self.money = saveData['totalMoney']
            self.maxHealth = saveData['maxHealth']
            self.floor = saveData['floor']
            self.dialogueHistory = saveData['dialogue']
            self.currentDifficulty = saveData['difficulty']
            self.currentLevelSize = saveData['mapSize']
            self.availableEnemyVariants = saveData['availableEnemyVariants']
            self.charactersMet = saveData['charactersMet']
            

        except FileNotFoundError:
            f = open('data/saves/' + str(saveSlot) + '.json', 'w')
            json.dump({'totalMoney': self.money}, f)
            f.close()

            
    def transitionToLevel(self, newLevel):
        if not self.dead:
            self.money += self.moneyThisRun
        self.moneyThisRun = 0
        self.nextLevel = newLevel
        self.transition += 1

    def checkNewDialogue(self):
        for character in self.characters:
            dialogue = self.dialogueHistory[str(character.name)]
            character.newDialogue = False
           
            
            for index in range(int(len(dialogue) / 2)):
                if dialogue[str(index) + 'available'] and not dialogue[str(index) + 'said']:
                    character.newDialogue = True
                    

    def update_dialogues(self):
        #Need both conditions with the previous text so you cant spend more money than you have.
        #Hilbert:
        if self.money >= 5:
            self.dialogueHistory['Hilbert']['2available'] = True
        elif not self.dialogueHistory['Hilbert']['2said']:
            self.dialogueHistory['Hilbert']['2available'] = False

        if self.money >= 50:
            self.dialogueHistory['Hilbert']['3available'] = True
        elif not self.dialogueHistory['Hilbert']['3said']:
            self.dialogueHistory['Hilbert']['3available'] = False
       
        if self.money >= 100:
            self.dialogueHistory['Hilbert']['4available'] = True
        elif not self.dialogueHistory['Hilbert']['4said']:
            self.dialogueHistory['Hilbert']['4available'] = False
        

        #Noether:
        if self.currentLevel == 'lobby' and self.charactersMet['Noether']:
            self.dialogueHistory['Noether']['1available'] = True
        elif not self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['1available'] = False
        
        if self.money >= 5 and self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['2available'] = True
        elif not self.dialogueHistory['Noether']['2said']:
            self.dialogueHistory['Noether']['2available'] = False
        
        if self.money >= 20 and self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['3available'] = True
        elif not self.dialogueHistory['Noether']['3said']:
            self.dialogueHistory['Noether']['3available'] = False

        if self.money >= 50 and self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['4available'] = True
        elif not self.dialogueHistory['Noether']['4said']:
            self.dialogueHistory['Noether']['4available'] = False
    
        if self.money >= 100 and self.dialogueHistory['Noether']['1said']:
            self.dialogueHistory['Noether']['5available'] = True
        elif not self.dialogueHistory['Noether']['5said']:
            self.dialogueHistory['Noether']['5available'] = False
       

    def darknessCircle(self, transparency, radius, pos):
        pygame.draw.circle(self.darkness_surface, (0, 0, 0, transparency), pos, radius)
        
    def load_level(self):
        
        #Save game:
        self.save_game(self.saveSlot)

        self.particles = []
        self.projectiles = []
        self.cogs = []
        self.sparks = []
        self.health = self.maxHealth
        self.moneyThisRun = 0
        self.player.dashing = 0

        #Spawn in dust particle spawners
        self.dust_spawners = []
        for dust in self.tilemap.extract([('large_decor', 3)], keep = True):
            self.dust_spawners.append(pygame.Rect(dust['pos'][0],dust['pos'][1], 16, 16))

        #Spawn in entities
        self.enemies = []
        self.portals = []
        self.characters = []
        self.glowworms = []
        self.spawner_list = [
            ('spawners', 0), #player
            ('spawners', 1), #character
            ('spawners', 2), #portal
            ('spawners', 3), #gunguy
            ('spawners', 4), #bat
            ('spawners', 5), #glowworm
            ('spawners', 6) #noether
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
        
        self.scroll = [self.player.rect().centerx - self.screen_width / 4,
                       self.player.rect().centery - self.screen_height / 4]
        
        self.screenshake = 0
        self.transition = -30

        if self.currentLevel == 'lobby':
            self.caveDarkness = 0
        else:
            self.caveDarkness = random.randint(self.caveDarknessRange[0], self.caveDarknessRange[1])

        self.update_dialogues()
        self.checkNewDialogue()
        

            


Game().loadMenu()