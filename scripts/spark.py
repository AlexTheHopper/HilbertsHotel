import math
import pygame

class Spark:
    def __init__(self, pos, angle, speed, color = (255, 255, 255)):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
        self.color = color

    def update(self, offset = (0, 0)):
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed

        self.speed = max(0, self.speed - 0.1)
        return not self.speed
    
    def render(self, surface, offset = (0, 0)):
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi / 2) * self.speed / 2 - offset[0], self.pos[1] + math.sin(self.angle + math.pi / 2) * self.speed / 2 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi / 2) * self.speed / 2 - offset[0], self.pos[1] + math.sin(self.angle - math.pi / 2) * self.speed / 2 - offset[1])
        ]
        pygame.draw.polygon(surface, self.color, render_points)

class ExpandingArc:
    def __init__(self, pos, maxRadius, angleA, angleB, speed, color = (255, 255, 255), width = 1):
        self.pos = list(pos)
        self.maxRadius = maxRadius
        self.radius = 0
        self.angleA = angleA
        self.angleB = angleB
        self.speed = speed
        self.color = color
        self.width = width
        self.displayWidth = width
        self.rect = pygame.Rect(self.pos[0] - self.radius / 2, self.pos[1] - self.radius / 2, 2 * self.radius, 2 * self.radius)
    
    def update(self, offset = (0, 0)):
        if self.width > 1:
            self.width = max(1, self.width - (self.width / (self.maxRadius / self.speed)))
            self.displayWidth = int(self.width)

        if self.radius < self.maxRadius:
            self.radius += self.speed
        else:
            return True

        self.rect = pygame.Rect(self.pos[0] - self.radius / 2 - offset[0], self.pos[1] - self.radius / 2 - offset[1], 2 * self.radius, 2 * self.radius)

        

    def render(self, surface, offset = (0, 0)):
        pygame.draw.arc(surface, self.color, self.rect, self.angleA, self.angleB, width = self.displayWidth)