from scripts.entities import *
  
class Character(physicsEntity):
    def __init__(self, game, pos, size, name):
        
        super().__init__(game, name.lower(), pos, size)
        self.type = name.lower()
        self.name = name

        self.walking = 0
        self.flip_x = True if random.random() < 0.5 else False
        self.canTalk = True
        self.newDialogue = False
        self.gravityAffected = True

        self.currentDialogueIndex = 0

        #To allow different trades at the same time to be green or red depending on wallet/succes. 
        #Needs to be as long as the longest character trade.
        self.currentTradeAbility = [False, False, False]


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
                self.walking = 0
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
            
            try:
                requirementNum = len(self.currencyRequirements[self.currentDialogueIndex + 1])
            except KeyError:
                requirementNum = 0

            xpos = 2 * (self.pos[0] - self.game.render_scroll[0] + self.anim_offset[0] + 7)
            ypos = 2 * int(self.pos[1] - self.game.render_scroll[1] + self.anim_offset[1]) - 30
            offsetLength = 80

            if requirementNum > 0:
                    offsetN = 0
                    for i, requirement in enumerate(self.currencyRequirements[self.currentDialogueIndex + 1]):
                        #Display requirements above character:
                        self.game.HUDdisplay.blit(self.game.displayIcons[requirement[1]], (xpos - (requirementNum * offsetLength) / 2 + offsetN * offsetLength + 10, ypos))
                        colour = (0,150,0) if self.currentTradeAbility[i] else (150,0,0)
                        self.game.draw_text(str(requirement[2]), (xpos + 30 - (requirementNum * offsetLength) / 2 + offsetN * offsetLength + 10, ypos - 2), self.game.text_font, colour, (0, 0), mode = 'left', scale = 0.75)
                        offsetN += 1
            
            elif distToPlayer >= 15 and self.newDialogue:
                self.game.draw_text('(!)', (xpos, ypos - (15 if requirementNum else -15)), self.game.text_font, (255, 255, 255), (0, 0), mode = 'center', scale = 0.75)

            if distToPlayer < 15:
                self.game.draw_text('(z)', (xpos, ypos - (15 if requirementNum else -15)), self.game.text_font, (255, 255, 255), (0, 0), mode = 'center', scale = 0.75)
                if self.game.interractionFrameZ and not self.game.dead:
                    self.game.run_text(self)


            
    def getConversation(self):
        self.game.update_dialogues()
        dialogue = self.game.dialogueHistory[self.name]
        
        for index in range(int(len(dialogue) / 2)):
            available = dialogue[str(index) + 'available']
            said = dialogue[str(index) + 'said']
            

            if not available:
                return(self.dialogue[str(index - 1)], index - 1)
            
            elif available and not said:
                return(self.dialogue[str(index)], index)
        
        index = int(len(dialogue) / 2) - 1
        return(self.dialogue[str(index)], int(index))

    def render(self, surface, offset = (0, 0)):
        super().render(surface, offset = offset)
        if self.game.caveDarkness:
            self.game.darknessCircle(0, 50, (int(self.pos[0]) - self.game.render_scroll[0] + self.size[0] / 2, int(self.pos[1]) - self.game.render_scroll[1] + self.size[1] / 2))


class Hilbert(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Hilbert')

        self.currencyRequirements = {
            0: [],
            1: [],
            2: [['purchase', 'cogs', 5]],
            3: [],
            4: [['purchase', 'cogs', 50]],
            5: [['purchase', 'cogs', 100]],
            6: [['purchase', 'cogs', 150]],
            7: [['purchase', 'eyes', 30]],
            8: [['purchase', 'redCogs', 5]]
        }

        self.dialogue = {
            '0': ['Oh no! My hotel was attacked! The whole thing has collapsed into the ground!',
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
                  
            '8': ['Spiffo youngster!! Thanks a bunch!']}


    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.

        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.dialogueHistory[self.name]['1available'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.enemyCountMax = 5
            self.game.currentLevelSize = 20
            self.game.wallet['cogs'] -= 5

        elif key == 4 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.enemyCountMax = 10
            self.game.currentLevelSize = 28
            self.game.wallet['cogs'] -= 50

            self.game.availableEnemyVariants['normal'].append(4)
            self.game.availableEnemyVariants['normalWeights'].append(1)
            
        elif key == 5 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.enemyCountMax = 20
            self.game.currentLevelSize = 35
            self.game.wallet['cogs'] -= 100

        elif key == 6 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.enemyCountMax = 25
            self.game.currentLevelSize = 40
            self.game.wallet['cogs'] -= 150

        elif key == 7 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.enemyCountMax = 30
            self.game.currentLevelSize = 45
            self.game.wallet['eyes'] -= 30
            self.game.difficulty += 1

        elif key == 8 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.enemyCountMax = 35
            self.game.currentLevelSize = 50
            self.game.wallet['purpleCogs'] -= 5

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True


class Noether(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Noether')

        self.currencyRequirements = {
            0: [],
            1: [],
            2: [['purchase', 'heartFragments', 5]],
            3: [['purchase', 'heartFragments', 20]],
            4: [['purchase', 'heartFragments', 50]],
            5: [['purchase', 'heartFragments', 100]]
        }

        self.dialogue = {
            '0': ['Oh by golly gosh am I lost! Do you know the way back to the lobby?',
                    'Brilliant, cheers Ill follow you back!'],

            '1': ['Oh yeah by the way I\'m also quite useful \'round here.',
                  'I can make you extra hearts! I just need a few Heart Fragments!',
                  'Bring me 5 and the heart is yours!'],

            '2': ['You\'ve got two hearts! Woo!',
                    'Ew, these things are disgusting... and still beating! EW!',
                    'Hearts are super useful! If you run out, you\'ll lose a quarter of everything :( I\'ll give ya another for 20 fragments.'],

            '3': ['You\'ve got three hearts! Woo!',
                    'Look at you go, youll be a cat in no time!',
                    'Keep \'em comin\' please.'],

            '4': ['You\'ve got four hearts! Woo!',
                    'Did you know that hagfish also have four hearts?',
                    'I\'ve only got one more, sorry!'],
                     
            '5': ['You\'ve got five hearts! Woo!',
                  'Similarly, earthworms also have five!',
                  'Sorry chief! All out of hearts for now :('] }


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

        self.currencyRequirements = {
            0: [],
            1: [],
            2: [['purchase', 'wings', 20]],
            3: [['purchase', 'wings', 35]],
            4: [['purchase', 'wings', 50]]
        }

        self.dialogue = {
            '0': ['Oh by golly gosh am I lost! Do you know the way back to the lobby?',
                    'Brilliant, cheers I\'ll follow you back!'],

            '1': ['Oh yeah by the way I\'m also quite useful \'round here.',
                  'I can make you winged boots! They let you jump more in the air!',
                  'I just need a few bat wings! Bring me 20 and the extra jump is yours!'],

            '2': ['You\'ve got two jumps! Woo! Isn\'t this such a novel mechanic?',
                    'I\'ll give ya another for 35 wings.'],

            '3': ['You\'ve got three jumps! Woo! We\'re really pushing this double jump idea.',
                    'I\'ll give ya another for 50 wings.'],
            
            '4': ['You\'ve got four jumps! Woo! How many is too many?',
                  'Sorry chief! All out of boots for now.']}

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Curie'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 20

        elif key == 3 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 35

        elif key == 4 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.player.total_jumps += 1

            self.game.wallet['wings'] -= 50

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True



class Planck(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Planck')


        self.currencyRequirements = {
            0: [],
            1: [],
            2: [['purchase', 'heartFragments', 5]]
        }

        self.dialogue = {
            '0': ['Oh by golly gosh am I lost! Do you know the way back to the lobby?',
                    'Brilliant, cheers I\'ll follow you back!'],

            '1': ['Oh yeah by the way I\'m also quite useful \'round here.',
                  'I can make you temporary hearts! They will only last until you get hit.',
                  'They\'re each yours for just 5 heart fragments!'],

            '2': ['Here\'s a temporary heart!',
                    'Don\'t go losing it all at once!']}

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Planck'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.wallet['heartFragments'] -= 5
            self.game.temporaryHealth += 1

        if key != 2:
            self.game.dialogueHistory[self.name][str(key) + 'said'] = True


class Faraday(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Faraday')


        self.currencyRequirements = {
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
                  'The hotel is much bigger than you think. There are infinite dimensions stacked side by side and some of them get... weird.',
                  'Bring me 100 cogs and I\'ll show you one.'],

            '2': ['Amazing, I\'ll build another elevator for you! It will be ready next time you come back to the lobby.',
                  'I\'ll hide it here so Hilbert wont see it! Give me a jiffy and it\'ll be ready!'],

            '3': ['I\'ve seen so many parts to this hotel but since the attack I can\'t get to most of them! They\'ve all been sealed off but I managed to scrape this portal together.',
                  'This one is very basic, but be warned, some you wont like. And the monsters... you\'ll need to get stronger to face them.']}

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.

        if key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 100
            self.game.portalsMet['grass'] = True

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True


class Lorenz(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Lorenz')


        self.currencyRequirements = {
            0: [],
            1: [],
            2: [],
            3: [['prime', 'cogs', 'P']],
            4: [['primePurchase', 'cogs', 'P>50', 50]],
            5: [['primePurchase', 'cogs', 'P>200', 200]],
            6: [['prime', 'redCogs', 'P'], ['prime', 'blueCogs', 'P']],
            7: [['floor', 'spooky', 20], ['floor', 'rubiks', 20], ['floor', 'grass', 20]]
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

            '2': ['Hammers are super useful for smashing walls that are already down on their luck by being structurally unsound.',
                  'But I aint a fan of the normal \'pay this much for this hammer\' boring shenanigans, I only like prime numbers!',
                  'Bring me EXACTLY a prime number of cogs and a hammer is yours!'],

            '3': ['Hammer go smash!',
                  'Oh and also, youll never lose hammers on death! WOO!',
                  'I got more too! But this time you gotta bring me a prime number of cogs OVER 50!'],
                  
            '4': ['Hammer go smash!',
                  'I got more too! But this time you gotta bring me a prime number of cogs OVER 200!'],

            '5': ['Hammer go smash!',
                  'I have another hammer, but now I want a prime number of a couple types of special cogs pls!'],
                  
            '6': ['Hammer go SMASH!',
                  'I only have one more hammer, now can you reach the 20th floor on each of these three areas?'],
                  
            '7': ['Hammer go SMASH!!',
                  'WOO! No more hammers well done!!']}

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Lorenz'] = True

        if key in [3, 4, 5] and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currencyEntities.append(Currency(self.game, 'hammer', self.game.player.pos))
            self.game.wallet['cogs'] = 0

        if key == 6 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currencyEntities.append(Currency(self.game, 'hammer', self.game.player.pos))
            self.game.wallet['redCogs'] = 0
            self.game.wallet['blueCogs'] = 0

        if key == 7 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currencyEntities.append(Currency(self.game, 'hammer', self.game.player.pos))
        
        self.game.dialogueHistory[self.name][str(key) + 'said'] = True


class Franklin(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Franklin')

        self.currencyRequirements = {
            0: [],
            1: [],
            2: [['purchase', 'chitins', 50]],
            3: [['purchase', 'chitins', 100]],
            4: [['purchase', 'chitins', 200]]
        }

        self.dialogue = {
            '0': ['Oopsie doopsie I got myself all stuck in this creepy as hell house. Do you know the way out?',
                    'Brilliant, cheers I\'ll follow you back!'],

            '1': ['Oh yeah by the way I\'m likely the most useful in these here parts.',
                  'I can tippity tap into your own DNA and make you stronger. There\'s this nifty stuff called chitin that I can use to reinforce you!',
                  'Bring me 50 chitin and I\'ll make you stronger!'],

            '2': ['Yay woo! Your power level is now 2!',
                    'I\'ll give ya another for 100 chitin.'],

            '3': ['Yay woo! Your power level is now 3!',
                    'I\'ll give ya another for 200 chitin.'],
            
            '4': ['Yay woo! Your power level is OVER 3!',
                  'But I\'m sorry chief! All out of upgrades for now.']}

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Franklin'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.powerLevel += 1

            self.game.wallet['chitins'] -= 50

        elif key == 3 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.powerLevel += 1

            self.game.wallet['chitins'] -= 100

        elif key == 4 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.powerLevel += 1

            self.game.wallet['chitins'] -= 200

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True
            

class Rubik(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Rubik')

        self.currencyRequirements = {
            0: [],
            1: [],
            2: [['purchase', 'cogs', 100], ['purchase', 'redCogs', 50], ['purchase', 'blueCogs', 25]]
        }

        self.dialogue = {
            '0': ['Oh my lordy! What have I created?! I just wanted to make a puzzle toy and now this whole world has been brought into existence!',
                    'By golly, I\'ll be following you back to the lobby methinks.'],

            '1': ['Wow! Thanks for helping me get out of there! This hotel really has some strange things going on.',
                  'I was just building toys out of little colourful cogs and BAM!',
                  'I\'ve got a little something for you if you bring me a few colourful cogs though!'],

            '2': ['TEMPORARY ENDGAME',
                  'WELL DONE YOU DID IT!']}

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Rubik'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.wallet['cogs'] -= 100
            self.game.wallet['redCogs'] -= 50
            self.game.wallet['blueCogs'] -= 25

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True


class Cantor(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Cantor')

        self.currencyRequirements = {
            0: [],
            1: [],
            2: []
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
                  'However it is quite nifty! When you enter here with a bunch of stuff, you are not at risk of losing it, only items you found in here will disappear.',
                  'And if you die, you only lose half of what you have collected!',
                  'You could always come back to the lobby from any of the floors and save it all, but if you were a true madlad you would keep going until you die.',
                  f'The furthest you have made it through The Infinite is to Floor {self.game.infiniteFloorMax}.']}

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Cantor'] = True

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True

    
    
class Melatos(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Melatos')

        self.currencyRequirements = {
            0: [],
            1: [],
            2: [['purchase', 'eyes', 25]],
            3: [['floor', 'aussie', 15], ['purchase', 'wings', 25], ['purchase', 'heartFragments', 10]],
            4: [['floor', 'aussie', 20], ['purchase', 'fairyBreads', 50]]
        }

        self.dialogue = {
            '0': ['G\'day champ! I\'ve gone and found myself stuck in what appears to be stereotypical Australia.',
                    'I will be following you out of here I think.'],

            '1': ['Damn, now that I am out of there I\'m getting really peckish.',
                  'Can you bring me something to eat?'],

            '2': ['EW! No! I am not eating eyes, I\'m not Hilbert...',
                    'Something MUCH more tasy, and Australian would be a win.',
                    'I was just thinking that world isn\'t actually Australian enough, when I heard some lil cuties scurrying around!',
                    'Can you explore it a bit for me, you should be able to find some prickly friends!'
                    '(Also snacks pls)'],

            '3': ['You absolutely cannot be serious? I am also not eating hearts and wings, you really have been spending too much time with Hilbert!',
                    'Anyway, I saw a cute little friend through the portal, have you seen one yet?',
                    'Keep exploring and I bet there are even more!',
                    'Also bring me actual food please I beg you.'],
            
            '4': ['YESSS!! This is absolutely delicious oh my god. Fairy Bread, Echidnas AND Kangaroos! :O']}

    def conversationAction(self, key):
        #Runs when dialogue matching key is said for thr first time.
        if key == 0 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.charactersMet['Melatos'] = True

        elif key == 2 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.wallet['eyes'] -= 25

        elif key == 3 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.wallet['wings'] -= 25
            self.game.wallet['heartFragments'] -= 10

            self.game.availableEnemyVariants['aussie'].append(19)
            self.game.availableEnemyVariants['aussieWeights'].append(2)

        elif key == 4 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.wallet['fairyBreads'] -= 50

            self.game.availableEnemyVariants['aussie'].append(20)
            self.game.availableEnemyVariants['aussieWeights'].append(2)

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True