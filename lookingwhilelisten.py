from psychopy import visual, core, event, sound, monitors
from EyeLinkCoreGraphicsPsychoPyAnimatedTarget_Other import EyeLinkCoreGraphicsPsychoPy
import numpy, pygame, string
import sys
import pickle
import random
import csv
import time
import os
import pylink
from datetime import datetime
import keyboard

print "Started Looking while listening."

os.chdir("D:\Manips\Chiara\Phonses")

################ EYET INFOS ########################
pylink.flushGetkeyQueue()
EDF = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
eye = None  # left ("left") or right ("right") eye used for EyeLink. Used for gaze contingent display
last_ET = 0  # last gaze position
# Getting the radius of the space of the central fixation point
TRACKER_FX_RADIUS = 900
RESOLUTION = [1600, 900]  # [1280,720][1600,900]#
tracker = True
# Set a few task parameters
#### SUBJECT INFO: get subject info with GUI ########################################################
particInfo = map(str, sys.argv[1].strip("[]\\").split(","))
particNum = (particInfo[1].replace("'", "").strip())
particInit = (particInfo[0].replace("'", ""))

with open('Participant.pickle', 'wb') as TheBigP:
    pickle.dump(particNum, TheBigP, protocol=pickle.HIGHEST_PROTOCOL)

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
#################
## SET MONITOR ##
#### MONITOR INFO: Initialize custom graphics for camera setup & drift correction ##################
scnWidth, scnHeight = (1600, 900)
mon = monitors.Monitor("MonsieurMadeleine")  # Need psychopy
# calibrating screen - width in cm of screen
mon.newCalib(calibName="B", width=31, distance=60, gamma=None, notes=None, useBits=False, verbose=True)
mon.setCurrent("B")
# screen size
mon.setSizePix([1600, 900])  # [1280,720]
mon.saveMon()
Window = visual.Window([600, 600], fullscr=True, monitor=mon, color=[0, 0, 0], units="pix")  #
mouse = event.Mouse()
mouse.setVisible(0)
Window.mouseVisible = False
#win32api.SetCursorPos((100, 100))

# this functional calls our custom calibration routine "EyeLinkCoreGraphicsPsychopy.py"
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


############# CALIBRATE #############
# set up the camera and calibrate the tracker at the beginning of each block
# Window.flip()
mouse.setVisible(0)
Window.mouseVisible = False
Window.allowGUI = False
Window.flip()
initial_screen()
Window.flip()
tk.doTrackerSetup()
mouse.setVisible(0)
Window.mouseVisible = False
Window.allowGUI = False
#win32api.SetCursorPos((-100, 1000))
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
        print"saving file as {}".format([str("Results") + "/" + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + "_" + str(particNum)])
        tk.receiveDataFile(EDF, str("D:\Manips\Chiara\Phonses\LookingListening\Results") + "/" + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + "_" + str(particNum) + ".EDF")
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


def initial_screen():
    """instructions before calibration"""
    text = visual.TextStim(Window, text='At the next screen press:\n\nC to Calibrate \n\nESC to start experiment'
                                        '\n\n\n\nPress any key to continue.', height=36, pos=(0.0, 0.0))
    event.clearEvents()
    while 1:
        text.draw()
        Window.flip()
        keys = event.getKeys()
        if keys:
            break

def quitExp():
    """Exit function"""
    text = visual.TextStim(Window, text='Press Y to quit, N to return to experiment', font='', pos=(0.0, 0.0))
    event.clearEvents()
    trackerOff()
    break_=False
    while not break_:
        text.draw()
        Window.flip()
        if len(event.getKeys(['y'])):
            trackerClose()
            core.quit()
            break
        if len(event.getKeys(['n'])):
            trackerOn()
            core.wait(1)
            Window.flip()
            break_=True


#################
## SET STIMULI ##
# Creating the image objects - left right and center

## SET STIMULI ##
# Creating the image objects - left right and center
Image = visual.ImageStim(Window, image="LookingListening\Stimuli\Banane.jpg", pos=(0, 0),
                               size=10)  # 20, 10all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Left = visual.ImageStim(Window, image="LookingListening\Stimuli\Banane.jpg", pos=(-7, 0),
                              size=8.5)  # 20, 10, -9, 0all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Right = visual.ImageStim(Window, image="LookingListening\Stimuli\Banane.jpg", pos=(7, 0),
                               size=8.5)  # 20, 10all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Mid = visual.ImageStim(Window, image="LookingListening\Stimuli\\fixation.png", pos=(0, 0),
                             size=3)  # 6, 3all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Last = visual.ImageStim(Window, image="LookingListening\Stimuli\Ducky.jpg", pos=(0, 0), size=6)

# Creating the side positions
L = (-7, 0)
R = (7, 0)


###########################################
####### Definitions ######################
## SET PARTICIPANT FILE ##
## Opens data file and writes headers ##
DataOpener = open(
    str("D:\Manips\Chiara\Phonses\Wordfreqs\Results") + "/" + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + "_" + str(particNum) + ".csv", "wb")
DataWriter = csv.writer(DataOpener)
DataWriter.writerow(["sep=,"])
DataWriter.writerow(["Participant", "Initials", "Type", "Trial","LeftImage", "RightImage", "Target"])

# Creating the animated fixation point

def Reduce():
    Image_Mid.image = "D:\Manips\Chiara\Phonses\LookingListening\Stimuli\\fixation.png"
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
            elif thisKey == "s":
                print "pressed s"
                return True
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
    return False


# Create the end of experiment rotating image
def Rotate():
    n = 0
    while n < 370:
        Image_Last.ori = n
        Image_Last.draw()
        Window.flip()
        core.wait(0.0005)
        n += 10

    core.wait(1)


# Laughing baby image between trials
def BabyLaughing():
    Image_Mid.image = "D:\Manips\Chiara\Phonses\LookingListening\Stimuli\Baby.png"
    Image_Mid.size = 6
    Laugh = pygame.mixer.Sound("D:\Manips\Chiara\Phonses\LookingListening\Stimuli\Laugh.wav")
    Image_Mid.draw()
    Window.flip()
    Laugh.play()
    while pygame.mixer.get_busy():
        continue

######## GET STIMULI
os.chdir("D:\Manips\Chiara\Phonses\LookingListening\Stimuli")

WORDPAIRS = [("Vache.jpg", "Livre.jpg"),( "Main.jpg", "Biberon.jpg"),("Pomme.jpg", "Nez.jpg"), ("Balle.jpg", "Pied.jpg")]

AUDIOS = {"Balle.jpg":"Elle_est_ou_balle_FINAL_new.wav", "Banane.jpg":"oh_reg_banane_final.wav",
        "Chaussure.jpg":"Oh_reg_chaussure_final.wav", "Biberon.jpg":"Tu_c_est_biberon_FINAL_new.wav",
        "Bouche.jpg":"Tu_c_est_bouche_FINAL_new.wav", "Livre.jpg":"Oh_reg_livre_FINAL_new.wav",
        "Main.jpg":"Oh_reg_main_FINAL_new.wav", "Nez.jpg":"Tu_le_nez_FINAL_new.wav",
        "Pied.jpg":"Tu_le_vois_pied_FINAL_new.wav","Pomme.jpg":"Elle_est_ou_pomme_FINAL_new.wav",
        "Vache.jpg":"Elle_vache_FINAL_new.wav"}

WORDS_ = {"Balle.jpg":2,
        "Biberon.jpg":3,
        "Livre.jpg":5,
        "Main.jpg":3,
        "Nez.jpg":1,
        "Pied.jpg":2,
        "Pomme.jpg":1,
        "Vache.jpg":5}


def pseudorandomize(stimuli):
	"""Pseudorandomize the list of stimuli"""
    lineup = []
    attempt = 0
    while len(lineup) < 16:
        attempt += 1
        choice = random.choice(list(stimuli.keys()))
        if len(lineup) == 0:
            lineup.append(choice)
        elif stimuli[lineup[-1]] != stimuli[choice] and lineup.count(choice) != 2:
            lineup.append(choice)
        if attempt > 100:
            if stimuli[lineup[0]] != stimuli[choice]:
                lineup.insert(0, choice)
            else:
                continue

def check_keys():
	"""Handle key presses during experiment"""
    allKeys = event.getKeys()
    for thisKey in allKeys:
        if thisKey in ['q', 'escape']: # Creates escape possibility 
            pygame.mixer.stop()
            quitExp()
        elif thisKey == "s": # Skip trial directly
            pygame.mixer.stop()
            print "Going to next trial..."
            return True
        elif thisKey == "g": # Skip trial and present attention getter
            pygame.mixer.stop()
            print "Going to attention getter..."
            Reduce()
            while not trackerFX(): #until the gaze comes back
                skip=Reduce()
                if skip==True:
                    break
            return True
        else:
            return False

def Train(imgs):
    trial=0
    for v in imgs:
        skip=False
        trial += 1
        print("TRIAL NR: ", trial)
        tgt_sound = AUDIOS[v]
        Image.image = v
        Image.draw()
        Image.opacity = 1
        Window.flip()
        trialInit(trial)
        ## Plays sound with pygame
        tgt_sound = pygame.mixer.Sound(tgt_sound)
        tgt_sound.play()
        tagEvent("TRIALSTART", particNum, trial, str(v), str(v), str(v), "R")
        while pygame.mixer.get_busy():
            skip = check_keys() # check keys
            if skip == True:
                tagEvent("TRIALEND", particNum, trial, str(v), str(v), str(v), "R")
                break
        if skip==True: 
            continue
        # Write data 
        tagEvent("TRIALEND", particNum, trial, str(v), str(v), str(v), "R")
        DataWriter.writerow(
            [particNum, particInit, "TRIALEND", trial,"train", str(v)])
        # Attention Getter
        Reduce()
        while not trackerFX():
            skip=Reduce()
            if skip == False:
                break
            else:
                Window.flip()
                event.clearEvents()
                Reduce()

def Test(concrete_list):
	"""Experimental routine"""
    trial=0
    for item in concrete_list: # for item in pseudorandomized list
        skip=False
        trial += 1
        Left_image, right_image = [x for x in WORDPAIRS if item in x][0]
        # get names of items on L and R side to write results
        if item==Left_image:
            Target= "L"
            TgtImage = Left_image.strip(".jpg")
            Distractor=right_image.strip(".jpg")
        else:
            Target= "R"
            TgtImage = right_image.strip(".jpg")
            Distractor = Left_image.strip(".jpg")
        print Target
        #Set up psycopy objects
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
        Window.flip()

        wordpair=Left_image.strip(".jpg") +"_"+ right_image.strip(".jpg")
        tagEvent("TRIALSTART", particNum, trial, wordpair, TgtImage, Distractor, Target)
        trialInit(trial)
        DataWriter.writerow(
            [particNum, particInit, trial, wordpair, TgtImage, Distractor, Target])
        ## Plays sound ###
        tgt_sound = pygame.mixer.Sound(tgt_sound)
        tgt_sound.play()
        while pygame.mixer.get_busy():
            skip = check_keys()
            if skip == True:
                tagEvent("TRIALEND", particNum, trial, wordpair, TgtImage, Distractor, Target)
                break
        if skip==True:
            continue
        tagEvent("TRIALEND", particNum, trial, wordpair, TgtImage, Distractor, Target)
        if trial==8:
            BabyLaughing()
            continue
        # Fixation dot bw trials
        Reduce()
        while not trackerFX():
            skip=Reduce()
            if skip == True:
                break
            else:
                Window.flip()
                event.clearEvents()
                skip =Reduce()

####################
## INITIATE SOUND ##
pygame.mixer.init(48000, -16, 2, 2048)
Window.flip()
#### RUN EXPE #########################

trackerOn()
Window.flip()
core.wait(1)

# Before trial attention getter
Reduce()
#
while not trackerFX():
    Window.flip()
     # core.wait(1)
    event.clearEvents()
    skip=Reduce()
    if skip==True:
        break
Window.flip()
core.wait(1)

# 2 INITIAL TRIALS
Train(['Chaussure.jpg',
       'Banane.jpg'])

Window.flip()
core.wait(1)
Window.flip()
Reduce()
while not trackerFX():
    Window.flip()
     # core.wait(1)
    event.clearEvents()
    skip=Reduce()
    if skip == True:
        break

lineup=pseudorandomize(WORDS_)
Test(lineup)

Window.flip()
core.wait(1)
#PlayVid("Novel")
Window.flip()
core.wait(1)
Rotate()

######## CLOSING THINGS ######

pygame.mixer.quit()

trackerOff()
trackerClose()
