import math
import random

class Particle:
    def __init__(self, game, p_type, pos, vel = [0, 0], frame = 0):
        self.game = game
        self.type = p_type
        self.pos = list(pos)
        self.velocity = list(vel)
        self.animation = self.game.assets['particle/' + self.type].copy()
        self.animation.frame = frame
        self.randomness = random.random() * math.pi * 2

    def update(self):
        kill = False
        
        if self.animation.done:
            kill = True

        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        self.animation.update()
        return kill
    
    def render(self, surface, offset = (0, 0)):
        img = self.animation.img()
        surface.blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2))