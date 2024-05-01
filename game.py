import pygame
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
        self.screen_width = 1080
        self.screen_height = 720

        pygame.init()
        pygame.display.set_caption('Hilbert''s Hotel')

        self.text_font = pygame.font.SysFont('Arial', 30)
        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode((self.screen_width,self.screen_height))
        self.display_outline = pygame.Surface((self.screen_width / 2, self.screen_height / 2), pygame.SRCALPHA)
        self.display = pygame.Surface((self.screen_width / 2, self.screen_height / 2))

        self.currentLevel = 'lobby'
        self.nextLevel = 'lobby'
        self.currentDifficulty = 3
        self.currentLevelSize = 20

        self.movement = [False, False, False, False]

        #Import assets
        #BASE_PATH = 'data/images/'
        self.assets = {
            'player': load_image('entities/player.png'),
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'background': load_image('background.png'),
            'menuBackground': load_image('menuBackground.png'),
            'clouds': load_images('clouds'),
            'spawners': load_images('tiles/spawners'),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur = 10),
            'player/run': Animation(load_images('entities/player/run'), img_dur = 4),
            'player/jump': Animation(load_images('entities/player/jump'), img_dur = 5),
            'player/slide': Animation(load_images('entities/player/slide'), img_dur = 5),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide'), img_dur = 5),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur = 10),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur = 4),
            'enemy/grace': Animation(load_images('entities/enemy/grace'), img_dur = 10),
            'portal/idle': Animation(load_images('entities/portal/idle'), img_dur = 6),
            'particle/leaf': Animation(load_images('particles/leaf'),img_dur=20, loop = False),
            'particle/particle': Animation(load_images('particles/particle'),img_dur=6, loop = False),
            'coin/idle': Animation(load_images('entities/coin/idle'),img_dur=6)

        }
       
        self.sfx = {
           'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
           'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
           'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
           'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
           'ambience': pygame.mixer.Sound('data/sfx/ambience.wav')
       }
        
        self.sfx['jump'].set_volume(0.7)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['ambience'].set_volume(0.2)
        
        #Set player values:
        self.money = 0
        self.maxHealth = 3

        #Initialise map 
        self.player = Player(self, (50, 50), (8, 15))
        self.tilemap = tileMap(self, tile_size = 16)
        # self.clouds = Clouds(self.assets['clouds'], count = 20)

        
        
    def transitionToLevel(self, newLevel):
        self.nextLevel = newLevel
        self.transition += 1
        
    def load_level(self):

        #Save game:
        self.save_game(self.saveSlot)

        self.particles = []
        self.projectiles = []
        self.coins = []
        self.sparks = []
        self.portals = []
        self.health = self.maxHealth
        #Spawn in leaf particle spawners
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep = True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        #Spawn in entities
        self.enemies = []
        self.spawner_list = [
            ('spawners', 0), #player
            ('spawners', 1), #enemy
            ('spawners', 2) #portal
        ]
        for spawner in self.tilemap.extract(self.spawner_list):
            
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0

            elif spawner['variant'] == 1:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

            elif spawner['variant'] == 2:
                self.portals.append(Portal(self, spawner['pos'], (10,10)))

        

        self.dead = False
        self.player.velocity = [0, 0]
        self.player.set_action('idle')
        self.levelDone = False
        
        self.scroll = [0, 0]
        self.screenshake = 0
        self.transition = -30


    def loadMenu(self):
        
        self.sfx['ambience'].play(-1)

        inMenu = True

        saveSlots = [0, 1, 2]
        hoverSlot = 0

        selected = (200, 100, 100)
        notSelected = (255, 255, 255)

        while inMenu:


            background = pygame.transform.scale(self.assets['menuBackground'], (self.screen_width / 2, self.screen_height / 2))
            self.display_outline.blit(background, (0, 0))

            #Displaying HUD:
            displaySlot = (hoverSlot % len(saveSlots))
            self.draw_text('Welcome to Hilbert''s Hotel!', (self.screen_width / 4, 30), self.text_font, notSelected, (0, 0))   
            self.draw_text('Please Select Your Room', (self.screen_width / 4, 60), self.text_font, notSelected, (0, 0))   
            self.draw_text('Hint: Use the arrow keys and x', (self.screen_width / 4, 150), self.text_font, notSelected, (0, 0), scale = 0.75)
            self.draw_text('Room 0', (self.screen_width / 4 - 100, 180), self.text_font, selected if displaySlot == 0 else notSelected, (0, 0))
            self.draw_text('Room 1', (self.screen_width / 4, 180), self.text_font, selected if displaySlot == 1 else notSelected, (0, 0))
            self.draw_text('Room 2', (self.screen_width / 4 + 100, 180), self.text_font, selected if displaySlot == 2 else notSelected, (0, 0))   

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        hoverSlot -= 1
                    if event.key == pygame.K_RIGHT:
                        hoverSlot += 1
                    if event.key == pygame.K_x:
                        saveSlot = hoverSlot % len(saveSlots)
                        self.run(saveSlot)

            self.display.blit(self.display_outline, (0, 0))
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(self.fps)


    def run(self, saveSlot):

        self.saveSlot = saveSlot
        self.load_game(self.saveSlot)
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.tilemap.load_tilemap('lobby')
        self.load_level()
        
        
        while self.game_running:
            
            
            self.scroll[0] += (self.player.rect().centerx - self.screen_width / 4 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.screen_height / 4 - self.scroll[1]) / 30
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            background = pygame.transform.scale(self.assets['menuBackground'], (self.screen_width / 2, self.screen_height / 2))
            self.display.blit(background, (0, 0))
            self.display_outline.fill((0, 0, 0, 0))
            
            self.screenshake = max(0, self.screenshake - 1)

            # self.clouds.update()
            # self.clouds.render(self.display, offset = self.render_scroll)

            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display_outline, offset = self.render_scroll)
            for enemy in self.enemies.copy():
                
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display_outline, offset = self.render_scroll)
                if kill:
                    self.enemies.remove(enemy)
                

            for projectile in self.projectiles:
                if projectile.update(self):
                    self.projectiles.remove(projectile)

            self.tilemap.render(self.display_outline, offset = self.render_scroll)
  
            for portal in self.portals:
                portal.update(self)
                portal.render(self.display_outline, offset = self.render_scroll)

            for rect in self.leaf_spawners:
                  if random.random() * 10000 < rect.width * rect.height:
                      pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                      self.particles.append(Particle(self, 'leaf', pos, vel = [0.1, 0.3], frame = random.randint(0, 20)))


            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display_outline, offset = self.render_scroll)
                if kill:
                    self.sparks.remove(spark)

            

            display_outline_mask = pygame.mask.from_surface(self.display_outline)
            display_outline_sillhouette = display_outline_mask.to_surface(setcolor = (0, 0, 0, 180), unsetcolor = (0, 0, 0, 0))
            for offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                self.display.blit(display_outline_sillhouette, offset)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display_outline, offset = self.render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.2
                if kill:
                    self.particles.remove(particle)  

            for coin in self.coins:
                
                if coin.update(self.tilemap, (0, 0)):
                    self.coins.remove(coin)
                coin.render(self.display_outline, offset = self.render_scroll)
                
            #Displaying HUD:
            self.draw_text('Enemies: ' + str(len(self.enemies)), (70, 30), self.text_font, (200, 200, 200), (0, 0))        
            self.draw_text('Money: ' + str(self.money), (70, 60), self.text_font, (200, 200, 200), (0, 0))        
            self.draw_text('Health: ' + str(self.health), (70, 90), self.text_font, (200, 200, 200), (0, 0))        
            
            #level transition
            if self.transition > 30:
                self.tilemap.load_tilemap(self.nextLevel, self.currentLevelSize, self.currentDifficulty)
                self.currentLevel = self.nextLevel
                self.load_level()
                self.dead = False

            elif self.transition < 31 and self.transition != 0:
                self.transition += 1
            
            
           
            if self.currentLevel == 'random' and len(self.enemies) == 0 and self.transition == 0:
                self.transitionToLevel('lobby')
                # self.currentDifficulty += 10
                # self.currentLevelSize += 10
                    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        if self.player.jump():
                            self.sfx['jump'].play()
                        self.movement[2] = True
                    if event.key == pygame.K_DOWN:
                        self.movement[3] = True
                    if event.key == pygame.K_x:
                        self.player.dash()

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
                self.draw_text('You Are Dead!', (self.player.pos[0], self.player.pos[1]), self.text_font, (200, 0, 0), self.render_scroll)
                if self.dead == 90:
                    self.transitionToLevel('lobby')
                    
                


            if self.transition:
                transition_surface = pygame.Surface(self.display_outline.get_size())
                pygame.draw.circle(transition_surface, (255, 255, 255), (self.display_outline.get_width() // 2, self.display_outline.get_height() // 2), (30 - abs(self.transition)) * (self.display_outline.get_width() / 30))
                transition_surface.set_colorkey((255, 255, 255))
                self.display_outline.blit(transition_surface, (0, 0))

            self.display.blit(self.display_outline, (0, 0))


            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2) 
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(self.fps)

    def draw_text(self, text, pos, font, colour = (0, 0, 0), offset = (0, 0), scale = 1):

        img = font.render(str(text), True, colour)
        img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
        self.display_outline.blit(img, (pos[0] - offset[0] - img.get_width() / 2, pos[1] - offset[1] - img.get_height() / 2))
        

    def save_game(self, saveSlot):

        f = open('data/saves/' + str(saveSlot), 'w')
        json.dump({'totalMoney': self.money}, f)
        
        f.close()

    def load_game(self, saveSlot):
        try:
            f = open('data/saves/' + str(saveSlot), 'r')
            saveData = json.load(f)
            f.close()

            self.money = saveData['totalMoney']
            

        except:
            f = open('data/saves/' + str(saveSlot), 'w')
            json.dump({'totalMoney': self.money}, f)
            f.close()

            


Game().loadMenu()