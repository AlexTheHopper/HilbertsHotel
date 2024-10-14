"""
Characters module for Hilbert's Hotel.
Includes all character information and behaviour including trades and dialogue.
"""
import random
import math
import scripts.entities as _entities

class Character(_entities.PhysicsEntity):
    def __init__(self, game, pos, size, name):

        super().__init__(game, name.lower(), pos, size)
        self.type = name.lower()
        self.name = name

        self.walking = 0
        self.flip_x = True if random.random() < 0.5 else False
        self.can_talk = True
        self.new_dialogue = False
        self.gravity_affected = True

        self.current_dialogue_index = 0

        # To allow different trades at the same time to be green or red depending on wallet/succes.
        # Needs to be as long as the longest character trade.
        self.current_trade_ability = [False, False, False, False]

    def update(self, tilemap, movement=(0, 0)):
        # Walking logic, turning around etc

        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip_x else 7), self.pos[1] + 23)):
                if (self.collisions['left'] or self.collisions['right']):
                    self.flip_x = not self.flip_x

                else:
                    movement = (
                        movement[0] - 0.5 if self.flip_x else 0.5, movement[1])
            else:
                self.flip_x = not self.flip_x
                self.walking = 0
            self.walking = max(self.walking - 1, 0)

        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(self.game.tilemap, movement=movement)

        # Setting animation type
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if self.can_talk:

            distto_player = math.dist(
                self.rect().center, self.game.player.rect().center)

            try:
                requirement_num = len(
                    self.currency_requirements[self.current_dialogue_index + 1])
            except KeyError:
                requirement_num = 0

            xpos = 2 * (self.pos[0] - self.game.render_scroll[0] + self.anim_offset[0] + 7)
            ypos = 2 * int(self.pos[1] - self.game.render_scroll[1] + self.anim_offset[1]) - 30
            offset_length = 80

            if requirement_num > 0:
                offset_n = 0
                for i, requirement in enumerate(self.currency_requirements[self.current_dialogue_index + 1]):
                    # Display requirements above character:
                    self.game.hud_display.blit(self.game.display_icons[requirement[1]], (
                        xpos - (requirement_num * offset_length) / 2 + offset_n * offset_length + 10, ypos))
                    colour = (0, 150, 0) if self.current_trade_ability[i] else (
                        150, 0, 0)
                    self.game.draw_text(str(requirement[2]), (xpos + 30 - (requirement_num * offset_length) / 2 + offset_n *
                                        offset_length + 10, ypos - 2), self.game.text_font, colour, (0, 0), mode='left', scale=0.75)
                    offset_n += 1

            elif distto_player >= 15 and self.new_dialogue:
                self.game.draw_text('(!)', (xpos, ypos - (15 if requirement_num else -15)),
                                    self.game.text_font, (255, 255, 255), (0, 0), mode='center', scale=0.75)

            if distto_player < 15:
                self.game.draw_text('(z)', (xpos, ypos - (15 if requirement_num else -15)),
                                    self.game.text_font, (255, 255, 255), (0, 0), mode='center', scale=0.75)
                if self.game.interraction_frame_z and not self.game.dead:
                    self.game.run_text(self)

    def get_conversation(self):
        self.game.update_dialogues()
        dialogue = self.game.dialogue_history[self.name]

        for index in range(int(len(dialogue) / 2)):
            available = dialogue[str(index) + 'available']
            said = dialogue[str(index) + 'said']

            if not available:
                return (self.dialogue[str(index - 1)], index - 1)

            elif available and not said:
                return (self.dialogue[str(index)], index)

        index = int(len(dialogue) / 2) - 1
        return (self.dialogue[str(index)], int(index))

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)
        if self.game.cave_darkness:
            self.game.darkness_circle(0, 50, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(
                self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))


class Hilbert(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Hilbert')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'cogs', 5]],
            3: [],
            4: [['purchase', 'cogs', 50]],
            5: [['purchase', 'cogs', 100]],
            6: [['purchase', 'cogs', 150]],
            7: [['purchase', 'eyes', 30]],
            8: [['purchase', 'redCogs', 5]],
            9: [['purchase', 'blueCogs', 5], ['purchase', 'purpleCogs', 5]],
            10: [['purchase', 'fairyBreads', 20], ['purchase', 'boxingGloves', 20], ['floor', 'aussie', 15]],
            11: [['purchase', 'purpleCogs', 10], ['floor', 'space', 20]],
            12: [['purchase', 'yellowOrbs', 20], ['purchase', 'redOrbs', 20], ['floor', 'heaven_hell', 25]],
        }

        self.dialogue = {
            '0': ['Welcome...To my (Hilbert\'s) Hotel!',
                  'Where it\'s not only bigger, but INFINITE on the inside!',
                  'I sure am glad I hired you, it\'s been attacked and the whole thing is full of intruders!',
                  'Would you be able to help me take back control, and find my friends somewhere in the hotel?',
                  'Oh! You can dash attack with your x key?',
                  'How original...'],

            '1': ['Anyway, we\'ll need a few things to build a super secret weapon to fight back. Some of them are slightly odd, but trust in the process!',
                  'You can travel up the hotel through my portal elevator!',
                  'Please bring me back the cogs that were stolen! I\'m gonna need about 5 to start this.'],

            '2': ['Thanks for getting some cogs woow!',
                  'I just realised I actually need another 50 though.',
                  'Be careful! The floors get bigger as you ascend! Which makes no structural sense, I dont know how it works!',
                  'Oh and if you get lost, follow the fireflies!'],

            '3': ['Also, yes I know its dark as hell up there sometimes.',
                  'I dunno, maybe find some extra eyes. I\'m sure that\'d help you see better.'],

            '4': ['Amazing job wow!',
                  'Really sorry but I still need 100 more.',
                  'I think I heard some bats around earlier, watch out for them. They fly around and suddenly go AHHH at you, ya know?'],

            '5': ['You know the drill...',
                  'This time I\'ll need 150 cogs.'],

            '6': ['A\'ight spiffo. I think we have enough cogs.',
                  'Now, this is very gross, but you know those eyes I mentioned before? I need like 30 of them. I\'m not super sure where to get them but I believe in you my lil buddy!'],

            '7': ['Yay thanks I love eyes! Now, with this newfound sense of vision, I detect that some of these bad guys are getting much stronger this far up!',
                  'From now on, you\'ll have to pack a harder punch somehow. I\'m at a loss how to do that but I\'m sure theres a way!',
                  'Oh and yeah, DONT go into this portal until you\'re a bit stronger. Like seriously you just wont be able to kill them.',
                  'Seriously.',
                  'But I do think these stronger enemies should drop a special kind of cog! Please bring me some to investigate!'],

            '8': ['Ooooooh, I love these cogs! We\'re getting close now, soon my super secret weapon will be ready! It will be able to remove ALL of the intruders from the Hotel, finally allowing the guests to stay in peace!',
                  'You got any more kinds of these here cogs?'],

            '9': ['Hehe spiffo! Thanks bud!',
                  'This one is going to be a strange request, but I need you to delve deep into the heart of Australia and fetch a couple things for the machine.'],
                  
            '10': ['Beautiful and amazing you are! Soon my Hotel will be rid of all these intruders and I will be able to house as many customers as I like!',
                   'Now I need you to go and defeat some of these pesky spaceships flying around somewhere in here, they\'re really messing with the vibe.'],

            '11': ['Finally, I think the machine is ready. I only need a power source now.',
                   'I only know of one thing with the gusto needed for this to work.',
                   'I need you to defeat devils and gods, and bring me back their power sources.',
                   'Tall ask, I know, but you got this chief!'],

            '12': ['This is it. The machine is ready. Meet me at the penthouse.']
            }

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.

        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.dialogue_history[self.name]['1available'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 5

        elif key == 4 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 50

            self.game.available_enemy_variants['normal'].append(4)
            self.game.available_enemy_variants['normalWeights'].append(1)

        elif key == 5 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 100

        elif key == 6 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 150

        elif key == 7 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['eyes'] -= 30
            self.game.difficulty += 1

        elif key == 8 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['redCogs'] -= 5

        elif key == 9 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['purpleCogs'] -= 5
            self.game.wallet['blueCogs'] -= 5

        elif key == 10 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['fairyBreads'] -= 20
            self.game.wallet['boxingGloves'] -= 20

        elif key == 11 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['purpleCogs'] -= 10

        elif key == 12 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.currency_entities.append(
                _entities.Currency(self.game, 'penthouseKey', self.game.player.pos))
            self.game.wallet['yellowOrbs'] -= 20
            self.game.wallet['redOrbs'] -= 20

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Noether(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Noether')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'heartFragments', 5]],
            3: [['purchase', 'heartFragments', 25]],
            4: [['purchase', 'heartFragments', 50]],
            5: [['purchase', 'heartFragments', 75]],
            6: [['purchase', 'heartFragments', 100]],
            7: [['purchase', 'heartFragments', 100]],
            8: [['purchase', 'heartFragments', 100]],
            9: [['purchase', 'heartFragments', 100]],
        }

        self.dialogue = {
            '0': ['Oh by golly gosh am I lost! Do you know the way back to the lobby?',
                  'Brilliant, cheers Ill follow you back!'],

            '1': ['Oh yeah by the way I\'m also quite useful \'round here.',
                  'I can make you extra hearts! I just need a few Heart Fragments!',
                  'Bring me 5 and the heart is yours!'],

            '2': ['You\'ve got two hearts! Woo!',
                  'Ew, these things are disgusting... and still beating! EW!',
                  'Hearts are super useful! If you run out, you\'ll lose a quarter of everything :( I\'ll give ya another for 25 fragments.'],

            '3': ['You\'ve got three hearts! Woo!',
                  'Look at you go, youll be a cat in no time!',
                  'You know what else has three hearts? Octopuses!',
                  'Octopi? Octopodes? Octipodes? I dunno, but them!'],

            '4': ['You\'ve got four hearts! Woo!',
                  'Did you know that hagfish also have four hearts?',
                  'Yummy yummy hearts in my tummy!'],

            '5': ['You\'ve got five hearts! Woo!',
                  'Similarly, earthworms also have five, isn\'t that crazy!',
                  'I bet you want six right?'],

            '6': ['You\'ve got six hearts! Woo!',
                  'That\'s like, two octopoides!',
                  'I bet you want seven right?'],

            '7': ['You\'ve got seven hearts! Woo!',
                  'Damn, seven hearts is like if an earthworm and Mr. David Tennant had a baby! Isn\'t that neat to think about?'],

            '8': ['You\'ve got eight hearts! Woo!',
                  'Crazy how if two octopodidies and Mr. David Tennant all had a baby it would also have that many hearts!'],

            '9': ['You\'ve got nine whole hearts! Woo!',
                  'You\'re a cat now, go you!!',
                  'Wow I love cats, I\'ll follow you to the ends of the world!'], }

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Noether'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.max_health += 1
            self.game.health = self.game.max_health

            self.game.wallet['heartFragments'] -= 5

        elif key == 3 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.max_health += 1
            self.game.health = self.game.max_health

            self.game.wallet['heartFragments'] -= 25

        elif key == 4 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.max_health += 1
            self.game.health = self.game.max_health

            self.game.wallet['heartFragments'] -= 50

        elif key == 5 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.max_health += 1
            self.game.health = self.game.max_health

            self.game.wallet['heartFragments'] -= 75

        elif key in [6, 7, 8, 9] and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.max_health += 1
            self.game.health = self.game.max_health

            self.game.wallet['heartFragments'] -= 100

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Curie(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Curie')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'wings', 20]],
            3: [['purchase', 'wings', 25]],
            4: [['purchase', 'wings', 40]],
            5: [['purchase', 'wings', 50], ['purchase', 'cogs', 100], ['purchase', 'redCogs', 25], ['purchase', 'chitins', 25]],
            6: [['purchase', 'wings', 50], ['purchase', 'cogs', 100], ['purchase', 'redCogs', 50], ['purchase', 'chitins', 50]]
        }

        self.dialogue = {
            '0': ['Oh by golly gosh am I lost! Do you know the way back to the lobby?',
                  'Brilliant, cheers I\'ll follow you back!'],

            '1': ['Oh yeah by the way I\'m also quite useful \'round here.',
                  'I can make you winged boots! They let you jump more in the air!',
                  'I just need a few bat wings! Bring me 25 and the extra jump is yours!'],

            '2': ['You\'ve got two jumps! Woo! Isn\'t this such a novel mechanic?',
                  'I\'ll give ya another for 50 wings.'],

            '3': ['You\'ve got three jumps! Woo! We\'re really pushing this double jump idea.',
                  'I\'ll give ya another for 75 wings.'],

            '4': ['You\'ve got four jumps! Woo! How many is too many?',
                  'Now, this next deal I got for ya is very lucrative. Not even Hilbert knows about this tech. I heard that you can do a lil dash in the air right?',
                  'Well, I have worked out a way to let you dash more times in a row before cooling down!',
                  'It\'s a bit expensive but I\'m sure you\'ll love it!'],

            '5': ['How crazy is this! You can do two lil dashes in the air!',
                  'I can improve this more, just you watch!'],

            '6': ['Wow. I\'m digging your style, my guy.',
                  'Unfortunately, that\'s the limit of my tech at the moment, but I would love to see these boots in action soon! Let me know if you need any help in there!']
        }

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Curie'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 25

        elif key == 3 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 50

        elif key == 4 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 75

        elif key == 5 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.player.total_dashes += 1

            self.game.wallet['wings'] -= 50
            self.game.wallet['cogs'] -= 100
            self.game.wallet['redCogs'] -= 25
            self.game.wallet['chitins'] -= 25

        elif key == 6 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.player.total_dashes += 1

            self.game.wallet['wings'] -= 50
            self.game.wallet['cogs'] -= 100
            self.game.wallet['blueCogs'] -= 50
            self.game.wallet['chitins'] -= 50

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Planck(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Planck')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'heartFragments', 5]]
        }

        self.dialogue = {
            '0': ['Oh by golly gosh am I lost! Do you know the way back to the lobby?',
                  'Brilliant, cheers I\'ll follow you back!'],

            '1': ['Oh yeah by the way I\'m also quite useful \'round here.',
                  'I can make you temporary hearts! They will only last until you get hit.',
                  'They\'re each yours for just 5 heart fragments! It\'s been a bit slow here at the ol\' Temporary Heart Shop... Please buy them...'],

            '2': ['Here\'s a temporary heart!',
                  'Don\'t go losing it all at once!',
                  '']}

        self.update_final_text()

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Planck'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['heartFragments'] -= 5
            self.game.temp_hearts_bought += 1
            self.update_final_text()
            self.game.temporary_health += 1

        if key != 2:
            self.game.dialogue_history[self.name][str(key) + 'said'] = True

    def update_final_text(self):
        self.final_text = f'If you buy {self.game.temp_hearts_for_planck -
                                       self.game.temp_hearts_bought} more I will be able to pay off all my debts to Hilbert and be forever in your debt!' if self.game.temp_hearts_bought < self.game.temp_hearts_for_planck else 'I can finally pay off my debts! Thank you so so much kind stranger!'
        self.dialogue['2'][2] = self.final_text


class Faraday(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Faraday')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'cogs', 100]],
            3: []
        }

        self.dialogue = {
            '0': ['Psssst... Yay you found me woo!',
                  'But also... it took me so long to put up that wall! :(',
                  'Anyway, I\'ve been hiding from Hilbert. I dont think he really has the Hotel\'s best interests at heart!'],

            '1': ['He\'s been doing some real sneaky things recently and I would be really careful about ascending too far in the hotel.',
                  'The hotel is much bigger than you think. There are infinite slices stacked side by side and some of them get... weird.',
                  'Bring me 100 cogs and I\'ll show you one.'],

            '2': ['Amazing, I\'ll build another elevator for you! It will be ready next time you come back to the lobby.',
                  'I\'ll hide it here so Hilbert wont see it! Give me a jiffy and it\'ll be ready!'],

            '3': ['I\'ve seen so many parts to this hotel but since the attack I can\'t get to most of them! They\'ve all been sealed off but I managed to scrape this portal together.',
                  'This one is very basic, but be warned, some you wont like. And the monsters... you\'ll need to get stronger to face them.',
                  'I\'m too scared to face Hilbert on my own but if you ever build up the courage, I\'ll be there by your side.']}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.

        if key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 100
            self.game.portals_met['grass'] = True

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Lorenz(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Lorenz')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [],
            3: [['prime', 'cogs', 'P']],
            4: [['primePurchase', 'cogs', 'P>200', 200]],
            5: [['primePurchase', 'cogs', 'P>200', 200], ['primePurchase', 'wings', 'P>50', 50]],
            6: [['prime', 'cogs', 'P'], ['prime', 'wings', 'P'], ['prime', 'heartFragments', 'P']],
            7: [['floor', 'normal', 25]],
            8: [['primeFloor', 'normal', 'P'], ['primeFloor', 'infinite', 'P']],
            9: [['floor', 'infinite', 20]]
        }

        self.dialogue = {
            '0': ['AHHHHH! I\'m so lost oops! Do you know the way back to the lobby?',
                  'Oh, yeah the big obvious door, that makes sense, cheers mate!'],

            '1': ['Oh yeah by the way I\'m definitely the most useful \'round here.',
                  'For you...',
                  'I\'ve got...',
                  '......',
                  '......................',
                  '...................................................................',
                  'HAMMERS!!'],

            '2': ['Hammers are super useful for smashing walls that are already down on their luck by being structurally unsound. You can see those lil cracks just like on my right!',
                  'But I aint a fan of the normal \'pay this much for this hammer\' boring shenanigans, I only like prime numbers!',
                  'Bring me EXACTLY a prime number of cogs and a hammer is yours!'],

            '3': ['Hammer go smash!',
                  'Oh and also, youll never lose hammers on death! WOO! Go give it a go!',
                  'I got more too! But this time you gotta bring me a prime number of cogs OVER 200!'],

            '4': ['Hammer go smash!',
                  'I got more too! But this time you gotta bring me a prime number of cogs over 200 and a prime number of wings over 50!',
                  'Also, have you noticed those cracks on the middle of the roof? Suuuuuper weird...'],

            '5': ['Hammer go smash!',
                  'I have another hammer, but now I want a prime number of more things! :)'],

            '6': ['Hammer go smash!',
                  'I have another hammer, but can you explore and clear up to floor 25 please!',
                  'Some of the others keep talking about something special in there and I reeeeealy wanna know what it is!'],

            '7': ['Hammer go SMASH!',
                  'Now for this next hammer, can you clea up to a prime floor on each of these areas please?'],

            '8': ['Hammer go SMASH!',
                  'For the FINAL hammer, can you clear floor 20 on this infinite thing please?',
                  'Doesn\'t seem like this special thing is where the bats are so maybe it\'s somewhere else!'],

            '9': ['Hammer go SMASH!!',
                  'Please forgive me, I don\'t have anymore hammers :(',
                  'But if you find it and need me, I\'ll be there for you!']}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Lorenz'] = True

        if key in [3, 4, 5] and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.currency_entities.append(
                _entities.Currency(self.game, 'hammer', self.game.player.pos))
            self.game.wallet['cogs'] = 0

        if key == 6 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.currency_entities.append(
                _entities.Currency(self.game, 'hammer', self.game.player.pos))
            self.game.wallet['cogs'] = 0
            self.game.wallet['wings'] = 0
            self.game.wallet['heartFragments'] = 0

        if key in [7, 8, 9] and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.currency_entities.append(
                _entities.Currency(self.game, 'hammer', self.game.player.pos))

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Franklin(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Franklin')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'chitins', 50]],
            3: [['purchase', 'chitins', 50], ['purchase', 'boxingGloves', 50], ['purchase', 'cogs', 50]],
            4: [['purchase', 'chitins', 50], ['purchase', 'cogs', 50], ['purchase', 'blueCogs', 25], ['purchase', 'redCogs', 25]]
        }

        self.dialogue = {
            '0': ['Oopsie doopsie I got myself all stuck in this creepy as hell house. Do you know the way out?',
                  'Brilliant, cheers I\'ll follow you back!'],

            '1': ['Oh yeah by the way I\'m likely the most useful in these here parts.',
                  'I can tippity tap into your own DNA and make you stronger. There\'s this nifty stuff called chitin that I can use to reinforce you!',
                  '"What is chitin?" you ask? Who knows!'
                  'Bring me 50 chitin and I\'ll make you stronger!'],

            '2': ['Yay woo! Your power level is now 2!',
                  'I\'ll give ya another for 50 more chitin and some real smackeroonie gloves!'],

            '3': ['Yay woo! Your power level is now 3!',
                  'And just in time! I\'ve just detected that some of those guys have become stronger!'
                  'I\'ll give ya another for 50 more chitin and a few little goodies.'],

            '4': ['Yay woo! Your power level is OVER 3!',
                  'Wow, just in time again, what a coinkidink! Some of those guys shooting at you just got even stronger!'
                  'I would love to see this power in action! When you take on your biggest challenge, I\'ll be there!']}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Franklin'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.power_level += 1

            self.game.wallet['chitins'] -= 50

        elif key == 3 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.power_level += 1
            self.game.difficulty += 1

            self.game.wallet['chitins'] -= 50
            self.game.wallet['boxingGloves'] -= 50

        elif key == 4 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.power_level += 1
            self.game.difficulty += 1

            self.game.wallet['chitins'] -= 50
            self.game.wallet['cogs'] -= 50
            self.game.wallet['redCgs'] -= 25
            self.game.wallet['blueCogs'] -= 25

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Rubik(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Rubik')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'cogs', 100], ['purchase', 'redCogs', 50], ['purchase', 'blueCogs', 25]],
            3: [['purchase', 'cogs', 50], ['purchase', 'fairyBreads', 25], ['floor', 'rubiks', 20]]
        }

        self.dialogue = {
            '0': ['Oh my lordy! What have I created?! I just wanted to make a puzzle toy and now this whole world has been brought into existence!',
                  'By golly, I\'ll be following you back to the lobby methinks.'],

            '1': ['Wow! Thanks for helping me get out of there! This hotel really has some strange things going on.',
                  'I was just building toys out of little colourful cogs and BAM!',
                  'I\'ve got a lil\' nugget of information for you if you bring me a few colourful cogs though!'],

            '2': ['Pssst...',
                  'Don\'t go telling anyone, but I actually created this slice on purpose. I was trying to get away from Hilbert and got stuck.',
                  'He was doing some really weird stuff before you arrived and all of us on the concierge team are very suspicious.',
                  'He was hanging out on his penthouse floor for days, and I think he has created something terribly scary.',
                  'Just be a bit careful pls.'],

            '3': ['With your altrustic gifts, I have a newfound sense of bravery that came out of nowhere!',
                  'If you decide to take down Hilbert, I will stand with you.']}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Rubik'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 100
            self.game.wallet['redCogs'] -= 50
            self.game.wallet['blueCogs'] -= 25

        elif key == 3 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 50
            self.game.wallet['fairyBreads'] -= 25

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Cantor(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Cantor')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [],
            3: [],
            4: [['floor', 'infinite', 30]]
        }

        self.dialogue = {
            '0': ['Well by golly, I\'m lost in the infinite.',
                  'I keep going through my \'infinite\' portal but it never takes me back to the lobby like it should!',
                  'What\'s that you say? Just go through the other portal?! Nonsense!'],

            '1': ['Yeah okay you were right...',
                  'That really is the best way back to the lobby.'],

            '2': ['This is my creation: The Infinite.',
                  'Any slice of the Hotel that you have even partially explored exists in here.',
                  'And every time you enter it, you go back to floor one. So you must climb up it all every time.',
                  'All the first floors are a little strange, have you noticed how these Gun Guys never attack you there?'],

            '3': ['The Infinite is quite nifty! When you enter here with a bunch of stuff, you are not at risk of losing it, only items you found in here will disappear.',
                  'And if you die, you only lose half of what you have collected!',
                  'You could always come back to the lobby from any of the floors and save it all, but if you were a true madlad you would keep going until you die.',
                  'If you make it past floor 30, you will have earned my respect. How good is that, the respect of a guy you\'ve never met before!',
                  f'The furthest you have made it through The Infinite is to Floor {self.game.infinite_floor_max}.'],

            '4': ['You did it, woo! My respect is now yours!',
                  f'The furthest you have made it through The Infinite is to Floor {self.game.infinite_floor_max}.']}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Cantor'] = True

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Melatos(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Melatos')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'eyes', 25]],
            3: [['floor', 'aussie', 10], ['purchase', 'wings', 25], ['purchase', 'heartFragments', 10]],
            4: [['floor', 'aussie', 15], ['purchase', 'fairyBreads', 50]],
            5: [['purchase', 'boxingGloves', 25], ['purchase', 'fairyBreads', 25]]
        }

        self.dialogue = {
            '0': ['G\'day champ! I\'ve gone and found myself stuck in what appears to be stereotypical Australia.',
                  'I will be following you out of here I think.'],

            '1': ['Damn, now that I am out of there I\'m getting really peckish.',
                  'Can you bring me something to eat?'],

            '2': ['EW! No! I am not eating eyes, I\'m not Hilbert...',
                  'Something MUCH more tasy, and Australian would be a win.',
                  'I was just thinking that world isn\'t actually Australian enough, when I heard some lil cuties scurrying around!',
                  'Can you explore it a bit for me, you should be able to find some prickly friends!',
                  '(Also snacks pls)'],

            '3': ['You absolutely cannot be serious? I am also not eating hearts and wings, you really have been spending too much time with Hilbert!',
                  'Anyway, I saw a cute little friend through the portal, have you seen one yet?',
                  'Keep exploring and I bet there are even more!',
                  'Also bring me actual food please I beg you.'],

            '4': ['YESSS!! This is absolutely delicious oh my god. Fairy Bread, Echidnas AND Kangaroos! :O'],

            '5': ['Also...',
                  'I heard rumors of a huge number of guests arriving soon, apparently each with an infinitely long, unique name. I\'m not really sure why this matters but ever since this anouncement, Hilbert has been all up in arms.',
                  'You have earned my respect, mate. My fairy bread and I will be with you \'til the end.']}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Melatos'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['eyes'] -= 25

            self.game.available_enemy_variants['aussie'].append(20)
            self.game.available_enemy_variants['aussieWeights'].append(2)

        elif key == 3 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['wings'] -= 25
            self.game.wallet['heartFragments'] -= 10

            self.game.available_enemy_variants['aussie'].append(19)
            self.game.available_enemy_variants['aussieWeights'].append(2)

        elif key == 4 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['fairyBreads'] -= 50

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Webster(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Webster')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'purpleCogs', 5]],
            3: [['purchase', 'purpleCogs', 10]],
            4: [['purchase', 'purpleCogs', 15]]
        }

        self.dialogue = {
            '0': ['WAIT!!!',
                  'Be careful about heading into space! Some of the bad guys out there are... out-of-this-world strong!',
                  'Haha! Get it?'],

            '1': ['Anyway, surely by now you\'ve realised that Hilbert is up to no good. For some sweet sweet purple cogs, I\'ll give you some more goss.'],

            '2': ['As you probably know, these so-called \'Gun Guys\' never seem to attack you on floor 1 of any part of the Hotel.',
                  'What you may not know, is that they\'re not the bad guys at all, in fact they\'re the Hotel\'s security personnel!',
                  'They can only communicate within a slice of the Hotel and so just leave you alone if they dont know about you.'],

            '3': ['So you may be thinking, \'well then, all of these monsters must be the ones attacking the hotel\' and youd be wrong too, silly.',
                  'They\'re the Hotel\'s GUESTS! They just have very well-suited rooms catered to their specific needs.'],

            '4': ['I\'m not sure why, but Hilbert has hired you to kill all of his security AND his guests.',
                  'There isn\'t anyone attacking this Hotel at all!',
                  'I don\'t know what he\'s planning, but you\'re in too deep now, you musn\'t tell him anything! Play along for now or he will kill every living thing in here, I know he has the power to do so.',
                  'When the time comes, I will stand with you.']}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Webster'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['purpleCogs'] -= 5

        elif key == 3 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['purpleCogs'] -= 10

        elif key == 4 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['purpleCogs'] -= 15

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Barad(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Barad')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'redOrbs', 10], ['floor', 'heaven_hell', 10]],
            3: [['purchase', 'yellowOrbs', 10], ['floor', 'heaven_hell', 15]],
            4: [['purchase', 'yellowOrbs', 25], ['purchase', 'redOrbs', 25], ['purchase', 'purpleCogs', 25]],
        }

        self.dialogue = {
            '0': ['Hello stranger! Welcome to the most powerful slice in the Hotel.'],

            '1': ['I believe this is where Hilbert wants to draw power from to create his weapon. Inside exists the power of the gods.',
                  'But what he wants to do is truly evil and we must not let him complete it.',
                  'Please do not bring him the real power of the Orbs, bring fake ones or something idk.',
                  'But if you bring me some, I will be able to fight him with you, armed with this true power.'],

            '2': ['Mmmm yes. I can feel the power of the devils in these.',
                  'You have defeated a devil, incredible work!',
                  'I will also need the power of a god too.'],

            '3': ['Mmmm yes muy bien. These are brilliant thank you.',
                  'You have defeated a god, you can truly do anythng.',
                  'I only need a few more and then I will fight him with you.'],

            '4': ['Brilliant work! I am ready to fight. He will be at his weakest near his weapon. We can use it against him.',
                  'But you musn\'t let him know. Ease him into a false sense of security, and then BAM! We give him the biggest smackaroo of his life!'],}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Barad'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['redOrbs'] -= 10

        elif key == 3 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['yellowOrbs'] -= 10

        elif key == 4 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['yellowOrbs'] -= 25
            self.game.wallet['redOrbs'] -= 25
            self.game.wallet['purpleCogs'] -= 25

        self.game.dialogue_history[self.name][str(key) + 'said'] = True


class Watson(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Watson')

        self.currency_requirements = {
            0: [],
            1: [],
            2: [['purchase', 'credits', 5]],
            3: [['purchase', 'credits', 5]],
            4: [['purchase', 'credits', 5]]
        }

        self.dialogue = {
            '0': ['Woah hey hi!',
                  'I been sitting down here so long it\'s been ages since I\'ve seen anyone!',
                  'I have some reeeaaallly top secret information for you... for a price.',
                  'It\'s worth it, I promise, I was told this by God!'],

            '1': ['Gimme CREDIT!! Mmmm gobble gobble gobble yummy I just love credit!',
                  'Uh I mean credits, yeah, the currency.'],

            '2': ['So... The first, and most important piece of information:',
                  'I hear this "world" was created by another being and is called a "game". Here are God\'s words:',
                  'Created By: Alex Hopper',
                  'Yummy yummy gimme more credits for more!'],

            '3': ['God also says:',
                  'Playtested by: Eloisa Perez-Bennetts.',
                  'Yummy yooo, more credits pleeeease!'],

            '4': ['Yeah just kidding, no more words of God.',
                  'But, if you want to be mentioned by God, this "game" is still in playtest so let him know what you think!',
                  'Pretty please.']}

    def conversation_action(self, key):
        # Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.characters_met['Webster'] = True

        elif key == 2 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['purpleCogs'] -= 5

        elif key == 3 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['purpleCogs'] -= 10

        elif key == 4 and not self.game.dialogue_history[self.name][str(key) + 'said']:
            self.game.wallet['purpleCogs'] -= 15

        self.game.dialogue_history[self.name][str(key) + 'said'] = True
