import os
import json
import tkinter
import subprocess
from PIL import Image
from PIL import ImageDraw
import PIL.Image
import PIL.ImageTk
import pyfireconnect
import RPi.GPIO as GPIO
import serial
import sys
import threading
from threading import Thread
import time
from tkinter import *
from tkinter import ttk
import tkinter.font as font
import urllib.request
import multiprocessing


#GROTECONNECT
import zmq
import datetime
import psycopg2
import psycopg2.extras
from uuid import getnode as get_mac
import fcntl, socket, struct

from smart.delegator import delegator
from smart.delegator import getGeoSensorAttribute
from smart.delegator import updateGeoSensorAttribute
from smart.delegator import incrementGeoSensorAttributeLocal
from smart.delegator import setCurrentGeoSensorAttributeLocal
# from smart.store import smart  # Import the singleton instance
# from smart.smart_util import * # Import utilities we need
class smart:filepath='/usr/data'
# Sm^rt Cutter Software
_version = '1.0.0'
_iiotd_version = '1193'
_update = '2023-05-24'
_hardware = 'Touch'
_location = 'Orange'
_power = True

p_conn = None  # psql connection
i_mac = None  # the interface MAC used as identification of this GroteNode

context_zmq = zmq.Context()
socket_zmq = context_zmq.socket(zmq.PUB)
print("socket created")
# this stopped working: zmq.error.ZMQError: Address already in use
#socket_zmq.bind("tcp://127.0.0.1:5680")
#print("socket connected")


#initial saucer mac needs to be like..... DCA6324738780400
def getHwAddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    # return ':'.join('%02X' % b for b in info[18:24])
    # return '{0:02X}'.format(b for b in info[18:24]).join('0400')
    return f"{info[18]:02X}" + f"{info[19]:02X}" + f"{info[20]:02X}" + f"{info[21]:02X}" + f"{info[22]:02X}" + f"{info[23]:02X}" + f"{4:02X}" + f"{0:02X}"


def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial.upper()


filepath = '/usr/data/donatos/'

if os.environ.get('DISPLAY', '') == '':
    print('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')

if i_mac is None or "00:00:00:00:00:00":
    try:
        i_mac = getserial()
    except:
        i_mac = "00:00:00:00:00:00"
        print("ERROR: MAC of eth0 [" + i_mac + "]")
    finally:
        print("MAC of eth0 [" + str(i_mac) + "]")


def delegator():
    """ Connect to the PostgreSQL database server """
    global p_conn
    global i_mac

    if p_conn is None or p_conn.closed:
        try:
            # connect to the PostgreSQL server
            # conn.cursor will return a cursor object, you can use this query to perform queries
            # note that in this example we pass a cursor_factory argument that will
            # dictionary cursor so COLUMNS will be returned as a dictionary so we
            # can access columns by their name instead of index.
            # print('Connecting to the PostgreSQL database...')
            p_conn = psycopg2.connect(
                host="127.0.0.1",
                port="5432",
                database="groteconnect",
                user="groteconnect",
                password="D0WhutdGateway",
                cursor_factory=psycopg2.extras.DictCursor)


            # create a cursor
            # cur = p_conn.cursor()

            # execute a statement
            # print('PostgreSQL database version:')
            # cur.execute('SELECT version()')

            # display the PostgreSQL database server version
            # db_version = cur.fetchone()
            # print(db_version)

            # close the communication with the PostgreSQL
            # cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            print('DBMS ERROR Connecting to the PostgreSQL database...')
        # finally:
        #     if p_conn is not None:
        #         # conn.close()
        #         print('Database connection is open.')
    return p_conn




#         ######################## CUTTER_ON is the HEART_BEAT of the python code ##################

class Heartbeat(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.running = True
        #resets the the current count to 0, but allows the lifetime to continue incrementing
        setCurrentGeoSensorAttributeLocal("CUTTER_ON",0,1)

    def run(self):
        while self.running:
            # using now() to get current time
            now = datetime.datetime.now()

            #starts incrementing the 5 minute intervals unit is on
            incrementGeoSensorAttributeLocal("CUTTER_ON",1,1)
            print(now.strftime("%Y-%m-%d %H:%M:%S") + ': CUTTER_ON pulse created')
            time.sleep(300) # 5 minute delay
    def stop(self):
        #resets the the current count to 0, but allows the lifetime to continue incrementing
        setCurrentGeoSensorAttributeLocal("CUTTER_ON",0,1)
        self.running = False

pulse = Heartbeat()
pulse.start()

def check_internet():
    internet = False

    import urllib
    from urllib import request
    try:
        urllib.request.urlopen('http://google.com',timeout=5)
        # If you want you can add the timeout parameter to filter slower connections. i.e. urllib.request.urlopen('http://google.com', timeout=5)
        internet = True
    except:
        internet = False
    return internet


# Set timezone
os.environ['TZ'] = 'US/Eastern'
#!GROTECONNECT

# *************************************START CONNECTION**************************************
# Open UART serial connection
try: #connect to MC and define serial comm functions
    ser = serial.Serial("/dev/ttyS0",115200,writeTimeout=3)
    ser.write(('$STEPPER_START,PUMP4,FORWARD,1000,20\r\n').encode())
except:
    print('SERIAL ERROR')


# ***********************************VARIABLE DECLARATIONS***********************************

# Color variables for consistency
main_bg = "#FFFFFF"  # switched from gray20
second_bg = "#CCCDD0"
button_color = "#CCCDD0"  # switched from gray20
dough_color = "#EFE4B0"
donatos_path = filepath + "tenant_logo.png"  # switched from white
main_fg = "#000000"  # switched from FFFFFF

#convert inches to motor steps
#[200 motor steps/rev] / ([20 teeth on pulley] * [.2" pulley pitch]) * [.8 fudge factor]
inch2step = 80 #steps/in

# Variables for emergency stop
shutdown = False
running = False
global currentScreen

# *************************************BUTTON FUNCTIONS**************************************
def freeze_all_motor_function():
    ser.write(('$STEPPER_STOP,PUMP1\r\n').encode())
    ser.write(('$STEPPER_STOP,PUMP2\r\n').encode())
    ser.write(('$STEPPER_STOP,PUMP3\r\n').encode())
    ser.write(('$STEPPER_STOP,PUMP4\r\n').encode())
    ser.write(('$STEPPER_STOP,TURNTABLE\r\n').encode())
    up()    #Move actators up

def stop(emergency=False):
    global shutdown
    shutdown = True
    set_color("lime green")
    freeze_all_motor_function()
    if emergency:
    #GROTECONNECT
        incrementGeoSensorAttributeLocal("CUTTER_STOP",1,1)
    # incrementGeoSensorAttributeLocal("VIDEO_STOP",1,1)
    # socket_zmq.send_string("VIDEO_STOP")
    #!GROTECONNECT

def kill_two_screens(screen1, screen2):
    screen2.destroy()
    screen1.destroy()

# ************************************CUTTER GLOBALS***************************************
#RPI Pin Declarations
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
R_EN = 23
L_EN = 24
RPWM = 12
LPWM = 7
DOOR1 = 4
HOME = 21
EN_A = 16
EN_W = 20

#RPI Pin Setup
GPIO.setup(R_EN, GPIO.OUT)
GPIO.setup(L_EN, GPIO.OUT)
GPIO.setup(RPWM, GPIO.OUT)
GPIO.setup(LPWM, GPIO.OUT)
GPIO.setup(DOOR1, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(HOME, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(EN_A, GPIO.OUT)
GPIO.setup(EN_W, GPIO.OUT)

# Variables for cut spacing
global first_cut_dist
global thin_cut_spc
global maj2_cut_spc
global maj1_cut_dist
# ************************************CUTTER FUNCTIONS***************************************

def read_info_file():
    global info
    try:
        with open(smart.filepath +'/cutterinfo.json', 'r') as reader:
            info = json.load(reader)
    except FileNotFoundError:
        print('new info file at '+smart.filepath+'/cutterinfo.json')
        info = {'slices': 0,'bladeslices':0, 'presets':{
            0:{'cuts':[4,0],'dist':[6.9, 800, 0, 0]},
            7:{'cuts':[3,1],'dist':[5.8, 1.8, 1.0, 0]},
            10:{'cuts':[5,2],'dist':[4.1, 1.7, 1.3, 3]},
            12:{'cuts':[5,2],'dist':[3.4, 2.0, 1.8, 3.5]},
            14:{'cuts':[6,2],'dist':[2.0, 2.0, 3.0, 5]},
            14.5:{'cuts':[7,2],'dist':[2.0, 1.8, 3.0, 5]}
            }}
        with open(smart.filepath + '/cutterinfo.json', 'w+') as writer:
            json.dump(info, writer)

read_info_file()
print(info)

def write_info_file():
    try:
        with open(smart.filepath + '/cutterinfo.json', 'w+') as writer:
            json.dump(info, writer)
    except PermissionError:
        print('write_info_file() permission error, line 296-ish')
        pass

def up():
    GPIO.output(R_EN,GPIO.HIGH)
    try:
        rpwm = GPIO.PWM(L_EN, 1000)
        rpwm.start(100)
        time.sleep(0.4)
        rpwm.ChangeDutyCycle(0)
        rpwm.stop()
    except RuntimeError: pass
def down():
    global shutdown
    if shutdown: return #immobilize for e-stop
    GPIO.output(R_EN,GPIO.LOW)
    rpwm = GPIO.PWM(L_EN, 1000)
    rpwm.start(100)
    time.sleep(0.3)
    rpwm.ChangeDutyCycle(0)
    rpwm.stop()
def turntable(steps):
    ser.write(('$STEPPER_START,TURNTABLE,FORWARD,1500,'+str(steps)+'\r\n').encode())
    time.sleep(steps*.0012)
def turntableREV(steps):
    ser.write(('$STEPPER_START,TURNTABLE,REVERSE,1500,'+str(steps)+'\r\n').encode())
    time.sleep(steps*.0012)
def gantry(steps):
    ser.write(('$STEPPER_START,PUMP4,FORWARD,100,'+str(steps)+'\r\n').encode())
    time.sleep(steps*.0008+.15)
def gantryREV(steps):
    ser.write(('$STEPPER_START,PUMP4,REVERSE,100,'+str(steps)+'\r\n').encode())
    time.sleep(steps*.0008+.15)
def air():
    while True:
        start_cut(7)
        time.sleep(13)
def water(dur=2):
    GPIO.output(EN_W,GPIO.HIGH)
    time.sleep(dur)
    GPIO.output(EN_W,GPIO.LOW)    
def home(use_ref=False):
    global shutdown
    shutdown=False
    up()
    if use_ref: ser.write(('$STEPPER_GOTO,PUMP4,0,500\r\n').encode())
    else: ser.write(('$STEPPER_START,PUMP4,REVERSE,4000,4000\r\n').encode())
    elapsed=0
    while not shutdown:
        if GPIO.input(HOME): #if switch pressed, stop and set 0 pos
            ser.write(('$STEPPER_STOP,PUMP4\r\n').encode())
            ser.write(('$STEPPER_SET_HOME_REF,PUMP4\r\n').encode())
            break
        time.sleep(0.1)
        elapsed=elapsed+1
        if elapsed>25: #timeout
            ser.write(('$STEPPER_STOP,PUMP4\r\n').encode())
            break

class LockOut(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.running = True
        #resets the the current count to 0, but allows the lifetime to continue incrementing
        # setCurrentGeoSensorAttributeLocal("CUTTER_ON",0,1)
        self.lockout=GPIO.input(DOOR1) 

    def run(self):
        global shutdown
        while self.running:
            # using now() to get current time
            now = datetime.datetime.now()
            #starts incrementing the 5 minute intervals unit is on
            # /incrementGeoSensorAttributeLocal("CUTTER_ON",1,1)
            if GPIO.input(DOOR1)!=self.lockout:
                self.lockout = GPIO.input(DOOR1)
                print(now.strftime("%Y-%m-%d %H:%M:%S") + ': door position',self.lockout)
                setCurrentGeoSensorAttributeLocal("CUTTER_DOOR_1",1,GPIO.input(DOOR1)) #using the value_current ==1 to indicate "true", will flip it at the end
                if not self.lockout: #flipped bool 20241024 J3M
                    set_active('disabled')
                    debugLabel.config(text='DOOR OPEN')
                    shutdown=True
                else:
                    set_active('active')
                    debugLabel.config(text='DOOR CLOSED')
                    shutdown=False
        time.sleep(3) # 3 seconds delay
    def stop(self):
        #resets the the current count to 0, but allows the lifetime to continue incrementing
        # setCurrentGeoSensorAttributeLocal("CUTTER_ON",0,1)
        self.running = False

tagOut = LockOut()
#tagOut.start()

# **************************************RUN SIZE FUNCTIONS**************************************

def start_cut(sz):
    global shutdown
    shutdown=False
    debugLabel.config(text='RUNNING '+str(sz))
    set_active('disabled')
    if sz==0: run_process = multiprocessing.Process(target=run_pie_cut)
    else: run_process = multiprocessing.Process(target=run_cut, args=(sz,))
    run_process.daemon=True
    run_process.start()    
    def check_stop():
        global shutdown
        global debugLabel
        startTime=time.time() #timeout counter to prevent buildup of active threads of stop_thread
        while shutdown==False and run_process.is_alive(): 
            run_process.join(0.1)
        debugLabel.config(text=str(round(time.time()-startTime,1))+' seconds')
        run_process.terminate()
        freeze_all_motor_function()
        #tagOut.lockout=1-tagOut.lockout #force door check on cycle stop
        print("STOPPING**************************************************")
    stop_thread = threading.Thread(target=check_stop)
    stop_thread.start()
#     run_process.join()
#     stop_thread.join()
#     set_active('active')
        
def run_cut(sz):
    global shutdown
    shutdown=False
    global info
    global inch2step
    global first_cut_dist #From the home postition to the first cut on the pizza
    global thin_cut_spc #Distance between pizza slices
    global maj2_cut_spc #Distance between the two major cuts
    global maj1_cut_dist #Last cut distnce away from the home position
    global geoSensorAttribute
#     set_active('disabled')
    num_cuts = info['presets'][str(sz)]['cuts']
    first_cut_dist = info['presets'][str(sz)]['dist'][0]*inch2step
    thin_cut_spc = info['presets'][str(sz)]['dist'][1]*inch2step
    tt_rot=850
    maj1_cut_dist = info['presets'][str(sz)]['dist'][2]*inch2step
    maj2_cut_spc = info['presets'][str(sz)]['dist'][3]*inch2step
    
    setCurrentGeoSensorAttributeLocal("CUTTER_RUNNING",1,1) #using the value_current ==1 to indicate "true", will flip it at the end
    now = datetime.datetime.now()
    print(now.strftime("%Y-%m-%d %H:%M:%S") + ": PARTY CUTTING PIZZA SIZE: " + str(sz))
    paramstr=str(first_cut_dist)+' '+str(thin_cut_spc)+' '+str(maj1_cut_dist)+' '+str(maj2_cut_spc)
    print(' params: '+paramstr)
    socket_zmq.send_string("VIDEO_COUNT_" + str(sz))
    print("IPC to socket_zmq:")

    #report the status of the doors
    # if(GPIO.input(DOOR1) == False):
    #     setCurrentGeoSensorAttributeLocal("CUTTER_DOOR_1",1,0) #using the value_current ==1 to indicate "true", will flip it at the end
    #     print("Door1 Closed")
    # else:
    #     setCurrentGeoSensorAttributeLocal("CUTTER_DOOR_1",1,1) #using the value_current ==1 to indicate "true", will flip it at the end
    #     print("Door1 Open")
    #
    currentTime = time.time()
    home()
    gantry(first_cut_dist)
    down() #Cut 1
    up()
    for i in range(1,num_cuts[0]):
        gantry(thin_cut_spc)
        down() #Cut 2...n
        up()
    TT=threading.Thread(target=gantryREV, args=(maj1_cut_dist,))
    TT.start()
    turntable(tt_rot)
    down() #Cut 1 transverse
    up()
    for i in range(1,num_cuts[1]):
        gantryREV(maj2_cut_spc)
        down() #Cut 2...m transverse
        up()
    TT=threading.Thread(target=turntableREV, args=(tt_rot,))
    TT.start()
    home(1)
    #Clean blade
#     set_active('normal')
    endTime = time.time()
    finalTime = str(round(endTime-currentTime,1))+' seconds'
    print('cycle time = ',finalTime)
    setCurrentGeoSensorAttributeLocal("CUTTER_RUNNING",1,0) #using the value_current ==1 to indicate "true", will flip it at the end
    if not shutdown: # Update if emergency stop was not made
        incrementGeoSensorAttributeLocal("CUT_COUNT_" + str(sz),1,1)
    shutdown=True #trigger run_process terminate?

def run_pie_cut():
    global shutdown
    shutdown=False
    now = datetime.datetime.now()
    print(now.strftime("%Y-%m-%d %H:%M:%S") + ": PIE CUTTING PIZZA")
    home()
    cut_dist=int(info['presets']['0']['dist'][0]*inch2step) #inches*[steps/rev]/[pulley circumference]
    cut_rot=int(info['presets']['0']['dist'][1])
    gantry(cut_dist)
    for i in range(4):
        down()
        up()
        if i==3:break
        turntable(cut_rot)
    home(1)
    if not shutdown: #Update if emergency stop was not made
        incrementGeoSensorAttributeLocal("CUT_COUNT_" + "PIE",1,1)
    shutdown=True #trigger run_process terminate

# *************************************CHANGE SAUCE AMT**************************************
# Functions for setting pump amount as percentage of speeds and colors of buttons
def set_color(color):
    fourteenButton.config(bg=color, activebackground=color)
    twelveButton.config(bg=color, activebackground=color)
    tenButton.config(bg=color, activebackground=color)
    sevenButton.config(bg=color, activebackground=color)
    pieButton.config(bg=color, activebackground=color)
    halfButton.config(bg=color, activebackground=color)
#     if color!='grey40':color='red'
#     stopButton.config(bg=color, activebackground=color)

# Can activate or deactive buttons. Change mod to 0 for just size, mod anything but 0 for all but stop
def set_active(active): #active = 'normal' or 'disabled'
    fourteenButton.config(state=active)
    twelveButton.config(state=active)
    tenButton.config(state=active)
    sevenButton.config(state=active)
    homeButton.config(state=active)
    pieButton.config(state=active)
    halfButton.config(state=active)
    moreButton.config(state=active)
#     stopButton.config(state=active)
    if active == 'disabled': set_color("grey40")
    else: set_color('lime green')
    
# destroys all toplevel screen widgets. Uses to destroy all top windows to reach the home screen
def destroy_all_screens():
    for widget in screen.winfo_children():
        if isinstance(widget, Toplevel):
            widget.destroy()

# ***********************************CALIBRATION SCREEN SET UP*************************************
# Function setting up ... screen with various helpful features
def calibration_screen():
    global currentScreen
    global geoSensorAttribute
    global cut_val
    
    calib = Toplevel()
    calib.title("Cutter Calibration Screen")
    calib.geometry('800x480')
    calib.configure(bg=main_bg)
    calib.overrideredirect(1)
    #other.config(cursor="none")

    geoSensorAttributeWt = ''
    geoSensorAttributeCut = ''

    calibration_header = Label(calib, text='7″  CALIBRATION', font=heading_bold_font, bg=main_bg, justify=LEFT)
    calibration_header.place(x= 280, y = 10)
    Button(calib,text=' ',bg='white',relief=FLAT,highlightthickness=0,command=screen.destroy).place(x=785,y=0)


    # Notebook setup
    ttk.Style().configure('TNotebook.Tab', font=calib_font, background=main_bg, padding=[25,0], take_focus=0)
    size_tab = ttk.Notebook(calib)
    size_tab.place(x=120, y=50)
    frame = {0: Frame(size_tab, width=650, height=375),
             7: Frame(size_tab),
             10: Frame(size_tab),
             12: Frame(size_tab),
             14: Frame(size_tab),
             14.5: Frame(size_tab)}

    # used for incrementing values associated with sliders
    def increment(item):
        num = item.get()
        if num < 10:
            num = num + 1
            item.set(num)

    # used for decrementing the values associated with sliders
    def decrement(item):
        num = item.get()
        if num > -10:
            num = num - 1
            item.set(num)

    # When a user changes the tab, the corresponding title and test button text are changed
    def set_tab(event):
        tabname = ['PIE', '7"', '10"', '12"', '14"', 'HALF']
        sizes = [0, 7, 10, 12, 14, 14.5]
        i = size_tab.index("current")
        calibration_header.config(text='  ' + str(tabname[i]) + ' CALIBRATION')
        testButton.config(command=lambda: test_set_size(sizes[i]), text=tabname[i] + '\nTEST')


    def slider_update(sz,value):
        print("slider update sz is [" + str(sz) + "] and value [" + str(value) + "]")
        #updateGeoSensorAttribute("CUT_COUNT_" + str(sz), cut_val[sz][0].get(), cut_val[sz][1].get(), cut_val[sz][2].get(), cut_val[sz][3].get(), cut_val[sz][4].get(), cut_val[sz][5].get(), cut_val[sz][6].get())
        for i in range(4):
            print(cut_val[sz][i].get())
            info['presets'][str(sz)]['dist'][i]=cut_val[sz][i].get()
            
    read_info_file()
    cut_val={0:[],7:[],10:[],12:[],14:[],14.5:[]}
    for sz in [0, 7, 10, 12, 14, 14.5]:  # for each size tab, populate appropriate sliders and labels
        frame[sz].pack()
        xframe = 230

        if sz==0: size_tab.add(frame[sz], text='PIE')
        elif sz>14: size_tab.add(frame[sz], text='HALF')
        else: size_tab.add(frame[sz], text=str(sz)+'"')

        #query the GeoSensorAttribute table for current configurations for this SIZE and load the cut_val array
#         geoSensorAttribute =  getGeoSensorAttribute("CUT_COUNT_" + str(sz))
#         for attributeName in ["cond_value", "other_value", "lh_value", "rh_value", "x_value", "y_value", "z_value"]:
#             val = tkinter.IntVar()
#             val_str = ''
#             try:
#                 val_str = geoSensorAttribute[attributeName]
#                 val.set(int(val_str))
#             except: #set a safe default value
#                 val.set(0)
# 
#             print("val_str found from dbms [" + val_str + "] and val.get [" + str(val.get()) + "] for attributeName [" + attributeName + "] size [" + str(sz) +"]")
#             cut_val[sz].append(val)
        #load cut_val from info dictionary instead
        for i in range(4):
            cut_val[sz].append(DoubleVar())
            print(sz,i,info['presets'][str(sz)]['dist'][i])
            cut_val[sz][i].set(info['presets'][str(sz)]['dist'][i])
        
        #slider 1
        Scale(frame[sz], variable=cut_val[sz][0], command=lambda value, sz=sz: slider_update(sz, value), orient=VERTICAL, length=230, width=35, from_=8, to=0, resolution=.1, font=small_font).place(x=xframe, y=120)
        Label(frame[sz], text="First Cut\nDistance", font=med_font, bd=-2, fg='red').place(x=xframe, y=80)

        if sz>0: #for party cut
            #slider 2
            Scale(frame[sz], variable=cut_val[sz][1], command=lambda value, sz=sz: slider_update(sz, value), orient=VERTICAL, length=230, width=35, from_=3, to=1, resolution=.1, font=small_font).place(x=xframe+100, y=120)
            Label(frame[sz], text="Thin Cut\nSpacing", font=med_font, bd=-2, fg='dark turquoise').place(x=xframe+100, y=80)
            #slider 3
            Scale(frame[sz], variable=cut_val[sz][2], command=lambda value, sz=sz: slider_update(sz, value), orient=VERTICAL, length=230, width=35, from_=3.5, to=.5, resolution=.1, font=small_font).place(x=xframe+200, y=120)
            Label(frame[sz], text="Cross Cut\nDistance", font=med_font, bd=-2, fg='green').place(x=xframe+200, y=80)
        else:
            #slider 2 for pie cut only
            Scale(frame[sz], variable=cut_val[sz][1], command=lambda value, sz=sz: slider_update(sz, value), orient=VERTICAL, length=230, width=35, from_=1000, to=600, resolution=20, font=small_font).place(x=xframe+100, y=120)
            Label(frame[sz], text="Rotation\nSteps", font=med_font, bd=-2, fg='green').place(x=xframe+100, y=80)
        if info['presets'][str(sz)]['cuts'][1] > 1: #if more than one transverse cut, show spacing option
            #slider 4
            Scale(frame[sz], variable=cut_val[sz][3], command=lambda value, sz=sz: slider_update(sz, value), orient=VERTICAL, length=230, width=35, from_=5, to=0, resolution=.1, font=small_font).place(x=xframe+300, y=120)
            Label(frame[sz], text="Cross Cut\nSpacing", font=med_font, bd=-2, fg='orange').place(x=xframe+300, y=80)

        #Main cutter image
        # imgPATH = 'CCP/'+ str(sz) +'in.png'
        imgPATH = 'filepath'+ str(sz) +'in.png'
        # photo = PIL.ImageTk.PhotoImage(PIL.Image.open(imgPATH).resize((200, 200)))
        photo = PIL.ImageTk.PhotoImage(PIL.Image.open(filepath + str(sz) +'in.png').resize((200, 200)))
        img = Label(frame[sz], image=photo)
        img.photo = photo
        img.pack()
        img.place(x=20, y=120)
    # Like set_active but for the test button
    # Changes the state of all widgets on the config screen
    def test_set_active(active, _):
        testButton.config(state=active)
        homeButton.config(state=active)
        helpButton.config(state=active)
        wifiButton.config(state=active)
        idx = size_tab.index("current")

    size_tab.bind('<<NotebookTabChanged>>',set_tab)
    # Like set_size but for the test button. Calls run_saucer but passes test_set_active and deactivates calibration widgets
    def test_set_size(sz):
        global size
        size = sz
        #test_set_active('disabled', '')
        write_info_file()
        start_cut(sz)
        #test_set_active('enabled', '')

    # Like emergency stop, but for the test button. This stops the test from running.
    def test_emergency_stop():
        global shutdown
        shutdown = True
        testButton.config(bg="lime green", activebackground="lime green")
        #GROTECONNECT
        incrementGeoSensorAttributeLocal("CUTTER_STOP",1,1)
        # incrementGeoSensorAttributeLocal("VIDEO_STOP",1,1)
        # socket_zmq.send_string("VIDEO_STOP")
        test_set_active('normal', '')


    homeButton = Button(calib, text="HOME", font=heading_font, activebackground=button_color, bg=button_color,
                        fg=main_fg,
                        command=lambda: [destroy_all_screens(),write_info_file()], height=3, width=5)
    homeButton.place(x=0, y=0)

    helpButton = Button(calib, text="HELP", font=heading_font, activebackground=button_color, bg=button_color,
                        fg=main_fg,
                        command=lambda: [trouble_shooting_screen()], height=3, width=5)
    helpButton.place(x=0, y=95)

    wifiButton = Button(calib, text="WIFI", font=heading_font, activebackground=button_color, bg=button_color,
                        fg=main_fg,
                        command=lambda: [wifi_screen()], height=3, width=5)
    wifiButton.place(x=0, y=190)
    testButton = Button(calib, text=" \nTEST", font=heading_font, activebackground="lime green", activeforeground="white",
                        bg="lime green", fg="white", disabledforeground="white", command=lambda: test_set_size(7),
                        height=3, width=5)
    testButton.place(x=0, y=285)
    stopTestButton = Button(calib, text='STOP', font=heading_font, activebackground="red", activeforeground="white", bg="red",
                            fg="white", disabledforeground="white", command=test_emergency_stop, height=3, width=5)
    stopTestButton.place(x=0, y=380)


def trouble_shooting_screen():
    global speed
    global currentScreen

    tss = Toplevel()
    tss.title("Cutter Troubleshooting Screen")
    tss.geometry('800x480')
    # tss.geometry('1024x600')
    tss.configure(bg=main_bg)
    tss.overrideredirect(1)
    tss.config(cursor="none")

    imgs = []
    imgButton = []
    buttonLabel = ['Under Weight', 'Over Weight', 'Missing Ring', 'Heavy Ring', 'Center Hole', 'Center Puddle',
                   'Off Center', 'Far From Edge', 'Other Issue']
    buttonText = [
        'In the settings screen, select the appropriate size tab and increase the weight slider for the amount of sauce being applied',
        'In the settings screen, select the appropriate size tab and decrease the weight slider for the amount of sauce being applied',
        'In the settings screen, select the appropriate size tab and increase the zone slider for the missing ring',
        'In the settings screen, select the appropriate size tab and decrease the zone slider for the heavy ring',
        'Brush out center nozzle holes',
        'Brush out all nozzle holes',
        'Center dough and pan on turntable',
        'Push nozzle blocks all the way back in the holder',
        'Call Craig at 614-226-4421\n\n']
    help_var = StringVar()
    help_var.set('Troubleshooting help: select an issue for assistance')
    xcoord = [0, 1, 2, 0, 1, 2, 0, 1, 2]
    ycoord = [0, 0, 0, 1, 1, 1, 2, 2, 2]
    helptext = Text(tss, font=heading_font, wrap=WORD, bg='white', fg=main_fg, width=18, height=14)
    helptext.insert(INSERT, help_var.get())
    helptext.place(x=110, y=10)
    for i in range(9):
        xcoord[i] = xcoord[i] * 120 + 400
        ycoord[i] = ycoord[i] * 140 + 20
        imgs.append(PIL.ImageTk.PhotoImage(
            PIL.Image.open(filepath + 'ts' + str(i + 1) + '.png').resize((100, 100), PIL.Image.ANTIALIAS)))
        imgButton.append(
            Button(tss, text=buttonLabel[i], image=imgs[i], compound=TOP, font=small_font, bg=button_color,
                   fg=main_fg))
        imgButton[i].photo = imgs[i]
        imgButton[i].config(command=lambda i=i: [helptext.delete('1.0', END), helptext.insert(INSERT, buttonText[i])])
        imgButton[i].place(x=xcoord[i], y=ycoord[i])

    homeButton = Button(tss, text="HOME", font=heading_font, activebackground=button_color, bg=button_color,
                        fg=main_fg,
                        command=lambda: [destroy_all_screens()], height=3, width=5)
    homeButton.place(x=0, y=0)
    dataButton = Button(tss, text="BACK", font=heading_font, activebackground=button_color, bg=button_color,
                        fg=main_fg,
                        command=lambda: [tss.destroy()], height=3, width=5)
    dataButton.place(x=0, y=95)


# def wifi_screen():
#     wfs = Toplevel()
#     wfs.title("Cutter Wifi Screen")
#     wfs.geometry('800x480')
#     # wfs.geometry('1024x600')
#     wfs.configure(bg=main_bg)
#     wfs.overrideredirect(1)
#     wfs.config(cursor="none")
# 
#     class _PopupKeyboard(Toplevel):
#         """
#         A Top level instance that displays a keyboard that is attached to
#         another widget. Only the Entry widget has a subclass in this version.
#         """
# 
#         def __init__(self, parent, attach, x, y, keycolor, keysize=5):
#             """
#             Popup Keyboard
#             :param parent: parent
#             :param attach: is attached to
#             :param x: x position
#             :param y: y position
#             :param keycolor: key color
#             :param keysize: key size
#             """
#             Toplevel.__init__(self, takefocus=0)
# 
#             # self.overrideredirect(True)
#             self.attributes('-alpha', 0.85)
# 
#             self.parent = parent
#             self.attach = attach
#             self.keysize = keysize
#             self.keycolor = keycolor
#             self.x = x
#             self.y = y
# 
#             self.board = Frame(self.parent)
#             self.board.place(x=35, y=300)
# 
#             self.normal_keys = Frame(self.board)
#             self.normal_keys.pack(fill=BOTH)
# 
#             self.row0 = Frame(self.normal_keys)
#             self.row1 = Frame(self.normal_keys)
#             self.row2 = Frame(self.normal_keys)
#             self.row3 = Frame(self.normal_keys)
#             self.row4 = Frame(self.normal_keys)
# 
#             self.row0.grid(row=0)
#             self.row1.grid(row=1)
#             self.row2.grid(row=2)
#             self.row3.grid(row=3)
#             self.row4.grid(row=4, columnspan=5, sticky=W + E + N + S)
# 
#             self.shift_keys = Frame(self.board)
#             self.s_row0 = Frame(self.shift_keys)
#             self.s_row1 = Frame(self.shift_keys)
#             self.s_row2 = Frame(self.shift_keys)
#             self.s_row3 = Frame(self.shift_keys)
#             self.s_row4 = Frame(self.shift_keys)
# 
#             self.s_row0.grid(row=0)
#             self.s_row1.grid(row=1)
#             self.s_row2.grid(row=2)
#             self.s_row3.grid(row=3)
#             self.s_row4.grid(row=4, columnspan=5, sticky=W + E + N + S)
# 
#             self._init_keys()
# 
#             # resize to fit keys
#             # self.update_idletasks()
# 
#             # x = (self.winfo_screenwidth() - self.winfo_width()) / 2
#             # y = (self.winfo_screenheight() - self.winfo_height()) - 20
# 
#             # self.geometry('{}x{} + {} + {}'.format(self.winfo_width(),
#             #                                    self.winfo_height(),
#             #                                    x, y))
# 
#             self.geometry('{}x{}'.format(self.winfo_width(),
#                                          self.winfo_height()))
# 
#         def _init_keys(self):
#             self.alpha = {
#                 'row0': ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '<-'],
#                 'row1': ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
#                 'row2': ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'Enter'],
#                 'row3': ['Shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'],
#                 'row4': ['Space']
#             }
# 
#             self.shift_alpha = {
#                 'row0': ['~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '<-'],
#                 'row1': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '|'],
#                 'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"', 'Enter'],
#                 'row3': ['Shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?'],
#                 'row4': ['Space']
#             }
# 
#             for row in self.alpha:  # iterate over dictionary of rows
#                 if row == 'row0':
#                     i = 1  # for readability and functionality
#                     for k in self.alpha[row]:
#                         Button(self.row0,
#                                text=k,
#                                width=self.keysize,
#                                bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=i)
#                         i += 1
#                 if row == 'row1':  # TO-DO: re-write this method
#                     i = 1  # for readability and functionality
#                     for k in self.alpha[row]:
#                         Button(self.row1,
#                                text=k,
#                                width=self.keysize,
#                                bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=i)
#                         i += 1
#                 elif row == 'row2':
#                     i = 2
#                     for k in self.alpha[row]:
#                         Button(self.row2,
#                                text=k,
#                                width=self.keysize,
#                                bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=i)
#                         i += 1
#                 elif row == 'row3':
#                     i = 2
#                     for k in self.alpha[row]:
#                         Button(self.row3,
#                                text=k,
#                                width=self.keysize,
#                                bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=i)
#                         i += 1
#                 elif row == 'row4':
#                     i = 3
#                     for k in self.alpha[row]:
#                         Button(self.row4, text=k, width=self.keysize, bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).pack(fill=X)
#                         i += 1
# 
#             for row in self.shift_alpha:  # iterate over dictionary of rows
#                 if row == 'row0':
#                     i = 1  # for readability and functionality
#                     for k in self.shift_alpha[row]:
#                         Button(self.s_row0,
#                                text=k,
#                                width=self.keysize,
#                                bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=i)
#                         i += 1
#                 if row == 'row1':
#                     i = 1  # for readability and functionality
#                     for k in self.shift_alpha[row]:
#                         Button(self.s_row1,
#                                text=k,
#                                width=self.keysize,
#                                bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=i)
#                         i += 1
#                 elif row == 'row2':
#                     i = 2
#                     for k in self.shift_alpha[row]:
#                         Button(self.s_row2,
#                                text=k,
#                                width=self.keysize,
#                                bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=i)
#                         i += 1
#                 elif row == 'row3':
#                     i = 2
#                     for k in self.shift_alpha[row]:
#                         Button(self.s_row3,
#                                text=k,
#                                width=self.keysize,
#                                bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=i)
#                         i += 1
#                 elif row == 'row4':
#                     i = 3
#                     for k in self.shift_alpha[row]:
#                         Button(self.s_row4, text=k, width=self.keysize, bg=self.keycolor,
#                                command=lambda k=k: self._attach_key_press(k)).pack(fill=X)
#                         i += 1
# 
#         def destroy_popup(self):
#             self.destroy()
# 
#         def _attach_key_press(self, k):
#             if k == 'Space':
#                 self.attach.insert(END, ' ')
# 
#             elif k == 'Shift':
#                 if self.normal_keys.winfo_ismapped():
#                     self.normal_keys.pack_forget()
#                     self.shift_keys.pack(fill=BOTH)
#                 else:
#                     self.shift_keys.pack_forget()
#                     self.normal_keys.pack(fill=BOTH)
# 
#             elif k == '<-':
#                 self.attach.delete(len(self.attach.get()) - 1)
# 
#             elif k == 'Enter':
#                 self.attach.event_generate('<<Fout>>')
# 
#             else:
#                 self.attach.insert(END, k)
# 
#     class KeyboardEntry(Frame):
#         """
#         A entry widget with a popup keyboard subclass. Input in widget
#         using the popup keyboard.
#         """
#         def __init__(self, parent, keysize=3, keycolor='white', *args, **kwargs):
#             Frame.__init__(self, parent)
#             self.parent = parent
# 
#             self.entry = Entry(self, *args, **kwargs)
#             self.entry.pack()
# 
#             self.keysize = keysize
#             self.keycolor = keycolor
# 
#             self.state = 'idle'
# 
#             self.entry.bind('<Button-1>', self._call_popup)
#             self.entry.bind('<<Fout>>', self._destroy_popup)
#             self.entry.bind('<FocusOut>', self._destroy_popup)
# 
#         def _call_popup(self, event):
# 
#             if (not hasattr(self, 'kb')) or (hasattr(self, 'kb') and self.kb is None):
#                 self.kb = _PopupKeyboard(attach=self.entry, parent=self.parent, x=self.entry.winfo_rootx(),
#                                          y=self.entry.winfo_rooty() + self.entry.winfo_reqheight(),
#                                          keysize=self.keysize,
#                                          keycolor=self.keycolor)
#             elif not hasattr(self, 'kb'):
#                 self.kb = _PopupKeyboard(attach=self.entry, parent=self.parent, x=self.entry.winfo_rootx(),
#                                          y=self.entry.winfo_rooty() + self.entry.winfo_reqheight(),
#                                          keysize=self.keysize,
#                                          keycolor=self.keycolor)
# 
#         def _destroy_popup(self, event):
#             if hasattr(self, 'kb'):
#                 if self.kb is not None:
#                     self.kb.destroy_popup()
#                 self.kb = None
# 
#         def get_text(self):
#             text = self.entry.get()
#             self.entry.delete(0, 'end')
#             return text
# 
#         def replace(self, newtext):
#             self.entry.delete(0,'end')
#             self.entry.insert(0, newtext)
# 
#     # Adds wifi config to local json
#     def CreateWifiConfig(SSID, password):
# 
#         print("-> Adding wifi")
# 
#         # List the networks in wpa_supplicant.conf
#         def network_list():
#             networks = subprocess.check_output("wpa_cli list_network", shell=True)
#             networks = networks.decode("utf-8")
#             networks = networks.split("flags")[1]
#             networks = networks.split("\n")
#             networks = [n.replace("\tany\t","") for n in networks]
#             networks = [n.replace("[DISABLED]","") for n in networks]
#             networks = [n.replace("[ENABLED]","") for n in networks]
#             networks = [n[(int(n.find("\t"))+1):] for n in networks]
#             networks = [*set(list(filter(None, networks)))]
#             return networks
# 
#         networks = network_list()
# 
#         if SSID in networks:
#             # If SSID config already exists, remove it
#             subprocess.call(f"wpa_cli remove_network {networks.index(SSID)}", shell=True)
#             # Get networks list again
#             networks = network_list()
# 
#         # Add a network
#         subprocess.call("wpa_cli add_network", shell=True)
# 
#         # New network will be the last entry in the list of configs
#         new_entry_num = len(networks)
# 
#         # Set the new network SSID
#         subprocess.call(f"wpa_cli set_network {new_entry_num} ssid '\"{SSID}\"'", shell=True)
# 
#         # Set the new network password
#         subprocess.call(f"wpa_cli set_network {new_entry_num} psk '\"{password}\"'", shell=True)
# 
#         # Set the new network key_mgmt
#         subprocess.call(f"wpa_cli set_network {new_entry_num} key_mgmt 'WPA-PSK'", shell=True)
# 
#         # Enable the new network
#         subprocess.call(f"wpa_cli enable {new_entry_num}", shell=True)
# 
#         # Save the config
#         subprocess.call(f"wpa_cli save_config", shell=True)
# 
#         # Select the new network
#         subprocess.call(f"wpa_cli select_network {new_entry_num}", shell=True)
# 
#         # Reconfigure wifi, retry to connect to networks without restarting
#         subprocess.Popen(f"wpa_cli -i wlan0 reconfigure", shell=True)
# 
#         print("-> Wifi added !")
# 
#     # Adds wifi config to local json
#     def ListWifiConfigs():
#         print("-> Retrieving configs")
# 
#         try:
#             # Read file WPA suppliant
#             networks = []
#             with open("/etc/wpa_supplicant/wpa_supplicant.conf", "r") as f:
#                 in_lines = f.readlines()
# 
#             # Discover networks
#             out_lines = []
#             networks = []
#             i = 0
#             isInside = False
#             for line in in_lines:
#                 if "network={" == line.strip().replace(" ", ""):
#                     networks.append({})
#                     isInside = True
#                 elif "}" == line.strip().replace(" ", ""):
#                     i += 1
#                     isInside = False
#                 elif isInside:
#                     key_value = line.strip().split("=")
#                     networks[i][key_value[0]] = key_value[1]
#                 else:
#                     out_lines.append(line)
#             return networks
#         except:
#             return {}
# 
#     # Lists wireless networks ssids available
#     def ListSSIDS():
#         ssids = []
#         for attempt in range(3):
#             try:
#                 ssids = subprocess.check_output("sudo iwlist wlan0 scan |grep -i SSID", shell=True)
#                 ssids = ssids.decode("utf-8")
#                 ssids = ssids.split("\n")
#                 ssids = [s.strip() for s in ssids]
#                 ssids = [s.replace("\"","") for s in ssids]
#                 ssids = [s.replace("ESSID:","") for s in ssids]
#                 ssids = [*set(list(filter(None, ssids)))]
#                 ssids = sorted(ssids)
#             except subprocess.CalledProcessError as e:
#                 ssids = []
#             else:
#                 break
# 
#         return ssids
# 
# 
#     # Shows if the saucer is connected to wifi or not
#     wifiOnImg = PIL.ImageTk.PhotoImage(PIL.Image.open(filepath + 'wifiOn.png'))
#     wifiOffImg = PIL.ImageTk.PhotoImage(PIL.Image.open(filepath + 'wifiOff.png'))
# 
#     wifi_info = "No internet connection!"
# 
#     if check_internet():
#         wifiLabel = Label(wfs, image=wifiOnImg, bg=main_bg, width=43, height=43)
#         wifiLabel.image = wifiOnImg
#         wifi_info = "Connected to the internet"
#     else:
#         wifiLabel = Label(wfs, image=wifiOffImg, bg=main_bg, width=43, height=43)
#         wifiLabel.image = wifiOffImg
#     wifiLabel.place(x=150, y=20)
# 
#     wifi_label = Label(wfs, text=wifi_info, font=data_size_font, bg=main_bg)
#     wifi_label.place(x=200, y=20)
# 
#     # **** LOCAL WIFI CONFIGS ****
# 
#     global wifi_configs
#     wifi_configs = []
# 
#     def fill_wifi_configs_list():
#         global wifi_configs
#         wifi_configs = ListWifiConfigs()
#         # Fill wifi configs listbox
#         idx = 0
#         for things in wifi_configs:
#             wifi_config_list.insert(idx, things['ssid'].strip('"'))
#             idx += 1
# 
#     # Label for the wifi networks already configured
#     wifi_config_label = Label(wfs, text="Registered:", font=diag_font, bg=main_bg)
#     wifi_config_label.place(x=150, y=300)
# 
#     wifi_config_scrollbar = Scrollbar(wfs, width=15)
#     wifi_config_scrollbar.place(x=135, y=335, height=112)
# 
#     # List of the wifi network configs
#     wifi_config_list = Listbox(wfs, activestyle='none', selectmode='browse', cursor='none', height='6', width='36')
#     wifi_config_list.place(x=150, y=335)
# 
#     wifi_config_list.config(yscrollcommand = wifi_config_scrollbar.set)
#     wifi_config_scrollbar.config(command = wifi_config_list.yview)
# 
#     fwcl = threading.Thread(fill_wifi_configs_list())
#     fwcl.start()
# 
#     # **** AVAILABLE NETWORKS ****
# 
#     global wifi_networks
#     wifi_networks = []
# 
#     def fill_wifi_networks_list():
#         global wifi_networks
#         wifi_networks = ListSSIDS()
#         # Fill available wifi networks listbox
#         idx = 0
#         for thing in wifi_networks:
#             wifi_network_list.insert(idx, thing)
#             idx += 1
# 
#     # Label for the wifi networks available
#     wifi_network_label = Label(wfs, text="Available:", font=diag_font, bg=main_bg)
#     wifi_network_label.place(x=475, y=300)
# 
#     wifi_network_scrollbar = Scrollbar(wfs, width=15)
#     wifi_network_scrollbar.place(x=460, y=335, height=112)
# 
#     # List of the available wifi networks
#     wifi_network_list = Listbox(wfs, activestyle='none', selectmode='browse', cursor='none', height='6', width='36')
#     wifi_network_list.place(x=475, y=335)
# 
#     wifi_network_list.config(yscrollcommand = wifi_network_scrollbar.set)
#     wifi_network_scrollbar.config(command = wifi_network_list.yview)
# 
#     fwnl = threading.Thread(fill_wifi_networks_list())
#     fwnl.start()
# 
#     # idx = 1
#     # for things in wifi_networks:
#     #     wifi_config_list.insert(idx, "SSID: " + things['ssid'] + " - PASSWORD: " + things['psk'])
#     #     idx += 1
# 
#     # * SSID ENTRY *
#     ssid_label = Label(wfs, text="SSID:", font=diag_font, bg=main_bg)
#     ssid_label.place(x=150, y=110)
#     ssid_entry = KeyboardEntry(wfs, keycolor='white', keysize=3, font=diag_font, cusor=None)
#     ssid_entry.place(x=225, y=110)
# 
#     # * PASSWORD ENTRY *
# 
#     pass_label = Label(wfs, text="PWD:", font=diag_font, bg=main_bg)
#     pass_label.place(x=150, y=160)
#     pass_entry = KeyboardEntry(wfs, keycolor='white', keysize=3, font=diag_font, cusor=None)
#     pass_entry.place(x=225, y=160)
# 
#     # Fill in the entry boxes with the wifi config selected
#     def configFill(event):
#         if wifi_config_list.curselection():
#             ssid_entry.replace(wifi_configs[wifi_config_list.curselection()[0]]['ssid'].replace('"', ''))
#             pass_entry.replace(wifi_configs[wifi_config_list.curselection()[0]]['psk'].replace('"', ''))
# 
#     wifi_config_list.bind('<<ListboxSelect>>', configFill)
# 
#     # Fill in the ssid entry box with the ssid selected
#     def wifiFill(event):
#         if wifi_network_list.curselection():
#             ssid_entry.replace(wifi_networks[wifi_network_list.curselection()[0]])
#             pass_entry.replace("")
# 
#     wifi_network_list.bind('<<ListboxSelect>>', wifiFill)
# 
#     # Destroy keyboard
#     # def destroy_keyboard():
#     #     boards = []
#     #     jdx = 0
#     #     while jdx < len(wfs.winfo_children()):
#     #         if str(wfs.winfo_children()[jdx]).find("frame") > 0:
#     #             boards.append(jdx)
#     #         jdx += 1
#     #     boards.reverse()
#     #     for board in boards:
#     #         wfs.winfo_children()[board].destroy()
# 
#     # For destroying the keyboard entity after clicking off of it
#     # def onClick(event):
#     #     destroy_keyboard()
#     #     print(wifi_networks)
# 
#     # Destroy keyboard if clicked off
#     # wfs_canvas.bind('<Button-1>', onClick)
# 
#     # Sends ssid_entry
#     def submit():
#         ssid = ssid_entry.get_text()
#         password = pass_entry.get_text()
#         CreateWifiConfig(ssid, password)
#         # destroy_keyboard()
# 
#     # Clears the entry boxes
#     def clear():
#         ssid_entry.replace("")
#         pass_entry.replace("")
# 
#     # Change focus when something is pressed
#     def change_focus(event):
#         event.widget.focus_set()
# 
#     submitButton = Button(wfs, text="Submit", font=diag_font, activebackground=button_color, bg=button_color, fg=main_fg,
#                           command=lambda:[submit()], height=1, width=5)
#     submitButton.place(x=135, y=220)
# 
#     homeButton = Button(wfs, text="HOME", font=heading_font, activebackground=button_color, bg=button_color,
#                         fg=main_fg,
#                         command=lambda: [destroy_all_screens()], height=3, width=5)
#     homeButton.place(x=0, y=0)
#     dataButton = Button(wfs, text="BACK", font=heading_font, activebackground=button_color, bg=button_color,
#                         fg=main_fg,
#                         command=lambda: [wfs.destroy()], height=3, width=5)
#     dataButton.place(x=0, y=95)
# 
#     # For deselecting widgets when another widget is pressed
#    # wfs.bind_all('<Button>', change_focus)

# **************************************TKINTER SET UP***************************************

# TK screen set up
screen = Tk()
screen.overrideredirect(1)
screen.geometry('800x480')
screen.configure(bg=main_bg)
screen.title("Sm^rt Cutter")
#screen.config(cursor="none")

first_cut_dist = tkinter.IntVar()
thin_cut_spc = tkinter.IntVar()
maj2_cut_spc = tkinter.IntVar()
maj1_cut_dist = tkinter.IntVar()

# Fonts for screen
small_font = font.Font(family='Helvetica', size=10, weight='normal')
small_bold_font = font.Font(family='Helvetica', size=10, weight='bold')
med_font = font.Font(family='Helvetica', size=13, weight='bold')
diag_font = font.Font(family='Helvetica', size=19, weight='normal')
heading_font = font.Font(family='Helvetica', size=20, weight='normal')
heading_bold_font = font.Font(family='Helvetica', size=24, weight='bold')
description_font = font.Font(family='Helvetica', size=20, weight='normal')
title_font = font.Font(family='Helvetica', size=20, weight='bold')
other_font = font.Font(family='Helvetica', size=24, weight='normal')
data_size_font = font.Font(family='Helvetica', size=25, weight='normal')
calib_font = font.Font(family='Helvetica', size=28, weight='normal')
phone_font = font.Font(family='Helvetica', size=45, weight='bold')
stop_font = font.Font(family='Helvetica', size=50, weight='bold')
main_size_font = font.Font(family='Helvetica', size=52, weight='bold')

# Size buttons
fourteenButton = Button(screen, text="14″", font=main_size_font, activebackground="lime green",
                        activeforeground="white", bg="lime green", fg="white", disabledforeground="white",
                        command=lambda: start_cut(14), height=2, width=3)
fourteenButton.place(x=640, y=15)

twelveButton = Button(screen, text="12″", font=main_size_font, activebackground="lime green", activeforeground="white"
                      , bg="lime green", fg="white", disabledforeground="white",
                      command=lambda: start_cut(12), height=2, width=3)
twelveButton.place(x=430, y=15)

tenButton = Button(screen, text="10″", font=main_size_font, activebackground="lime green", activeforeground="white",
                   bg="lime green", fg="white", disabledforeground="white", command=lambda: start_cut(10),
                   height=2, width=3)
tenButton.place(x=222, y=15)

sevenButton = Button(screen, text="7″", font=main_size_font, activebackground="lime green", activeforeground="white",
                     bg="lime green", fg="white", disabledforeground="white", command=lambda: start_cut(7),
                     height=2, width=3)
sevenButton.place(x=15, y=15)

#EXIT/DESTROY TKINTER
Button(screen,text='X',bg='red',fg='white',command=screen.destroy).place(x=0,y=0)

# Donatos Image
img = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((170, 37), PIL.Image.ANTIALIAS))
logo = Label(screen, image=img, bg=main_bg)
logo.place(x=20, y=260)

# Function button
stopButton = Button(screen, text="STOP", font=stop_font, activebackground="red2", activeforeground="white", bg="red2",
                    fg="white", command=lambda: stop(True), height=1, width=9)
stopButton.place(x=220, y=235)

moreButton = Button(screen, text="\u2699", font=stop_font, activebackground=button_color, bg=button_color, fg=main_fg,
                    command=calibration_screen, height=1, width=3)
moreButton.place(x=640, y=235)

homeButton = Button(screen, text="HOME", font=other_font, activebackground=button_color, bg=button_color, fg=main_fg,
                     command=lambda: home(), height=1, width=10)
homeButton.place(x=290, y=360)

Button(screen,text='AIR',font=other_font, activebackground=button_color, bg=button_color, fg=main_fg,
                     command=lambda: air(), height=1, width=10).place(x=290,y=410)
halfButton = Button(screen, text="Half & Half",font=other_font,activebackground="lime green",bg="lime green",
                    activeforeground="white",fg="white",disabledforeground='white',command=lambda: start_cut(14.5), height=2, width=10)
halfButton.place(x=15, y=380)

pieButton = Button(screen, text="Pie Cut",font=other_font,activebackground="lime green",bg="lime green",
                    activeforeground="white",fg="white",disabledforeground='white',command=lambda: start_cut(0), height=2, width=10)
pieButton.place(x=565, y=380)

debugLabel=Label(screen,bg=main_bg)
debugLabel.place(x=340,y=320)

tagOut.lockout=1-tagOut.lockout #force door check on startup after button objects are created
mainloop()
