"""
Utilities module for Hilbert's Hotel.
Includes animation management, entity information loading.
"""

import os
import numpy as np
import math
import pygame
if __name__ != '__main__':
    import scripts.entities as _entities
    import scripts.characters as _characters

BASE_PATH = 'data/images/'

def load_image(path, dim=False):
    """Load in an image from file ignoring (0, 0, 0) pixels.

    Args:
        path: the path to the image.
        dim: resize image.
    Returns:
        pygame surface of image

    """
    if not dim:
        img = pygame.image.load(BASE_PATH + path).convert()
        img.set_colorkey((0, 0, 0))
    else:
        img = pygame.transform.scale(
            pygame.image.load(BASE_PATH + path).convert(), dim)
        img.set_colorkey((0, 0, 0))
    return img

def load_images(path, dim=False, reverse=False):
    """Load a set of images from folder ignoring (0, 0, 0) pixels.

    Args:
        path: the path to the folder containing the image(s).
        dim: resize image.
        reverse: reverse order of returned list.
    Returns:
        list of pygame surfaces of the images.

    """
    images = [load_image(path + '/' + img_name, dim)
              for img_name in sorted(os.listdir(BASE_PATH + path))]
    if reverse:
        images.reverse()
    return images

def initialise_main_screen(game):
    """Set game parameters for the pygame screen to function.

    Args:
        game: game object.
    Returns:
        none

    """
    game.screen_width = 1080
    game.screen_height = 720
    game.screen = pygame.display.set_mode(
        (game.screen_width, game.screen_height))
    game.hud_display = pygame.Surface((game.screen_width, game.screen_height))
    game.hud_display.set_colorkey((0, 0, 0))
    game.draw_text('Loading...', (game.screen_width / 2, game.screen_height / 2),
                   game.text_font, (86, 31, 126), (0, 0), scale=1.5, mode='center')
    game.screen.blit(game.hud_display, (0, 0))
    pygame.display.update()

def initialise_game_params(game):
    """Set game parameters for all entity info.

    Args:
        game: game object.
    Returns:
        none

    """
    game.game_running = True
    game.fps = 60
    game.display_fps = game.fps
    game.initialising_game = True

    game.movement = [False, False, False, False]
    game.paused = False
    game.talking = False
    game.dead = False
    game.death_count = 0
    game.interraction_frame_z = False
    game.interraction_frame_s = False
    game.interraction_frame_v = False
    game.cave_darkness_range = (50, 250)
    game.cave_darkness = True
    game.min_pause_darkness = 150
    game.currency_entities = []
    game.boss_frequency = 5

    game.current_text_list = []
    game.max_characters_line = 45
    game.talking_to = ''
    game.temp_hearts_bought = 0
    game.temp_hearts_for_planck = 25
    game.heaven_hell = ''

    # Remove these later / debug
    game.previous_level = 'lobby'
    game.current_level = 'lobby'
    game.next_level = 'lobby'

    game.level_style = 'lobby'

    game.infinite_mode_active = False
    game.infinite_floor_max = 1
    game.floors = {
        'normal': 1,
        'grass': 1,
        'spooky': 1,
        'rubiks': 1,
        'aussie': 1,
        'space': 1,
        'heaven_hell': 1,
        'infinite': 1,
        'final': 'The Penthouse'
    }

    # Decorations are of form [type, [variant(s)], weight, [tilesToBeEmpty(relative to x,y)], tilesToBePhysics, offset]
    game.floor_specifics = {
        'normal': {'decorationMod': 2,
                   'decorations': [['decor', [3], 1, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                   ['potplants', range(0, 4), 1, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                   ['spawners', [18], 0.03, [[0, 0]], ['all', [0, 1]], [[0], [0]]],
                                   ['decor', [7], 1, [[0, 0], [1, 0]], ['all', [0, 1], [1, 1]], [range(-4, 4), range(7, 13)]]]},

        'grass': {'decorationMod': 10,
                  'decorations': [['decor', range(0, 2), 5, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                  ['spawners', [18], 0.01, [[0, 0]], ['all', [0, 1]], [[0], [0]]],
                                  ['decor', [8], 1, [[0, 0], [1, 0]], ['all', [0, 1], [1, 1]], [range(-4, 4), range(7, 13)]],
                                  ['decor', [9], 1, [[x, y] for x in range(0, 2) for y in range(0, 3)], ['all', [0, 3], [1, 3]], [range(-3, 3), range(3, 8)]]]},

        'spooky': {'decorationMod': 1,
                   'decorations': [['decor', [3], 1, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                   ['spawners', [18], 0.05, [[0, 0]], ['all', [0, 1]], [[0], [0]]],
                                   ['spawners', [12], 1, [[0, 0]], ['any', [-1, 0], [1, 0]], [[0], [0]]]]},

        'rubiks': {'decorationMod': 1,
                   'decorations': [['decor', [15], 1, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                   ['decor', [16], 0.01, [[0, 0]], ['all', [0, 1]], [[0], [0]]],
                                   ['spawners', [18], 0.05, [[0, 0]], ['all', [0, 1]], [[0], [0]]],]},

        'aussie': {'decorationMod': 1,
                   'decorations': [['decor', [4], 1, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                   ['decor', [5], 1, [[0, 0], [1, 0]], ['all', [0, 1], [1, 1]], [range(-4, 4), [4]]],
                                   ['decor', [6], 1, [[x, y] for x in range(0, 2) for y in range(0, 3)], ['all', [0, 3], [1, 3]], [range(-3, 3), range(3, 8)]],
                                   ['decor', [17], 0.1, [[0, 0]], ['all', [0, 1]], [range(-2, 3), [0]]],
                                   ['decor', [18], 0.1, [[0, 0]], ['all', [0, 1]], [range(-3, 4), [0]]],
                                   ['spawners', [18], 0.05, [[0, 0]], ['all', [0, 1]], [range(-3, 3), range(-1, 1)]],]},

        'space': {'decorationMod': 3,
                  'decorations': [['spawners', [18], 0.05, [[0, 0]], ['all', [0, 1]], [[0], [0]]],
                                  ['decor', [10], 0.01, [[0, 0], [0, 1]], ['all', [0, 2]], [[1], [0]]],
                                  ['decor', [11], 1, [[0, 0]], ['all', [0, 1]], [range(0, 3), [0]]],
                                  ['decor', [12], 1, [[0, 0]], ['all', [0, 1]], [range(0, 5), [0]]],
                                  ['decor', [13], 1, [[0, 0]], ['all', [0, 1]], [range(0, 2), [0]]],]},

        'heaven': {'decorationMod': 5,
                   'decorations': [['spawners', [18], 0.05, [[0, 0]], ['all', [0, 1]], [[0], [0]]],
                                   ['decor', [19], 1, [[0, 0]], ['all', [0, 1]], [range(0, 11), range(1, 8)]],]},

        'hell': {'decorationMod': 5,
                 'decorations': [['spawners', [18], 0.05, [[0, 0]], ['all', [0, 1]], [[0], [0]]],
                                 ['spawners', [36], 0.8, [[0, 0]], ['all', [0, 1]], [range(-3, 3), [0]]],
                                 ['decor', [20], 1, [[0, 0]], ['all', [0, -1]], [range(0, 5), [0]]],
                                 ['decor', [21], 1, [[0, 0]], ['all', [0, 1]], [range(0, 5), [0]]],]},
    }

    game.available_enemy_variants = {
        'normal': [3],
        'normalWeights': [2],
        'grass': [3, 9],
        'grassWeights': [1, 0.5],
        'spooky': [3, 13],
        'spookyWeights': [1, 1],
        'rubiks': [3, 15],
        'rubiksWeights': [1, 1],
        'aussie': [3],
        'aussieWeights': [1],
        'space': [3, 22],
        'spaceWeights': [1, 1],
        'heaven': [3, 22, 37],
        'heavenWeights': [1, 1, 2],
        'hell': [3, 4, 13, 39],
        'hellWeights': [1, 1, 1, 2],
    }

    game.entity_info = {
        1: {'type': 'character', 'object': _characters.Hilbert, 'name': 'Hilbert'},
        6: {'type': 'character', 'object': _characters.Noether, 'name': 'Noether'},
        7: {'type': 'character', 'object': _characters.Curie, 'name': 'Curie'},
        8: {'type': 'character', 'object': _characters.Planck, 'name': 'Planck'},
        2: {'type': 'character', 'object': _characters.Faraday, 'name': 'Faraday'},
        11: {'type': 'character', 'object': _characters.Lorenz, 'name': 'Lorenz'},
        14: {'type': 'character', 'object': _characters.Franklin, 'name': 'Franklin'},
        16: {'type': 'character', 'object': _characters.Rubik, 'name': 'Rubik'},
        17: {'type': 'character', 'object': _characters.Cantor, 'name': 'Cantor'},
        21: {'type': 'character', 'object': _characters.Melatos, 'name': 'Melatos'},
        23: {'type': 'character', 'object': _characters.Webster, 'name': 'Webster'},
        26: {'type': 'character', 'object': _characters.Watson, 'name': 'Watson'},
        42: {'type': 'character', 'object': _characters.Barad, 'name': 'Barad'},

        5: {'type': 'extra_entity', 'object': _entities.Glowworm, 'size': (5, 5)},
        12: {'type': 'extra_entity', 'object': _entities.Torch, 'size': (16, 16)},
        18: {'type': 'extra_entity', 'object': _entities.HeartAltar, 'size': (16, 16)},
        24: {'type': 'extra_entity', 'object': _entities.CreepyEyes, 'size': (16, 16)},
        29: {'type': 'extra_entity', 'object': _entities.MeteorBait, 'size': (16, 16)},
        31: {'type': 'extra_entity', 'object': _entities.Gravestone, 'size': (32, 32)},
        32: {'type': 'extra_entity', 'object': _entities.FlyGhost, 'size': (12, 12)},
        34: {'type': 'extra_entity', 'object': _entities.RubiksCubeThrow, 'size': (16, 16)},
        36: {'type': 'extra_entity', 'object': _entities.Candle, 'size': (10, 6)},
        38: {'type': 'extra_entity', 'object': _entities.Orb, 'size': (4, 4)},
        43: {'type': 'extra_entity', 'object': _entities.PenthouseLock, 'size': (16, 16)},
        44: {'type': 'extra_entity', 'object': _entities.Helper, 'size': (8, 15)},

        10: {'type': 'spawn_point', 'object': _entities.SpawnPoint, 'size': (16, 16)},

        3: {'type': 'enemy', 'object': _entities.GunGuy, 'size': (8, 15)},
        4: {'type': 'enemy', 'object': _entities.Bat, 'size': (6, 6)},
        9: {'type': 'enemy', 'object': _entities.RolyPoly, 'size': (12, 12)},
        13: {'type': 'enemy', 'object': _entities.Spider, 'size': (10, 10)},
        15: {'type': 'enemy', 'object': _entities.RubiksCube, 'size': (16, 16)},
        19: {'type': 'enemy', 'object': _entities.Kangaroo, 'size': (14, 11)},
        20: {'type': 'enemy', 'object': _entities.Echidna, 'size': (14, 9)},
        22: {'type': 'enemy', 'object': _entities.AlienShip, 'size': (12, 8)},
        37: {'type': 'enemy', 'object': _entities.Cherub, 'size': (8, 15)},
        39: {'type': 'enemy', 'object': _entities.Imp, 'size': (8, 15)},

        25: {'type': 'boss', 'object': _entities.SpookyBoss, 'size': (14, 28)},
        27: {'type': 'boss', 'object': _entities.NormalBoss, 'size': (26, 8)},
        28: {'type': 'boss', 'object': _entities.GrassBoss, 'size': (20, 20)},
        30: {'type': 'boss', 'object': _entities.SpaceBoss, 'size': (26, 8)},
        33: {'type': 'boss', 'object': _entities.RubiksBoss, 'size': (32, 32)},
        35: {'type': 'boss', 'object': _entities.AussieBoss, 'size': (20, 20)},
        40: {'type': 'boss', 'object': _entities.HeavenBoss, 'size': (11, 30)},
        41: {'type': 'boss', 'object': _entities.HellBoss, 'size': (11, 30)},
    }

    game.asset_info = {
        'entities/.enemies/': {
            'alienship/': [['idle', 10, True], ['flying', 10, True]],
            'bat/': [['idle', 10, True], ['grace', 10, True], ['charging', 20, False], ['attacking', 10, True]],
            'echidna/': [['idle', 10, True], ['grace', 10, True], ['charging', 30, False], ['walking', 6, True]],
            'gunguy/': [['idle', 10, True], ['grace', 4, True], ['run', 4, True], ['jump', 20, True]],
            'gunguyBlue/': [['idle', 10, True], ['grace', 4, True], ['run', 4, True], ['jump', 20, True]],
            'gunguyOrange/': [['idle', 10, True], ['grace', 4, True], ['run', 4, True], ['jump', 20, True]],
            'gunguyPurple/': [['idle', 10, True], ['grace', 4, True], ['run', 4, True], ['jump', 20, True]],
            'kangaroo/': [['idle', 10, True], ['grace', 5, True], ['prep', 4, True], ['jumping', 4, True]],
            'rolypoly/': [['idle', 10, True], ['run', 4, True]],
            'rubiksCube/': [['idle', 60, True], ['blue', 60, True], ['green', 60, True], ['orange', 60, True], ['red', 60, True], ['white', 60, True], ['yellow', 60, True]],
            'spider/': [['idle', 10, True], ['grace', 5, True], ['run', 4, True]],
            'cherub/': [['idle', 10, True], ['flying', 6, True], ['run', 4, True], ['jump', 10, True]],
            'imp/': [['idle', 10, True], ['flying', 6, True], ['run', 4, True], ['jump', 10, True]],
        },

        'entities/': {
            'player/': [['idle', 10, True], ['jump', 5, True], ['run', 4, True], ['wall_slide', 5, True]],
            'creepy_eyes/': [['idle', 15, True]],
            'glowworm/': [['idle', 15, True]],
            'heart_altar/': [['idle', 10, True], ['active', 10, True]],
            'meteor/': [['idle', 10, False], ['kaboom', 5, False]],
            'meteor_bait/': [['idle', 6, True]],
            'spawn_point/': [['idle', 5, True], ['active', 5, True]],
            'torch/': [['idle', 4, True]],
            'gravestone/': [['idle', 4, True]],
            'fly_ghost/': [['idle', 6, True]],
            'candle/': [['idle', 8, True], ['preparing', 8, True], ['active', 8, True]],
            'orb_cherub/': [['idle', 6, True]],
            'orb_imp/': [['idle', 6, True]],
            'penthouse_lock/': [['idle', 6, True]],
            'helper/': [['idle', 5, True], ['grace', 5, True]],
        },

        'entities/.bosses/': {
            'normalboss/': [['idle', 45, True], ['activating', 16, False], ['flying', 6, True], ['attacking', 16, False], ['dying', 30, False]],
            'grassboss/': [['idle', 45, True], ['activating', 10, False], ['run', 6, True], ['attacking', 6, True], ['dying', 30, False]],
            'spaceboss/': [['idle', 45, True], ['activating', 10, True], ['flying', 6, True], ['attacking', 30, False], ['dying', 30, False]],
            'spookyboss/': [['idle', 30, True], ['flying', 6, True], ['teleporting', 6, True], ['dying', 25, False]],
            'rubiksboss/': [['idle', 60, True], ['blue', 60, True], ['green', 60, True], ['orange', 60, True], ['red', 60, True], ['white', 60, True], ['yellow', 60, True], ['dying', 6, True]],
            'aussieboss/': [['idle', 30, True], ['prep', 45, False], ['active', 6, True], ['jumping', 6, True], ['dying', 25, False]],
            'heavenboss/': [['idle', 30, True], ['flying', 6, True], ['dying', 25, False]],
            'hellboss/': [['idle', 30, True], ['flying', 6, True], ['dying', 25, False]],
        }
    }

    game.portal_info = {
        0: 'lobby',
        1: 'normal',
        2: 'grass',
        3: 'spooky',
        4: 'rubiks',
        5: 'infinite',
        6: 'aussie',
        7: 'space',
        8: 'heaven_hell',
        9: 'final',
    }

    # Screen and display
    game.scroll = [game.screen_width / 2, game.screen_height / 2]
    game.render_scroll = (int(game.scroll[0]), int(game.scroll[1]))

    # overlay displays
    game.display_outline = pygame.Surface(
        (game.screen_width / 2, game.screen_height / 2), pygame.SRCALPHA)
    game.display = pygame.Surface(
        (game.screen_width / 2, game.screen_height / 2))
    game.darkness_surface = pygame.Surface(
        game.display_outline.get_size(), pygame.SRCALPHA)

    # VALUES THAT SAVE
    game.max_health = 1
    game.health = game.max_health
    game.power_level = 1
    game.difficulty = 1
    game.temporary_health = 0
    game.not_lost_on_death = ['hammers', 'penthouseKeys']
    game.spawn_point = False
    game.screenshake_on = True
    game.volume_on = True

    game.wallet = {
        'cogs': 0,
        'redCogs': 0,
        'blueCogs': 0,
        'purpleCogs': 0,
        'heartFragments': 0,
        'wings': 0,
        'eyes': 0,
        'chitins': 0,
        'fairyBreads': 0,
        'boxingGloves': 0,
        'yellowOrbs': 0,
        'redOrbs': 0,
        'hammers': 0,
        'penthouseKeys': 0,
        'credits': 0,
    }

    # Prep dialogue management.
    game.dialogue_history = {
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
                    '6said': False,
                    '7available': False,
                    '7said': False,
                    '8available': False,
                    '8said': False,
                    '9available': False,
                    '9said': False,
                    '10available': False,
                    '10said': False,
                    '11available': False,
                    '11said': False,
                    '12available': False,
                    '12said': False,},

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
                    '5said': False,
                    '6available': False,
                    '6said': False,
                    '7available': False,
                    '7said': False,
                    '8available': False,
                    '8said': False,
                    '9available': False,
                    '9said': False},

        'Curie': {'0available': True,
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
                    '3said': False},

        'Lorenz': {'0available': True,
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
                   '6said': False,
                   '7available': False,
                   '7said': False,
                   '8available': False,
                   '8said': False,
                   '9available': False,
                   '9said': False},

        'Franklin': {'0available': True,
                     '0said': False,
                     '1available': False,
                     '1said': False,
                     '2available': False,
                     '2said': False,
                     '3available': False,
                     '3said': False,
                     '4available': False,
                     '4said': False},

        'Rubik': {'0available': True,
                  '0said': False,
                  '1available': False,
                  '1said': False,
                  '2available': False,
                  '2said': False,
                  '3available': False,
                  '3said': False},

        'Cantor': {'0available': True,
                   '0said': False,
                   '1available': False,
                   '1said': False,
                   '2available': False,
                   '2said': False,
                   '3available': False,
                   '3said': False,
                   '4available': False,
                   '4said': False},

        'Melatos': {'0available': True,
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

        'Webster': {'0available': True,
                    '0said': False,
                    '1available': False,
                    '1said': False,
                    '2available': False,
                    '2said': False,
                    '3available': False,
                    '3said': False,
                    '4available': False,
                    '4said': False},

        'Barad': {'0available': True,
                    '0said': False,
                    '1available': False,
                    '1said': False,
                    '2available': False,
                    '2said': False,
                    '3available': False,
                    '3said': False,
                    '4available': False,
                    '4said': False},

        'Watson': {'0available': True,
                   '0said': False,
                   '1available': False,
                   '1said': False,
                   '2available': False,
                   '2said': False,
                   '3available': False,
                   '3said': False,
                   '4available': False,
                   '4said': False},

    }

    game.characters_met = {
        'Hilbert': True,
        'Noether': False,
        'Curie': False,
        'Planck': False,
        'Faraday': True,
        'Lorenz': False,
        'Franklin': False,
        'Rubik': False,
        'Cantor': False,
        'Melatos': False,
        'Webster': True,
        'Barad': True,
        'Watson': True
    }

    game.portals_met = {
        'lobby': True,
        'normal': True,
        'grass': False,
        'spooky': True,
        'rubiks': True,
        'aussie': True,
        'space': True,
        'infinite': True,
        'heaven_hell': True,
        'final': False,
    }

    game.encounters_check = {
        'spawn_points': False,
        'heart_altars': False,
        'cogs': False,
        'redCogs': False,
        'blueCogs': False,
        'purpleCogs': False,
        'heartFragments': False,
        'wings': False,
        'eyes': False,
        'chitins': False,
        'fairyBreads': False,
        'boxingGloves': False,
        'yellowOrbs': False,
        'redOrbs': False,
        'hammers': False,
        'penthouseKeys': False,
        'credits': False
    }

    game.encounters_check_text = {
        'spawn_points': ['Spawn Point: Activate to change your spawn point in the lobby!'],
        'heart_altars': ['Heart Altar: Gives you a handy lil heart back! Only if you have an empty one though.'],
        'cogs': ['Cogs: Handy little machinery parts. Can be used to fix things. Found commonly everywhere.'],
        'redCogs': ['Red Cogs: Just like a normal cog, but fancier! And Red!'],
        'blueCogs': ['Blue Cogs: Just like a normal cog, but fancier! And Blue!'],
        'purpleCogs': ['Purple Cogs: Just like a normal cog, but fancier! And Purple!'],
        'heartFragments': ['Heart Fragments: Gross little part of a heart. Can be used to increase your health. Rare drop from enemies but more common from wizards.'],
        'wings': ['Wings: The poor bat. Can be used to increase amounts of jumps in the air. Common drop from flying enemies.'],
        'eyes': ['Eyes: Ew this is just getting disgusting. The more you have, the more you can see. Common drop from roly-poly eyeballs.'],
        'chitins': ['Chitin: What the hell is this thing? Apparently some strong stuff in insects, this could probably increase the power of your smacks.'],
        'fairyBreads': ['Fairy Bread: Only the most delicious snack that has ever existed.'],
        'boxingGloves': ['Boxing Gloves: For some reason kangaroos got \'em. Punchy punch!'],
        'yellowOrbs': ['Heavenly Orbs: They glow with the power of one million beers.'],
        'redOrbs': ['Satanic Orbs: They glow with the power of one million Jägermeisters.'],
        'hammers': ['Hammer: Hammer go SMASH! Can be used to break cracked walls to reveal secrets.'],
        'penthouseKeys': ['Penthouse Key: Grants acess to the penthouse.'],
        'credits': ['Credit: Ooh, interesting little thingy, can be used to give credit where credit it due. Of this game. Not DNA.'],
        'error': ['OOPS! Something went wrong here and I couldnt find the text for you, soz.']
    }

    game.tunnels_broken = {
        'tunnel1': False,
        'tunnel2': False,
        'tunnel3': False,
        'tunnel4': False,
        'tunnel5': False,
        'tunnel6': False,
        'tunnel7': False,
        'tunnel8': False,
    }

    game.tunnel_positions = {
        'tunnel1': [[x, y] for x in range(36, 54) for y in range(-1, 1)],
        'tunnel2': [[x, y] for x in range(-17, 1) for y in range(-1, 1)],
        'tunnel3': [[x, y] for x in range(17, 20) for y in range(-24, -16)],
        'tunnel4': [[x, y] for x in range(-4, 7) for y in range(-33, -30)],
        'tunnel5': [[x, y] for x in range(30, 41) for y in range(-33, -30)],
        'tunnel6': [[x, y] for x in range(17, 20) for y in range(-51, -44)],
        'tunnel7': [[18, y] for y in range(12, 16)],
        'tunnel8': [[x, y] for x in range(2, 35) for y in range(-78, -63)],
    }

    # Death message stuff
    game.damaged_by = 'default'
    game.death_message = ''
    game.enemy_names = {
        'default': 'Nothing',
        'gunguy': 'Gun Guy',
        'gunguyOrange': 'Orange Gun Guy',
        'gunguyBlue': 'Blue Gun Guy',
        'gunguyPurple': 'Purple Gun Guy',
        'gunguyStaff': 'Wizard',
        'gunguyOrangeStaff': 'Orange Wizard',
        'gunguyBlueStaff': 'Blue Wizard',
        'gunguyPurpleStaff': 'Purple Wizard',
        'gunguyWitch': 'Witch',
        'gunguyOrangeWitch': 'Orange Witch',
        'gunguyBlueWitch': 'Blue Witch',
        'gunguyPurpleWitch': 'Purple Witch',
        'bat': 'Bat',
        'rolypoly': 'Roly Poly',
        'spider': 'Spider',
        'rubiksCube': 'Rubik\'s Cube',
        'kangaroo': 'Kangaroo',
        'echidna': 'Echidna',
        'meteor': 'Meteor',
        'alienship': 'Alien Spaceship',
        'fly_ghost': 'Lil\' Ghost',
        'candle': 'Hot Candle',
        'cherub': 'Cherub',
        'orb_cherub': 'Magical Yellow Orb',
        'orb_imp': 'Magical Red Orb',

        'normalboss': 'Big Bat',
        'grassboss': 'Big Roly Poly',
        'spookyboss': 'Ghost',
        'rubiksboss': 'Big Rubik\'s Cube',
        'aussieboss': 'Big Ol\' Roo',
        'spaceboss': 'Big Alien Spaceship',
        'heavenboss': 'God',
        'hellboss': 'Demon',
    }
    game.death_verbs = ['killed',
                       'vanquished',
                       'taken down',
                       'eliminated',
                       'slain',
                       'obliterated',
                       'bested',
                       'removed from this world',
                       'nibbled to death',
                       'chewed up',
                       'bonked',
                       'bamboozled',
                       'yoinked',
                       'pwned',
                       'tickled a little too hard',
                       'just slightly harmed']

def is_prime(num):
    """Determine if an integer is a prime number.

    Args:
        num: integer.
    Returns:
        bool

    """
    if num < 2:
        return False
    if num == 2:
        return True

    for n in range(2, math.ceil(np.sqrt(num)) + 1):
        if num % n == 0:
            return False
    return True

class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.img_duration = img_dur
        self.loop = loop
        self.done = False
        self.frame = 0

    def copy(self):
        """Copy Animation object.

        Args:
            none
        Returns:
            Animation object.

        """
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        """Update Animation object's frame.

        Args:
            none
        Returns:
            none

        """
        if self.loop:
            self.frame = (
                self.frame + 1) % (self.img_duration * len(self.images))

        else:
            self.frame = min(
                self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        """Get current frame of Animation object.

        Args:
            none
        Returns:
            Pygame surface of current Animation frame.

        """
        return self.images[int(self.frame / self.img_duration)]
