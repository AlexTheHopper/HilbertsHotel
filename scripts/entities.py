import pygame
import sys
import math
import random
import numpy as np

from scripts.particle import *
from scripts.spark import *
from scripts.utilities import *

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

        self.terminal_vel = 5
        self.gravity = 0.12

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip_x = False
        self.set_action('idle')
        self.renderDistance = self.game.screen_width / 2

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
                    if self.collideWall:
                        self.pos[1] = entity_rect.y

                    if self.type == 'player':
                        self.lastCollidedWall = self.game.tilemap.tilemap[str(rect.x // self.game.tilemap.tilesize) + ';' + str(rect.y // self.game.tilemap.tilesize)]
                        


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
        if self.gravityAffected:
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
            surface.blit(pygame.transform.flip(self.animation.img(), self.flip_x, False), (posx, posy))





    def kill(self, intensity = 10, cogCount = 0, redCogCount = 0, blueCogCount = 0, purpleCogCount = 0, heartFragmentCount = 0, wingCount = 0, eyeCount = 0, chitinCount = 0):
        self.game.screenshake = max(intensity, self.game.screenshake)
        self.game.sfx['hit'].play()
        for _ in range(intensity):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5

            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random() * (intensity / 10)))
            self.game.particles.append(Particle(self.game, 'particle1', self.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
        
        self.game.sparks.append(Spark(self.rect().center, 0, intensity / 2))
        self.game.sparks.append(Spark(self.rect().center, math.pi, intensity / 2))

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



class Bat(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'bat', pos, size)

        self.cogCount = random.randint(0,3)
        self.heartFragmentCount = (1 if random.random() < 0.2 else 0)
        self.wingCount = (1 if random.random() < 0.8 else 0)

        self.attackPower = 1

        self.deathIntensity = 5

        self.gravityAffected = False

        self.grace = random.randint(90,210)
        self.graceDone = False
        self.set_action('grace')
        self.isAttacking = False
        self.anim_offset = [-2, -1]
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
            if self.rect().collidepoint(projectile.pos):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, wingCount = self.wingCount)
                self.game.projectiles.remove(projectile)
                return True

        
        #Check for player collision, not dashing and in attack mode:
        if self.game.player.rect().collidepoint(self.pos) and abs(self.game.player.dashing) < 50 and self.action == 'attacking':
            if not self.game.dead:
                self.game.player.damage(self.attackPower)


    def render(self, surface, offset = (0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        
        angle = 0
        if self.action in ['charging', 'attacking']:
            angle = math.atan2(-self.velocity[1], self.velocity[0]) + math.pi/2 + (math.pi if self.action == 'attacking' else 0)
           
        super().render(surface, offset = offset, rotation = angle)
        
class GunGuy(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'gunguy', pos, size)
        self.deathIntensity = 5
        self.difficultyLevel = 1
        self.walking = 0
        self.flying = False
        self.attack_dist_y = 24
        self.bullet_speed = 1.5
        self.shootCountdown = 0
        self.weaponIndex = 0
        self.gravityAffected = True
        
        self.intelligence = math.floor(self.game.floors[str(self.game.currentLevel)] / 5) if self.game.currentLevel == 'normal' else 2
        self.weapon = 'gun' if self.intelligence < 2 else ('staff' if random.random() < (0.85 if self.game.currentLevel == 'spooky' else 0.25) else 'gun')

        self.witch = False
        self.staffCooldown = 120
        self.trajectory = [0, 0]

        if self.game.difficulty >= 2 and self.game.currentLevel == 'normal':
            self.difficultyLevel = random.randint(0, self.game.difficulty)
            if self.difficultyLevel == 2:
                self.type = 'gunguyOrange'
            elif self.difficultyLevel == 3:
                self.type = 'gunguyBlue'
            elif self.difficultyLevel == 4:
                self.type = 'gunguyPurple'


        self.cogCount = random.randint(2,4)
        self.redCogCount = random.randint(1,3) if (self.type == 'gunguyOrange') else 0
        self.blueCogCount = random.randint(1,3) if (self.type == 'gunguyBlue') else 0
        self.purpleCogCount = random.randint(1,3) if (self.type == 'gunguyPurple') else 0
        self.heartFragmentCount = 1 if self.weapon == 'staff' else (1 if random.random() < 0.1 else 0)
        self.wingCount = random.randint(0,3) if self.witch else 0
        self.eyeCount = 0


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


        if self.velocity[0]:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        elif not self.witch:
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
                    
                    #Create bullet
                    if self.flip_x:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append(Bullet(self.game, [self.rect().centerx - bulletOffset[0], self.rect().centery + bulletOffset[1]], bulletVelocity))
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5 + math.pi, 2 + random.random()))
                    
                    else:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append(Bullet(self.game, [self.rect().centerx + bulletOffset[0], self.rect().centery + bulletOffset[1]], bulletVelocity))
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5, 2 + random.random()))
                    
                    

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
                
                
            elif random.random() < 0.01:
                self.walking = random.randint(30, 120)

            #Attack condition
            if (random.random() < 0.02 and not self.shootCountdown):
                #Gun:
                if self.weapon == 'gun':
                    disty = self.game.player.pos[1] - self.pos[1]
                    distx = self.game.player.pos[0] - self.pos[0]
                    #Y axis condition:
                    if abs(disty) < self.attack_dist_y and not self.game.dead:
                        #X axis condition
                        if (self.flip_x and distx < 0) or (not self.flip_x and distx > 0):
                            self.shootCountdown = 60
                            self.walking = 0
                elif self.weapon == 'staff' and not self.staffCooldown:
                   
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

            #Setting animation type
            if self.action == 'jump':
                if self.collisions['down']:
                    self.set_action('idle')
            if self.action not in ['shooting', 'jump']:
                if movement[0] != 0:
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
            'spooky': [(55, 20, 15), (108, 50, 40)]}

    def update(self, game):
        self.animation.update()

        #Changing state/action
        if self.game.currentLevel == 'lobby':
            self.set_action('active')
            self.lightSize = 40
        elif self.action == 'idle' and len(self.game.enemies) == 0:
            self.set_action('opening')
            

        if self.action == 'opening':
            if self.animation.done:
                self.set_action('active')
            self.lightSize += 0.5


        #Decals
        if self.action in ['opening', 'active']:
            if random.random() < (0.1 + (0.1 if self.action == 'active' else 0)):
                angle = (random.random()) * 2 * math.pi
                speed = random.random() * (3 if self.action == 'active' else 2)
                self.game.sparks.append(Spark(self.rect().center, angle, speed, color = random.choice(self.colours[self.destination])))

        #Collision and level change
        playerRect = self.game.player.rect()
        if self.rect().colliderect(playerRect) and self.action == 'active' and self.game.transition == 0:
            self.game.transitionToLevel(self.destination)

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
        
        if self.damageCooldown:
            self.damageCooldown = max(self.damageCooldown - 1, 0) 
        
        self.air_time += 1
        if self.air_time > 180 and not self.wall_slide:
            # self.game.dead += 1
            pass
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
        if (self.collisions['left'] or self.collisions['right']) and self.air_time > 4:
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
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
 

        
        if abs(self.dashing) > 50:
            
            self.downwards = self.game.movement[3] - self.game.movement[2]
            self.velocity[1] = self.downwards * 8

            self.sideways = self.game.movement[1] - self.game.movement[0]
            if self.sideways == 0 and not self.downwards:
                self.sideways = 1 - 2*self.flip_x    
            self.velocity[0] = self.sideways * 8

            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
                self.velocity[1] *= 0.1

                #Breaking cracked tiles:
                if any(self.collisions.values()) and self.game.wallet['hammers'] > 0:
                    if self.lastCollidedWall['type'] == 'cracked':
                        
                        #Find correct tunnel:
                        for tunnelName in self.game.tunnelStates.keys():
                            if any(loc == self.lastCollidedWall['pos'] for loc in self.game.tunnelStates[tunnelName]['posList']):
                                
                                #Actually break all the tiles and save tunnel as broken:
                                for loc in self.game.tunnelStates[tunnelName]['posList']:
                                    del self.game.tilemap.tilemap[str(loc[0]) + ';' + str(loc[1])]
                                    self.game.sparks.append(Spark((loc[0] * self.game.tilemap.tilesize, loc[1] * self.game.tilemap.tilesize), random.random() * math.pi * 2, random.random() * 5))

                                self.game.tunnelStates[tunnelName]['broken'] = True

                        self.game.wallet['hammers'] -= 1
                    

            if self.game.transition < 1:
                p_velocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
                self.game.particles.append(Particle(self.game, 'particle' + str(self.game.powerLevel), self.rect().center, vel=[movement[0] + random.random(), movement[1] + random.random()], frame = random.randint(0,7)))

        if abs(self.dashing) in {60, 50}:
            if self.game.transition < 1:
                for _ in range(20):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 0.5 + 0.5
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
            if enemy.pos[0] < 0 or enemy.pos[0] > self.game.mapHeight*16 or enemy.pos[1] < 0 or enemy.pos[1] > self.game.mapWidth*16:
                self.game.enemies.remove(enemy)
                print('removing enemy ',enemy.type, ' at ', enemy.pos) #debug
                print('bounds: ', 0,0, ",",self.game.tilemap.mapSize*16,self.game.tilemap.mapSize*16)
                        
                    
        self.nearestEnemy = returnEnemy

    def damage(self, damageAmount):
        if not self.damageCooldown:
            self.damageCooldown = 60
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

                for currency in self.game.wallet:
                    if currency not in self.game.notLostOnDeath:
                        lostAmount = math.floor(self.game.wallet[currency] * 0.25)
                        self.game.wallet[currency] -= lostAmount
                        self.game.walletLostAmount[currency] = lostAmount


            else:
                self.game.screenshake = max(5, self.game.screenshake)
                for _ in range(10):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.game.player.rect().center, angle, 2 + random.random(), color = (100,0,0)))
                        self.game.particles.append(Particle(self.game, 'particle', self.game.player.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
    
class Currency(physicsEntity):
    def __init__(self, game, currencyType, pos, size = (6,6)):
        super().__init__(game, currencyType, pos, size)

        self.velocity = [2 * (random.random()-0.5), -1.5]
        self.value = 1
        self.currencyType = currencyType
        self.size = list(size)
        self.gravityAffected = True
        self.lightSize = 5
        
        self.animation.img_duration += (self.animation.img_duration*random.random()) 
        
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        self.velocity[0] *= 0.95

        
        if np.linalg.norm((self.pos[0] - self.game.player.pos[0] - self.game.player.size[0] / 2, self.pos[1] - self.game.player.pos[1] - self.game.player.size[1] / 2)) < 15:
            if self.pos[0] - self.game.player.pos[0] > 0:
                self.velocity[0] = -0.5
            else:
                self.velocity[0] = 0.5

        #Check for player collision
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 40:
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
        self.hoverDistance = 10
        self.anim_offset = (0, 0)
        self.animation.img_duration += (self.animation.img_duration*random.random())  
        self.direction = [random.random(), random.random()]      

    def update(self, tilemap, movement = (0, 0)):
       
       #Choose a random direction to head for a bit,
       #They will go towards a priority entity.

        if random.random() < 0.05:
            #First priority go to random enemy
            directionExtra = [0, 0]
            checkPortal = True

            if len(self.game.enemies) > 0 and self.game.player.nearestEnemy:
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
    def __init__(self, game, pos, speed):
        self.pos = list(pos)
        self.game = game
        self.speed = list(speed)
        self.type = 'projectile'
        self.img = self.game.assets[self.type]
        self.anim_offset = (-2, 0)

        self.attackPower = 1

    def update(self, game):
        self.game.display_outline.blit(self.img, (self.pos[0] - self.img.get_width() / 2 - self.game.render_scroll[0], self.pos[1] - self.img.get_height() / 2 - self.game.render_scroll[1]))
        
        if not self.game.paused:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]
       
        #Check to destroy
        if self.game.tilemap.solid_check(self.pos):
            for _ in range(4):
                self.game.sparks.append(Spark(self.pos, random.random() - 0.5 + (math.pi if self.speed[0] > 0 else 0), 2 + random.random()))
            return True
        
        #Check for player collision:
        if self.game.player.rect().collidepoint(self.pos) and abs(self.game.player.dashing) < 50:
            if not self.game.dead:
                self.game.player.damage(self.attackPower)
                return True
            

        if self.game.caveDarkness:
            self.game.darknessCircle(0, 15, (int(self.pos[0]) - self.game.render_scroll[0] + (1 if self.speed[0] < 0 else -1), int(self.pos[1]) - self.game.render_scroll[1]))

class RolyPoly(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'rolypoly', pos, size)

        self.size = list(size)
        self.speed = round(random.random() * 0.5 + 0.5, 2)
        self.gravityAffected = False
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

        self.attackPower = 1
        self.cogCount = random.randint(0,3)
        self.eyeCount = random.randint(1,3)    

    def update(self, tilemap, movement = (0, 0)):         
        super().update(tilemap, movement = movement)  
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        
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
                self.kill(cogCount = self.cogCount, eyeCount = self.eyeCount)
                return True
            
        #Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos):
                self.kill(cogCount = self.cogCount, eyeCount = self.eyeCount)
                self.game.projectiles.remove(projectile)
                return True
            
        #Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'idle':
            if not self.game.dead:
                self.game.player.damage(self.attackPower)
                

 


    def render(self, surface, offset = (0, 0)):
        # pygame.draw.rect(self.game.HUDdisplay, (255,0,0), (2*(self.rect().x - self.game.render_scroll[0] - self.anim_offset[0]), 2*(self.rect().y - self.game.render_scroll[1] - self.anim_offset[1]), self.size[0]*2, self.size[1]*2))
        
        super().render(surface, offset = offset)
       

class SpawnPoint(physicsEntity):
    def __init__(self, game, pos, size, action = 'idle'):
        super().__init__(game, 'spawnPoint', pos, size)
        self.gravityAffected = False
        self.collideWallCheck = False
        self.collideWall = False
        self.set_action(action)

        self.anim_offset = [0,-1]

    def update(self, tilemap, movement = (0, 0)):         
        super().update(tilemap, movement = movement)  

        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) > 50 and self.action == 'idle':
            for point in self.game.spawnPoints:
                if point.action == 'active':
                    point.set_action('idle')
            
            self.set_action('active')
            self.game.spawnPoint = self.pos[:]
            self.game.check_encounter('spawnPoints')

        if self.action == 'active':
            if random.random() < 0.05:
                angle = (random.random() + 1) * math.pi
                speed = random.random() * 3
                self.game.sparks.append(Spark(self.rect().center, angle, speed, color = random.choice([(58, 6, 82), (111, 28, 117)])))

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
        left = str((self.pos[0] - 1) // self.game.tilemap.tilesize) + ';' + str(self.pos[1] // self.game.tilemap.tilesize) in self.game.tilemap.tilemap
        right = str((self.pos[0] + 17) // self.game.tilemap.tilesize) + ';' + str(self.pos[1] // self.game.tilemap.tilesize) in self.game.tilemap.tilemap
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
        self.deathIntensity = 5
        self.gravityAffected = False

        self.grace = random.randint(90,210)
        self.graceDone = False
        self.set_action('grace')
        self.anim_offset = [-3, -3]
        self.pos[0] += 4
        self.pos[1] += 5
        self.timer = 0

        self.toPlayer = [0, 0]
        self.facing = [0, -1]
        
    
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
            if self.rect().collidepoint(projectile.pos):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount, chitinCount = self.chitinCount)
                self.game.projectiles.remove(projectile)
                return True

        
        #Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'grace':
            if not self.game.dead:
                self.game.player.damage(self.attackPower)


    def render(self, surface, offset = (0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        
        angle = 0
        if self.action != 'grace':
            angle = math.atan2(-self.facing[1], self.facing[0]) - math.pi / 2
           
        super().render(surface, offset = offset, rotation = angle)