import pygame
import json
import tkinter
from tkinter import filedialog
import os
import random
import math
import matplotlib.pyplot as plt
import numpy as np

#Nine neighbor tiles:
NEIGHBOR_OFFSETS = [(x, y) for x in range(-1,2) for y in range(-1,2)]
NEIGHBOR_OFFSETS_EXTRA = [(x, y) for x in range(-2,3) for y in range(-2,3)]
PHYSICS_TILES = {'grass', 'stone', 'normal', 'spooky', 'rubiks', 'aussie', 'space', 'cracked'}
AUTOTILE_TYPES = {'grass', 'stone', 'normal', 'spooky', 'rubiks', 'aussie', 'space', 'cracked'}

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(1, 0), (-1, 0)])): 1,
    tuple(sorted([(0, 1)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 5,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(0, 1), (0, -1)])): 5,
    tuple(sorted([(0, -1)])): 5,
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
        self.mapSize = 50
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


    def extract(self, search, keep=False):
        matches = []
        if isinstance(search, list):
            for tile in self.offgrid_tiles.copy():
                
                if (tile['type'], tile['variant']) in search:
                    matches.append(tile.copy())

                    if not keep:
                        self.offgrid_tiles.remove(tile)

            for loc in self.tilemap.copy():
                tile = self.tilemap[loc]
                if (tile['type'], tile['variant']) in search:
                    matches.append(tile.copy())
                    matches[-1]['pos'] = matches[-1]['pos'].copy()
                    matches[-1]['pos'][0] *= self.tilesize
                    matches[-1]['pos'][1] *= self.tilesize

                    if not keep:
                        del self.tilemap[loc]
        elif isinstance(search, str):
            for tile in self.offgrid_tiles.copy():
                
                if tile['type'] == search:
                    matches.append(tile.copy())

                    if not keep:
                        self.offgrid_tiles.remove(tile)

            for loc in self.tilemap.copy():
                tile = self.tilemap[loc]
                if tile['type'] == search:
                    matches.append(tile.copy())
                    matches[-1]['pos'] = matches[-1]['pos'].copy()
                    matches[-1]['pos'][0] *= self.tilesize
                    matches[-1]['pos'][1] *= self.tilesize

                    if not keep:
                        del self.tilemap[loc]
        
        return matches


    def nearby_tiles(self, pixPos, isBoss = False):
        potentialTiles = []
        tile_pos = (int(pixPos[0] // self.tile_size), int(pixPos[1] // self.tile_size))
        for offset in (NEIGHBOR_OFFSETS if not isBoss else NEIGHBOR_OFFSETS_EXTRA):
            check_loc = str(tile_pos[0] + offset[0]) + ';' + str(tile_pos[1] + offset[1])

            if check_loc in self.tilemap:
                potentialTiles.append(self.tilemap[check_loc])
        return potentialTiles
    

    def load_random_tilemap(self, size, enemyCountMax = 5, levelType = 'normal'):
        if levelType == 'infinite':
            levelType = self.game.getRandomLevel()
        self.game.levelType = levelType

        self.tilemap = self.generateTiles(size, levelType)
        self.offgrid_tiles = self.populateMap(size, enemyCountMax, levelType)
        self.autotile()


    def generateTiles(self, size, levelType):
        tilemap = {}
      
        size = max(size, 10)
        vertexNum = int(size / 2)
        roomCount = int((size / 5) ** 1.3)
        roomSize = size * 1
        corridorLengthMin = 5
        corridorLengthMax = int(size / 2)

        #Floor specific alterations:
        if levelType == 'aussie':
            size *= 1.5
            roomSize *= 2
            roomCount *= 2

        buffer = 18
        self.mapSize = int(size + 2 * buffer)

        map = np.zeros((self.mapSize, self.mapSize))
        for i in range(self.mapSize):
            for j in range(self.mapSize):
                map[i,j] = 1

        roomLocations = []
        for _ in range(vertexNum):
           
            corridorSuccess = False
            corridorLength = random.randint(corridorLengthMin, corridorLengthMax)
            while not corridorSuccess:
                
                if len(roomLocations) == 0:
                    digPos = [random.randint(buffer, self.mapSize - buffer), random.randint(buffer, self.mapSize - buffer)]
                else:
                    digPos = random.choice(roomLocations)

                currentDirection = [0, 0]
                currentDirection[random.randint(0,1)] = random.choice([-1,1])
                newPos = [digPos[0] + currentDirection[0] * corridorLength, digPos[1] + currentDirection[1] * corridorLength]
                
                if newPos[0] in range(buffer, self.mapSize - buffer) and newPos[1] in range(buffer, self.mapSize - buffer):
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
                horiVert = random.choice([0, 1]) 
                currentDirection[horiVert] = random.choice([-1,1])
                newPos = [digPos[0] + currentDirection[0], digPos[1] + currentDirection[1]]
                
                if newPos[0] in range(buffer, self.mapSize - buffer) and newPos[1] in range(buffer, self.mapSize - buffer):
                    map[newPos[1],newPos[0]] = 0
                    digPos = newPos
                    currentRoomCount += 1

        for i in range(self.mapSize):
            for j in range(self.mapSize):
                if map[i,j] == 1:
                    tilemap[str(i) + ';' + str(j)] = {'type': levelType, 'variant': 1, 'pos': [i, j]}
        return tilemap
    

    def populateMap(self, size, enemyCountMax, levelType):
        offgrid_tiles = []
        buffer = 18

        player_placed = False
        portal_placed = False
        infinite_portal_placed = False if self.game.infiniteModeActive else True
        noether_placed = False
        curie_placed = False
        planck_placed = False
        lorenz_placed = False
        franklin_placed = False
        rubik_placed = False
        cantor_placed = False
        melatos_placed = False
        enemyCount = 0
        attemptCounter = 0

        while (not player_placed or not portal_placed or enemyCount < enemyCountMax or not infinite_portal_placed) and attemptCounter < 5000:
            attemptCounter += 1

            y = random.choice(range(buffer, self.mapSize - buffer))
            x = random.choice(range(buffer, self.mapSize - buffer))
            loc = str(x) + ';' + str(y)

            #Important things:
            if not self.isTile([[x, y]]):
                if self.isPhysicsTile([[x, y+1]]):

                    #Player
                    if not player_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 0, 'pos': [x, y]}
                        player_placed = True

                    #Portal
                    elif not portal_placed:
                        self.tilemap[loc] = {'type': 'spawnersPortal', 'variant': 0, 'pos': [x, y]}
                        portal_placed = True
                    
                    #Infinite Portal
                    elif not infinite_portal_placed and self.game.infiniteModeActive:
                        infinite_portal_placed = True

                        self.tilemap[loc] = {'type': 'spawnersPortal', 'variant': 5, 'pos': [x, y]}
                        

                    #Characters
                    elif not self.game.charactersMet['Noether'] and self.game.floors[levelType] > 7 and levelType == 'normal' and not noether_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 6, 'pos': [x, y]}
                        noether_placed = True
                    elif not self.game.charactersMet['Curie'] and self.game.floors[levelType] > 10 and levelType == 'normal' and not curie_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 7, 'pos': [x, y]}
                        curie_placed = True
                    elif not self.game.charactersMet['Planck'] and self.game.floors[levelType] > 13 and levelType == 'normal' and not planck_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 8, 'pos': [x, y]}
                        planck_placed = True
                    elif not self.game.charactersMet['Lorenz'] and self.game.floors[levelType] > 17 and levelType == 'normal' and not lorenz_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 11, 'pos': [x, y]}
                        lorenz_placed = True
                    elif not self.game.charactersMet['Franklin'] and self.game.floors[levelType] > 10 and levelType == 'spooky' and not franklin_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 14, 'pos': [x, y]}
                        franklin_placed = True
                    elif not self.game.charactersMet['Rubik'] and self.game.floors[levelType] > 1 and levelType == 'rubiks' and not rubik_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 16, 'pos': [x, y]}
                        rubik_placed = True
                    elif not self.game.charactersMet['Melatos'] and self.game.floors[levelType] > 5 and levelType == 'aussie' and not melatos_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 21, 'pos': [x, y]}
                        melatos_placed = True
                    elif not self.game.charactersMet['Cantor'] and self.game.floors['infinite'] > 3 and not cantor_placed:
                        self.tilemap[loc] = {'type': 'spawners', 'variant': 17, 'pos': [x, y]}
                        cantor_placed = True
                    
                           
                    #Add enemies:
                    else:
                        variant = random.choices(self.game.availableEnemyVariants[levelType], self.game.availableEnemyVariants[levelType + 'Weights'], k = 1)[0]
                        self.tilemap[loc] = {'type': 'spawners', 'variant': int(variant), 'pos': [x, y]}
                        enemyCount += 1

        #Decorations
        decoNum = 0
        glowwormCount = 0
        glowwwormMax = 15
        decoNumMax = math.ceil(size / 5 * self.game.floorSpecifics[levelType]['decorationMod'])
        decorationList = self.game.floorSpecifics[levelType]['decorations']
        weights = [deco[2] for deco in decorationList]
        attemptCounter = 0

        while (decoNum < decoNumMax) and attemptCounter < 5000:
            attemptCounter += 1      
            x = random.choice(range(buffer, self.mapSize - buffer))
            y = random.choice(range(buffer, self.mapSize - buffer))
            loc = str(x) + ';' + str(y)

            #Add random decorations
            potentialDecoration = random.choices(decorationList, weights, k = 1)[0]
            if not self.isPhysicsTile([[x, y]], offsets = potentialDecoration[3]):
                if self.isPhysicsTile([[x, y]], offsets = potentialDecoration[4][1:], mode = potentialDecoration[4][0]):

                    decoOffsetx = random.choice(potentialDecoration[5][0])
                    decoOffsety = random.choice(potentialDecoration[5][1])
                    add_deco = {'type': potentialDecoration[0], 'variant': random.choice(potentialDecoration[1]), 'pos': [x * self.tile_size + decoOffsetx, y * self.tile_size + decoOffsety]}
                    offgrid_tiles.append(add_deco)
                    decoNum += 1                        
            
            #Glowworms
            if glowwormCount < glowwwormMax:
                to_add = {'type': 'spawners', 'variant': 5, 'pos': [self.tile_size * (x + random.random()), self.tile_size * (y + random.random())]}
                offgrid_tiles.append(to_add)
                glowwormCount += 1

        return offgrid_tiles
    

    def isPhysicsTile(self, poss, offsets = [[0, 0]], mode = 'any'):
        for pos in poss:
            for offset in offsets:
                loc = str(pos[0] + offset[0]) + ';' + str(pos[1] + offset[1])

                if mode == 'all':
                    if loc in self.tilemap:
                        if self.tilemap[loc]['type'] not in PHYSICS_TILES:
                            return False   
   
                    else:
                        return False
                    
                #also counts portal as physics tile to not block portal.
                elif mode == 'any':
                    if loc in self.tilemap:
                        if self.tilemap[loc]['type'] in PHYSICS_TILES or self.tilemap[loc]['type'] == 'spawnersPortal':
                            return True
                        
        return True if mode == 'all' else False


    def isTile(self, poss, offsets = [[0, 0]], mode = 'any'):
        for pos in poss:
            for offset in offsets:
                loc = str(pos[0] + offset[0]) + ';' + str(pos[1] + offset[1])

                if mode == 'all':
                    if loc in self.tilemap:
                        return False   
   
                    else:
                        return False
                    
                elif mode == 'any':
                    if loc in self.tilemap:
                        return True
        return True if mode == 'all' else False


    def save_tilemap(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()
    

    def load_tilemap(self, name = '', size = 50, enemyCountMax = 5):
        #Floors levels:
        if name in self.game.floors.keys():
            #Normal levels:
            if (self.game.floors[name] + (1 if name == 'infinite' else 0)) % 10 != 0:
                #All levels scale with floor:
                enemyCountMax = int(self.game.floors[name])
                size = int(5 * np.log(enemyCountMax ** 2) + 13 + enemyCountMax / 4)
                if name == 'infinite':
                    enemyCountMax *= 2
                    size += 5
                    
                self.load_random_tilemap(size, enemyCountMax, levelType = name)
                return()

            #Boss levels:
            else:
                filepath = 'data/maps/' + str(name) + 'Boss.json'
       
        #Only for level editor
        elif name == 'editor':
            root = tkinter.Tk()
            root.withdraw()

            currdir = os.getcwd()
            filepath = filedialog.askopenfilename(initialdir=currdir,
                                            title="Open map",
                                            filetypes= (("JSON Files","*.json*"),
                                                        ("All Files","*.*")))
            
        #Otherwise try to open file eg for lobby.
        else:
            filepath = 'data/maps/' + str(name) + '.json'

        f = open(filepath, 'r')
        map_data = json.load(f)
        f.close()
        
        self.tilemap = map_data['tilemap']
        self.tilesize = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']


    def solid_check(self, pos, returnValue = ''):
        tile_loc = str(int(pos[0]) // self.tile_size) + ';' + str(int(pos[1]) // self.tile_size)
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                if returnValue == 'pos':
                    return tuple(self.tilemap[tile_loc]['pos'])
                elif returnValue == 'bool':
                    return True
                else:   
                    return self.tilemap[tile_loc]
            elif returnValue == 'bool':
                return False
        elif returnValue == 'bool':
                return False


    def autotile(self, windows = True):
        for loc in self.tilemap:
            tile = self.tilemap[loc]

            #Rubik's level randomising
            if tile['type'] == 'rubiks':
                tile['variant'] = random.choice(range(0,6))
                continue

            #Tunnel correction
            if tile['type'] == 'cracked':
                tile['variant'] = 4
                for int, shift in enumerate([(0, 1), (0, -1), (1, 0), (-1, 0)]):
                    check_loc  = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                    if check_loc not in self.tilemap:
                        tile['variant'] = int
                        continue
                continue

            neighbours = set()
            for shift in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                check_loc  = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:

                    if self.tilemap[check_loc]['type'] in AUTOTILE_TYPES:
                        neighbours.add(shift)

            neighbours = tuple(sorted(neighbours))

            if (tile['type'] in AUTOTILE_TYPES) and (neighbours in AUTOTILE_MAP):
                if AUTOTILE_MAP[neighbours] == 5 and windows == True:

                    windowChoice = random.choice(range(10, len(self.game.assets[tile['type']])))
                    tile['variant'] = windowChoice if random.random() < 0.01 else 5

                    if tile['type'] == 'space' and random.random() < 0.1:
                        tile['variant'] = random.choice(range(13, len(self.game.assets[tile['type']])))

                    elif tile['type'] == 'spooky' and random.random() < 0.005:
                        self.offgrid_tiles.append({'type': 'spawners', 'variant': 24, 'pos': [tile['pos'][0] * self.tilesize, tile['pos'][1] * self.tilesize]})
                        tile['variant'] = random.choice(range(13, len(self.game.assets[tile['type']])))

                else:
                    tile['variant'] = AUTOTILE_MAP[neighbours]

            


    def physics_rects_around(self, pos, isBoss = False):
        rects = []
        for tile in self.nearby_tiles(pos, isBoss = isBoss):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects



