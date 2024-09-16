import pygame
import sys
import math
import random
import numpy as np

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
        self.collideWallCheck = True
        self.collideWall = True
        self.isBoss = False
        self.attackPower = 1

        self.terminal_vel = 5
        self.gravity = 0.12

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip_x = False
        self.set_action('idle')
        self.renderDistance = self.game.screen_width / 3

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
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1]))

        # Only update/render at close distances
        renderDistToPlayer = np.linalg.norm((self.pos[0] - self.game.player.pos[0], self.pos[1] - self.game.player.pos[1]))
        if renderDistToPlayer > self.renderDistance:
            return False
        
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        #Forced movement plus velocity already there
        self.frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        self.last_movement = movement

        if self.collideWallCheck:
            #Check for collision with physics tiles
            self.pos[1] += self.frame_movement[1]
            entity_rect = self.rect()
            for rect in tilemap.physics_rects_around(self.pos, isBoss = self.isBoss):
                if entity_rect.colliderect(rect):

                    #Collision moving down
                    if self.frame_movement[1] > 0:
                        entity_rect.bottom = rect.top
                        self.collisions['down'] = True

                    #Collision moving up
                    elif self.frame_movement[1] < 0:
                        entity_rect.top = rect.bottom
                        self.collisions['up'] = True
                    if self.collideWall:
                        self.pos[1] = entity_rect.y

                    if self.type == 'player':
                        self.lastCollidedWall = self.game.tilemap.tilemap[str(rect.x // self.game.tilemap.tilesize) + ';' + str(rect.y // self.game.tilemap.tilesize)]

            self.pos[0] += self.frame_movement[0]
            entity_rect = self.rect()
            for rect in tilemap.physics_rects_around(self.pos, isBoss = self.isBoss):
                if entity_rect.colliderect(rect):

                    #Collision moving right
                    if self.frame_movement[0] > 0:
                        entity_rect.right = rect.left
                        self.collisions['right'] = True
                        
                    #Collision moving left
                    elif self.frame_movement[0] < 0:
                        entity_rect.left = rect.right
                        self.collisions['left'] = True
                    if self.collideWall:
                        self.pos[0] = entity_rect.x

                    if self.type == 'player':
                        self.lastCollidedWall = self.game.tilemap.tilemap[str(rect.x // self.game.tilemap.tilesize) + ';' + str(rect.y // self.game.tilemap.tilesize)]

        #Facing direction
        if movement[0] > 0:
            self.flip_x = False
        elif movement[0] < 0:
            self.flip_x = True

        #Add gravity up to terminal velocity
        if self.gravityAffected and not (self.collisions['down'] or self.collisions['up']):
            self.velocity[1] = min(self.velocity[1] + self.gravity, self.terminal_vel)

        #Reset velocity if vertically hit tile if affected by gravity:
        if (self.collisions['up'] or self.collisions['down']) and self.gravityAffected:
            self.velocity[1] = 0
    
        self.animation.update()
        

    def render(self, surface, offset = (0, 0), rotation = 0):
        # Only update/render at close distances
        renderDistToPlayer = np.linalg.norm((self.pos[0] - self.game.player.pos[0], self.pos[1] - self.game.player.pos[1]))
        if renderDistToPlayer > self.renderDistance:
            return False

        posx = self.pos[0] - offset[0] + self.anim_offset[0]
        posy = self.pos[1] - offset[1] + self.anim_offset[1]
        
        if rotation != 0:
            image = pygame.transform.rotate(self.animation.img(), rotation * 180 / math.pi)
            surface.blit(pygame.transform.flip(image, self.flip_x, False), (posx, posy))
        else:
            surface.blit(pygame.transform.flip(self.animation.img(), self.flip_x, False), (math.floor(posx), math.floor(posy)))

    def damage(self, intensity = 10):
        self.game.screenshake = max(intensity, self.game.screenshake)
        self.game.sfx['hit'].play()
        for _ in range(intensity):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random() * (intensity / 10)))
            self.game.particles.append(Particle(self.game, 'particle1', self.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
        
        self.game.sparks.append(Spark(self.rect().center, 0, intensity / 4))
        self.game.sparks.append(Spark(self.rect().center, math.pi, intensity / 4))


    def kill(self, intensity = 10, cogCount = 0, redCogCount = 0, blueCogCount = 0, purpleCogCount = 0, heartFragmentCount = 0, wingCount = 0, eyeCount = 0, chitinCount = 0, fairyBreadCount = 0, boxingGloveCount = 0, creditCount = 0):
        self.game.screenshake = max(intensity, self.game.screenshake)
        self.game.sfx['hit'].play()
        for _ in range(intensity):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random() * (intensity / 10)))
            self.game.particles.append(Particle(self.game, 'particle1', self.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
        
        self.game.sparks.append(Spark(self.rect().center, 0, intensity / 4))
        self.game.sparks.append(Spark(self.rect().center, math.pi, intensity / 4))

        #Create currencies
        spawnLoc = (int(self.pos[0] // self.game.tilemap.tile_size), int(self.pos[1] // self.game.tilemap.tile_size))
        spawnLoc = ((spawnLoc[0] * self.game.tilemap.tile_size) + self.game.tilemap.tile_size/2, (spawnLoc[1] * self.game.tilemap.tile_size) + self.game.tilemap.tile_size/2)
        
        for _ in range(cogCount):
            self.game.currencyEntities.append(Currency(self.game, 'cog', spawnLoc))
        for _ in range(redCogCount):
            self.game.currencyEntities.append(Currency(self.game, 'redCog', spawnLoc))
        for _ in range(blueCogCount):
            self.game.currencyEntities.append(Currency(self.game, 'blueCog', spawnLoc))
        for _ in range(purpleCogCount):
            self.game.currencyEntities.append(Currency(self.game, 'purpleCog', spawnLoc))
        for _ in range(heartFragmentCount):
            self.game.currencyEntities.append(Currency(self.game, 'heartFragment', spawnLoc))
        for _ in range(wingCount):
            self.game.currencyEntities.append(Currency(self.game, 'wing', spawnLoc))
        for _ in range(eyeCount):
            self.game.currencyEntities.append(Currency(self.game, 'eye', spawnLoc))
        for _ in range(chitinCount):
            self.game.currencyEntities.append(Currency(self.game, 'chitin', spawnLoc))
        for _ in range(fairyBreadCount):
            self.game.currencyEntities.append(Currency(self.game, 'fairyBread', spawnLoc))
        for _ in range(boxingGloveCount):
            self.game.currencyEntities.append(Currency(self.game, 'boxingGlove', spawnLoc))
        for _ in range(creditCount):
            self.game.currencyEntities.append(Currency(self.game, 'credit', spawnLoc))


class Bat(physicsEntity):
    def __init__(self, game, pos, size, graceDone = False, velocity = [0, 0]):
        super().__init__(game, 'bat', pos, size)

        self.cogCount = random.randint(0,3)
        self.heartFragmentCount = (1 if random.random() < 0.2 else 0)
        self.wingCount = (1 if random.random() < 0.8 else 0)

        self.attackPower = 1
        self.deathIntensity = 10

        self.gravityAffected = False
        self.grace = random.randint(90,210)
        self.graceDone = graceDone
        self.set_action('grace')
        if self.graceDone:
            self.set_action('attacking')
            self.timer = 120
            self.velocity = velocity
        
        self.isAttacking = False
        self.anim_offset = [-3, -2]
        self.timer = 0
        self.pos[1] += 9
        self.pos[0] += 4
        self.toPlayer = [0, 0]
        
    
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        
        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(180,500)
                self.velocity = [random.random() - 1/2, random.random()*0.5 + 0.5]                
                self.graceDone = True
                   
            self.animation.update()

        if self.graceDone:
            if self.action == 'idle':
                self.timer = max(self.timer - 1, 0)

                if np.linalg.norm(self.velocity) > 5:
                    self.velocity[0] *= 0.99
                    self.velocity[1] *= 0.99

                if not self.timer:
                    self.set_action('charging')
                    toPlayer = (self.game.player.pos[0] - self.pos[0] + 4, self.game.player.pos[1] - self.pos[1] + 5)
                    self.toPlayer = toPlayer / np.linalg.norm(toPlayer) 
                    self.velocity = [-self.toPlayer[0] * 0.15, -self.toPlayer[1] * 0.15]

                    self.timer = random.randint(90,120)
                    
            elif self.action == 'charging':
                self.timer = max(self.timer - 1, 0)

                if self.timer == 0:
                    self.velocity[0] = self.toPlayer[0] * 2
                    self.velocity[1] = self.toPlayer[1] * 2
                    self.timer = 120
                    self.set_action('attacking')     

            elif self.action == 'attacking':
                self.timer = max(self.timer - 1, 0)
                if any(self.collisions.values()) and not self.timer:
                    self.set_action('idle')
                    self.timer = random.randint(180,500)
                  
            if self.action != 'charging':
                if self.collisions['up'] or self.collisions['down']:
                    self.velocity[1] = -self.velocity[1] * 0.9
                elif self.collisions['left'] or self.collisions['right']:
                    self.velocity[0] = -self.velocity[0] * 0.9
                    
        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, wingCount = self.wingCount)
                return True
            
        #Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, wingCount = self.wingCount)
                self.game.projectiles.remove(projectile)
                return True

        #Check for player collision, not dashing and in attack mode:
        if self.game.player.rect().colliderect(self.rect()):
            if abs(self.game.player.dashing) < 50 and self.action == 'attacking' and not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)


    def render(self, surface, offset = (0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        angle = 0
        if self.action in ['charging', 'attacking']:
            angle = math.atan2(-self.velocity[1], self.velocity[0]) + math.pi/2 + (math.pi if self.action == 'attacking' else 0)
           
        super().render(surface, offset = offset, rotation = angle)


class GunGuy(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'gunguy', pos, size)
        self.deathIntensity = 15
        self.difficultyLevel = 1
        self.walking = 0
        self.flying = 0
        self.attack_dist_y = 24
        self.bullet_speed = 1.5
        self.shootCountdown = 0
        self.weaponIndex = 0
        self.gravityAffected = True
        
        self.intelligence = math.floor(self.game.floors[str(self.game.currentLevel)] / 5) if self.game.currentLevel == 'normal' else 2
        self.weapon = 'gun' if self.intelligence < 2 else ('staff' if random.random() < (0.75 if self.game.currentLevel in ['spooky', 'space'] else 0.25) else 'gun')

        self.witch = False
        if ((self.weapon == 'staff' and self.game.floors['spooky'] > 1) or self.game.difficulty >= 2) and random.random() < 0.5:
            self.witch = True
        elif self.weapon == 'staff' and self.game.currentLevel == 'space' and random.random() < 0.75:
            self.witch = True

        self.staffCooldown = 120
        self.trajectory = [0, 0]
        self.colours = [(196, 44, 54), (120, 31, 44)]

        if self.game.difficulty >= 2 and self.game.currentLevel in ['normal', 'space']:
            self.difficultyLevel = random.randint(0, self.game.difficulty)
            if self.difficultyLevel == 2:
                self.type = 'gunguyOrange'
                self.colours = [(255, 106, 0), (198, 61, 1)]
            elif self.difficultyLevel == 3:
                self.type = 'gunguyBlue'
                self.colours = [(0, 132, 188), (0, 88, 188)]
            elif self.difficultyLevel == 4:
                self.type = 'gunguyPurple'
                self.colours = [(127, 29, 116), (99, 22, 90)]

        self.cogCount = random.randint(2,4)
        self.redCogCount = random.randint(1,3) if (self.type == 'gunguyOrange') else 0
        self.blueCogCount = random.randint(1,3) if (self.type == 'gunguyBlue') else 0
        self.purpleCogCount = random.randint(1,3) if (self.type == 'gunguyPurple') else 0
        self.heartFragmentCount = 1 if self.weapon == 'staff' else (1 if random.random() < 0.1 else 0)
        self.wingCount = random.randint(0,3) if self.witch else 0
        self.eyeCount = 0

        self.label = self.type + ('Witch' if self.witch else ('Staff' if self.weapon == 'staff' else ''))

        if random.random() < 0.5:
            self.flip_x = True

        self.grace = random.randint(60,120)
        self.graceDone = False
        self.set_action('grace')
    
    def update(self, tilemap, movement = (0, 0)):
        # Only update/render at close distances
        renderDistToPlayer = np.linalg.norm((self.pos[0] - self.game.player.pos[0], self.pos[1] - self.game.player.pos[1]))
        if renderDistToPlayer > self.renderDistance:
            return False

        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.graceDone = True
            self.animation.update()

        if not self.flying:
            if self.velocity[0] > 0:
                self.velocity[0] = max(self.velocity[0] - 0.1, 0)
            else:
                self.velocity[0] = min(self.velocity[0] + 0.1, 0)

        if self.staffCooldown:
            self.staffCooldown = max(self.staffCooldown - 1, 0)
        
        if self.graceDone:
            #Walking logic, turning around etc
            if self.shootCountdown:
                self.shootCountdown = max(self.shootCountdown - 1, 0)
                self.weaponIndex = math.ceil(self.shootCountdown / 20)

                #Shoot condition
                if not self.shootCountdown:
                    #offsets for asset sizes
                    bulletOffset = [4, -4] if self.weapon == 'staff' else [5, 0]
                    bulletVelocity = [-self.bullet_speed, 0] if self.flip_x else [self.bullet_speed, 0]

                    #Vector to player if staff
                    if self.weapon == 'staff':
                        toPlayer = (self.game.player.pos[0] - self.pos[0] + (bulletOffset[0] if self.flip_x else -bulletOffset[0]), self.game.player.pos[1] - self.pos[1])
                        bulletVelocity = toPlayer / np.linalg.norm(toPlayer) * 1.5 
                        self.staffCooldown = 0
                    
                    #Create bullet/bat/meteor
                    if self.witch and self.game.currentLevel == 'space':
                        #Find empty space near/on player and summon meteor
                        foundSpot = False
                        checkSpot = [0, 0]
                        playerPosTile = (self.game.player.pos[0] // self.game.tilemap.tilesize, self.game.player.pos[1] // self.game.tilemap.tilesize)
                        
                        while not foundSpot:
                            checkSpot[0], checkSpot[1] = int(playerPosTile[0] + random.choice(range(-3,4))), int(playerPosTile[1] + random.choice(range(-2,3)))
                            locStr = str(checkSpot[0]) + ';' + str(checkSpot[1])
                            if locStr not in self.game.tilemap.tilemap:
                                foundSpot = True
                        self.game.extraEntities.append(Meteor(self.game, (checkSpot[0] * self.game.tilemap.tilesize, checkSpot[1] * self.game.tilemap.tilesize), (16, 16)))

                    elif self.witch and random.random() < 0.25:
                        batpos = (self.pos[0] - self.pos[0] % self.game.tilemap.tilesize, self.pos[1] - self.pos[1] % self.game.tilemap.tilesize - 5)
                        self.game.enemies.append(Bat(self.game, batpos, (10, 10), graceDone = True, velocity = bulletVelocity))
                    else:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append(Bullet(self.game, [self.rect().centerx - (bulletOffset[0] if self.flip_x else -bulletOffset[0]), self.rect().centery + bulletOffset[1]], bulletVelocity, self.label))
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5 + (math.pi if self.flip_x else 0), 2 + random.random()))
                    
            elif self.walking:
                #Check jump condition, tilemap infront and above:
                inFront = tilemap.solid_check((self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery))
                inFrontDown = tilemap.solid_check((self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 16))
                above = tilemap.solid_check((self.rect().centerx, self.rect().centery - 16))
                
                if inFront and not above and self.collisions['down']:
                    aboveSide = tilemap.solid_check((self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery - 16))
                    aboveAboveSide = tilemap.solid_check((self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery - 32))

                    #Check jump 2 space:
                    aboveAbove = tilemap.solid_check((self.rect().centerx, self.rect().centery - 32))
                    if not above and not aboveAbove and not aboveAboveSide and aboveSide:
                        self.set_action('jump')
                        self.velocity[1] = -3
                        self.velocity[0] =(-0.5 if self.flip_x else 0.5)
                       
                    #Jump one space
                    elif not aboveSide:
                        self.set_action('jump')
                        self.velocity[1] = -2
                        self.velocity[0] =(-0.5 if self.flip_x else 0.5)

                elif not inFrontDown:
                    inFrontDown2 = tilemap.solid_check((self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 32))
                    inFrontDown3 = tilemap.solid_check((self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 48))
                    if not inFrontDown2 and not inFrontDown3:
                        self.flip_x = not self.flip_x
                        self.walking = random.randint(5,15)

                #Turn around if bump into a wall
                if (self.collisions['left'] or self.collisions['right']) and self.action != 'jump':
                    self.flip_x = not self.flip_x  
                else:
                    movement = (movement[0] - 0.5 if self.flip_x else 0.5, movement[1])       

                self.walking = max(self.walking - 1, 0)
               
            elif self.flying:
                self.flying = max(self.flying - 1, 0)
                
                if not self.flying:
                    self.velocity = [0, 0] 
                    self.set_action('idle')
                
            elif random.random() < 0.01:
                #If setting new flying direction, dont fly into a wall
                posCentre = [self.rect().centerx, self.rect().centery]
                leftEmpty = not tilemap.solid_check([posCentre[0] - tilemap.tilesize, posCentre[1]],returnValue = 'bool')
                rightEmpty = not tilemap.solid_check([posCentre[0] + tilemap.tilesize, posCentre[1]],returnValue = 'bool')
                upEmpty = not tilemap.solid_check([posCentre[0], posCentre[1] - tilemap.tilesize],returnValue = 'bool')
                downEmpty = not tilemap.solid_check([posCentre[0], posCentre[1] + tilemap.tilesize],returnValue = 'bool')

                if self.witch and not self.gravityAffected:
                    self.flying = random.randint(30,90)
                    self.velocity = [random.uniform(-leftEmpty, rightEmpty), random.uniform(-upEmpty, downEmpty)]
                    self.flip_x = True if self.velocity[0] < 0 else False
                    self.set_action('run')

                #only activate flying mode if not surrounded by tiles
                elif self.witch and random.random() < 0.2 and upEmpty:
                    self.gravityAffected = False
                    self.flying = random.randint(30,90)
                    self.velocity = [random.uniform(-leftEmpty, rightEmpty), random.uniform(-upEmpty, downEmpty)]
                    self.flip_x = True if self.velocity[0] < 0 else False
                    self.set_action('run')
                
                else:
                    self.walking = random.randint(30, 120)

            #Attack condition
            if (random.random() < 0.02):
                if (self.game.floors[self.game.currentLevel] != 1 or self.game.currentLevel == 'infinite') and not self.shootCountdown:
       
                    if self.weapon == 'gun':
                        disty = self.game.player.pos[1] - self.pos[1]
                        distx = self.game.player.pos[0] - self.pos[0]
                        #Y axis condition:
                        if abs(disty) < self.attack_dist_y and not self.game.dead:
                            #X axis condition
                            if (self.flip_x and distx < 0) or (not self.flip_x and distx > 0):
                                self.shootCountdown = 60
                                self.walking = 0

                    elif self.weapon == 'staff' and self.game.currentLevel == 'space':
                        distToPlayer = np.linalg.norm((self.pos[0] - self.game.player.pos[0], self.pos[1] - self.game.player.pos[1]))

                        if distToPlayer < self.game.screen_width / 8:
                            self.shootCountdown = 60
                            self.walking = 0

                    elif self.weapon == 'staff':
                    
                        x1, y1 = self.pos[0], self.pos[1]
                        x2, y2 = self.game.player.pos[0], self.game.player.pos[1]
                    
                        xDist = x2 - x1
                        yDist = y2 - y1
                        clear = True
                        self.staffCooldown = 120
                        for n in range(10):
                            x = int((x1 + (n/10) * xDist) // 16)
                            y = int((y1 + (n/10) * yDist) // 16)
                            loc = str(x) + ';' + str(y)
                            if loc in self.game.tilemap.tilemap:
                                clear = False
                                
                        if clear:
                            self.shootCountdown = 60
                            self.walking = 0
                       
            super().update(tilemap, movement = movement)

            #If flying and land on ground, stop flying
            if not self.gravityAffected and self.collisions['down']:
                if tilemap.solid_check([self.rect().center[0], self.rect().center[1] + tilemap.tilesize],returnValue = 'bool'):
                    self.gravityAffected = True
                    self.flying = 0

            if not self.gravityAffected and random.random() < 0.1:
                self.game.sparks.append(Spark(self.rect().midbottom, random.random() * math.pi, random.random() * 2, color = random.choice(self.colours)))

            #Setting animation type
            if self.action == 'jump':
                if self.collisions['down']:
                    self.set_action('idle')
            if self.action not in ['shooting', 'jump']:
                if movement[0] != 0 or self.flying:
                    self.set_action('run')
                    
                else:
                    self.set_action('idle')
                
        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()) and (self.game.powerLevel >= self.difficultyLevel):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, redCogCount = self.redCogCount, blueCogCount = self.blueCogCount, purpleCogCount = self.purpleCogCount, heartFragmentCount = self.heartFragmentCount, eyeCount = self.eyeCount)
                return True

            
    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

        if self.game.caveDarkness:
            self.game.darknessCircle(0, 30, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))

        if self.action != 'grace':
            yOffset = (4 if self.weapon == 'staff' else 0) + (3 if (self.weapon == 'staff' and self.shootCountdown) else 0)

            if self.flip_x:
                xpos = self.rect().centerx - 2 - self.game.assets['weapons/' + self.weapon][self.weaponIndex].get_width() - offset[0]
                ypos = self.rect().centery - offset[1] - yOffset
                surface.blit(pygame.transform.flip(self.game.assets['weapons/' + self.weapon][self.weaponIndex], True, False), (xpos, ypos))
            else:
                xpos = self.rect().centerx + 2 - offset[0]
                ypos = self.rect().centery - offset[1] - yOffset
                surface.blit(self.game.assets['weapons/' + self.weapon][self.weaponIndex], (xpos, ypos))

            if self.witch:
                surface.blit(pygame.transform.flip(self.game.assets['witchHat'], self.flip_x, False), [self.rect().midtop[0] - offset[0] - 7, self.rect().midtop[1] - offset[1] - 7])


class Portal(physicsEntity):
    def __init__(self, game, pos, size, destination):
        super().__init__(game, 'portal' + str(destination), pos, size)
        self.anim_offset = (0, 0)
        self.destination = destination
        self.lightSize = 0
        self.colours = {
            'lobby': [(58, 6, 82), (111, 28, 117)],
            'normal': [(58, 6, 82), (111, 28, 117)],
            'grass': [(36, 120, 29), (12, 62, 8)],
            'spooky': [(55, 20, 15), (108, 50, 40)],
            'rubiks': [(255, 255, 255), (255, 255, 0), (255, 0, 0), (255, 153, 0), (0, 0, 255), (0, 204, 0)],
            'aussie': [(55, 20, 15)],
            'space': [(0, 0, 0), (255, 255, 255)],}
        self.colours['infinite'] = [colour for colours in self.colours.values() for colour in colours]
        
        if self.game.currentLevel == 'lobby':
            self.set_action('active')
            self.lightSize = 40

    def update(self, game):
        self.animation.update()
        #Changing state/action
        
        if self.action == 'idle' and (len(self.game.enemies) + len(self.game.bosses)) == 0:
            self.set_action('opening')
            
        if self.action == 'opening':
            self.lightSize += 0.5
            if self.animation.done:
                self.set_action('active')

        #Decals
        if self.action in ['opening', 'active']:
            if random.random() < (0.1 + (0.1 if self.action == 'active' else 0)):
                angle = (random.random()) * 2 * math.pi
                speed = random.random() * (3 if self.action == 'active' else 2)
                self.game.sparks.append(Spark(self.rect().center, angle, speed, color = random.choice(self.colours[self.destination])))

        #Collision and level change
        playerRect = self.game.player.rect()
        if self.rect().colliderect(playerRect) and self.action == 'active' and self.game.transition == 0:
            if not self.game.infiniteModeActive or self.game.interractionFrameZ:
                if self.destination == 'infinite':
                    self.game.infiniteModeActive = True    
                else: 
                    self.game.infiniteModeActive = False       
                self.game.transitionToLevel(self.destination)

            else:
                xpos = 2 * (self.rect().centerx - self.game.render_scroll[0])
                ypos = 2 * (self.rect().centery - self.game.render_scroll[1]) - 30
                self.game.draw_text('(z)', (xpos, ypos), self.game.text_font, (255, 255, 255), (0, 0), mode = 'center', scale = 0.75)
            

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)
    
        if self.game.caveDarkness and self.action in ['opening', 'active']:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))              


class Player(physicsEntity):

    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0

        self.total_jumps = 1
        self.jumps = self.total_jumps

        self.wall_slide = False
        self.lastCollidedWall = False

        self.spark_timer = 0
        self.spark_timer_max = 60
        self.gravityAffected = True
        self.nearestEnemy = False
        self.damageCooldown = 0
        self.lightSize = 90
        self.anim_offset = (-3, -6)

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        self.lightSize = 90 + self.game.wallet['eyes'] if 90 + self.game.wallet['eyes'] < 250 else 500
        self.air_time += 1
        
        if self.damageCooldown:
            self.damageCooldown = max(self.damageCooldown - 1, 0) 
        
        if self.spark_timer:
            self.spark_timer = max(self.spark_timer - 1, 0)
        
        if self.collisions['down']:
            if self.air_time > 20 and not self.spark_timer and not self.game.transition:
                self.spark_timer = self.spark_timer_max
                for _ in range(5):
                    angle = (random.random()) * math.pi
                    speed = random.random() * (2)
                    extra = 2 if abs(self.dashing) > 40 else 0
                    self.game.sparks.append(Spark((self.rect().centerx, self.rect().bottom), angle, speed + extra, color = (190, 200, 220)))
            self.air_time = 0
            self.jumps = self.total_jumps

        if self.collisions['up'] and not self.spark_timer and self.dashing and not self.game.transition:
            self.spark_timer = self.spark_timer_max
            for _ in range(5):
                angle = (random.random()) * math.pi
                speed = random.random() * (2)
                extra = 2 if self.dashing else 0
                self.game.sparks.append(Spark((self.rect().centerx, self.rect().top), angle, speed + extra, color = (190, 200, 220)))
          
        self.wall_slide = False
        if (self.collisions['left'] or self.collisions['right']) and self.air_time > 5:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)

            if self.collisions['right']:
                self.flip_x = False
            else:
                self.flip_x = True

            self.set_action('wall_slide')
            self.air_time = 5
            
            if self.dashing and not self.spark_timer and not self.game.transition:
                self.spark_timer = self.spark_timer_max
                for _ in range(5):
                    angle = (random.random() - 0.5) * math.pi + (math.pi if self.collisions['right'] else 0)
                    speed = random.random() * (2)
                    extra = 2
                    self.game.sparks.append(Spark(((self.rect().left if self.collisions['left'] else self.rect().right), self.rect().centery), angle, speed + extra, color = (190, 200, 220)))
            
        if not self.wall_slide:
            if self.air_time > 5:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
  
        if abs(self.dashing) > 50:
            
            self.downwards = self.game.movement[3] - self.game.movement[2]
            
            self.sideways = self.game.movement[1] - self.game.movement[0]
            if self.sideways == 0 and not self.downwards:
                self.sideways = 1 - 2 * self.flip_x   

            #Set dashing vel. and normalise for diagonal movement
            self.velocity[1] = self.downwards * 8 / (math.sqrt(2) if self.sideways else 1)
            self.velocity[0] = self.sideways * 8 / (math.sqrt(2) if self.downwards else 1)
            
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
                self.velocity[1] *= 0.1
                    
            if self.game.transition < 1:
                p_velocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
                self.game.particles.append(Particle(self.game, 'particle' + str(self.game.powerLevel), self.rect().center, vel=[movement[0] + random.random(), movement[1] + random.random()], frame = random.randint(0,7)))

            #Breaking cracked tiles:
            if any(self.collisions.values()) and self.game.wallet['hammers'] > 0:
                if self.lastCollidedWall['type'] == 'cracked':
                    
                    #Find correct tunnel:
                    for tunnelName in self.game.tunnelsBroken.keys():
                        if any(loc == self.lastCollidedWall['pos'] for loc in self.game.tunnelPositions[tunnelName]):
                            
                            #Actually break all the tiles and save tunnel as broken:
                            for loc in self.game.tunnelPositions[tunnelName]:
                                del self.game.tilemap.tilemap[str(loc[0]) + ';' + str(loc[1])]
                                self.game.sparks.append(Spark((loc[0] * self.game.tilemap.tilesize, loc[1] * self.game.tilemap.tilesize), random.random() * math.pi * 2, random.random() * 5))

                            self.game.tunnelsBroken[tunnelName] = True

                    self.game.wallet['hammers'] -= 1

        

        elif abs(self.dashing) in {60, 50}:
            if self.game.transition < 1:
                for _ in range(20):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 0.5 + 0.5
                    p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                    self.game.particles.append(Particle(self.game, 'particle' + str(self.game.powerLevel), self.rect().center, vel=p_velocity, frame = random.randint(0,7)))

        elif abs(self.dashing) == 1:
            self.game.sfx['dashClick'].play()
            for _ in range(20):
                angle = random.random() * 2 * math.pi
                speed = random.random() * 1.5
                p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle' + str(self.game.powerLevel), self.rect().center, vel=p_velocity, frame = random.randint(0,7)))


        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        elif self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)


        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surface, offset = (0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        
        if abs(self.dashing) <= 50 and self.game.transition < 1:
            super().render(surface, offset = offset)
        
        if self.game.caveDarkness and self.game.transition <= 0:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))


    def jump(self):
        if self.wall_slide:
            self.velocity[1] = -2.3
            self.air_time = 5
            self.jumps = max(0, self.jumps - 1)

            self.velocity[0] = -1.5 + 3*self.flip_x
            for _ in range(5):
                    angle = (random.random() + 1 + self.flip_x) * (math.pi / 4)
                    speed = random.random() * (2)
                    
                    self.game.sparks.append(Spark((self.rect().centerx, self.rect().bottom), angle, speed, color = (190, 200, 220)))
            return True

        elif self.jumps > 0 and abs(self.dashing) < 50:
            self.jumps -= 1
            self.velocity[1] = min(self.velocity[1], -3)
            self.air_time = 5
            for _ in range(5):
                    angle = (random.random()) * math.pi
                    speed = random.random() * (2)
                    self.game.sparks.append(Spark((self.rect().centerx, self.rect().bottom), angle, speed, color = (190, 200, 220)))
            return True

    def dash(self):
        if not self.dashing and not self.game.dead:
            self.spark_timer = 0
            self.game.sfx['dash'].play()
            if self.flip_x:
                self.dashing = -self.dash_dist
            else:
                self.dashing = self.dash_dist

    def updateNearestEnemy(self):
        distance = 10000
        returnEnemy = False
        for enemy in self.game.enemies:
            if np.linalg.norm((self.pos[0] - enemy.pos[0], self.pos[1] - enemy.pos[1])) < distance:
                returnEnemy = enemy
                distance = np.linalg.norm((self.pos[0] - enemy.pos[0], self.pos[1] - enemy.pos[1]))

            #Remove enemy if it got out of bounds.
            if enemy.pos[0] < 0 or enemy.pos[0] > self.game.tilemap.mapSize*16 or enemy.pos[1] < 0 or enemy.pos[1] > self.game.tilemap.mapSize*16:
                self.game.enemies.remove(enemy)
                print('removing enemy ',enemy.type, ' at ', enemy.pos) #debug
                print('bounds: ', 0,0, ",",self.game.tilemap.mapSize*16, self.game.tilemap.mapSize*16)      
        self.nearestEnemy = returnEnemy

    def damage(self, damageAmount, type):
        if not self.damageCooldown:
            self.damageCooldown = 60
            self.game.damagedBy = type

            if self.game.temporaryHealth:
                self.game.temporaryHealth -= 1
            else:
                self.game.health = max(0, self.game.health - damageAmount)
            self.game.sfx['hit'].play()

            if self.game.health == 0:
                self.game.screenshake = max(50, self.game.screenshake)
                for _ in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.game.player.rect().center, angle, 2 + random.random(), color = (200,0,0)))
                        self.game.particles.append(Particle(self.game, 'particle' + str(self.game.powerLevel), self.game.player.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
                self.game.dead += 1
                self.game.deathCount += 1

                nameVowel = True if self.game.enemyNames[type][0].lower() in ['a', 'e', 'i', 'o', 'u'] else False
                randomVerb = random.choice(self.game.deathVerbs)
                self.game.deathMessage = 'You were ' + randomVerb + ' by a' + ('n ' if nameVowel else ' ') + self.game.enemyNames[type]
                for currency in self.game.wallet:
                    if currency not in self.game.notLostOnDeath:
                        lostAmount = math.floor(self.game.wallet[currency] * 0.25) if self.game.currentLevel != 'infinite' else 0
                        self.game.wallet[currency] -= lostAmount
                        self.game.walletLostAmount[currency] = lostAmount

                    if self.game.currentLevel == 'infinite':
                        self.game.walletGainedAmount[currency] = int(self.game.walletTemp[currency] / 2)

            else:
                self.game.screenshake = max(5, self.game.screenshake)
                for _ in range(10):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.game.player.rect().center, angle, 2 + random.random(), color = (100,0,0)))
                        self.game.particles.append(Particle(self.game, 'particle' + str(self.game.powerLevel), self.game.player.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))


class Currency(physicsEntity):
    def __init__(self, game, currencyType, pos, size = (6,6)):
        super().__init__(game, currencyType, pos, size)

        self.velocity = [2 * (random.random()-0.5), random.random() - 2]
        self.value = 1
        self.currencyType = currencyType
        self.size = list(size)
        self.gravityAffected = True
        self.lightSize = 5
        self.oldEnough = 30
        
        self.animation.img_duration += (self.animation.img_duration*random.random()) 
        
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        if abs(self.velocity[0]) > 1:
            self.velocity[0] *= 0.98
        else:
            self.velocity[0] *= 0.95

        if self.oldEnough:
            self.oldEnough = max(0, self.oldEnough - 1)

        if not self.oldEnough and np.linalg.norm((self.pos[0] - self.game.player.pos[0] - self.game.player.size[0] / 2, self.pos[1] - self.game.player.pos[1] - self.game.player.size[1] / 2)) < 15:
            if self.pos[0] - self.game.player.pos[0] > 0:
                self.velocity[0] = max(self.velocity[0]-0.1, -0.5)
            else:
                self.velocity[0] = min(self.velocity[0]+0.1, 0.5)

        #Check for player collision
        if self.game.player.rect().colliderect(self.rect()) and not self.oldEnough:
            if self.game.currentLevel == 'lobby':
                self.game.wallet[str(self.currencyType) + 's'] += self.value
            else:
                self.game.walletTemp[str(self.currencyType) + 's'] += self.value
            self.game.check_encounter(self.currencyType + 's')
            self.game.sfx['coin'].play()
            return True
    
    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)
        if self.game.caveDarkness:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2 - 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2 - 2))


class Glowworm(physicsEntity):
    def __init__(self, game, pos, size = (5,5)):
        super().__init__(game, 'glowworm', pos, size)

        #All spawn at the same point with 0 vel.
        self.velocity = [(random.random()-0.5), -1.5]
        self.size = list(size)
        self.gravityAffected = False
        self.collideWallCheck = False
        self.hoverDistance = 30
        self.anim_offset = (0, 0)
        self.animation.img_duration += (self.animation.img_duration*random.random())  
        self.direction = [random.random(), random.random()]      


    def update(self, tilemap, movement = (0, 0)):
       #They will go towards a priority entity.
        if random.random() < 0.05:
            directionExtra = [0, 0]
            checkPortal = True

            if len(self.game.bosses) > 0:
                for boss in self.game.bosses:

                    if boss.glowwormFollow:
                        checkPortal = False

                        if np.linalg.norm((self.pos[0] - boss.pos[0], self.pos[1] - boss.pos[1])) > self.hoverDistance:
                            directionExtra = [self.pos[0] - boss.pos[0], self.pos[1] - boss.pos[1]]
                        else:
                            directionExtra = [0, 0]

                        break

            elif len(self.game.enemies) > 0 and self.game.player.nearestEnemy:
                checkPortal = False
                enemy = self.game.player.nearestEnemy
                
                if np.linalg.norm((self.pos[0] - enemy.pos[0], self.pos[1] - enemy.pos[1])) > self.hoverDistance:
                    directionExtra = [self.pos[0] - enemy.pos[0], self.pos[1] - enemy.pos[1]]
                    
                else:
                    directionExtra = [0, 0]
                    

            #Second priority go to character with new dialogue
            elif len(self.game.characters) > 0:
                for character in self.game.characters:
                    if character.newDialogue:
                        checkPortal = False
                        if np.linalg.norm((self.pos[0] - character.pos[0], self.pos[1] - character.pos[1])) > self.hoverDistance:
                            directionExtra = [self.pos[0] - character.pos[0], self.pos[1] - character.pos[1]]
                            break
                    else:
                        directionExtra = [0, 0]
                        

            #Third priority go to active portal
            if len(self.game.portals) > 0 and checkPortal:
                portal = random.choice(self.game.portals)
                for p in self.game.portals:
                    if p.destination == 'infinite':
                        portal = p
                if np.linalg.norm((self.pos[0] - portal.pos[0], self.pos[1] - portal.pos[1])) > self.hoverDistance:
                    directionExtra = [self.pos[0] - portal.pos[0], self.pos[1] - portal.pos[1]]
                else:
                    directionExtra = [0, 0]
                 
            extraLength = np.linalg.norm(directionExtra)

            if extraLength > 0:
                directionExtra /= (np.linalg.norm(directionExtra) * 3)
            self.direction = [random.random() - 0.5 - directionExtra[0], random.random() - 0.5 - directionExtra[1]]
          
        self.pos[0] += self.direction[0] + (random.random() - 0.5)
        self.pos[1] += self.direction[1] + (random.random() - 0.5)
        
        super().update(tilemap, movement = movement)


    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)
        if self.game.caveDarkness:
            self.game.darknessCircle(0, 6, (int(self.pos[0]) - self.game.render_scroll[0] + self.animation.img().get_width() / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.animation.img().get_height() / 2))


class Bullet():
    def __init__(self, game, pos, speed, origin, type = 'projectile'):
        self.attackPower = 1

        self.pos = list(pos)
        self.game = game
        self.speed = list(speed)
        self.type = type
        self.origin = origin
        self.img = self.game.assets[self.type]
        self.anim_offset = (-2, 0)

    
    def update(self, game):
        self.game.display_outline.blit(self.img, (self.pos[0] - self.img.get_width() / 2 - self.game.render_scroll[0], self.pos[1] - self.img.get_height() / 2 - self.game.render_scroll[1]))
        
        if not self.game.paused:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]
       
        #Check to destroy
        if self.game.tilemap.solid_check(self.pos):
            if self.type == 'projectile':
                for _ in range(4):
                    self.game.sparks.append(Spark(self.pos, random.random() - 0.5 + (math.pi if self.speed[0] > 0 else 0), 2 + random.random()))
            return True
        
        #Check for player collision:
        if self.game.player.rect().collidepoint(self.pos) and abs(self.game.player.dashing) < 50:
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.origin)
                return True

        if self.game.caveDarkness and self.type == 'projectile':
            self.game.darknessCircle(0, 15, (int(self.pos[0]) - self.game.render_scroll[0] + (1 if self.speed[0] < 0 else -1), int(self.pos[1]) - self.game.render_scroll[1]))


class RolyPoly(physicsEntity):
    def __init__(self, game, pos, size, initialFall = True):
        super().__init__(game, 'rolypoly', pos, size)

        self.attackPower = 1
        self.cogCount = random.randint(0,3)
        self.eyeCount = random.randint(1,5)  

        self.deathIntensity = 10

        self.size = list(size)
        self.speed = round(random.random() * 0.5 + 0.5, 2)
        self.gravityAffected = initialFall
        self.collideWallCheck = True
        self.collideWall = False
        self.anim_offset = (0, 0)
        self.heading = [-self.speed if random.random() < 0.5 else self.speed, 0]
        self.wallSide = [0, self.speed]
        self.timeSinceTurn = 0
        self.pos[1] += 5
        self.pos[0] += random.randint(0, 4)
        self.grace = random.randint(120,180)
        self.animation.img_duration += (self.animation.img_duration*random.random()) 


    def update(self, tilemap, movement = (0, 0)):         
        super().update(tilemap, movement = movement) 

        if self.gravityAffected:
            if any(self.collisions.values()):
                self.set_action('run')
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.gravityAffected = False
                self.grace = 0
                self.pos[1] -= 4

        if self.grace:
            self.grace = max(self.grace - 1, 0)
            if self.grace == 0:
                self.set_action('run')
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
        
        elif self.action != 'idle':
            if self.timeSinceTurn < 5:
                self.timeSinceTurn += 1                     

            # Change direction if it leaves a tileblock:
            if not any(x == True for x in self.collisions.values()) and self.timeSinceTurn > 3:  
                self.wallSide, self.heading = [-self.heading[0], -self.heading[1]], self.wallSide
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.timeSinceTurn = 0
                
            #Also change direction if run into a wall:
            elif any(self.collisions.values()) and self.timeSinceTurn > 3:
                self.wallSide, self.heading = self.heading, [-self.wallSide[0], -self.wallSide[1]]
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.timeSinceTurn = 0

        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, eyeCount = self.eyeCount)
                return True
            
        #Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, eyeCount = self.eyeCount)
                self.game.projectiles.remove(projectile)
                return True
            
        #Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'idle':
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)
                

    def render(self, surface, offset = (0, 0)):
        # pygame.draw.rect(self.game.HUDdisplay, (255,0,0), (2*(self.rect().x - self.game.render_scroll[0] - self.anim_offset[0]), 2*(self.rect().y - self.game.render_scroll[1] - self.anim_offset[1]), self.size[0]*2, self.size[1]*2))
        
        super().render(surface, offset = offset)
       

class SpawnPoint(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spawnPoint', pos, size)

        self.gravityAffected = False
        self.collideWallCheck = False
        self.collideWall = False
        self.set_action('active' if self.pos == self.game.spawnPoint else 'idle')

        self.anim_offset = [0,-1]


    def update(self, tilemap, movement = (0, 0)):         
        super().update(tilemap, movement = movement)  

        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) > 50 and self.action == 'idle':
            for point in self.game.spawnPoints:
                if point.action == 'active':
                    point.set_action('idle')
            
            self.set_action('active')
            self.game.spawnPoint = self.pos[:]
            self.game.sfx['ding'].play()
            self.game.check_encounter('spawnPoints')

        if self.action == 'active':
            if random.random() < 0.05:
                angle = (random.random() + 1) * math.pi
                speed = random.random() * 3
                self.game.sparks.append(Spark(self.rect().center, angle, speed, color = random.choice([(58, 6, 82), (111, 28, 117)])))

class HeartAltar(physicsEntity):
    def __init__(self, game, pos, size, action = 'active'):
        super().__init__(game, 'heartAltar', pos, size)

        self.gravityAffected = False
        self.collideWallCheck = False
        self.collideWall = False
        self.set_action(action)

        self.anim_offset = [0, 0]
        self.animation.img_duration += (self.animation.img_duration*random.random()) 


    def update(self, tilemap, movement = (0, 0)):         
        super().update(tilemap, movement = movement)  

        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) > 50 and self.action == 'active':
            self.game.check_encounter('heartAltars')

            if self.game.health < self.game.maxHealth:
                self.game.health += 1
                self.set_action('idle')
                self.game.sfx['ding'].play()
                

class Torch(physicsEntity):
    def __init__(self, game, pos, size, action = 'idle'):
        super().__init__(game, 'torch', pos, size)
        self.gravityAffected = False
        self.collideWallCheck = False
        self.collideWall = False
        self.lightSize = 50
        self.anim_offset = (0, 0)
        self.animation.img_duration += (self.animation.img_duration*random.random()) 
        
        #Check for flip:
        left = self.game.tilemap.solid_check([self.pos[0] - self.game.tilemap.tilesize, self.pos[1]], returnValue = 'bool')
        right = self.game.tilemap.solid_check([self.pos[0] + self.game.tilemap.tilesize, self.pos[1]], returnValue = 'bool')
        if left and not right:
            self.flip_x = True
        elif left and right and random.random() < 0.5:
            self.flip_x = True


    def update(self, tilemap, movement = (0, 0)):         
        super().update(tilemap, movement = movement)  

        if self.game.caveDarkness:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2)) 

        if random.random() < 0.05:
            self.game.sparks.append(Spark([self.rect().x + (4 if self.flip_x else 12), self.pos[1]], random.random() * math.pi + math.pi, random.random() + 1, color = random.choice([(229, 0, 0), (229, 82, 13)])))
             
            
class Spider(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spider', pos, size)

        self.cogCount = random.randint(0,3)
        self.heartFragmentCount = (1 if random.random() < 0.2 else 0)
        self.chitinCount = random.randint(0, 3)
        self.attackPower = 1
        self.deathIntensity = 10
        
        self.grace = random.randint(90,210)
        self.graceDone = False
        self.gravityAffected = False
        self.set_action('grace')
        self.anim_offset = [-3, -3]
        self.pos[0] += 4
        self.pos[1] += 5
        self.timer = 0
        self.toPlayer = [0, 0]
        self.facing = [random.random() - 0.5, random.random() - 0.5]
        
    
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        
        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(30,90)             
                self.graceDone = True
            self.animation.update()

        if self.graceDone:
            if self.action == 'idle':
                self.timer = max(self.timer - 1, 0)

                if not self.timer:
                    self.set_action('run')
                    toPlayer = (self.game.player.pos[0] - self.pos[0] + 4, self.game.player.pos[1] - self.pos[1] + 5)
                    self.toPlayer = toPlayer / np.linalg.norm(toPlayer) 
                    self.velocity = [self.toPlayer[0] * 0.2, self.toPlayer[1] * 0.2]

                    self.velocity[0] += random.random() - 0.5
                    self.velocity[1] += random.random() - 0.5

                    self.facing[0] = self.velocity[0]
                    self.facing[1] = self.velocity[1]

                    self.timer = random.randint(30,90)
                    
            elif self.action == 'run':
                self.timer = max(self.timer - 1, 0)

                if self.timer == 0:
                    self.velocity = [0, 0]
                    self.timer = random.randint(10, 30)
                    self.set_action('idle')
                
        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, chitinCount = self.chitinCount)
                return True
            
        #Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, chitinCount = self.chitinCount)
                self.game.projectiles.remove(projectile)
                return True

        #Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'grace':
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)


    def render(self, surface, offset = (0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        angle = 0
        angle = math.atan2(-self.facing[1], self.facing[0]) - math.pi / 2
           
        super().render(surface, offset = offset, rotation = angle)


class RubiksCube(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'rubiksCube', pos, size)

        self.cogCount = random.randint(0,3)
        self.redCogCount = 0
        self.blueCogCount = 0
        self.heartFragmentCount = (1 if random.random() < 0.2 else 0)
        self.attackPower = 1
        self.deathIntensity = 10
        
        self.grace = random.randint(90,210)
        self.graceDone = False
        self.gravityAffected = False
        self.anim_offset = [0, 0]  
        self.canMoveVectors = []
        self.speed = 1
        self.maxSpeed = 3
        self.states = ['white', 'yellow', 'blue', 'green', 'red', 'orange']
    
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        
        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action(random.choice(self.states))
                self.timer = random.randint(120,300)             
                self.graceDone = True
                if self.action == 'red':
                    self.redCogCount = random.randint(1, 5)
                elif self.action == 'blue':
                    self.blueCogCount = random.randint(1, 5)
                    
            self.animation.update()

        if self.graceDone:
            if self.timer:
                self.timer = max(self.timer - 1, 0)

                #When timer runs out, move in a random direction until hit a wall
                #Then change colour and reset timer.
                if not self.timer:
                    #Find random directions that entity can move in
                    self.canMoveVectors = []
                    posCentre = [self.rect().centerx, self.rect().centery]

                    #left:
                    if not tilemap.solid_check([posCentre[0] - tilemap.tilesize, posCentre[1]],returnValue = 'bool'):
                        self.canMoveVectors.append([-self.speed, 0])
                    #right:
                    if not tilemap.solid_check([posCentre[0] + tilemap.tilesize, posCentre[1]],returnValue = 'bool'):
                        self.canMoveVectors.append([self.speed, 0])
                    #up:
                    if not tilemap.solid_check([posCentre[0], posCentre[1] - tilemap.tilesize],returnValue = 'bool'):
                        self.canMoveVectors.append([0, -self.speed])
                    #down:
                    if not tilemap.solid_check([posCentre[0], posCentre[1] + tilemap.tilesize],returnValue = 'bool'):
                        self.canMoveVectors.append([0, self.speed])
       
                    #Set velocity to that direction
                    self.velocity = random.choice(self.canMoveVectors)
            else:
                self.velocity[0] = max(min(self.velocity[0] * 1.02, self.maxSpeed), -self.maxSpeed)
                self.velocity[1] = max(min(self.velocity[1] * 1.02, self.maxSpeed), -self.maxSpeed)
                
            #When hit a tile, stop and change colour, repeat
            if any(self.collisions.values()):
                self.timer = random.randint(120,300)
                self.velocity = [0, 0]
                self.set_action(random.choice(self.states))

                self.redCogCount, self.blueCogCount = 0, 0
                if self.action == 'red':
                    self.redCogCount = random.randint(1, 5)
                elif self.action == 'blue':
                    self.blueCogCount = random.randint(1, 5)
                
                
                
        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, redCogCount = self.redCogCount, blueCogCount = self.blueCogCount, heartFragmentCount = self.heartFragmentCount)
                return True
            
        #Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, redCogCount = self.redCogCount, blueCogCount = self.blueCogCount, heartFragmentCount = self.heartFragmentCount)
                self.game.projectiles.remove(projectile)
                return True

        #Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'idle':
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)


class Kangaroo(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'kangaroo', pos, size)

        self.cogCount = random.randint(0,3)
        self.heartFragmentCount = (1 if random.random() < 0.3 else 0)
        self.fairyBreadCount = random.randint(0, 4)
        self.boxingGloveCount = random.randint(0, 3)
        self.attackPower = 1
        self.deathIntensity = 10
        
        self.grace = random.randint(90,210)
        self.graceDone = False
        self.gravityAffected = True
        self.set_action('grace')
        self.anim_offset = [0, 0]
        self.timer = 0
        self.timeSinceBounce = 0
        self.flip_x = True if random.random() < 0.5 else False
        
    
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        
        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(30,90)             
                self.graceDone = True
            self.animation.update()

        if self.graceDone:
            if self.action == 'idle':
                self.timer = max(self.timer - 1, 0)

                if not self.timer:
                    self.set_action('prep')
                    self.timer = random.randint(30,60)


            if self.action == 'prep':
                self.timer = max(self.timer - 1, 0)

                if not self.timer:
                    ###JUMP ROUGHLY IN DIRECTION OF PLAYER
                    self.set_action('jumping')
                    if self.pos[0] < self.game.player.pos[0]:
                        self.flip_x = False
                    else:
                        self.flip_x = True
                    
                    self.velocity[0] = -(random.random() + 1.5) if self.flip_x else (random.random() + 1.5)
                    self.velocity[1] = -(random.random() * 2.5 + 1)
                    self.timeSinceBounce = 0
                    self.timer = random.randint(120,300)
                    
            elif self.action == 'jumping':
                self.timer = max(self.timer - 1, 0)
                self.timeSinceBounce = min(self.timeSinceBounce + 1, 10)
                self.velocity[0] *= 0.99
                self.velocity[1] *= 0.99

                if self.collisions['left'] or self.collisions['right'] and self.timeSinceBounce >= 10:
                    self.timeSinceBounce = 0
                    self.velocity[0] = -self.velocity[0]
                    self.flip_x = not self.flip_x

                if self.collisions['down']:
                    posCentre = [self.rect().centerx, self.rect().centery]
                    if tilemap.solid_check([posCentre[0], posCentre[1] + tilemap.tilesize], returnValue = 'bool'):
                        self.velocity = [0, 0]

                        self.timer = random.randint(90, 120)
                        self.set_action('idle')                    
                
        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, fairyBreadCount = self.fairyBreadCount, boxingGloveCount = self.boxingGloveCount)
                return True
            
        #Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, fairyBreadCount = self.fairyBreadCount, boxingGloveCount = self.boxingGloveCount)
                self.game.projectiles.remove(projectile)
                return True

        #Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'grace':
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)


class Echidna(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'echidna', pos, size)

        self.cogCount = random.randint(0,3)
        self.heartFragmentCount = (1 if random.random() < 0.3 else 0)
        self.fairyBreadCount = random.randint(0, 4)
        self.attackPower = 1
        self.deathIntensity = 10
        
        self.grace = random.randint(90,210)
        self.graceDone = False
        self.gravityAffected = True
        self.set_action('grace')
        self.anim_offset = [0, 0]
        self.timer = 0
        self.flip_x = True if random.random() < 0.5 else False
        
    
    def update(self, tilemap, movement = (0, 0)):
        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(30,90)             
                self.graceDone = True
            self.animation.update()

        if self.graceDone:
            if self.action == 'idle':
                self.timer = max(self.timer - 1, 0)

                if not self.timer:
                    self.set_action('walking')
                    self.timer = random.randint(120,180)
                    self.velocity = [-random.random() if self.flip_x else random.random(), 0]

                elif random.random() < 0.005:
                    self.set_action('charging')
                    self.velocity = [0, 0]

            if self.action == 'walking':
                self.timer = max(self.timer - 1, 0)

                floorCheck = tilemap.solid_check((self.rect().centerx + (-8 if self.flip_x else 8), self.rect().centery + 16))

                if self.collisions['left'] or self.collisions['right'] or not floorCheck:

                    self.flip_x = not self.flip_x
                    self.set_action('idle')
                    self.timer = random.randint(120,180) 
                    self.velocity = [0, 0]

                elif random.random() < 0.005:
                    self.set_action('charging')
                    self.velocity = [0, 0]
                    
            elif self.action == 'charging':
                #When animation finishes, shoot spines in random directions and go to idle.
                if self.animation.done:

                    for _ in range(10):
                        angle = random.random() * math.pi + math.pi
                        spineVelocity = [2*math.cos(angle), 2*math.sin(angle)]
                        self.game.projectiles.append(Bullet(self.game, [self.rect().centerx, self.rect().centery], spineVelocity, 'echidna', type = 'spine'))
                    self.game.projectiles.append(Bullet(self.game, [self.rect().centerx, self.rect().centery], [2, 0], 'echidna', type = 'spine'))
                    self.game.projectiles.append(Bullet(self.game, [self.rect().centerx, self.rect().centery], [-2, 0], 'echidna', type = 'spine'))
                    self.set_action('idle')  
                    self.timer = random.randint(120,180)                
                
        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, fairyBreadCount = self.fairyBreadCount)
                return True
            
        #Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, fairyBreadCount = self.fairyBreadCount)
                self.game.projectiles.remove(projectile)
                return True

        #Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'grace':
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)
        
        super().update(tilemap, movement = movement)



class Meteor(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'meteor', pos, size)

        self.attackPower = 1

        self.gravityAffected = False
        self.collideWallCheck = False
        self.set_action('idle')
        self.anim_offset = [0, 0]  
        self.angle = random.random() * 2 * math.pi   
    
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)  

        if self.action == 'idle':
            if self.animation.done:
                self.set_action('kaboom')

        elif self.action == 'kaboom':
            #Check for player collision:
            if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.animation.frame > 10:
                if not self.game.dead:
                    self.game.player.damage(self.attackPower, self.type)
            
            if self.animation.done:
                return True
            
    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset, rotation = self.angle)

class AlienShip(physicsEntity):
    def __init__(self, game, pos, size, graceDone = False, velocity = [0, 0]):
        super().__init__(game, 'alienship', pos, size)

        self.cogCount = random.randint(0,3)
        self.heartFragmentCount = (1 if random.random() < 0.2 else 0)
        self.purpleCogCount = (1 if random.random() < 0.2 else 0)

        self.attackPower = 1
        self.deathIntensity = 10

        self.gravityAffected = False
        self.grace = random.randint(90,210)
        self.graceDone = graceDone
        self.set_action('idle')
        if self.graceDone:
            self.set_action('flying')
            self.velocity = velocity

        self.anim_offset = [0, -1]
        self.pos[1] += 9
        self.pos[0] += 4
        
    
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
         
        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('flying')
                self.velocity = [random.random() - 1/2, random.random()*0.5 + 0.5]                
                self.graceDone = True
                   
            self.animation.update()

        if self.graceDone:
            if self.collisions['up'] or self.collisions['down']:
                self.velocity[1] = -self.velocity[1]
            elif self.collisions['left'] or self.collisions['right']:
                self.velocity[0] = -self.velocity[0]

            if any(self.collisions.values()) and random.random() < 0.1:
                toPlayer = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                norm = np.linalg.norm(toPlayer) * random.uniform(1.2, 1.5)

                if not (tilemap.solid_check((self.rect().centerx + 8, self.rect().centery)) and tilemap.solid_check((self.rect().centerx - 8, self.rect().centery))):
                    self.velocity[0] = toPlayer[0] / norm
                if not (tilemap.solid_check((self.rect().centerx, self.rect().centery + 8)) and tilemap.solid_check((self.rect().centerx, self.rect().centery - 8))):
                    self.velocity[1] = toPlayer[1] / norm
                    
        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, purpleCogCount = self.purpleCogCount)
                return True
            
        #Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, purpleCogCount = self.purpleCogCount)
                self.game.projectiles.remove(projectile)
                return True

        #Check for player collision, not dashing and in attack mode:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action == 'flying':
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)                        
                

class CreepyEyes(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'creepyeyes', pos, size)

        self.gravityAffected = False
        self.collideWallCheck = False
        self.mainPos = pos
        
        self.anim_offset = [0, 0]


    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        toPlayer = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
        self.toPlayerNorm = toPlayer / np.linalg.norm(toPlayer)

        self.pos[0] = self.mainPos[0] + round(self.toPlayerNorm[0] if abs(self.toPlayerNorm[0]) > 0.38 else 0)
        self.pos[1] = self.mainPos[1] + round(self.toPlayerNorm[1] if abs(self.toPlayerNorm[1]) > 0.38 else 0)

class TestBoss(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'testboss', pos, size)

        self.gravityAffected = True
        self.collideWallCheck = True
        self.isBoss = True

        self.deathIntensity = 25
        self.cogCount = 100

        self.health = 3
        self.maxHealth = self.health
        self.damageCooldown = 0
        
        self.anim_offset = [0, 0]

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.action == 'idle':
            distToPlayer = np.linalg.norm((self.pos[0] - self.game.player.pos[0], self.pos[1] - self.game.player.pos[1]))
            if distToPlayer < 50:
                self.set_action('active')


        elif self.action == 'active':
            if self.damageCooldown:
                self.damageCooldown = max(self.damageCooldown - 1, 0)
        
            #Death Condition
            if abs(self.game.player.dashing) >= 50 and not self.damageCooldown:
                if self.rect().colliderect(self.game.player.rect()):
                    self.health -= self.game.powerLevel
                    self.damageCooldown = 30

            if self.health <= 0:
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount)
                return True
            
class boss(physicsEntity):
    def __init__(self, game, type, pos, size):
        super().__init__(game, type, pos, size)

        self.isBoss = True
        self.glowwormFollow = True
        self.difficulty = round(self.game.floors['normal'] / 10)

        self.deathIntensity = 50
        self.cogCount = random.randint(25 + 25 * self.difficulty, 50 + 25 * self.difficulty)
        self.wingCount = 0
        self.heartFragmentCount = random.randint(5 + 10 * self.difficulty, 10 + 10 * self.difficulty)

        self.damageCooldown = 0
        self.timer = 0
        self.anim_offset = [0, 0]

    def checkDamageTaken(self, invincibleStates = [], passiveStates = []):
        #Death Condition for Boss
        if self.action not in invincibleStates:
            if abs(self.game.player.dashing) >= 50 and not self.damageCooldown:
                if self.rect().colliderect(self.game.player.rect()):
                    self.health -= 1
                    self.damageCooldown = 30
                    self.damage(intensity = 10)

            if self.health <= 0:
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, wingCount = self.wingCount, heartFragmentCount = self.heartFragmentCount)
                
                #Not zero because this boss hasnt been removed yet, but returns True in 3 lines.
                if len(self.game.bosses) == 1:
                    for enemy in self.game.enemies.copy():
                        enemy.kill(intensity = enemy.deathIntensity, creditCount = 1)
                    self.game.enemies = []
                return True
            
        #Check for player collision, not dashing and in attack mode:
        if self.game.player.rect().colliderect(self.rect()):
            if abs(self.game.player.dashing) < 50 and self.action not in passiveStates and not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)

            
class NormalBoss(boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'normalboss', pos, size)

        self.gravityAffected = False
        self.collideWallCheck = True

        self.attackRadius = int(100 * math.atan(self.difficulty / 5))
        self.wingCount = random.randint(20 + 20 * self.difficulty, 40 + 20 * self.difficulty)

        self.health = 2 + 2 * self.difficulty
        self.maxHealth = self.health

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.damageCooldown:
            self.damageCooldown = max(self.damageCooldown - 1, 0)
        if self.checkDamageTaken(invincibleStates = ['idle'], passiveStates = ['idle']):
            return True

        toPlayer = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
        norm = np.linalg.norm(toPlayer)

        if self.action == 'idle':
            if norm < 140:
                self.set_action('activating')
                self.timer = 0
                self.velocity[0] = random.random() - 0.5
                self.gravityAffected = True



        elif self.action == 'activating':
            self.timer += 1
            if self.animation.done or any(self.collisions.values()):
                self.set_action('flying')
                self.gravityAffected = False
                self.timer = 0

                self.velocity[0] = 2 * toPlayer[0] / norm
                self.velocity[1] = 2 * toPlayer[1] / norm



        elif self.action == 'flying':
            if self.health <= self.maxHealth / 2 and norm < 50 and random.random() < 0.05:
                self.set_action('attacking')

            #Head towards the player on wall impact, sometimes
            elif any(self.collisions.values()) and random.random() < 0.5:
                if not (tilemap.solid_check((self.rect().centerx + 8, self.rect().centery)) and tilemap.solid_check((self.rect().centerx - 8, self.rect().centery))):
                    self.velocity[0] = random.uniform(0.8, 1.3) * 2 * toPlayer[0] / norm
                if not (tilemap.solid_check((self.rect().centerx, self.rect().centery + 8)) and tilemap.solid_check((self.rect().centerx, self.rect().centery - 8))):
                    self.velocity[1] = random.uniform(0.8, 1.3) * 2 * toPlayer[1] / norm

            #Otherwise just bounce off
            elif self.collisions['left'] or self.collisions['right']:
                self.velocity[0] *= random.uniform(-1.2, -0.9)
            elif self.collisions['up'] or self.collisions['down']:
                self.velocity[1] *= random.uniform(-1.2, -0.9)



        elif self.action == 'attacking':

            if self.collisions['left'] or self.collisions['right']:
                self.velocity[0] *= -1
            elif self.collisions['up'] or self.collisions['down']:
                self.velocity[1] *= -1
            
            if np.linalg.norm(self.velocity) > 0.1:
                self.velocity[0] *= 0.98
                self.velocity[1] *= 0.98

            elif self.animation.done:
                self.set_action('flying')

                for _ in range(20):
                    self.game.sparks.append(Spark(self.rect().center, random.random() * 2 * math.pi, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle1', self.rect().center, vel = [math.cos(random.random() * 2 * math.pi), math.cos(random.random() * 2 * math.pi)], frame = random.randint(0,7)))

                #Check for player collision, not dashing and in attack mode:
                if norm < self.attackRadius and abs(self.game.player.dashing) < 50:
                    if not self.game.dead:
                        self.game.player.damage(self.attackPower, self.type)   

                batpos = (self.rect().center)
                for _ in range(random.randint(1, self.difficulty + 1)):
                    self.game.enemies.append(Bat(self.game, (batpos[0], batpos[1] - 4), (10, 10), graceDone = True, velocity = [3 * toPlayer[0] / norm + random.random() / 4, 3 * toPlayer[1] / norm + random.random() / 4]))

                for _ in range(5):
                    startAngle = random.random() * math.pi * 2
                    endAngle = startAngle + math.pi / 6 + random.random() * math.pi / 3
                    speed = random.random() * 2 + 1
                    redness = random.randint(150,200)
                    self.game.sparks.append(ExpandingArc(self.rect().center, self.attackRadius, startAngle, endAngle, speed, color = (redness, 0, 0), width = 5))

                self.velocity[0] = 0.5 + random.random()
                self.velocity[1] = 0.5 + random.random()


    def render(self, surface, offset = (0, 0)):
        angle = 0
        if self.action == 'activating':
            angle = self.animation.frame / 24.5
           
        super().render(surface, offset = offset, rotation = angle)

class GrassBoss(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'grassboss', pos, size)

        self.gravityAffected = True
        self.collideWallCheck = True
        self.isBoss = True

        self.deathIntensity = 25
        self.cogCount = 50

        self.health = 3
        self.maxHealth = self.health
        self.damageCooldown = 0
        
        self.anim_offset = [0, 0]

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.action == 'idle':
            pass

        elif self.action == 'activating':
            pass

        elif self.action == 'run':
            pass

class SpookyBoss(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spookyboss', pos, size)

        self.gravityAffected = True
        self.collideWallCheck = True
        self.isBoss = True

        self.deathIntensity = 25
        self.cogCount = 50

        self.health = 3
        self.maxHealth = self.health
        self.damageCooldown = 0
        
        self.anim_offset = [0, 0]

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.action == 'idle':
            pass

        elif self.action == 'activating':
            pass

        elif self.action == 'teleporting':
            pass

        elif self.action == 'attacking':
            pass

class RubiksBoss(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'rubiksboss', pos, size)

        self.gravityAffected = True
        self.collideWallCheck = True
        self.isBoss = True

        self.deathIntensity = 25
        self.cogCount = 50

        self.health = 3
        self.maxHealth = self.health
        self.damageCooldown = 0
        
        self.anim_offset = [0, 0]

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.action == 'idle':
            pass

        elif self.action == 'activating':
            pass

        elif self.action == 'run':
            pass

class AussieBoss(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'aussieboss', pos, size)

        self.gravityAffected = True
        self.collideWallCheck = True
        self.isBoss = True

        self.deathIntensity = 25
        self.cogCount = 50

        self.health = 3
        self.maxHealth = self.health
        self.damageCooldown = 0
        
        self.anim_offset = [0, 0]

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.action == 'idle':
            pass

        elif self.action == 'activating':
            pass

        elif self.action == 'run':
            pass

class SpaceBoss(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spaceboss', pos, size)

        self.gravityAffected = True
        self.collideWallCheck = True
        self.isBoss = True

        self.deathIntensity = 25
        self.cogCount = 50

        self.health = 3
        self.maxHealth = self.health
        self.damageCooldown = 0
        
        self.anim_offset = [0, 0]

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.action == 'idle':
            pass

        elif self.action == 'activating':
            pass

        elif self.action == 'flying':
            pass