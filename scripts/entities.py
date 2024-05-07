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
        if self.gravityAffected:
            self.velocity[1] = min(self.velocity[1] + self.gravity, self.terminal_vel)

        #Reset velocity if vertically hit tile
        if self.collisions['up'] or self.collisions['down']:
            self.velocity[1] = 0


        self.animation.update()
        

    def render(self, surface, offset = (0, 0)):
        posx = self.pos[0] - offset[0] + self.anim_offset[0]
        posy = self.pos[1] - offset[1] + self.anim_offset[1]
        
        surface.blit(pygame.transform.flip(self.animation.img(), self.flip_x, False), (posx, posy))



    def kill(self, coinCount, coinValue, screenshakeValue = 10, intensity = 10):
        self.game.screenshake = max(screenshakeValue, self.game.screenshake)
        self.game.sfx['hit'].play()
        for _ in range(intensity):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5

            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random() * (intensity / 10)))
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, vel = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0,7)))
        
        self.game.sparks.append(Spark(self.rect().center, 0, intensity / 2))
        self.game.sparks.append(Spark(self.rect().center, math.pi, intensity / 2))

        #Create coins
        spawnLoc = (int(self.pos[0] // self.game.tilemap.tile_size), int(self.pos[1] // self.game.tilemap.tile_size))
        spawnLoc = ((spawnLoc[0] * self.game.tilemap.tile_size) + self.game.tilemap.tile_size/2, (spawnLoc[1] * self.game.tilemap.tile_size) + self.game.tilemap.tile_size/2)
        
        for _ in range(coinCount):
            self.game.coins.append(Coin(self.game, spawnLoc, coinValue))



class Bat(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'bat', pos, size)

        self.coinCount = 3
        self.coinValue = 1

        self.deathIntensity = 5

        self.gravityAffected = False

        self.grace = random.randint(90,210)
        self.graceDone = False
        self.set_action('grace')

    def update(self, tilemap, movement = (0, 0)):

        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.graceDone = True
            self.animation.update()

        if self.graceDone:
            super().update(tilemap, movement = movement)

        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(self.coinCount, self.coinValue, screenshakeValue = 10, intensity = self.deathIntensity)
                return True


    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)


class GunGuy(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'gunguy', pos, size)

        self.coinCount = 1
        self.coinValue = 1

        self.deathIntensity = 5


        if random.random() < 0.5:
            self.flip_x = True

        self.walking = 0
        self.attack_dist_y = 24
        self.bullet_speed = 1.5
        self.shootCountdown = 0
        self.gunIndex = 0
        self.gravityAffected = True

        

        self.grace = random.randint(90,210)
        self.graceDone = False
        self.set_action('grace')
    
    def update(self, tilemap, movement = (0, 0)):
        
        if not self.graceDone:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.graceDone = True
            self.animation.update()
           
            
        if self.graceDone:
            #Walking logic, turning around etc
            if self.shootCountdown:
                self.shootCountdown = max(self.shootCountdown - 1, 0)
                self.gunIndex = math.ceil(self.shootCountdown / 20)
                
                if not self.shootCountdown:
                    # dist = self.game.player.pos[0] - self.pos[0]
                    
                    if self.flip_x:
                            self.game.sfx['shoot'].play()
                            self.game.projectiles.append(Bullet(self.game, [self.rect().centerx - 5, self.rect().centery], -self.bullet_speed))
                            for _ in range(4):
                                self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5 + math.pi, 2 + random.random()))
                    if not self.flip_x:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append(Bullet(self.game, [self.rect().centerx - 5, self.rect().centery], self.bullet_speed))
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5, 2 + random.random()))
                    

            elif self.walking:
                # if tilemap.solid_check((self.rect().centerx + (-7 if self.flip_x else 7), self.pos[1] + 23)):
                if (self.collisions['left'] or self.collisions['right']):
                    self.flip_x = not self.flip_x
                else:
                    movement = (movement[0] - 0.5 if self.flip_x else 0.5, movement[1])
                # else:
                #     self.flip_x = not self.flip_x
                self.walking = max(self.walking - 1, 0)

                #Attack condition
                if not self.walking:
                    disty = self.game.player.pos[1] - self.pos[1]
                    distx = self.game.player.pos[0] - self.pos[0]
                    #Y axis condition:
                    if abs(disty) < self.attack_dist_y and not self.game.dead:
                        #X axis condition
                        if (self.flip_x and distx < 0) or (not self.flip_x and distx > 0):
                            self.shootCountdown = 60
                       
            
            
           
           
            elif random.random() < 0.01:
                self.walking = random.randint(30, 120)


            super().update(tilemap, movement = movement)

            #Setting animation type
            if self.action != 'shooting':
                if movement[0] != 0:
                    self.set_action('run')
                    
                else:
                    self.set_action('idle')
                

        #Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(self.coinCount, self.coinValue, screenshakeValue = 10, intensity = self.deathIntensity)
                return True

                

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

        if self.flip_x:
            xpos = self.rect().centerx - 2 - self.game.assets['guns'][self.gunIndex].get_width() - offset[0]
            ypos = self.rect().centery - offset[1]
            surface.blit(pygame.transform.flip(self.game.assets['guns'][self.gunIndex], True, False), (xpos, ypos))
        else:
            xpos = self.rect().centerx + 2 - offset[0]
            ypos = self.rect().centery - offset[1]
            surface.blit(self.game.assets['guns'][self.gunIndex], (xpos, ypos))

class Portal(physicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'portal', pos, size)
        self.anim_offset = (0, 0)

    def update(self, game):
        self.animation.update()
        if len(self.game.enemies) == 0 or self.game.currentLevel == 'lobby':
            self.set_action('active')

        playerRect = self.game.player.rect()
        if self.rect().colliderect(playerRect) and self.game.transition == 0:
            
            if self.game.currentLevel == 'lobby':
                self.game.floor += 1
                self.game.transitionToLevel('random')
            elif self.game.currentLevel == 'random' and self.action == 'active':
                self.game.transitionToLevel('lobby')
                
            

class Player(physicsEntity):

    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0

        self.total_jumps = 2
        self.jumps = self.total_jumps

        self.wall_slide = False

        self.spark_timer = 0
        self.spark_timer_max = 60
        self.gravityAffected = True

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
     
    
        
        self.air_time += 1
        if self.air_time > 180 and not self.wall_slide:
            # self.game.dead += 1
            pass
        if self.spark_timer:
            self.spark_timer = max(self.spark_timer - 1, 0)
        

        
        if self.collisions['down']:
            if self.air_time > 15 and not self.spark_timer and not self.game.transition and abs(self.dashing) > 10:
                self.spark_timer = self.spark_timer_max
                for _ in range(5):
                    angle = (random.random()) * math.pi
                    speed = random.random() * (2)
                    extra = 2 if self.dashing else 0
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
            self.velocity[1] = -2.5
            self.air_time = 5
            self.jumps = max(0, self.jumps - 1)

            if self.flip_x and self.last_movement[0] < 0:
                self.velocity[0] = 1.5
                for _ in range(5):
                        angle = (random.random() + 2) * (math.pi / 4)
                        speed = random.random() * (2)
                       
                        self.game.sparks.append(Spark((self.rect().centerx, self.rect().bottom), angle, speed, color = (190, 200, 220)))
                return True


            elif not self.flip_x and self.last_movement[0] > 0:
                self.velocity[0] = -1.5
                for _ in range(5):
                        angle = (random.random() + 1) * (math.pi / 4)
                        
                        speed = random.random() * (2)
                        self.game.sparks.append(Spark((self.rect().centerx, self.rect().bottom), angle, speed, color = (190, 200, 220)))
                return True
               


        elif self.jumps > 0:
            self.jumps -= 1
            self.velocity[1] = min(self.velocity[1], -3)
            self.air_time = 5
            for _ in range(5):
                    angle = (random.random()) * math.pi
                    speed = random.random() * (2)
                    self.game.sparks.append(Spark((self.rect().centerx, self.rect().bottom), angle, speed, color = (190, 200, 220)))
                
            return True

    def dash(self):
        if not self.dashing:
            self.spark_timer = 0
            self.game.sfx['dash'].play()
            if self.flip_x:
                self.dashing = -self.dash_dist
            else:
                self.dashing = self.dash_dist

    def damage(self, damageAmount):

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

class Coin(physicsEntity):
    def __init__(self, game, pos, value, size = (6,6)):
        super().__init__(game, 'coin', pos, size)

        #All spawn at the same point with 0 vel.
        self.velocity = [(random.random()-0.5), -1.5]
        self.value = value
        self.size = list(size)
        self.gravityAffected = True
        

        

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement = movement)
        self.velocity[0] *= 0.95



        #Check for player collision
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 10:
            self.game.moneyThisRun += self.value
            return True
    
    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

class Bullet():
    def __init__(self, game, pos, speed):
        self.pos = list(pos)
        self.game = game
        self.speed = speed
        self.type = 'projectile'
        self.img = self.game.assets[self.type]

        self.attackPower = 1

    def update(self, game):
        self.game.display_outline.blit(self.img, (self.pos[0] - self.img.get_width() / 2 - self.game.render_scroll[0], self.pos[1] - self.img.get_height() / 2 - self.game.render_scroll[1]))
        self.pos[0] += self.speed

        #Check to destroy
        if self.game.tilemap.solid_check(self.pos):
            for _ in range(4):
                self.game.sparks.append(Spark(self.pos, random.random() - 0.5 + (math.pi if self.speed > 0 else 0), 2 + random.random()))
            return True
        # elif self.pos[0] > 500:
        #     return True
        
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

        if self.canTalk and not self.game.transition:
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
            '0': ['Oh no! Our hotel was attacked!',
                    'The whole thing has collapsed into the ground!',
                    'Please help us make it safe again!',
                    'By getting 5 moneys for me!'],
            '1': ['Thanks for getting some money woow!',
                    'Now go get 50 pls',
                    'The maps should now be bigger and harder :)'],
            '2': ['Amazing job wow!',
                    'Now go get 100 pls',
                    'Again, bigger and harder :)'],
            '3': ['phenomenal work, my little slave',
                    'thanks a bunch, now the maps are huge!']  }

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)

    def update(self, tilemap, movement = (0, 0)):
        super().update(tilemap, movement)

    def getConversation(self):
        return super().getConversation()

    def conversationAction(self, key):
        #Runs when dialogue matching key is said
        
        if key == 1 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currentDifficulty = 10
            self.game.currentLevelSize = 20
            self.game.money -= 5

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currentDifficulty = 20
            self.game.currentLevelSize = 30
            self.game.money -= 50
            
        elif key == 3 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currentDifficulty = 50
            self.game.currentLevelSize = 50
            self.game.money -= 100

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True

            

        

    