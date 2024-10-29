"""
Tilemap module for Hilbert's Hotel.
Manages all tilemap behaviour, generation and rendering.
"""

import json
import tkinter
from tkinter import filedialog
import os
import random
import math
import numpy as np
import pygame
import scripts.clouds as _clouds

# Nine neighbor tiles:
NEIGHBOR_OFFSETS = [(x, y) for x in range(-1, 2) for y in range(-1, 2)]
NEIGHBOR_OFFSETS_EXTRA = [(x, y) for x in range(-2, 3) for y in range(-2, 3)]
PHYSICS_TILES = {'grass', 'stone', 'normal', 'spooky',
                 'rubiks', 'aussie', 'space', 'heaven', 'hell', 'cracked'}
AUTOTILE_TYPES = {'grass', 'stone', 'normal', 'spooky',
                  'rubiks', 'aussie', 'space', 'heaven', 'hell', 'cracked'}

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
    tuple(sorted([(0, 1)])): 9,
    tuple(sorted([(0, -1)])): 10,
    tuple(sorted([])): 11,
}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        self.map_size = 80
        self.game = game
        self.autotile_count = len(set(AUTOTILE_MAP.values()))

    def render(self, surface, offset=(0, 0)):
        # Render non-grid assets
        for tile in self.offgrid_tiles:
            asset = self.game.assets[tile['type']][tile['variant']]
            position = (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1])
            surface.blit(asset, position)

        # Render tiles
        for x in range(offset[0] // self.tile_size, (offset[0] + surface.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surface.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]

                    asset = self.game.assets[tile['type']][tile['variant']]
                    position = (tile['pos'][0] * self.tile_size - offset[0],
                                tile['pos'][1] * self.tile_size - offset[1])
                    surface.blit(asset, position)

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

    def nearby_tiles(self, pix_pos, is_boss=False):
        potential_tiles = []
        tile_pos = (int(pix_pos[0] // self.tile_size),
                    int(pix_pos[1] // self.tile_size))
        for offset in (NEIGHBOR_OFFSETS if not is_boss else NEIGHBOR_OFFSETS_EXTRA):
            check_loc = str(tile_pos[0] + offset[0]) + \
                ';' + str(tile_pos[1] + offset[1])

            if check_loc in self.tilemap:
                potential_tiles.append(self.tilemap[check_loc])
        return potential_tiles

    def load_random_tilemap(self, size, enemy_count_max=5, level_type='normal', level_style=''):
        if level_type != 'heaven_hell':
            level_style = level_type
            self.game.level_style = level_style

        if level_type == 'infinite':
            level_style = self.game.get_random_level()
            self.game.level_style = level_style

        self.game.level_type = level_type

        self.tilemap = self.generate_tiles(size, level_style)
        self.offgrid_tiles = self.populate_map(size, enemy_count_max, level_type, level_style)
        self.autotile()

    def generate_tiles(self, size, level_type):
        tilemap = {}

        size = max(size, 10)
        vertex_num = int(size / 2)
        room_count = int((size / 5) ** 1.3)
        room_size = size * 1
        corridor_length_min = 5
        corridor_length_max = int(size / 2)

        # Floor specific alterations:
        if level_type == 'aussie':
            size *= 1.5
            room_size *= 2
            room_count *= 2

        buffer = 22
        self.map_size = int(size + 2 * buffer)

        map = np.zeros((self.map_size, self.map_size))
        for i in range(self.map_size):
            for j in range(self.map_size):
                map[i, j] = 1

        room_locations = []
        for _ in range(vertex_num):

            corridor_success = False
            corridor_length = random.randint(
                corridor_length_min, corridor_length_max)
            while not corridor_success:

                if len(room_locations) == 0:
                    dig_pos = [random.randint(
                        buffer, self.map_size - buffer), random.randint(buffer, self.map_size - buffer)]
                else:
                    dig_pos = random.choice(room_locations)

                current_direction = [0, 0]
                current_direction[random.randint(0, 1)] = random.choice([-1, 1])
                new_pos = [dig_pos[0] + current_direction[0] * corridor_length,
                          dig_pos[1] + current_direction[1] * corridor_length]

                if new_pos[0] in range(buffer, self.map_size - buffer) and new_pos[1] in range(buffer, self.map_size - buffer):
                    room_locations.append(new_pos)
                    map[new_pos[1], new_pos[0]] = 0
                    while dig_pos != new_pos:
                        map[dig_pos[1], dig_pos[0]] = 0
                        dig_pos[0] += current_direction[0]
                        dig_pos[1] += current_direction[1]
                    corridor_success = True

        for _ in range(room_count):
            dig_pos = random.choice(room_locations)
            current_room_count = 0

            while current_room_count < room_size:
                current_direction = [0, 0]
                hori_vert = random.choice([0, 1])
                current_direction[hori_vert] = random.choice([-1, 1])
                new_pos = [dig_pos[0] + current_direction[0],
                          dig_pos[1] + current_direction[1]]

                if new_pos[0] in range(buffer, self.map_size - buffer) and new_pos[1] in range(buffer, self.map_size - buffer):
                    map[new_pos[1], new_pos[0]] = 0
                    dig_pos = new_pos
                    current_room_count += 1

        for i in range(self.map_size):
            for j in range(self.map_size):
                if map[i, j] == 1:
                    tilemap[str(i) + ';' + str(j)
                            ] = {'type': level_type, 'variant': 1, 'pos': [i, j]}
        return tilemap

    def populate_map(self, size, enemy_count_max, level_type, level_style):
        offgrid_tiles = []
        buffer = 18

        player_placed = False
        portal_placed = False
        infinite_portal_placed = False if self.game.infinite_mode_active else True
        noether_placed = False
        curie_placed = False
        planck_placed = False
        lorenz_placed = False
        franklin_placed = False
        rubik_placed = False
        cantor_placed = False
        melatos_placed = False
        enemy_count = 0
        attempt_counter = 0

        while (not player_placed or not portal_placed or enemy_count < enemy_count_max or not infinite_portal_placed) and attempt_counter < 5000:
            attempt_counter += 1

            y = random.choice(range(buffer, self.map_size - buffer))
            x = random.choice(range(buffer, self.map_size - buffer))
            loc = str(x) + ';' + str(y)

            # Important things:
            if not self.is_tile([[x, y]]):
                if self.is_physics_tile([[x, y+1]]):

                    # Player
                    if not player_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 0, 'pos': [x, y]}
                        player_placed = True

                    # Portal
                    elif not portal_placed:
                        self.tilemap[loc] = {
                            'type': 'spawnersPortal', 'variant': 0, 'pos': [x, y]}
                        portal_placed = True

                    # Infinite Portal
                    elif not infinite_portal_placed and self.game.infinite_mode_active:
                        infinite_portal_placed = True

                        self.tilemap[loc] = {
                            'type': 'spawnersPortal', 'variant': 5, 'pos': [x, y]}

                    # Characters
                    elif not self.game.characters_met['Noether'] and self.game.floors[level_type] > 7 and level_type == 'normal' and not noether_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 6, 'pos': [x, y]}
                        noether_placed = True
                    elif not self.game.characters_met['Curie'] and self.game.floors[level_type] > 10 and level_type == 'normal' and not curie_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 7, 'pos': [x, y]}
                        curie_placed = True
                    elif not self.game.characters_met['Planck'] and self.game.floors[level_type] > 13 and level_type == 'normal' and not planck_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 8, 'pos': [x, y]}
                        planck_placed = True
                    elif not self.game.characters_met['Lorenz'] and self.game.floors[level_type] > 17 and level_type == 'normal' and not lorenz_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 11, 'pos': [x, y]}
                        lorenz_placed = True
                    elif not self.game.characters_met['Franklin'] and self.game.floors[level_type] > 6 and level_type == 'spooky' and not franklin_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 14, 'pos': [x, y]}
                        franklin_placed = True
                    elif not self.game.characters_met['Rubik'] and self.game.floors[level_type] > 1 and level_type == 'rubiks' and not rubik_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 16, 'pos': [x, y]}
                        rubik_placed = True
                    elif not self.game.characters_met['Melatos'] and self.game.floors[level_type] > 3 and level_type == 'aussie' and not melatos_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 21, 'pos': [x, y]}
                        melatos_placed = True
                    elif not self.game.characters_met['Cantor'] and self.game.floors['infinite'] > 3 and not cantor_placed:
                        self.tilemap[loc] = {
                            'type': 'spawners', 'variant': 17, 'pos': [x, y]}
                        cantor_placed = True

                    # Add enemies:
                    else:
                        variant = random.choices(self.game.available_enemy_variants[level_style], self.game.available_enemy_variants[level_style + 'Weights'], k=1)[0]
                        self.tilemap[loc] = {'type': 'spawners', 'variant': int(variant), 'pos': [x, y]}
                        enemy_count += 1

        # Decorations
        deco_num = 0
        glowworm_count = 0
        glowwom_max = 15
        deco_num_max = math.ceil(
            size / 5 * self.game.floor_specifics[level_style]['decorationMod'])
        decoration_list = self.game.floor_specifics[level_style]['decorations']
        weights = [deco[2] for deco in decoration_list]
        attempt_counter = 0

        while (deco_num < deco_num_max) and attempt_counter < 5000:
            attempt_counter += 1
            x = random.choice(range(buffer, self.map_size - buffer))
            y = random.choice(range(buffer, self.map_size - buffer))
            loc = str(x) + ';' + str(y)

            # Add random decorations
            potential_decoration = random.choices(
                decoration_list, weights, k=1)[0]
            if not self.is_physics_tile([[x, y]], offsets=potential_decoration[3]):
                if self.is_physics_tile([[x, y]], offsets=potential_decoration[4][1:], mode=potential_decoration[4][0]):

                    deco_offset_x = random.choice(potential_decoration[5][0])
                    deco_offset_y = random.choice(potential_decoration[5][1])
                    add_deco = {'type': potential_decoration[0], 'variant': random.choice(
                        potential_decoration[1]), 'pos': [x * self.tile_size + deco_offset_x, y * self.tile_size + deco_offset_y]}
                    offgrid_tiles.append(add_deco)
                    deco_num += 1

            # Glowworms
            if glowworm_count < glowwom_max:
                to_add = {'type': 'spawners', 'variant': 5, 'pos': [
                    self.tile_size * (x + random.random()), self.tile_size * (y + random.random())]}
                offgrid_tiles.append(to_add)
                glowworm_count += 1

        return offgrid_tiles

    def is_physics_tile(self, poss, offsets=[[0, 0]], mode='any'):
        for pos in poss:
            for offset in offsets:
                loc = str(pos[0] + offset[0]) + ';' + str(pos[1] + offset[1])

                if mode == 'all':
                    if loc in self.tilemap:
                        if self.tilemap[loc]['type'] not in PHYSICS_TILES:
                            return False

                    else:
                        return False

                # also counts portal as physics tile to not block portal.
                elif mode == 'any':
                    if loc in self.tilemap:
                        if self.tilemap[loc]['type'] in PHYSICS_TILES or self.tilemap[loc]['type'] == 'spawnersPortal':
                            return True

        return True if mode == 'all' else False

    def is_tile(self, poss, offsets=[[0, 0]], mode='any'):
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
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size,
                  'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load_tilemap(self, name=''):
        # Floors levels:
        self.game.heaven_hell = ''
        if name in self.game.floors.keys() and name != 'final':
            specific_name = name
            if name == 'heaven_hell':
                specific_name = 'hell' if self.game.floors[name] % 2 == 0 else 'heaven'
                self.game.heaven_hell = specific_name
                self.game.level_style = specific_name

            # Boss levels:
            actual_floor = (
                self.game.floors[name] + (1 if name == 'infinite' else 0))
            if actual_floor % self.game.boss_frequency == 0 and actual_floor != 5:
                filepath = 'data/maps/' + str(specific_name) + 'Boss.json'
                self.game.level_style = specific_name

            # Normal levels:
            else:
                # All levels scale with floor:
                enemy_count_max = int(self.game.floors[name])
                size = int(5 * np.log(enemy_count_max ** 2) + 13 + enemy_count_max / 4)
                if name == 'infinite':
                    enemy_count_max *= 2
                    size += 5

                self.load_random_tilemap(
                    size, enemy_count_max, level_type=name, level_style=specific_name)
                return ()

        # Only for level editor
        elif name == 'editor':
            root = tkinter.Tk()
            root.withdraw()

            currdir = os.getcwd()
            filepath = filedialog.askopenfilename(initialdir=currdir,
                                                  title="Open map",
                                                  filetypes=(("JSON Files", "*.json*"),
                                                             ("All Files", "*.*")))

        # Otherwise try to open file eg for lobby.
        else:
            filepath = 'data/maps/' + str(name) + '.json'
            self.game.level_style = name

        f = open(filepath, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tilesize = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

        if filepath.endswith('infiniteBoss.json'):
            # Decide which boss spawners to keep:

            type_to_spawner = {
                'normal': 27,
                'grass': 28,
                'spooky': 31,
                'rubiks': 33,
                'aussie': 35,
                'space': 30,
                'hell': 40,
                'heaven': 41,

                'bait': 29,
            }
            keep = [type_to_spawner[self.game.get_random_level()] for _ in range(2)]
            keep_meteor_baits = 30 in keep
            if keep[0] == keep[1] and keep[0] in ['heaven', 'hell']:
                keep[1] = 'heaven' if keep[0] == 'hell' else 'hell'
            print(keep)

            # remove the rest:
            for spawner in self.extract('spawners', keep=True):
                # spawner type must be of boss types.
                if spawner['variant'] in type_to_spawner.values():

                    if spawner['variant'] in keep:
                        keep[keep.index(spawner['variant'])] = ''
                    elif spawner['variant'] == 29 and keep_meteor_baits:
                        pass
                    else:
                        del self.tilemap[str(int(spawner['pos'][0] // self.tile_size)) + ';' + str(
                            int(spawner['pos'][1] // self.tile_size))]

    def solid_check(self, pos, return_value=''):
        tile_loc = str(int(pos[0]) // self.tile_size) + \
            ';' + str(int(pos[1]) // self.tile_size)
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                if return_value == 'pos':
                    return tuple(self.tilemap[tile_loc]['pos'])
                elif return_value == 'bool':
                    return True
                else:
                    return self.tilemap[tile_loc]
            elif return_value == 'bool':
                return False
        elif return_value == 'bool':
            return False

    def autotile(self, windows=True):
        for loc in self.tilemap:
            tile = self.tilemap[loc]

            # Rubik's level randomising
            if tile['type'] == 'rubiks':
                tile['variant'] = random.choice(range(0, 6))
                continue

            # Tunnel correction
            if tile['type'] == 'cracked':
                tile['variant'] = 4
                for int, shift in enumerate([(0, 1), (0, -1), (1, 0), (-1, 0)]):
                    check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                    if check_loc not in self.tilemap:
                        tile['variant'] = int
                        continue
                continue

            neighbours = set()
            for shift in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:

                    if self.tilemap[check_loc]['type'] in AUTOTILE_TYPES:
                        neighbours.add(shift)

            neighbours = tuple(sorted(neighbours))

            if (tile['type'] in AUTOTILE_TYPES) and (neighbours in AUTOTILE_MAP):
                if AUTOTILE_MAP[neighbours] == 5 and windows == True:

                    window_choice = random.choice(range(self.autotile_count, self.autotile_count + 3))
                    tile['variant'] = window_choice if random.random() < 0.01 else 5

                    if tile['type'] in ['space', 'heaven'] and random.random() < 0.1:
                        tile['variant'] = random.choice(range(self.autotile_count + 3, len(self.game.assets[tile['type']])))

                    elif tile['type'] == 'spooky' and random.random() < 0.005:
                        self.offgrid_tiles.append({'type': 'spawners', 'variant': 24, 'pos': [tile['pos'][0] * self.tilesize, tile['pos'][1] * self.tilesize]})
                        variant = random.choice(range(self.autotile_count + 3, len(self.game.assets[tile['type']])))
                        tile['variant'] = variant

                else:
                    tile['variant'] = AUTOTILE_MAP[neighbours]

    def physics_rects_around(self, pos, is_boss=False):
        rects = []
        for tile in self.nearby_tiles(pos, is_boss=is_boss):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(
                    tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects
