from psychopy import visual, core, event, sound, monitors
from EyeLinkCoreGraphicsPsychoPyAnimatedTarget_Other import EyeLinkCoreGraphicsPsychoPy
import numpy as np
import cv2, pygame
import pickle
import random
import itertools
import csv
import time, subprocess
from py.path import local
import glob
import os
import pylink
import pandas
from ffprobe import FFProbe
# import TheMainOrderAlmostThere_Else
from datetime import datetime
import win32api, win32con, psutil, win32gui


# The mouse will reappear after the subprocess, because it does not recognise the window that is active
# A click brings it back to the window
# Making the click automatic


def click(x, y):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

import logging, numpy, pygame, string, sys, threading
import scipy.optimize
from scipy.stats import norm
from matplotlib import pyplot as plt

################ EYET INFOS ########################
pylink.flushGetkeyQueue()
EDF = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
eye = None  # left ("left") or right ("right") eye used for EyeLink. Used for gaze contingent display
last_ET = 0  # last gaze position
# Getting the radius of the space of the central fixation point
TRACKER_FX_RADIUS = 150

RESOLUTION = [1600, 900]  # [1280,720][1600,900]#

tracker = True
# Set a few task parameters
useGUI = True  # whether use the Psychopy GUI module to collect subject information
dummyMode = not tracker  # If in Dummy Mode, press ESCAPE to skip calibration/validataion

#### SUBJECT INFO: get subject info with GUI ########################################################
expInfo = {'SubjectNO': '00', 'SubjectType': 'Baby', 'SubjectInitials': 'AA'}

if useGUI:
    from psychopy import gui

    dlg = gui.DlgFromDict(dictionary=expInfo, title="GC Example", order=['SubjectNO', 'SubjectInitials'])
    if dlg.OK == False: core.quit()  # user pressed cancel
else:
    expInfo['SubjectNo'] = raw_input('Subject # (1-99): ')
    expInfo['SubjectInitials'] = raw_input('Subject Initials (e.g., WZ): ')
    expInfo['SubjectType'] = raw_input('Subject Type (e.g., Test): ')

particInfo = list(expInfo.values())
particNum = (particInfo[2])
particType = (particInfo[1])
particInit = (particInfo[0])

with open('Participant.pickle', 'wb') as TheBigP:
    pickle.dump(particNum, TheBigP, protocol=pickle.HIGHEST_PROTOCOL)

import TheMainOrderAlmostThere_Else

#### EYELINK LINK: established a link to the tracker ###############################################
if not dummyMode:
    tk = pylink.EyeLink('100.1.1.1')
else:
    tk = pylink.EyeLink(None)

#### EYELINK FILE: Open an EDF data file EARLY ####################################################
# Eye to be tracked
eye = "left"

# Note that for Eyelink 1000/II, the file name cannot exceeds 8 characters
# we need to open eyelink data files early so as to record as much info as possible
tk.openDataFile(EDF)

# add personalized header (preamble text)
tk.sendCommand("add_file_preamble_text 'Psychopy GC demo'")

#### MONITOR INFO: Initialize custom graphics for camera setup & drift correction ##################
scnWidth, scnHeight = (1600, 900)
# scnWidth, scnHeight = (1600,900)
# scnWidth, scnHeight = (2560,1440)

# you MUST specify the physical properties of your monitor first, otherwise you won't be able to properly use
# different screen "units" in psychopy
#################
## SET MONITOR ##

mon = monitors.Monitor("MonsieurMadeleine")  # Need psychopy
# calibrating screen - width in cm of screen
mon.newCalib(calibName="Bob", width=31, distance=60, gamma=None, notes=None, useBits=False, verbose=True)
mon.setCurrent("Bob")
# screen size
mon.setSizePix([1600, 900])  # [1280,720]
# mon.setSizePix([1280,720])
# mon.setSizePix([1600,900])
# mon.setSizePix([2560,1440])
mon.saveMon()
Window = visual.Window([600, 600], fullscr=True, monitor=mon, color=[0, 0, 0], units="pix")  #
# Window = visual.Window([1600,900], fullscr=True, monitor=mon, color=[0,0,0], units="pix")#
# Window = visual.Window([2560, 1440], fullscr=True, monitor=mon, color=[0,0,0], units="pix")
mouse = event.Mouse()
mouse.setVisible(0)
Window.mouseVisible = False
win32api.SetCursorPos((100, 100))
# mouse=event.Mouse()
# mouseVisible = False
# mouse = event.Mouse(visible=False)

# win = visual.Window([1280,720], fullscr=True, monitor=mon, color=[0,0,0], units="pix")
# this functional calls our custom calibration routin "EyeLinkCoreGraphicsPsychopy.py"
genv = EyeLinkCoreGraphicsPsychoPy(tk, Window)
pylink.openGraphicsEx(genv)

# this functional calls our custom calibration routin "EyeLinkCoreGraphicsPsychopy.py"
genv = EyeLinkCoreGraphicsPsychoPy(tk, Window)
pylink.openGraphicsEx(genv)

#### TRACKER SETUP: Set up the tracker ################################################################
# we need to put the tracker in offline mode before we change its configrations
tk.setOfflineMode()
# sampling rate, 250, 500, 1000, or 2000
tk.sendCommand('sample_rate 500')

# Online parser configuration: 0-> standard/coginitve, 1-> sensitive/psychophysiological
# [see Eyelink User Manual, Section 4.3: EyeLink Parser Configuration]
tk.sendCommand('select_parser_configuration 0')
# Set the tracker to record Event Data in "GAZE" (or "HREF") coordinates
tk.sendCommand("recording_parse_type = GAZE")

# inform the tracker the resolution of the subject display
# [see Eyelink Installation Guide, Section 8.4: Customizing Your PHYSICAL.INI Settings ]
tk.sendCommand("screen_pixel_coords = 0 0 %d %d" % (scnWidth - 1, scnHeight - 1))

# stamp display resolution in EDF data file for Data Viewer integration
# [see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration]
tk.sendMessage("DISPLAY_COORDS = 0 0 %d %d" % (scnWidth - 1, scnHeight - 1))

# specify the calibration type, H3, HV3, HV5, HV13 (HV = horiztonal/vertical),
tk.sendCommand("calibration_type = HV5")  # tk.setCalibrationType('HV9') also works, see the Pylink manual
# specify the proportion of subject display to calibrate/validate
tk.sendCommand("calibration_area_proportion 0.80 0.83")
tk.sendCommand("validation_area_proportion  0.80 0.83")

# allow buttons on the gamepad to accept calibration/dirft check target, so you
# do not need to press keys on the keyboard to initiate/accept calibration
tk.sendCommand("button_function 1 'accept_target_fixation'")

# data stored in data file and passed over the link (online)
# [see Eyelink User Manual, Section 4.6: Settting File Contents]
eyelinkVer = tk.getTrackerVersion()
if eyelinkVer >= 3:  # Eyelink 1000/1000 plus
    tk.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
    tk.sendCommand("link_event_filter = LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
    tk.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,HREF,PUPIL,STATUS,INPUT,HTARGET")
    tk.sendCommand("link_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,HREF,PUPIL,STATUS,INPUT,HTARGET")
else:  # Eyelink II
    tk.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
    tk.sendCommand("link_event_filter = LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
    tk.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,HREF,PUPIL,STATUS,INPUT")
    tk.sendCommand("link_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,HREF,PUPIL,STATUS,INPUT")


########## BEFORE CALIB - MOVIE ############
# Function for playing videos
def Duration(Type):
    VDur = subprocess.check_output(['ffprobe', '-i', str(Type)+'.mp4', '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
    return (float(VDur))

def PlayVid(Type):
    if Type == "Fantasia":
        process = subprocess.Popen(
            ["C:/Program Files/VideoLAN/VLC/vlc.exe", "fantasia.mov", "--fullscreen", "vlc://quit"])
        core.wait(1)
        Window.minimize()
        while process.poll() == None:  # while process is still running
            continue
        Window.maximize()
        Window.flip()
        # to fine the file with such name and of .mov format
        # for video in glob.glob(str(Type)+'.mov'):
        # defines this as the video in question
        # TheVids = video
    else:
        duration = Duration(Type)
        # core.wait(1)
        process = subprocess.Popen(
            ["C:/Program Files/VideoLAN/VLC/vlc.exe", str(Type) + ".mp4", "--fullscreen", "vlc://quit"])
        timer = core.Clock()  # starting clock
        core.wait(1)
        Window.minimize()
        while timer.getTime() < duration - 0.5:  # while video not finished, giving the possibility to escape
            # exit option
            allKeys = event.getKeys()
            ## Determining keys ##
            for thisKey in allKeys:
                ## Creates escape possibility ##
                if thisKey in ['q', 'escape']:
                    Window.maximize()
                    quitExp()
                    Window.minimize()

            continue
        Window.maximize()
        Window.flip()
        core.wait(1)

    # Window.close()
    # Window.flip()


# Play video - Fantasia
PlayVid("Fantasia")


############# CALIBRATE #############
# set up the camera and calibrate the tracker at the beginning of each block
# Window.flip()
mouse.setVisible(0)
Window.mouseVisible = False
Window.allowGUI = False
win32api.SetCursorPos((-100, 1000))
Window.flip()

tk.doTrackerSetup()

mouse.setVisible(0)
Window.mouseVisible = False
Window.allowGUI = False
win32api.SetCursorPos((-100, 1000))
Window.flip()

Window.units = "deg"


###### TRACKER FUNCTIONS #############
def trackerOn():
    """Set Eyelink in record mode, prior to starting the actual trial."""
    if tracker:
        tk.startRecording(1, 1, 1, 1)
        time.sleep(2)
    return


def trackerOff():
    """Set EyeLink to offline mode (stop recording)."""
    if tracker:
        # pylink.endRealTimeMode()

        # pylink.pumpDelay(100)
        tk.stopRecording()
        time.sleep(2)
    return


def trackerClose():
    """Close the connection to EyeLink and save data"""
    # File transfer and cleanup!
    if tracker:
        trackerOff()
        tk.setOfflineMode()
        time.sleep(2)
        # Close the file and transfer it to Display PC
        tk.closeDataFile()
        tk.receiveDataFile(EDF, str("TheResultsEyeT") + "/" + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + "_" + str(
            particType) + "_" + str(particNum) + ".EDF")
        tk.close()


def trialInit(Trial_ID):
    """EyeLink Trial Initialization"""
    if tracker:
        message = "record_status_message 'Trial " + str(Trial_ID) + "'"
        tk.sendCommand(message)
        # tk.sendMessage("TRIALID "+str(Trial_ID))


def trialStart(Trial_ID):
    """EyeLink trial starting (after trialInit has been called)"""
    if tracker:
        tk.sendMessage("STARTBUTTON")


def tagTrialAborted():
    currentTrialState = 0  # flush the counter to start again
    if tracker:
        tk.sendMessage("TRIAL ABORTED")

def tagEvent(Participant, Trial, Marker, Time, Left, Right, Target):
    """Target onset"""
    thisTag = str(Participant) + " " + str(Trial) + " " + str(Marker) + " " + str(Time) + " " + str(Left) + " " + str(Right) + " " + str(Target)
    thisTag = thisTag.upper()
    if tracker:
        tk.sendMessage(thisTag)


def trialClose(Trial_ID):
    """Close the trial, trialInit can be called after this for next trial."""
    if tracker:
        tk.sendMessage("TRIAL OK")


def trialStop(Trial_ID):
    """EyeLink trial stop. When answer has been prompted by user, stop trial."""
    if tracker:
        tk.sendMessage("ENDBUTTON")
    trialClose(Trial_ID)


def trackGazePos():
    """Get last gaze position - this is only for gaze contingent setting. Return tupple with gaze coordinates, None if no gaze, and 2 if blinks"""
    gazePos = None
    if tracker:
        # tk.getNextData() # update data link, must be called prior to getFloatData()
        newEvent = tk.getNewestSample()
        if newEvent.getRightEye() is not None:
            gazePos = newEvent.getRightEye().getGaze()
        if newEvent.getLeftEye() is not None:
            gazePos = newEvent.getLeftEye().getGaze()
        # elif isinstance(newEvent,pylink.StartBlinkEvent): # if this is a blink
        # gazePos=2
    return gazePos


def trackerFX():
    """This will return 1 if gaze coordinates are within the fixation radius given in parameters, 0 if not, and 2 if a blink occured"""
    if tracker:  # tracker or mouse sim is enabled
        gaze = trackGazePos()  # get gaze coordinates
        if gaze != None:
            x, y = gaze
            radius = TRACKER_FX_RADIUS
            center_x, center_y = RESOLUTION[0] / 2, RESOLUTION[1] / 2
            if numpy.sqrt((x - center_x) ** 2 + (y - center_y) ** 2) < radius:  # or conf.TRACKER==False:
                return 1
            else:
                return 0
    else:
        return 1


def quitExp():
    """Exit function"""
    text = visual.TextStim(Window, text='Etes-vous certain.e de vouloir quitter ?', font='', pos=(0.0, 0.0))
    event.clearEvents()
    trackerOff()
    while 1:
        text.draw()
        Window.flip()
        if len(event.getKeys(['y'])):
            trackerClose()
            core.quit()
            break
        if len(event.getKeys(['n'])):
            # why tracker off before?
            trackerOn()
            core.wait(1)
            event.clearEvents()
            Window.flip()
            break


# Duration of vids
def Duration(Type):
    VDur = subprocess.check_output(
        ['ffprobe', '-i', str(Type) + '.mp4', '-show_entries', 'format=duration', '-v', 'quiet', '-of',
         'csv=%s' % ("p=0")])
    return (float(VDur))
    # VDur = subprocess.check_output(['C:\FFmpeg\bin\ffprobe.exe', '-i', str(Type)+'.mp4', '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
    # result = float(FFProbe(str(Type)+'.mp4').video[0].duration)
    # print(result)
    # return result


##########################
## SET PARTICIPANT FILE ##
## Opens data file and writes headers ##
DataOpener = open(
    str("TheResultsPointing") + "/" + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + "_" + str(particNum) + "_" + str(
        particType) + ".csv", "wb")
DataWriter = csv.writer(DataOpener)
DataWriter.writerow(["sep=,"])
DataWriter.writerow(["Participant", "Initials", "Type", "Trial","LeftImage", "RightImage", "Target"])
#MAYBE ADD TARGET SIDE

########################################
############ Tech Works ###############
########################################

#################
## SET MONITOR ##

mon = monitors.Monitor("MonsieurMadeleine")  # Need psychopy
# calibrating screen - width in cm of screen
mon.newCalib(calibName="Bob", width=31, distance=60, gamma=None, notes=None, useBits=False, verbose=True)
mon.setCurrent("Bob")
mon.setSizePix([1600, 900])
# screen size
# mon.setSizePix([1600,900])

# mon.setSizePix([1600,900])
mon.saveMon()

#################
## SET WINDOW ###

# Window = visual.Window(fullscr=True,monitor=mon,size=[1280, 720],units="deg") #the images are adjusted
# Window = visual.Window(fullscr=True,monitor=mon,size=[1600,900],units="deg") #the images are adjusted
# visual.CustomMouse(Window, newPos=None, visible=False)
mouse.setVisible(0)
Window.setMouseVisible(False)
win32api.SetCursorPos((-100, 400))
# Initiate window

#################
## SET STIMULI ##
# Creating the image objects - left right and center
Image_Left = visual.ImageStim(Window, image="Chien_Image.jpg", pos=(-7, 0),
                              size=8.5)  # 20, 10, -9, 0all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Right = visual.ImageStim(Window, image="Chien_Image.jpg", pos=(7, 0),
                               size=8.5)  # 20, 10all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Mid = visual.ImageStim(Window, image="fixation.png", pos=(0, 0),
                             size=3)  # 6, 3all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Last = visual.ImageStim(Window, image="Ducky.jpg", pos=(0, 0), size=6)
# Creating the square to indicate the choice
Square = visual.Rect(Window, lineWidth=0, fillColor='orange', pos=(0, 0), size=25)  # 25, 50
# Creating the side positions
L = (-7, 0)
R = (7, 0)


###########################################
####### Definitions ######################


# Creating the animated fixation point
def Reduce():
    # Image_Mid.image = Image
    Image_Mid.draw()
    Window.flip()
    core.wait(1)

    n = 0
    while n < 3:
        allKeys = event.getKeys()
        ## Determining keys ##
        for thisKey in allKeys:
            ## Creates escape possibility ##
            if thisKey in ['q', 'escape']:
                quitExp()
        Image_Mid.size = 3 - n
        # Image_Mid.ori = 0 + (n*30)
        Image_Mid.draw()
        Window.flip()
        core.wait(0.05)
        n += 1

    m = 0
    while m < 3:
        allKeys = event.getKeys()
        ## Determining keys ##
        for thisKey in allKeys:
            ## Creates escape possibility ##
            if thisKey in ['q', 'escape']:
                quitExp()
        Image_Mid.size = 1 + m
        # Image_Mid.ori = 0 + (m/30)
        Image_Mid.draw()
        Window.flip()
        core.wait(0.05)
        m += 1

    core.wait(1)


def Rotate():
    n = 0
    while n < 370:
        Image_Last.ori = n
        Image_Last.draw()
        Window.flip()
        core.wait(0.0005)
        n += 10

    core.wait(1)


def BabyLaughing():
    Image_Mid.image = "Baby.png"
    Image_Mid.size = 6
    Laugh = pygame.mixer.Sound("Laugh.wav")

    Image_Mid.draw()
    Window.flip()
    Laugh.play()
    while pygame.mixer.get_busy():
        continue
    core.wait(1)

    Image_Mid.image = "fixation.png"
    Image_Mid.size = 3


###############################################
######### Setting the dictonaries ##############

###### REAL WORDS

######### Special manipulations for the novel words ###################
# Need to get them in the right order for the dictonary mapping

#### STEP 1 ###############

### For BABYLAB
os.chdir('C:/Users/lscpuser/Desktop/Monica - Dev/Stim/Visuo/Novel')


# print(TheOrderGetFilesNovel

### For BABYLAB
os.chdir('C:/Users/lscpuser/Desktop/Monica - Dev')

##########################
###########################
###### THE EXPE ##########
###########################
##########################

WORDPAIRS = [("Chien_Image.jpg", "Poussette_Image.jpg"), ( "Lapin_Image.jpg", "Tracteur_Image.jpg"), ("Cochon_Image.jpg","Biberon_Image.jpg"),("Souris_Image.jpg", "Chaussure_Image.jpg")]
AUDIOS = {"Chien_Image.jpg": "ko_chien_48000.wav",
"Poussette_Image.jpg": "ka_poussette_48000.wav",
"Lapin_Image.jpg": "ko_lapin_48000.wav",
"Tracteur_Image.jpg": "ka_tracteur_48000.wav",
"Cochon_Image.jpg": "ko_cochon_48000.wav",
"Biberon_Image.jpg": "ka_biberon_48000.wav",
"Souris_Image.jpg":"ko_souris_48000.wav",
"Chaussure_Image.jpg": "ka_chaussure_48000.wav"}

def find_wordpair(word,wordpairs):
    for wp in wordpairs:
        if word in wp:
            return wordpairs.index(wp)

def generate_concrete_list(WORDPAIRS):
    accumulator = []
    for i in range(0, 2):
        local_list = WORDPAIRS
        random.shuffle(local_list)
        k = map(list, zip(*local_list))
        items = [item for sublist in k for item in sublist]
        random.shuffle(items)
        for i in items:
            index=find_wordpair(i,WORDPAIRS)
            while items.index(i)<len(items)-1 and items[items.index(i)+1] in WORDPAIRS[index]:
                print("DOUBLE",i,WORDPAIRS[index])
                random.shuffle(items)
        print 'ITEMS GENERATED -> {}'.format(items)
        accumulator.append(items)
    concrete_list = [item for sublist in accumulator for item in sublist]
    print(concrete_list)
    return (concrete_list)

concrete_list=generate_concrete_list(WORDPAIRS)
def New_train(concrete_list):
    trial=0
    for item in concrete_list:
        trial += 1
        print("TRIAL NR: ", trial)
        Left_image, right_image = [x for x in WORDPAIRS if item in x][0]
        print("L:", Left_image, "R:", right_image)
        if item==Left_image:
            Target= "L"
        else:
            Target= "R"
        print Target
        tgt_sound = AUDIOS[item]
        Left=Left_image
        Image_Left.image = Left_image
        Image_Left.opacity = 1
        Image_Left.draw()
        Right = right_image
        Image_Right.image = right_image
        Image_Right.opacity = 1
        Image_Right.draw()
        Target = Target.strip("_Image.jpeg")
        print("Target: ", Target)
        Window.flip()
        timer = core.Clock()
        Momes = timer.getTime()
        tagEvent("TRIALSTART", particNum, trial, Momes, Left, Right, Target) #write which wp is belongs
        trialInit(trial)

        ## Plays sound ###
        tgt_sound = pygame.mixer.Sound(tgt_sound)
        # Marks the start of the trial
        # trialStart(N_TRAINING_TRIALS)
        Del = None

        tgt_sound.play()
        while pygame.mixer.get_busy():
            continue
        core.wait(1)
        allKeys = event.getKeys()
        ## Determining keys ##
        for thisKey in allKeys:
            ##Creates escape possibility ##
            if thisKey in ['q', 'escape']:
                quitExp()
        n = 0
        timer = core.Clock()
        Momes = timer.getTime()
        tagEvent("TRIALEND", particNum, trial, Momes, Left, Right, Target)
        #            tagEvent(particNum, "TRIALEND", Moment, Target, Foil, AI, CorrectSide)
        DataWriter.writerow([particNum, particInit, particType, trial, Left, Right, Target])
        if trial==8:
            BabyLaughing()
        Reduce()


###########################
## SET THE TRIAL COUNTER ##
N_TRAINING_TRIALS = 1
N_TRIALS = 1

####################
## INITIATE SOUND ##
pygame.mixer.init(48000, -16, 2, 2048)

################
### PLAY VIDEO ##

# clip = VideoFileClip("Stim/Animacy_Training.mp4")
# clipre=clip.resize([1280,720])
# clipre.preview()

##################
### SET WINDOW ###


Window.flip()

########################################
#### RUN EXPE #########################
########################################

#################
### Training ####
# ET
trackerOn()
Window.flip()
core.wait(1)

# Run EXP
## Fixation Cross ##
# Before trial
Reduce()
#
while not trackerFX():
    Window.flip()
     # core.wait(1)
    event.clearEvents()
    Reduce()
#     if len(event.getKeys(['b'])):
#         BabyLaughing()
#         event.clearEvents()
#         break
#     if len(event.getKeys(['m'])):
#         event.clearEvents()
#         break

Window.flip()
core.wait(1)

## INTRODUCTION TRIALS: 2

New_train(concrete_list)

n += 1

Window.flip()
core.wait(1)
#PlayVid("Novel")
Window.flip()
core.wait(1)
Rotate()

######## CLOSING THINGS ######
# Close sound
pygame.mixer.quit()

trackerOff()
trackerClose()
