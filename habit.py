#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

# ============================================
#                                            =
# Looking-time infant study                  =
#                                            =
# ============================================
from __future__ import print_function
import sys
import random
import pygame
import imageio
imageio.plugins.ffmpeg.download()
from moviepy.editor import *
import datetime
import libpsypsy.psypsyio as psypsyio
import libpsypsy.psypsyinterface as psypsyinterface
import libpsypsy.psypsyvideo as psypsyvideo
#import win32api, win32con
import pylink
import string
import time
import numpy

##### TRACKER FUNCTIONS #############
tracker = True
particInfo = map(str, sys.argv[1].strip("[]\\").split(","))
particNum = (particInfo[1].replace("'", "").strip())
particInit = (particInfo[0].replace("'", ""))

def check_exit(video):
    if video == "quit":
        screen.fill((100, 100, 100))
        psypsyinterface.display_text(screen, "Are you sure you want to quit? Press Y or N",
                                     font_size=60)  # Wait for key press
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_y:
                    pygame.quit()
                    trackerClose()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                    return

def initial_screen(screen):
    """Before calibration instruction"""
    screen.fill((100, 100, 100))
    psypsyinterface.display_text(screen, "At the next screen press: C to Calibrate, ESC to start experiment.  Press any key to continue.", font_size=40)  # Wait for key press
    psypsyinterface.wait_for_key()


def trackerOn():
    """Set Eyelink in record mode, prior to starting the actual trial."""
    tk.startRecording(1, 1, 1, 1)
    time.sleep(2)
    return


def trackerOff():
    """Set EyeLink to offline mode (stop recording)."""
    tk.stopRecording()
    time.sleep(2)
    return


def trackerClose():
    """Close the connection to EyeLink and save data"""
    # File transfer and cleanup!
    trackerOff()
    tk.setOfflineMode()
    time.sleep(2)
    # Close the file and transfer it to Display PC
    tk.closeDataFile()
    tk.receiveDataFile(EDF, str("D:\Manips\Chiara\Phonses\_experimental_suite\HabitResults") + "/" + str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")) + "_" + str(particNum) + ".EDF")
    tk.close()
    #pygame.quit()


def trialInit(Trial_ID):
    """EyeLink Trial Initialization"""
    message = "record_status_message 'Trial " + str(Trial_ID) + "'"
    tk.sendCommand(message)
        # tk.sendMessage("TRIALID "+str(Trial_ID))


def trialStart(Trial_ID):
    """EyeLink trial starting (after trialInit has been called)"""
    tk.sendMessage("STARTBUTTON")


def tagTrialAborted():
    currentTrialState = 0  # flush the counter to start again
    tk.sendMessage("TRIAL ABORTED")

def tagEvent(Participant, Trial, Marker, Time, Left, Right, Target):
    """Target onset"""
    thisTag = str(Participant) + " " + str(Trial) + " " + str(Marker) + " " + str(Time) + " " + str(Left) + " " + str(Right) + " " + str(Target)
    thisTag = thisTag.upper()
    tk.sendMessage(thisTag)


def trialClose(Trial_ID):
    """Close the trial, trialInit can be called after this for next trial."""
    tk.sendMessage("TRIAL OK")


def trialStop(Trial_ID):
    """EyeLink trial stop. When answer has been prompted by user, stop trial."""
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
            radius = TRACKER_FX_RADIUS_screen
            center_x, center_y = RESOLUTION[0] / 2, RESOLUTION[1] / 2
            if numpy.sqrt((x - center_x) ** 2 + (y - center_y) ** 2) < radius:  # or conf.TRACKER==False:
                return 1
            else:
                return 0
    else:
        return 1



def write_result_phase3(output, subj, start_time, condition_p3, trial_number, trial_on, trial_off,
                        end, duration, trial_type, stimulus, log,startend="TRIALSTART"):
    f = open(output, 'a')
    print("Writing {} results to file".format(trial_type))
    result_list = [subj, start_time, condition_p3, trial_number, str(trial_on), str(trial_off),
                   end, str(duration), trial_type, stimulus, log]
    result = "\t".join(result_list)
    print("Sending {} info to eyetracker".format(trial_type))
    tagEvent(startend, trial_number, trial_on, trial_off,
                        end, trial_type, stimulus)
    print(result, file=f)
    f.close()


# Phase 3 Habituation ===================================================
def habituation_3(subj, condition_p3, skip_to_3, path, screen, tk, screen_width, screen_height):
    start_time = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')  # get current date time
    background_black = (0, 0, 0)  # black
    background_white = (255, 255, 255)  # white
    psypsyinterface.clear_screen(screen, background_black)
    # Path to files ==========================================================
    # path to experiment materials
    phase3_path = "_experimental_suite\Exp_1_looking_time\\2018tsi_nn"
    hab_video_path = phase3_path + "\hab_test\\"

    # Stimuli Path
    stimuli_file = "_experimental_suite\exp1_p3_test_trial_.csv"

    # output
    output = "_experimental_suite\\results\exp1_p3_results_{}.csv".format(participant_id)

    # Check experiment condition ==============================================
    u = "u"
    y = "y"

    if skip_to_3:
        u = "a"
        y = "i"

    if condition_p3 == "u-c":
        habituation = u
    elif condition_p3 == "u-s":
        habituation = u
    elif condition_p3 == "y-c":
        habituation = y
    elif condition_p3 == "y-s":
        habituation = y
    else:
        raise ValueError('something is wrong in condition')

    # Start Experiment =======================================================


    # Attention-getter ==================================
    # loop video until there's a key press
    trial_on = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    trial_start = pygame.time.get_ticks()
    duration=0
    trial_off=False
    write_result_phase3(output, subj, start_time, condition_p3, "1", trial_on, trial_off,
                        "gaze on", duration, "attention-getter", "spiral.mov", "NA",startend="attentionSTART")
    attention_getter = "_experimental_suite\Exp_1_looking_time\\2018tsi_nn\\attention-getter\spiral.mov"
    loop=psypsyvideo.play_video_loop(attention_getter, screen, tk, -1)
    print("Looping video...")
    check_exit(loop)
    trial_end = pygame.time.get_ticks()
    duration = trial_end - trial_start
    trial_off = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

    write_result_phase3(output, subj, start_time, condition_p3, "1", trial_on, trial_off,
                        "gaze on", duration, "attention-getter", "spiral.mov", "NA",startend="attentionEND")

    psypsyinterface.clear_screen(screen, background_black)

    # Habituation section ====================================================

    trial_duration_list = []
    hab_i = 1
    while hab_i < 24:  # reach 24 habituation trial

        # Attention-getter ==================================
        # loop video until there's a key press
        trial_on = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        trial_start = pygame.time.get_ticks()
        write_result_phase3(output, subj, start_time, condition_p3, str(hab_i + 2), trial_on, trial_off,
                            "gaze on", duration, "attention-getter", "spiral.mov", "NA",startend="attentionSTART")
        loop=psypsyvideo.play_video_loop(attention_getter, screen, tk, -1)
        check_exit(loop)

        trial_end = pygame.time.get_ticks()
        duration = trial_end - trial_start
        trial_off = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

        write_result_phase3(output, subj, start_time, condition_p3, str(hab_i + 2), trial_on, trial_off,
                            "gaze on", duration, "attention-getter", "spiral.mov", "NA",startend="attentionEND")

        psypsyinterface.clear_screen(screen, background_black)

        trial_on = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        trial_start = pygame.time.get_ticks()
        habituation_file="habituation.mov"
        habituation_trial_video = hab_video_path+"habituation.mov"
        clip_habituation = VideoFileClip(habituation_trial_video)
        log = "NA"
        # Habituation trial
        # Trial ends when the movie finishes, or when there's no key press for the last 2 seconds
        tagEvent("TRIALSTART", hab_i, trial_on, trial_off,
                 "end", "habituation", habituation_file)
        key = psypsyvideo.play_video_2s(clip_habituation, screen,tk)
        check_exit(key)
        trial_end = pygame.time.get_ticks()
        duration = trial_end - trial_start
        trial_off = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

        trial_duration_list.append(duration)

        # Calculate average duration
        if len(trial_duration_list) > 3:
            order = trial_duration_list[:]
            ordered = sorted(order)
            average_duration_long = int((ordered[-1] + ordered[-2] + ordered[-3]) / 3)
            last_three_duration = int((trial_duration_list[-1] + trial_duration_list[-2] + trial_duration_list[-3]) / 3)
            log = str(average_duration_long) + " / " + str(last_three_duration)
            if last_three_duration < (average_duration_long * 0.5):
                log = str(average_duration_long) + " / " + str(last_three_duration) + "_criterion_met"
                write_result_phase3(output, subj, start_time, condition_p3, str(hab_i + 2), trial_on, trial_off,
                                    key, duration, "habituation", habituation_file, log,startend="criterionmet")
                break

        if hab_i == 24:
            write_result_phase3(output, subj, start_time, condition_p3, str(hab_i + 2), trial_on, trial_off,
                                key, duration, "habituation", habituation_file, log + "_24_trial",startend="24TRIAL")
        else:
            write_result_phase3(output, subj, start_time, condition_p3, str(hab_i + 2), trial_on, trial_off,
                                key, duration, "habituation", habituation_file, log,startend="TRIALEND")

        hab_i += 1

        psypsyinterface.clear_screen(screen, background_black)


    # Test trial =======================================================================
    trial, header_index = psypsyio.read_stimuli(stimuli_file, "\t")
    print(trial,header_index)

    index = 0
    for i in range(trial["trial_number"]):
        screen.fill(background_gray)
        pygame.display.flip()
        # Attention-getter ==================================
        # loop video until there's a key press
        trial_on = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        trial_start = pygame.time.get_ticks()

        write_result_phase3(output, subj, start_time, condition_p3, str(i + hab_i + 3), trial_on, trial_off,
                            "gaze on", duration, "attention-getter", "attention.mov", "NA",startend="attentionSTART")
        loop=psypsyvideo.play_video_loop(attention_getter, screen, tk, -1)
        check_exit(loop)
        trial_end = pygame.time.get_ticks()
        duration = trial_end - trial_start
        trial_off = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

        write_result_phase3(output, subj, start_time, condition_p3, str(i + hab_i + 3), trial_on, trial_off,
                            "gaze on", duration, "attention-getter", "attention.mov", "NA",startend="attentionEND")

        psypsyinterface.clear_screen(screen, background_black)

        trial_on = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        trial_start = pygame.time.get_ticks()
        # replace file name to correspond to conditions
        trial_video_file = trial[condition_p3][i]
        print("file: ",trial_video_file)
        if skip_to_3:
            trial_video_file = trial_video_file
            #trial_video_file = re.sub(r"u", "a", trial_video_file) kk
            #trial_video_file = re.sub(r"y", "i", trial_video_file) kk

        #video_file = hab_video_path + "test-" + trial_video_file + "_trial" + ".mp4" kk
        video_file=hab_video_path+trial_video_file+".mov"
        print(video_file)
        video_file=VideoFileClip(video_file)
        tagEvent("TRIALSTART", i, trial_on, trial_off,
                 "end", "test", str(video_file))
        # Each trial ends when the sound file finishes, or when there's a key press
        # test_video = VideoFileClip(video_file)
        key = psypsyvideo.play_video_2s(video_file, screen,tk)
        check_exit(key)
        trial_end = pygame.time.get_ticks()
        duration = trial_end - trial_start
        trial_off = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        write_result_phase3(output, subj, start_time, condition_p3, str(i + hab_i + 3), trial_on, trial_off,
                            key, duration, "test", trial_video_file, "NA",startend="TRIALEND")

        index = i + hab_i + 4

    psypsyinterface.clear_screen(screen, background_black)
    pygame.quit()

# MAIN =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*

if __name__ == "__main__":

    ################ EYET INFOS ########################
    pylink.flushGetkeyQueue()
    EDF = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    eye = None  # left ("left") or right ("right") eye used for EyeLink. Used for gaze contingent display
    last_ET = 0  # last gaze position
    # Getting the radius of the space of the central fixation point
    TRACKER_FX_RADIUS = 900
    TRACKER_FX_RADIUS_screen = 1600
    RESOLUTION = [1280, 900]  # [1280,720][1600,900]#


    tracker = True
    # Set a few task parameters
    useGUI = True  # whether use the Psychopy GUI module to collect subject information
    dummyMode = not tracker  # If in Dummy Mode, press ESCAPE to skip calibration/validataion

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
    screen, screen_width, screen_height = psypsyinterface.initialisation_pygame((200, 200, 200))

    #### MONITOR INFO: Initialize custom graphics for camera setup & drift correction ##################

    #################
    ## SET MONITOR ##
    pylink.openGraphics([screen_width, screen_height])

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
    tk.sendCommand("screen_pixel_coords = 0 0 %d %d" % (screen_width - 1, screen_height - 1))

    # stamp display resolution in EDF data file for Data Viewer integration
    # [see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration]
    tk.sendMessage("DISPLAY_COORDS = 0 0 %d %d" % (screen_width - 1, screen_height - 1))

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
    initial_screen(screen)
    tk.doTrackerSetup()
    # sys.argv
    skip_to_3 = False
    participant_id = particNum
    condition_p3 = "c"
    # Parameters  =*=*=**=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=**=*=*=*=*=*=*=*=*=*=*
    # == Experiment path =*=*=**=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
    path = {
            "path": "Exp_1_looking_time/",
            # Phase 1
            "phase1": "2018tsi_audiovisual/",
            # Phase 2
            "phase2": "2018tsi_lex/",
            # Phase 3
            "phase3": "2018tsi_nn/"
    }

    # == Program environment parameter =*=*=*=**=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*

    background_gray = (100,100,100)  # light gray
    background_black = (0, 0, 0)  # black
    background_white = (255, 255, 255)  # white
    # Initialisation Pygame

    screen, screen_width, screen_height = psypsyinterface.initialisation_pygame(background_gray)
    pygame.mouse.set_visible(0)
    # Experiment procedure
    trackerOn()
    running=True
    habituation_3(participant_id, "c", skip_to_3, path, screen, tk, screen_width, screen_height)
    print("tracker off")
    trackerOff()
    print("tracker closing")
    trackerClose()

