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

        if self.collideWall:
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
        
        
        image = pygame.transform.rotate(self.animation.img(), rotation * 180 / math.pi)
        surface.blit(pygame.transform.flip(image, self.flip_x, False), (posx, posy))



    def kill(self, intensity = 10, cogCount = 0, heartFragmentCount = 0, wingCount = 0):
        self.game.screenshake = max(intensity, self.game.screenshake)
        self.game.sfx['hit'].play()
        for _ in range(intensity):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5

            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random() * (intensity / 10)))
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
        
        self.game.sparks.append(Spark(self.rect().center, 0, intensity / 2))
        self.game.sparks.append(Spark(self.rect().center, math.pi, intensity / 2))

        #Create currencies
        spawnLoc = (int(self.pos[0] // self.game.tilemap.tile_size), int(self.pos[1] // self.game.tilemap.tile_size))
        spawnLoc = ((spawnLoc[0] * self.game.tilemap.tile_size) + self.game.tilemap.tile_size/2, (spawnLoc[1] * self.game.tilemap.tile_size) + self.game.tilemap.tile_size/2)
        
        for _ in range(cogCount):
            self.game.cogs.append(Cog(self.game, spawnLoc))
        for _ in range(heartFragmentCount):
            self.game.cogs.append(HeartFragment(self.game, spawnLoc))
        for _ in range(wingCount):
            self.game.wings.append(Wing(self.game, spawnLoc))



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
        self.anim_offset = [-4, -1]
        self.timer = 0
        self.slingTimer = 0
        self.pos[1] += 3

        self.toPlayer = [0, 0]
        self.pos[0] += 2
        self.pos[1] += 8
    
        

        

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        # pygame.draw.rect(self.game.HUDdisplay, (255,0,0), (2*(self.rect().x - self.game.render_scroll[0] - self.anim_offset[0]), 2*(self.rect().y - self.game.render_scroll[1] - self.anim_offset[1]), self.size[0], self.size[1] ))
        
                

        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(180,500)
                self.velocity = [random.random(), random.random()]
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
                    self.timer = random.randint(90,120)
                    

            elif self.action == 'charging':
                self.timer = max(self.timer - 1, 0)
                self.velocity[0] = -self.toPlayer[0] * 0.15
                self.velocity[1] = -self.toPlayer[1] * 0.15

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
                  
                        


            if not self.slingTimer:
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
        angle = 0
        if self.action in ['charging', 'attacking']:
            angle = math.atan2(-self.velocity[1], self.velocity[0]) + math.pi/2 + (math.pi if self.action == 'attacking' else 0)
           

        super().render(surface, offset = offset, rotation = angle)
        

class GunGuy(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'gunguy', pos, size)
        self.deathIntensity = 5

        self.intelligence = math.floor(self.game.floor / 5)
        self.weapon = 'gun' if self.intelligence < 2 else ('staff' if random.random() < 0.25 else 'gun')
        self.staffCooldown = 120
        self.trajectory = [0, 0]

        self.cogCount = random.randint(2,3)
        self.heartFragmentCount = 1 if self.weapon == 'staff' else (1 if random.random() < 0.1 else 0)
        self.wingCount = 0


        if random.random() < 0.5:
            self.flip_x = True

        self.walking = 0
        self.attack_dist_y = 24
        self.bullet_speed = 1.5
        self.shootCountdown = 0
        self.weaponIndex = 0
        self.gravityAffected = True
        

        

        self.grace = random.randint(60,120)
        self.graceDone = False
        self.set_action('grace')
    
    def update(self, tilemap, movement = (0, 0)):

        # Only update/render at close distances
        renderDistToPlayer = np.linalg.norm((self.pos[0] - self.game.player.pos[0], self.pos[1] - self.game.player.pos[1]))
        if renderDistToPlayer > self.renderDistance:
            return False
        
        if self.game.caveDarkness:
            self.game.darknessCircle(0, 30, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))

        
        
        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.graceDone = True
            self.animation.update()


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
                    
                    #Create bullet
                    if self.flip_x:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append(Bullet(self.game, [self.rect().centerx - bulletOffset[0], self.rect().centery + bulletOffset[1]], bulletVelocity))
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5 + math.pi, 2 + random.random()))
                    
                    
                    if not self.flip_x:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append(Bullet(self.game, [self.rect().centerx + bulletOffset[0], self.rect().centery + bulletOffset[1]], bulletVelocity))
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5, 2 + random.random()))
                    

            elif self.walking:
                #Check jump condition, tilemap infront and above:
                inFront = tilemap.solid_check((self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery))
                above = tilemap.solid_check((self.rect().centerx, self.rect().centery - 16))
                
                if inFront and not above and self.collisions['down'] and self.intelligence > 0:
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
                    
                #Turn around if bump into a wall
                if (self.collisions['left'] or self.collisions['right']) and self.action != 'jump':
                    self.flip_x = not self.flip_x
                else:
                    movement = (movement[0] - 0.5 if self.flip_x else 0.5, movement[1])               
                self.walking = max(self.walking - 1, 0)

            #also turn around if stopped to face player
            # elif random.random() < 0.05 and self.intelligence > 0:
            #     distx = self.game.player.pos[0] - self.pos[0]
            #     if (self.flip_x and distx > 0) or (not self.flip_x and distx < 0):
            #         self.flip_x = not self.flip_x

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
                    for n in range(50):
                        x = int((x1 + (n/50) * xDist) // 16)
                        y = int((y1 + (n/50) * yDist) // 16)
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
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity = self.deathIntensity, cogCount = self.cogCount, heartFragmentCount = self.heartFragmentCount)
                return True

                

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

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
        super().__init__(game, 'portal', pos, size)
        self.anim_offset = (0, 0)
        self.destination = destination
        self.lightSize = 0

    def update(self, game):
        self.animation.update()
       

        if self.game.caveDarkness and self.action in ['opening', 'active']:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))


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
                speed = random.random() * (2.5 if self.action == 'active' else 2)
                colours = [(58, 6, 82), (111, 28, 117)]
                self.game.sparks.append(Spark(self.rect().center, angle, speed, color = random.choice(colours)))

        #Collision and level change
        playerRect = self.game.player.rect()
        if self.rect().colliderect(playerRect) and self.action == 'active' and self.game.transition == 0:
            self.game.transitionToLevel(self.destination)

                
            
class Player(physicsEntity):

    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0

        self.total_jumps = 1
        self.jumps = self.total_jumps

        self.wall_slide = False

        self.spark_timer = 0
        self.spark_timer_max = 60
        self.gravityAffected = True
        self.nearestEnemy = False
        self.damageCooldown = 0

    def update(self, tilemap, movement = (0, 0)):
        # pygame.draw.rect(self.game.HUDdisplay, (255,0,0), (2*(self.rect().x - self.game.render_scroll[0] - self.anim_offset[0]), 2*(self.rect().y - self.game.render_scroll[1] - self.anim_offset[1]), self.size[0], self.size[1] ))
        super().update(tilemap, movement = movement)

        if self.game.caveDarkness and self.game.transition <= 0:
            self.game.darknessCircle(0, 90, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))

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
            if self.game.transition < 1:
                p_velocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, vel=[movement[0] + random.random(), movement[1] + random.random()], frame = random.randint(0,7)))

        if abs(self.dashing) in {60, 50}:
            if self.game.transition < 1:
                for _ in range(20):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 0.5 + 0.5
                    p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, vel=p_velocity, frame = random.randint(0,7)))
        
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        elif self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)


        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surface, offset = (0, 0)):
        if abs(self.dashing) <= 50 and self.game.transition < 1:
            super().render(surface, offset = offset)

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
        self.nearestEnemy = returnEnemy

    def damage(self, damageAmount):
        if not self.damageCooldown:
            self.damageCooldown = 60
            self.game.health = max(0, self.game.health - damageAmount)
            self.game.sfx['hit'].play()
            if self.game.health == 0:

                self.game.screenshake = max(50, self.game.screenshake)
                for _ in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.game.player.rect().center, angle, 2 + random.random()))
                        self.game.particles.append(Particle(self.game, 'particle', self.game.player.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
                self.game.dead += 1
            else:
                self.game.screenshake = max(5, self.game.screenshake)
                for _ in range(10):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.game.player.rect().center, angle, 2 + random.random()))
                        self.game.particles.append(Particle(self.game, 'particle', self.game.player.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
    

class Cog(physicsEntity):
    def __init__(self, game, pos, size = (6,6)):
        super().__init__(game, 'cog', pos, size)

        #All spawn at the same point with 0 vel.
        self.velocity = [2 * (random.random()-0.5), -1.5]
        self.value = 1
        self.size = list(size)
        self.gravityAffected = True
        self.lightSize = 5
        
        self.animation.img_duration += (self.animation.img_duration*random.random()) 
        
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        self.velocity[0] *= 0.95

        if self.game.caveDarkness:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2 - 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2 - 2))


        #Check for player collision
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 40:
            self.game.walletTemp['cogs'] += self.value
            self.game.sfx['coin'].play()
            return True
    
    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

class HeartFragment(physicsEntity):
    def __init__(self, game, pos, size = (6,6)):
        super().__init__(game, 'heartFragment', pos, size)

        #All spawn at the same point with 0 vel.
        self.velocity = [2 * (random.random()-0.5), -1.5]
        self.value = 1
        self.size = list(size)
        self.gravityAffected = True
        self.lightSize = 5
        
        self.animation.img_duration += (self.animation.img_duration*random.random()) 
        
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        self.velocity[0] *= 0.95

        if self.game.caveDarkness:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2 - 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2 - 2))


        #Check for player collision
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 40:
            self.game.walletTemp['heartFragments'] += self.value
            self.game.sfx['coin'].play()
            return True
    
    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

class Wing(physicsEntity):
    def __init__(self, game, pos, size = (6,6)):
        super().__init__(game, 'wing', pos, size)

        #All spawn at the same point with 0 vel.
        self.velocity = [2 * (random.random()-0.5), -1.5]
        self.value = 1
        self.size = list(size)
        self.gravityAffected = True
        self.lightSize = 5
        
        self.animation.img_duration += (self.animation.img_duration*random.random()) 
        
    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        self.velocity[0] *= 0.95

        if self.game.caveDarkness:
            self.game.darknessCircle(0, self.lightSize, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2 - 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2 - 2))


        #Check for player collision
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 40:
            self.game.walletTemp['wings'] += self.value
            self.game.sfx['coin'].play()
            return True
    
    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

class Glowworm(physicsEntity):
    def __init__(self, game, pos, size = (5,5)):
        super().__init__(game, 'glowworm', pos, size)

        #All spawn at the same point with 0 vel.
        self.velocity = [(random.random()-0.5), -1.5]
        self.size = list(size)
        self.gravityAffected = False
        self.collideWall = False
        self.hoverDistance = 100
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
        
        if self.game.caveDarkness:
            self.game.darknessCircle(0, 6, (int(self.pos[0]) - self.game.render_scroll[0] + self.animation.img().get_width() / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.animation.img().get_height() / 2))
        
        super().update(tilemap, movement = movement)

    
    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

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
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

        if self.game.caveDarkness:
            self.game.darknessCircle(0, 15, (int(self.pos[0]) - self.game.render_scroll[0] + (1 if self.speed[0] < 0 else -1), int(self.pos[1]) - self.game.render_scroll[1]))


        
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
            
        
class Character(physicsEntity):
    def __init__(self, game, pos, size, name):
        
        super().__init__(game, name.lower(), pos, size)
        self.type = name.lower()
        self.name = name

        self.walking = 0
        self.canTalk = True
        self.newDialogue = False
        self.gravityAffected = True


    def update(self, tilemap, movement = (0, 0)):   

        if self.game.caveDarkness:
            self.game.darknessCircle(0, 50, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))


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

        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(self.game.tilemap, movement = movement)

        #Setting animation type
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if self.canTalk:
            distToPlayer = math.dist(self.rect().center, self.game.player.rect().center)
            if distToPlayer < 15:
                xpos = 2 * (self.pos[0] - self.game.render_scroll[0] + self.anim_offset[0] + 7)
                ypos = 2 * int(self.pos[1] - self.game.render_scroll[1] + self.anim_offset[1]) - 15
                
                self.game.draw_text('(z)', (xpos, ypos), self.game.text_font, (255, 255, 255), (0, 0), mode = 'center', scale = 0.75)
                if self.game.interractionFrame:
                    
                    self.game.run_text(self)
            elif distToPlayer >= 15 and self.newDialogue:
                xpos = 2 * (self.pos[0] - self.game.render_scroll[0] + self.anim_offset[0] + 7)
                ypos = 2 * int(self.pos[1] - self.game.render_scroll[1] + self.anim_offset[1]) - 15
                
                self.game.draw_text('(!)', (xpos, ypos), self.game.text_font, (255, 255, 255), (0, 0), mode = 'center', scale = 0.75)
                

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)



    def getConversation(self):
        self.game.update_dialogues()
        dialogue = self.game.dialogueHistory[self.name]
        
        for index in range(int(len(dialogue) / 2)):
            available = dialogue[str(index) + 'available']
            said = dialogue[str(index) + 'said']
            

            if not available:
                return(self.dialogue[str(index - 1)], index - 1)
            
            elif available and not said:
                #self.game.dialogueHistory[str(self.name)][str(index) + 'said'] = True
                return(self.dialogue[str(index)], index)
        
        index = int(len(dialogue) / 2) - 1
        #self.game.dialogueHistory[str(self.name)][str(index) + 'said'] = True
        return(self.dialogue[str(index)], int(index))

class Hilbert(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Hilbert')

        self.dialogue = {
            '0': ['Oh no! My hotel was attacked!',
                    'The whole thing has collapsed into the ground!',
                    'Would you be able to help me take back control,',
                    '...and find my friends somewhere in the hotel?',
                    'Oh! You can dash attack with your x key?',
                    'How original...'],

            '1': ['Anyway, we\'ll need to fix the portal elevator over there.',
                  'It works a bit but it\'ll only take you up one floor.',
                  'Please bring my back the cogs that were stolen!',
                  'I\'m gonna need about 5 cogs to start these repairs.'],

            '2': ['Thanks for getting some cogs woow!',
                    'I just realised I actually need another 50 though.',
                    'Be careful! The floors get bigger as you ascend!',
                    'Which makes no structural sense, I dont know how it works!',
                    'Oh and if you get lost, follow the fireflies!'],

            '3': ['Amazing job wow!',
                    'Really sorry but I still need 100 more.',
                    'I think I heard some bats around earlier, watch out for them.',
                    'They fly around and suddenly go AHHH at you, ya know?'],

            '4': ['Phenomenal work, my little slave!!',
                  'I dont know what else to do but please keep exploring!']  }

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement)

    def getConversation(self):
        return super().getConversation()

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.

        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.dialogueHistory[self.name]['1available'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currentDifficulty = 5
            self.game.currentLevelSize = 25
            self.game.wallet['cogs'] -= 5

        elif key == 3 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currentDifficulty = 20
            self.game.currentLevelSize = 30
            self.game.wallet['cogs'] -= 50

            self.game.availableEnemyVariants['4'] = 3
            
        elif key == 4 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currentDifficulty = 50
            self.game.currentLevelSize = 40
            self.game.wallet['cogs'] -= 100

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True
       



class Noether(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Noether')

        self.dialogue = {
            '0': ['Oh by golly gosh am I lost!',
                    'Do you know the way back to the lobby?',
                    'Brilliant, cheers Ill follow you back!'],

            '1': ['Oh yeah by the way I\'m also quite useful \'round here.',
                  'I can make you extra hearts!',
                  'I just need a few Heart Fragments!',
                  'Bring me 5 and the heart is yours!'],

            '2': ['You\'ve got two hearts! Woo!',
                    'Ew, these things are disgusting,',
                    '...and still beating! EW!',
                    'Hearts are super useful!',
                    'If you run out, you\'ll lose half your stuff :(',
                    'I\'ll give ya another for 20 fragments.'],

            '3': ['You\'ve got three hearts! Woo!',
                    'Look at you go, youll be a cat in no time!',
                    'I\'ll give ya another for 50 fragments.'],

            '4': ['You\'ve got four hearts! Woo!',
                    'Did you know that hagfish also have four hearts?',
                    'I\'ll give ya another for 100 fragments.'],
                     
            '5': ['You\'ve got five hearts! Woo!',
                  'Similarly, earthworms also have five!',
                  'Sorry chief! All out of hearts for now :('] }

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement)

    def getConversation(self):
        return super().getConversation()

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Noether'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.maxHealth += 1
            self.game.health = self.game.maxHealth

            self.game.wallet['heartFragments'] -= 5

        elif key == 3 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.maxHealth += 1
            self.game.health = self.game.maxHealth

            self.game.wallet['heartFragments'] -= 20
            
        elif key == 4 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.maxHealth += 1
            self.game.health = self.game.maxHealth

            self.game.wallet['heartFragments'] -= 50

        elif key == 5 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.maxHealth += 1
            self.game.health = self.game.maxHealth

            self.game.wallet['heartFragments'] -= 100

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True
        

class Curie(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Curie')

        self.dialogue = {
            '0': ['Oh by golly gosh am I lost!',
                    'Do you know the way back to the lobby?',
                    'Brilliant, cheers I\'ll follow you back!'],

            '1': ['Oh yeah by the way I\'m also quite useful \'round here.',
                  'I can make you winged boots!',
                  'They let you jump more in the air!',
                  'I just need a few bat wings!',
                  'Bring me 5 and the extra jump is yours!'],

            '2': ['You\'ve got two jumps! Woo!',
                    'Isn\'t this such a novel mechanic?',
                    'I\'ll give ya another for 50 wings.'],

            '3': ['You\'ve got three jumps! Woo!',
                    'We\'re really pushing this double jump idea.',
                    'I\'ll give ya another for 100 wings.'],
            
            '4': ['You\'ve got four jumps! Woo!',
                  'How many is too many?',
                  'Sorry chief! All out of boots for now.']}

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement)

    def getConversation(self):
        return super().getConversation()

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Curie'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 5

        elif key == 3 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 50

        elif key == 4 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 100

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True

            

        

    