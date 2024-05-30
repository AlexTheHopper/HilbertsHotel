import pygame
import json
import tkinter
from tkinter import filedialog
import os
import random
import math
from perlin_noise import PerlinNoise
import matplotlib.pyplot as plt
import numpy as np


#Nine neighbor tiles:
NEIGHBOR_OFFSETS = [(x, y) for x in range(-1,2) for y in range(-1,2)]
PHYSICS_TILES = {'grass', 'stone', 'walls'}
AUTOTILE_TYPES = {'grass', 'stone', 'walls'}
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0)])): 0, #Added
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(1, 0), (-1, 0)])): 1, #added
    tuple(sorted([(0, 1)])): 1, #added
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0)])): 2, #Added
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 5,
    tuple(sorted([(0, 1)])): 1, #Added
    tuple(sorted([(0, -1)])): 5, #Added
    tuple(sorted([(0, 1), (0, -1)])): 5, #added
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(0, 1), (0, -1)])): 8,
    tuple(sorted([(0, -1)])): 8,
    tuple(sorted([(0, 1)])): 9,
    tuple(sorted([])): 9
    
    
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
                    

                    #Add tiles to minimap:
                    if self.game.minimapActive and tile['type'] in PHYSICS_TILES:
                        self.game.minimapList[loc] = [(tile['pos'][0] * self.tile_size - offset[0]) / 16, (tile['pos'][1] * self.tile_size - offset[1]) / 16]



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
    
    def load_random_tilemap(self, game, size, difficulty = 5, levelType = ''):
        ##generate random level
        self.tilemap = {}
        self.offgrid_tiles = []
      
        size = max(size, 10)
        vertexNum = int(size / 2)
        roomCount = int((size / 5) ** 1.3)
        roomSize = size * 1.5
        corridorLengthMin = int(size / 4)
        corridorLengthMax = int(size / 2)

        horBuffer = game.screen_height // (self.tile_size * 4) + 4
        vertBuffer = game.screen_width // (self.tile_size * 4) + 4
        mapHeight = int(size + 2 * vertBuffer) 
        mapWidth = int(size + 2 * horBuffer) 

        

        map = np.zeros((mapHeight, mapWidth))
        for i in range(mapHeight):
            for j in range(mapWidth):
                map[i,j] = 1

        
        roomLocations = []
        for _ in range(vertexNum):
           
            
            corridorSuccess = False
            corridorLength = random.randint(corridorLengthMin, corridorLengthMax)
            while not corridorSuccess:
                
                if len(roomLocations) == 0:
                    digPos = [random.randint(horBuffer, mapWidth - horBuffer), random.randint(vertBuffer, mapHeight - vertBuffer)]
                else:
                    digPos = random.choice(roomLocations)

            
                currentDirection = [0, 0]
                currentDirection[random.randint(0,1)] = random.choice([-1,1])
                newPos = [digPos[0] + currentDirection[0] * corridorLength, digPos[1] + currentDirection[1] * corridorLength]
                
                if newPos[0] in range(horBuffer, mapWidth - horBuffer) and newPos[1] in range(vertBuffer, mapHeight - vertBuffer):
                    roomLocations.append(newPos)
                    map[newPos[1],newPos[0]] = 0
                    while digPos != newPos:
                        map[digPos[1],digPos[0]] = 0
                        digPos[0] += currentDirection[0]
                        digPos[1] += currentDirection[1]
                    corridorSuccess = True

        for _ in range(roomCount):
            digPos = random.choice(roomLocations)
            currentRoomCount = 0

            while currentRoomCount < roomSize: 
                currentDirection = [0, 0]           
                currentDirection[random.randint(0,1)] = random.choice([-1,1])
                newPos = [digPos[0] + currentDirection[0], digPos[1] + currentDirection[1]]
                

                if newPos[0] in range(horBuffer, mapWidth - horBuffer) and newPos[1] in range(vertBuffer, mapHeight - vertBuffer):
                    map[newPos[1],newPos[0]] = 0
                    digPos = newPos
                    currentRoomCount += 1

        for i in range(mapHeight):
            for j in range(mapWidth):
                if map[i,j] == 1:
                    self.tilemap[str(i) + ';' + str(j)] = {'type': 'walls' if levelType == 'normal' else 'grass', 'variant': 1, 'pos': [i, j]}

        #placing entities:
        player_placed = False
        portal_placed = False
        noether_placed = False
        curie_placed = False
        faraday_placed = False
        difficultyProgress = 0
        potplantNum = 0
        potplantNumMax = int(size / 2)
        glowwormCount = 0
        glowwwormMax = 15

        while not player_placed or not portal_placed or difficultyProgress < difficulty:
            y = random.choice(range(horBuffer, mapWidth - horBuffer))
            x = random.choice(range(vertBuffer, mapHeight - vertBuffer))
            loc = str(x) + ';' + str(y)
            locUnder = str(x) + ';' + str(y + 1)
            locRight = str(x + 1) + ';' + str(y)
            locUnderRight = str(x + 1) + ';' + str(y + 1)
            if locUnder in self.tilemap:
                if loc not in self.tilemap and self.tilemap[locUnder]['type'] in PHYSICS_TILES:
                    #Player
                    if not player_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 0, 'pos': [x, y]}
                        player_placed = True

                    #Characters
                    elif not self.game.charactersMet['Noether'] and self.game.floor > 7 and not noether_placed and random.random() < 0.25:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 6, 'pos': [x, y]}
                        noether_placed = True
                    elif not self.game.charactersMet['Curie'] and self.game.floor > 10 and not curie_placed and random.random() < 0.25:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 7, 'pos': [x, y]}
                        curie_placed = True
                    elif not self.game.charactersMet['Planck'] and self.game.floor > 15 and not curie_placed and random.random() < 0.25:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 8, 'pos': [x, y]}
                        curie_placed = True
                    elif not self.game.charactersMet['Faraday'] and self.game.floor > 20 and not faraday_placed and random.random() < 0.25:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 2, 'pos': [x, y]}
                        faraday_placed = True
                        
                    #Portal
                    elif not portal_placed:
                        self.tilemap[loc] = {'type': 'spawnersPortal', 'variant': 0, 'pos': [x, y]}
                        portal_placed = True

                    #Potplants
                    elif random.random() < 0.5 and potplantNum < potplantNumMax:
                        randomXOffset = random.randint(-4,4)
                        to_add = {'type': 'potplants', 'variant': random.randint(0,len(self.game.assets['potplants']) - 1), 'pos': [x * self.tile_size + randomXOffset, y * self.tile_size]}
                        self.offgrid_tiles.append(to_add)
                        potplantNum += 1
                        
                    #Rocks
                    elif random.random() < 0.5 and locUnderRight in self.tilemap and locRight not in self.tilemap:
                        if self.tilemap[locUnder]['type'] in PHYSICS_TILES and self.tilemap[locUnderRight]['type'] in PHYSICS_TILES:
                            to_add = {'type': 'large_decor', 'variant': 0, 'pos': [x * self.tile_size + random.randint(-4,4), y * self.tile_size + self.tile_size / 2 + random.randint(0,6)]}
                            self.offgrid_tiles.append(to_add)

                    #Add enemies:
                    else:
                        variant, enemyDifficulty = random.choice(list(self.game.availableEnemyVariants.items()))
                       
                        self.tilemap[loc] = {'type': 'spawners', 'variant': int(variant), 'pos': [x, y]}
                        difficultyProgress += enemyDifficulty
            
            #Glowworms
            elif glowwormCount < glowwwormMax:
                to_add = {'type': 'spawners', 'variant': 5, 'pos': [self.tile_size * (x + random.random()), self.tile_size * (y + random.random())]}
                self.offgrid_tiles.append(to_add)
                glowwormCount += 1

       
        # plt.imshow(map)
        # plt.show()
        self.autotile()
    
    def save_tilemap(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()
    
    def load_tilemap(self, name = '', size = 50, difficulty = 5):

        if name in ['normal', 'three']:
            self.load_random_tilemap(self.game, size, difficulty, levelType = name)
            return()
        
    
        elif name == 'editor':
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

                    if self.tilemap[check_loc]['type'] in AUTOTILE_TYPES:# == tile['type']:
                        neighbours.add(shift)

            neighbours = tuple(sorted(neighbours))

            if (tile['type'] in AUTOTILE_TYPES) and (neighbours in AUTOTILE_MAP):
                if AUTOTILE_MAP[neighbours] == 5:
                    tile['variant'] = random.choice([10,11,12]) if random.random() < 0.01 else 5
                else:
                    tile['variant'] = AUTOTILE_MAP[neighbours]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.nearby_tiles(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects



