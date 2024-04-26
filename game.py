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
        self.running = True
        self.fps = 60
        self.screen_width = 1080
        self.screen_height = 720

        pygame.init()
        pygame.display.set_caption('Ninja')

        self.text_font = pygame.font.SysFont(None, 30)

        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode((self.screen_width,self.screen_height))
        self.display_outline = pygame.Surface((self.screen_width / 2, self.screen_height / 2), pygame.SRCALPHA)
        self.display = pygame.Surface((self.screen_width / 2, self.screen_height / 2))

        self.movement = [False, False]

        #Import assets
        #BASE_PATH = 'data/images/'
        self.assets = {
            'player': load_image('entities/player.png'),
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'background': load_image('background.png'),
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
            'particle/leaf': Animation(load_images('particles/leaf'),img_dur=20, loop = False),
            'particle/particle': Animation(load_images('particles/particle'),img_dur=6, loop = False)

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
        

        #Initialise map
        self.player = Player(self, (50, 50), (8, 15))
        self.tilemap = tileMap(self, tile_size = 16)
        self.clouds = Clouds(self.assets['clouds'], count = 20)

        self.level = 0
        self.load_level(self.level)


    def load_level(self, map_id):
        self.tilemap.load_tilemap('data/maps/' + str(map_id) + '.json')

        #Spawn in leaf particle spawners
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep = True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        #Spawn in enemies
        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        self.particles = []
        self.projectiles = []
        self.sparks = []

        self.dead = False
        self.player.velocity = [0, 0]
        self.player.set_action('idle')
        
        self.scroll = [0, 0]
        self.screenshake = 0
        self.transition = -30




    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        while self.running:
            
            self.scroll[0] += (self.player.rect().centerx - self.screen_width / 4 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.screen_height / 4 - self.scroll[1]) / 30
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            background = pygame.transform.scale(self.assets['background'], (self.screen_width / 2, self.screen_height / 2))
            self.display.blit(background, (0, 0))
            self.display_outline.fill((0, 0, 0, 0))
            
            self.screenshake = max(0, self.screenshake - 1)

            #level transition
            if not len(self.enemies):
                self.transition += 1

                if self.transition > 30:
                    # self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.level = (self.level + 1) % (len(os.listdir('data/maps')))
                    self.load_level(self.level)

            if self.transition < 0:
                self.transition += 1

            self.clouds.update()
            self.clouds.render(self.display, offset = self.render_scroll)

            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display_outline, offset = self.render_scroll)
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display_outline, offset = self.render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            self.tilemap.render(self.display_outline, offset = self.render_scroll)


            #projectiles are like:
            #[[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] == 1
                img = self.assets['projectile']
                self.display_outline.blit(img, (projectile[0][0] - img.get_width() / 2 - self.render_scroll[0], projectile[0][1] - img.get_height() / 2 - self.render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for _ in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                
                elif projectile[2] > 500:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        if not self.dead:
                            self.projectiles.remove(projectile)
                            self.dead += 1
                            self.screenshake = max(50, self.screenshake)
                            self.sfx['hit'].play()

                            for _ in range(30):
                                angle = random.random() * math.pi * 2
                                speed = random.random() * 5
                                self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                                self.particles.append(Particle(self, 'particle', self.player.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
                        

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
                    if event.key == pygame.K_x:
                        self.player.dash()

                    if event.key == pygame.K_r:
                        self.load_level(self.level)
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            if self.dead:
                self.dead += 1
                self.draw_text('You Are Dead!', (self.player.pos[0], self.player.pos[1]), self.text_font, (200, 0, 0), self.render_scroll)
                if self.dead >= 90:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 120:
                    self.level = 0
                    self.load_level(self.level)


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

    def draw_text(self, text, pos, font, colour = (0, 0, 0), offset = (0, 0)):

        img = font.render(str(text), True, colour)
        self.display_outline.blit(img, (pos[0] - offset[0] - img.get_width() / 2, pos[1] - offset[1] - img.get_height() / 2))


Game().run()