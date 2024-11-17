"""
Main game for Hilbert's Hotel.
Manages game loop, updating all entities and display.
"""
import random
import math
import numpy as np
import os
import json
import cProfile
import sys
import pygame
import pygame.freetype
import scripts.entities as _entities
import scripts.characters as _characters
import scripts.utilities as _utilities
import scripts.tilemap as _tilemap
import scripts.clouds as _clouds
import scripts.particle as _particle
import scripts.spark as _spark



class Game:
    def __init__(self, fullscreen = True, screen_size = (1080, 720)):

        # Pygame specific parameters and initialisation
        pygame.init()
        game_version = '0.8.5'
        pygame.display.set_caption(f'Hilbert\'s Hotel v{game_version}')
        self.text_font = pygame.font.Font('data/font.ttf', 8)
        self.clock = pygame.time.Clock()

        # Define all general game parameters and load in assets
        self.is_fullscreen = fullscreen
        self.screen_width = screen_size[0]
        self.screen_height = screen_size[1]

        _utilities.initialise_main_screen(self)
        _utilities.initialise_game_params(self)
        self.load_game_assets()

        self.player = _entities.Player(self, (0, 0), (8, 12))
        self.tilemap = _tilemap.Tilemap(self, tile_size=16)

    def load_menu(self):
        self.sfx['ambience'].play(-1)

        save_slots = [0, 1, 2]
        save_info = self.get_save_info()
        hover_slot = 1
        deleting = 0

        selected = (86, 31, 126)
        not_selected = (1, 1, 1)

        self.clouds = _clouds.Clouds(self.assets['clouds'], count=30)

        background = pygame.transform.scale(self.assets['menuBackground'], (self.screen_width / 2, self.screen_height / 2))
        foreground = pygame.transform.scale(self.assets['menuForeground'], (self.screen_width / 2, self.screen_height / 2))
        
        while self.in_menu:
            self.display_outline.fill((0, 0, 0, 0))
            self.display_outline.blit(background, (0, 0))
            self.hud_display.fill((0, 0, 0, 0))

            self.clouds.update()
            self.clouds.render(self.display_outline, offset=self.render_scroll)

            self.display_outline.blit(foreground, (0, 0))

            # Displaying menu HUD:
            display_slot = hover_slot % len(save_slots)
            self.draw_text('Hilbert\'s Hotel', (self.screen_width * (1/2), 45), self.text_font, selected, scale = 4, mode='center')
            self.draw_text('Select: [X]', (self.screen_width * (2/4) - 75, self.screen_height - 20), self.text_font, not_selected, scale = 2, mode='center')
            self.draw_text('Delete: [Z]', (self.screen_width * (2/4) + 75, self.screen_height - 20), self.text_font, not_selected, scale = 2, mode='center')
            self.draw_text('Quit Game: [Q]', (self.screen_width * 0.9, self.screen_height - 20), self.text_font, not_selected, scale = 2, mode='center')
            self.draw_text('Fullscreen: [F]', (self.screen_width * 0.1, self.screen_height - 20), self.text_font, not_selected, scale = 2, mode='center')

            for n in range(0, len(save_slots)):
                if self.saved_characters[n]:
                    image = self.saved_characters[n].copy()
                    if n == display_slot and deleting:
                        image.set_alpha(deleting)
                    self.display_outline.blit(image, ((self.screen_width * (2/4) - 160 + 130*n)/2, (self.screen_height - 110)/2))
                else:
                    self.draw_text('No Data', (self.screen_width * (2/4) - 130 + 130*n, self.screen_height - 65), self.text_font,
                                selected if display_slot == n else not_selected, mode='center', scale = 3)
            self.draw_text('<     >', (self.screen_width * (2/4) - 128 + 130*display_slot, self.screen_height - 65), self.text_font,
                            selected, mode='center', scale = 8)
            
            # Delete save if held for 5 secs
            if deleting:
                deleting = max(deleting - 1, 0)
                if deleting == 0:
                    self.delete_save(display_slot)
                    save_info = self.get_save_info()
                #Show that it is being deleted:
                self.draw_text('DELETING', (self.screen_width * (2/4) - 130 + 130*display_slot, self.screen_height - 65), self.text_font,
                                (255,0,0), mode='center', scale = 3)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        hover_slot -= 1
                        if deleting:
                            deleting = 0
                    if event.key == pygame.K_RIGHT:
                        hover_slot += 1
                        if deleting:
                            deleting = 0
                    if event.key == pygame.K_x or event.key == pygame.K_RETURN:
                        save_slot = hover_slot % len(save_slots)
                        self.game_running = True
                        self.run(save_slot)
                    if event.key == pygame.K_z and self.saved_characters[display_slot]:
                        deleting = 255
                    if event.key == pygame.K_f:
                        self.is_fullscreen = not self.is_fullscreen
                        self.toggle_fullscreen()
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_z:
                        deleting = 0

            self.display.blit(self.display_outline, (0, 0))
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            self.screen.blit(pygame.transform.scale(self.hud_display, self.screen.get_size()), (0, 0))

            pygame.display.update()
            self.clock.tick(self.fps)
            self.interraction_frame_int = False

        self.end_game()

    def set_player_colours(self):
        #When not starting a new game, no options to change colour, just alter assets and jump straight in.
        if self.creation_done:
            default_player_colours = {
            'shirt': (74, 94, 132),
            'front Leg': (51, 20, 0),
            'back Leg': (38, 15, 0),
            'tie': (2, 2, 2),
            'belt': (5, 5, 5),
            'skin': (175, 168, 151),
            'eye': (0, 1, 104),
            }

            for clothing_type in default_player_colours.keys():
                _utilities.alter_character_colour(self, default_player_colours[clothing_type], self.player_colours[clothing_type])
            _utilities.alter_character_colour(self, (150, 143, 126), tuple((max(1, c - 25) for c in self.player_colours['skin'])))
            return
        self.dummy_player = _entities.PlayerCustomise(self, (635, 455), (8, 12))
        background = pygame.transform.scale(self.assets['backgroundcustom'], (self.screen_width / 2, self.screen_height / 2))
        self.tilemap.tilemap = {
            f'{x};32': {"type": "normal", "variant": 1, "pos": [x, 32]}
            for x in range(26, 46)
        }
        customising_colours = True
        selected = (255, 255, 255)
        not_selected = (150, 150, 150)
        player_render_scale = 5
        darkness = 0
        reducing_player = False

        height_index = 0
        selection_indices = {
        'shirt': 0,
        'front Leg': 0,
        'back Leg': 0,
        'tie': 0,
        'belt': 0,
        'skin': 0,
        'eye': 0,
        }

        while customising_colours:

            # Background
            self.display.blit(background, (0, 0))
            self.display_outline.fill((0, 0, 0, 0))
            self.hud_display.fill((0, 0, 0, 0))
            self.darkness_surface.fill((0, 0, 0, darkness))

            if not reducing_player:
                self.draw_text('Who are you?', (self.screen_width / 4 + 30, self.screen_height / 2 - 125), self.text_font, (255, 255, 255), scale = 4, mode='center')
                self.draw_text('Confirm: [X]', (self.screen_width / 4 + 30, self.screen_height / 2 + 125), self.text_font, (255, 255, 255), scale = 4, mode='center')

                for n, piece in enumerate(list(selection_indices.keys())):
                    text_col = selected if piece == _utilities.index_to_value(height_index, list(selection_indices.keys())) else not_selected
                    self.draw_text(f'{piece.capitalize()}:', (self.screen_width / 2 + 265, self.screen_height / 2 - 275 + 80*n), self.text_font, text_col, mode='center', scale = 2)

                    for offset, colour in enumerate(range(selection_indices[piece]-2, selection_indices[piece]+3)):
                        circle_size = 20 - 3*abs(offset - 2)
                        pygame.draw.circle(self.hud_display, (255, 255, 255), (self.screen_width / 2 + 115 + offset*75, self.screen_height / 2 - 230 + 80*n), circle_size)
                        pygame.draw.circle(self.hud_display, _utilities.index_to_value(selection_indices[piece] - 2 + offset, self.player_colours_options[piece]), (self.screen_width / 2 + 115 + offset*75, self.screen_height / 2 - 230 + 80*n), circle_size-2)
                
                #Triangle indicators
                tri_point = (self.screen_width / 2 + 465, self.screen_height / 2 - 230 + 80*(height_index % 7))
                pygame.draw.lines(self.hud_display, selected, False, [(tri_point[0], tri_point[1]-10),
                                                                        (tri_point[0]+10, tri_point[1]),
                                                                        (tri_point[0], tri_point[1]+10)], 5)
                tri_point = (self.screen_width / 2 + 65, self.screen_height / 2 - 230 + 80*(height_index % 7))
                pygame.draw.lines(self.hud_display, selected, False, [(tri_point[0], tri_point[1]-10),
                                                                        (tri_point[0]-10, tri_point[1]),
                                                                        (tri_point[0], tri_point[1]+10)], 5)
                self.tilemap.move_tiles_customise()
                self.tilemap.render_colour_screen(self.display_outline, offset=self.render_scroll)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT and not reducing_player:
                        self.sfx['blip'].play()
                        clothing_type = _utilities.index_to_value(height_index, list(selection_indices.keys()))

                        if clothing_type != 'confirm':
                            current_colour = _utilities.index_to_value(selection_indices[clothing_type], self.player_colours_options[clothing_type])
                            new_colour = _utilities.index_to_value(selection_indices[clothing_type] - 1, self.player_colours_options[clothing_type])
                            _utilities.alter_character_colour(self, current_colour, new_colour)
                            self.player_colours[clothing_type] = new_colour

                        selection_indices[_utilities.index_to_value(height_index, list(selection_indices.keys()))] -= 1
                    if event.key == pygame.K_RIGHT and not reducing_player:
                        self.sfx['blip'].play()
                        clothing_type = _utilities.index_to_value(height_index, list(selection_indices.keys()))

                        if clothing_type != 'confirm':
                            current_colour = _utilities.index_to_value(selection_indices[clothing_type], self.player_colours_options[clothing_type])
                            new_colour = _utilities.index_to_value(selection_indices[clothing_type] + 1, self.player_colours_options[clothing_type])
                            _utilities.alter_character_colour(self, current_colour, new_colour)
                            self.player_colours[clothing_type] = new_colour

                        selection_indices[_utilities.index_to_value(height_index, list(selection_indices.keys()))] += 1
                    if event.key == pygame.K_UP and not reducing_player:
                        self.sfx['dashClick'].play()
                        height_index -= 1
                    if event.key == pygame.K_DOWN and not reducing_player:
                        self.sfx['dashClick'].play()
                        height_index += 1
                    if event.key == pygame.K_x or event.key == pygame.K_RETURN:
                        reducing_player = True
                        _utilities.alter_character_colour(self, (150, 143, 126), tuple((max(1, c - 25) for c in self.player_colours['skin'])))
                        self.dummy_player.set_action('idle')

                    if event.key == pygame.K_f:
                        self.is_fullscreen = not self.is_fullscreen
                        self.toggle_fullscreen()
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        self.__init__(fullscreen = self.is_fullscreen, screen_size=(self.screen_width, self.screen_height))
                        self.load_menu()

            if reducing_player:
                player_render_scale = max(player_render_scale - 0.01, 1)
                self.scroll[0] += ((self.dummy_player.rect().centerx + (self.dummy_player.size[0] * min(player_render_scale, 3) / 2)) - self.screen_width / 4 - self.scroll[0]) / 15
                self.scroll[1] += ((self.dummy_player.rect().centery + (self.dummy_player.size[1] * min(player_render_scale, 3) / 2)) - self.screen_height / 4 - self.scroll[1]) / 15
                self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
                darkness =min(darkness + 3, 255)

            if player_render_scale <= 1:
                self.creation_done = True
                customising_colours = False

            self.dummy_player.update(self.tilemap, (0, 0))
            self.display_outline.blit(self.darkness_surface, (0, 0))
            self.dummy_player.render(self.display_outline, offset=self.render_scroll, scale = min(player_render_scale, 3))

            
            self.display.blit(self.display_outline, (0, 0))
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            self.screen.blit(pygame.transform.scale(self.hud_display, self.screen.get_size()), (0, 0))

            pygame.display.update()
            self.clock.tick(self.fps)

    def run(self, save_slot):

        self.save_slot = save_slot
        self.load_game(self.save_slot)

        self.set_player_colours()
        self.in_menu = False
        self.frame_count = 0
        self.display_frame = True
        self.sfx['lobby_music'].play(-1)
        self.sfx['ambience'].stop()

        self.tilemap.load_tilemap('lobby')
        self.load_level()

        #####################################################
        ######################GAME LOOP######################
        #####################################################

        while self.game_running:
            #Skip blitting on some frames to increase FPS on some machines
            self.frame_count += 1
            self.display_frame = self.display_this_frame()

            # Camera movement
            self.scroll[0] += (self.player.rect().centerx - self.screen_width / 4 - self.scroll[0]) / 15
            self.scroll[1] += (self.player.rect().centery - self.screen_height / 4 - self.scroll[1]) / 15
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            if self.display_frame:
                # Background
                self.display.blit(self.background, (0, 0))
                self.display_outline.fill((0, 0, 0, 0))
                self.hud_display.fill((0, 0, 0, 0))
                self.darkness_surface.fill((0, 0, 0, self.cave_darkness))
            self.screenshake = max(0, self.screenshake - 1)

            # RENDER AND UPDATE ALL THE THINGS
            for portal in self.portals:
                if not self.paused:
                    portal.update(self.tilemap)
                if self.display_frame:
                    portal.render(self.display_outline, offset=self.render_scroll)

            for enemy in self.enemies.copy():
                if not self.paused:
                    if enemy.update(self.tilemap, (0, 0)):
                        self.enemies.remove(enemy)
                        self.player.updatenearest_enemy()
                if self.display_frame:
                    enemy.render(self.display_outline, offset=self.render_scroll)

            for boss in self.bosses.copy():
                if not self.paused:
                    if boss.update(self.tilemap, (0, 0)):
                        self.bosses.remove(boss)
                if self.display_frame:
                    boss.render(self.display_outline, offset=self.render_scroll)

            for character in self.characters.copy():
                if not self.paused:
                    character.update(self.tilemap)
                if self.display_frame:
                    character.render(self.display_outline, offset=self.render_scroll)

            for spawn_point in self.spawn_points:
                if not self.paused:
                    spawn_point.update(self.tilemap)
                if self.display_frame:
                    spawn_point.render(self.display_outline, offset=self.render_scroll)

            if not self.dead:
                if not self.paused:
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                if self.display_frame:
                    self.player.render(self.display_outline, offset=self.render_scroll)

            for projectile in self.projectiles.copy():
                if projectile.update(self):
                    self.projectiles.remove(projectile)

            for rect in self.potplants:
                if random.random() < 0.01 and not self.paused:
                    pos = (rect.x + rect.width * random.random(),
                           rect.y + rect.height * random.random())
                    self.particles.append(_particle.Particle(self, 'leaf', pos, vel=[0, random.uniform(0.2, 0.4)], frame=random.randint(0, 10)))

            for currency_item in self.currency_entities.copy():
                if not self.paused:
                    if currency_item.update(self.tilemap, (0, 0)):
                        self.currency_entities.remove(currency_item)
                if self.display_frame:
                    currency_item.render(self.display_outline, offset=self.render_scroll)

            if self.display_frame:
                self.tilemap.render(self.display_outline, offset=self.render_scroll)

            for extra_entity in self.extra_entities.copy():
                if not self.paused:
                    if extra_entity.update(self.tilemap):
                        self.extra_entities.remove(extra_entity)
                if self.display_frame:
                    extra_entity.render(self.display_outline, offset=self.render_scroll)

            for spark in self.sparks.copy():
                if not self.paused:
                    if spark.update(self, offset=self.render_scroll):
                        self.sparks.remove(spark)
                if self.display_frame:
                    spark.render(self.display_outline, offset=self.render_scroll)

            if self.display_frame:
                display_outline_mask = pygame.mask.from_surface(self.display_outline)
                display_outline_sillhouette = display_outline_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))

                for offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    self.display.blit(display_outline_sillhouette, offset)

            for particle in self.particles.copy():
                if self.display_frame:
                    particle.render(self.display_outline, offset=self.render_scroll)
                if not self.paused:
                    kill = particle.update()
                    if particle.type == 'leaf':
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035 + particle.randomness) * 0.2
                    if kill:
                        self.particles.remove(particle)

            # Displaying HUD and text: - brilliant comment, I know
            self.display_hud_text()

            # Level transition
            if self.transition > 30:
                self.tilemap.load_tilemap(self.next_level)
                self.previous_level = self.current_level
                self.current_level = self.next_level

                self.current_level = self.next_level
                self.load_level()
                self.dead = False

            elif self.transition < 31 and self.transition != 0:
                self.transition += 1

            # Remove interaction frames
            self.interraction_frame_c = False
            self.interraction_frame_f = False
            self.interraction_frame_q = False
            self.interraction_frame_s = False
            self.interraction_frame_v = False
            self.interraction_frame_z = False
            self.interraction_frame_int = False
            self.interraction_frame_up = False
            self.interraction_frame_down = False
            self.interraction_frame_left = False
            self.interraction_frame_right = False
            self.interraction_frame_key = False

            # Event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.floors['infinite'] = 1

                    # Add important items left on ground:
                    for currency in self.currency_entities:
                        type = str(currency.currency_type) + 's'
                        if type in self.not_lost_on_death:
                            self.wallet[type] += currency.value
                    self.save_game(self.save_slot)

                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    #Player Controls:
                    if event.key == self.player_controls['Left']:
                        self.movement[0] = True
                    if event.key == self.player_controls['Right']:
                        self.movement[1] = True
                    if event.key == self.player_controls['Up / Jump']:
                        if not self.paused and self.player.jump() and abs(self.player.dashing) < 50:
                            self.sfx['jump'].play()
                        self.movement[2] = True
                    if event.key == self.player_controls['Down']:
                        self.movement[3] = True
                        self.player.gravity = 0.12 if self.level_style == 'space' else 0.2
                    if event.key == self.player_controls['Dash']:
                        if not self.paused:
                            self.player.dash()
                    if event.key == self.player_controls['Interract']:
                        self.interraction_frame_int = True
                    self.interraction_frame_key = event.key

                    #Menu Controls:
                    if event.key == pygame.K_LEFT:
                        self.interraction_frame_left = True
                    if event.key == pygame.K_RIGHT:
                        self.interraction_frame_right = True
                    if event.key == pygame.K_UP:
                        self.interraction_frame_up = True
                    if event.key == pygame.K_DOWN:
                        self.interraction_frame_down = True
                    if event.key == pygame.K_c:
                        self.interraction_frame_c = True
                    if event.key == pygame.K_s:
                        self.interraction_frame_s = True
                    if event.key == pygame.K_v:
                        self.interraction_frame_v = True
                    if event.key == pygame.K_f:
                        self.interraction_frame_f = True
                    if event.key == pygame.K_q:
                        self.interraction_frame_q = True
                    if event.key == pygame.K_z:
                        self.interraction_frame_z = True
                    if event.key == pygame.K_h:
                        self.display_hud = not self.display_hud
                    if event.key == pygame.K_ESCAPE:
                        if not self.talking and not self.dead:
                            self.paused = not self.paused
                        if self.in_controls:
                            self.in_controls = False

                    # DEBUGGING
                    if event.key == pygame.K_r:
                        self.transition_to_level(self.current_level)
                    if event.key == pygame.K_m:
                        self.game_running = False
                    if event.key == pygame.K_t:
                        for currency in self.wallet:
                            self.wallet[currency] += 20
                    if event.key == pygame.K_k:
                        for e in self.enemies.copy():
                            e.kill()
                            self.enemies.remove(e)
                        for c in self.extra_entities.copy():
                            if c.type == 'crate':
                                c.kill()
                                self.extra_entities.remove(c)
                    if event.key ==pygame.K_j:
                        for c in self.currency_entities.copy():
                            self.wallet_temp[str(c.currency_type) + 's'] += c.value
                            self.currency_entities.remove(c)
                    if event.key == pygame.K_p:
                        self.fps += 5
                        print(f'New FPS: {self.fps}')
                    if event.key == pygame.K_o:
                        self.fps -= 5
                        print(f'New FPS: {self.fps}')
                    if event.key == pygame.K_l:
                        self.machine_count = 0
                        loops = 10
                        for lvl in list(self.floor_specifics.keys()):
                            for flr in range(1, 25):
                                for _ in range(loops):
                                    self.tilemap.load_random_tilemap(int(5 * np.log(flr ** 2) + 13 + flr / 4), 20, level_style=lvl, level_type=lvl if lvl not in ['heaven', 'hell'] else 'heaven_hell')
                            print(f'in lvl {lvl} there were {round(self.machine_count/loops, 2)} per run on average')
                            self.machine_count = 0



                if event.type == pygame.KEYUP:
                    if event.key == self.player_controls['Left']:
                        self.movement[0] = False
                    if event.key == self.player_controls['Right']:
                        self.movement[1] = False
                    if event.key == self.player_controls['Up / Jump']:
                        self.movement[2] = False
                    if event.key == self.player_controls['Down']:
                        self.movement[3] = False
                        self.player.gravity = 0.075 if self.level_style == 'space' else 0.12

            if self.dead:
                if self.display_frame:
                    self.darkness_surface.fill(
                        (0, 0, 0, max(self.min_pause_darkness, self.cave_darkness)))
                    self.draw_text('YOU DIED', (self.screen_width / 4, self.screen_height / 4 - 30), self.text_font, (200, 0, 0), scale = 2, mode='center')

                    self.draw_text(self.death_message, (self.screen_width / 4, self.screen_height / 4 - 10), self.text_font, (200, 0, 0), mode='center')
                    self.draw_text('Deaths: ' + str(self.death_count), (self.screen_width / 4, self.screen_height / 4 + 15), self.text_font, (200, 0, 0), mode='center')
                    self.draw_text(f'Press [{pygame.key.name(self.player_controls['Interract'])}] to Alive Yourself', (self.screen_width / 4, self.screen_height / 4 + 30), self.text_font, (200, 0, 0), mode='center')

                if self.interraction_frame_int:
                    self.transition_to_level('lobby')

            if self.display_frame:
                # Darkness effect blit:
                if self.cave_darkness or self.paused or self.dead:
                    self.display_outline.blit(self.darkness_surface, (0, 0))

                self.display.blit(self.display_outline, (0, 0))
                screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2) if self.screenshake_on else (0, 0)
                self.display.blit(self.hud_display, screenshake_offset)

                self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)

                # Level transition circle
                if self.transition:
                    transition_surface = pygame.Surface(self.screen.get_size())
                    pygame.draw.circle(transition_surface, (255, 255, 255), (self.screen.get_width() // 2, self.screen.get_height() // 2), (30 - abs(self.transition)) * (self.screen.get_width() / 30))
                    transition_surface.set_colorkey((255, 255, 255))
                    self.screen.blit(transition_surface, (0, 0))

                pygame.display.update()
                self.clock.tick(self.fps)

        #####################################################
        ####################GAME LOOP END####################
        #####################################################

    def end_game(self):

        self.run_text(self.ending_texts[self.end_type], 'ending')
        self.game_ending = True

        while self.game_ending:

            self.hud_display.fill((1, 1, 1))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.interraction_frame_int = True

            self.display_text()
            if not self.talking:
                self.in_menu = True
                self.game_ending = False

            self.interraction_frame_int = False


            self.display.blit(self.display_outline, (0, 0))
            self.display.blit(self.hud_display, (0, 0))
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

            # self.display.blit(self.display_outline, (0, 0))
            # self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            # self.screen.blit(pygame.transform.scale(self.hud_display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(self.fps)

        self.__init__(fullscreen = self.is_fullscreen, screen_size=(self.screen_width, self.screen_height))
        self.load_menu()

    def update_dialogues(self):
        """Update next available dialogue for all present characters.

        Args:
            none
        Returns:
            none

        """
        for character in self.characters:
            # Update which dialogue the character is up to.
            dialogue = self.dialogue_history[str(character.name)]
            character.new_dialogue = False

            for index in range(int(len(dialogue) / 2)):
                if dialogue[str(index) + 'said']:
                    character.current_dialogue_index = index

            # Checks to see if the player has the required currency to unlock new dialogues.
            for index in character.currency_requirements:
                if index > character.current_dialogue_index + 1:
                    break
                individual_success = True
                success = True

                for i, trade in enumerate(character.currency_requirements[index]):
                    # To unlock dialogue you need to fulfill requirement/s:
                    individual_success = self.check_currency_requirement(trade, self.wallet, index, character.current_dialogue_index, character)

                    if individual_success:
                        character.current_trade_ability[i] = True
                    else:
                        character.current_trade_ability[i] = False
                        success = False

                # SPECIAL CASES:
                # e.g. dont unlock dialogue if in wrong floor etc.
                character_move_to_lobby = ['Noether', 'Curie', 'Planck', 'Lorenz', 'Franklin', 'Rubik', 'Cantor', 'Melatos']
                if (character.name in character_move_to_lobby) & (index >= 1) & (self.current_level != 'lobby'):
                    success = False

                if success:
                    self.dialogue_history[character.name][str(index) + 'available'] = True
                elif index > character.current_dialogue_index + 1 or not self.dialogue_history[character.name][str(index) + 'said']:
                    self.dialogue_history[character.name][str(index) + 'available'] = False

            # Check to see if new dialogue is available:
            for index in range(int(len(dialogue) / 2)):
                if dialogue[str(index) + 'available'] and not dialogue[str(index) + 'said']:
                    character.new_dialogue = True

    def check_currency_requirement(self, trade, wallet, index, character_index, character):
        """Determine whether a trade requirement is met from a specific character.

        Args:
            trade: the specific trade in questionin character's currency_requirements
            wallet: library of player's currencies.
            index: index of specific trade in character's currency_requirements.
            character_index: character's current_dialogue_index
            character: the character's name as a string.
        Returns:
            boolean

        """
        # If you havent reached the dialogue, it is not available
        if index > character_index + 1:
            return False

        # Purchasing things
        if trade[0] == 'purchase':
            if wallet[trade[1]] < trade[2]:
                return False

        # Specifically prime num
        elif trade[0] == 'prime':
            if not _utilities.is_prime(wallet[trade[1]]):
                return False

        # Specifically prime num over a value
        elif trade[0] == 'primePurchase':
            if not _utilities.is_prime(wallet[trade[1]]) or wallet[trade[1]] < trade[3]:
                return False

        # Beat a specific floor of a level:
        elif trade[0] == 'floor':
            # Check for maximum infinite floor
            if trade[1] == 'infinite':
                if self.infinite_floor_max < trade[2]:
                    return False
            # Else check against current floor levels
            elif self.floors[trade[1]] < trade[2] + 1:
                return False

        # Specifically prime num floor
        elif trade[0] == 'primeFloor':
            if trade[1] == 'infinite':
                if not _utilities.is_prime(self.infinite_floor_max):
                    return False
            elif not _utilities.is_prime(self.floors[trade[1]]):
                return False

        # Also the previous dialogue needs to have been said:
        if index != 0:
            if not self.dialogue_history[character.name][str(index - 1) + 'said']:
                return False

        # You can probably access the dialogue.
        return True

    def display_text(self):
        """Displays game.current_text_list one character at a time.

        Args:
            none
        Returns:
            none

        """
        # Each frame an extra character is added to the displayed text.
        # If the length of a line is larger than self.max_characters_line, it creates a new line IF there is a space to not chop words.
        if self.text_length < self.text_length_end and self.current_text_index < self.end_text_index:
            if self.current_text_list[self.current_text_index][self.text_length] == ' ' and len(self.display_text_list[-1]) > self.max_characters_line:
                self.display_text_list.append('')
            else:
                self.display_text_list[-1] = self.display_text_list[-1] + self.current_text_list[self.current_text_index][self.text_length]
            self.text_length += 1
        if self.text_length == self.text_length_end - 1:
            self.sfx['textBlip'].fadeout(50)

        # If all text in current chunk is displayed, move to next chunk.
        if self.interraction_frame_int and self.text_length > 1:
            if self.text_length == self.text_length_end:
                self.sfx['textBlip'].play(fade_ms=50)
                self.current_text_index += 1
                self.text_length = 0
                # Only shallow copy needed
                self.display_text_list = self.talking_object[:]
                try:
                    self.text_length_end = len(self.current_text_list[self.current_text_index])
                except IndexError:
                    pass

            # Fills in current text if the player is impatient
            else:
                # Im sure this while loop will always end, right?
                self.sfx['textBlip'].fadeout(50)
                while self.text_length < self.text_length_end:

                    if self.current_text_list[self.current_text_index][self.text_length] == ' ' and len(self.display_text_list[-1]) > self.max_characters_line:
                        self.display_text_list.append('')
                    else:
                        self.display_text_list[-1] = self.display_text_list[-1] + self.current_text_list[self.current_text_index][self.text_length]
                    self.text_length += 1

        # When to end the dialogue:
        if self.current_text_index >= self.end_text_index:
            self.sfx['textBlip'].fadeout(50)
            self.talking = False
            self.paused = False
            self.update_dialogues()

        # Actually display the text (and icon):
        for n in range(len(self.display_text_list)):
            self.draw_text(str(self.display_text_list[n]), (self.screen_width / 4, (self.screen_height / 4 - 25)-15 + 24*n), self.text_font, (255, 255, 255), scale = 2, mode='center')

        if self.display_icon in self.characters_met.keys():
            char_img = self.assets[f'{self.display_icon.lower()}/idle'].images[0]
            char_img = pygame.transform.scale(char_img, (char_img.get_width() * 3, char_img.get_height() * 3))
            self.hud_display.blit(char_img, ((self.screen_width / 4) - char_img.get_width() / 2, self.screen_height / 4 - 80 - char_img.get_height() / 2))

        elif self.display_icon:
            icon = self.display_icons[self.display_icon]
            icon = pygame.transform.scale(icon, (icon.get_width() * 2, icon.get_height() * 2))
            self.hud_display.blit(icon, ((self.screen_width / 4) - icon.get_width() / 2, self.screen_height / 4 - 70 - icon.get_height() / 2))

    def check_encounter(self, entity):
        """Determine if the player has encountered entity before.
            If not, run text for introduction.

        Args:
            entity: Interracted entity name.
        Returns:
            none

        """
        if not self.encounters_check[entity] and not self.dead:
            self.run_text('New!', entity)
            self.encounters_check[entity] = True

    def load_level(self):
        """Changes currently loaded level to game.next_level.

        Args:
            none
        Returns:
            none

        """
        # Save game:
        self.save_game(self.save_slot)

        # Add important items left on ground:
        for currency in self.currency_entities:
            type = str(currency.currency_type) + 's'
            if type in self.not_lost_on_death:
                self.wallet[type] += currency.value

        self.particles = []
        self.projectiles = []
        self.currency_entities = []
        self.sparks = []
        self.player.dashing = 0
        self.parrots_randomised = False

        if self.next_level != 'infinite':
            self.infinite_floor_max = max(self.floors['infinite'], self.infinite_floor_max)
            self.floors['infinite'] = 1

        if self.dead:
            self.health = self.max_health
            for currency in self.wallet:
                self.wallet_temp[currency] = 0 if not self.infinite_mode_active else int(self.wallet_gained_amount[currency])
                self.wallet[currency] += self.wallet_temp[currency]

                self.wallet_temp[currency] = 0
                self.wallet_gained_amount[currency] = 0
            self.infinite_mode_active = False
                

        elif not self.dead and not self.infinite_mode_active:
            for currency in self.wallet:
                self.wallet[currency] += self.wallet_temp[currency]
                self.wallet_temp[currency] = 0

            if not self.initialising_game and (self.current_level == 'lobby') and self.previous_level not in ['lobby', 'infinite', 'final', 'dump']:
                self.floors[self.previous_level] += 1

        elif not self.dead and self.infinite_mode_active and self.previous_level == 'infinite':
            self.floors[self.previous_level] += 1

        self.player.light_size = min(90 + self.wallet['eyes'], 200)

        # Spawn in entities
        self.enemies = []
        self.bosses = []
        self.portals = []
        self.characters = []
        self.extra_entities = []
        self.spawn_points = []
        self.potplants = []
        self.meteor_sounds = 0

        # Spawn in leaf particle spawners
        self.potplants = []
        for plant in self.tilemap.extract([('potplants', 0), ('potplants', 1), ('potplants', 2), ('potplants', 3), ('decor', 8), ('decor', 9)], keep=True):
            self.potplants.append(pygame.Rect(plant['pos'][0], plant['pos'][1], self.tilemap.tilesize if plant['type'] == 'potplants' else self.tilemap.tilesize*2, self.tilemap.tilesize))

        # Replaces spawn tile with an actual object of the entity:
        for spawner in self.tilemap.extract('spawners'):
            # Player
            if spawner['variant'] == 0:
                # Spawn at spawn_point if one is active, else default spawn pos.
                if self.spawn_point and self.current_level == 'lobby':
                    self.player.pos[0], self.player.pos[1] = self.spawn_point[0], self.spawn_point[1]
                else:
                    self.player.pos = spawner['pos']

                self.player.air_time = 0
                self.player.pos[0] += 4
                self.player.pos[1] += 4

            # Spawns characters if met OR in their world
            elif self.entity_info[spawner['variant']]['type'] == 'character':
                if self.characters_met[self.entity_info[spawner['variant']]['name']] or self.current_level != 'lobby':
                    self.characters.append(self.entity_info[spawner['variant']]['object'](self, spawner['pos'], (8, 15)))

            # Spawns Enemies
            elif self.entity_info[spawner['variant']]['type'] == 'enemy':
                self.enemies.append(self.entity_info[spawner['variant']]['object'](self, spawner['pos'], self.entity_info[spawner['variant']]['size']))

            # Spawns Bosses
            elif self.entity_info[spawner['variant']]['type'] == 'boss':
                self.bosses.append(self.entity_info[spawner['variant']]['object'](self, spawner['pos'], self.entity_info[spawner['variant']]['size']))

            # Spawns Entities
            elif self.entity_info[spawner['variant']]['type'] == 'extra_entity':
                self.extra_entities.append(self.entity_info[spawner['variant']]['object'](self, spawner['pos'], self.entity_info[spawner['variant']]['size']))

            # Spawns Spawn Points
            elif self.entity_info[spawner['variant']]['type'] == 'spawn_point':
                self.spawn_points.append(self.entity_info[spawner['variant']]['object'](self, spawner['pos'], self.entity_info[spawner['variant']]['size']))

        # Replaces spawn tile with an actual object of the portal:
        for portal in self.tilemap.extract('spawnersPortal'):
            if self.portals_met[self.portal_info[portal['variant']]]:
                self.portals.append(_entities.Portal(self, portal['pos'], (self.tilemap.tilesize, self.tilemap.tilesize), self.portal_info[portal['variant']]))

        self.dead = False
        self.player.velocity = [0, 0]
        self.player.set_action('idle')
        self.player.updatenearest_enemy()

        self.screenshake = 0
        self.transition = -30

        self.scroll = [self.player.rect().centerx - self.screen_width / 4,
                       self.player.rect().centery - self.screen_height / 4]

        self.background = pygame.transform.scale(self.assets[f'{self.heaven_hell + self.current_level}Background'], (self.screen_width / 2, self.screen_height / 2))

        # Level Specifics
        if self.current_level == 'lobby':
            self.cave_darkness = 0
            self.remove_broken_tunnels()

        elif self.level_style == 'normal':
            self.cave_darkness = random.randint(self.cave_darkness_range[0], self.cave_darkness_range[1])
        elif self.level_style in ['grass', 'aussie', 'heaven']:
            self.cave_darkness = 0
        elif self.level_style in ['spooky', 'space', 'hell']:
            self.cave_darkness = random.randint(self.cave_darkness_range[1]-50, self.cave_darkness_range[1])
        elif self.level_style in ['rubiks']:
            self.cave_darkness = 100
        elif self.level_style in ['final']:
            self.cave_darkness = 200

        _utilities.set_area_music(self, self.level_style, self.previous_level)

        # Gravity:
        self.player.gravity = 0.12
        if self.level_style == 'space':
            self.player.gravity = 0.075
            for enemy in self.enemies:
                enemy.gravity = 0.075
            for boss in self.bosses:
                boss.gravity = 0.075

        self.update_dialogues()
        self.initialising_game = False

    def draw_text(self, text, pos, font, colour=(0, 0, 0), scale=1, mode='topleft'):
        """Displays text onto the game.hud_display.

        Args:
            text: string of text to display.
            pos: tuple of text coordinates.
            font: text font
            colour: triple of RGB values.
            offset: offset from coordinates.
            scale: resizes text.
            mode: Determines where on the text the pos is. Can be: 'topleft', 'center', 'right', 'left'.
        Returns:
            none

        """
        x_adj = 0
        y_adj = 0

        img = font.render(str(text), True, colour)
        if scale != 1:
            img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
        if mode == 'center':
            x_adj = img.get_width() / 2
            y_adj = img.get_height() / 2
        elif mode == 'right':
            x_adj = img.get_width()
            y_adj = img.get_height()
        elif mode == 'left':
            x_adj = 0
            y_adj = img.get_height()
        self.hud_display.blit(img, (pos[0] - x_adj, pos[1] - y_adj))

    def display_hud_text(self):
        """Displays all the HUD info onto game.hud_display as text.

        Args:
            none
        Returns:
            none

        """
        hud_width = self.screen_width / 2
        hud_height = self.screen_height / 2
        if self.display_hud:
            text_col = (200, 200, 200) if not self.dead else (200, 0, 0)
            if self.frame_count % 60 == 0:
                self.display_fps = round(self.clock.get_fps())
            self.draw_text('FPS: ' + str(self.display_fps), (hud_width - 10,
                        hud_height - 5), self.text_font, text_col, mode='right')

            if not self.in_controls:
                if self.current_level not in ['lobby', 'dump']:
                    self.draw_text('Floor: ' + str(self.floors[self.current_level]), (
                        hud_width - 10, 20), self.text_font, text_col, mode='right')
                    
                    self.draw_text('Enemies Remaining: ' + str(len(self.enemies) + len(self.bosses)),
                                (hud_width / 2, 30), self.text_font, text_col, mode='center')
                else:
                    self.draw_text('Floor: Lobby', (hud_width - 10, 20),
                                self.text_font, text_col, mode='right')
            
                # Display Wallet
                depth = 0
                for currency in self.wallet:
                    if self.wallet[currency] > 0 or self.wallet_temp[currency] > 0:

                        if self.infinite_mode_active:
                            extra = (' (' + str(self.wallet_gained_amount[currency]) + ' gained)' if (self.dead) else '')

                        else:
                            extra = (' (' + str(self.walletlost_amount[currency]) + ' lost)' if (self.dead and currency not in self.not_lost_on_death) else '')

                        currency_display = str(self.wallet[currency]) + (' + ('+str(self.wallet_temp[currency])+')' if (self.current_level != 'lobby' and not self.dead and self.wallet_temp[currency]) else '') + extra

                        self.hud_display.blit(self.display_icons[currency], (5, 5 + depth*15))
                        self.draw_text(currency_display, (25, 5 + depth*15), self.text_font, text_col)
                        depth += 1

                # Display Player Health
                for n in range(self.max_health + self.temporary_health):
                    if n < self.health:
                        heart_img = self.assets['heart']
                    elif n < self.max_health:
                        heart_img = self.assets['heartEmpty']
                    else:
                        heart_img = self.assets['heartTemp']

                    self.hud_display.blit(heart_img, (hud_width / 2 - ((self.max_health + self.temporary_health) * 15) / 2 + n * 15, 5))

                # Display Boss Health once active
                for index, boss in enumerate(self.bosses):
                    if boss.active:
                        for n in range(boss.max_health):
                            if n < boss.health:
                                heart_img = self.assets['bossHeart']
                            else:
                                heart_img = self.assets['bossHeartEmpty']

                            self.hud_display.blit(heart_img, (hud_width / 2 - (boss.max_health * 15) / 2 + n * 15, 40 + 15*index))

        # Display Pause Menu
        if self.paused and not self.talking:
            if self.in_controls:
                self.draw_text('CONTROLS', (hud_width / 2, 25), self.text_font, (200, 200, 200), scale = 2, mode='center')
                self.draw_text('Return To Game: ESC', (hud_width / 2 - 100, hud_height - 15), self.text_font, (200, 200, 200), mode='center')
                self.draw_text('Return To Paused: [Q]', (hud_width / 2 + 100, hud_height - 15), self.text_font, (200, 200, 200), mode='center')

                self.control_index_selected = self.control_index % len(list(self.player_controls.keys()))

                for index, control in enumerate(list(self.player_controls.keys())):
                    self.draw_text(f'{control}', (hud_width / 2 - 75, 75 + 25 * index), self.text_font,(86, 31, 126) if index == self.control_index_selected else (200, 200, 200), mode='left')
                    self.draw_text(f'{pygame.key.name(self.player_controls[control])}', (hud_width / 2 + 75, 75 + 25 * index), self.text_font,(86, 31, 126) if index == self.control_index_selected else (200, 200, 200), mode='right')
                    self.hud_display.blit(self.control_icons[control], (hud_width / 2 - 100, 75 + 25 * index - 12))
                self.draw_text('Press New Key...' if self.changing_control else 'Change: [C]', (hud_width / 2 + 85, 75 + 25 * self.control_index_selected), self.text_font,(86, 31, 126), mode='left')
                
                if not self.changing_control:
                    if self.interraction_frame_up:
                        self.control_index -= 1
                    elif self.interraction_frame_down:
                        self.control_index += 1
                    elif self.interraction_frame_q:
                        self.in_controls = False
                    elif self.interraction_frame_c:
                        self.changing_control = True
                if self.changing_control:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if event.key not in self.disallowed_controls and (event.key not in list(self.player_controls.values()) or event.key == self.player_controls[list(self.player_controls.keys())[self.control_index_selected]]):
                                self.sfx['ding'].play()
                                control_change = list(self.player_controls.keys())[self.control_index_selected]
                                self.player_controls[control_change] = event.key
                                self.changing_control = False
                            else:
                                self.sfx['hit'].play()
            else:
                self.draw_text('PAUSED', (hud_width / 2, hud_height / 2 - 20), self.text_font, (200, 200, 200), scale = 2, mode='center')
                self.draw_text('Return To Game: [ESC]', (hud_width / 2, hud_height / 2), self.text_font, (200, 200, 200), mode='center')
                self.draw_text('Return To Main Menu: [Q]', (hud_width / 2, hud_height / 2 + 20), self.text_font, (200, 200, 200), mode='center')
                self.draw_text('Controls: [C]', (hud_width / 2, hud_height / 2 + 40), self.text_font, (200, 200, 200), mode='center')
                            
                self.draw_text('Screenshake: ' + ('On' if self.screenshake_on else 'Off') + ' [S]', (3 * hud_width / 4, hud_height - 15), self.text_font, (200, 200, 200), mode='center')
                self.draw_text('Volume: ' + ('On' if self.volume_on else 'Off') + ' [V]', (hud_width / 2, hud_height - 15), self.text_font, (200, 200, 200), mode='center')
                self.draw_text('Fullscreen: ' + ('On' if self.is_fullscreen else 'Off') + ' [F]', (hud_width / 4, hud_height - 15), self.text_font, (200, 200, 200), mode='center')

                if self.interraction_frame_s:
                    self.screenshake_on = not self.screenshake_on
                if self.interraction_frame_c:
                    self.in_controls = True
                if self.interraction_frame_f:
                    self.is_fullscreen = not self.is_fullscreen
                    self.toggle_fullscreen()
                if self.interraction_frame_v:
                    self.volume_on = not self.volume_on
                    for sound in self.sfx_volumes.keys():
                        self.sfx[sound].set_volume(self.sfx_volumes[sound] if self.volume_on else 0)
                if self.interraction_frame_q:
                    self.paused = False
                    self.current_level = 'lobby'
                    self.floors['infinite'] = 1
                    _utilities.reset_music(self)
                    self.save_game(self.save_slot)
                    self.__init__(fullscreen = self.is_fullscreen, screen_size=(self.screen_width, self.screen_height))
                    self.load_menu()

            self.darkness_surface.fill((0, 0, 0, max(self.min_pause_darkness, self.cave_darkness)))
        if self.talking:
            self.display_text()
            self.darkness_surface.fill((0, 0, 0, max(self.min_pause_darkness, self.cave_darkness)))

    def load_game_assets(self):
        """Loads all needed images for the game to operate as pygame surfaces.

        Args:
            none
        Returns:
            none

        """
        # BASE_PATH = 'data/images/'
        self.assets = {
            'clouds': _utilities.load_images('clouds'),
            'weapons/gun': _utilities.load_images('weapons/gun'),
            'weapons/staff': _utilities.load_images('weapons/staff'),
            'heart': _utilities.load_image('misc/heart.png'),
            'heartEmpty': _utilities.load_image('misc/heartEmpty.png'),
            'heartTemp': _utilities.load_image('misc/heartTemp.png'),
            'bossHeart': _utilities.load_image('misc/bossHeart.png'),
            'bossHeartEmpty': _utilities.load_image('misc/bossHeartEmpty.png'),
            'exclamation': _utilities.load_image('misc/exclamation.png'),
            'particle/leaf': _utilities.Animation(_utilities.load_images('particles/leaf'), img_dur=20, loop=False),
        }

        # Most entity animations:
        for path in self.asset_info.keys():
            for entity_type in self.asset_info[path].keys():
                for state_info in self.asset_info[path][entity_type]:

                    self.assets[f'{entity_type}{state_info[0]}'] = _utilities.Animation(_utilities.load_images(
                        f'{path}{entity_type}{state_info[0]}'), img_dur=state_info[1], loop=state_info[2])

        for tile in ['decor', 'potplants', 'spawners', 'cracked']:
            self.assets[tile] = _utilities.load_images(f'tiles/{tile}')

        for misc in ['menuBackground', 'menuForeground', 'backgroundcustom', 'spine', 'light', 'witchHat']:
            self.assets[misc] = _utilities.load_image(f'misc/{misc}.png')
        for proj_colour in ['', 'Red', 'Blue', 'Purple']:
            self.assets[f'projectile_{proj_colour}'] = _utilities.load_image(f'misc/projectile_{proj_colour}.png')

        for currency in self.wallet.keys():
            self.assets[f'{currency[:-1]}/idle'] = _utilities.Animation(_utilities.load_images(
                f'currencies/{currency[:-1]}/idle', dim=(7, 7)), img_dur=6)

        for level_type in self.portals_met.keys():
            self.assets[f'portal{level_type}/idle'] = _utilities.Animation(
                _utilities.load_images(f'entities/.portals/portal{level_type}/idle'), img_dur=6)
            self.assets[f'portal{level_type}/opening'] = _utilities.Animation(_utilities.load_images(
                f'entities/.portals/portal{level_type}/opening'), img_dur=6, loop=False)
            self.assets[f'portal{level_type}/closing'] = _utilities.Animation(_utilities.load_images(
                f'entities/.portals/portal{level_type}/opening', reverse=True), img_dur=3, loop=False)
            self.assets[f'portal{level_type}/active'] = _utilities.Animation(
                _utilities.load_images(f'entities/.portals/portal{level_type}/active'), img_dur=6)

            if level_type != 'heaven_hell':
                self.assets[f'{level_type}Background'] = _utilities.load_image(
                    f'misc/background{level_type}.png')

            if level_type not in ['infinite', 'lobby', 'heaven_hell', 'final', 'dump']:
                self.assets[level_type] = _utilities.load_images(f'tiles/{level_type}')

        self.assets['heavenheaven_hellBackground'] = _utilities.load_image(
            'misc/backgroundheaven.png')
        self.assets['heaven'] = _utilities.load_images('tiles/heaven')
        self.assets['hellheaven_hellBackground'] = _utilities.load_image(
            'misc/backgroundhell.png')
        self.assets['hell'] = _utilities.load_images('tiles/hell')

        for character in self.characters_met.keys():
            self.assets[f'{character.lower()}/idle'] = _utilities.Animation(_utilities.load_images(
                f'entities/.characters/{character.lower()}/idle'), img_dur=10)
            self.assets[f'{character.lower()}/run'] = _utilities.Animation(_utilities.load_images(
                f'entities/.characters/{character.lower()}/run'), img_dur=4)
            self.assets[f'{character.lower()}/jump'] = _utilities.Animation(_utilities.load_images(
                f'entities/.characters/{character.lower()}/jump'), img_dur=5)

        for n in range(1, 5):
            self.assets[f'particle/particle{n}'] = _utilities.Animation(
                _utilities.load_images(f'particles/particle{n}'), img_dur=6, loop=False)

        self.assets['stone'] = _utilities.load_images('tiles/stone')

        self.wallet_temp = {}
        self.walletlost_amount = {}
        self.wallet_gained_amount = {}
        self.display_icons = {}
        for currency in self.wallet:
            self.wallet_temp[currency] = 0
            self.walletlost_amount[currency] = ''
            self.wallet_gained_amount[currency] = ''
            self.display_icons[currency] = _utilities.load_image(f'currencies/{currency[:-1]}/idle/0.png')
        for floor in self.floors:
            self.display_icons[floor] = self.assets['normal' if floor in ['infinite', 'heaven_hell', 'final', 'dump'] else floor][0 if floor == 'rubiks' else 11]
        self.display_icons['infinite'] = _utilities.load_image(f'misc/infinitedisplay_icon.png')
        self.display_icons['heaven_hell'] = _utilities.load_image(f'misc/heaven_helldisplay_icon.png')
        self.display_icons['spawn_points'] = self.assets['spawn_point/active'].images[0]
        self.display_icons['heart_altars'] = self.assets['heart_altar/active'].images[0]
        self.display_icons['skull'] = self.assets['skull/idle'].images[0]

        self.sfx_volumes = {
            'lobby_music': 0.6,
            'normal_music': 0.5,
            'grass_music': 0.5,
            'spooky_music': 0.2,
            'rubiks_music': 0.5,
            'aussie_music': 1,
            'space_music': 0.3,
            'heaven_music': 0.5,
            'hell_music': 0.5,
            'final_music': 0.5,
            'hilbert_music': 0.5,
            'jump': 0.2,
            'dash': 0.1,
            'hit': 0.7,
            'shoot': 0.4,
            'coin': 0.6,
            'ambience': 0.2,
            'textBlip': 0.25,
            'ding': 0.1,
            'dashClick': 0.05,
            'blip': 0.1,
            'meteor': 0.3,
            'laser': 0.3,
            'proj_bye': 0.2,
            'chirp': 1,
            'spider': 0.5,
        }

        self.sfx = {}

        for sound in self.sfx_volumes.keys():
            self.sfx[sound] = pygame.mixer.Sound(f'data/sfx/{sound}.wav')
            self.sfx[sound].set_volume(self.sfx_volumes[sound])

        self.window_icon = _utilities.load_image('misc/window_icon.png', dim = [32, 32])
        pygame.display.set_icon(self.window_icon)

    def run_text(self, character, talk_type='npc'):
        """Initiates text to be blit onto screen.

        Args:
            character: character with the dialogue
            talk_type: either 'npc' or not depending on character or other entity interaction.
        Returns:
            none

        """
        self.paused = True
        self.talking = True
        self.talking_to = character
        self.sfx['textBlip'].play(fade_ms=50)
        if talk_type == 'npc':
            convo_info = character.get_conversation()
            self.current_text_list = convo_info[0]
            character.conversation_action(convo_info[1])
            convo_info = character.get_conversation()
            self.display_text_list = [str(character.name) + ': ', ' ']
            self.display_icon = character.name
        elif character == 'New!':
            try:
                self.current_text_list = self.encounters_check_text[talk_type]
            except KeyError:
                self.current_text_list = self.encounters_check_text['error']
            self.display_text_list = [character, '']
            self.display_icon = talk_type
        else:
            self.current_text_list = character
            self.display_text_list = [' ']
            self.display_icon = False

        self.update_dialogues()
        # Only shallow copy needed
        self.talking_object = self.display_text_list[:]
        self.current_text_index = 0
        self.end_text_index = len(self.current_text_list)
        self.text_length = 0
        self.text_length_end = len(self.current_text_list[0])

    def transition_to_level(self, new_level):
        """Sets game.next_level to the new level to be loaded.

        Args:
            new_level: next level to load
        Returns:
            none

        """
        self.next_level = new_level
        self.transition += 1

    def darkness_circle(self, transparency, radius, pos):
        """Displays circle of light on the game.darkness_surface surface.

        Args:
            transparency: transparency value 0 - 255
            radius: radius in pixels of circle
            pos: where to blit circle
        Returns:
            none

        """
        pygame.draw.circle(self.darkness_surface, (0, 0, 0, transparency), pos, radius)

    def get_save_info(self):
        """Used on main menu to retrieve number of deaths for each save file.
        Also changes the saved character looks.

        Args:
            none
        Returns:
            list, each element is 'No Data' or 'N Deaths'

        """
        death_list = ['No Data', 'No Data', 'No Data']
        for i in range(len(death_list)):
            try:
                f = open('data/saves/' + str(i) + '.json', 'r')
                save_data = json.load(f)
                f.close()

                death_list[i] = 'Deaths: ' + str(save_data['death_count'])

                #Get image of saved character:
                img = self.assets['player/idle'].images[0].copy()
                char_colours = save_data['player_colours']
                for cosmetic in char_colours.keys():
                    img = _utilities.colour_change(img, self.player_colours[cosmetic], tuple(char_colours[cosmetic]))
                img = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
                self.saved_characters[i] = img

            except FileNotFoundError:
                self.saved_characters[i] = False
        try:
            f.close()
        except UnboundLocalError:
            pass

        return death_list

    def get_random_level(self):
        """Get list of level types that the player has beaten at least one floor in.

        Args:
            none
        Returns:
            list of visited level types.

        """
        available_floors = []

        for level in self.floors.keys():
            if level not in ['final', 'dump']:
                if self.floors[level] > 1 and level not in ['infinite', 'heaven_hell', 'final']:
                    available_floors.append(level)

                elif self.floors[level] > 1 and level == 'heaven_hell':
                    available_floors.append('heaven')

                    if self.floors[level] > 2:
                        available_floors.append('hell')
        try:
            return random.choice(available_floors)
        except IndexError:

            return 'normal'

    def remove_broken_tunnels(self):
        """Remove certain tiles in lobby level that correspond to tunnel tiles.

        Args:
            none
        Returns:
            none

        """
        for tunnel in [e for e in self.tunnels_broken if self.tunnels_broken[e] is True]:

            for loc in self.tunnel_positions[tunnel]:
                if self.tilemap.tilemap[str(loc[0]) + ';' + str(loc[1])]['type'] == 'cracked':
                    del self.tilemap.tilemap[str(loc[0]) + ';' + str(loc[1])]

    def get_completed_characters(self):
        """Get list of characters who's last dialogue has been said.

        Args:
            none
        Returns:
            list of completed characters.

        """
        completed = []

        for character in self.dialogue_history:
            last_key = list(self.dialogue_history[character])[-1]

            if self.dialogue_history[character][last_key] and character != 'Hilbert':
                completed.append(character)

            elif character == 'Planck' and self.temp_hearts_bought >= self.temp_hearts_for_planck:
                completed.append(character)

        return completed
    
    def begin_final_boss(self):

        #Get characters to help
        completed_characters = self.get_completed_characters()

        #Get helper objects
        helper_objects = []
        machine_x = 0
        for e in self.extra_entities:
            if e.type == 'helper':
                helper_objects.append(e)
            elif e.type == 'machine':
                machine_x = e.pos[0]

        #Assign character skins to the helpers:
        for character in completed_characters:

            helper = random.choice(helper_objects)
            helper.activate(character.lower(), flip = True if helper.pos[0] > machine_x else False)

            helper_objects.remove(helper)

        #Remove other helpers:
        for helper in helper_objects:
            self.extra_entities.remove(helper)

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            # self.screen_width = screen_info.current_w
            # self.screen_height = screen_info.current_h
        else:
            # self.screen_width = self.default_width
            # self.screen_height = self.default_height
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

    def display_this_frame(self):
        """Determine whether current frame should be blitted. This returns false more the lower the fps.

        Args:
            none
        Returns:
            Boolean. Whether the tiles/entities are blitted or not

        """
        self.frame_fps = max(round(self.clock.get_fps()), 1)
        self.display_inc = max(min(1, self.frame_fps / self.master_fps), 0.05)

        if self.frame_fps <= 30:
            self.display_inc = round(max(1, self.master_fps / self.frame_fps))
            return True if self.frame_count % self.display_inc == 0 else False
        
        elif self.frame_fps < 55:
            self.display_inc = round(max(1, self.master_fps / (self.master_fps-self.frame_fps)))
            return False if self.frame_count % self.display_inc == 0 else True
        else:
            return True

    def delete_save(self, save_slot):
        """Deleted selected save file.

        Args:
            save_slot: save file to be deleted
        Returns:
            none

        """
        try:
            os.remove('data/saves/' + str(save_slot) + '.json')
        except FileNotFoundError:
            pass

    def save_game(self, save_slot):
        """Saves game's necessary data into specific save file.

        Args:
            save_slot: save file to save to
        Returns:
            none

        """
        if self.health <= 0:
            self.health = self.max_health
        with open('data/saves/' + str(save_slot) + '.json', 'w') as f:
            json.dump({'wallet': self.wallet,
                       'max_health': self.max_health,
                       'power_level': self.power_level,
                       'difficulty': self.difficulty,
                       'tempHealth': self.temporary_health,
                       'temp_hearts_bought': self.temp_hearts_bought,
                       'totalJumps': self.player.total_jumps,
                       'totalDashes': self.player.total_dashes,
                       'health': self.health,
                       'tunnels_broken': self.tunnels_broken,
                       'death_count': self.death_count,
                       'floors': self.floors,
                       'infinite_floor_max': self.infinite_floor_max,
                       'spawn_point': self.spawn_point,
                       'available_enemy_variants': self.available_enemy_variants,
                       'screenshake_on': self.screenshake_on,
                       'volume_on': self.volume_on,
                       'portals_met': self.portals_met,
                       'characters_met': self.characters_met,
                       'encounters_check': self.encounters_check,
                       'completed_wins': self.completed_wins,
                       'creation_done': self.creation_done,
                       'player_colours': self.player_colours,
                       'player_controls': self.player_controls,
                       'dump_machine_state': self.dump_machine_state,
                       'dialogue': self.dialogue_history}, f, indent=4)

    def load_game(self, save_slot):
        """Loads game parameters from a save file and sets them to game object.

        Args:
            save_slot: save file to be loaded
        Returns:
            none

        """
        try:
            with open('data/saves/' + str(save_slot) + '.json', 'r') as f:
                save_data = json.load(f)

                # Ensure needed data exists:
                self.validate_save(save_data)

                # load data:
                self.wallet = save_data['wallet']
                self.max_health = save_data['max_health']
                self.power_level = save_data['power_level']
                self.difficulty = save_data['difficulty']
                self.temporary_health = save_data['tempHealth']
                self.temp_hearts_bought = save_data['temp_hearts_bought']
                self.player.total_jumps = save_data['totalJumps']
                self.player.total_dashes = save_data['totalDashes']
                self.health = save_data['health']
                self.tunnels_broken = save_data['tunnels_broken']
                self.death_count = save_data['death_count']
                self.floors = save_data['floors']
                self.infinite_floor_max = save_data['infinite_floor_max']
                self.spawn_point = save_data['spawn_point']
                self.available_enemy_variants = save_data['available_enemy_variants']
                self.screenshake_on = save_data['screenshake_on']
                self.volume_on = save_data['volume_on']
                self.portals_met = save_data['portals_met']
                self.characters_met = save_data['characters_met']
                self.encounters_check = save_data['encounters_check']
                self.completed_wins = save_data['completed_wins']
                self.creation_done = save_data['creation_done']
                self.player_colours = save_data['player_colours']
                self.player_controls = save_data['player_controls']
                self.dump_machine_state = save_data['dump_machine_state']
                self.dialogue_history = save_data['dialogue']

        except FileNotFoundError:
            pass

        for sound in self.sfx_volumes.keys():
            self.sfx[sound].set_volume(
                self.sfx_volumes[sound] if self.volume_on else 0)

    def validate_save(self, data):
        """Validates game parameters from a save file.

        Args:
            save_slot: save file to be validated
        Returns:
            none

        """
        for currency in self.wallet.keys():
            if currency not in data['wallet']:
                data['wallet'][currency] = 0

        for tunnel in self.tunnels_broken.keys():
            if tunnel not in data['tunnels_broken']:
                data['tunnels_broken'][tunnel] = self.tunnels_broken[tunnel]

        for floor in self.floors.keys():
            if floor not in data['floors']:
                data['floors'][floor] = 1

        for type in self.floor_specifics.keys():
            if type not in data['available_enemy_variants']:
                data['available_enemy_variants'][type] = self.available_enemy_variants[type]
                data['available_enemy_variants'][type + 'Weights'] = self.available_enemy_variants[type + 'Weights']

        for portal in self.portals_met.keys():
            if portal not in data['portals_met']:
                data['portals_met'][portal] = self.portals_met[portal]

        for character in self.characters_met.keys():
            if character not in data['characters_met']:
                data['characters_met'][character] = self.characters_met[character]

        for encounter in self.encounters_check.keys():
            if encounter not in data['encounters_check']:
                data['encounters_check'][encounter] = False

        for character in self.dialogue_history.keys():
            if character not in data['dialogue'].keys():
                data['dialogue'][character] = self.dialogue_history[character]

            else:
                for text_info in self.dialogue_history[character].keys():
                    if text_info not in data['dialogue'][character]:
                        data['dialogue'][character][text_info] = self.dialogue_history[character][text_info]
        
        if 'player_controls' not in data:
            data['player_controls'] = self.player_controls
        for control in self.player_controls.keys():
            if control not in data['player_controls']:
                data['player_controls'][control] = self.player_controls[control]

        if 'dump_machine_state' not in data:
            data['dump_machine_state'] = self.dump_machine_state
        


if __name__ == '__main__':
    Game().load_menu()
    # cProfile.run('Game().load_menu()', sort = 'tottime')
