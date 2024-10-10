"""
Entities module for Hilbert's Hotel.
Includes all entity behaviour.
"""
import pygame
import sys
import math
import random
import numpy as np
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

        self.terminal_vel = 5
        self.gravity = 0.12
        self.light_size = 0

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip_x = False
        self.set_action('idle')
        self.render_distance = self.game.screen_width / 3

        self.last_movement = [0, 0]

        self.dashing = 0
        self.dash_dist = 60

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type +
                                              '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1]))

        # Only update/render at close distances
        render_dist_to_player = np.linalg.norm(self.vector_to(self.game.player))
        if render_dist_to_player > self.render_distance and not self.is_boss:
            return False

        self.collisions = {'up': False, 'down': False,
                           'left': False, 'right': False}

        # Forced movement plus velocity already there
        self.frame_movement = (
            movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        self.last_movement = movement

        if self.collide_wall_check:
            # Check for collision with physics tiles
            self.pos[1] += self.frame_movement[1]
            entity_rect = self.rect()
            for rect in tilemap.physics_rects_around(self.pos, is_boss=self.is_boss):
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
            for rect in tilemap.physics_rects_around(self.pos, is_boss=self.is_boss):
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
            self.velocity[1] = min(
                self.velocity[1] + self.gravity, self.terminal_vel)

        # Reset velocity if vertically hit tile if affected by gravity:
        if (self.collisions['up'] or self.collisions['down']) and self.gravity_affected:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surface, offset=(0, 0), rotation=0, transparency=255):
        # Only update/render at close distances
        render_dist_to_player = np.linalg.norm(self.vector_to(self.game.player))
        if render_dist_to_player > self.render_distance and not self.is_boss:
            return False

        posx = self.pos[0] - offset[0] + self.anim_offset[0]
        posy = self.pos[1] - offset[1] + self.anim_offset[1]

        image = self.animation.img()
        image.set_alpha(transparency)

        if rotation != 0:
            image = pygame.transform.rotate(image, rotation * 180 / math.pi)
            surface.blit(pygame.transform.flip(
                image, self.flip_x, False), (posx, posy))
        else:
            surface.blit(pygame.transform.flip(image, self.flip_x,
                         False), (math.floor(posx), math.floor(posy)))

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

    def kill(self, intensity=10, cog_count=0, redcog_count=0, bluecog_count=0, purplecog_count=0, heartfragment_count=0, wing_count=0, eye_count=0, chitin_count=0, fairybread_count=0, boxingglove_count=0, credit_count=0):
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

        # Create currencies
        # Need to make sure the currency wont spawn in a physics tile.
        spawn_loc = (self.pos[0] + (self.size[0] / 2) - 3,
                    self.pos[1] + (self.size[1] / 2) - 3)

        for _ in range(cog_count):
            self.game.currency_entities.append(
                Currency(self.game, 'cog', spawn_loc))
        for _ in range(redcog_count):
            self.game.currency_entities.append(
                Currency(self.game, 'redCog', spawn_loc))
        for _ in range(bluecog_count):
            self.game.currency_entities.append(
                Currency(self.game, 'blueCog', spawn_loc))
        for _ in range(purplecog_count):
            self.game.currency_entities.append(
                Currency(self.game, 'purpleCog', spawn_loc))
        for _ in range(heartfragment_count):
            self.game.currency_entities.append(
                Currency(self.game, 'heartFragment', spawn_loc))
        for _ in range(wing_count):
            self.game.currency_entities.append(
                Currency(self.game, 'wing', spawn_loc))
        for _ in range(eye_count):
            self.game.currency_entities.append(
                Currency(self.game, 'eye', spawn_loc))
        for _ in range(chitin_count):
            self.game.currency_entities.append(
                Currency(self.game, 'chitin', spawn_loc))
        for _ in range(fairybread_count):
            self.game.currency_entities.append(
                Currency(self.game, 'fairyBread', spawn_loc))
        for _ in range(boxingglove_count):
            self.game.currency_entities.append(
                Currency(self.game, 'boxingGlove', spawn_loc))
        for _ in range(credit_count):
            self.game.currency_entities.append(
                Currency(self.game, 'credit', spawn_loc))

    def display_darkness_circle(self):
        if self.game.cave_darkness and self.game.transition <= 0:
            self.game.darkness_circle(0, self.light_size, (self.rect(
            ).centerx - self.game.render_scroll[0], self.rect().centery - self.game.render_scroll[1]))

    def wall_rebound(self):
        if self.collisions['left'] or self.collisions['right']:
            self.velocity[0] *= -1
        elif self.collisions['up'] or self.collisions['down']:
            self.velocity[1] *= -1

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
            self.game.sparks.append(_spark.ExpandingArc(pos, radius, start_angle, end_angle, speed, color, color_str=color_str,
                                    can_damage_boss=can_damage_boss, width=5, damage=self.attack_power, type=self.type))

class Bat(PhysicsEntity):
    def __init__(self, game, pos, size, grace_done=False, velocity=[0, 0]):
        super().__init__(game, 'bat', pos, size)

        self.cog_count = random.randint(0, 3)
        self.heartfragment_count = (1 if random.random() < 0.2 else 0)
        self.wing_count = (1 if random.random() < 0.8 else 0)

        self.attack_power = 1
        self.death_intensity = 10

        self.gravity_affected = False
        self.grace = random.randint(90, 210)
        self.grace_done = grace_done
        self.set_action('grace')
        if self.grace_done:
            self.set_action('attacking')
            self.timer = 120
            self.velocity = velocity

        self.is_attacking = False
        self.anim_offset = (-3, -2)
        self.timer = 0
        self.pos[1] += 9
        self.pos[0] += 4
        self.to_player = [0, 0]

    def update(self, tilemap, movement=(0, 0)):
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

                if not self.timer:
                    self.set_action('charging')
                    to_player = self.vector_to(self.game.player)
                    self.to_player = to_player / np.linalg.norm(to_player)
                    self.velocity = [-self.to_player[0]
                                     * 0.15, -self.to_player[1] * 0.15]

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

        # Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count,
                          heartfragment_count=self.heartfragment_count, wing_count=self.wing_count)
                return True

        # Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count,
                          heartfragment_count=self.heartfragment_count, wing_count=self.wing_count)
                self.game.projectiles.remove(projectile)
                return True

        # Check for player collision, not dashing and in attack mode:
        if self.game.player.rect().colliderect(self.rect()):
            if abs(self.game.player.dashing) < 50 and self.action == 'attacking' and not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

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
        self.light_size = 30
        self.gravity_affected = True

        self.intelligence = math.floor(self.game.floors[str(
            self.game.current_level)] / 5) if self.game.current_level == 'normal' else 2
        self.weapon = 'gun' if self.intelligence < 2 else ('staff' if random.random() < (
            0.75 if self.game.current_level in ['spooky', 'space'] else 0.25) else 'gun')

        self.witch = False
        if ((self.weapon == 'staff' and self.game.floors['spooky'] > 1) or self.game.difficulty >= 2) and random.random() < 0.5:
            self.witch = True
        elif self.weapon == 'staff' and self.game.current_level == 'space' and random.random() < 0.75:
            self.witch = True

        self.staff_cooldown = 120
        self.trajectory = [0, 0]
        self.colours = [(196, 44, 54), (120, 31, 44)]

        if self.game.difficulty >= 2 and self.game.current_level in ['normal', 'space']:
            self.difficulty_level = random.randint(0, self.game.difficulty)
            if self.difficulty_level == 2:
                self.type = 'gunguyOrange'
                self.colours = [(255, 106, 0), (198, 61, 1)]
            elif self.difficulty_level == 3:
                self.type = 'gunguyBlue'
                self.colours = [(0, 132, 188), (0, 88, 188)]
            elif self.difficulty_level == 4:
                self.type = 'gunguyPurple'
                self.colours = [(127, 29, 116), (99, 22, 90)]

        self.cog_count = random.randint(2, 4)
        self.redcog_count = random.randint(1, 3) if (
            self.type == 'gunguyOrange') else 0
        self.bluecog_count = random.randint(1, 3) if (
            self.type == 'gunguyBlue') else 0
        self.purplecog_count = random.randint(1, 3) if (
            self.type == 'gunguyPurple') else 0
        self.heartfragment_count = 1 if self.weapon == 'staff' else (
            1 if random.random() < 0.1 else 0)
        self.wing_count = random.randint(0, 3) if self.witch else 0
        self.eye_count = 0

        self.label = self.type + \
            ('Witch' if self.witch else ('Staff' if self.weapon == 'staff' else ''))

        if random.random() < 0.5:
            self.flip_x = True

        self.grace = random.randint(60, 120)
        self.grace_done = False
        self.set_action('grace')

    def update(self, tilemap, movement=(0, 0)):
        # Only update/render at close distances
        render_dist_to_player = np.linalg.norm(self.vector_to(self.game.player))
        if render_dist_to_player > self.render_distance:
            return False

        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
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
                    bullet_offset = [
                        4, -4] if self.weapon == 'staff' else [5, 0]
                    bullet_velocity = [-self.bullet_speed,
                                      0] if self.flip_x else [self.bullet_speed, 0]

                    # Vector to player if staff
                    if self.weapon == 'staff':
                        to_player = (self.game.player.pos[0] - self.pos[0] + (
                            bullet_offset[0] if self.flip_x else -bullet_offset[0]), self.game.player.pos[1] - self.pos[1])
                        bullet_velocity = to_player / \
                            np.linalg.norm(to_player) * 1.5
                        self.staff_cooldown = 0

                    # Create bullet/bat/meteor
                    if self.witch and self.game.current_level == 'space':
                        # Find empty space near/on player and summon meteor
                        found_spot = False
                        check_spot = [0, 0]
                        player_pos_tile = (
                            self.game.player.pos[0] // self.game.tilemap.tilesize, self.game.player.pos[1] // self.game.tilemap.tilesize)

                        while not found_spot:
                            check_spot[0], check_spot[1] = int(player_pos_tile[0] + random.choice(
                                range(-3, 4))), int(player_pos_tile[1] + random.choice(range(-2, 3)))
                            loc_str = str(check_spot[0]) + \
                                ';' + str(check_spot[1])
                            if loc_str not in self.game.tilemap.tilemap:
                                found_spot = True
                        self.game.extra_entities.append(Meteor(
                            self.game, (check_spot[0] * self.game.tilemap.tilesize, check_spot[1] * self.game.tilemap.tilesize), (16, 16)))

                    elif self.witch and random.random() < 0.25:
                        batpos = (self.pos[0] - self.pos[0] % self.game.tilemap.tilesize,
                                  self.pos[1] - self.pos[1] % self.game.tilemap.tilesize - 5)
                        self.game.enemies.append(Bat(
                            self.game, batpos, self.game.entity_info[4]['size'], grace_done=True, velocity=bullet_velocity))
                    else:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append(Bullet(self.game, [self.rect(
                        ).centerx - (bullet_offset[0] if self.flip_x else -bullet_offset[0]), self.rect().centery + bullet_offset[1]], bullet_velocity, self.label))
                        for _ in range(4):
                            self.game.sparks.append(_spark.Spark(self.game.projectiles[-1].pos, random.random(
                            ) - 0.5 + (math.pi if self.flip_x else 0), 2 + random.random()))

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
                    movement = (
                        movement[0] - 0.5 if self.flip_x else 0.5, movement[1])

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
                    self.flip_x = True if self.velocity[0] < 0 else False
                    self.set_action('run')

                # only activate flying mode if not surrounded by tiles
                elif self.witch and random.random() < 0.2 and up_empty:
                    self.gravity_affected = False
                    self.flying = random.randint(30, 90)
                    self.velocity = [
                        random.uniform(-left_empty, right_empty), random.uniform(-up_empty, down_empty)]
                    self.flip_x = True if self.velocity[0] < 0 else False
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
                        if abs(disty) < self.attack_dist_y and not self.game.dead:
                            # X axis condition
                            if (self.flip_x and distx < 0) or (not self.flip_x and distx > 0):
                                self.shoot_countdown = 60
                                self.walking = 0

                    elif self.weapon == 'staff' and self.game.current_level == 'space':
                        distto_player = np.linalg.norm(
                            self.vector_to(self.game.player))

                        if distto_player < self.game.screen_width / 8:
                            self.shoot_countdown = 60
                            self.walking = 0

                    elif self.weapon == 'staff':

                        x1, y1 = self.pos[0], self.pos[1]
                        x2, y2 = self.game.player.pos[0], self.game.player.pos[1]

                        x_dist = x2 - x1
                        y_dist = y2 - y1
                        clear = True
                        self.staff_cooldown = 120
                        for n in range(10):
                            x = int((x1 + (n/10) * x_dist) // 16)
                            y = int((y1 + (n/10) * y_dist) // 16)
                            loc = str(x) + ';' + str(y)
                            if loc in self.game.tilemap.tilemap:
                                clear = False

                        if clear:
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
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()) and (self.game.power_level >= self.difficulty_level):
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count, redcog_count=self.redcog_count, bluecog_count=self.bluecog_count,
                          purplecog_count=self.purplecog_count, heartfragment_count=self.heartfragment_count, eye_count=self.eye_count)
                return True

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)

        self.display_darkness_circle()

        if self.action != 'grace':
            y_offset = (4 if self.weapon == 'staff' else 0) + \
                (3 if (self.weapon == 'staff' and self.shoot_countdown) else 0)

            if self.flip_x:
                xpos = self.rect().centerx - 2 - \
                    self.game.assets['weapons/' +
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
            self.set_action('active')
            self.light_size = 40

    def update(self, game):
        self.animation.update()
        # Changing state/action

        if self.action == 'idle' and (len(self.game.enemies) + len(self.game.bosses)) == 0:
            self.set_action('opening')

        if self.action == 'opening':
            self.light_size += 0.5
            if self.animation.done:
                self.set_action('active')

        # Decals
        if self.action in ['opening', 'active']:
            if random.random() < (0.1 + (0.1 if self.action == 'active' else 0)):
                angle = (random.random()) * 2 * math.pi
                speed = random.random() * (3 if self.action == 'active' else 2)
                self.game.sparks.append(_spark.Spark(self.rect(
                ).center, angle, speed, color=random.choice(self.colours[self.destination])))

        # Collision and level change
        player_rect = self.game.player.rect()
        if self.rect().colliderect(player_rect) and self.action == 'active' and self.game.transition == 0:
            if not self.game.infinite_mode_active or self.game.interraction_frame_z:
                if self.destination == 'infinite':
                    self.game.infinite_mode_active = True
                else:
                    self.game.infinite_mode_active = False
                self.game.transition_to_level(self.destination)

                self.set_action('closing')

            else:
                xpos = 2 * (self.rect().centerx - self.game.render_scroll[0])
                ypos = 2 * (self.rect().centery -
                            self.game.render_scroll[1]) - 30
                self.game.draw_text('(z)', (xpos, ypos), self.game.text_font,
                                    (255, 255, 255), (0, 0), mode='center', scale=0.75)

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)

        self.display_darkness_circle()

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0

        self.total_jumps = 1
        self.jumps = self.total_jumps

        self.total_dashes = 1
        self.dashes = self.total_dashes

        self.wall_slide = False
        self.last_collided_wall = False

        self.spark_timer = 0
        self.spark_timer_max = 60
        self.gravity_affected = True
        self.nearest_enemy = False
        self.damage_cooldown = 0
        self.light_size = 90
        self.anim_offset = (-3, -6)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.light_size = 90 + \
            self.game.wallet['eyes'] if 90 + \
            self.game.wallet['eyes'] < 250 else 500
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
                    angle = (random.random() - 0.5) * math.pi + \
                        (math.pi if self.collisions['right'] else 0)
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
            self.velocity[1] = self.downwards * 8 / \
                (math.sqrt(2) if self.sideways else 1)
            self.velocity[0] = self.sideways * 8 / \
                (math.sqrt(2) if self.downwards else 1)

            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
                self.velocity[1] *= 0.1

            if self.game.transition < 1:
                p_velocity = [abs(self.dashing) /
                              self.dashing * random.random() * 3, 0]
                self.game.particles.append(_particle.Particle(self.game, 'particle' + str(self.game.power_level), self.rect(
                ).center, vel=[movement[0] + random.random(), movement[1] + random.random()], frame=random.randint(0, 7)))

            # Breaking cracked tiles:
            if any(self.collisions.values()) and self.game.wallet['hammers'] > 0:
                if self.last_collided_wall['type'] == 'cracked':

                    # Find correct tunnel:
                    for tunnel_name in self.game.tunnels_broken.keys():
                        if any(loc == self.last_collided_wall['pos'] for loc in self.game.tunnel_positions[tunnel_name]):

                            # Actually break all the tiles and save tunnel as broken:
                            for loc in self.game.tunnel_positions[tunnel_name]:
                                del self.game.tilemap.tilemap[str(
                                    loc[0]) + ';' + str(loc[1])]
                                self.game.sparks.append(_spark.Spark(
                                    (loc[0] * self.game.tilemap.tilesize, loc[1] * self.game.tilemap.tilesize), random.random() * math.pi * 2, random.random() * 5))

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

    def render(self, surface, offset=(0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))

        if abs(self.dashing) <= 50 and self.game.transition < 1:
            super().render(surface, offset=offset)

        self.display_darkness_circle()

    def jump(self):
        if self.wall_slide:
            self.velocity[1] = -2.3
            self.air_time = 5
            self.jumps = max(0, self.jumps - 1)

            self.velocity[0] = -1.5 + 3*self.flip_x
            for _ in range(5):
                angle = (random.random() + 1 + self.flip_x) * (math.pi / 4)
                speed = random.random() * (2)

                self.game.sparks.append(_spark.Spark(
                    (self.rect().centerx, self.rect().bottom), angle, speed, color=(190, 200, 220)))
            return True

        elif self.jumps > 0 and abs(self.dashing) < 50:
            self.jumps -= 1
            self.velocity[1] = min(self.velocity[1], -3)
            self.air_time = 5
            for _ in range(5):
                angle = (random.random()) * math.pi
                speed = random.random() * (2)
                self.game.sparks.append(_spark.Spark(
                    (self.rect().centerx, self.rect().bottom), angle, speed, color=(190, 200, 220)))
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
                self.game.dead += 1
                self.game.death_count += 1

                name_vowel = True if self.game.enemy_names[type][0].lower() in [
                    'a', 'e', 'i', 'o', 'u'] else False
                random_verb = random.choice(self.game.death_verbs)
                self.game.death_message = 'You were ' + random_verb + ' by a' + \
                    ('n ' if name_vowel else ' ') + self.game.enemy_names[type]
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

class Currency(PhysicsEntity):
    def __init__(self, game, currency_type, pos, size=(6, 6), value=1):
        super().__init__(game, currency_type, pos, size)

        self.velocity = [2 * (random.random()-0.5), random.random() - 2]
        self.value = value
        self.currency_type = currency_type
        self.size = list(size)
        self.gravity_affected = True
        self.light_size = 5
        self.old_enough = 30

        self.anim_offset = (-1, random.choice([-1, -2]))
        self.animation.img_duration += (
            self.animation.img_duration*random.random())

    def update(self, tilemap, movement=(0, 0)):
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
                self.game.wallet_temp[str(
                    self.currency_type) + 's'] += self.value
            self.game.check_encounter(self.currency_type + 's')
            self.game.sfx['coin'].play()
            return True

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)
        self.display_darkness_circle()

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

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)
        self.display_darkness_circle()

class Bullet():
    def __init__(self, game, pos, speed, origin, type='projectile'):
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
        if self.game.cave_darkness and self.game.transition <= 0:
            self.game.darkness_circle(0, self.light_size, (int(
                self.pos[0]) - self.game.render_scroll[0], int(self.pos[1]) - self.game.render_scroll[1]))
        self.game.display_outline.blit(self.img, (self.pos[0] - self.img.get_width(
        ) / 2 - self.game.render_scroll[0], self.pos[1] - self.img.get_height() / 2 - self.game.render_scroll[1]))

        if not self.game.paused:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]

        # Check to destroy
        if self.game.tilemap.solid_check(self.pos):
            if self.type == 'projectile':
                velocity_angle = math.atan(self.speed[1] / self.speed[0])
                for _ in range(4):
                    self.game.sparks.append(
                        _spark.Spark(self.pos, random.random() - 0.5 + velocity_angle, 2 + random.random()))
            return True

        # Check for player collision:
        if self.game.player.rect().collidepoint(self.pos) and abs(self.game.player.dashing) < 50:
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.origin)
                return True

class RolyPoly(PhysicsEntity):
    def __init__(self, game, pos, size, initialFall=False):
        super().__init__(game, 'rolypoly', pos, size)

        self.attack_power = 1
        self.cog_count = random.randint(0, 3) if len(
            game.bosses) == 0 else random.randint(0, 1)
        self.eye_count = random.randint(1, 5) if len(
            game.bosses) == 0 else random.randint(0, 1)

        self.death_intensity = 10

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
        self.pos[1] += 5
        self.grace = random.randint(120, 180)
        self.animation.img_duration += (
            self.animation.img_duration*random.random())

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

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
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity=self.death_intensity,
                          cog_count=self.cog_count, eye_count=self.eye_count)
                return True

        # Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity=self.death_intensity,
                          cog_count=self.cog_count, eye_count=self.eye_count)
                self.game.projectiles.remove(projectile)
                return True

        # Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'idle':
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

    def render(self, surface, offset=(0, 0)):
        # pygame.draw.rect(self.game.hud_display, (255,0,0), (2*(self.rect().x - self.game.render_scroll[0] - self.anim_offset[0]), 2*(self.rect().y - self.game.render_scroll[1] - self.anim_offset[1]), self.size[0]*2, self.size[1]*2))

        super().render(surface, offset=offset)

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
                self.game.sparks.append(_spark.Spark(self.rect(
                ).center, angle, speed, color=random.choice([(58, 6, 82), (111, 28, 117)])))

class HeartAltar(PhysicsEntity):
    def __init__(self, game, pos, size, action='active'):
        super().__init__(game, 'heartAltar', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.collide_wall = False
        self.set_action(action)

        self.anim_offset = (0, 0)
        self.animation.img_duration += (
            self.animation.img_duration*random.random())

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) > 50 and self.action == 'active':
            self.game.check_encounter('heartAltars')

            if self.game.health < self.game.max_health:
                self.game.health += 1
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
        self.animation.img_duration += (
            self.animation.img_duration*random.random())

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
        super().update(tilemap, movement=movement)

        self.display_darkness_circle()
        if random.random() < 0.05:
            self.game.sparks.append(_spark.Spark([self.rect().x + (4 if self.flip_x else 12), self.pos[1]], random.random(
            ) * math.pi + math.pi, random.random() + 1, color=random.choice([(229, 0, 0), (229, 82, 13)])))

class Spider(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spider', pos, size)

        self.cog_count = random.randint(0, 3)
        self.heartfragment_count = (1 if random.random() < 0.2 else 0)
        self.chitin_count = random.randint(0, 3)
        self.attack_power = 1
        self.death_intensity = 10

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

    def update(self, tilemap, movement=(0, 0)):
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
                    self.to_player = to_player / np.linalg.norm(to_player)
                    self.velocity = [self.to_player[0]
                                     * 0.2, self.to_player[1] * 0.2]

                    self.velocity[0] += random.random() - 0.5
                    self.velocity[1] += random.random() - 0.5

                    self.facing[0] = self.velocity[0]
                    self.facing[1] = self.velocity[1]

                    self.timer = random.randint(30, 90)

            elif self.action == 'run':
                self.timer = max(self.timer - 1, 0)

                if self.timer == 0:
                    self.velocity = [0, 0]
                    self.timer = random.randint(10, 30)
                    self.set_action('idle')

        # Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count,
                          heartfragment_count=self.heartfragment_count, chitin_count=self.chitin_count)
                return True

        # Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count,
                          heartfragment_count=self.heartfragment_count, chitin_count=self.chitin_count)
                self.game.projectiles.remove(projectile)
                return True

        # Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'grace':
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

    def render(self, surface, offset=(0, 0)):
        # pygame.draw.rect(self.game.display_outline, (255,0,0), (1*(self.pos[0] - self.game.render_scroll[0]), 1*(self.pos[1] - self.game.render_scroll[1]), self.size[0], self.size[1] ))
        angle = 0
        angle = math.atan2(-self.facing[1], self.facing[0]) - math.pi / 2

        super().render(surface, offset=offset, rotation=angle)

class RubiksCube(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'rubiksCube', pos, size)

        self.cog_count = random.randint(0, 3)
        self.redcog_count = 0
        self.bluecog_count = 0
        self.heartfragment_count = (1 if random.random() < 0.2 else 0)
        self.attack_power = 1
        self.death_intensity = 10

        self.grace = random.randint(90, 210)
        self.grace_done = False
        self.gravity_affected = False
        self.anim_offset = (0, 0)
        self.can_move_vectors = []
        self.speed = 1
        self.max_speed = 3
        self.states = ['white', 'yellow', 'blue', 'green', 'red', 'orange']

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if not self.grace_done:
            self.grace = max(0, self.grace - 1)
            if self.grace == 0:
                self.set_action(random.choice(self.states))
                self.timer = random.randint(120, 300)
                self.grace_done = True
                if self.action == 'red':
                    self.redcog_count = random.randint(1, 5)
                elif self.action == 'blue':
                    self.bluecog_count = random.randint(1, 5)

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

                self.redcog_count, self.bluecog_count = 0, 0
                if self.action == 'red':
                    self.redcog_count = random.randint(1, 5)
                elif self.action == 'blue':
                    self.bluecog_count = random.randint(1, 5)

        # Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count, redcog_count=self.redcog_count,
                          bluecog_count=self.bluecog_count, heartfragment_count=self.heartfragment_count)
                return True

        # Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count, redcog_count=self.redcog_count,
                          bluecog_count=self.bluecog_count, heartfragment_count=self.heartfragment_count)
                self.game.projectiles.remove(projectile)
                return True

        # Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'idle':
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

class Kangaroo(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'kangaroo', pos, size)

        self.cog_count = random.randint(0, 3)
        self.heartfragment_count = (1 if random.random() < 0.3 else 0)
        self.fairybread_count = random.randint(0, 4)
        self.boxingglove_count = random.randint(0, 3)
        self.attack_power = 1
        self.death_intensity = 10

        self.grace = random.randint(90, 210)
        self.grace_done = False
        self.gravity_affected = True
        self.set_action('grace')
        self.anim_offset = (0, 0)
        self.timer = 0
        self.time_since_bounce = 0
        self.flip_x = True if random.random() < 0.5 else False

    def update(self, tilemap, movement=(0, 0)):
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
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count, heartfragment_count=self.heartfragment_count,
                          fairybread_count=self.fairybread_count, boxingglove_count=self.boxingglove_count)
                return True

        # Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count, heartfragment_count=self.heartfragment_count,
                          fairybread_count=self.fairybread_count, boxingglove_count=self.boxingglove_count)
                self.game.projectiles.remove(projectile)
                return True

        # Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'grace':
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

class Echidna(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'echidna', pos, size)

        self.cog_count = random.randint(0, 3)
        self.heartfragment_count = (1 if random.random() < 0.3 else 0)
        self.fairybread_count = random.randint(0, 4)
        self.attack_power = 1
        self.death_intensity = 10

        self.grace = random.randint(90, 210)
        self.grace_done = False
        self.gravity_affected = True
        self.set_action('grace')
        self.anim_offset = (0, 0)
        self.timer = 0
        self.flip_x = True if random.random() < 0.5 else False

    def update(self, tilemap, movement=(0, 0)):
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

                elif random.random() < 0.005:
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

                elif random.random() < 0.005:
                    self.set_action('charging')
                    self.velocity = [0, 0]

            elif self.action == 'charging':
                # When animation finishes, shoot spines in random directions and go to idle.
                if self.animation.done:

                    for _ in range(10):
                        angle = random.random() * math.pi + math.pi
                        spine_velocity = [2*math.cos(angle), 2*math.sin(angle)]
                        self.game.projectiles.append(Bullet(self.game, [self.rect(
                        ).centerx, self.rect().centery], spine_velocity, 'echidna', type='spine'))
                    self.game.projectiles.append(Bullet(self.game, [self.rect(
                    ).centerx, self.rect().centery], [2, 0], 'echidna', type='spine'))
                    self.game.projectiles.append(Bullet(self.game, [self.rect(
                    ).centerx, self.rect().centery], [-2, 0], 'echidna', type='spine'))
                    self.set_action('idle')
                    self.timer = random.randint(120, 180)

        # Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count,
                          heartfragment_count=self.heartfragment_count, fairybread_count=self.fairybread_count)
                return True

        # Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count,
                          heartfragment_count=self.heartfragment_count, fairybread_count=self.fairybread_count)
                self.game.projectiles.remove(projectile)
                return True

        # Check for player collision:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action != 'grace':
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

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
            if self.animation.done:
                self.set_action('kaboom')

        elif self.action == 'kaboom':
            # Check for player collision:
            if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.animation.frame > 10:
                if not self.game.dead:
                    self.game.player.damage(self.attack_power, self.type)

            if self.animation.done:
                return True

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset, rotation=self.angle)
        self.display_darkness_circle()

class AlienShip(PhysicsEntity):
    def __init__(self, game, pos, size, grace_done=False, velocity=[0, 0]):
        super().__init__(game, 'alienship', pos, size)

        self.cog_count = random.randint(0, 3)
        self.heartfragment_count = (1 if random.random() < 0.2 else 0)
        self.purplecog_count = (1 if random.random() < 0.2 else 0)

        self.attack_power = 1
        self.death_intensity = 10

        self.gravity_affected = False
        self.grace = random.randint(90, 210)
        self.grace_done = grace_done
        self.set_action('idle')
        if self.grace_done:
            self.set_action('flying')
            self.velocity = velocity

        self.anim_offset = (0, -1)
        self.pos[1] += 9
        self.pos[0] += 4

    def update(self, tilemap, movement=(0, 0)):
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

            if any(self.collisions.values()) and random.random() < 0.1:
                to_player = self.vector_to(self.game.player)
                norm = np.linalg.norm(to_player) * random.uniform(1.2, 1.5)

                if not (tilemap.solid_check((self.rect().centerx + 8, self.rect().centery)) and tilemap.solid_check((self.rect().centerx - 8, self.rect().centery))):
                    self.velocity[0] = to_player[0] / norm
                if not (tilemap.solid_check((self.rect().centerx, self.rect().centery + 8)) and tilemap.solid_check((self.rect().centerx, self.rect().centery - 8))):
                    self.velocity[1] = to_player[1] / norm

        # Death Condition
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count,
                          heartfragment_count=self.heartfragment_count, purplecog_count=self.purplecog_count)
                return True

        # Also dies if hit by bullet:
        for projectile in self.game.projectiles:
            if self.rect().collidepoint(projectile.pos) and projectile.type == 'projectile':
                self.kill(intensity=self.death_intensity, cog_count=self.cog_count,
                          heartfragment_count=self.heartfragment_count, purplecog_count=self.purplecog_count)
                self.game.projectiles.remove(projectile)
                return True

        # Check for player collision, not dashing and in attack mode:
        if self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50 and self.action == 'flying':
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

class CreepyEyes(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'creepyeyes', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.main_pos = list(pos)

        self.anim_offset = (0, 0)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        to_player = self.vector_to(self.game.player)
        self.to_player_norm = to_player / np.linalg.norm(to_player)

        self.pos[0] = self.main_pos[0] + \
            round(self.to_player_norm[0] if abs(
                self.to_player_norm[0]) > 0.38 else 0)
        self.pos[1] = self.main_pos[1] + \
            round(self.to_player_norm[1] if abs(
                self.to_player_norm[1]) > 0.38 else 0)

class MeteorBait(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'meteorbait', pos, size)

        self.gravity_affected = False
        self.collide_wall_check = False
        self.pos = list(pos)
        self.anim_offset = (0, 0)

        self.cooldown = 0

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.cooldown:
            self.cooldown = max(self.cooldown - 1, 0)

        if self.rect().colliderect(self.game.player.rect()) and abs(self.game.player.dashing) >= 50 and not self.cooldown:
            self.cooldown = 30
            self.summon_meteor(self.rect().center, [
                              [x, y] for x in range(-2, 3) for y in range(-15, 2)], 7)

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
        self.anim_offset = (0, 0)
        self.timer = random.randint(400, 800)
        self.light_size = 0

    def update(self, tilemap, movement=(0, 0)):
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

            self.display_darkness_circle()

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

            self.display_darkness_circle()

class Boss(PhysicsEntity):
    def __init__(self, game, type, pos, size):
        super().__init__(game, type, pos, size)

        self.is_boss = True
        self.glowworm_follow = True
        self.difficulty = round(
            self.game.floors[self.game.current_level] / self.game.boss_frequency) - 1
        if self.game.current_level == 'infinite':
            self.difficulty = round(
                self.game.floors['infinite'] / self.game.boss_frequency) - 1
        self.death_intensity = 50

        self.currency_drops = {
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

        self.cog_count = random.randint(
            25 + 25 * self.difficulty, 50 + 25 * self.difficulty)
        self.heartfragment_count = random.randint(
            5 + 10 * self.difficulty, 10 + 10 * self.difficulty)

        self.damage_cooldown = 0
        self.timer = 0
        self.anim_offset = (0, 0)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.damage_cooldown:
            self.damage_cooldown = max(self.damage_cooldown - 1, 0)
        if self.check_damage_taken(invincible_states=self.invincible_states, passive_states=self.passive_states):
            self.set_action('dying')

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
                self.kill(intensity=self.death_intensity)
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
                        enemy.kill(intensity=enemy.death_intensity,
                                   credit_count=1)
                    self.game.enemies = []
                return True

class NormalBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'normalboss', pos, size)

        self.currency_drops['heartFragment'] = random.randint(
            0, 5) * self.difficulty
        self.currency_drops['wing'] = random.randint(4, 10) * self.difficulty

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

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        to_player = self.vector_to(self.game.player)
        norm = np.linalg.norm(to_player)

        if self.action == 'idle':
            if norm < 140:
                for boss in self.game.bosses:
                    boss.activate()

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
                    self.game.enemies.append(Bat(self.game, (batpos[0], batpos[1] - 4), self.game.entity_info[4]['size'], grace_done=True, velocity=[
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

        self.currency_drops['heartFragment'] = random.randint(
            0, 5) * self.difficulty
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
                self.wall_side[0], self.wall_side[1] = - \
                    self.wall_side[0], self.wall_side[1]

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

        self.currency_drops['heartFragment'] = random.randint(
            0, 5) * self.difficulty
        self.currency_drops['purpleCog'] = random.randint(
            0, 2) * self.difficulty

        self.gravity_affected = True
        self.collide_wall_check = True

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))

        self.health = 2 + 2 * self.difficulty
        self.max_health = self.health

        self.shoot_count_max = self.difficulty
        self.shoot_count = self.shoot_count_max
        self.speed = self.difficulty / 2
        self.light_size = 25

        self.invincible_states = ['idle', 'activating',
                                 'attacking', 'flying', 'dying']
        self.passive_states = ['idle', 'dying']

        self.anim_offset = (-3, -8)

    def activate(self):
        self.set_action('activating')
        self.velocity[0] = random.uniform(-0.75, 0.75)
        self.velocity[1] = -random.uniform(2, 3)

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

                for _ in range(3):
                    self.game.sparks.append(_spark.Spark(self.rect().midbottom, random.uniform(
                        0, math.pi), random.uniform(1.5, 2), color=random.choice([(0, 255, 0), (200, 0, 200)])))

        elif self.action == 'activating':
            if any(self.collisions.values()):
                self.set_action('flying')
                self.gravity_affected = False

                self.velocity[0] = self.speed * to_player[0] / norm
                self.velocity[1] = self.speed * to_player[1] / norm

            elif random.random() < 0.03:
                self.velocity[0] = random.uniform(-0.75, 0.75)
                self.velocity[1] = -random.uniform(2, 3)

                for _ in range(3):
                    self.game.sparks.append(_spark.Spark(self.rect().midbottom, random.uniform(
                        0, math.pi), random.uniform(1.5, 2), color=random.choice([(0, 255, 0), (200, 0, 200)])))

        elif self.action == 'flying':
            self.display_darkness_circle()
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
            self.display_darkness_circle()
            self.timer += 1

            self.wall_rebound()

            if np.linalg.norm(self.velocity) > 0.1:
                self.velocity[0] *= 0.98
                self.velocity[1] *= 0.98

            if self.timer % 45 == 0 and self.shoot_count < self.shoot_count_max:
                self.shoot_count += 1

                self.game.sfx['shoot'].play()
                angleto_player = math.atan(
                    to_player[1] / (to_player[0] if to_player[0] != 0 else 0.01))
                bullet_speed = 2 * math.atan(self.difficulty / 2)

                for angle in np.linspace(angleto_player, angleto_player + math.pi * 2, 5 + 3 * self.difficulty):
                    bullet_velocity = (
                        bullet_speed * math.cos(angle), bullet_speed * math.sin(angle))

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

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.spawn_count and not self.spawning:
            to_player = (self.game.player.rect().centerx - self.rect().centerx,
                        self.game.player.rect().centery - self.rect().centery)
            norm = np.linalg.norm(to_player)

            if norm < 50:
                self.spawning = True

        elif self.spawn_count and self.spawning and random.random() < 0.05:
            self.game.bosses.append(SpookyBoss(self.game, [
                                    self.pos[0] + random.randint(-8, 40), self.pos[1] + random.randint(16, 32)], self.game.entity_info[25]['size']))
            self.spawn_count -= 1

class FlyGhost(PhysicsEntity):
    def __init__(self, game, pos, size, difficulty):
        super().__init__(game, 'flyghost', pos, size)

        self.gravity_affected = False
        self.collide_wall = False
        self.pos = list(pos)
        self.anim_offset = (-2, -2)
        self.is_boss = True
        self.difficulty = difficulty

        self.credit_count = 1 if random.random() < 0.05 else 0

        to_player = (self.game.player.rect().centerx - self.rect().centerx,
                    self.game.player.rect().centery - self.rect().centery)
        norm = np.linalg.norm(to_player)

        self.velocity = [random.uniform(0.9, 1.1 + 0.3 * self.difficulty) * to_player[0] /
                         norm, random.uniform(0.9, 1.1 + 0.3 * self.difficulty) * to_player[1] / norm]
        self.angle = math.atan2(-self.velocity[1], self.velocity[0])

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        to_player = (self.game.player.rect().centerx - self.rect().centerx,
                    self.game.player.rect().centery - self.rect().centery)
        norm = np.linalg.norm(to_player)

        if norm > self.game.screen_width / 2.7 or len(self.game.bosses) == 0:
            return True

        if random.random() < 0.1:
            self.game.sparks.append(_spark.Spark(
                self.rect().center, -self.angle + math.pi + random.uniform(-0.3, 0.3), 1.5))

        # Death Condition
        elif abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.kill(credit_count=self.credit_count)
                return True

        # Check for player collision
        elif self.game.player.rect().colliderect(self.rect()) and abs(self.game.player.dashing) < 50:
            if not self.game.dead:
                self.game.player.damage(self.attack_power, self.type)

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset, rotation=self.angle)

class SpookyBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'spookyboss', pos, size)

        self.currency_drops['chitin'] = random.randint(2, 5) * self.difficulty

        self.gravity_affected = False
        self.collide_wall = False

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))

        self.health = 2 + 2 * self.difficulty
        self.max_health = self.health

        self.transparency = 0
        self.transparency_inc = 3
        self.tele_coords = [0, 0]
        self.timer = 0

        self.player_tele_dist = 100
        self.velocity[0] = random.uniform(-0.5, 0.5)
        self.velocity[1] = random.uniform(-0.5, 0)

        self.invincible_states = ['idle', 'teleporting', 'dying']
        self.passive_states = ['idle', 'teleporting', 'dying']

        self.anim_offset = (0, 0)

    def update(self, tilemap, movement=(0, 0)):
        if super().update(tilemap, movement=movement):
            return True

        if self.action == 'idle':
            self.transparency = min(self.transparency + 2, 255)
            if self.transparency >= 255:
                self.set_action('flying')

        elif self.action == 'flying':
            to_player = (self.game.player.rect().centerx - self.rect().centerx,
                        self.game.player.rect().centery - self.rect().centery)
            norm = np.linalg.norm(to_player)

            # Teleport
            if random.random() < 0.005 or norm > 250:
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

        # Create attack ghost
        if random.random() < 0.01:
            spawn_angle = random.random() * 2 * math.pi
            spawn_dist = self.game.screen_width / 2.8

            spawn_pos = [self.game.player.pos[0] + (math.sin(
                spawn_angle) * spawn_dist), self.game.player.pos[1] + (math.cos(spawn_angle) * spawn_dist)]

            self.game.extra_entities.append(FlyGhost(
                self.game, spawn_pos, self.game.entity_info[32]['size'], self.difficulty))

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset, transparency=abs(self.transparency))

class RubiksBoss(Boss):
    def __init__(self, game, pos, size):
        super().__init__(game, 'rubiksboss', pos, size)

        self.currency_drops['redCog'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['blueCog'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['purpleCog'] = random.randint(
            0, 1) * self.difficulty

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

        self.currency_drops['fairyBread'] = random.randint(
            2, 5) * self.difficulty
        self.currency_drops['chitin'] = random.randint(2, 5) * self.difficulty
        self.currency_drops['purpleCog'] = random.randint(
            0, 1) * self.difficulty

        self.attack_radius = int(100 * math.atan(self.difficulty / 5))
        self.active_min_time = max(60, 100 - self.difficulty * 20)
        self.active_max_time = max(70, 120 - self.difficulty * 20)

        self.health = 2 + 2 * self.difficulty
        self.max_health = self.health

        self.gravity_affected = True
        self.timer = 0

        self.anim_offset = (-8, -12)

        self.invincible_states = ['idle', 'dying']
        self.passive_states = ['idle', 'dying']

    def activate(self):
        self.set_action('active')
        self.timer = random.randint(90, 120)

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

                self.velocity[0] = -(random.random() +
                                     3.5) if self.flip_x else (random.random() + 3.5)
                self.velocity[1] = - \
                    (random.random() * 4 + 7 if player_above else 4)
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

                    self.timer = random.randint(
                        self.active_min_time, self.active_max_time)
                    self.set_action('active')
                    self.circular_attack(self.attack_radius,
                                        pos=self.rect().midbottom)

                    # Sometimes spawn other lil guys:
                    spawn_pos = [self.rect().centerx - 8, self.rect().y]

                    if random.random() < 0.134:
                        self.game.enemies.append(
                            Kangaroo(self.game, spawn_pos, self.game.entity_info[19]['size']))

                    elif random.random() < 0.134:
                        self.game.enemies.append(
                            Echidna(self.game, spawn_pos, self.game.entity_info[20]['size']))
