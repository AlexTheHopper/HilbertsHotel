import pygame
import os
import numpy as np
import math
import random

BASE_PATH = 'data/images/'

def load_image(path, dim = False):
    if not dim:
        img = pygame.image.load(BASE_PATH + path).convert()
        img.set_colorkey((0, 0, 0))
    else:
        img = pygame.transform.scale(pygame.image.load(BASE_PATH + path).convert(), dim)
        img.set_colorkey((0, 0, 0))
    return img


def load_images(path, dim = False):
    images = [load_image(path + '/' + img_name, dim) for img_name in sorted(os.listdir(BASE_PATH + path))]
    return images


def initialiseMainScreen(game):
    game.screen_width = 1080
    game.screen_height = 720
    game.screen = pygame.display.set_mode((game.screen_width,game.screen_height))
    game.HUDdisplay = pygame.Surface((game.screen_width, game.screen_height))
    game.HUDdisplay.set_colorkey((0, 0, 0))
    game.draw_text('Loading...', (game.screen_width / 2, game.screen_height / 2), game.text_font, (86, 31, 126), (0, 0), scale = 1.5, mode = 'center') 
    game.screen.blit(game.HUDdisplay, (0, 0))
    pygame.display.update()


def initialiseGameParams(game):
    game.game_running = True
    game.fps = 60
    game.displayFPS = game.fps
    game.initialisingGame = True

    game.movement = [False, False, False, False]
    game.paused = False
    game.talking = False
    game.dead = False
    game.deathCount = 0
    game.interractionFrame = False
    game.caveDarknessRange = (50,250)
    game.caveDarkness = True
    game.minPauseDarkness = 150
    game.minimapActive = False
    game.minimapList = {}

    game.currentTextList = []
    game.maxCharactersLine = 55
    game.talkingTo = ''

    game.currentLevel = 'lobby'
    game.nextLevel = 'lobby'
    game.floors = {
        'normal': 1,
        'grass': 1,
        'spooky': 1
        }
    
    #Decorations are of form [type, [variant(s)], weight, [tilesToBeEmpty(relative to x,y)], tilesToBePhysics, offset]
    game.floorSpecifics = {
        'normal': {'decorationMod': 2,
                   'decorations': [['decor', [3], 1, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                ['potplants', range(0, 4), 1, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                ['large_decor', [0], 1, [[0, 0], [1, 0]], ['all', [0, 1], [1, 1]], [range(-4, 4), range(7,13)]]]},

        'grass': {'decorationMod': 15,
                  'decorations': [['decor', range(0,2), 5, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                ['large_decor', [1], 1, [[0, 0], [1, 0]], ['all', [0, 1], [1, 1]], [range(-4, 4), range(7,13)]],
                                ['large_decor', [2], 1, [[x,y] for x in range(0,2) for y in range(0,3)], ['all', [0, 3], [1, 3]], [range(-3, 3), range(3,8)]]]},

        'spooky': {'decorationMod': 1,
                   'decorations': [['decor', [3], 1, [[0, 0]], ['all', [0, 1]], [range(-4, 4), [0]]],
                                ['spawners', [12], 1, [[0, 0], [0, 1]], ['any', [1, 0], [-1, 0]], [[0], [0]]]]}
        }

    game.availableEnemyVariants = {
        'normal': [3],
        'normalWeights': [2],
        'grass': [3, 9],
        'grassWeights': [1, 0.5],
        'spooky': [3, 13],
        'spookyWeights': [1, 1]
    }

    #Screen and display
    game.scroll = [game.screen_width / 2, game.screen_height / 2]
    game.render_scroll = (int(game.scroll[0]), int(game.scroll[1]))
    
    #overlay displays
    game.display_outline = pygame.Surface((game.screen_width / 2, game.screen_height / 2), pygame.SRCALPHA)
    game.display = pygame.Surface((game.screen_width / 2, game.screen_height / 2))
    game.minimapdisplay = pygame.Surface((game.screen_width / 4, game.screen_height / 4), pygame.SRCALPHA)
    game.darkness_surface = pygame.Surface(game.display_outline.get_size(), pygame.SRCALPHA)

    #VALUES THAT SAVE
    game.maxHealth = 1
    game.health = game.maxHealth
    game.powerLevel = 1
    game.difficulty = 1
    game.temporaryHealth = 0
    game.enemyCountMax = 1
    game.currentLevelSize = 15
    game.notLostOnDeath = ['hammers']
    game.spawnPoint = False

    game.wallet = {
        'cogs': 0,
        'redCogs': 0,
        'blueCogs': 0,
        'purpleCogs': 0,
        'heartFragments': 0,
        'wings': 0,
        'eyes': 0,
        'chitins': 0,
        'hammers': 0
    }

    #Prep dialogue management.
    game.dialogueHistory = {
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
                '8said': False},

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
                '4said': False},

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
                '5said': False},

        'Franklin': {'0available': True,
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

    game.charactersMet = {
        'Hilbert': True,
        'Noether': False,
        'Curie': False,
        'Planck': False,
        'Faraday': True,
        'Lorenz': False,
        'Franklin': False
    }

    game.portalsMet = {
        'lobby': True,
        'normal': True,
        'grass': False,
        'spooky': True
    }

    game.encountersCheck = {
        'spawnPoints': False,
        'cogs': False,
        'redCogs': False,
        'blueCogs': False,
        'purpleCogs': False,
        'heartFragments': False,
        'wings': False,
        'eyes': False,
        'chitins': False,
        'hammers': False
    }

    game.encountersCheckText = {
        'spawnPoints': ['Spawn Point: Activate to change your spawn point in the lobby!'],
        'cogs': ['Cogs: Handy little machinery parts. Can be used to fix things. Found commonly everywhere.'],
        'redCogs': ['Red Cogs: Just like a normal cog, but fancier! And Red!'],
        'blueCogs': ['Blue Cogs: Just like a normal cog, but fancier! And Blue!'],
        'purpleCogs': ['Purple Cogs: Just like a normal cog, but fancier! And Purple!'],
        'heartFragments': ['Heart Fragments: Gross little part of a heart. Can be used to increase your health. Rare drop from enemies but more common from wizards.'],
        'wings': ['Wings: The poor bat. Can be used to increase amounts of jumps in the air. Common drop from flying enemies.'],
        'eyes': ['Eyes: Ew this is just getting disgusting. The more you have, the more you can see. Common drop from roly-poly eyeballs.'],
        'chitins': ['Chitin: What the hell is this thing? Apparently some strong stuff in insects, this could probably increase the power of your smacks.'],
        'hammers': ['Hammer: Hammer go SMASH! Can be used to break cracked walls to reveal secrets.']
    }

    game.tunnelsBroken = {
        'tunnel1': False,
        'tunnel2': False,
        'tunnel3': False
    }

    game.tunnelPositions = {
        'tunnel1': [[x, y] for x in range(36, 54) for y in range(-1,1)],
        'tunnel2': [[x, y] for x in range(-17, 1) for y in range(-1,1)],
        'tunnel3': [[x, y] for x in range(17, 20) for y in range(-24,-16)]
    }


def isPrime(num):
    if num < 2:
        return False
    if num == 2:
        return True
    
    for n in range(2, math.ceil(np.sqrt(num)) + 1):
        if num % n == 0:
            return False
    return True


class Animation:
    def __init__(self, images, img_dur = 5, loop = True):
        self.images = images
        self.img_duration = img_dur
        self.loop = loop
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))

        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        return self.images[int(self.frame / self.img_duration)]