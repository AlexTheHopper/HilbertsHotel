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
        self.lightSize = 0

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
        renderDistToPlayer = np.linalg.norm(self.vectorTo(self.game.player))
        if renderDistToPlayer > self.renderDistance and not self.isBoss:
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
        

    def render(self, surface, offset = (0, 0), rotation = 0, transparency = 255):
        # Only update/render at close distances
        renderDistToPlayer = np.linalg.norm(self.vectorTo(self.game.player))
        if renderDistToPlayer > self.renderDistance and not self.isBoss:
            return False

        posx = self.pos[0] - offset[0] + self.anim_offset[0]
        posy = self.pos[1] - offset[1] + self.anim_offset[1]

        image = self.animation.img()
        image.set_alpha(transparency)

        if rotation != 0:
            image = pygame.transform.rotate(image, rotation * 180 / math.pi)
            surface.blit(pygame.transform.flip(image, self.flip_x, False), (posx, posy))
        else:
            surface.blit(pygame.transform.flip(image, self.flip_x, False), (math.floor(posx), math.floor(posy)))

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
        #Need to make sure the currency wont spawn in a physics tile.
        spawnLoc = (self.pos[0] + (self.size[0] / 2) - 3, self.pos[1] + (self.size[1] / 2) - 3)

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

    def displayDarknessCircle(self):
        if self.game.caveDarkness and self.game.transition <= 0:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0] + self.size[0] / 2) - self.game.render_scroll[0], int(self.pos[1] + self.size[1] / 2) - self.game.render_scroll[1]))

    def wallRebound(self):
        if self.collisions['left'] or self.collisions['right']:
            self.velocity[0] *= -1
        elif self.collisions['up'] or self.collisions['down']:
            self.velocity[1] *= -1

    def vectorTo(self, other):
        rectO = self.rect()
        rectD = other.rect()
        return [rectD.centerx - rectO.centerx, rectD.centery - rectO.centery]

    def circularAttack(self, radius, pos = [0, 0], color = (random.randint(150, 200), 0, 0), colorStr = 'red', canDamageBoss = False):
        for _ in range(int(radius / 3)):
            startAngle = random.random() * math.pi * 2
            endAngle = startAngle + math.pi / 6 + random.random() * math.pi / 3
            speed = random.random() * 2 + 1
            if pos == [0, 0]:
                pos = self.rect().center
            self.game.sparks.append(ExpandingArc(pos, radius, startAngle, endAngle, speed, color, colorStr = colorStr, canDamageBoss = canDamageBoss, width = 5, damage = self.attackPower, type = self.type))

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
        self.anim_offset = (-3, -2)
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
                    toPlayer = self.vectorTo(self.game.player)
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
        renderDistToPlayer = np.linalg.norm(self.vectorTo(self.game.player))
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
                        self.game.enemies.append(Bat(self.game, batpos, self.game.entityInfo[4]['size'], graceDone = True, velocity = bulletVelocity))
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
                        distToPlayer = np.linalg.norm(self.vectorTo(self.game.player))

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

        self.displayDarknessCircle()

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
            'space': [(0, 0, 0), (255, 255, 255)],
            'heavenHell': [(107, 176, 255), (255, 71, 68)],}
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

                self.set_action('closing')

            else:
                xpos = 2 * (self.rect().centerx - self.game.render_scroll[0])
                ypos = 2 * (self.rect().centery - self.game.render_scroll[1]) - 30
                self.game.draw_text('(z)', (xpos, ypos), self.game.text_font, (255, 255, 255), (0, 0), mode = 'center', scale = 0.75)
            

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)
    
        self.displayDarknessCircle()

class Player(physicsEntity):

    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0

        self.total_jumps = 1
        self.jumps = self.total_jumps

        self.total_dashes = 1
        self.dashes = self.total_dashes

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
        elif self.dashing == 0:
            self.dashes = self.total_dashes
        


        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surface, offset = (0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        
        if abs(self.dashing) <= 50 and self.game.transition < 1:
            super().render(surface, offset = offset)
        
        self.displayDarknessCircle()

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
        if abs(self.dashing) <= 50 and self.dashes > 0 and not self.game.dead:
            self.spark_timer = 0
            self.dashes = max(self.dashes - 1, 0)
            self.game.sfx['dash'].play()
            if self.flip_x:
                self.dashing = -self.dash_dist
            else:
                self.dashing = self.dash_dist

    def updateNearestEnemy(self):
        distance = 10000
        returnEnemy = False
        for enemy in self.game.enemies:
            if np.linalg.norm(self.vectorTo(enemy)) < distance:
                returnEnemy = enemy
                distance = np.linalg.norm(self.vectorTo(enemy))

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
    def __init__(self, game, currencyType, pos, size = (6,6), value = 1):
        super().__init__(game, currencyType, pos, size)

        self.velocity = [2 * (random.random()-0.5), random.random() - 2]
        self.value = value
        self.currencyType = currencyType
        self.size = list(size)
        self.gravityAffected = True
        self.lightSize = 5
        self.oldEnough = 30

        self.anim_offset = (-1, random.choice([-1,-2]))
        self.animation.img_duration += (self.animation.img_duration*random.random()) 

        
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        if abs(self.velocity[0]) > 1:
            self.velocity[0] *= 0.98
        else:
            self.velocity[0] *= 0.95

        if self.oldEnough:
            self.oldEnough = max(0, self.oldEnough - 1)

        if not self.oldEnough and np.linalg.norm(self.vectorTo(self.game.player)) < 15:
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
        self.displayDarknessCircle()

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
                        toBoss = self.vectorTo(boss)

                        if np.linalg.norm(toBoss) > self.hoverDistance:
                            directionExtra = toBoss
                        else:
                            directionExtra = [0, 0]

                        break

            elif len(self.game.enemies) > 0 and self.game.player.nearestEnemy:
                checkPortal = False
                enemy = self.game.player.nearestEnemy
                toEnemy = self.vectorTo(enemy)
                
                if np.linalg.norm(toEnemy) > self.hoverDistance:
                    directionExtra = toEnemy
                    
                else:
                    directionExtra = [0, 0]
                    

            #Second priority go to character with new dialogue
            elif len(self.game.characters) > 0:
                for character in self.game.characters:
                    if character.newDialogue:
                        checkPortal = False
                        toCharacter = self.vectorTo(character)

                        if np.linalg.norm(toCharacter) > self.hoverDistance:
                            directionExtra = toCharacter
                            break
                    else:
                        directionExtra = [0, 0]
                        
            #Third priority go to active portal
            if len(self.game.portals) > 0 and checkPortal:
                portal = random.choice(self.game.portals)
                for p in self.game.portals:
                    if p.destination == 'infinite':
                        portal = p
                toPortal = self.vectorTo(portal)

                if np.linalg.norm(toPortal) > self.hoverDistance:
                    directionExtra = toPortal
                else:
                    directionExtra = [0, 0]
                 
            extraLength = np.linalg.norm(directionExtra)

            if extraLength > 0:
                directionExtra /= (np.linalg.norm(directionExtra) * 3)
            self.direction = [random.random() - 0.5 + directionExtra[0], random.random() - 0.5 + directionExtra[1]]
          
        self.pos[0] += self.direction[0] + (random.random() - 0.5)
        self.pos[1] += self.direction[1] + (random.random() - 0.5)
        
        super().update(tilemap, movement = movement)


    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)
        self.displayDarknessCircle()

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
        self.lightSize = 10

    
    def update(self, game):
        if self.game.caveDarkness and self.game.transition <= 0:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0], int(self.pos[1]) - self.game.render_scroll[1]))
        self.game.display_outline.blit(self.img, (self.pos[0] - self.img.get_width() / 2 - self.game.render_scroll[0], self.pos[1] - self.img.get_height() / 2 - self.game.render_scroll[1]))
        
        if not self.game.paused:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]
       
        #Check to destroy
        if self.game.tilemap.solid_check(self.pos):
            if self.type == 'projectile':
                velocityAngle = math.atan(self.speed[1] / self.speed[0])
                for _ in range(4):
                    self.game.sparks.append(Spark(self.pos, random.random() - 0.5 + velocityAngle, 2 + random.random()))
            return True
        
        #Check for player collision:
        if self.game.player.rect().collidepoint(self.pos) and abs(self.game.player.dashing) < 50:
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.origin)
                return True



class RolyPoly(physicsEntity):
    def __init__(self, game, pos, size, initialFall = False):
        super().__init__(game, 'rolypoly', pos, size)

        self.attackPower = 1
        self.cogCount = random.randint(0,3) if len(game.bosses) == 0 else random.randint(0,1)
        self.eyeCount = random.randint(1,5) if len(game.bosses) == 0 else random.randint(0,1)

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

        elif self.grace:
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

        self.anim_offset = (0,-1)


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

        self.anim_offset = (0, 0)
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

        self.displayDarknessCircle()
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
        self.anim_offset = (-3, -3)
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
                    toPlayer = self.vectorTo(self.game.player)
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
        self.anim_offset = (0, 0)
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
        self.anim_offset = (0, 0)
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
        self.anim_offset = (0, 0)
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
        self.anim_offset = (0, 0)
        self.angle = random.random() * 2 * math.pi   
    
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)  

        if self.action == 'idle':
            self.lightSize += 0.2
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
        self.displayDarknessCircle()

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

        self.anim_offset = (0, -1)
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
                toPlayer = self.vectorTo(self.game.player)
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
        self.mainPos = list(pos)
        
        self.anim_offset = (0, 0)


    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        toPlayer = self.vectorTo(self.game.player)
        self.toPlayerNorm = toPlayer / np.linalg.norm(toPlayer)

        self.pos[0] = self.mainPos[0] + round(self.toPlayerNorm[0] if abs(self.toPlayerNorm[0]) > 0.38 else 0)
        self.pos[1] = self.mainPos[1] + round(self.toPlayerNorm[1] if abs(self.toPlayerNorm[1]) > 0.38 else 0)

class MeteorBait(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'meteorbait', pos, size)

        self.gravityAffected = False
        self.collideWallCheck = False
        self.pos = list(pos)
        self.anim_offset = (0, 0)

        self.cooldown = 0

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.cooldown:
            self.cooldown = max(self.cooldown - 1, 0)

        if self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) >= 50 and not self.cooldown:
            self.cooldown = 30
            self.summonMeteor(self.rect().center, [[x, y] for x in range(-2, 3) for y in range(-15,2)], 7)

    def summonMeteor(self, centerPos, area, quantity):
            testLoc = [0, 0]
            centerTile = (centerPos[0] // self.game.tilemap.tilesize, centerPos[1] // self.game.tilemap.tilesize)
            successTiles = []
            attempts = 0
            
            while len(successTiles) < quantity and attempts < 100:

                testLoc[0] = int(centerTile[0] + random.choice([e[0] for e in area]))
                testLoc[1] = int(centerTile[1] + random.choice([e[1] for e in area]))
                
                locStr = str(testLoc[0]) + ';' + str(testLoc[1])
                if locStr not in self.game.tilemap.tilemap and testLoc not in successTiles:
                    successTiles.append(testLoc.copy())

                attempts += 1

            for loc in successTiles:
                self.game.extraEntities.append(Meteor(self.game, (loc[0] * self.game.tilemap.tilesize, loc[1] * self.game.tilemap.tilesize), (16, 16)))
            
class boss(physicsEntity):
    def __init__(self, game, type, pos, size):
        super().__init__(game, type, pos, size)

        self.isBoss = True
        self.glowwormFollow = True
        self.difficulty = round(self.game.floors[self.game.levelType] / self.game.bossFrequency) - 1
        if self.game.currentLevel == 'infinite':
            self.difficulty = round(self.game.floors['infinite'] / self.game.bossFrequency) - 1
        self.deathIntensity = 50

        self.currencyDrops = {
            'cog': 20,
            'redCog': 0,
            'blueCog': 0,
            'purpleCog': 0,
            'heartFragment': 0,
            'wing': 0,
            'eye': 0,
            'chitin': 0,
            'fairyBread': 0,
            'boxingGlove': 0,
            'hammer': 0,
            'credit': 0
        }

        self.cogCount = random.randint(25 + 25 * self.difficulty, 50 + 25 * self.difficulty)
        self.heartFragmentCount = random.randint(5 + 10 * self.difficulty, 10 + 10 * self.difficulty)

        self.damageCooldown = 0
        self.timer = 0
        self.anim_offset = (0, 0)

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.damageCooldown:
            self.damageCooldown = max(self.damageCooldown - 1, 0)
        if self.checkDamageTaken(invincibleStates = self.invincibleStates, passiveStates = self.passiveStates):
            self.set_action('dying')

        if self.action == 'dying':

            self.velocity[0] *= 0.98
            self.velocity[1] *= 0.98

            spawnLoc = (self.pos[0] + (self.size[0] / 2) - 3, self.pos[1] + (self.size[1] / 2) - 3)
            for currency in self.currencyDrops:
                if self.currencyDrops[currency] > 0 and random.random() < 0.1:
                
                    self.game.currencyEntities.append(Currency(self.game, currency, spawnLoc, value = 5))
                    self.currencyDrops[currency] = max(self.currencyDrops[currency] - 1, 0)
            if max(self.currencyDrops.values()) == 0:
                self.kill(intensity = self.deathIntensity)
                return True

    def checkDamageTaken(self, invincibleStates = [], passiveStates = []):
        #Death Condition for Boss
        if self.action not in invincibleStates:
            if abs(self.game.player.dashing) >= 50:
                if self.rect().colliderect(self.game.player.rect()):

                    if self.damageSelf():
                        return True
                    
        #Check for player collision, not dashing and in attack mode:
        if self.game.player.rect().colliderect(self.rect()):
            if abs(self.game.player.dashing) < 50 and self.action not in passiveStates and not self.game.dead:
                self.game.player.damage(self.attackPower, self.type)


    def damageSelf(self, amount = 1):
        if not self.damageCooldown:
            self.health -= amount
            self.damageCooldown = 50
            self.damage(intensity = 10)

            if self.health <= 0:
                #Not zero because this boss hasnt been removed yet, but returns True in 3 lines.
                if len(self.game.bosses) == 1:
                    for enemy in self.game.enemies.copy():
                        enemy.kill(intensity = enemy.deathIntensity, creditCount = 1)
                    self.game.enemies = []
                return True
        
class NormalBoss(boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'normalboss', pos, size)

        self.currencyDrops['heartFragment'] = random.randint(0,5) * self.difficulty
        self.currencyDrops['wing'] = random.randint(4,10) * self.difficulty

        self.gravityAffected = False
        self.collideWallCheck = True

        self.attackRadius = int(100 * math.atan(self.difficulty / 5))
        self.wingCount = random.randint(20 + 20 * self.difficulty, 40 + 20 * self.difficulty)

        self.health = 2 + 2 * self.difficulty
        self.maxHealth = self.health

        self.anim_offset = (-3, -2)
        self.pos[1] += 3

        self.invincibleStates = ['idle', 'dying']
        self.passiveStates = ['idle', 'dying']

    def activate(self):
        self.set_action('activating')
        self.timer = 0
        self.velocity[0] = random.random() - 0.5
        self.gravityAffected = True

    def update(self, tilemap, movement = (0, 0)):
        if super().update(tilemap, movement = movement):
            return True

        toPlayer = self.vectorTo(self.game.player)
        norm = np.linalg.norm(toPlayer)

        if self.action == 'idle':
            if norm < 140:
                for boss in self.game.bosses:
                    boss.activate()

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

            self.wallRebound()
            
            if np.linalg.norm(self.velocity) > 0.1:
                self.velocity[0] *= 0.98
                self.velocity[1] *= 0.98

            elif self.animation.done:
                self.set_action('flying')

                for _ in range(20):
                    self.game.sparks.append(Spark(self.rect().center, random.random() * 2 * math.pi, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle1', self.rect().center, vel = [math.cos(random.random() * 2 * math.pi), math.cos(random.random() * 2 * math.pi)], frame = random.randint(0,7)))

                #Check for player collision, not dashing and in attack mode:
                self.circularAttack(self.attackRadius)

                batpos = (self.rect().center)
                for _ in range(random.randint(1, self.difficulty + 1)):
                    self.game.enemies.append(Bat(self.game, (batpos[0], batpos[1] - 4), self.game.entityInfo[4]['size'], graceDone = True, velocity = [3 * toPlayer[0] / norm + random.random() / 4, 3 * toPlayer[1] / norm + random.random() / 4]))

                self.velocity[0] = 0.5 + random.random()
                self.velocity[1] = 0.5 + random.random()


    def render(self, surface, offset = (0, 0)):
        angle = 0
        if self.action == 'activating':
            angle = self.animation.frame / 24.5
           
        super().render(surface, offset = offset, rotation = angle)

class GrassBoss(boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'grassboss', pos, size)

        self.currencyDrops['heartFragment'] = random.randint(0,5) * self.difficulty
        self.currencyDrops['eye'] = random.randint(4,10) * self.difficulty

        self.gravityAffected = False
        self.collideWallCheck = True
        self.collideWall = False

        self.attackRadius = int(100 * math.atan(self.difficulty / 5)) + 10
        self.eyeCount = random.randint(20 + 20 * self.difficulty, 40 + 20 * self.difficulty)

        self.health = 2 + 2 * self.difficulty
        self.maxHealth = self.health

        self.speed = -1
        self.heading = [self.speed, 0]
        self.wallSide = [0, -self.speed]
        self.timeSinceTurn = 0
        self.pos[0] += 6
        self.anim_offset = (-3, -3)

        self.invincibleStates = ['idle', 'dying']
        self.passiveStates = ['idle', 'dying']

        self.returning = False
        self.timeSinceAir = 0

    def activate(self):
        self.set_action('activating')
        self.timer = 0

    def update(self, tilemap, movement = (0, 0)):
        if super().update(tilemap, movement = movement):
            return True

        self.timeSinceAir += 1

        if self.action == 'idle':
            toPlayer = self.vectorTo(self.game.player)
            norm = np.linalg.norm(toPlayer)
            if norm < 120:
                for boss in self.game.bosses:
                    boss.activate()

        elif self.action == 'activating':
            self.timer += 1
            if self.animation.done:
                self.set_action('run')
                self.pos[1] -= 5
                self.timer = 0

        elif self.action == 'run':
            #Turn around at torches
            for ent in self.game.extraEntities:
                if ent.type == 'torch' and ent.rect().colliderect(self.rect()):

                    #Reverse direction
                    self.heading[0] *= -1
                    self.heading[1] *= -1

                    self.pos[0] -= self.velocity[0]
                    self.pos[1] -= self.velocity[1]

                    self.timeSinceTurn = 5

            if self.timeSinceAir > 60:
                self.pos[1] += 1
                self.timeSinceAir = 0

            #spawning small rolypolys
            if random.random() < 0.005 and self.health <= self.maxHealth / 2:
                #Find spot to spawn lil guy
                availableSpawnSpots = []
                for spawnLocOffset in [[0, 0], [0, 1], [1, 0], [1, 1]]:
                    tileLoc = [int(self.pos[0] // tilemap.tilesize) + spawnLocOffset[0], int(self.pos[1] // tilemap.tilesize) + spawnLocOffset[1]]

                    if str(str(tileLoc[0]) + ';' + str(tileLoc[1])) not in self.game.tilemap.tilemap:
                        availableSpawnSpots.append([tileLoc[0] * self.game.tilemap.tilesize, tileLoc[1] * self.game.tilemap.tilesize])

                #Spawn lil guys
                for _ in range(self.difficulty + round(random.random())):
                    spawnSpot = random.choice(availableSpawnSpots)
                    self.game.enemies.append(RolyPoly(self.game, [spawnSpot[0], spawnSpot[1] + 2], self.game.entityInfo[9]['size'], initialFall = True))


            if self.timeSinceTurn < 5:
                self.timeSinceTurn += 1          

            # Change direction if it leaves a tileblock:
            if not any(x == True for x in self.collisions.values()) and self.timeSinceTurn > 3:  
                self.wallSide, self.heading = [-self.heading[0], -self.heading[1]], self.wallSide
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.timeSinceTurn = 0
                self.timeSinceAir = 0
                
                
            #Also change direction if run into a wall:
            elif any(self.collisions.values()) and self.timeSinceTurn > 3:
                self.wallSide, self.heading = self.heading, [-self.wallSide[0], -self.wallSide[1]]
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.timeSinceTurn = 0
                

            if random.random() < 0.005 and not any(self.collisions.values()):
                self.set_action('attacking')
                self.velocity = [0, 0]
                self.gravityAffected = True
                self.timer = 30
                self.wallSide[0], self.wallSide[1] = -self.wallSide[0], self.wallSide[1]

        elif self.action == 'attacking':
            if self.timer:
                self.timer = max(self.timer - 1, 0)

            if any(self.collisions.values()) and not self.timer and not self.returning:
                self.timer = random.randint(70,100)
                self.collideWall = True

                if random.random() < 0.3:
                    self.velocity[1] = -8
                    self.velocity[0] = random.random() - 0.5
                    self.pos[1] -= 2
                    self.timer = 5
                    self.returning = True

                else:
                    self.circularAttack(self.attackRadius)

            elif any(self.collisions.values()) and not self.timer and self.returning:
                self.gravityAffected = False
                self.collideWall = False
                self.returning = False
                self.set_action('run')

                self.wallSide[0], self.wallSide[1] = 0, -1
                self.heading[0], self.heading[1] = random.choice([-1, 1]), 0
            
class SpaceBoss(boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spaceboss', pos, size)

        self.currencyDrops['heartFragment'] = random.randint(0,5) * self.difficulty
        self.currencyDrops['purpleCog'] = random.randint(0,2) * self.difficulty

        self.gravityAffected = True
        self.collideWallCheck = True

        self.attackRadius = int(100 * math.atan(self.difficulty / 5))

        self.health = 2 + 2 * self.difficulty
        self.maxHealth = self.health

        self.shootCountMax = self.difficulty
        self.shootCount = self.shootCountMax
        self.speed = self.difficulty / 2
        self.lightSize = 25

        self.invincibleStates = ['idle', 'activating', 'attacking', 'flying', 'dying']
        self.passiveStates = ['idle', 'dying']

        self.anim_offset = (-3, -8)

    def activate(self):
        self.set_action('activating')
        self.velocity[0] = random.uniform(-0.75, 0.75)
        self.velocity[1] = -random.uniform(2, 3)


    def update(self, tilemap, movement = (0, 0)):
        if super().update(tilemap, movement = movement):
            return True
       
        #Also damage self from meteor collision:
        for entity in self.game.extraEntities:
            if entity.type == 'meteor' and entity.action == 'kaboom':
                if self.rect().colliderect(entity.rect()):

                    if self.damageSelf():
                        self.set_action('dying')
                        self.gravityAffected = True


        toPlayer = (self.game.player.rect().x - self.rect().x, self.game.player.rect().y - self.rect().y)
        norm = np.linalg.norm(toPlayer)

        if self.action == 'idle':
            if norm < 50:
                for boss in self.game.bosses:
                    boss.activate()

                for _ in range(3):
                    self.game.sparks.append(Spark(self.rect().midbottom, random.uniform(0, math.pi), random.uniform(1.5, 2), color = random.choice([(0, 255, 0), (200, 0, 200)])))

        elif self.action == 'activating':
            if any(self.collisions.values()):
                self.set_action('flying')
                self.gravityAffected = False

                self.velocity[0] = self.speed * toPlayer[0] / norm
                self.velocity[1] = self.speed * toPlayer[1] / norm

            elif random.random() < 0.03:
                self.velocity[0] = random.uniform(-0.75, 0.75)
                self.velocity[1] = -random.uniform(2, 3)

                for _ in range(3):
                    self.game.sparks.append(Spark(self.rect().midbottom, random.uniform(0, math.pi), random.uniform(1.5, 2), color = random.choice([(0, 255, 0), (200, 0, 200)])))

        elif self.action == 'flying':
            self.displayDarknessCircle()
            if self.health <= self.maxHealth / 2 and norm > 100 and random.random() < 0.01:
                self.set_action('attacking')
                self.timer = 0
                self.shootCount = 0

            #Head towards the player on wall impact, sometimes
            elif any(self.collisions.values()) and random.random() < 0.5:
                if not (tilemap.solid_check((self.rect().centerx + 8, self.rect().centery)) and tilemap.solid_check((self.rect().centerx - 8, self.rect().centery))):
                    self.velocity[0] = random.uniform(0.8, 1.3) * self.speed * toPlayer[0] / norm
                if not (tilemap.solid_check((self.rect().centerx, self.rect().centery + 8)) and tilemap.solid_check((self.rect().centerx, self.rect().centery - 8))):
                    self.velocity[1] = random.uniform(0.8, 1.3) * self.speed * toPlayer[1] / norm

            #Otherwise just bounce off
            elif self.collisions['left'] or self.collisions['right']:
                self.velocity[0] *= random.uniform(-1.2, -0.9)
            elif self.collisions['up'] or self.collisions['down']:
                self.velocity[1] *= random.uniform(-1.2, -0.9)

        elif self.action == 'attacking':
            self.displayDarknessCircle()
            self.timer += 1

            self.wallRebound()

            if np.linalg.norm(self.velocity) > 0.1:
                self.velocity[0] *= 0.98
                self.velocity[1] *= 0.98

            if self.timer % 45 == 0 and self.shootCount < self.shootCountMax:
                self.shootCount += 1

                self.game.sfx['shoot'].play()
                angleToPlayer = math.atan(toPlayer[1] / (toPlayer[0] if toPlayer[0] != 0 else 0.01))
                bulletSpeed = 2 * math.atan(self.difficulty / 2)

                for angle in np.linspace(angleToPlayer, angleToPlayer + math.pi * 2, 5 + 3 * self.difficulty):
                    bulletVelocity = (bulletSpeed * math.cos(angle), bulletSpeed * math.sin(angle))

                    self.game.projectiles.append(Bullet(self.game, [self.rect().centerx, self.rect().centery], bulletVelocity, self.type))
                    self.game.sparks.append(Spark(self.rect().center, angle + math.pi, self.difficulty))

            elif self.animation.done:
                self.set_action('flying')
                self.timer = 0

                self.velocity[0] = self.speed * toPlayer[0] / norm
                self.velocity[1] = self.speed * toPlayer[1] / norm

        #Create sparks
        if self.action not in ['idle', 'activating']:
            if random.random() < 0.1:
                self.game.sparks.append(Spark(self.rect().midbottom, random.uniform(0, math.pi), random.uniform(1.5, 2), color = random.choice([(0, 255, 0), (200, 0, 200)])))

class Gravestone(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'gravestone', pos, size)

        self.gravityAffected = False
        self.collideWallCheck = False
        self.pos = list(pos)
        self.spawnCount = round(self.game.floors[self.game.levelType] / 10)
        self.spawning = False
        self.anim_offset = (0, 0)

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if self.spawnCount and not self.spawning:
            toPlayer = (self.game.player.rect().centerx - self.rect().centerx, self.game.player.rect().centery - self.rect().centery)
            norm = np.linalg.norm(toPlayer)

            if norm < 50:
                self.spawning = True

        elif self.spawnCount and self.spawning and random.random() < 0.05:
            self.game.bosses.append(SpookyBoss(self.game, [self.pos[0] + random.randint(-8, 40), self.pos[1] + random.randint(16, 32)], self.game.entityInfo[25]['size']))
            self.spawnCount -= 1

class FlyGhost(physicsEntity):
    def __init__(self, game, pos, size, difficulty):
        super().__init__(game, 'flyghost', pos, size)

        self.gravityAffected = False
        self.collideWall = False
        self.pos = list(pos)
        self.anim_offset = (-2, -2)
        self.isBoss = True
        self.difficulty = difficulty

        self.creditCount = 1 if random.random() < 0.05 else 0

        toPlayer = (self.game.player.rect().centerx - self.rect().centerx, self.game.player.rect().centery - self.rect().centery)
        norm = np.linalg.norm(toPlayer)

        self.velocity = [random.uniform(0.9, 1.1 + 0.3 * self.difficulty) * toPlayer[0] / norm, random.uniform(0.9, 1.1 + 0.3 * self.difficulty) * toPlayer[1] / norm]
        self.angle = math.atan2(-self.velocity[1], self.velocity[0])

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        toPlayer = (self.game.player.rect().centerx - self.rect().centerx, self.game.player.rect().centery - self.rect().centery)
        norm = np.linalg.norm(toPlayer)

        if norm > self.game.screen_width / 2.7 or len(self.game.bosses) == 0:
            return True
        
        if random.random() < 0.1:
            self.game.sparks.append(Spark(self.rect().center, -self.angle + math.pi + random.uniform(-0.3,0.3), 1.5))
        
        #Death Condition
        elif abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(creditCount = self.creditCount)
                return True 
        
        #Check for player collision
        elif self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50:
            if not self.game.dead:
                self.game.player.damage(self.attackPower, self.type) 

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset, rotation = self.angle)

class SpookyBoss(boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spookyboss', pos, size)

        self.currencyDrops['chitin'] = random.randint(2,5) * self.difficulty

        self.gravityAffected = False
        self.collideWall = False

        self.attackRadius = int(100 * math.atan(self.difficulty / 5))

        self.health = 2 + 2 * self.difficulty
        self.maxHealth = self.health

        self.transparency = 0
        self.transparencyInc = 3
        self.teleCoords = [0, 0]
        self.timer = 0

        self.playerTeleDist = 100
        self.velocity[0] = random.uniform(-0.5, 0.5)
        self.velocity[1] = random.uniform(-0.5, 0)

        self.invincibleStates = ['idle', 'teleporting', 'dying']
        self.passiveStates = ['idle', 'teleporting', 'dying']

        self.anim_offset = (0, 0)

    def update(self, tilemap, movement = (0, 0)):
        if super().update(tilemap, movement = movement):
            return True     

        if self.action == 'idle':
            self.transparency = min(self.transparency + 2, 255)
            if self.transparency >= 255:
                self.set_action('flying')

        elif self.action == 'flying':
            toPlayer = (self.game.player.rect().centerx - self.rect().centerx, self.game.player.rect().centery - self.rect().centery)
            norm = np.linalg.norm(toPlayer)

            #Teleport
            if random.random() < 0.005 or norm > 250:
                self.set_action('teleporting')

                foundSpot = False
                checkSpot = [0, 0]
                playerPosTile = (self.game.player.pos[0] // self.game.tilemap.tilesize, self.game.player.pos[1] // self.game.tilemap.tilesize)
                
                while not foundSpot:
                    checkSpot[0], checkSpot[1] = int(playerPosTile[0] + random.choice(range(-5,6))), int(playerPosTile[1] + random.choice(range(-10,4)))
                    locStr = str(checkSpot[0]) + ';' + str(checkSpot[1])
                    locStr2 = str(checkSpot[0]) + ';' + str(checkSpot[1] + 1)
                    if locStr not in self.game.tilemap.tilemap and locStr2 not in self.game.tilemap.tilemap:
                        foundSpot = True
                self.teleCoords = [checkSpot[0] * tilemap.tilesize, checkSpot[1] * tilemap.tilesize]

                self.transparency = -255
                self.transparencyInc = random.choice([1,2,3])
                self.timer = random.randint(30,90)

        elif self.action == 'teleporting':
            #Fading away
            if self.timer and self.transparency < 0:
                self.transparency = min(self.transparency + self.transparencyInc, 0)

            #Waiting to move (invisible)
            elif self.transparency == 0 and self.timer:
                self.timer = max(self.timer - 1, 0)

            #Teleport
            elif self.transparency == 0 and not self.timer:
                self.pos[0] = self.teleCoords[0]
                self.pos[1] = self.teleCoords[1]

                self.velocity[0] = (random.random() - 0.5) * 0.5
                self.velocity[1] = (random.random() - 0.5) * 0.5
                self.transparency += 1

            #Fading back in
            elif not self.timer and self.transparency > 0:
                self.transparency = min(self.transparency + self.transparencyInc, 255)

                if self.transparency >= 255:
                    self.set_action('flying')

        #Create attack ghost
        if random.random() < 0.01:
            spawnAngle = random.random() * 2 * math.pi
            spawnDist = self.game.screen_width / 2.8

            spawnPos = [self.game.player.pos[0] + (math.sin(spawnAngle) * spawnDist), self.game.player.pos[1] + (math.cos(spawnAngle) * spawnDist)]

            self.game.extraEntities.append(FlyGhost(self.game, spawnPos, self.game.entityInfo[32]['size'], self.difficulty))

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset, transparency = abs(self.transparency))
                    
class RubiksBoss(boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'rubiksboss', pos, size)

        self.currencyDrops['redCog'] = random.randint(2,5) * self.difficulty
        self.currencyDrops['blueCog'] = random.randint(2,5) * self.difficulty
        self.currencyDrops['purpleCog'] = random.randint(0,1) * self.difficulty

        self.gravityAffected = False
        self.collideWallCheck = True

        self.attackRadius = int(100 * math.atan(self.difficulty / 5))

        self.health = 2 + 2 * self.difficulty
        self.maxHealth = self.health

        self.speed = 1
        self.maxSpeed = 3
        self.canMove = True

        self.anim_offset = (0, 0)

        self.states = ['white', 'yellow', 'blue', 'green', 'red', 'orange']
        self.invincibleStates = ['idle', 'white', 'yellow', 'blue', 'green', 'red', 'orange', 'dying']
        self.passiveStates = ['idle', 'dying']
        self.halfBlockDist = game.tilemap.tilesize / 2

    def activate(self):
        self.set_action(random.choice(self.states))
        self.timer = random.randint(90,120)

    def update(self, tilemap, movement = (0, 0)):
        if super().update(tilemap, movement = movement):
            return True
    
        if self.action == 'idle':
            toPlayer = (self.game.player.rect().x - self.rect().x, self.game.player.rect().y - self.rect().y)
            norm = np.linalg.norm(toPlayer)
            if norm < 150:
                for boss in self.game.bosses:
                    boss.activate()

        elif self.action != 'dying':
            #When timer runs out, move in a random direction until hit a wall
            self.timer = max(self.timer - 1, 0)
            #Then change colour and reset timer.
            if self.canMove and not self.timer:
                #Find random directions that entity can move in
                self.canMoveVectors = []
                posCentre = [self.rect().centerx, self.rect().centery]

                #left:
                if not (tilemap.solid_check([posCentre[0] - 3 * self.halfBlockDist, posCentre[1] - self.halfBlockDist], returnValue = 'bool') or tilemap.solid_check([posCentre[0] - 3 * self.halfBlockDist, posCentre[1] + self.halfBlockDist], returnValue = 'bool')):
                    self.canMoveVectors.append([-self.speed, 0])
                #right:
                if not (tilemap.solid_check([posCentre[0] + 3 * self.halfBlockDist, posCentre[1] - self.halfBlockDist], returnValue = 'bool') or tilemap.solid_check([posCentre[0] + 3 * self.halfBlockDist, posCentre[1] + self.halfBlockDist], returnValue = 'bool')):
                    self.canMoveVectors.append([self.speed, 0])
                #up:
                if not (tilemap.solid_check([posCentre[0] - self.halfBlockDist, posCentre[1] - 3 * self.halfBlockDist], returnValue = 'bool') or tilemap.solid_check([posCentre[0] + self.halfBlockDist, posCentre[1] - 3 * self.halfBlockDist], returnValue = 'bool')):
                    self.canMoveVectors.append([0, -self.speed])
                #down:
                if not (tilemap.solid_check([posCentre[0] - self.halfBlockDist, posCentre[1] + 3 * self.halfBlockDist], returnValue = 'bool') or tilemap.solid_check([posCentre[0] + self.halfBlockDist, posCentre[1] + 3 * self.halfBlockDist], returnValue = 'bool')):
                    self.canMoveVectors.append([0, self.speed])
    
                #Set velocity to that direction
                self.velocity = random.choice(self.canMoveVectors)
                self.canMove = False

            else:
                self.velocity[0] = max(min(self.velocity[0] * 1.02, self.maxSpeed), -self.maxSpeed)
                self.velocity[1] = max(min(self.velocity[1] * 1.02, self.maxSpeed), -self.maxSpeed)
                
            #When hit a tile, stop and change colour, repeat
            if any(self.collisions.values()):
                self.timer = random.randint(120,180)
                self.velocity = [0, 0]
                self.set_action(random.choice(self.states))
                self.canMove = True

            #Spawn falling cube:
            if random.random() < 0.01 and len(self.game.extraEntities) < 20:
                posCentre = [self.rect().centerx, self.rect().centery]
                if not (tilemap.solid_check([posCentre[0] - self.halfBlockDist, posCentre[1] + 3 * self.halfBlockDist], returnValue = 'bool') or tilemap.solid_check([posCentre[0] + self.halfBlockDist, posCentre[1] + 3 * self.halfBlockDist], returnValue = 'bool')):
                    if self.action != 'dying':
                        self.game.extraEntities.append(RubiksCubeThrow(self.game, [self.pos[0] + self.halfBlockDist, self.pos[1] + self.halfBlockDist], self.game.entityInfo[34]['size'], action = self.action))

class RubiksCubeThrow(physicsEntity):
    def __init__(self, game, pos, size, action = 'idle'):
        super().__init__(game, 'rubiksCube', pos, size)

        self.gravityAffected = True
        self.pos = list(pos)
        self.spawnCount = round(self.game.floors[self.game.levelType] / 10)
        self.anim_offset = (0, 0)
        self.activated = False
        self.attackRadius = 50
        self.bombDelay = 5
        self.initialAttack = False
        self.states = {
            'white': (155, 155, 155),
            'yellow': (175, 152, 0),
            'blue': (0, 0, 204),
            'green': (0, 119, 0),
            'red': (175, 0, 0),
            'orange': (206, 123, 0),
        }
        self.set_action(action)

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)

        if not self.initialAttack:
            if any(self.collisions.values()):
                self.circularAttack(self.attackRadius / 2, color = self.states[self.action], colorStr = self.action)
                self.initialAttack = True

        if self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) >= 50:
            self.velocity = [random.random() - 0.5, random.uniform(-8, -6)]
            self.activated = True

        elif self.activated:
            self.bombDelay = max(self.bombDelay - 1, 0)
            if any(self.collisions.values()) and not self.bombDelay:
                self.circularAttack(self.attackRadius, color = self.states[self.action], colorStr = self.action, canDamageBoss = True)
                self.kill()
                return True
            for boss in self.game.bosses:
                if self.rect().colliderect(boss.rect()):
                    self.circularAttack(self.attackRadius, color = self.states[self.action], colorStr = self.action, canDamageBoss = True)
                    self.kill()
                    return True
                       
class AussieBoss(boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'aussieboss', pos, size)

        self.currencyDrops['fairyBread'] = random.randint(2,5) * self.difficulty
        self.currencyDrops['chitin'] = random.randint(2,5) * self.difficulty
        self.currencyDrops['purpleCog'] = random.randint(0,1) * self.difficulty

        self.attackRadius = int(100 * math.atan(self.difficulty / 5))
        self.activeMinTime = max(60, 100 - self.difficulty * 20)
        self.activeMaxTime = max(70, 120 - self.difficulty * 20)

        self.health = 2 + 2 * self.difficulty
        self.maxHealth = self.health

        self.gravityAffected = True
        self.timer = 0

        self.anim_offset = (-8, -12)

        self.invincibleStates = ['idle', 'dying']
        self.passiveStates = ['idle', 'dying']

    def activate(self):
        self.set_action('active')
        self.timer = random.randint(90,120)


    def update(self, tilemap, movement = (0, 0)):
        if super().update(tilemap, movement = movement):
            return True
    
        if self.action == 'idle':
            toPlayer = (self.game.player.rect().x - self.rect().x, self.game.player.rect().y - self.rect().y)
            norm = np.linalg.norm(toPlayer)
            if norm < 150:
                for boss in self.game.bosses:
                    boss.activate()

        elif self.action == 'active':
            self.timer = max(self.timer - 1, 0)

            if not self.timer:
                self.set_action('prep')

        elif self.action == 'prep':

            if self.animation.done:
                ###JUMP ROUGHLY IN DIRECTION OF PLAYER
                self.set_action('jumping')
                if self.pos[0] < self.game.player.pos[0]:
                    self.flip_x = False
                else:
                    self.flip_x = True

                playerAbove = False
                if self.pos[1] > self.game.player.pos[1]:
                    playerAbove = True
                
                self.velocity[0] = -(random.random() + 3.5) if self.flip_x else (random.random() + 3.5)
                self.velocity[1] = -(random.random() * 4 + 7 if playerAbove else 4)
                self.timeSinceBounce = 0 
                    
        elif self.action == 'jumping':
            self.timeSinceBounce = min(self.timeSinceBounce + 1, 10)
            self.velocity[0] *= 0.99
            self.velocity[1] *= 0.99

            if self.collisions['left'] or self.collisions['right'] and self.timeSinceBounce >= 10:
                self.timeSinceBounce = 0
                self.velocity[0] = -self.velocity[0]
                self.flip_x = not self.flip_x

            if self.collisions['down']:
                posCentre = [self.rect().centerx, self.rect().centery]
                if tilemap.solid_check([posCentre[0] - tilemap.tilesize / 2, posCentre[1] + tilemap.tilesize], returnValue = 'bool') or tilemap.solid_check([posCentre[0] + tilemap.tilesize / 2, posCentre[1] + tilemap.tilesize], returnValue = 'bool'):
                    self.velocity = [0, 0]

                    self.timer = random.randint(self.activeMinTime, self.activeMaxTime)
                    self.set_action('active')  
                    self.circularAttack(self.attackRadius, pos = self.rect().midbottom)

                    #Sometimes spawn other lil guys:
                    spawnPos = [self.rect().centerx - 8, self.rect().y]

                    if random.random() < 0.134:
                        self.game.enemies.append(Kangaroo(self.game, spawnPos, self.game.entityInfo[19]['size']))
                    
                    elif random.random() < 0.134:
                        self.game.enemies.append(Echidna(self.game, spawnPos, self.game.entityInfo[20]['size']))