from scripts.entities import *
       
class Character(physicsEntity):
    def __init__(self, game, pos, size, name):
        
        super().__init__(game, name.lower(), pos, size)
        self.type = name.lower()
        self.name = name

        self.walking = 0
        self.canTalk = True
        self.newDialogue = False
        self.gravityAffected = True

        self.currentDialogueIndex = 0


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

        if self.canTalk:

            distToPlayer = math.dist(self.rect().center, self.game.player.rect().center)
            
            try:
                requirementNum = len(self.currencyRequirements[self.currentDialogueIndex + 1])
            except KeyError:
                requirementNum = 0

            xpos = 2 * (self.pos[0] - self.game.render_scroll[0] + self.anim_offset[0] + 7)
            ypos = 2 * int(self.pos[1] - self.game.render_scroll[1] + self.anim_offset[1]) - 15
            offsetLength = 60

            if requirementNum > 0:
                    offsetN = 0
                    for requirement in self.currencyRequirements[self.currentDialogueIndex + 1]:

                        self.game.HUDdisplay.blit(self.game.currencyIcons[requirement[0]], (xpos - (requirementNum * offsetLength) / 2 + offsetN * offsetLength, ypos - 12))
                        colour = (0,150,0) if self.game.wallet[str(requirement[0])] >= requirement[1] else (150,0,0)
                        self.game.draw_text(str(requirement[1]), (xpos + 45 - (requirementNum * offsetLength) / 2 + offsetN * offsetLength, ypos), self.game.text_font, colour, (0, 0), mode = 'center', scale = 0.75)

                        offsetN += 1

            if distToPlayer < 15:
                self.game.draw_text('(z)', (xpos, ypos - (30 if requirementNum else 0)), self.game.text_font, (255, 255, 255), (0, 0), mode = 'center', scale = 0.75)
                
                if self.game.interractionFrame:
                    self.game.run_text(self)

            elif distToPlayer >= 15 and self.newDialogue:
                self.game.draw_text('(!)', (xpos, ypos - (30 if requirementNum else 0)), self.game.text_font, (255, 255, 255), (0, 0), mode = 'center', scale = 0.75)


                



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
            2: [['cogs', 5]],
            3: [['cogs', 50]],
            4: [['cogs', 100]],
            5: [['cogs', 150]]
        }

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

            '4': ['You know the drill...',
                  'This time I\'ll need 150 cogs.'],
                    
            '5': ['Phenomenal work, my little slave!!',
                  'I dont know what else to do but please keep exploring!']  }


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

        elif key == 5 and not self.game.dialogueHistory[self.name][str(key) + 'said']:
            self.game.currentDifficulty = 75
            self.game.currentLevelSize = 50
            self.game.wallet['cogs'] -= 150

        self.game.dialogueHistory[self.name][str(key) + 'said'] = True


class Noether(Character):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Noether')

        self.currencyRequirements = {
            0: [],
            1: [],
            2: [['heartFragments', 5]],
            3: [['heartFragments', 20]],
            4: [['heartFragments', 50]],
            5: [['heartFragments', 100]]
        }

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
            2: [['wings', 5]],
            3: [['wings', 50]],
            4: [['wings', 100]]
        }

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

            

        

    