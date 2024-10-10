import pygame
import sys
from scripts.utilities import *
from scripts.tilemap import *

RENDER_SCALE = 2.0

class Editor:
    def __init__(self):
        self.running = True
        self.fps = 60
        self.screen_width = 1080
        self.screen_height = 720

        pygame.init()
        pygame.display.set_caption('Hilbert\'s Hotel_Editor')

        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.screen_width,self.screen_height))
        self.display = pygame.Surface((self.screen_width / 2, self.screen_height / 2))


        #BASE_PATH = 'data/images/'
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'stone': load_images('tiles/stone'),
            'spooky': load_images('tiles/spooky'),
            'rubiks': load_images('tiles/rubiks'),
            'aussie': load_images('tiles/aussie'),
            'space': load_images('tiles/space'),
            'potplants': load_images('tiles/potplants'),
            'normal': load_images('tiles/normal'),
            'cracked': load_images('tiles/cracked'),
            'spawners': load_images('tiles/spawners'),
            'spawnersPortal': load_images('tiles/spawnersPortal')
        }

        self.characters_met = {
        'Hilbert': True,
        'Noether': False,
        'Curie': False,
        'Planck': False,
        'Faraday': True,
        'Lorenz': False
         }
        
        self.floors = {
        'normal': 100,
        'grass': 100}

        self.available_enemy_variants = {
        'normal': [3],
        'normalWeights': [2],
        'grass': [3, 9],
        'grassWeights': [1, 0.5]
    }
        
        
        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, tile_size = 16)

        try:
            self.tilemap.load_tilemap(name = 'editor')
        except:
            print("ERROR FETCHING MAP")
        self.savename = 'map.json'
        
        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False

        self.shift = False

        self.ongrid = True

        self.floodfill = False
        self.floodfillLocs = [[0, 0], [0, 0]]
        self.minimapActive = False


    def run(self):
        while self.running:

            self.display.fill((0, 0, 0))
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 4
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 4
            

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            self.tilemap.render(self.display, offset = render_scroll)


            current_tile_image = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_image.set_alpha(100)
            
            mouse_pos = pygame.mouse.get_pos()
            mouse_pos = (mouse_pos[0] / RENDER_SCALE, mouse_pos[1] / RENDER_SCALE)
            tile_pos = (int((mouse_pos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mouse_pos[1] + self.scroll[1]) // self.tilemap.tile_size))

            #Work out if ongrid or not
            #Display where tile will go
            if self.ongrid:
                self.display.blit(current_tile_image, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_image, mouse_pos)


            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}

                if self.floodfill:
                    
                    self.floodfill = False

                    if self.floodfillLocs == [[0, 0], [0, 0]]:
                        self.floodfillLocs[0] = tile_pos
                        print(self.floodfillLocs)
                    elif self.floodfillLocs[0] != [0, 0] and self.floodfillLocs[1] == [0, 0]:
                        self.floodfillLocs[1] = tile_pos
                        print(self.floodfillLocs)
                    

                        x1 = min(self.floodfillLocs[0][0], self.floodfillLocs[1][0])
                        x2 = max(self.floodfillLocs[0][0], self.floodfillLocs[1][0])
                        y1 = min(self.floodfillLocs[0][1], self.floodfillLocs[1][1])
                        y2 = max(self.floodfillLocs[0][1], self.floodfillLocs[1][1])
                        print(x1,x2,y1,y2)

                        for i in range(x1,x2+1):
                            for j in range(y1,y2+1):
                                self.tilemap.tilemap[str(i) + ';' + str(j)] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': (i,j)}

                        self.floodfillLocs = [[0, 0], [0, 0]]
                        
                
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]

                #Remove off-grid tiles
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mouse_pos):
                        self.tilemap.offgrid_tiles.remove(tile)

            for index, variant_i in enumerate(range(len(self.assets[self.tile_list[self.tile_group]]))):
                choice_tile = self.assets[self.tile_list[self.tile_group]][variant_i].copy()
                choice_tile.set_alpha(100)
                if variant_i == self.tile_variant:
                    choice_tile.set_alpha(200)
                self.display.blit(choice_tile, ((10 + 20*(variant_i % 20)), 10 + 30 * (math.floor(index / 20))))



            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            to_add = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': (mouse_pos[0] + self.scroll[0], mouse_pos[1] + self.scroll[1])}
                            self.tilemap.offgrid_tiles.append(to_add)
                    if event.button == 3:
                        self.right_clicking = True

                    else:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = 0
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                        if event.button == 5:
                            self.tile_variant = 0
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile(windows = False)
                    if event.key == pygame.K_r:
                        self.tilemap.load_random_tilemap(20)
                    if event.key == pygame.K_o:
                        self.tilemap.save_tilemap(self.savename)
                    if event.key == pygame.K_f:
                        self.floodfill = True
                    if event.key == pygame.K_n:
                        for tile in self.tilemap.tilemap.keys():
                            print(self.tilemap.tilemap[tile]['type'])
                            if self.tilemap.tilemap[tile]['type'] == 'walls':
                                self.tilemap.tilemap[tile]['type'] = 'normal'

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False

                    if event.key == pygame.K_LSHIFT:
                        self.shift = False


            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(self.fps)

Editor().run()