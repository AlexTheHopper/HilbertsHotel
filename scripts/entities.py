"""
Entities module for Hilbert's Hotel.
Includes all entity behaviour.
"""
import pygame
import sys
import math
import random
import numpy as np
import copy
import scripts.particle as _particle
import scripts.spark as _spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False,
                           'left': False, 'right': False}
        self.collide_wall_check = True
        self.collide_wall = True
        self.is_boss = False
        self.attack_power = 1
        self.attack_states = []

        self.terminal_vel = 5
        self.gravity = 0.12
        self.light_size = 0
        self.death_intensity = 5
        self.friendly = False

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip_x = False
        self.set_action('idle')
        self.render_distance = self.game.screen_width / 3

        self.frame_movement = [0, 0]
        self.last_movement = [0, 0]

        self.dashing = 0
        self.dash_dist = 60

        self.currency_drops = {
            'cog': 0,
            'redCog': 0,
            'blueCog': 0,
            'purpleCog': 0,
            'heartFragment': 0,
            'wing': 0,
            'eye': 0,
            'chitin': 0,
            'fairyBread': 0,
            'boxingGlove': 0,
            'yellowOrb': 0,
            'redOrb': 0,
            'hammer': 0,
            'credit': 0
        }

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action, override = False):
        if action != self.action or override:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def too_far_to_render(self):
        # Only update/render at close distances
        render_dist_to_player = np.linalg.norm(self.vector_to(self.game.player))
        if render_dist_to_player > self.render_distance and not self.is_boss:
            return True

    def update(self, tilemap, movement=(0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1]))
        self.collisions = {'up': False, 'down': False,
                           'left': False, 'right': False}

        # Forced movement plus velocity already there
        self.frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        self.last_movement = movement

        if self.collide_wall_check:
            # Check for collision with physics tiles
            self.pos[1] += self.frame_movement[1]
            entity_rect = self.rect()
            for rect in tilemap.physics_rects_around(self.rect().center, is_boss=self.is_boss):
                if entity_rect.colliderect(rect):

                    # Collision moving down
                    if self.frame_movement[1] > 0:
                        entity_rect.bottom = rect.top
                        self.collisions['down'] = True

                    # Collision moving up
                    elif self.frame_movement[1] < 0:
                        entity_rect.top = rect.bottom
                        self.collisions['up'] = True
                    if self.collide_wall:
                        self.pos[1] = entity_rect.y

                    if self.type == 'player':
                        self.last_collided_wall = self.game.tilemap.tilemap[str(
                            rect.x // self.game.tilemap.tilesize) + ';' + str(rect.y // self.game.tilemap.tilesize)]

            self.pos[0] += self.frame_movement[0]
            entity_rect = self.rect()
            for rect in tilemap.physics_rects_around(self.rect().center, is_boss=self.is_boss):
                if entity_rect.colliderect(rect):

                    # Collision moving right
                    if self.frame_movement[0] > 0:
                        entity_rect.right = rect.left
                        self.collisions['right'] = True

                    # Collision moving left
                    elif self.frame_movement[0] < 0:
                        entity_rect.left = rect.right
                        self.collisions['left'] = True
                    if self.collide_wall:
                        self.pos[0] = entity_rect.x

                    if self.type == 'player':
                        self.last_collided_wall = self.game.tilemap.tilemap[str(
                            rect.x // self.game.tilemap.tilesize) + ';' + str(rect.y // self.game.tilemap.tilesize)]

        # Facing direction
        if movement[0] > 0:
            self.flip_x = False
        elif movement[0] < 0:
            self.flip_x = True

        # Add gravity up to terminal velocity
        if self.gravity_affected and not (self.collisions['down'] or self.collisions['up']):
            self.velocity[1] = min(self.velocity[1] + self.gravity, self.terminal_vel)

        # Reset velocity if vertically hit tile if affected by gravity:
        if (self.collisions['up'] or self.collisions['down']) and self.gravity_affected:
            self.velocity[1] = 0

        self.animation.update()
        self.display_darkness_circle()

    def render(self, surface, offset=(0, 0), rotation=0, transparency=255, scale=1):
        # Only update/render at close distances
        posx = self.pos[0] - offset[0] + self.anim_offset[0]
        if posx < -self.size[0]*2 or posx > surface.get_size()[0]:
            return False
        posy = self.pos[1] - offset[1] + self.anim_offset[1]
        if posy < -self.size[1]*2 or posy > surface.get_size()[1]:
            return False

        image = self.animation.img()
        image.set_alpha(transparency)
        if scale != 1:
            image = pygame.transform.scale(image, (scale * image.get_width(), scale * image.get_height()))

        if rotation != 0:
            rot_image = pygame.transform.rotate(image, rotation * 180 / math.pi)
            new_rect = rot_image.get_rect(center=image.get_rect(topleft=(posx, posy)).center)

            surface.blit(pygame.transform.flip(rot_image, self.flip_x, False), new_rect.topleft)
        else:
            surface.blit(pygame.transform.flip(image, self.flip_x, False), (math.floor(posx), math.floor(posy)))

    def damage(self, intensity=10):
        self.game.screenshake = max(intensity, self.game.screenshake)
        self.game.sfx['hit'].play()
        for _ in range(intensity):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(
                _spark.Spark(self.rect().center, angle, 2 + random.random() * (intensity / 10)))
            self.game.particles.append(_particle.Particle(self.game, 'particle1', self.rect().center, vel=[math.cos(
                angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))

        self.game.sparks.append(_spark.Spark(self.rect().center, 0, intensity / 4))
        self.game.sparks.append(
            _spark.Spark(self.rect().center, math.pi, intensity / 4))

    def kill(self):
        self.game.screenshake = max(self.death_intensity, self.game.screenshake)
        self.game.sfx['hit'].play()
        for _ in range(self.death_intensity):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(_spark.Spark(self.rect().center, angle, 2 + random.random() * (self.death_intensity / 10)))
            self.game.particles.append(_particle.Particle(self.game, 'particle1', self.rect().center, vel=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))

        if self.is_boss:
            self.game.sparks.append(_spark.Spark(self.rect().center, 0, self.death_intensity / 2))
            self.game.sparks.append(_spark.Spark(self.rect().center, math.pi, self.death_intensity / 2))
            self.game.extra_entities.append(HeartAltar(self.game, self.pos, self.game.entity_info[18]['size'], falling = True, value = 3))

        # Create currencies only iff not boss - bosses drop currency in their own method.
        # Need to make sure the currency wont spawn in a physics tile.
        if not self.is_boss:
            spawn_loc = (self.pos[0] + (self.size[0] / 2) - 3, self.pos[1] + (self.size[1] / 2) - 3)

            for currency in self.currency_drops.keys():
                for _ in range(self.currency_drops[currency]):
                    self.game.currency_entities.append(Currency(self.game, currency, spawn_loc))

    def display_darkness_circle(self, offset = False):
        position = [self.rect().centerx, self.rect().centery]
        if offset:
            position[0] += offset[0]
            position[1] += offset[1]
        if self.game.cave_darkness and self.game.transition <= 0 and self.light_size > 0:
            self.game.darkness_circle(0, self.light_size, (position[0] - self.game.render_scroll[0], position[1] - self.game.render_scroll[1]))

    def check_damages(self, dash_die = True, bullet_die = True, player_contact = True):
        # Die if dashed through
        if abs(self.game.player.dashing) >= 50 and dash_die and not self.friendly:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill()
                return True

        # Also dies if hit by bullet:
        if bullet_die:
            for projectile in self.game.projectiles:
                if self.rect().collidepoint(projectile.pos) and projectile.type != 'spine':
                    self.kill()
                    self.game.projectiles.remove(projectile)
                    return True

        # Damages non-dashing player on contact
        if self.game.player.rect().colliderect(self.rect()) and player_contact:
            if abs(self.game.player.dashing) < 50 and self.action in self.attack_states and not self.game.dead and not self.friendly:
                self.game.player.damage(self.attack_power, self.type)

    def wall_rebound(self):
        if self.collisions['left'] or self.collisions['right']:
            self.velocity[0] *= -1
            self.flip_x = not self.flip_x
        elif self.collisions['up'] or self.collisions['down']:
            self.velocity[1] *= -1

    def flip_reset(self):
        if self.velocity[0] < 0:
            self.flip_x = True
        elif self.velocity[0] > 0:
            self.flip_x = False

    def check_line_to_player(self):
        x1, y1 = self.rect().centerx, self.rect().centery
        x2, y2 = self.game.player.rect().centerx, self.game.player.rect().centery

        x_dist = x2 - x1
        y_dist = y2 - y1

        clear = True
        for n in range(10):
            x = int((x1 + (n/10) * x_dist) // 16)
            y = int((y1 + (n/10) * y_dist) // 16)
            loc = str(x) + ';' + str(y)
            if loc in self.game.tilemap.tilemap:
                clear = False
        return clear

    def vector_to(self, other):
        rect_o = self.rect()
        rect_d = other.rect()
        return [rect_d.centerx - rect_o.centerx, rect_d.centery - rect_o.centery]

    def circular_attack(self, radius, pos=[0, 0], color=(random.randint(150, 200), 0, 0), color_str='red', can_damage_boss=False):
        for _ in range(int(radius / 3)):
            start_angle = random.random() * math.pi * 2
            end_angle = start_angle + math.pi / 6 + random.random() * math.pi / 3
            speed = random.random() * 2 + 1
            if pos == [0, 0]:
                pos = self.rect().center
            self.game.sparks.append(_spark.ExpandingArc(pos, radius, start_angle, end_angle, speed, color, color_str=color_str,can_damage_boss=can_damage_boss, width=5, damage=self.attack_power, type=self.type))

    def colour_change(self, image, old_c, new_c):
        img = pygame.Surface(image.get_size())
        img.fill(new_c)
        image.set_colorkey(old_c)
        img.blit(image, (0, 0))
        img.set_colorkey((0, 0, 0))
        return img

class Bat(PhysicsEntity):
    def __init__(self, game, pos, size, grace_done=False, velocity=[0, 0], friendly = False):
        super().__init__(game, 'bat', pos, size)

        self.currency_drops['cog'] = random.randint(0, 3)
        self.currency_drops['heartFragment'] = 1 if random.random() < 0.2 else 0
        self.currency_drops['wing'] =1 if random.random() < 0.8 else 0

        self.attack_power = 1
        self.death_intensity = 10
        self.attack_states = ['attacking']

        self.gravity_affected = False
        self.grace = random.randint(90, 210)
        self.grace_done = grace_done
        self.set_action('grace')
        if self.grace_done:
            self.set_action('attacking')
            self.timer = 120
            self.velocity = velocity

        self.friendly = friendly
        if self.friendly:
            self.set_action('idle')
            self.velocity = [random.random() - 0.5, random.random() - 0.5]

        self.is_attacking = False
        self.anim_offset = (-3, -2)
        self.timer = 0
        self.pos[1] += 9
        self.pos[0] += 4
        self.to_player = [0, 0]

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(180, 500)
                self.velocity = [
                    random.random() - 1/2, random.random()*0.5 + 0.5]
                self.grace_done = True

            self.animation.update()

        if self.grace_done:
            if self.action == 'idle':
                self.timer = max(self.timer - 1, 0)

                if np.linalg.norm(self.velocity) > 5:
                    self.velocity[0] *= 0.99
                    self.velocity[1] *= 0.99

                if not self.timer and not self.friendly:
                    self.set_action('charging')
                    to_player = self.vector_to(self.game.player)
                    self.to_player = to_player / np.linalg.norm(to_player)
                    self.velocity = [-self.to_player[0] * 0.15, -self.to_player[1] * 0.15]

                    self.timer = random.randint(90, 120)

            elif self.action == 'charging':
                self.timer = max(self.timer - 1, 0)

                if self.timer == 0:
                    self.velocity[0] = self.to_player[0] * 2
                    self.velocity[1] = self.to_player[1] * 2
                    self.timer = 120
                    self.set_action('attacking')

            elif self.action == 'attacking':
                self.timer = max(self.timer - 1, 0)
                if any(self.collisions.values()) and not self.timer:
                    self.set_action('idle')
                    self.timer = random.randint(180, 500)

            if self.action != 'charging':
                if self.collisions['up'] or self.collisions['down']:
                    self.velocity[1] = -self.velocity[1] * 0.9
                elif self.collisions['left'] or self.collisions['right']:
                    self.velocity[0] = -self.velocity[0] * 0.9

        if self.check_damages():
            return True

    def render(self, surface, offset=(0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        angle = 0
        if self.action in ['charging', 'attacking']:
            angle = math.atan2(-self.velocity[1], self.velocity[0]) + math.pi/2 + (
                math.pi if self.action == 'attacking' else 0)

        super().render(surface, offset=offset, rotation=angle)

class GunGuy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'gunguy', pos, size)
        self.death_intensity = 15
        self.difficulty_level = 1
        self.walking = 0
        self.flying = 0
        self.attack_dist_y = 24
        self.bullet_speed = 1.5
        self.shoot_countdown = 0
        self.weapon_index = 0
        self.light_size = 0
        self.gravity_affected = True
        self.pos[1] += 1

        self.can_have_staff = True if self.game.current_level != 'normal' or self.game.floors[str(self.game.current_level)] > 5 else False
        self.weapon = 'gun' if not self.can_have_staff else ('staff' if random.random() < (0.75 if self.game.current_level in ['spooky', 'space'] else 0.3) else 'gun')

        self.witch = False
        if self.weapon == 'staff' and self.game.floors['spooky'] > 1 and random.random() < 0.5:
            self.witch = True
        elif self.weapon == 'staff' and self.game.current_level == 'space' and random.random() < 0.75:
            self.witch = True

        self.staff_cooldown = 120
        self.trajectory = [0, 0]
        self.colours = [(196, 44, 54), (120, 31, 44)]
        if (self.game.difficulty >= 2 and self.game.current_level in ['normal', 'space']) or self.game.power_level >= self.game.difficulty:
            self.difficulty_level = random.randint(0, self.game.difficulty)
            if self.difficulty_level == 2:
                self.type = 'gunguyRed'
                self.colours = [(255, 106, 0), (198, 61, 1)]
            elif self.difficulty_level == 3:
                self.type = 'gunguyBlue'
                self.colours = [(0, 132, 188), (0, 88, 188)]
            elif self.difficulty_level == 4:
                self.type = 'gunguyPurple'
                self.colours = [(127, 29, 116), (99, 22, 90)]

        self.currency_drops['cog'] = random.randint(2, 4)
        self.currency_drops['redCog'] = random.randint(1, 3) if (self.type == 'gunguyRed') else 0
        self.currency_drops['blueCog'] = random.randint(1, 3) if (self.type == 'gunguyBlue') else 0
        self.currency_drops['purpleCog'] = random.randint(1, 3) if (self.type == 'gunguyPurple') else 0
        self.currency_drops['heartFragment'] = 1 if self.weapon == 'staff' else (1 if random.random() < 0.1 else 0)
        self.currency_drops['wing'] = random.randint(0, 3) if self.witch else 0

        self.label = self.type + ('Witch' if self.witch else ('Staff' if self.weapon == 'staff' else ''))

        if random.random() < 0.5:
            self.flip_x = True

        self.grace = random.randint(60, 120)
        self.grace_done = False
        self.set_action('grace')

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False

        self.display_darkness_circle()
        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.light_size <= 30 and not self.grace:
                self.light_size += 1
            elif self.light_size >= 30:
                self.set_action('idle')
                self.grace_done = True
                
            self.animation.update()

        if not self.flying:
            if self.velocity[0] > 0:
                self.velocity[0] = max(self.velocity[0] - 0.1, 0)
            else:
                self.velocity[0] = min(self.velocity[0] + 0.1, 0)

        if self.staff_cooldown:
            self.staff_cooldown = max(self.staff_cooldown - 1, 0)

        if self.grace_done:
            # Walking logic, turning around etc
            if self.shoot_countdown:
                self.shoot_countdown = max(self.shoot_countdown - 1, 0)
                self.weapon_index = math.ceil(self.shoot_countdown / 20)

                # Shoot condition
                if not self.shoot_countdown:
                    # offsets for asset sizes
                    bullet_offset = [4, -4] if self.weapon == 'staff' else [5, 0]
                    bullet_velocity = [-self.bullet_speed, 0] if self.flip_x else [self.bullet_speed, 0]

                    # Vector to player if staff
                    if self.weapon == 'staff':
                        to_player = (self.game.player.pos[0] - self.pos[0] + (bullet_offset[0] if self.flip_x else -bullet_offset[0]), self.game.player.pos[1] - self.pos[1])
                        bullet_velocity = to_player / np.linalg.norm(to_player) * 1.5
                        self.staff_cooldown = 0

                    # Create bullet/bat/meteor
                    if self.witch and self.game.current_level == 'space':
                        # Find empty space near/on player and summon meteor
                        found_spot = False
                        check_spot = [0, 0]
                        player_pos_tile = (self.game.player.pos[0] // self.game.tilemap.tilesize, self.game.player.pos[1] // self.game.tilemap.tilesize)

                        while not found_spot:
                            check_spot[0], check_spot[1] = int(player_pos_tile[0] + random.choice(
                                range(-3, 4))), int(player_pos_tile[1] + random.choice(range(-2, 3)))
                            loc_str = str(check_spot[0]) + ';' + str(check_spot[1])
                            if loc_str not in self.game.tilemap.tilemap:
                                found_spot = True
                        self.game.extra_entities.append(Meteor(
                            self.game, (check_spot[0] * self.game.tilemap.tilesize, check_spot[1] * self.game.tilemap.tilesize), (16, 16)))

                    elif self.witch and random.random() < 0.25:
                        batpos = (self.pos[0] - self.pos[0] % self.game.tilemap.tilesize,
                                  self.pos[1] - self.pos[1] % self.game.tilemap.tilesize - 5)
                        self.game.enemies.append(Bat(self.game, batpos, self.game.entity_info[4]['size'], grace_done=True, velocity=bullet_velocity))
                    else:
                        self.game.sfx['shoot' if self.weapon == 'gun' else 'laser'].play()
                        self.game.projectiles.append(Bullet(self.game, [self.rect().centerx - (bullet_offset[0] if self.flip_x else -bullet_offset[0]), self.rect().centery + bullet_offset[1]], bullet_velocity, self.label, type = f'projectile_{self.type.strip('gunguy')}'))
                        for _ in range(4):
                            self.game.sparks.append(_spark.Spark(self.game.projectiles[-1].pos, random.random() - 0.5 + (math.pi if self.flip_x else 0), 2 + random.random()))

            elif self.walking:
                # Check jump condition, tilemap in_front and above:
                in_front = tilemap.solid_check(
                    (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery))
                in_front_down = tilemap.solid_check(
                    (self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 16))
                above = tilemap.solid_check(
                    (self.rect().centerx, self.rect().centery - 16))

                if in_front and not above and self.collisions['down']:
                    above_side = tilemap.solid_check(
                        (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery - 16))
                    above_above_side = tilemap.solid_check(
                        (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery - 32))

                    # Check jump 2 space:
                    above_above = tilemap.solid_check(
                        (self.rect().centerx, self.rect().centery - 32))
                    if not above and not above_above and not above_above_side and above_side:
                        self.set_action('jump')
                        self.velocity[1] = -3
                        self.velocity[0] = (-0.5 if self.flip_x else 0.5)

                    # Jump one space
                    elif not above_side:
                        self.set_action('jump')
                        self.velocity[1] = -2
                        self.velocity[0] = (-0.5 if self.flip_x else 0.5)

                elif not in_front_down:
                    in_front_down2 = tilemap.solid_check(
                        (self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 32))
                    in_front_down3 = tilemap.solid_check(
                        (self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 48))
                    if not in_front_down2 and not in_front_down3:
                        self.flip_x = not self.flip_x
                        self.walking = random.randint(5, 15)

                # Turn around if bump into a wall
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
                # If setting new flying direction, dont fly into a wall
                pos_centre = [self.rect().centerx, self.rect().centery]
                left_empty = not tilemap.solid_check(
                    [pos_centre[0] - tilemap.tilesize, pos_centre[1]], return_value='bool')
                right_empty = not tilemap.solid_check(
                    [pos_centre[0] + tilemap.tilesize, pos_centre[1]], return_value='bool')
                up_empty = not tilemap.solid_check(
                    [pos_centre[0], pos_centre[1] - tilemap.tilesize], return_value='bool')
                down_empty = not tilemap.solid_check(
                    [pos_centre[0], pos_centre[1] + tilemap.tilesize], return_value='bool')

                if self.witch and not self.gravity_affected:
                    self.flying = random.randint(30, 90)
                    self.velocity = [
                        random.uniform(-left_empty, right_empty), random.uniform(-up_empty, down_empty)]
                    self.flip_reset()
                    self.set_action('run')

                # only activate flying mode if not surrounded by tiles
                elif self.witch and random.random() < 0.2 and up_empty:
                    self.gravity_affected = False
                    self.flying = random.randint(30, 90)
                    self.velocity = [random.uniform(-left_empty, right_empty), random.uniform(-up_empty, down_empty)]
                    self.flip_reset()
                    self.set_action('run')

                else:
                    self.walking = random.randint(30, 120)

            # Attack condition
            if (random.random() < 0.02):
                if (self.game.floors[self.game.current_level] != 1 or self.game.current_level == 'infinite') and not self.shoot_countdown:

                    if self.weapon == 'gun':
                        disty = self.game.player.pos[1] - self.pos[1]
                        distx = self.game.player.pos[0] - self.pos[0]
                        # Y axis condition:
                        if abs(disty) < self.attack_dist_y and not self.game.dead and self.check_line_to_player():
                            # X axis condition
                            if (self.flip_x and distx < 0) or (not self.flip_x and distx > 0):
                                self.shoot_countdown = 60
                                self.walking = 0

                    elif self.weapon == 'staff' and self.game.current_level == 'space' and self.witch:
                        distto_player = np.linalg.norm(self.vector_to(self.game.player))

                        if distto_player < self.game.screen_width / 8:
                            self.shoot_countdown = 60
                            self.walking = 0

                    elif self.weapon == 'staff':

                        self.staff_cooldown = 120
                        if self.check_line_to_player():
                            self.shoot_countdown = 60
                            self.walking = 0

            super().update(tilemap, movement=movement)

            # If flying and land on ground, stop flying
            if not self.gravity_affected and self.collisions['down']:
                if tilemap.solid_check([self.rect().center[0], self.rect().center[1] + tilemap.tilesize], return_value='bool'):
                    self.gravity_affected = True
                    self.flying = 0

            if not self.gravity_affected and random.random() < 0.1:
                self.game.sparks.append(_spark.Spark(self.rect().midbottom, random.random(
                ) * math.pi, random.random() * 2, color=random.choice(self.colours)))

            # Setting animation type
            if self.action == 'jump':
                if self.collisions['down']:
                    self.set_action('idle')
            if self.action not in ['shooting', 'jump']:
                if movement[0] != 0 or self.flying:
                    self.set_action('run')

                else:
                    self.set_action('idle')

        # Death Condition           
        if abs(self.game.player.dashing) >= 50 and self.rect().colliderect(self.game.player.rect()):
                if self.game.power_level >= self.difficulty_level:
                    self.kill()
                    return True

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)

        if self.action != 'grace':
            y_offset = (4 if self.weapon == 'staff' else 0) + (3 if (self.weapon == 'staff' and self.shoot_countdown) else 0)

            if self.flip_x:
                xpos = self.rect().centerx - 2 - self.game.assets['weapons/' +
                                     self.weapon][self.weapon_index].get_width() - offset[0]
                ypos = self.rect().centery - offset[1] - y_offset
                surface.blit(pygame.transform.flip(
                    self.game.assets['weapons/' + self.weapon][self.weapon_index], True, False), (xpos, ypos))
            else:
                xpos = self.rect().centerx + 2 - offset[0]
                ypos = self.rect().centery - offset[1] - y_offset
                surface.blit(
                    self.game.assets['weapons/' + self.weapon][self.weapon_index], (xpos, ypos))

            if self.witch:
                surface.blit(pygame.transform.flip(self.game.assets['witchHat'], self.flip_x, False), [
                             self.rect().midtop[0] - offset[0] - 7, self.rect().midtop[1] - offset[1] - 7])

class Portal(PhysicsEntity):
    def __init__(self, game, pos, size, destination):
        super().__init__(game, 'portal' + str(destination), pos, size)
        self.anim_offset = (0, 0)
        self.destination = destination
        self.light_size = 0
        self.colours = {
            'lobby': [(58, 6, 82), (111, 28, 117)],
            'normal': [(58, 6, 82), (111, 28, 117)],
            'grass': [(36, 120, 29), (12, 62, 8)],
            'spooky': [(55, 20, 15), (108, 50, 40)],
            'rubiks': [(255, 255, 255), (255, 255, 0), (255, 0, 0), (255, 153, 0), (0, 0, 255), (0, 204, 0)],
            'aussie': [(55, 20, 15)],
            'space': [(0, 0, 0), (255, 255, 255)],
            'heaven_hell': [(107, 176, 255), (255, 71, 68)], }
        self.colours['infinite'] = [
            colour for colours in self.colours.values() for colour in colours]

        if self.game.current_level == 'lobby':
            self.set_action('opening')

    def update(self, game):
        if self.too_far_to_render():
            return False
        self.animation.update()
        self.display_darkness_circle()
        # Changing state/action
        if self.action == 'idle' and (len(self.game.enemies) + len(self.game.bosses)) == 0:
            self.set_action('opening')
            self.game.sfx['ding'].play()

        if self.action == 'opening':
            self.light_size += 0.5
            if self.animation.done:
                self.set_action('active')

                if self.game.current_level != 'lobby':
                    self.game.sfx['ding'].play()

        # Decals
        if self.action in ['opening', 'active'] and self.destination in self.colours:
            if random.random() < (0.1 + (0.1 if self.action == 'active' else 0)):
                angle = (random.random()) * 2 * math.pi
                speed = random.random() * (3 if self.action == 'active' else 2)
                self.game.sparks.append(_spark.Spark(self.rect(
                ).center, angle, speed, color=random.choice(self.colours[self.destination])))

        # Collision and level change
        player_rect = self.game.player.rect()
        if self.rect().colliderect(player_rect) and self.action == 'active' and self.game.transition == 0:
            if self.game.interraction_frame_int:
                if self.destination == 'infinite':
                    self.game.infinite_mode_active = True
                else:
                    self.game.infinite_mode_active = False
                self.game.transition_to_level(self.destination)

                self.set_action('closing')

            else:
                xpos = (self.rect().centerx - self.game.render_scroll[0]) - 7
                ypos = (self.rect().centery -self.game.render_scroll[1]) - 22

                self.game.hud_display.blit(self.game.control_icons['Interract'], (xpos, ypos))

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0

        self.total_jumps = 1
        self.jumps = self.total_jumps

        self.total_dashes = 1
        self.dashes = self.total_dashes
        self.can_dash = True

        self.wall_slide = False
        self.last_collided_wall = False

        self.spark_timer = 0
        self.spark_timer_max = 60
        self.gravity_affected = True
        self.nearest_enemy = False
        self.damage_cooldown = 0
        self.light_size = 90
        self.anim_offset = (-3, -7)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1

        if self.damage_cooldown:
            self.damage_cooldown = max(self.damage_cooldown - 1, 0)

        if self.spark_timer:
            self.spark_timer = max(self.spark_timer - 1, 0)

        if self.collisions['down']:
            if self.air_time > 20 and not self.spark_timer and not self.game.transition:
                self.spark_timer = self.spark_timer_max
                for _ in range(5):
                    angle = (random.random()) * math.pi
                    speed = random.random() * (2)
                    extra = 2 if abs(self.dashing) > 40 else 0
                    self.game.sparks.append(_spark.Spark((self.rect().centerx, self.rect(
                    ).bottom), angle, speed + extra, color=(190, 200, 220)))
            self.air_time = 0
            self.jumps = self.total_jumps

        if self.collisions['up'] and not self.spark_timer and self.dashing and not self.game.transition:
            self.spark_timer = self.spark_timer_max
            for _ in range(5):
                angle = (random.random()) * math.pi
                speed = random.random() * (2)
                extra = 2 if self.dashing else 0
                self.game.sparks.append(_spark.Spark((self.rect().centerx, self.rect(
                ).top), angle, speed + extra, color=(190, 200, 220)))

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
                    self.game.sparks.append(_spark.Spark(((self.rect().left if self.collisions['left'] else self.rect(
                    ).right), self.rect().centery), angle, speed + extra, color=(190, 200, 220)))

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

            # Set dashing vel. and normalise for diagonal movement
            self.velocity[1] = self.downwards * 8 / (math.sqrt(2) if self.sideways else 1)
            self.velocity[0] = self.sideways * 8 / (math.sqrt(2) if self.downwards else 1)

            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
                self.velocity[1] *= 0.1

            if self.game.transition < 1:
                p_velocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
                self.game.particles.append(_particle.Particle(self.game, 'particle' + str(self.game.power_level), self.rect(
                ).center, vel=[movement[0] + random.random(), movement[1] + random.random()], frame=random.randint(0, 7)))

            # Breaking cracked tiles:
            if any(self.collisions.values()) and (self.game.wallet['hammers']) > 0:
                if self.last_collided_wall['type'] == 'cracked':

                    # Find correct tunnel:
                    for tunnel_name in self.game.tunnels_broken.keys():
                        if any(loc == self.last_collided_wall['pos'] for loc in self.game.tunnel_positions[tunnel_name]) and (tunnel_name == 'tunnel7' or self.game.tunnels_broken['tunnel7']):

                            # Actually break all the tiles and save tunnel as broken:
                            for loc in self.game.tunnel_positions[tunnel_name]:
                                if self.game.tilemap.tilemap[str(loc[0]) + ';' + str(loc[1])]['type'] == 'cracked':
                                    del self.game.tilemap.tilemap[str(loc[0]) + ';' + str(loc[1])]
                                    for _ in range(3):
                                        self.game.sparks.append(_spark.Spark(
                                        (loc[0] * self.game.tilemap.tilesize, loc[1] * self.game.tilemap.tilesize), random.random() * math.pi * 2, random.random() * 2 + 2))

                            self.game.tunnels_broken[tunnel_name] = True
                            self.game.wallet['hammers'] -= 1

        elif abs(self.dashing) in {60, 50}:
            if self.game.transition < 1:
                for _ in range(20):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 0.5 + 0.5
                    p_velocity = [math.cos(angle) * speed,
                                  math.sin(angle) * speed]
                    self.game.particles.append(_particle.Particle(self.game, 'particle' + str(
                        self.game.power_level), self.rect().center, vel=p_velocity, frame=random.randint(0, 7)))

        elif abs(self.dashing) == 1:
            self.game.sfx['dashClick'].play()
            for _ in range(20):
                angle = random.random() * 2 * math.pi
                speed = random.random() * 1.5
                p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(_particle.Particle(self.game, 'particle' + str(
                    self.game.power_level), self.rect().center, vel=p_velocity, frame=random.randint(0, 7)))

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

        if self.animation.frame % 5 == 0:
            webs = [e for e in self.game.extra_entities if e.type == 'web']
            self.terminal_vel = 5
            self.can_dash = True
            for web in webs:
                if self.rect().colliderect(web.rect()):
                    self.terminal_vel = 0.5
                    self.can_dash = False

    def render(self, surface, offset=(0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))

        if abs(self.dashing) <= 50 and self.game.transition < 1:
            super().render(surface, offset=offset)
        elif abs(self.dashing) > 50:
            super().render(surface, offset=offset, transparency=100)

    def jump(self):
        if self.wall_slide and self.can_dash:
            self.velocity[1] = -3
            self.air_time = 5
            self.jumps = max(0, self.jumps - 1)

            self.velocity[0] = -1.5 + 3*self.flip_x
            for _ in range(5):
                angle = (random.random() + 1 + self.flip_x) * (math.pi / 4)
                speed = random.random() * (2)
                self.game.sparks.append(_spark.Spark(
                    (self.rect().centerx, self.rect().bottom), angle, speed, color=(190, 200, 220)))
            return True

        elif self.jumps > 0 and abs(self.dashing) < 50 and self.can_dash:
            self.jumps -= 1
            self.velocity[1] = min(self.velocity[1], -3)
            self.air_time = 5
            for _ in range(5):
                angle = (random.random()) * math.pi
                speed = random.random() * (2)
                self.game.sparks.append(_spark.Spark(
                    (self.rect().centerx, self.rect().bottom), angle, speed, color=(190, 200, 220)))
            return True
        
        elif (self.jumps > 0 and abs(self.dashing) < 50 and not self.can_dash) or (self.wall_slide and not self.can_dash):
            self.jumps -= 1
            self.velocity[1] = min(self.velocity[1], -1)
            self.air_time = 5

    def dash(self):
        if abs(self.dashing) <= 50 and self.dashes > 0 and not self.game.dead and self.can_dash:
            self.spark_timer = 0
            self.dashes = max(self.dashes - 1, 0)
            self.game.sfx['dash'].play()
            if self.flip_x:
                self.dashing = -self.dash_dist
            else:
                self.dashing = self.dash_dist

    def updatenearest_enemy(self):
        distance = 10000
        return_enemy = False
        for enemy in self.game.enemies:
            if np.linalg.norm(self.vector_to(enemy)) < distance:
                return_enemy = enemy
                distance = np.linalg.norm(self.vector_to(enemy))

            # Remove enemy if it got out of bounds.
            if enemy.pos[0] < 0 or enemy.pos[0] > self.game.tilemap.map_size*16 or enemy.pos[1] < 0 or enemy.pos[1] > self.game.tilemap.map_size*16:
                self.game.enemies.remove(enemy)
                print('removing enemy ', enemy.type,
                      ' at ', enemy.pos)  # debug
                print('bounds: ', 0, 0, ",", self.game.tilemap.map_size *
                      16, self.game.tilemap.map_size*16)
        self.nearest_enemy = return_enemy

    def damage(self, damageAmount, type):
        if not self.damage_cooldown:
            self.damage_cooldown = 60
            self.game.damaged_by = type

            if self.game.temporary_health:
                self.game.temporary_health -= 1
            else:
                self.game.health = max(0, self.game.health - damageAmount)
            self.game.sfx['hit'].play()

            if self.game.health == 0:
                self.game.screenshake = max(50, self.game.screenshake)
                for _ in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(_spark.Spark(self.game.player.rect(
                    ).center, angle, 2 + random.random(), color=(200, 0, 0)))
                    self.game.particles.append(_particle.Particle(self.game, 'particle' + str(self.game.power_level), self.game.player.rect().center, vel=[
                                               math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.dead = True
                self.game.death_count += 1
                self.dashing = 0

                name_vowel = True if self.game.enemy_names[type][0].lower() in [
                    'a', 'e', 'i', 'o', 'u'] else False
                random_verb = random.choice(self.game.death_verbs)
                self.game.death_message = 'You were ' + random_verb + ' by a' + ('n ' if name_vowel else ' ') + self.game.enemy_names[type]
                for currency in self.game.wallet:
                    if currency not in self.game.not_lost_on_death:
                        lost_amount = math.floor(
                            self.game.wallet[currency] * 0.25) if self.game.current_level != 'infinite' else 0
                        self.game.wallet[currency] -= lost_amount
                        self.game.walletlost_amount[currency] = lost_amount

                    if self.game.current_level == 'infinite':
                        self.game.wallet_gained_amount[currency] = int(
                            self.game.wallet_temp[currency] / 2)

            else:
                self.game.screenshake = max(5, self.game.screenshake)
                for _ in range(10):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(_spark.Spark(self.game.player.rect(
                    ).center, angle, 2 + random.random(), color=(100, 0, 0)))
                    self.game.particles.append(_particle.Particle(self.game, 'particle' + str(self.game.power_level), self.game.player.rect().center, vel=[
                                               math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))

class PlayerCustomise(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.gravity_affected = False
        self.collide_wall_check = False
        self.collide_wall = False
        self.is_boss = True
        self.anim_offset = (0, 0)
        self.set_action('run')

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

class Currency(PhysicsEntity):
    def __init__(self, game, currency_type, pos, size=(6, 6), value=1, velocity_0 = [random.uniform(-1,1), random.uniform(-2,-1)]):
        super().__init__(game, currency_type, pos, size)

        self.velocity = velocity_0
        self.value = value
        self.currency_type = currency_type
        self.size = list(size)
        self.gravity_affected = True
        self.light_size = self.value * 5
        self.old_enough = 0 if self.currency_type == 'hammer' else 30

        self.anim_offset = (-1, random.choice([-1, -2]))
        self.animation.img_duration += (
            self.animation.img_duration*random.random())

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)
        if abs(self.velocity[0]) > 1:
            self.velocity[0] *= 0.98
        else:
            self.velocity[0] *= 0.95

        if self.old_enough:
            self.old_enough = max(0, self.old_enough - 1)

        if not self.old_enough and np.linalg.norm(self.vector_to(self.game.player)) < 15:
            if self.pos[0] - self.game.player.pos[0] > 0:
                self.velocity[0] = max(self.velocity[0]-0.1, -0.5)
            else:
                self.velocity[0] = min(self.velocity[0]+0.1, 0.5)

        # Check for player collision
        if self.game.player.rect().colliderect(self.rect()) and not self.old_enough:
            if self.game.current_level == 'lobby':
                self.game.wallet[str(self.currency_type) + 's'] += self.value
            else:
                self.game.wallet_temp[str(self.currency_type) + 's'] += self.value
            self.game.check_encounter(self.currency_type + 's')
            self.game.sfx['coin'].play()
            return True

class Glowworm(PhysicsEntity):
    def __init__(self, game, pos, size=(5, 5)):
        super().__init__(game, 'glowworm', pos, size)

        # All spawn at the same point with 0 vel.
        self.velocity = [(random.random()-0.5), -1.5]
        self.size = list(size)
        self.light_size = 5
        self.gravity_affected = False
        self.collide_wall_check = False
        self.hover_distance = 30
        self.anim_offset = (0, 0)
        self.animation.img_duration += (
            self.animation.img_duration*random.random())
        self.direction = [random.random(), random.random()]

    def update(self, tilemap, movement=(0, 0)):
       # They will go towards a priority entity.
        if random.random() < 0.05:
            direction_extra = [0, 0]
            check_portal = True

            if len(self.game.bosses) > 0:
                for boss in self.game.bosses:

                    if boss.glowworm_follow:
                        check_portal = False
                        to_boss = self.vector_to(boss)

                        if np.linalg.norm(to_boss) > self.hover_distance:
                            direction_extra = to_boss
                        else:
                            direction_extra = [0, 0]

                        break

            elif len(self.game.enemies) > 0 and self.game.player.nearest_enemy:
                check_portal = False
                enemy = self.game.player.nearest_enemy
                to_enemy = self.vector_to(enemy)

                if np.linalg.norm(to_enemy) > self.hover_distance:
                    direction_extra = to_enemy

                else:
                    direction_extra = [0, 0]

            # Second priority go to character with new dialogue
            elif len(self.game.characters) > 0:
                for character in self.game.characters:
                    if character.new_dialogue:
                        check_portal = False
                        to_character = self.vector_to(character)

                        if np.linalg.norm(to_character) > self.hover_distance:
                            direction_extra = to_character
                            break
                    else:
                        direction_extra = [0, 0]

            # Third priority go to active portal
            if len(self.game.portals) > 0 and check_portal:
                portal = random.choice(self.game.portals)
                for p in self.game.portals:
                    if p.destination == 'infinite':
                        portal = p
                to_portal = self.vector_to(portal)

                if np.linalg.norm(to_portal) > self.hover_distance:
                    direction_extra = to_portal
                else:
                    direction_extra = [0, 0]

            extra_length = np.linalg.norm(direction_extra)

            if extra_length > 0:
                direction_extra /= (np.linalg.norm(direction_extra) * 3)
            self.direction = [random.random() - 0.5 + direction_extra[0],
                              random.random() - 0.5 + direction_extra[1]]

        self.pos[0] += self.direction[0] + (random.random() - 0.5)
        self.pos[1] += self.direction[1] + (random.random() - 0.5)

        super().update(tilemap, movement=movement)

class Bullet():
    def __init__(self, game, pos, speed, origin, type='projectile_'):
        self.attack_power = 1

        self.pos = list(pos)
        self.game = game
        self.speed = list(speed)
        self.type = type
        self.origin = origin
        self.img = self.game.assets[self.type]
        self.anim_offset = (-2, 0)
        self.light_size = 10

    def update(self, game):
        if game.display_frame:
            if game.cave_darkness and game.transition <= 0:
                game.darkness_circle(0, self.light_size, (int(self.pos[0]) - game.render_scroll[0], int(self.pos[1]) - game.render_scroll[1]))
            game.display_outline.blit(self.img, (self.pos[0] - self.img.get_width() / 2 - game.render_scroll[0], self.pos[1] - self.img.get_height() / 2 - game.render_scroll[1]))

        if not game.paused:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]

        # Check to destroy
        if game.tilemap.solid_check(self.pos):
            if self.type != 'spine':
                velocity_angle = math.atan2(self.speed[1], (self.speed[0] if self.speed[0] != 0 else 0.01))
                for _ in range(4):
                    self.game.sparks.append(_spark.Spark(self.pos, random.random() - 0.5 + velocity_angle, 2 + random.random()))
                self.game.sfx['proj_bye'].play()
            return True

        # Check for player/crate collision:
        for crate in [e for e in game.extra_entities.copy() if e.type == 'crate']:
            if crate.rect().collidepoint(self.pos):
                crate.kill()
                game.extra_entities.remove(crate)
                return True

        if game.player.rect().collidepoint(self.pos) and abs(game.player.dashing) < 50:
            if not game.dead:
                game.player.damage(self.attack_power, self.origin)
                return True

class RolyPoly(PhysicsEntity):
    def __init__(self, game, pos, size, initialFall=False, friendly = False):
        super().__init__(game, 'rolypoly', pos, size)

        self.attack_power = 1

        self.currency_drops['cog'] = random.randint(0, 3) if len(game.bosses) == 0 else random.randint(0, 1)
        self.currency_drops['eye'] = random.randint(1, 2) if len(game.bosses) == 0 else random.randint(0, 1)
        self.currency_drops['heartFragment'] = random.randint(0, 1)

        self.death_intensity = 10
        self.attack_states = ['run']

        self.size = list(size)
        self.speed = round(random.random() * 0.5 + 0.5, 2)
        self.gravity_affected = initialFall
        self.collide_wall_check = True
        self.collide_wall = False
        self.anim_offset = (0, 0)
        self.heading = [-self.speed if random.random() <
                        0.5 else self.speed, 0]
        self.wall_side = [0, self.speed]
        self.time_since_turn = 0
        self.time_since_air = 0
        self.pos[1] += 5
        self.grace = random.randint(120, 180)
        self.animation.img_duration += (
            self.animation.img_duration*random.random())
        
        self.friendly = friendly
        if self.friendly:
            self.gravity_affected = True

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        #Attempt to stop them getting stuck in walls
        if any(self.collisions.values()):
            self.time_since_air += 1

            if self.time_since_air > 30 and self.time_since_air%5 == 0:
                to_player = self.vector_to(self.game.player)
                dist_to_player = np.linalg.norm(to_player)
                to_player = [to_player[0] / dist_to_player, to_player[1] / dist_to_player]

                self.pos[0] += to_player[0]
                self.pos[1] += to_player[1]
        else:
            self.time_since_air = 0

        if self.gravity_affected:
            if any(self.collisions.values()):
                self.set_action('run')
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.gravity_affected = False
                self.grace = 0
                self.pos[1] -= 4

        elif self.grace:
            self.grace = max(self.grace - 1, 0)
            if self.grace == 0:
                self.set_action('run')
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]

        elif self.action != 'idle':
            if self.time_since_turn < 5:
                self.time_since_turn += 1

            # Change direction if it leaves a tileblock:
            if not any(x == True for x in self.collisions.values()) and self.time_since_turn > 3:
                self.wall_side, self.heading = [-self.heading[0], -
                                               self.heading[1]], self.wall_side
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.time_since_turn = 0

            # Also change direction if run into a wall:
            elif any(self.collisions.values()) and self.time_since_turn > 3:
                self.wall_side, self.heading = self.heading, [
                    -self.wall_side[0], -self.wall_side[1]]
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.time_since_turn = 0

        # Death Condition
        if self.check_damages():
            return True

    def render(self, surface, offset=(0, 0)):
        # pygame.draw.rect(self.game.hud_display, (255,0,0), (2*(self.rect().x - self.game.render_scroll[0] - self.anim_offset[0]), 2*(self.rect().y - self.game.render_scroll[1] - self.anim_offset[1]), self.size[0]*2, self.size[1]*2))

        super().render(surface, offset=offset)

class Parrot(PhysicsEntity):
    def __init__(self, game, pos, size, friendly = False):
        super().__init__(game, 'parrot', pos, size)

        self.currency_drops['wing'] = 1 if random.random() < 0.3 else 0

        self.death_intensity = 3
        self.gravity_affected = True
        self.flip_x = True if random.random() < 0.5 else False
        self.colours = {
            'eye': (188, 188, 188),
            'back': (63, 63, 63),
            'front': (112, 112, 112),
            'wing': (175, 175, 175),
        }

        self.anim_offset = (-1, -2)

        self.friendly = friendly
        self.timer = 0 if self.friendly else random.randint(100, 300)

        if not self.game.parrots_randomised:
            self.reset_colours()
            self.randomise_colours()
            self.game.parrots_randomised = True

            self.set_action('idle', override=True)

    def reset_colours(self):
        self.game.assets[f'parrot/idle'] = copy.deepcopy(self.game.assets[f'parrot_saved/idle'])
        self.game.assets[f'parrot/flying'] = copy.deepcopy(self.game.assets[f'parrot_saved/flying'])

    def randomise_colours(self):
        for area in self.colours.keys():
            old_colour = self.colours[area]
            new_colour = tuple(random.randint(0, 255) for _ in range(3))
            
            #Colour change
            for state in ['idle', 'flying']:                
                for frame in range(len(self.game.assets[f'parrot/{state}'].images)):
                    self.game.assets[f'parrot/{state}'].images[frame] = self.colour_change(self.game.assets[f'parrot/{state}'].images[frame], old_colour, new_colour)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.action == 'idle':
            self.timer = max(self.timer - 1, 0)

            if not self.timer:
                self.set_action('flying')
                self.velocity = [random.uniform(-1, 1), random.uniform(-2, 0)]
                self.flip_reset()    

        elif self.action == 'flying':
            if random.random() < 0.1 and not self.collisions['up']:
                x_addition = 0.25 if self.vector_to(self.game.player)[0] > 0 else -0.25
                y_addition = -2 if self.vector_to(self.game.player)[1] > 0 else 0
                self.velocity = [random.random() - 0.5 + x_addition, -(random.random() + 2 + y_addition)]
                self.flip_reset()

            elif self.collisions['down'] and tilemap.solid_check((self.rect().centerx, self.rect().centery + 16)):
                self.set_action('idle')
                self.velocity = [0, 0]
                self.timer = random.randint(30, 60)

        if random.random() < 0.005:
            if np.linalg.norm(self.vector_to(self.game.player)) < 50:
                self.game.sfx['chirp'].play()

        # Death Condition
        if self.check_damages(player_contact=False):
            return True

class SpawnPoint(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spawn_point', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.collide_wall = False
        self.set_action('active' if self.pos ==
                        self.game.spawn_point else 'idle')

        self.anim_offset = (0, -1)

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) > 50 and self.action == 'idle':
            for point in self.game.spawn_points:
                if point.action == 'active':
                    point.set_action('idle')

            self.set_action('active')
            self.game.spawn_point = self.pos[:]
            self.game.sfx['ding'].play()
            self.game.check_encounter('spawn_points')

        if self.action == 'active':
            if random.random() < 0.05:
                angle = (random.random() + 1) * math.pi
                speed = random.random() * 3
                self.game.sparks.append(_spark.Spark(self.rect().center, angle, speed, color=random.choice([(58, 6, 82), (111, 28, 117)])))

class HeartAltar(PhysicsEntity):
    def __init__(self, game, pos, size, action='active', falling = False, value = 1, velocity_0 = [0,0]):
        super().__init__(game, 'heart_altar', pos, size)

        self.falling = falling
        self.value = value
        self.gravity_affected = self.falling
        self.collide_wall_check = self.falling
        self.collide_wall = self.falling
        self.velocity = velocity_0
        
        self.set_action(action)

        self.anim_offset = (0, 0)
        self.animation.img_duration += (
            self.animation.img_duration*random.random())

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if self.falling and self.collisions['down']:
            self.falling = False
            self.gravity_affected = self.falling
            self.collide_wall_check = self.falling
            self.collide_wall = self.falling
        elif self.falling and (self.collisions['left'] or self.collisions['right']):
            self.velocity[0] *= -0.75

        if self.value > 1 and random.random() < 0.1:
            self.game.sparks.append(_spark.Spark(self.rect().center, random.uniform(0, math.pi * 2), random.random() + 1, color=random.choice([(112, 0, 2), (170, 27, 36)])))
        
        dist_player = np.linalg.norm(self.vector_to(self.game.player))
        if dist_player < 15:
            xpos = (self.rect().centerx - self.game.render_scroll[0]) - 7
            ypos = (self.rect().centery -self.game.render_scroll[1]) - 22

            self.game.hud_display.blit(self.game.control_icons['Interract'], (xpos, ypos))

            if self.game.interraction_frame_int and self.action == 'active':
                self.game.check_encounter('heart_altars')

                if self.game.health < self.game.max_health:
                    self.game.health = min(self.game.health + self.value, self.game.max_health)
                    self.set_action('idle')
                    self.game.sfx['ding'].play()

class Torch(PhysicsEntity):
    def __init__(self, game, pos, size, action='idle'):
        super().__init__(game, 'torch', pos, size)
        self.gravity_affected = False
        self.collide_wall_check = False
        self.collide_wall = False
        self.light_size = 50
        self.anim_offset = (0, 0)
        self.rnd = [-1, 0, 1]
        self.animation.img_duration += (
            self.animation.img_duration*random.random())
        self.lights = {0: 30,
                       1: 31,
                       2: 32,
                       3: 32,
                       4: 31,
                       5: 30}

        # Check for flip:
        left = self.game.tilemap.solid_check(
            [self.pos[0] - self.game.tilemap.tilesize, self.pos[1]], return_value='bool')
        right = self.game.tilemap.solid_check(
            [self.pos[0] + self.game.tilemap.tilesize, self.pos[1]], return_value='bool')
        if left and not right:
            self.flip_x = True
        elif left and right and random.random() < 0.5:
            self.flip_x = True

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        # super().update(tilemap, movement=movement)
        self.light_size = self.lights[int(self.animation.frame / self.animation.img_duration)]

        if random.random() < 0.05:
            self.game.sparks.append(_spark.Spark([self.rect().x + (4 if self.flip_x else 12), self.pos[1]], random.random(
            ) * math.pi + math.pi, random.random() + 1, color=random.choice([(229, 0, 0), (229, 82, 13)])))

        self.animation.update()
        self.display_darkness_circle()

class Spider(PhysicsEntity):
    def __init__(self, game, pos, size, friendly = False):
        super().__init__(game, 'spider', pos, size)

        self.currency_drops['cog'] = random.randint(0, 3)
        self.currency_drops['heartFragment'] = 1 if random.random() < 0.2 else 0
        self.currency_drops['chitin'] = random.randint(0, 3)

        self.attack_power = 1
        self.death_intensity = 10
        self.attack_states = ['idle', 'run']

        self.grace = random.randint(90, 210)
        self.grace_done = False
        self.gravity_affected = False
        self.set_action('grace')
        self.anim_offset = (-3, -3)
        self.pos[0] += 4
        self.pos[1] += 5
        self.timer = 0
        self.to_player = [0, 0]
        self.facing = [random.random() - 0.5, random.random() - 0.5]

        self.friendly = friendly
        if self.friendly:
            self.set_action('idle')

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(30, 90)
                self.grace_done = True
            self.animation.update()

        if self.grace_done:
            if self.action == 'idle':
                self.timer = max(self.timer - 1, 0)

                if not self.timer:
                    self.set_action('run')
                    to_player = self.vector_to(self.game.player)
                    dist_to_player = np.linalg.norm(to_player)
                    self.to_player = to_player / dist_to_player
                    self.velocity = [self.to_player[0]
                                     * 0.2, self.to_player[1] * 0.2]

                    self.velocity[0] += random.random() - 0.5
                    self.velocity[1] += random.random() - 0.5

                    self.facing[0] = self.velocity[0]
                    self.facing[1] = self.velocity[1]

                    self.timer = random.randint(30, 90)

                    if random.random() < 0.05 and dist_to_player < 50:
                        self.game.sfx['spider'].play()

            elif self.action == 'run':
                self.timer = max(self.timer - 1, 0)

                if self.timer == 0:
                    self.velocity = [0, 0]
                    self.timer = random.randint(10, 30)
                    self.set_action('idle')

                    #create web sometimes
                    if random.random() < 0.5:
                        x = self.pos[0]//tilemap.tilesize
                        y = self.pos[1]//tilemap.tilesize
                        tile_pos = str(x) + ';' + str(y)
                        pos = [x*tilemap.tilesize, y*tilemap.tilesize]
                        web_positions = [w.pos for w in self.game.extra_entities if w.type == 'web']
                        if tile_pos not in tilemap.tilemap and pos not in web_positions:
                            self.game.extra_entities.append(Web(self.game, pos, self.game.entity_info[53]['size']))

        # Death Condition
        if self.check_damages():
            return True

    def render(self, surface, offset=(0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        angle = 0
        angle = math.atan2(-self.facing[1], self.facing[0]) - math.pi / 2

        super().render(surface, offset=offset, rotation=angle)

class RubiksCube(PhysicsEntity):
    def __init__(self, game, pos, size, friendly = False):
        super().__init__(game, 'rubiksCube', pos, size)

        self.currency_drops['cog'] = random.randint(0, 3)
        self.currency_drops['heartFragment'] = random.randint(0, 3)

        self.attack_power = 1
        self.death_intensity = 10
        self.attack_states = ['white', 'yellow', 'blue', 'green', 'red', 'orange']

        self.grace = random.randint(90, 210)
        self.grace_done = False
        self.gravity_affected = False
        self.anim_offset = (0, 0)
        self.can_move_vectors = []
        self.speed = 1
        self.max_speed = 3
        self.states = ['white', 'yellow', 'blue', 'green', 'red', 'orange']

        self.friendly = friendly
        if self.friendly:
            self.grace_done = True
            self.set_action(random.choice(self.states))
            self.timer = 1

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action(random.choice(self.states))
                self.timer = random.randint(120, 300)
                self.grace_done = True
                if self.action == 'red':
                    self.currency_drops['redCog'] = random.randint(1, 5)
                elif self.action == 'blue':
                    self.currency_drops['blueCog'] = random.randint(1, 5)

            self.animation.update()

        if self.grace_done:
            if self.timer:
                self.timer = max(self.timer - 1, 0)

                # When timer runs out, move in a random direction until hit a wall
                # Then change colour and reset timer.
                if not self.timer:
                    # Find random directions that entity can move in
                    self.can_move_vectors = []
                    pos_centre = [self.rect().centerx, self.rect().centery]

                    # left:
                    if not tilemap.solid_check([pos_centre[0] - tilemap.tilesize, pos_centre[1]], return_value='bool'):
                        self.can_move_vectors.append([-self.speed, 0])
                    # right:
                    if not tilemap.solid_check([pos_centre[0] + tilemap.tilesize, pos_centre[1]], return_value='bool'):
                        self.can_move_vectors.append([self.speed, 0])
                    # up:
                    if not tilemap.solid_check([pos_centre[0], pos_centre[1] - tilemap.tilesize], return_value='bool'):
                        self.can_move_vectors.append([0, -self.speed])
                    # down:
                    if not tilemap.solid_check([pos_centre[0], pos_centre[1] + tilemap.tilesize], return_value='bool'):
                        self.can_move_vectors.append([0, self.speed])

                    # Set velocity to that direction
                    self.velocity = random.choice(self.can_move_vectors)
            else:
                self.velocity[0] = max(
                    min(self.velocity[0] * 1.02, self.max_speed), -self.max_speed)
                self.velocity[1] = max(
                    min(self.velocity[1] * 1.02, self.max_speed), -self.max_speed)

            # When hit a tile, stop and change colour, repeat
            if any(self.collisions.values()):
                self.timer = random.randint(120, 300)
                self.velocity = [0, 0]
                self.set_action(random.choice(self.states))

                self.currency_drops['redCog'], self.currency_drops['blueCog'] = 0, 0
                if self.action == 'red':
                    self.currency_drops['redCog'] = random.randint(1, 5)
                elif self.action == 'blue':
                    self.currency_drops['blueCog'] = random.randint(1, 5)

        # Death Condition
        if self.check_damages():
            return True

class Kangaroo(PhysicsEntity):
    def __init__(self, game, pos, size, friendly = False):
        super().__init__(game, 'kangaroo', pos, size)

        self.currency_drops['cog'] = random.randint(0, 3)
        self.currency_drops['heartFragment'] = 1 if random.random() < 0.3 else 0
        self.currency_drops['fairyBread'] = random.randint(0, 4)
        self.currency_drops['boxingGlove'] = random.randint(0, 3)

        self.attack_power = 1
        self.death_intensity = 10
        self.attack_states = ['idle', 'jumping', 'prep']

        self.grace = random.randint(90, 210)
        self.grace_done = False
        self.gravity_affected = True
        self.set_action('grace')
        self.anim_offset = (0, 0)
        self.timer = 0
        self.time_since_bounce = 0
        self.flip_x = True if random.random() < 0.5 else False

        self.friendly = friendly
        if self.friendly:
            self.set_action('idle')

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(30, 90)
                self.grace_done = True
            self.animation.update()

        if self.grace_done:
            if self.action == 'idle':
                self.timer = max(self.timer - 1, 0)

                if not self.timer:
                    self.set_action('prep')
                    self.timer = random.randint(30, 60)

            if self.action == 'prep':
                self.timer = max(self.timer - 1, 0)

                if not self.timer:
                    # JUMP ROUGHLY IN DIRECTION OF PLAYER
                    self.set_action('jumping')
                    if self.pos[0] < self.game.player.pos[0]:
                        self.flip_x = False
                    else:
                        self.flip_x = True

                    self.velocity[0] = -(random.random() +
                                         1.5) if self.flip_x else (random.random() + 1.5)
                    self.velocity[1] = -(random.random() * 2.5 + 1)
                    self.time_since_bounce = 0
                    self.timer = random.randint(120, 300)

            elif self.action == 'jumping':
                self.timer = max(self.timer - 1, 0)
                self.time_since_bounce = min(self.time_since_bounce + 1, 10)
                self.velocity[0] *= 0.99
                self.velocity[1] *= 0.99

                if self.collisions['left'] or self.collisions['right'] and self.time_since_bounce >= 10:
                    self.time_since_bounce = 0
                    self.velocity[0] = -self.velocity[0]
                    self.flip_x = not self.flip_x

                if self.collisions['down']:
                    pos_centre = [self.rect().centerx, self.rect().centery]
                    if tilemap.solid_check([pos_centre[0], pos_centre[1] + tilemap.tilesize], return_value='bool'):
                        self.velocity = [0, 0]

                        self.timer = random.randint(90, 120)
                        self.set_action('idle')

        # Death Condition
        if self.check_damages():
            return True

class Echidna(PhysicsEntity):
    def __init__(self, game, pos, size, friendly = False):
        super().__init__(game, 'echidna', pos, size)

        self.currency_drops['cog'] = random.randint(0, 3)
        self.currency_drops['heartFragment'] = 1 if random.random() < 0.3 else 0
        self.currency_drops['fairyBread'] = random.randint(0, 4)

        self.attack_power = 1
        self.death_intensity = 10
        self.attack_states = ['idle', 'charging', 'walking']

        self.grace = random.randint(90, 210)
        self.grace_done = False
        self.gravity_affected = True
        self.set_action('grace')
        self.anim_offset = (0, 0)
        self.timer = 0
        self.flip_x = True if random.random() < 0.5 else False

        self.friendly = friendly
        if self.friendly:
            self.set_action('idle')

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('idle')
                self.timer = random.randint(30, 90)
                self.grace_done = True
            self.animation.update()

        if self.grace_done:
            if self.action == 'idle':
                self.timer = max(self.timer - 1, 0)

                if not self.timer:
                    self.set_action('walking')
                    self.timer = random.randint(120, 180)
                    self.velocity = [-random.random()
                                     if self.flip_x else random.random(), 0]

                elif random.random() < 0.005 and not self.friendly:
                    self.set_action('charging')
                    self.velocity = [0, 0]

            if self.action == 'walking':
                self.timer = max(self.timer - 1, 0)

                floor_check = tilemap.solid_check(
                    (self.rect().centerx + (-8 if self.flip_x else 8), self.rect().centery + 16))

                if self.collisions['left'] or self.collisions['right'] or not floor_check:

                    self.flip_x = not self.flip_x
                    self.set_action('idle')
                    self.timer = random.randint(120, 180)
                    self.velocity = [0, 0]

                elif random.random() < 0.005 and not self.friendly:
                    self.set_action('charging')
                    self.velocity = [0, 0]

            elif self.action == 'charging':
                # When animation finishes, shoot spines in random directions and go to idle.
                if self.animation.done:

                    for _ in range(10):
                        angle = random.random() * math.pi + math.pi
                        spine_velocity = [2*math.cos(angle), 2*math.sin(angle)]
                        self.game.projectiles.append(Bullet(self.game, self.rect().center, spine_velocity, 'echidna', type='spine'))
                    self.game.projectiles.append(Bullet(self.game, self.rect().center, [2, 0], 'echidna', type='spine'))
                    self.game.projectiles.append(Bullet(self.game, self.rect().center, [-2, 0], 'echidna', type='spine'))
                    self.set_action('idle')
                    self.timer = random.randint(120, 180)

        # Death Condition
        if self.check_damages():
            return True

        super().update(tilemap, movement=movement)

class Meteor(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'meteor', pos, size)

        self.attack_power = 1

        self.gravity_affected = False
        self.collide_wall_check = False
        self.set_action('idle')
        self.anim_offset = (0, 0)
        self.angle = random.random() * 2 * math.pi

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.action == 'idle':
            self.light_size += 0.2
            if round(self.light_size, 1) == 16.0 and self.game.meteor_sounds < 5:
                self.game.sfx['meteor'].play()
                self.game.meteor_sounds += 1
            if self.animation.done:
                self.set_action('kaboom')
                self.game.meteor_sounds -= 1

        elif self.action == 'kaboom':
            # Check for player collision:
            if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.animation.frame > 10:
                if not self.game.dead:
                    self.game.player.damage(self.attack_power, self.type)

            if self.animation.done:
                return True

class AlienShip(PhysicsEntity):
    def __init__(self, game, pos, size, grace_done=False, velocity=[0, 0], friendly = False):
        super().__init__(game, 'alienship', pos, size)

        self.currency_drops['cog'] = random.randint(0, 3)
        self.currency_drops['heartFragment'] = 1 if random.random() < 0.3 else 0
        self.currency_drops['purpleCog'] = 1 if random.random() < 0.2 else 0

        self.attack_power = 1
        self.death_intensity = 10
        self.attack_states = ['flying']

        self.gravity_affected = False
        self.grace = random.randint(90, 210)
        self.grace_done = grace_done
        self.set_action('idle')
        if self.grace_done:
            self.set_action('flying')
            self.velocity = velocity
        self.friendly = friendly
        if self.friendly:
            self.set_action('flying')
            self.velocity = [random.random() - 0.5, random.random() - 0.5]

        self.anim_offset = (0, -1)
        self.pos[1] += 9
        self.pos[0] += 4

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action('flying')
                self.velocity = [
                    random.random() - 1/2, random.random()*0.5 + 0.5]
                self.grace_done = True

            self.animation.update()

        if self.grace_done:
            if self.collisions['up'] or self.collisions['down']:
                self.velocity[1] = -self.velocity[1]
            elif self.collisions['left'] or self.collisions['right']:
                self.velocity[0] = -self.velocity[0]

            if any(self.collisions.values()) and random.random() < 0.3:
                to_player = self.vector_to(self.game.player)
                norm = np.linalg.norm(to_player) * random.uniform(1.2, 1.5)

                if not (tilemap.solid_check((self.rect().centerx + 8, self.rect().centery)) and tilemap.solid_check((self.rect().centerx - 8, self.rect().centery))):
                    self.velocity[0] = to_player[0] / norm
                if not (tilemap.solid_check((self.rect().centerx, self.rect().centery + 8)) and tilemap.solid_check((self.rect().centerx, self.rect().centery - 8))):
                    self.velocity[1] = to_player[1] / norm

        # Death Condition
        if self.check_damages():
            return True

class CreepyEyes(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'creepy_eyes', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.main_pos = tuple(pos)
        self.type = 'creepy_eyes'

        self.anim_offset = (0, 0)

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        to_player = self.vector_to(self.game.player)
        self.to_player_norm = to_player / np.linalg.norm(to_player)

        self.pos[0] = self.main_pos[0] + round(self.to_player_norm[0] if abs(self.to_player_norm[0]) > 0.38 else 0)
        self.pos[1] = self.main_pos[1] + round(self.to_player_norm[1] if abs(self.to_player_norm[1]) > 0.38 else 0)

class MeteorBait(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'meteor_bait', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.pos = list(pos)
        self.anim_offset = (0, 0)

        self.cooldown = 0
        self.animation.img_duration += (
            self.animation.img_duration*random.random())

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if self.cooldown:
            self.cooldown = max(self.cooldown - 1, 0)

        if self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) >= 50 and not self.cooldown:
            self.cooldown = 30
            self.summon_meteor(self.rect().center, [
                              [x, y] for x in range(-2, 3) for y in range(-15, 2)], random.randint(3,6))

    def summon_meteor(self, center_pos, area, quantity):
        test_loc = [0, 0]
        center_tile = (center_pos[0] // self.game.tilemap.tilesize,
                      center_pos[1] // self.game.tilemap.tilesize)
        success_tiles = []
        attempts = 0

        while len(success_tiles) < quantity and attempts < 100:

            test_loc[0] = int(center_tile[0] + random.choice([e[0]
                             for e in area]))
            test_loc[1] = int(center_tile[1] + random.choice([e[1]
                             for e in area]))

            loc_str = str(test_loc[0]) + ';' + str(test_loc[1])
            if loc_str not in self.game.tilemap.tilemap and test_loc not in success_tiles:
                success_tiles.append(test_loc.copy())

            attempts += 1

        for loc in success_tiles:
            self.game.extra_entities.append(Meteor(
                self.game, (loc[0] * self.game.tilemap.tilesize, loc[1] * self.game.tilemap.tilesize), (16, 16)))

class Candle(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'candle', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.pos = list(pos)
        self.timer = random.randint(400, 800)
        self.light_size = 0
        self.anim_offset = (-2, -3)
        self.pos[0] -= self.anim_offset[0]
        self.pos[1] -= self.anim_offset[1]

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        self.timer = max(self.timer - 1, 0)

        if self.action == 'idle' and not self.timer:
            self.set_action('preparing')
            self.timer = random.randint(120, 300)

        elif self.action == 'preparing':
            self.light_size = min(self.light_size + random.random(), 10)

            if not self.timer:
                self.set_action('active')
                self.timer = random.randint(200, 500)
            elif random.random() < 0.05:
                self.game.sparks.append(_spark.Spark(self.rect().center, random.random(
                ) * math.pi + math.pi, random.random() + 1, color=random.choice([(229, 0, 0), (229, 82, 13)])))

        elif self.action == 'active':
            self.light_size = min(self.light_size + random.random(), 25)

            if random.random() < 0.1:
                self.game.sparks.append(_spark.Spark(self.rect().center, random.random(
                ) * math.pi + math.pi, random.random() + 2, color=random.choice([(229, 0, 0), (229, 82, 13)])))

            if self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) <= 50:
                self.game.player.damage(self.attack_power, self.type)
            elif not self.timer:
                self.set_action('idle')
                self.light_size = 0
                self.timer = random.randint(400, 800)

class Chandelier(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'chandelier', pos, size)
        self.gravity_affected = False
        self.collide_wall_check = False
        self.collide_wall = False
        self.light_size = 10
        self.anim_offset = (0, 0)
        self.x_offset = 10
        self.lights = {0: 30,
                       1: 31,
                       2: 32,
                       3: 32,
                       4: 31,
                       5: 30}

    def update(self, tilemap, movement=(0, 0)):
        # super().update(tilemap, movement=movement)

        if random.random() < 0.05:
            self.game.sparks.append(_spark.Spark((self.rect().centerx + self.x_offset, self.rect().bottom - 18), random.random(
            ) * math.pi + math.pi, random.random() + 1, color=random.choice([(229, 0, 0), (229, 82, 13)])))

            self.game.sparks.append(_spark.Spark((self.rect().centerx - self.x_offset, self.rect().bottom - 18), random.random(
            ) * math.pi + math.pi, random.random() + 1, color=random.choice([(229, 0, 0), (229, 82, 13)])))

        self.animation.update()
        self.light_size = self.lights[int(self.animation.frame / self.animation.img_duration)]
        self.display_darkness_circle(offset=[10, 46])
        self.display_darkness_circle(offset=[-10, 46])

class Orb(PhysicsEntity):
    def __init__(self, game, pos, size, velocity, origin, colour):
        super().__init__(game, f'orb_{origin}', pos, size)
        self.pos = list(pos)
        self.size = size
        self.velocity = velocity
        self.gravity_affected = False
        self.colour = colour

        self.is_boss = True

        self.anim_offset = (-1, -1)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if any(self.collisions.values()) or self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) <= 50:
            self.circular_attack(25, self.rect().center, color=self.colour, color_str='yellow' if self.type == 'orb_cherub' else 'red')
            return True

class Cherub(PhysicsEntity):
    def __init__(self, game, pos, size, start_action = 'idle', friendly = False):
        super().__init__(game, 'cherub', pos, size)

        self.currency_drops['cog'] = random.randint(0, 3)
        self.currency_drops['blueCog'] = random.randint(2, 5)
        self.currency_drops['purpleCog'] = random.randint(0, 1)
        self.currency_drops['heartFragment'] = 1
        self.currency_drops['wing'] = 1
        self.currency_drops['yellowOrb'] = random.randint(0, 3)

        self.colour = (255, 249, 150)
        self.set_action(start_action)

        self.attack_power = 1
        self.death_intensity = 10
        self.attack_states = ['idle', 'jump', 'run', 'flying']
        self.gravity_affected = True

        self.gravity = 0.05
        self.anim_offset = (-4, -1)
        self.pos[1] += 1

        self.can_attack = False
        self.timer = random.randint(120,180)

        self.friendly = friendly
        if friendly:
            self.set_action('flying')
            self.velocity = [random.random() - 0.5, random.random() - 0.5]

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        super().update(tilemap, movement=movement)

        if self.action == 'idle':
            self.timer = max(self.timer - 1, 0)

            if not self.timer:
                self.set_action('run')
                self.velocity = [random.choice([-1, 1]), 0]
                self.flip_reset()
                self.can_attack = True

        elif self.action == 'jump':
            if self.collisions['down'] and tilemap.solid_check((self.rect().centerx, self.rect().centery + 16)):
                self.set_action('run')

        elif self.action == 'run':
            # Check jump condition, tilemap in_front and above:
            in_front = tilemap.solid_check(
                (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery))
            in_front_down = tilemap.solid_check(
                (self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 16))
            above = tilemap.solid_check(
                (self.rect().centerx, self.rect().centery - 16))
            
            if not above and random.random() < 0.05:
                self.set_action('flying')
                self.gravity = 0.05
                self.velocity = [random.random() - 0.5, -random.random() * 3]
                self.flip_reset()

            elif in_front and not above and self.collisions['down']:
                above_side = tilemap.solid_check(
                    (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery - 16))
                above_above_side = tilemap.solid_check(
                    (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery - 32))

                # Check jump 2 space:
                above_above = tilemap.solid_check(
                    (self.rect().centerx, self.rect().centery - 32))
                if not above and not above_above and not above_above_side and above_side:
                    self.set_action('jump')
                    self.velocity[1] = -3

                # Jump one space
                elif not above_side:
                    self.set_action('jump')
                    self.velocity[1] = -2

            # Turn around if bump into a wall
            elif (self.collisions['left'] or self.collisions['right']) and self.action != 'jump':
                self.flip_x = not self.flip_x
                self.velocity[0] *= -1
        

        elif self.action == 'flying':
            if random.random() < 0.05 and not tilemap.solid_check((self.rect().centerx, self.rect().centery - 16)):
                x_addition = 0.25 if self.vector_to(self.game.player)[0] > 0 else -0.25
                y_addition = -2 if self.vector_to(self.game.player)[1] > 0 else 0
                self.velocity = [random.random() - 0.5 + x_addition, -(random.random() + 2 + y_addition)]
                self.flip_reset()

            elif self.collisions['down'] and tilemap.solid_check((self.rect().centerx, self.rect().centery + 16)):
                self.set_action('idle')
                self.velocity = [0, 0]
                self.gravity = 0.12
                self.timer = random.randint(60, 120)

        if self.can_attack and random.random() < 0.01:
            if self.check_line_to_player() and np.linalg.norm(self.vector_to(self.game.player)) > 50 and not self.friendly:
                to_player = self.vector_to(self.game.player)
                norm = np.linalg.norm(to_player) * 2
                arrow_velocity = [to_player[0] / norm, to_player[1] / norm]
                self.game.extra_entities.append(Orb(self.game, self.rect().center, self.game.entity_info[38]['size'], arrow_velocity, self.type, colour = self.colour))

        # Death Condition
        if self.check_damages(player_contact=False):
            return True
        
class Imp(Cherub):
    def __init__(self, game, pos, size, start_action = 'idle', friendly = False):
        super().__init__(game, pos, size, start_action=start_action)

        self.colour = (124, 29, 42)
        self.friendly = friendly

        self.type = 'imp'
        self.set_action(start_action, override=True)

        self.currency_drops['redCog'] = random.randint(2, 5)
        self.currency_drops['redOrb'] = random.randint(0, 3)
        self.currency_drops['blueCog'] = 0
        self.currency_drops['yellowOrb'] = 0

class PenthouseLock(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'penthouse_lock', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.pos = list(pos)
        self.anim_offset = (0, 0)
        self.light_size = 0
        self.text = ['']
        self.can_create_portal = False

    def update_text(self):
        if self.game.wallet['penthouseKeys'] >= 1 or self.game.portals_met['final']:
            self.text = ['Welcome to The Penthouse.']

            if self.game.portals_met['final']:
                return False
            else:
                self.game.wallet['penthouseKeys'] -= 1
                self.game.portals_met['final'] = True
                return True

        else:
            self.text = ['Access not granted.']
            return False

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        dist_player = np.linalg.norm(self.vector_to(self.game.player))

        if dist_player < 15:
            xpos = (self.rect().centerx - self.game.render_scroll[0]) - 7
            ypos = (self.rect().centery -self.game.render_scroll[1]) - 22

            self.game.hud_display.blit(self.game.control_icons['Interract'], (xpos, ypos))

            if self.game.interraction_frame_int and not self.game.dead:
                if self.update_text():
                    #spawn final boss portal with effects
                    self.game.portals.append(Portal(self.game, [tilemap.tilesize * 18, tilemap.tilesize * -82], (tilemap.tilesize, tilemap.tilesize), 'final'))
                    for _ in range(10):
                        self.game.sparks.append(_spark.Spark([tilemap.tilesize * 18 + 8, tilemap.tilesize * -82 + 8], random.uniform(0, 2 * math.pi), 2, color=random.choice([(1, 1, 1), (255, 255, 255)])))
                self.game.run_text(self.text, talk_type = 'entity')

class Web(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'web', pos, size)
        self.gravity_affected = False
        self.collide_wall_check = False
        self.collide_wall = False
        self.anim_offset = (0, 0)
        self.currency_drops['chitin'] = 1 if random.random() < 0.1 else 0

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        # super().update(tilemap, movement=movement)
        if self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) >= 50:
            self.kill()
            return True

class Crate(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'crate', pos, size)
        self.gravity_affected = False
        self.collide_wall_check = False
        self.collide_wall = False
        self.anim_offset = (-2, -4)

        for currency in self.currency_drops.keys():
            if self.game.encounters_check[f'{currency}s'] and random.random() < 0.2 and currency not in ['hammer', 'credit']:
                self.currency_drops[currency] += 1

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        if self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) >= 50:
            self.kill()
            return True

        self.animation.update()

class Skull(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'skull', pos, size)
        self.gravity_affected = False
        self.collide_wall_check = False
        self.collide_wall = False
        self.anim_offset = (0, 0)
        self.checked = False

    def update(self, tilemap, movement=(0, 0)):
        if self.too_far_to_render():
            return False
        if self.rect().colliderect(self.game.player.rect()) and not self.checked:
            self.game.check_encounter('skull')
            self.checked = True

        elif self.rect().colliderect(self.game.player.rect()) and not self.game.dead:
            xpos = (self.rect().centerx - self.game.render_scroll[0]) - 7
            ypos = (self.rect().centery -self.game.render_scroll[1]) - 22
            self.game.hud_display.blit(self.game.control_icons['Interract'], (xpos, ypos))

            if self.game.interraction_frame_int:
                self.game.player.damage(1, self.type)


        self.animation.update()

class DumpMachine(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'dump_machine', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.pos = list(pos)
        self.anim_offset = (0, 0)
        self.light_size = 0
        self.credits = self.game.dump_machine_state['credits']
        self.attempts = self.game.dump_machine_state['attempts']
        self.max_credits = 8
        self.credit_value = 10
        self.selected_currency = ''
        self.active = self.game.dump_machine_state['active']
        self.quarter_length = int(self.size[0] / 4)
        self.mini_credit = pygame.transform.scale(self.game.display_icons['credits'], (4, 4))
        self.increment_currency()
        self.random_func_weights = [5, 2, 0.1]

    #RANDOM FUNCTIONS:
    def random_0(self):
        #Do Nothing
        pass
    def random_1(self):
        #Spit out random currency that the player has encountered
        available = [c for c in list(self.game.wallet.keys()) if (c not in ['credits', 'hammers', 'penthouseKeys'] and self.game.encounters_check[c])]
        if len(available) > 0:
            chosen_currency = random.choice(available)
            self.game.currency_entities.append(Currency(self.game, chosen_currency[:-1], self.rect().midtop, value=1, velocity_0=self.get_random_velocity()))
    def random_2(self):
        #Spawn heart altar
        self.game.extra_entities.append(HeartAltar(self.game, self.rect().midtop, self.game.entity_info[18]['size'], falling = True, value = 1,
                                                    velocity_0=self.get_random_velocity()))
        
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        ypos = (self.rect().centery - self.game.render_scroll[1]) + int(self.size[1] / 2) + 4
        if self.rect().colliderect(self.game.player.rect()) and self.active:

            #Changing currency:
            if self.game.player.pos[0] + 4 < self.pos[0] + self.quarter_length:
                xpos = (self.rect().x - self.game.render_scroll[0]) + self.quarter_length - 12
                if self.game.interraction_frame_int:
                    self.increment_currency()
            #Go
            elif self.game.player.pos[0] + 4 < self.pos[0] + 3 * self.quarter_length:
                xpos = (self.rect().x - self.game.render_scroll[0]) + 2 * self.quarter_length - 7
                if self.game.interraction_frame_int and self.attempts > 0:
                    self.do_random_thing()
                elif self.game.interraction_frame_int:
                    self.update_credits()
            #Adding credits
            else:
                xpos = (self.rect().x - self.game.render_scroll[0]) + 3 * self.quarter_length - 2
                if self.game.interraction_frame_int and self.credits < self.max_credits:
                    self.add_credit()
            
            self.game.hud_display.blit(self.game.control_icons['Interract'], (xpos, ypos))

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)
        if self.active:
            ypos = (self.rect().centery - self.game.render_scroll[1]) + int(self.size[1] / 2) + 4

            self.game.hud_display.blit(self.game.display_icons[self.selected_currency], (self.rect().x - self.game.render_scroll[0] + 5, ypos - 40))
            
            self.game.draw_text(f'{self.attempts}' if self.attempts > 0 else '-', 
                                ((self.rect().x - self.game.render_scroll[0]) + 2 * self.quarter_length, ypos - 29), 
                                self.game.text_font, (255, 255, 255), mode = 'center')

            for n in range(self.credits):
                x = (self.rect().x - self.game.render_scroll[0]) + 3 * self.quarter_length
                x += 6 if (n % 2) != 0 else 0 

                y = ypos - 40
                y += (n // 2) * 4
                self.game.hud_display.blit(self.mini_credit, (x, y))
        
    def get_random_velocity(self):
        x_vel = random.uniform(2,4) * (-1 if random.random() < 0.5 else 1)
        y_vel = random.uniform(-2, -4)
        return([x_vel, y_vel])

    def increment_currency(self):
        available_currencies = [c for c in list(self.game.wallet.keys()) if (self.game.wallet[c] > 0 and c not in ['credits', 'hammers', 'penthouseKeys'])]
        if len(available_currencies) == 0:
            self.selected_currency = 'cogs'
            return
        elif len(available_currencies) == 1:
            self.selected_currency = available_currencies[0]
            return
        else:
            found = False
            all_currencies = [c for c in list(self.game.wallet.keys()) if c not in ['credits', 'hammers', 'penthouseKeys']]
            for index, currency in enumerate(all_currencies):
        
                if currency == self.selected_currency:
                    found = True
                #Needs to be elif to get the next currency:
                elif found and currency in available_currencies:
                    self.selected_currency = currency
                    return
            self.selected_currency = available_currencies[0]
            return

    def add_credit(self):
        if self.game.wallet['credits'] > 0:
            self.game.wallet['credits'] -= 1
            self.game.dump_machine_state['credits'] += 1
            self.credits += 1

    def update_credits(self):
        if self.attempts > 0:
            self.game.dump_machine_state['attempts'] -= 1
            self.attempts -=  1

            if self.attempts == 0 and self.credits > 0:
                self.game.dump_machine_state['credits'] -= 1
                self.credits -=  1
                self.game.dump_machine_state['attempts'] += self.credit_value
                self.attempts += self.credit_value
            
        elif self.credits > 0:
            self.game.dump_machine_state['credits'] -= 1
            self.credits -=  1
            self.game.dump_machine_state['attempts'] += self.credit_value
            self.attempts += self.credit_value

    def do_random_thing(self):
        if (self.attempts > 0 or self.credits > 0) and self.game.wallet[self.selected_currency] > 0:
            self.game.wallet[self.selected_currency] -= 1
            self.update_credits()

            random_choice = random.choices(list(range(0, len(self.random_func_weights))), self.random_func_weights, k=1)[0]
            function = getattr(self, 'random_' + str(random_choice))
            function()

class Machine(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'machine', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.pos = list(pos)
        self.anim_offset = (0, 0)
        self.light_size = 0

        self.guest_list = [4, 9, 13, 15, 19, 20, 22, 37, 39,
                           32, 44]
        
        tile_w = game.tilemap.tilesize
        self.base = [f'{(self.rect().centerx + (n * tile_w)) // tile_w};{(self.rect().bottom + tile_w // 2) // tile_w}' for n in [-1,0,1]]

    def activate_machine(self):
        self.set_action('active')
        self.game.begin_final_boss()
        self.game.end_type = 2
        self.game.screenshake = max(20, self.game.screenshake)

    def destroy_machine(self):
        self.game.begin_final_boss()
        self.game.bosses.append(HilbertBoss(self.game, [self.rect().centerx + 48, self.rect().centery - (15 * self.game.tilemap.tilesize)], self.game.entity_info[46]['size']))
        self.set_action('destroyed')
        self.game.end_type = 1
        self.game.screenshake = max(30, self.game.screenshake)

    def end_game(self, end_type = 1):
        self.game.end_type = end_type
        self.game.completed_wins[str(self.game.end_type)] += 1

        for c in self.game.currency_entities.copy():
            self.game.wallet_temp[str(c.currency_type) + 's'] += c.value
            self.game.currency_entities.remove(c)

        for currency in self.game.wallet_temp.keys():
            self.game.wallet[currency] += self.game.wallet_temp[currency]
            self.game.wallet_temp[currency] = 0

        self.game.save_game(self.game.save_slot)
        self.game.game_running = False

    def spawn_random_guest(self, pos):
        
        random_guest_id = random.choice(self.guest_list)
        random_guest_size = self.game.entity_info[random_guest_id]['size']

        self.game.extra_entities.append(self.game.entity_info[random_guest_id]['object'](self.game, pos, random_guest_size, friendly = True))
        

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        dist_player = np.linalg.norm(self.vector_to(self.game.player))

        if self.action == 'idle':
            if random.random() < 0.03:
                self.game.sparks.append(_spark.Spark((self.rect().centerx, self.rect().centery - 15), random.uniform(0, 2 * math.pi), 2, color=random.choice([(149, 33, 211), (129, 29, 183)])))

        elif self.action == 'active':
            if random.random() < 0.1:
                self.game.sparks.append(_spark.Spark((self.rect().centerx, self.rect().centery - 15), random.uniform(0, 2 * math.pi), 3.5, color=random.choice([(149, 33, 211), (129, 29, 183)])))
                
            #Entities to go:
            entity_n = len(self.game.extra_entities)
            if entity_n > 1 and random.random() < 0.02:
                entity = random.choice([e for e in self.game.extra_entities if (e.type != 'machine')])
                entity_pos = entity.rect().center
                entity.kill()
                self.game.extra_entities.remove(entity)
                for _ in range(10):
                    self.game.sparks.append(_spark.Spark(entity_pos, random.uniform(0, 2 * math.pi), 2, color=random.choice([(149, 33, 211), (129, 29, 183)])))
                self.game.screenshake = max(20, self.game.screenshake)

            elif entity_n <= 1 and self.game.cave_darkness >= 255:
                self.end_game(end_type = 2)
            elif entity_n <= 1:
                self.game.cave_darkness = min(self.game.cave_darkness + 0.05, 255)

            #Remove tiles:
            for _ in range(2):
                random_tile = random.choice(list(self.game.tilemap.tilemap.keys()))
                if str(random_tile) not in self.base:
                    del self.game.tilemap.tilemap[random_tile]

        if dist_player < 35 and self.action == 'idle':
            xpos = (self.rect().centerx - self.game.render_scroll[0])
            ypos = (self.rect().centery - self.game.render_scroll[1]) - 60

            self.game.draw_text('Activate Machine       Destroy Machine', (xpos, ypos), self.game.text_font, (255, 255, 255), mode='center')
            self.game.hud_display.blit(self.game.control_icons['Down'], (xpos-40 - 8, ypos + 10))
            self.game.hud_display.blit(self.game.control_icons['Interract'], (xpos+40 - 8, ypos + 10))

            if self.game.interraction_frame_key == self.game.player_controls['Interract'] and not self.game.dead:
                self.destroy_machine()
                self.game.sfx['hit'].play()
                for _ in range(10):
                    self.game.sparks.append(_spark.Spark((self.rect().centerx, self.rect().centery - 15), random.uniform(0, 2 * math.pi), 4, color=random.choice([(230, 230, 230), (220, 220, 220)])))

            elif self.game.interraction_frame_key == self.game.player_controls['Down'] and not self.game.dead:
                self.activate_machine()
                for _ in range(10):
                    self.game.sparks.append(_spark.Spark((self.rect().centerx, self.rect().centery - 15), random.uniform(0, 2 * math.pi), 4, color=random.choice([(149, 33, 211), (129, 29, 183)])))

        elif self.action == 'destroyed' and len(self.game.bosses) == 0:
            if random.random() < 0.1:
                spawn_portal = random.choice([e for e in self.game.extra_entities if e.type == 'hilbert_orb_spawner'])
                orb_spawn_loc = spawn_portal.rect().center
                spawn_portal.set_action('activating')

                self.spawn_random_guest(orb_spawn_loc)

            if len(self.game.extra_entities) > 50 and (self.game.display_fps < 45 or len(self.game.extra_entities) > 200):
                self.end_game(end_type = 1)
                
class HilbertOrb(PhysicsEntity):
    def __init__(self, game, pos, size, velocity):
        super().__init__(game, 'hilbert_orb', pos, size)
        self.pos = list(pos)
        self.size = size
        self.velocity = list(velocity)
        self.gravity_affected = False
        self.max_speed = random.uniform(1.2, 1.6)
        self.target_mult = random.uniform(0.02, 0.06)
        self.targeted = False
        self.colour = (255, 0, 255)
        self.angle = random.uniform(0, math.pi * 2)

        self.is_boss = True

        self.boid_radius = 25
        self.boid_sepraration_strength = 0.001
        self.time_to_update_neighbours = 45
        self.neighbour_timer = 0
        self.neighbours = []

        self.anim_offset = (-3, -3)

    def boidsify(self):
        self.neighbour_timer = min(self.neighbour_timer + 1, self.time_to_update_neighbours)
        #find close boids:
        #only doing separation here because since theyre folloring the player its fine to not bunch up.
        if self.neighbour_timer >= self.time_to_update_neighbours:
            self.neighbour_timer = 0
            self.neighbours = []
            for boid in [e for e in self.game.extra_entities if (e.type == 'hilbert_orb' and e is not self)]:
                if np.linalg.norm(self.vector_to(boid)) < self.boid_radius:
                    self.neighbours.append(boid)

        if len(self.neighbours) == 0:
            return [0, 0]

        separation_extra = [0, 0]

        for boid in (b for b in self.neighbours if b in self.game.extra_entities):
            #separation
            separation_extra[0] += self.pos[0] - boid.pos[0]
            separation_extra[1] += self.pos[1] - boid.pos[1]
            
        return [separation_extra[0] * self.boid_sepraration_strength, separation_extra[1] * self.boid_sepraration_strength]
            

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.angle += 0.05

        toPlayer = self.vector_to(self.game.player)
        norm = np.linalg.norm(toPlayer)
        if abs(norm) < 0.01:
            norm = 0.01

        self.velocity[0] += self.target_mult * toPlayer[0] / norm
        self.velocity[1] += self.target_mult * toPlayer[1] / norm

        vel_norm = np.linalg.norm(self.velocity)
        if vel_norm > self.max_speed:
            self.velocity[0] /= vel_norm
            self.velocity[1] /= vel_norm

        boid_vel = self.boidsify()
        self.velocity[0] += boid_vel[0]
        self.velocity[1] += boid_vel[1]

        if any(self.collisions.values()) or self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) <= 50:
            self.circular_attack(25, self.rect().center, color=self.colour, color_str='purple')
            return True
        
    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset, rotation=self.angle)
        
class HelperOrb(PhysicsEntity):
    def __init__(self, game, pos, size, velocity):
        super().__init__(game, 'helper_orb', pos, size)
        self.pos = list(pos)
        self.size = size
        self.velocity = list(velocity)
        self.gravity_affected = False
        self.max_speed = 5
        self.target_mult = 1
        self.target_exists = True
        self.colour = (0, 255, 0)
        self.light_size = 20

        self.is_boss = True

        self.anim_offset = (-2, -2)

        self.target = random.choice([e for e in self.game.extra_entities if (e.type == 'hilbert_orb' and e.targeted == False)])
        self.target.targeted = True

    def create_sparks(self):
        velocity_angle = math.atan2(self.velocity[1], self.velocity[0])
        for _ in range(10):
            self.game.sparks.append(_spark.Spark(self.rect().center, velocity_angle + random.uniform(-1, 1), 1.5))

    def does_target_exist(self):
        if self.target in self.game.extra_entities:
            self.target_exists = True
            return True
        self.target_exists = False
        return False

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.does_target_exist():
            toTarget = self.vector_to(self.target)
            norm = np.linalg.norm(toTarget)
            if norm == 0:
                norm = 0.01

            self.velocity[0] += self.target_mult * toTarget[0] / norm
            self.velocity[1] += self.target_mult * toTarget[1] / norm

            vel_norm = np.linalg.norm(self.velocity)
            if vel_norm > self.max_speed:
                self.velocity[0] /= vel_norm
                self.velocity[1] /= vel_norm

        if any(self.collisions.values()):
            self.create_sparks()
            self.target.targeted = False
            return True
        
        elif self.rect().colliderect(self.target.rect()) and self.target_exists:
            self.create_sparks()
            self.game.extra_entities.remove(self.target)
            return True

class Helper(PhysicsEntity):
    def __init__(self, game, pos, size, post_boss = False, friendly = False):
        super().__init__(game, 'helper', pos, size)

        self.timer = random.randint(120,180)
        self.gravity_affected = False
        self.can_attack = False
        self.attacking = 'Hilbert'
        self.is_boss = True
        self.time_since_orb = 0
        self.help_frequency = 200
        self.light_size = 0
        self.set_action('grace')

        self.sad_messages = ['How could you...',
                             'I trusted you...',
                             'Aw man...',
                             'This isn\'t like you!',
                             'You\'re better than this.',
                             'This hurts to find out...',
                             'I\'m at such a loss...',
                             'I\'m not angry, just disappointed.',
                             'Why...']
        self.is_sad = False
        self.sad_timer = random.randint(60, 300)
        self.sad_message = ''

        if post_boss or friendly:
            self.activate(random.choice(list(game.characters_met.keys())).lower())
            self.flip_x = True if random.random() < 0.5 else False
            self.timer = 30

    def activate(self, character, flip = False):
        self.type = character
        self.gravity_affected = True
        self.flip_x = flip
        self.light_size = 25
        self.set_action('idle')

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.time_since_orb += 1

        if self.action =='grace':
            pass

        elif self.action == 'idle':
            self.timer = max(self.timer - 1, 0)

            if not self.timer and self.collisions['down']:
                self.set_action('run')
                self.velocity = [random.choice([-0.5, 0.5]), 0]
                self.flip_reset()
                self.can_attack = True

        elif self.action == 'jump':
            if self.collisions['down'] and tilemap.solid_check((self.rect().centerx, self.rect().centery + 16)):
                self.set_action('run')

        elif self.action == 'run':
            # Check jump condition, tilemap in_front and above:
            in_front = tilemap.solid_check(
                (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery))
            in_front_down = tilemap.solid_check(
                (self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 16))
            in_front_down_down = tilemap.solid_check(
                (self.rect().centerx + (-4 if self.flip_x else 4), self.rect().centery + 32))
            above = tilemap.solid_check(
                (self.rect().centerx, self.rect().centery - 16))

            if in_front and not above and self.collisions['down']:
                above_side = tilemap.solid_check(
                    (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery - 16))
                above_above_side = tilemap.solid_check(
                    (self.rect().centerx + (-10 if self.flip_x else 10), self.rect().centery - 32))

                # Check jump 2 space:
                above_above = tilemap.solid_check(
                    (self.rect().centerx, self.rect().centery - 32))
                if not above and not above_above and not above_above_side and above_side:
                    self.set_action('jump')
                    self.velocity[1] = -3

                # Jump one space
                elif not above_side:
                    self.set_action('jump')
                    self.velocity[1] = -2
            
            #Turn around if two block drop:
            elif not in_front and not in_front_down and not in_front_down_down:
                self.flip_x = not self.flip_x
                self.velocity[0] *= -1

            # Turn around if bump into a wall
            elif (self.collisions['left'] or self.collisions['right']) and self.action != 'jump':
                self.flip_x = not self.flip_x
                self.velocity[0] *= -1

            if random.random() < 0.1 and self.time_since_orb > self.help_frequency:
                if len([e for e in self.game.extra_entities if (e.type == 'hilbert_orb' and e.targeted == False)]) > 0:
                    self.game.extra_entities.append(HelperOrb(self.game, self.rect().center, self.game.entity_info[48]['size'], [0, -2]))
                    self.time_since_orb = 0

        if self.game.end_type == 2 and self.action != 'grace':
            if not self.is_sad:
                if not self.sad_timer:
                    self.is_sad = True
                    self.sad_timer = random.randint(180, 250)
                    self.sad_message = random.choice(self.sad_messages)
            
            elif self.is_sad:
                posx = int(self.pos[0] - self.game.render_scroll[0] + self.anim_offset[0])
                posy = int(self.pos[1] - self.game.render_scroll[1] + self.anim_offset[1])
                self.game.draw_text(self.sad_message, (posx + self.size[0], posy - 10), self.game.text_font, (255, 255, 255), mode='center')

                if not self.sad_timer:
                    self.is_sad = False
                    self.sad_timer = random.randint(180, 250)

            self.sad_timer = max(self.sad_timer - 1, 0)

class HilbertOrbSpawner(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'hilbert_orb_spawner', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.pos = list(pos)
        self.anim_offset = (0, 0)
        self.light_size = 0
        self.angle = 0
        self.angle_speed = random.uniform(2 * math.pi / 65, 2 * math.pi / 55)
        self.transparency = 0

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.action != 'idle':
            self.angle += self.angle_speed
            self.transparency += 1

        if self.action == 'activating' and self.transparency >= 255:
            self.set_action('active')

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset, rotation=self.angle, transparency = self.transparency)


class Boss(PhysicsEntity):
    def __init__(self, game, type, pos, size):
        super().__init__(game, type, pos, size)

        self.is_boss = True
        self.glowworm_follow = True
        if self.game.current_level != 'final':
            self.difficulty = round(self.game.floors[self.game.current_level] / self.game.boss_frequency) - 1
        else:
            self.difficulty = 1
        if self.game.current_level == 'infinite':
            self.difficulty = round(self.game.floors['infinite'] / self.game.boss_frequency) - 1
        self.death_intensity = 50

        self.currency_drops['cog'] = 20 + 2 * self.difficulty
        self.currency_drops['heartFragment'] = random.randint(0, 5) * self.difficulty

        self.damage_cooldown = 0
        self.timer = 0
        self.anim_offset = (0, 0)
        self.active = False

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.damage_cooldown:
            self.damage_cooldown = max(self.damage_cooldown - 1, 0)
        if self.check_damage_taken(invincible_states=self.invincible_states, passive_states=self.passive_states):
            self.set_action('dying')
            if self.type not in ['spookyboss']:
                self.gravity_affected = True
                self.collide_wall = True

        if self.action == 'dying':

            self.velocity[0] *= 0.98
            self.velocity[1] *= 0.98

            spawn_loc = (self.pos[0] + (self.size[0] / 2) - 3,
                        self.pos[1] + (self.size[1] / 2) - 3)
            for currency in self.currency_drops:
                if self.currency_drops[currency] > 0 and random.random() < 0.1:

                    self.game.currency_entities.append(
                        Currency(self.game, currency, spawn_loc, value=5))
                    self.currency_drops[currency] = max(
                        self.currency_drops[currency] - 1, 0)
            if max(self.currency_drops.values()) == 0:
                self.kill()
                return True

    def check_damage_taken(self, invincible_states=[], passive_states=[]):
        # Death Condition for Boss
        if self.action not in invincible_states:
            if abs(self.game.player.dashing) >= 50:
                if self.rect().colliderect(self.game.player.rect()):

                    if self.damage_self():
                        return True

        # Check for player collision, not dashing and in attack mode:
        if self.game.player.rect().colliderect(self.rect()):
            if abs(self.game.player.dashing) < 50 and self.action not in passive_states and not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

    def damage_self(self, amount=1):
        if not self.damage_cooldown:
            self.health -= amount
            self.damage_cooldown = 50
            self.damage(intensity=10)

            if self.health <= 0:
                # Not zero because this boss hasnt been removed yet, but returns True in 3 lines.
                if len(self.game.bosses) == 1:
                    for enemy in self.game.enemies.copy():
                        enemy.currency_drops['credit'] = 1
                        enemy.kill()
                    self.game.enemies = []
                return True

class NormalBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'normalboss', pos, size)

        self.currency_drops['wing'] = random.randint(2, 4) * self.difficulty

        self.gravity_affected = False
        self.collide_wall_check = True

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))
        self.wing_count = random.randint(
            20 + 20 * self.difficulty, 40 + 20 * self.difficulty)

        self.health = 2 + 2 * self.difficulty
        self.max_health = self.health

        self.anim_offset = (-3, -2)
        self.pos[1] += 3

        self.invincible_states = ['idle', 'dying']
        self.passive_states = ['idle', 'dying']

    def activate(self):
        self.set_action('activating')
        self.timer = 0
        self.velocity[0] = random.random() - 0.5
        self.gravity_affected = True
        self.active = True

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        to_player = self.vector_to(self.game.player)
        norm = np.linalg.norm(to_player)

        if self.action == 'idle':
            if norm < 140:
                for boss in self.game.bosses:
                    boss.activate()
                for grave in [e for e in self.game.extra_entities if e.type == 'gravestone']:
                    grave.activate()

        elif self.action == 'activating':
            self.timer += 1
            if self.animation.done or any(self.collisions.values()):
                self.set_action('flying')
                self.gravity_affected = False
                self.timer = 0

                self.velocity[0] = 2 * to_player[0] / norm
                self.velocity[1] = 2 * to_player[1] / norm

        elif self.action == 'flying':
            if self.health <= self.max_health / 2 and norm < 50 and random.random() < 0.05:
                self.set_action('attacking')

            # Head towards the player on wall impact, sometimes
            elif any(self.collisions.values()) and random.random() < 0.5:
                if not (tilemap.solid_check((self.rect().centerx + 8, self.rect().centery)) and tilemap.solid_check((self.rect().centerx - 8, self.rect().centery))):
                    self.velocity[0] = random.uniform(
                        0.8, 1.3) * 2 * to_player[0] / norm
                if not (tilemap.solid_check((self.rect().centerx, self.rect().centery + 8)) and tilemap.solid_check((self.rect().centerx, self.rect().centery - 8))):
                    self.velocity[1] = random.uniform(
                        0.8, 1.3) * 2 * to_player[1] / norm

            # Otherwise just bounce off
            elif self.collisions['left'] or self.collisions['right']:
                self.velocity[0] *= random.uniform(-1.2, -0.9)
            elif self.collisions['up'] or self.collisions['down']:
                self.velocity[1] *= random.uniform(-1.2, -0.9)

        elif self.action == 'attacking':

            self.wall_rebound()

            if np.linalg.norm(self.velocity) > 0.1:
                self.velocity[0] *= 0.98
                self.velocity[1] *= 0.98

            elif self.animation.done:
                self.set_action('flying')

                for _ in range(20):
                    self.game.sparks.append(
                        _spark.Spark(self.rect().center, random.random() * 2 * math.pi, 2 + random.random()))
                    self.game.particles.append(_particle.Particle(self.game, 'particle1', self.rect().center, vel=[math.cos(
                        random.random() * 2 * math.pi), math.cos(random.random() * 2 * math.pi)], frame=random.randint(0, 7)))

                # Check for player collision, not dashing and in attack mode:
                self.circular_attack(self.attack_radius)

                batpos = (self.rect().center)
                for _ in range(random.randint(1, self.difficulty + 1)):
                    self.game.enemies.append(Bat(self.game, (batpos[0] - 3, batpos[1] - 1), self.game.entity_info[4]['size'], grace_done=True, velocity=[
                                             3 * to_player[0] / norm + random.random() / 4, 3 * to_player[1] / norm + random.random() / 4]))

                self.velocity[0] = 0.5 + random.random()
                self.velocity[1] = 0.5 + random.random()

    def render(self, surface, offset=(0, 0)):
        angle = 0
        if self.action == 'activating':
            angle = self.animation.frame / 24.5

        super().render(surface, offset=offset, rotation=angle)

class GrassBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'grassboss', pos, size)

        self.currency_drops['eye'] = random.randint(4, 10) * self.difficulty

        self.gravity_affected = False
        self.collide_wall_check = True
        self.collide_wall = False

        self.attack_radius = int(100 * math.atan(self.difficulty / 5)) + 10
        self.eye_count = random.randint(
            20 + 20 * self.difficulty, 40 + 20 * self.difficulty)

        self.health = 2 + 2 * self.difficulty
        self.max_health = self.health

        self.speed = -1
        self.heading = [self.speed, 0]
        self.wall_side = [0, -self.speed]
        self.time_since_turn = 0
        self.pos[0] += 6
        self.anim_offset = (-3, -3)

        self.invincible_states = ['idle', 'dying']
        self.passive_states = ['idle', 'dying']

        self.returning = False
        self.time_since_air = 0

    def activate(self):
        self.set_action('activating')
        self.timer = 0
        self.active = True

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        self.time_since_air += 1

        if self.action == 'idle':
            to_player = self.vector_to(self.game.player)
            norm = np.linalg.norm(to_player)
            if norm < 120:
                for boss in self.game.bosses:
                    boss.activate()
                for grave in [e for e in self.game.extra_entities if e.type == 'gravestone']:
                    grave.activate()

        elif self.action == 'activating':
            self.timer += 1
            if self.animation.done:
                self.set_action('run')
                self.pos[1] -= 5
                self.timer = 0

        elif self.action == 'run':
            # Turn around at torches
            for ent in self.game.extra_entities:
                if ent.type == 'torch' and ent.rect().colliderect(self.rect()):

                    # Reverse direction
                    self.heading[0] *= -1
                    self.heading[1] *= -1

                    self.pos[0] -= self.velocity[0]
                    self.pos[1] -= self.velocity[1]

                    self.time_since_turn = 5

            if self.time_since_air > 60:
                self.pos[1] += 1
                self.time_since_air = 0

            # spawning small rolypolys
            if random.random() < 0.005 and self.health <= self.max_health / 2:
                # Find spot to spawn lil guy
                available_spawn_spots = []
                for spawn_loc_offset in [[0, 0], [0, 1], [1, 0], [1, 1]]:
                    tile_loc = [int(self.pos[0] // tilemap.tilesize) + spawn_loc_offset[0],
                               int(self.pos[1] // tilemap.tilesize) + spawn_loc_offset[1]]

                    if str(str(tile_loc[0]) + ';' + str(tile_loc[1])) not in self.game.tilemap.tilemap:
                        available_spawn_spots.append(
                            [tile_loc[0] * self.game.tilemap.tilesize, tile_loc[1] * self.game.tilemap.tilesize])

                # Spawn lil guys
                for _ in range(self.difficulty + round(random.random())):
                    spawn_spot = random.choice(available_spawn_spots)
                    self.game.enemies.append(RolyPoly(self.game, [
                                             spawn_spot[0], spawn_spot[1] + 2], self.game.entity_info[9]['size'], initialFall=True))

            if self.time_since_turn < 5:
                self.time_since_turn += 1

            # Change direction if it leaves a tileblock:
            if not any(x == True for x in self.collisions.values()) and self.time_since_turn > 3:
                self.wall_side, self.heading = [-self.heading[0], -
                                               self.heading[1]], self.wall_side
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.time_since_turn = 0
                self.time_since_air = 0

            # Also change direction if run into a wall:
            elif any(self.collisions.values()) and self.time_since_turn > 3:
                self.wall_side, self.heading = self.heading, [
                    -self.wall_side[0], -self.wall_side[1]]
                self.velocity[0] = self.heading[0]
                self.velocity[1] = self.heading[1]
                self.time_since_turn = 0

            if random.random() < 0.005 and not any(self.collisions.values()):
                self.set_action('attacking')
                self.velocity = [0, 0]
                self.gravity_affected = True
                self.timer = 30
                self.wall_side[0], self.wall_side[1] = -self.wall_side[0], self.wall_side[1]

        elif self.action == 'attacking':
            if self.timer:
                self.timer = max(self.timer - 1, 0)

            if any(self.collisions.values()) and not self.timer and not self.returning:
                self.timer = random.randint(70, 100)
                self.collide_wall = True

                if random.random() < 0.3:
                    self.velocity[1] = -8
                    self.velocity[0] = random.random() - 0.5
                    self.pos[1] -= 2
                    self.timer = 5
                    self.returning = True

                else:
                    self.circular_attack(self.attack_radius)

            elif any(self.collisions.values()) and not self.timer and self.returning:
                self.gravity_affected = False
                self.collide_wall = False
                self.returning = False
                self.set_action('run')

                self.wall_side[0], self.wall_side[1] = 0, -1
                self.heading[0], self.heading[1] = random.choice([-1, 1]), 0

class SpaceBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spaceboss', pos, size)

        self.currency_drops['purpleCog'] = self.difficulty

        self.gravity_affected = True
        self.collide_wall_check = True

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))

        self.health = 2 + 2 * self.difficulty
        self.max_health = self.health

        self.shoot_count_max = self.difficulty
        self.shoot_count = self.shoot_count_max
        self.speed = self.difficulty / 2
        self.light_size = 0

        self.invincible_states = ['idle', 'activating',
                                 'attacking', 'flying', 'dying']
        self.passive_states = ['idle', 'dying']

        self.anim_offset = (-3, -8)

    def activate(self):
        self.set_action('activating')
        self.velocity[0] = random.uniform(-0.75, 0.75)
        self.velocity[1] = -random.uniform(2, 3)
        self.active = True

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        # Also damage self from meteor collision:
        for entity in self.game.extra_entities:
            if entity.type == 'meteor' and entity.action == 'kaboom':
                if self.rect().colliderect(entity.rect()):

                    if self.damage_self():
                        self.set_action('dying')
                        self.gravity_affected = True

        to_player = (self.game.player.rect().x - self.rect().x,
                    self.game.player.rect().y - self.rect().y)
        norm = np.linalg.norm(to_player)

        if self.action == 'idle':
            if norm < 50:
                for boss in self.game.bosses:
                    boss.activate()
                for grave in [e for e in self.game.extra_entities if e.type == 'gravestone']:
                    grave.activate()

                for _ in range(3):
                    self.game.sparks.append(_spark.Spark(self.rect().midbottom, random.uniform(
                        0, math.pi), random.uniform(1.5, 2), color=random.choice([(0, 255, 0), (200, 0, 200)])))

        elif self.action == 'activating':
            if any(self.collisions.values()):
                self.set_action('flying')
                self.light_size = 25
                self.gravity_affected = False

                self.velocity[0] = self.speed * to_player[0] / norm
                self.velocity[1] = self.speed * to_player[1] / norm

            elif random.random() < 0.03:
                self.velocity[0] = random.uniform(-0.75, 0.75)
                self.velocity[1] = -random.uniform(2, 3)

                for _ in range(3):
                    self.game.sparks.append(_spark.Spark(self.rect().midbottom, random.uniform(
                        0, math.pi), random.uniform(1.5, 2), color=random.choice([(0, 255, 0), (200, 0, 200)])))
                    
                self.light_size = random.choice([0, 25])

        elif self.action == 'flying':
            if self.health <= self.max_health / 2 and norm > 100 and random.random() < 0.01:
                self.set_action('attacking')
                self.timer = 0
                self.shoot_count = 0

            # Head towards the player on wall impact, sometimes
            elif any(self.collisions.values()) and random.random() < 0.5:
                if not (tilemap.solid_check((self.rect().centerx + 8, self.rect().centery)) and tilemap.solid_check((self.rect().centerx - 8, self.rect().centery))):
                    self.velocity[0] = random.uniform(
                        0.8, 1.3) * self.speed * to_player[0] / norm
                if not (tilemap.solid_check((self.rect().centerx, self.rect().centery + 8)) and tilemap.solid_check((self.rect().centerx, self.rect().centery - 8))):
                    self.velocity[1] = random.uniform(
                        0.8, 1.3) * self.speed * to_player[1] / norm

            # Otherwise just bounce off
            elif self.collisions['left'] or self.collisions['right']:
                self.velocity[0] *= random.uniform(-1.2, -0.9)
            elif self.collisions['up'] or self.collisions['down']:
                self.velocity[1] *= random.uniform(-1.2, -0.9)

        elif self.action == 'attacking':
            self.timer += 1

            self.wall_rebound()

            if np.linalg.norm(self.velocity) > 0.1:
                self.velocity[0] *= 0.98
                self.velocity[1] *= 0.98

            if self.timer % 45 == 0 and self.shoot_count < self.shoot_count_max:
                self.shoot_count += 1

                self.game.sfx['shoot'].play()
                angleto_player = math.atan2(to_player[1], (to_player[0] if to_player[0] != 0 else 0.01))
                bullet_speed = 2 * math.atan(self.difficulty / 2)

                for angle in np.linspace(angleto_player, angleto_player + math.pi * 2, 5 + 3 * self.difficulty):
                    bullet_velocity = (bullet_speed * math.cos(angle), bullet_speed * math.sin(angle))

                    self.game.projectiles.append(Bullet(
                        self.game, [self.rect().centerx, self.rect().centery], bullet_velocity, self.type))
                    self.game.sparks.append(
                        _spark.Spark(self.rect().center, angle + math.pi, self.difficulty))

            elif self.animation.done:
                self.set_action('flying')
                self.timer = 0

                self.velocity[0] = self.speed * to_player[0] / norm
                self.velocity[1] = self.speed * to_player[1] / norm

        # Create sparks
        if self.action not in ['idle', 'activating']:
            if random.random() < 0.1:
                self.game.sparks.append(_spark.Spark(self.rect().midbottom, random.uniform(
                    0, math.pi), random.uniform(1.5, 2), color=random.choice([(0, 255, 0), (200, 0, 200)])))

class Gravestone(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'gravestone', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.pos = list(pos)
        self.spawn_count = round(self.game.floors[self.game.current_level] / 10)
        self.spawning = False
        self.anim_offset = (0, 0)

    def activate(self):
        self.set_action('active')

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.action == 'idle':
            to_player = (self.game.player.rect().centerx - self.rect().centerx,
                        self.game.player.rect().centery - self.rect().centery)
            norm = np.linalg.norm(to_player)

            if norm < 50:
                for boss in self.game.bosses:
                    boss.activate()
                for grave in [e for e in self.game.extra_entities if e.type == 'gravestone']:
                    grave.activate()

        elif self.action == 'active' and self.spawn_count and random.random() < 0.05:
            self.game.bosses.append(SpookyBoss(self.game, [
                                    self.pos[0] + random.randint(-8, 40), self.pos[1] + random.randint(16, 32)], self.game.entity_info[25]['size']))
            self.spawn_count -= 1

class FlyGhost(PhysicsEntity):
    def __init__(self, game, pos, size, difficulty = 1, friendly = False):
        super().__init__(game, 'fly_ghost', pos, size)

        self.gravity_affected = False
        self.collide_wall = False
        self.pos = list(pos)
        self.anim_offset = (-2, -2)
        self.is_boss = True
        self.difficulty = difficulty

        self.credit_count = 1 if random.random() < 0.05 else 0

        to_player = (self.game.player.rect().centerx - self.rect().centerx,
                    self.game.player.rect().centery - self.rect().centery)
        self.friendly = friendly
        if friendly:
            to_player = [random.random() - 0.5, random.random() - 0.5]
        norm = np.linalg.norm(to_player)

        self.velocity = [random.uniform(0.9, 1.1 + 0.3 * self.difficulty) * to_player[0] /
                         norm, random.uniform(0.9, 1.1 + 0.3 * self.difficulty) * to_player[1] / norm]
        self.angle = math.atan2(-self.velocity[1], self.velocity[0])

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        to_player = (self.game.player.rect().centerx - self.rect().centerx,
                    self.game.player.rect().centery - self.rect().centery)
        norm = np.linalg.norm(to_player)

        if norm > self.game.screen_width / 2.7 or (len(self.game.bosses) == 0 and not self.friendly):
            return True

        if random.random() < 0.1:
            self.game.sparks.append(_spark.Spark(
                self.rect().center, -self.angle + math.pi + random.uniform(-0.3, 0.3), 1.5))

        # Death Condition
        elif abs(self.game.player.dashing) >= 50 and not self.friendly:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill()
                return True

        # Check for player collision
        elif self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and not self.friendly:
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset, rotation=self.angle)

class SpookyBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spookyboss', pos, size)

        self.currency_drops['heartFragment'] = 0
        self.currency_drops['chitin'] = random.randint(2, 5) * self.difficulty

        self.gravity_affected = False
        self.collide_wall = False

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))

        self.health = 5
        self.max_health = self.health
        self.prev_health = self.health

        self.transparency = 0
        self.transparency_inc = 3
        self.tele_coords = [0, 0]
        self.timer = 0
        self.time_vulnerable = 0
        self.active = True

        self.player_tele_dist = 100
        self.velocity[0] = random.uniform(-0.5, 0.5)
        self.velocity[1] = random.uniform(-0.5, 0)

        self.invincible_states = ['idle', 'teleporting', 'dying']
        self.passive_states = ['idle', 'teleporting', 'dying']

        self.anim_offset = (0, 0)

    def activate(self):
        self.active = True

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        if self.action == 'idle':
            self.transparency = min(self.transparency + 2, 255)
            if self.transparency >= 255:
                self.set_action('flying')
                self.time_vulnerable = 0

        elif self.action == 'flying':
            self.time_vulnerable += 1
            to_player = (self.game.player.rect().centerx - self.rect().centerx,
                        self.game.player.rect().centery - self.rect().centery)
            norm = np.linalg.norm(to_player)

            # Teleport
            if (random.random() < 0.005 and self.time_vulnerable > 180) or norm > 250 or (self.health < self.prev_health):
                self.prev_health = self.health
                self.set_action('teleporting')

                found_spot = False
                check_spot = [0, 0]
                player_pos_tile = (self.game.player.pos[0] // self.game.tilemap.tilesize,
                                 self.game.player.pos[1] // self.game.tilemap.tilesize)

                while not found_spot:
                    check_spot[0], check_spot[1] = int(player_pos_tile[0] + random.choice(
                        range(-5, 6))), int(player_pos_tile[1] + random.choice(range(-10, 4)))
                    loc_str = str(check_spot[0]) + ';' + str(check_spot[1])
                    loc_str2 = str(check_spot[0]) + ';' + str(check_spot[1] + 1)
                    if loc_str not in self.game.tilemap.tilemap and loc_str2 not in self.game.tilemap.tilemap:
                        found_spot = True
                self.tele_coords = [
                    check_spot[0] * tilemap.tilesize, check_spot[1] * tilemap.tilesize]

                self.transparency = -255
                self.transparency_inc = random.choice([1, 2, 3])
                self.timer = random.randint(30, 90)

        elif self.action == 'teleporting':
            # Fading away
            if self.timer and self.transparency < 0:
                self.transparency = min(
                    self.transparency + self.transparency_inc, 0)

            # Waiting to move (invisible)
            elif self.transparency == 0 and self.timer:
                self.timer = max(self.timer - 1, 0)

            # Teleport
            elif self.transparency == 0 and not self.timer:
                self.pos[0] = self.tele_coords[0]
                self.pos[1] = self.tele_coords[1]

                self.velocity[0] = (random.random() - 0.5) * 0.5
                self.velocity[1] = (random.random() - 0.5) * 0.5
                self.transparency += 1

            # Fading back in
            elif not self.timer and self.transparency > 0:
                self.transparency = min(
                    self.transparency + self.transparency_inc, 255)

                if self.transparency >= 255:
                    self.set_action('flying')
                    self.time_vulnerable = 0

        # Create attack ghost
        if random.random() < 0.01:
            spawn_angle = random.random() * 2 * math.pi
            spawn_dist = self.game.screen_width / 2.8

            spawn_pos = [self.game.player.pos[0] + (math.sin(
                spawn_angle) * spawn_dist), self.game.player.pos[1] + (math.cos(spawn_angle) * spawn_dist)]

            self.game.extra_entities.append(FlyGhost(
                self.game, spawn_pos, self.game.entity_info[32]['size'], difficulty = self.difficulty))

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset, transparency=abs(self.transparency))

class RubiksBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'rubiksboss', pos, size)

        self.currency_drops['redCog'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['blueCog'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['purpleCog'] = random.randint(0, 1) * self.difficulty
        self.currency_drops['heartFragment'] = 0

        self.gravity_affected = False
        self.collide_wall_check = True

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))

        self.health = 2 + 2 * self.difficulty
        self.max_health = self.health

        self.speed = 1
        self.max_speed = 3
        self.can_move = True

        self.anim_offset = (0, 0)

        self.states = ['white', 'yellow', 'blue', 'green', 'red', 'orange']
        self.invincible_states = ['idle', 'white', 'yellow',
                                 'blue', 'green', 'red', 'orange', 'dying']
        self.passive_states = ['idle', 'dying']
        self.half_block_dist = game.tilemap.tilesize / 2

    def activate(self):
        self.set_action(random.choice(self.states))
        self.timer = random.randint(90, 120)
        self.active = True

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        if self.action == 'idle':
            to_player = (self.game.player.rect().x - self.rect().x,
                        self.game.player.rect().y - self.rect().y)
            norm = np.linalg.norm(to_player)
            if norm < 150:
                for boss in self.game.bosses:
                    boss.activate()
                for grave in [e for e in self.game.extra_entities if e.type == 'gravestone']:
                    grave.activate()

        elif self.action != 'dying':
            # When timer runs out, move in a random direction until hit a wall
            self.timer = max(self.timer - 1, 0)
            # Then change colour and reset timer.
            if self.can_move and not self.timer:
                # Find random directions that entity can move in
                self.can_move_vectors = []
                pos_centre = [self.rect().centerx, self.rect().centery]

                # left:
                if not (tilemap.solid_check([pos_centre[0] - 3 * self.half_block_dist, pos_centre[1] - self.half_block_dist], return_value='bool') or tilemap.solid_check([pos_centre[0] - 3 * self.half_block_dist, pos_centre[1] + self.half_block_dist], return_value='bool')):
                    self.can_move_vectors.append([-self.speed, 0])
                # right:
                if not (tilemap.solid_check([pos_centre[0] + 3 * self.half_block_dist, pos_centre[1] - self.half_block_dist], return_value='bool') or tilemap.solid_check([pos_centre[0] + 3 * self.half_block_dist, pos_centre[1] + self.half_block_dist], return_value='bool')):
                    self.can_move_vectors.append([self.speed, 0])
                # up:
                if not (tilemap.solid_check([pos_centre[0] - self.half_block_dist, pos_centre[1] - 3 * self.half_block_dist], return_value='bool') or tilemap.solid_check([pos_centre[0] + self.half_block_dist, pos_centre[1] - 3 * self.half_block_dist], return_value='bool')):
                    self.can_move_vectors.append([0, -self.speed])
                # down:
                if not (tilemap.solid_check([pos_centre[0] - self.half_block_dist, pos_centre[1] + 3 * self.half_block_dist], return_value='bool') or tilemap.solid_check([pos_centre[0] + self.half_block_dist, pos_centre[1] + 3 * self.half_block_dist], return_value='bool')):
                    self.can_move_vectors.append([0, self.speed])

                # Set velocity to that direction
                self.velocity = random.choice(self.can_move_vectors)
                self.can_move = False

            else:
                self.velocity[0] = max(
                    min(self.velocity[0] * 1.02, self.max_speed), -self.max_speed)
                self.velocity[1] = max(
                    min(self.velocity[1] * 1.02, self.max_speed), -self.max_speed)

            # When hit a tile, stop and change colour, repeat
            if any(self.collisions.values()):
                self.timer = random.randint(120, 180)
                self.velocity = [0, 0]
                self.set_action(random.choice(self.states))
                self.can_move = True

            # Spawn falling cube:
            if random.random() < 0.01 and len(self.game.extra_entities) < 20:
                pos_centre = [self.rect().centerx, self.rect().centery]
                if not (tilemap.solid_check([pos_centre[0] - self.half_block_dist, pos_centre[1] + 3 * self.half_block_dist], return_value='bool') or tilemap.solid_check([pos_centre[0] + self.half_block_dist, pos_centre[1] + 3 * self.half_block_dist], return_value='bool')):
                    if self.action != 'dying':
                        self.game.extra_entities.append(RubiksCubeThrow(self.game, [
                                                       self.pos[0] + self.half_block_dist, self.pos[1] + self.half_block_dist], self.game.entity_info[34]['size'], action=self.action))

class RubiksCubeThrow(PhysicsEntity):
    def __init__(self, game, pos, size, action='idle'):
        super().__init__(game, 'rubiksCube', pos, size)

        self.gravity_affected = True
        self.pos = list(pos)
        self.spawn_count = round(self.game.floors[self.game.current_level] / 10)
        self.anim_offset = (0, 0)
        self.activated = False
        self.attack_radius = 50
        self.bomb_delay = 5
        self.initial_attack = False
        self.states = {
            'white': (155, 155, 155),
            'yellow': (175, 152, 0),
            'blue': (0, 0, 204),
            'green': (0, 119, 0),
            'red': (175, 0, 0),
            'orange': (206, 123, 0),
        }
        self.set_action(action)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if not self.initial_attack:
            if any(self.collisions.values()):
                self.circular_attack(
                    self.attack_radius / 2, color=self.states[self.action], color_str=self.action)
                self.initial_attack = True

        if self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) >= 50:
            self.velocity = [random.random() - 0.5, random.uniform(-8, -6)]
            self.activated = True

        elif self.activated:
            self.bomb_delay = max(self.bomb_delay - 1, 0)
            if any(self.collisions.values()) and not self.bomb_delay:
                self.circular_attack(
                    self.attack_radius, color=self.states[self.action], color_str=self.action, can_damage_boss=True)
                self.kill()
                return True
            for boss in self.game.bosses:
                if self.rect().colliderect(boss.rect()):
                    self.circular_attack(
                        self.attack_radius, color=self.states[self.action], color_str=self.action, can_damage_boss=True)
                    self.kill()
                    return True

class AussieBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'aussieboss', pos, size)

        self.currency_drops['fairyBread'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['boxingGlove'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['chitin'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['purpleCog'] = random.randint(0, 1) * self.difficulty

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))
        self.active_min_time = max(60, 100 - self.difficulty * 20)
        self.active_max_time = max(70, 120 - self.difficulty * 20)

        self.health = 6 + 2 * self.difficulty
        self.max_health = self.health

        self.gravity_affected = True
        self.timer = 0

        self.anim_offset = (-8, -12)

        self.invincible_states = ['idle', 'dying']
        self.passive_states = ['idle', 'dying']

    def activate(self):
        self.set_action('active')
        self.timer = random.randint(90, 120)
        self.active = True

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        if self.action == 'idle':
            to_player = (self.game.player.rect().x - self.rect().x,
                        self.game.player.rect().y - self.rect().y)
            norm = np.linalg.norm(to_player)
            if norm < 150:
                for boss in self.game.bosses:
                    boss.activate()
                for grave in [e for e in self.game.extra_entities if e.type == 'gravestone']:
                    grave.activate()

        elif self.action == 'active':
            self.timer = max(self.timer - 1, 0)

            if not self.timer:
                self.set_action('prep')

        elif self.action == 'prep':

            if self.animation.done:
                # JUMP ROUGHLY IN DIRECTION OF PLAYER
                self.set_action('jumping')
                if self.pos[0] < self.game.player.pos[0]:
                    self.flip_x = False
                else:
                    self.flip_x = True

                player_above = False
                if self.pos[1] > self.game.player.pos[1]:
                    player_above = True

                self.velocity[0] = -(random.random() + 3.5) if self.flip_x else (random.random() + 3.5)
                self.velocity[1] = -(random.random() * 4 + 7 if player_above else 4)
                self.time_since_bounce = 0

        elif self.action == 'jumping':
            self.time_since_bounce = min(self.time_since_bounce + 1, 10)
            self.velocity[0] *= 0.99
            self.velocity[1] *= 0.99

            if self.collisions['left'] or self.collisions['right'] and self.time_since_bounce >= 10:
                self.time_since_bounce = 0
                self.velocity[0] = -self.velocity[0]
                self.flip_x = not self.flip_x

            if self.collisions['down']:
                pos_centre = [self.rect().centerx, self.rect().centery]
                if tilemap.solid_check([pos_centre[0] - tilemap.tilesize / 2, pos_centre[1] + tilemap.tilesize], return_value='bool') or tilemap.solid_check([pos_centre[0] + tilemap.tilesize / 2, pos_centre[1] + tilemap.tilesize], return_value='bool'):
                    self.velocity = [0, 0]

                    self.timer = random.randint(self.active_min_time, self.active_max_time)
                    self.set_action('active')
                    self.circular_attack(self.attack_radius,
                                        pos=self.rect().midbottom)

                    # Sometimes spawn other lil guys:
                    spawn_pos = [self.rect().centerx - 8, self.rect().y]

                    if random.random() < 0.5:
                        self.game.enemies.append(
                            Kangaroo(self.game, spawn_pos, self.game.entity_info[19]['size']))
                    else:
                        self.game.enemies.append(
                            Echidna(self.game, spawn_pos, self.game.entity_info[20]['size']))
                        
class HeavenBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'heavenboss', pos, size)

        self.currency_drops['wing'] = random.randint(2, 3) * self.difficulty
        self.currency_drops['blueCog'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['yellowOrb'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['purpleCog'] = random.randint(0, 1) * self.difficulty

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))

        self.health = 6 + 2 * self.difficulty
        self.max_health = self.health

        self.gravity_affected = False
        self.gravity = 0.05
        self.flip_x = True
        self.timer = 0
        self.shoot_count = 0

        self.anim_offset = (0, 0)
        self.pos[0] += 10
        self.set_action('flying')
        self.anim_offset = (-11, -2)
        self.orb_type = 'cherub'
        self.orb_colour = (255, 249, 150)

        self.invincible_states = ['dying']
        self.passive_states = ['dying']

    def activate(self):
        self.active = True
        self.gravity_affected = True
        self.timer = 120

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        if not self.active:
            to_player = self.vector_to(self.game.player)
            norm = np.linalg.norm(to_player)
            if norm < 75:
                for boss in self.game.bosses:
                    boss.activate()
                for grave in [e for e in self.game.extra_entities if e.type == 'gravestone']:
                    grave.activate()

        elif self.action == 'flying':
            self.timer = max(self.timer - 1, 0)
            if random.random() < 0.05 and not tilemap.solid_check((self.rect().centerx, self.rect().centery - 16)):
                x_addition = 0.25 if self.vector_to(self.game.player)[0] > 0 else -0.25
                y_addition = -2 if self.vector_to(self.game.player)[1] > 0 else 0
                self.velocity = [random.random() - 0.5 + x_addition, -(random.random() + 2 + y_addition)]
                self.flip_reset()

            if self.active and self.timer == 0:
                self.shoot_count += 1

                #create lil guys
                if self.health <= self.max_health / 2 and random.random() < 0.3:
                    if self.type == 'heavenboss':
                        self.game.enemies.append(Cherub(self.game, self.pos, self.game.entity_info[37]['size'], start_action='flying'))
                    elif self.type == 'hellboss':
                        self.game.enemies.append(Imp(self.game, self.pos, self.game.entity_info[39]['size'], start_action='flying'))

                for angle in np.linspace(-math.pi / 2, math.pi * (3/2), self.difficulty + 2):
                    speed = min(0.8 + 0.2 * self.difficulty, 2)
                    orb_velocity = [speed * math.cos(angle), speed * math.sin(angle)]
                    self.game.extra_entities.append(Orb(self.game, self.rect().center, self.game.entity_info[38]['size'], orb_velocity, self.orb_type, colour = self.orb_colour))

                if self.shoot_count > self.difficulty:
                    self.shoot_count = 0
                    self.timer = random.randint(250,350)
                else:
                    self.timer = random.randint(45,60)

class HellBoss(HeavenBoss):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size)

        self.type = 'hellboss'
        self.set_action('flying', override=True)
        self.orb_type = 'imp'
        self.orb_colour = (124, 29, 42)

        self.currency_drops['blueCog'] = 0
        self.currency_drops['redCog'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['yellowOrb'] = 0
        self.currency_drops['redOrb'] = random.randint(2, 5) * self.difficulty

class HilbertBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'hilbertboss', pos, size)

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))

        self.currency_drops['purpleCog'] = 20

        self.health = 15
        self.stage_two_health = 10
        self.max_health = self.health

        self.gravity_affected = True
        self.gravity = 0.05

        self.anim_offset = (0, 0)

        self.invincible_states = ['idle', 'dying']
        self.passive_states = ['idle', 'dying']

        self.shoot_count_max = 3
        self.shoot_num = 0
        self.shoot_count = 0
        self.shoot_countdown = 300

        self.can_shoot = False
        self.preparing_to_shoot = False
        self.preparing = 0
        self.preparing_time = 60
        self.flip_x = True

    def activate(self):
        self.set_action('active')
        self.game.sfx['hilbert_music'].play(loops = -1, fade_ms = 1000)
        self.game.sfx['final_music'].fadeout(2000)
        self.active = True

    def set_preparing_to_shoot(self):
        self.preparing_to_shoot = True
        self.preparing = 0

    def begin_shooting(self):
        self.can_shoot = True
        self.shoot_countdown = 0
        self.preparing_to_shoot = False
        self.shoot_num = random.randint(5, 7)

    def stop_shooting(self):
        self.shoot_countdown = random.randint(250,300)
        self.shoot_count = 0
        self.can_shoot = False
        self.preparing_to_shoot = False

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            self.game.sfx['hilbert_music'].fadeout(1000)
            return True
        
        toPlayer = self.vector_to(self.game.player)
        
        if self.action == 'idle':
            self.pos[1] += 1

            
            if np.linalg.norm(toPlayer) < 50 or any(self.collisions.values()):
                self.activate()

        elif self.action == 'active':
            self.shoot_countdown = max(self.shoot_countdown - 1, 0)

            if np.linalg.norm(toPlayer) < 35 and not self.can_shoot and not self.preparing_to_shoot:
                self.set_preparing_to_shoot()

            if random.random() < 0.05:
                x_addition = 0.5 if self.vector_to(self.game.player)[0] > 0 else -0.5
                y_addition = -0.5 if self.vector_to(self.game.player)[1] > 8 else 2

                self.velocity = [random.random() - 0.5 + x_addition, -(random.random() + y_addition)]
                self.flip_reset()
                if self.health <= self.stage_two_health:
                    if random.random() < 0.75 and len([e for e in self.game.extra_entities if e.type == 'hilbert_orb']) < 20:
                        spawn_portal = random.choice([e for e in self.game.extra_entities if e.type == 'hilbert_orb_spawner'])
                        orb_spawn_loc = spawn_portal.rect().center
                        self.game.extra_entities.append(HilbertOrb(self.game, orb_spawn_loc, self.game.entity_info[47]['size'], [random.uniform(-2,2), 0]))
                        spawn_portal.set_action('activating')
                #Jump sparks
                for _ in range(5):
                    angle = random.uniform(0, math.pi)
                    speed = max(abs(self.velocity[1]), 2)

                    self.game.sparks.append(_spark.Spark(
                        (self.rect().centerx, self.rect().bottom), angle, speed, color=(190, 200, 220)))

            elif not self.shoot_countdown and not self.can_shoot and not self.preparing_to_shoot and random.random() < 0.01:
                self.set_preparing_to_shoot()

            elif self.preparing_to_shoot:
                if random.random() < (self.preparing / self.preparing_time):
                    spark_angle = random.uniform(0, 2 * math.pi)
                    spark_location = [self.rect().centerx + 35 * math.cos(spark_angle), self.rect().centery + 35 * math.sin(spark_angle)]
                    self.game.sparks.append(_spark.Spark(spark_location, spark_angle, 2, color = (255, 0, 255)))
                self.preparing += 1

                if self.preparing > self.preparing_time:
                    self.begin_shooting()

            elif not self.shoot_countdown and self.can_shoot:
                self.shoot_count += 1
                speed = random.uniform(1, 1.5)
                self.circular_attack(40, self.rect().center, color = (200, 0, 200), color_str = 'purple')
                for angle in np.linspace(-math.pi / 2, math.pi * (3/2), self.shoot_num)[:-1]:
                    orb_velocity = [speed * math.cos(angle), speed * math.sin(angle)]
                    self.game.extra_entities.append(Orb(self.game, self.rect().center, self.game.entity_info[38]['size'], orb_velocity, 'imp', colour = (124, 29, 42)))

                if self.shoot_count > self.shoot_count_max:
                    self.stop_shooting()
                else:
                    self.shoot_countdown = random.randint(30, 40)