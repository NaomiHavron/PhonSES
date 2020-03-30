#!C:\Program Files (x86)\PsychoPy2\python27.exe
from psychopy import gui,core, visual,monitors
import subprocess
import cv2

###### EXPERIMENTS LOCATIONS #######

python="D:\PsychoPy2\python27.exe"
exp1="D:\Manips\Chiara\Phonses\Wordfreqs\\freqsword.py"
exp2="D:\Manips\Chiara\Phonses\LookingListening\lookingwhilelisten.py"
exp3="D:\Manips\Chiara\Phonses\_experimental_suite\habit_2.py"

def select_exp():
    """Select Experiment"""
    exp = {'Which experiments do you want to run? \n\n 0: Run all tasks'
           ' \n 1: Hab and LWL \n 2: Hab and WF \n 3: LWL and WF \n 4: LWL only \n 5: Hab only \n 6: WF only': '0'}
    useGUI = True
    if useGUI:
        dlg = gui.DlgFromDict(dictionary=exp, title="Experiment to run")
        if dlg.OK == False:
            core.quit()  # user pressed cancel
    exp_list = list(exp.values())[0]
    if exp_list=="0":
        exp_list=[exp1, exp3, exp2] # Run all three experiments
    elif exp_list=="1":
        exp_list=[exp2,exp3] # Run only habituation and LWL
    elif exp_list=="2":
        exp_list = [exp3, exp1]
    elif exp_list=="3":
        exp_list = [exp1, exp2]
    elif exp_list == "4":
        exp_list = [exp2]  # Run only LWL
    elif exp_list=="5":
        exp_list = [exp3]  # Run only habituation
    elif exp_list=="6":
        exp_list = [exp1]  # Run only WF
    return exp_list

def get_partinfo():
    """Collect participant Info"""
    expInfo = {'SubjectNO': '00', 'SubjectName': 'AA'}
    useGUI = True
    if useGUI:
        dlg = gui.DlgFromDict(dictionary=expInfo, title="Participant Information", order=['SubjectNO', 'SubjectName'])
        if dlg.OK == False:
            core.quit()  # user pressed cancel
    else:
        expInfo['SubjectNo'] = raw_input('Subject # (1-99): ')
        expInfo['SubjectName'] = raw_input('Subject Name')
    particInfo = list(expInfo.values())
    return particInfo

def PlayVid():
    """Introduction Video: to exit, close manually and wait for experiment to start"""
    process = subprocess.Popen(
        ["C:/Program Files/VideoLAN/VLC/vlc.exe", "D:\Manips\Chiara\Phonses\\fantasia.avi", "--fullscreen"])
    core.wait(1)
    while process.poll() == None: 
        continue


def start_routine():
    """Run experiments one after the other in random order"""
    exp_list = select_exp()
    particInfo = get_partinfo()
    particNum = (int(particInfo[1]))
    if (particNum % 2) == 0 and len(exp_list) == 3:
        exp_list.reverse()
    "The order of this participant's experiments is {}".format(exp_list)
    PlayVid()
    for i in exp_list:
        if i != exp3:
            cmd1 = [python, i, "{}".format(particInfo)]
        else:
            cmd1 = [python, i, "{}".format(particInfo)]
        print "Running {}".format(i)
        subprocess.call(cmd1)

cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
img = cv2.imread("C:\Users\lscpuser.BABYLAB2\Desktop\\baby.jpg")
cv2.imshow("window", img)
start_routine()
cv2.waitKey(0)
cv2.destroyAllWindows()
