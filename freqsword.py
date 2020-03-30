from psychopy import visual, core, event, sound, monitors
import numpy, pygame, string, sys
from EyeLinkCoreGraphicsPsychoPyAnimatedTarget_Other import EyeLinkCoreGraphicsPsychoPy
import pickle
import random
import csv
import time
import pylink
import keyboard
from datetime import datetime
from random import shuffle


################ EYET INFOS ########################

pylink.flushGetkeyQueue()
EDF = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
eye = "Left"  # left ("left") or right ("right") eye used for EyeLink. Used for gaze contingent display
last_ET = 0  # last gaze position
# Getting the radius of the space of the central fixation point
TRACKER_FX_RADIUS = 900
TRACKER_FX_RADIUS_screen=900
RESOLUTION = [1600, 900] 

tracker = True
useGUI = True  # whether use the Psychopy GUI module to collect subject information
dummyMode = not tracker  # If in Dummy Mode, press ESCAPE to skip calibration/validataion

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
# Note that for Eyelink 1000/II, the file name cannot exceed 8 characters
# we need to open eyelink data files early so as to record as much info as possible
tk.openDataFile(EDF)
eye = "left"
# add personalized header (preamble text)
tk.sendCommand("add_file_preamble_text 'Psychopy GC demo'")
#### MONITOR INFO: Initialize custom graphics for camera setup & drift correction ##################
scnWidth, scnHeight = (1600, 900)
#################
## SET MONITOR ##
mon = monitors.Monitor("MonsieurMadeleine")  # Need psychopy
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
#win32api.SetCursorPos((-100, 1000))
Window.flip()
initial_screen()
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
        tk.receiveDataFile(EDF, str("D:\Manips\Chiara\Phonses\Wordfreqs\Results") + "/" + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + "_" + str(particNum) + ".EDF")
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

def initial_screen():
    """Before calibration instruction"""
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
            # why tracker off before?
            trackerOn()
            core.wait(1)
            Window.flip()
            break_=True

##########################
## SET PARTICIPANT FILE ##
## Opens data file and writes headers ##
DataOpener = open(
    str("D:\Manips\Chiara\Phonses\Wordfreqs\Results_log") + "/" + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + "_" + str(particNum) + "_"  + ".csv", "wb")
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
mon.saveMon()
## SET WINDOW ###
mouse.setVisible(0)
Window.setMouseVisible(False)
#################
## SET STIMULI ##
Image = visual.ImageStim(Window, image="Wordfreqs/Stimuli/Chien_Image.jpg", pos=(0, 0),
                               size=10)  # 20, 10all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Mid = visual.ImageStim(Window, image="Wordfreqs/Stimuli/fixation.png", pos=(0, 0),
                             size=3)  # 6, 3all objects must be initiated here, even if some attributes (image for example) are not known yet
Image_Last = visual.ImageStim(Window, image="Wordfreqs/Stimuli/Ducky.jpg", pos=(0, 0), size=6)
# Creating the square to indicate the choice
Square = visual.Rect(Window, lineWidth=0, fillColor='orange', pos=(0, 0), size=25)  # 25, 50
# Creating the side positions
L = (-7, 0)
R = (7, 0)


###########################################
####### Definitions ######################

# Creating the animated fixation point
def Reduce():
    Image_Mid.image = "Wordfreqs/Stimuli/fixation.png"
    Image_Mid.size = 3
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
                return True
        Image_Mid.size = 3 - n
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

# End of experiment image
def Rotate():
    n = 0
    while n < 370:
        Image_Last.ori = n
        Image_Last.draw()
        Window.flip()
        core.wait(0.0005)
        n += 10
    core.wait(1)


# Laughing Baby attention getter

def BabyLaughing():
    Image_Mid.image = "D:\Manips\Chiara\Phonses\LookingListening\Stimuli\Baby.png"
    Image_Mid.size = 6
    Laugh = pygame.mixer.Sound("D:\Manips\Chiara\Phonses\LookingListening\Stimuli\Laugh.wav")
    Image_Mid.draw()
    Window.flip()
    Laugh.play()
    while pygame.mixer.get_busy():
        allKeys = event.getKeys()
        ## Determining keys ##
        for thisKey in allKeys:
            ## Creates escape possibility ##
            if thisKey in ['q', 'escape']:
                quitExp()
            elif thisKey == "s":
                pygame.mixer.stop()
                print "Going to next trial..."
                return True
            else:
                continue

###########################
##########################
stim_path="D:\Manips\Chiara\Phonses\Wordfreqs\Stimuli"
import glob
AUDIOS=glob.glob(stim_path+"\*.wav")


def monitor_attention(trackingfun):
    startTime = time.time()
    a = True
    while trackingfun == False:
        endTime = time.time()
        if (endTime - startTime > 3):
            print("Longer than 3 seconds")
            a=False
            break
    else:
        pass
    return a

def check_keys():
    allKeys = event.getKeys()
    for thisKey in allKeys:
        ## Creates escape possibility ##
        if thisKey in ['q', 'escape']:
            pygame.mixer.stop()
            quitExp()
        elif thisKey == "s":
            pygame.mixer.stop()
            print "Going to next trial..."
            return True
        elif thisKey == "g":
            pygame.mixer.stop()
            print "Going to attention getter..."
            Reduce()
            while not trackerFX(TRACKER_FX_RADIUS):
                skip=Reduce()
                if skip==True:
                    break
            return True
        else:
            return False

def Test(AUDIOS):
    trial=0
    shuffle(AUDIOS)
    for v in AUDIOS:
        trial += 1
        tgt_sound = v
        Image.image = "D:\Manips\Chiara\Phonses\Wordfreqs\Stimuli\Bullseye.jpg"
        Image.draw()
        Image.opacity = 1
        Window.flip()
        timer = core.Clock()
        Momes = timer.getTime()
        tagEvent("TRIALSTART", particNum, trial, tgt_sound, Momes)
        trialInit(trial)
        ## Plays sound ###
        tgt_sound = pygame.mixer.Sound(tgt_sound)
        timeout= time.time() + tgt_sound.get_length()
        tgt_sound = pygame.mixer.Sound(tgt_sound)
        tgt_sound.play()
        skip=False
        babylaugh=False
        # for the duration of the audiofile
        while time.time() < timeout:
            gaze=trackGazePos()
            startTime = time.time()
            skip=check_keys() #keep checking keys
            if skip == True:
                tagEvent("TrialInterrupted", particNum, trial, tgt_sound, Momes)
                break
            # monitor how long gaze has been gone 
            while gaze[0]<0:
                gaze = trackGazePos()
                endTime = time.time()
                if (endTime - startTime > 3):
                    pygame.mixer.stop()
                    print("Longer than 3 seconds")
                    babylaugh=BabyLaughing()
                    if babylaugh == True: 
                        break
            if babylaugh == True: 
                    break
            else: #go back to the experiment
                continue
        if babylaugh==True or skip == True:
            tagEvent("TrialInterrupted", particNum, trial, tgt_sound, Momes)
            continue
        while pygame.mixer.get_busy():
            continue
        else:
            pygame.mixer.stop()
        timer = core.Clock()
        Momes = timer.getTime()
        tagEvent("TRIALEND", particNum, trial, tgt_sound, Momes)
        if trial == 8:
            BabyLaughing()
            continue
        Reduce()
        while not trackerFX(TRACKER_FX_RADIUS_screen):
            skip=Reduce()
            if skip == True:
                break
            else:
                Window.flip()
                event.clearEvents()
                Reduce()


####################
## INITIATE SOUND AND TRACKER
pygame.mixer.init(32000, -16, 2, 2048)
Window.flip()
trackerOn()
Window.flip()
core.wait(1)

#### RUN EXPERIMENT
# Attention getter
Reduce()
while not trackerFX(TRACKER_FX_RADIUS_screen):
    skip = Reduce()
    if skip == True:
        break
    else:
        Window.flip()
        event.clearEvents()
        Reduce()
Window.flip()
core.wait(1)

### Testing ####
Test(AUDIOS)
Window.flip()
core.wait(1)
Rotate()

######## CLOSING THINGS ######
# Close sound
pygame.mixer.quit()
trackerOff()
trackerClose()


