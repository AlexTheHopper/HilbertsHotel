import pygame
import json
import tkinter
from tkinter import filedialog
import os
import random
import math
from perlin_noise import PerlinNoise


#Nine neighbor tiles:
NEIGHBOR_OFFSETS = [(x, y) for x in range(-1,2) for y in range(-1,2)]
PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8
    
}

class tileMap:
    def __init__(self, game, tile_size = 16):
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        self.game = game

    def render(self, surface, offset = (0, 0)):

        #Render non-grid assets
        for tile in self.offgrid_tiles:
            asset = self.game.assets[tile['type']][tile['variant']]
            position = (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1])
            surface.blit(asset, position)

        #Render tiles
        for x in range(offset[0] // self.tile_size, (offset[0] + surface.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surface.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]

                    asset = self.game.assets[tile['type']][tile['variant']]
                    position = (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1])
                    surface.blit(asset, position)

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())

                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in self.tilemap.copy():
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tilesize
                matches[-1]['pos'][1] *= self.tilesize

                if not keep:
                    del self.tilemap[loc]
        return matches
            
    def nearby_tiles(self, pixPos):
        potentialTiles = []
        tile_pos = (int(pixPos[0] // self.tile_size), int(pixPos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_pos[0] + offset[0]) + ';' + str(tile_pos[1] + offset[1])

            if check_loc in self.tilemap:
                potentialTiles.append(self.tilemap[check_loc])
        return potentialTiles
    
    def load_random_tilemap(self,game,  radius, difficulty = 5):
        ##generate random level
        #needs to return tilemap (and maybe offgrid tiles)
        self.tilemap = {}
        player_placed = False
        difficultyProgress = 0

         
        mapWidth = int(1 + radius * 2 + (game.screen_width // self.tile_size) / 2)
        mapHeight = int(1 + radius * 2 + (game.screen_height // self.tile_size) / 2)
        
   

        #perlin map:
        mapSeed = random.randint(0,10000)
        # mapSeed = 3
        print('seed',mapSeed)
        noise = PerlinNoise(octaves=2, seed=mapSeed)
        for i in range(mapWidth):
            for j in range(mapHeight):

                distToCenter = math.sqrt((i - mapWidth / 2)**2 + (j - mapHeight / 2)**2)

                if distToCenter > radius or noise([i/radius, j/radius]) < 0:
                    self.tilemap[str(i) + ';' + str(j)] = {'type': 'stone', 'variant': 0, 'pos': [i, j]}

        #placing entities:
        while not player_placed or difficultyProgress < difficulty:
            x = int(random.randint(-int(radius), int(radius)) + mapWidth / 2)
            y = int(random.randint(-int(radius), int(radius)) + mapHeight / 2)
            loc = str(x) + ';' + str(y)
            locUnder = str(x) + ';' + str(y + 1)
            distToCenter = math.sqrt((x - mapWidth / 2)**2 + (y - mapHeight / 2)**2)
           
    
            if loc not in self.tilemap and locUnder in self.tilemap:
                if not player_placed:
                    self.tilemap[loc] = {'type': 'spawners', 'variant': 0, 'pos': [x, y]}
                    
                   
                    player_placed = True
                else:
                    self.tilemap[loc] = {'type': 'spawners', 'variant': 1, 'pos': [x, y]}
                    difficultyProgress += 1


        self.autotile()

    def save_tilemap(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()
    
    def load_tilemap(self, name = '', size = 15, difficulty = 5):

        if name == 'random':
            self.load_random_tilemap(self.game, size, difficulty)
            return()
    
        elif name == '':
            root = tkinter.Tk()
            root.withdraw()

            currdir = os.getcwd()
            filepath = filedialog.askopenfilename(initialdir=currdir,
                                            title="Open map",
                                            filetypes= (("JSON Files","*.json*"),
                                                        ("All Files","*.*")))
        else:
            filepath = 'data/maps/' + str(name) + '.json'

        f = open(filepath, 'r')
        map_data = json.load(f)
        f.close()
        
        self.tilemap = map_data['tilemap']
        self.tilesize = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def solid_check(self, pos):
        tile_loc = str(int(pos[0]) // self.tile_size) + ';' + str(int(pos[1]) // self.tile_size)
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]

            neighbours = set()
            for shift in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                check_loc  = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:

                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbours.add(shift)

            neighbours = tuple(sorted(neighbours))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbours in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbours]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.nearby_tiles(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects

