import math
import pygame

class Spark:
    def __init__(self, pos, angle, speed, color = (255, 255, 255)):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
        self.color = color

    def update(self, game, offset = (0, 0)):
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
    def __init__(self, pos, maxRadius, angleA, angleB, speed, color = (255, 255, 255), colorStr = 'white', canDamageBoss = False, width = 1, damage = 1, type = 'default'):
        self.pos = list(pos)
        self.maxRadius = maxRadius
        self.radius = 0
        self.angleA = angleA
        self.angleB = angleB
        self.speed = speed
        self.color = color
        self.colorStr = colorStr
        self.canDamageBoss = canDamageBoss
        self.width = width
        self.displayWidth = width
        self.type = type
        self.damage = damage
        self.rect = pygame.Rect(self.pos[0] - self.radius / 2, self.pos[1] - self.radius / 2, 2 * self.radius, 2 * self.radius)
    
    def update(self, game, offset = (0, 0)):
        if self.width > 1:
            self.width = max(1, self.width - (self.width / (self.maxRadius / self.speed)))
            self.displayWidth = int(self.width)

        if self.radius < self.maxRadius:
            self.radius += self.speed
        else:
            return True

        self.dispRect = pygame.Rect(self.pos[0] - self.radius - offset[0], self.pos[1] - self.radius - offset[1], 2 * self.radius, 2 * self.radius)
        self.posRect = pygame.Rect(self.pos[0] - self.radius, self.pos[1] - self.radius, 2 * self.radius, 2 * self.radius)

        #Check for player collision:
        if self.checkCollision(game.player.rect()):
            game.player.damage(self.damage, self.type)

        #Check for boss collision (Rubiks)
        for boss in game.bosses.copy():
            if self.checkCollision(boss.rect()) and self.colorStr == boss.action and self.canDamageBoss:
                if boss.damageSelf():
                    boss.set_action('dying')
                    boss.gravityAffected = True


    def render(self, surface, offset = (0, 0)):
        pygame.draw.arc(surface, self.color, self.dispRect, self.angleA, self.angleB, width = self.displayWidth)

    def checkCollision(self, rectToCollide):
        if self.posRect.colliderect(rectToCollide):

            for angle in range(int(math.degrees(self.angleA)), int(math.degrees(self.angleB)), 5):
                rad_angle = math.radians(angle)
                x = self.posRect.centerx + self.radius * math.cos(rad_angle)
                y = self.posRect.centery + self.radius * math.sin(rad_angle)

                if rectToCollide.collidepoint(x, y):
                    return True