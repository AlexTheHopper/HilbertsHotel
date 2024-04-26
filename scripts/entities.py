import pygame
import sys
import math
import random
from scripts.particle import *
from scripts.spark import *

class physicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        self.terminal_vel = 5
        self.gravity = 0.1

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip_x = False
        self.set_action('idle')

        self.last_movement = [0, 0]

        self.dashing = 0
        self.dash_dist = 60

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement = (0, 0)):
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        #Forced movement plus velocity already there
        self.frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        self.last_movement = movement

        #Check for collision with physics tiles
        self.pos[1] += self.frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):

                #Collision moving down
                if self.frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                #Collision moving up
                elif self.frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y


        self.pos[0] += self.frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):

                #Collision moving right
                if self.frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                #Collision moving left
                elif self.frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        #Facing direction
        if movement[0] > 0:
            self.flip_x = False
        elif movement[0] < 0:
            self.flip_x = True

        #Add gravity up to terminal velocity
        self.velocity[1] = min(self.velocity[1] + self.gravity, self.terminal_vel)

        #Reset velocity if vertically hit tile
        if self.collisions['up'] or self.collisions['down']:
            self.velocity[1] = 0


        self.animation.update()
        

    def render(self, surface, offset = (0, 0)):
        posx = self.pos[0] - offset[0] + self.anim_offset[0]
        posy = self.pos[1] - offset[1] + self.anim_offset[1]
        surface.blit(pygame.transform.flip(self.animation.img(), self.flip_x, False), (posx, posy))

class Enemy(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0
        self.attack_dist_y = 16
        self.attack_dist_y = 16
        self.bullet_speed = 1.5
    
    def update(self, tilemap, movement = (0, 0)):
        #Walking logic, turning around etc
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip_x else 7), self.pos[1] + 23)):
                if (self.collisions['left'] or self.collisions['right']):
                    self.flip_x = not self.flip_x
                else:
                    movement = (movement[0] - 0.5 if self.flip_x else 0.5, movement[1])
            else:
                self.flip_x = not self.flip_x
            self.walking = max(self.walking - 1, 0)

            #Attack condition
            if not self.walking:
                dist = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if abs(dist[1]) < self.attack_dist_y and not self.game.dead:
                    if self.flip_x and dist[0] < 0:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -self.bullet_speed, 0])
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                    if not self.flip_x and dist[0] > 0:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], self.bullet_speed, 0])
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
                        



        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)


        super().update(tilemap, movement = movement)

        #Setting animation type
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(20, self.game.screenshake)
                self.game.sfx['hit'].play()
                for _ in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

        if self.flip_x:
            xpos = self.rect().centerx - 3 - self.game.assets['gun'].get_width() - offset[0]
            ypos = self.rect().centery - offset[1]
            surface.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (xpos, ypos))
        else:
            xpos = self.rect().centerx + 3 - offset[0]
            ypos = self.rect().centery - offset[1]
            surface.blit(self.game.assets['gun'], (xpos, ypos))

class Player(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0

        self.total_jumps = 2
        self.jumps = self.total_jumps

        self.wall_slide = False

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        self.air_time += 1
        if self.air_time > 180 and not self.wall_slide:
            self.game.dead += 1


        if self.collisions['down']:
            self.air_time = 0
            self.jumps = self.total_jumps

        self.wall_slide = False
        if (self.collisions['left'] or self.collisions['right']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)

            if self.collisions['right']:
                self.flip_x = False
            else:
                self.flip_x = True

            self.set_action('wall_slide')
            
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1

            p_velocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, vel=p_velocity, frame = random.randint(0,7)))

        if abs(self.dashing) in {60, 50}:
            for _ in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, vel=p_velocity, frame = random.randint(0,7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)


        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surface, offset = (0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surface, offset = offset)

    def jump(self):
        if self.wall_slide:
            self.velocity[1] = -2.5
            self.air_time = 5
            self.jumps = max(0, self.jumps - 1)

            if self.flip_x and self.last_movement[0] < 0:
                self.velocity[0] = 2.5
                return True
                
            elif not self.flip_x and self.last_movement[0] > 0:
                self.velocity[0] = -2.5
                return True
               


        elif self.jumps > 0:
            self.jumps -= 1
            self.velocity[1] = min(self.velocity[1], -3)
            self.air_time = 5
            return True

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip_x:
                self.dashing = -self.dash_dist
            else:
                self.dashing = self.dash_dist