#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# baqueta: link
# https://pixabay.com/p-149338/?no_redirect

import Leap, sys, thread
import os, time, pygame
from pygame.locals import *
from pygame.compat import geterror
import pygbutton

if not pygame.font: print ('Warning, fonts disabled')
if not pygame.mixer: print ('Warning, sound disabled')

main_dir = os.path.split(os.path.abspath(__file__))[0]
image_dir = os.path.join(main_dir, 'data/images')
sound_dir = os.path.join(main_dir, 'data/sounds')

#inputDevice = pygame.mouse

#functions to create our resources
def loadImage(name, colorkey=None):
    fullname = os.path.join(image_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print ('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

def loadSound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join(sound_dir, name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error:
        print ('Cannot load sound: %s' % fullname)
        raise SystemExit(str(geterror()))
    return sound

def changeVolumeSounds(instruments, option):
    if option == 0:
        volume = 0.1
    elif option == 1:
        volume = 0.5
    elif option == 2:
        volume = 1
    else:
        raise ValueError("Volume option not 0, 1 or 2")

    for i in instruments:
        i.sound.set_volume(volume)

#classes for our game objects
class Stick(pygame.sprite.Sprite):
    """moves a stick on the screen, following the tool detected by the Leap"""
    controller = None
    lastID = 0
    def __init__(self, imageName):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect = loadImage(imageName,-1)
        self.kicking = False
        self.idTool = Stick.lastID
        Stick.lastID += 1
        self.visible = False

    def update(self):
        "move the stick based on the tool position"
        if Stick.controller.sticksPosition[self.idTool]:
            self.rect.midtop  = Stick.controller.sticksPosition[self.idTool]
            self.visible = True
        else:
            self.visible = False
        if self.kicking:
            pass
            #PRINT FLASH
            #self.rect.move_ip(5, 10)

    def kick(self, targets):
        "returns the target that the stick collides with"
        if not self.kicking:
            self.kicking = True
            # hitbox = self.rect.inflate(-5, -5)
            hitbox = self.rect
            for target in targets:
                if hitbox.colliderect(target.rect):
                    target.kicked()
                    return target
            else:
                return None

    def unkick(self):
        "called to pull the stick back"
        self.kicking = False

class Instrument(pygame.sprite.Sprite):
    controller = None
    def __init__(self,imageName,sound,topleft):
        pygame.sprite.Sprite.__init__(self) #call Sprite intializer
        self.image, self.rect = loadImage(imageName,-1)
        self.original = self.image.copy()
        self.sound = sound
        self.rect.topleft = topleft
        self.kicking = False

    def update(self):
        self.image = self.original

        if (Instrument.controller.sticksPosition[0] and
                self.rect.collidepoint(Instrument.controller.sticksPosition[0])
                ) or (Instrument.controller.sticksPosition[1] and
                self.rect.collidepoint(Instrument.controller.sticksPosition[1]) ):
            self.image = pygame.transform.smoothscale(self.image,
                (int(self.original.get_height()*1.1),
                int(self.original.get_width()*1.1)))

        if self.kicking:
            self.image = pygame.transform.flip(self.image, 1, 1)

    def kicked(self):
        if not self.kicking:
            self.kicking = True
            self.sound.play()

    def unkicked(self):
        self.kicking = False

    def play(self):
        self.sound.play()

class Button(pygame.sprite.Sprite):
    controller = None
    def __init__(self,imagename,text,topleft=(0,0),center=None,hoverable=True):
        pygame.sprite.Sprite.__init__(self) #call Sprite intializer
        self.image, self.rect = loadImage(imagename,-1)

        if center:
            self.rect.center = center
        else:
            self.rect.topleft = topleft
        #self.kicking = 0

        font = pygame.font.Font(None, 20)
        self.text = font.render(text, 1, (255, 255, 255))
        self.hoverable = hoverable
        self.textpos = self.text.get_rect(centerx=self.image.get_width()/2,
            centery=self.image.get_height()/2)
        self.image.blit(self.text, self.textpos)

        self.original = self.image.copy()

        self.hovered = False
        self.starthovering = None
        self.speedhovering = 60
        self.hoveringended = False
        self.is_enable = False

    def update(self):
        self.image = self.original.copy()

        if self.is_enable:
            self.image.fill((0,100,0))
            self.image.blit(self.text, self.textpos)

        if Button.controller.sticksPosition[0] is None:
            pos = (0,0)
        else:
            pos = Button.controller.sticksPosition[0]

        if self.hoverable and self.rect.collidepoint(pos):
            if self.hovered:
                timepast = time.time() - self.starthovering
            else:
                timepast = 0
                self.hovered = True
                self.starthovering = time.time()

            self.image.fill((0,100,0),self.image.get_rect().inflate(-100+(timepast*self.speedhovering),-15))
            self.image.blit(self.text, self.textpos)

            if timepast*self.speedhovering > self.image.get_width()-22:
                self.hoveringended = True
                self.hovered = False
        else:
            self.hovered = False

    def enable(self):
        self.is_enable = True

    def disable(self):
        self.is_enable = False

# Leap Motion controller class
class DataController:
    def __init__(self, controller,app_width,app_height):
        self.controller = controller
        self.app_width = 800
        self.app_height = 600
        self.lastFrame = None
        self.lastFrameID = 0
        self.lastProcessedFrameID = 0
        self.detectedGesture = False
        self.sticksPosition = [None,None]
        self.sticksDirection = [None,None]

        self.controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);

    #def get_pos(self):
    #    return self.sticksPosition

    def map2Dcoordinates(self,pointable,frame):
        #if self.lastFrame and self.lastFrame.pointables:
        iBox = frame.interaction_box
        leapPoint = pointable.stabilized_tip_position
        normalizedPoint = iBox.normalize_point(leapPoint, False)

        app_x = normalizedPoint.x * self.app_width
        # app_y = (1 - normalizedPoint.y) * app_height
        app_y = (normalizedPoint.z) * self.app_height
        #The z-coordinate is not used
        pos = (app_x, app_y)
        return pos
        #else:
        #    return (0,0)

    def processNextFrame(self):
        frame = self.controller.frame()

        if frame.id == self.lastFrameID:
            return
        if frame.is_valid:
            i = 0
            for tool in frame.tools:
                self.sticksPosition[i] = self.map2Dcoordinates(tool,frame)
                self.sticksDirection[i] = tool.direction
                i += 1
                if i == 2:
                    break
            for j in range(i,2):
                self.sticksPosition[j] = None
                self.sticksDirection[j] = None

            if self.lastFrame:
                #print self.lastFrameID, frame.id
                gestures = frame.gestures(self.lastFrame)
                #print len(gestures)
                for gesture in gestures:
                    # Key tap
                    if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                        self.detectedGesture = True
            else:
                self.detectedGesture = None

        self.lastFrame = frame
        self.lastFrameID = frame.id

def main():
    """this function is called when the program starts.
       it initializes everything it needs, then runs in
       a loop until the function returns."""
#Initialize Everything
    pygame.init()
    screen_with = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_with, screen_height))
    pygame.display.set_caption('Drums')
    # pygame.mouse.set_visible(0)
    controller = Leap.Controller()
    dataController = DataController(controller,screen_with,screen_height)
    Stick.controller = dataController
    Instrument.controller = dataController
    Button.controller = dataController

    # if dataController.controller.is_connected:
        # global inputDevice
        # inputDevice = dataController
    # global inputDevice
    # inputDevice = dataController

#Create The Backgound
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

#Put Text On The Background, Centered
    if pygame.font:
        font = pygame.font.Font(None, 36)
        text = font.render("Virtual drums", 1, (255, 255, 255))
        textpos = text.get_rect(centerx=background.get_width()/2,centery=30)
        background.blit(text, textpos)

#Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()

#Prepare Game Objects
    clock = pygame.time.Clock()

    stick1 = Stick('stick1.png')
    stick2 = Stick('stick2.png')
    # stick = Stick(dataController)
    # stick = Stick(inputDevice)

    #Start Screen
    buttonStart = Button('button.bmp','Start',
        center=(5*screen_with/10, 5*screen_height/10))

    spritesStartScreen = pygame.sprite.OrderedUpdates(buttonStart,stick1)

    #Drums Screen
    buttonOptions = Button('button.bmp','Options',
        (4*screen_with/5, 3*screen_height/20))

    #battery A
    snare = Instrument('snare.bmp',loadSound('snare-acoustic01.wav'),
        (1*screen_with/5, 3*screen_height/5))

    instrumentsBatteryA = [snare]
    spritesBatteryA = pygame.sprite.OrderedUpdates()
    spritesBatteryA.add(*instrumentsBatteryA)
    spritesBatteryA.add(buttonOptions)

    #battery B
    floortom = Instrument('floortom.bmp', loadSound('floortom-acoustic01.wav'),
        (3*screen_with/5, 3*screen_height/5))

    instrumentsBatteryB = [floortom]
    spritesBatteryB = pygame.sprite.OrderedUpdates()
    spritesBatteryB.add(*instrumentsBatteryB)
    spritesBatteryB.add(buttonOptions)

    #Options Screen
    buttonBackToDrums = Button('button.bmp','Back',
        (4*screen_with/5, 1*screen_height/20))
    buttonSetVolume = Button('button.bmp','Volume',
        center=(2*screen_with/10, 2*screen_height/10), hoverable=False)
    buttonVolume0 = Button('button.bmp','Low',
        center=(4*screen_with/10, 2*screen_height/10))
    buttonVolume1 = Button('button.bmp','Medium',
        center=(6*screen_with/10, 2*screen_height/10))
    buttonVolume2 = Button('button.bmp','High',
        center=(8*screen_with/10, 2*screen_height/10))
    buttonSetBattery = Button('button.bmp','Battery',
        center=(2*screen_with/10, 4*screen_height/10), hoverable=False)
    buttonBatteryA = Button('button.bmp','Battery A',
        center=(4*screen_with/10, 4*screen_height/10))
    buttonBatteryB = Button('button.bmp','Battery B',
        center=(6*screen_with/10, 4*screen_height/10))

    spritesOptionsScreen = pygame.sprite.OrderedUpdates()
    spritesOptionsScreen.add(buttonBackToDrums,buttonSetVolume,
        buttonVolume0,buttonVolume1,buttonVolume2,
        buttonSetBattery,buttonBatteryA,buttonBatteryB)

#Main Loop
    going = True
    current_screen = "drumsScreen"
    currentInstruments = instrumentsBatteryA
    allInstruments = instrumentsBatteryA + instrumentsBatteryB
    spritesDrumsScreen = spritesBatteryA
    buttonVolume1.enable()
    buttonBatteryA.enable()
    instrument_kicked = None
    while going:
        clock.tick(60)
        dataController.processNextFrame()

        currentSticks = pygame.sprite.OrderedUpdates(stick1,stick2)

        if current_screen == "startScreen":
            if buttonStart.hoveringended:
                current_screen = "drumsScreen"
                buttonStart.hoveringended = False
        elif current_screen =="drumsScreen":
            if buttonOptions.hoveringended:
                current_screen = "optionsScreen"
                buttonOptions.hoveringended = False

            if dataController.detectedGesture:
                instrument_kicked = stick1.kick(currentInstruments)
            else:
                stick1.unkick()
                if instrument_kicked:
                    instrument_kicked.unkicked()
                    instrument_kicked = None
                #for instrument in currentInstruments:
                #    instrument.unkicked()
            dataController.detectedGesture = False
        elif current_screen == "optionsScreen":
            if buttonBackToDrums.hoveringended:
                current_screen = "drumsScreen"
                buttonBackToDrums.hoveringended = False

            if buttonVolume0.hoveringended:
                buttonVolume0.hoveringended = False
                buttonVolume0.enable()
                buttonVolume1.disable()
                buttonVolume2.disable()
                changeVolumeSounds(allInstruments,0)
            elif buttonVolume1.hoveringended:
                buttonVolume1.hoveringended = False
                buttonVolume1.enable()
                buttonVolume0.disable()
                buttonVolume2.disable()
                changeVolumeSounds(allInstruments,1)
            elif buttonVolume2.hoveringended:
                buttonVolume2.hoveringended = False
                buttonVolume2.enable()
                buttonVolume0.disable()
                buttonVolume1.disable()
                changeVolumeSounds(allInstruments,2)
            elif buttonBatteryA.hoveringended:
                buttonBatteryA.hoveringended = False
                buttonBatteryA.enable()
                buttonBatteryB.disable()
                spritesDrumsScreen = spritesBatteryA
                currentInstruments = instrumentsBatteryA
            elif buttonBatteryB.hoveringended:
                buttonBatteryB.hoveringended = False
                buttonBatteryB.enable()
                buttonBatteryA.disable()
                spritesDrumsScreen = spritesBatteryB
                currentInstruments = instrumentsBatteryB

        #Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                going = False
            elif event.type == KEYDOWN and (event.key == K_ESCAPE or event.key == K_q):
                going = False

        currentSticks.update()
        if current_screen == "startScreen":
            spritesStartScreen.update()
        elif current_screen == "drumsScreen":
            spritesDrumsScreen.update()
        elif current_screen == "optionsScreen":
            spritesOptionsScreen.update()

        #print (stick1.rect.midtop, stick2.rect.midtop)
        if stick1.visible == False:
             currentSticks.remove(stick1)
        if stick2.visible == False:
             currentSticks.remove(stick2)

        #Draw Everything
        screen.blit(background, (0, 0))
        if current_screen == "startScreen":
            spritesStartScreen.draw(screen)
        elif current_screen == "drumsScreen":
            spritesDrumsScreen.draw(screen)
        elif current_screen == "optionsScreen":
            spritesOptionsScreen.draw(screen)
        currentSticks.draw(screen)

        pygame.display.flip()

    pygame.quit()

#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    main()
