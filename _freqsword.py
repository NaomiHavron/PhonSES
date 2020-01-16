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
    # You want it to be somewhere in particular
    win32api.SetCursorPos((x, y))
    # ?
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)


# from moviepy.editor import *

# Is it needed?
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
TRACKER_FX_RADIUS_screen=900
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
Window = visual.Window([600, 600], fullscr=False, monitor=mon, color=[0, 0, 0], units="pix")  #
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
# PlayVid("Fantasia")


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

def tagEvent(Participant, Trial, Marker, Time, Image):
    """Target onset"""
    thisTag = str(Participant) + " " + str(Trial) + " " + str(Marker) + " " + str(Time) + " " + str(Image)
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
            print gazePos
        elif isinstance(newEvent,pylink.StartBlinkEvent): # if this is a blink
            gazePos=2
    return gazePos


def trackerFX(radius):
    """This will return 1 if gaze coordinates are within the fixation radius given in parameters, 0 if not, and 2 if a blink occured"""
    if tracker:  # tracker or mouse sim is enabled
        gaze = trackGazePos()  # get gaze coordinates
        if gaze != None and gaze!=2:
            x, y = gaze
            center_x, center_y = RESOLUTION[0] / 2, RESOLUTION[1] / 2
            if numpy.sqrt((x - center_x) ** 2 + (y - center_y) ** 2) < radius:  # or conf.TRACKER==False:
                return 1
            else:
                return 0
        elif gaze==2:
            print ("blink")
            return 1
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
Image = visual.ImageStim(Window, image="Chien_Image.jpg", pos=(0, 0),
                               size=10)  # 20, 10all objects must be initiated here, even if some attributes (image for example) are not known yet
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

## Prep Work ##

## Associating the files with the words ##
def WordToFile(List, Dicto, Files):
    n = 0
    for Word in List:
        Dicto[Word] = Files[n]
        n += 1


## Creating a list that incorportates animacy and the novel pairings
def NovelPairing(Woord, Pair):
    n = 0
    while n < 4:
        if Woord[n] in Pair[0][0][0]:
            TheTreeps = (Woord[n], Pair[0][0][0][0], "Ko")
        elif Woord[n] in Pair[1][0][0]:
            TheTreeps = (Woord[n], Pair[1][0][0][0], "Ko")
        elif Woord[n] in Pair[0][0][1]:
            TheTreeps = (Woord[n], Pair[0][0][1][0], "Ka")
        elif Woord[n] in Pair[1][0][1]:
            TheTreeps = (Woord[n], Pair[1][0][1][0], "Ka")
        GetFilesNovel.append(TheTreeps)
        # print(GetFilesNovel)
        n += 1


## Getting the index of strings in a list, and creating a tuple with the item and index
def Index(List, IndexedList):
    n = 0
    while n < 4:
        Index = List.index(List[n])
        TheInd = (List[n], Index)
        IndexedList.append(TheInd)
        n += 1


# Getting the right order of the Object-Word to use in the Dict
def Order(Pairing, IndexedFile, List):
    n = 0
    while n < 4:
        name = Pairing[n][1]
        ### finding a file with a substring in name
        for file in glob.glob(str(name) + '*'):
            if file == IndexedFile[n][0]:
                TheIndexed = (Pairing[n], IndexedFile[n][1])
                List.append(TheIndexed)
                n += 1
            else:
                random.shuffle(Pairing)


# Getting the right order of the Sound-Word to use in the Dict
def SoundFiles(AnimIndex, NewList):
    n = 0
    while n < 4:
        name = AnimIndex[n][0][0]
        # make the string lowercase
        Name = name.lower()

        if AnimIndex[n][0][2] == 'Ko':
            # if the order one is an animate find the sound file with the pseudoword in it
            for kofile in glob.glob('ko_' + str(Name) + '_48000.wav'):
                NewList.append(kofile)
                # print(NewList)
                # print('kohere')
                n += 1
        elif AnimIndex[n][0][2] == 'Ka':
            for kafile in glob.glob('ka_' + str(Name) + '_48000.wav'):
                NewList.append(kafile)
                # print(NewList)
                # print('Kahere')
                n += 1


## During the expe ##
# Once the choice is made, it is shown explicitly to the participant
def Flash(ChoiceImage, OtherImage, Square, ChoiceSide, OtherSide):
    # Number of times it will flash
    n = 0
    while n < 2:
        # Place the flashing square
        Square.pos = ChoiceSide
        Square.draw()

        # Superpose the chosen image
        ChoiceImage.pos = ChoiceSide
        ChoiceImage.draw()

        # The other image as semi-transparent
        OtherImage.pos = OtherSide
        OtherImage.opacity = 0.5
        OtherImage.draw()

        # Display all
        Window.flip()
        core.wait(0.5)

        # Same but without the square to create flash
        ChoiceImage.draw()
        OtherImage.draw()

        # Display all
        Window.flip()
        core.wait(0.5)

        n += 1


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


# Gets the values from the excel file - determine the target, the column name, the kind of target, and subset information, here dets
def GetTiming(Target, Marker, Kind, Delete):
    # Making the value global
    # Dividing the kinds of items into two processing kinds - one step and two step
    theItem = None
    print(Kind)
    if Kind == "N":
        # Here we want to find the subset of the list, because there are two of these items present and we want one
        # List, List, Column to be searched, specifing that the thing you want to eliminate is a string, putting in the string (here the unwanted determiner)
        TheSubset = EyeT_Info[~EyeT_Info.Determiner.str.contains(Delete)]
        # List, going to look at rows, #list, in column titled as such, the target# # #the column you want data from# get value
        theItem = TheSubset.loc[TheSubset['Noun'] == Target][Marker].values
        print("Novel")
    else:
        print("here")
        theItem = EyeT_Info.loc[EyeT_Info['Noun'] == Target][Marker].values
        # theThing = EyeT_Info
    print(theItem)
    return theItem


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

AUDIOS = {"Chien_Image.jpg": "ko_chien_48000.wav",
"Poussette_Image.jpg": "ka_poussette_48000.wav",
"Lapin_Image.jpg": "ko_lapin_48000.wav",
"Tracteur_Image.jpg": "ka_tracteur_48000.wav",
"Cochon_Image.jpg": "ko_cochon_48000.wav",
"Biberon_Image.jpg": "ka_biberon_48000.wav",
"Souris_Image.jpg":"ko_souris_48000.wav",
"Chaussure_Image.jpg": "ka_chaussure_48000.wav"}



def monitor_attention(trackingfun):
    startTime = time.time()
    a = True
    while trackingfun == False:
        print "here"
        endTime = time.time()
        if (endTime - startTime > 3):
            print("Longer than 3 seconds")
            a=False
            break
    else:
        print "now here"
    return a

def New_train(AUDIOS):
    trial=0
    for k,v in AUDIOS.items():
        trial += 1
        print("TRIAL NR: ", trial)
        tgt_sound = v
        Image.image = k
        Image.draw()
        Image.opacity = 1
        Window.flip()
        timer = core.Clock()
        Momes = timer.getTime()
        tagEvent("TRIALSTART", particNum, trial, Momes, Image)
        trialInit(trial)
        ## Plays sound ###
        tgt_sound = pygame.mixer.Sound(tgt_sound)
        timeout= time.time() + tgt_sound.get_length() +1
        tgt_sound = pygame.mixer.Sound(tgt_sound)
        tgt_sound.play()
        while time.time() < timeout:
            gaze=trackGazePos()
            startTime = time.time()
#            if not monitor_attention(trackerFX(TRACKER_FX_RADIUS_screen)):
#            pygame.mixer.stop()
#            tagEvent("TRIAL INTERRUPTED", particNum, trial, Momes, Image)
            while gaze[0]<0:
                gaze = trackGazePos()
                print "here"
                endTime = time.time()
                if (endTime - startTime > 3):
                    pygame.mixer.stop()
                    print("Longer than 3 seconds")
                    BabyLaughing()
                    tagEvent("Trial Interrupted", particNum, trial, Momes, Image)
                    break
            else:
                print "blink"
                continue
        while pygame.mixer.get_busy():
            continue
        else:
            pygame.mixer.stop()
        allKeys = event.getKeys()
        for thisKey in allKeys:
            if thisKey in ['q', 'escape']:
                quitExp()
        timer = core.Clock()
        Momes = timer.getTime()
        tagEvent("TRIALEND", particNum, trial, Momes, Image)
        if trial == 8:
            BabyLaughing()
            Reduce()
            break
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


#### RUN EXPE #########################
########################################
### Training ####
# ET

trackerOn()
Window.flip()
core.wait(1)

# Run training

    ## Fixation Cross ##
    # Before trial
Reduce()
while not trackerFX(TRACKER_FX_RADIUS):
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

New_train(AUDIOS)

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
