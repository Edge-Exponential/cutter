#**********************************Declarations*********************************************
import RPi.GPIO as GPIO
import time
import _thread
from tkinter import *
import tkinter.font as font
import sys
import tkinter as tk

#OPEN 12,19,26
#weird 9,10,11,14,15
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(24,  GPIO.OUT) #relay
GPIO.setup(25, GPIO.OUT) #relay
GPIO.output(24, GPIO.HIGH)
GPIO.output(25,GPIO.HIGH)


GPIO.setup(2, GPIO.OUT) #Y_Axis limit Switch Setup
GPIO.output(2, GPIO.HIGH) #Set Y_Axis Limit Switch to High
GPIO.setup(3, GPIO.IN) #Blade Cleaner Limit Switch
GPIO.setup(5, GPIO.OUT) #Emergency Stop Setup
GPIO.output(5, GPIO.HIGH) #Set Emergency Stop to High
GPIO.setup(7, GPIO.IN) #Z_Axis Hall Effect Limit Switch
GPIO.setup(8, GPIO.IN) #Z_Axis Hall Effect Limit Switch
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP) # X_Axis Limit Switch



GPIO.setup(27,  GPIO.OUT) #x-axis1 clk
GPIO.setup(4, GPIO.OUT) #x-axis1 direction
GPIO.setup(6,  GPIO.OUT) #x-axis2 clk
GPIO.setup(16, GPIO.OUT) #x-axis2 direction
GPIO.setup(17, GPIO.OUT) #y-axis clk
GPIO.setup(18, GPIO.OUT) #y-axis direction
GPIO.setup(21, GPIO.OUT) #z-axis clk
GPIO.setup(13, GPIO.OUT) #z-axis direction
GPIO.setup(22, GPIO.OUT) #Blade cleaner clk
GPIO.setup(23, GPIO.OUT) #Blade cleaner direction


global motor_x_time_sleep
motor_x_time_sleep = 0.001
global motor_x_time_sleep_acc
motor_x_time_sleep_acc =0.00
global moter_x_acc_steps
moter_x_acc_steps =15
global motor_y_time_sleep
motor_y_time_sleep = 0.001
global motor_y_time_sleep_end
motor_y_time_sleep_end = 0.003
global moter_y_acc_steps
moter_y_acc_steps =15
global motor_z_time_sleep
motor_z_time_sleep = 0.0015
global motor_bladecleaner_time_sleep
motor_bladecleaner_time_sleep = 0.0004

#screen setup
window=Tk()
stopFont=font.Font(family='Helvetica', size=50, weight='bold')
font=font.Font(family='Helvetica', size=24, weight='normal')
window.overrideredirect(1)
window.geometry('800x480')

#*************************************FUNCTIONS*********************************************


#********Screen Functions**********************
def killscreen():
    window.destroy()

def switchbuttonstate():
    if(GPIO.input(8)==0 and GPIO.input(2)==0 and GPIO.input(7)==0):
        text14['state']=tk.NORMAL
        text14hh['state']=tk.NORMAL
        text12['state']=tk.NORMAL
        text10['state']=tk.NORMAL
        text07['state']=tk.NORMAL
        textpiecut['state']=tk.NORMAL
        changebladebutton['state']=tk.NORMAL
        cleanbutton['state']=tk.NORMAL
    else:
        text14['state']=tk.DISABLED
        text14hh['state']=tk.DISABLED
        text12['state']=tk.DISABLED
        text10['state']=tk.DISABLED
        text07['state']=tk.DISABLED
        textpiecut['state']=tk.DISABLED
        changebladebutton['state']=tk.DISABLED
        cleanbutton['state']=tk.DISABLED
        
#********Move x axis**********************
def movexaxishome():
    i=1
    while GPIO.input(20)==1 and GPIO.input(5)==0:#385 
        GPIO.output(27, GPIO.LOW)
        GPIO.output(4, GPIO.HIGH)
        GPIO.output(6, GPIO.HIGH)
        GPIO.output(16, GPIO.HIGH)
        time.sleep(motor_x_time_sleep)
        GPIO.output(27, GPIO.LOW)
        GPIO.output(4, GPIO.LOW)
        GPIO.output(6, GPIO.HIGH)
        GPIO.output(16, GPIO.LOW)
        time.sleep(motor_x_time_sleep)
        i+=1
        
def movexaxismiddle(steps):
    if steps<0:
        GPIO.output(27, GPIO.HIGH)
        GPIO.output(6, GPIO.LOW)
        steps=-steps
    else:
        GPIO.output(27,GPIO.LOW)
        GPIO.output(6, GPIO.HIGH)
    i=1
    while GPIO.input(8)==1 and GPIO.input(5)==0: #120
        GPIO.output(4, GPIO.HIGH)
        GPIO.output(16, GPIO.HIGH)
        time.sleep(motor_x_time_sleep)
        GPIO.output(4, GPIO.LOW)
        GPIO.output(16, GPIO.LOW)
        time.sleep(motor_x_time_sleep)
        i+=1

def movexaxis(steps):
    if steps<0:
        GPIO.output(27, GPIO.HIGH)
        GPIO.output(6, GPIO.LOW)
        steps=-steps
    else:
        GPIO.output(27,GPIO.LOW)
        GPIO.output(6, GPIO.HIGH)
    i=1
    while i<=steps and GPIO.input(5)==0: #120
        GPIO.output(4, GPIO.HIGH)
        GPIO.output(16, GPIO.HIGH)
        time.sleep(motor_x_time_sleep)
        GPIO.output(4, GPIO.LOW)
        GPIO.output(16, GPIO.LOW)
        time.sleep(motor_x_time_sleep)
        i+=1
    
#********Move y axis**********************
def moveyaxisforward(steps):
    i=0    
    while i<=steps and GPIO.input(5)==0:
        GPIO.output(17, GPIO.LOW)
        GPIO.output(18, GPIO.HIGH)
        time.sleep(motor_y_time_sleep)
        GPIO.output(17, GPIO.LOW)
        GPIO.output(18, GPIO.LOW)
        time.sleep(motor_y_time_sleep)
        i+=1

def moveyaxisbackward(steps):
    i=1
    while i<=steps and GPIO.input(5)==0: #
        GPIO.output(17, GPIO.HIGH)
        GPIO.output(18, GPIO.HIGH)
        time.sleep(motor_y_time_sleep)
        GPIO.output(17, GPIO.HIGH)
        GPIO.output(18, GPIO.LOW)
        time.sleep(motor_y_time_sleep)
        i+=1
        
def moveyaxishome():
    i=1
    while GPIO.input(2)==1 and GPIO.input(5)==0: #
        GPIO.output(17, GPIO.HIGH)
        GPIO.output(18, GPIO.HIGH)
        time.sleep(motor_y_time_sleep)
        GPIO.output(17, GPIO.HIGH)
        GPIO.output(18, GPIO.LOW)
        time.sleep(motor_y_time_sleep)
        i+=1

#*************Move z axis***************
def movezaxis(steps):
    if steps<0:
        GPIO.output(21, GPIO.LOW)
        steps=-steps
    else:
        GPIO.output(21, GPIO.HIGH)
    i=1
    while i<=steps  and GPIO.input(5)==0:
        GPIO.output(13, GPIO.HIGH)
        time.sleep(motor_z_time_sleep)
        GPIO.output(13, GPIO.LOW)
        time.sleep(motor_z_time_sleep)
        i+=1

def movezaxishome():
    if GPIO.input(7)==1 and GPIO.input(5)==0:
        i=1
        while GPIO.input(7)==1 and GPIO.input(5)==0:
            GPIO.output(21, GPIO.LOW)
            GPIO.output(13, GPIO.HIGH)
            time.sleep(motor_z_time_sleep)
            GPIO.output(21, GPIO.LOW)
            GPIO.output(13, GPIO.LOW)
            time.sleep(motor_z_time_sleep)
        while i<3:
            GPIO.output(21, GPIO.LOW)
            GPIO.output(13, GPIO.HIGH)
            time.sleep(motor_z_time_sleep)
            GPIO.output(21, GPIO.LOW)
            GPIO.output(13, GPIO.LOW)
            time.sleep(motor_z_time_sleep)
            i+=1
#*************Other Movements***************
#clean function
def cleanblade():
    i=1
    while i<1360 and GPIO.input(5)==0:
        GPIO.output(23, GPIO.LOW)
        GPIO.output(22, GPIO.HIGH)
        time.sleep(motor_bladecleaner_time_sleep)
        GPIO.output(23, GPIO.LOW)
        GPIO.output(22, GPIO.LOW)
        time.sleep(motor_bladecleaner_time_sleep)
        i+=1
def cleanbladehome():
    i=1
    while i<1360 and GPIO.input(5)==0:
        GPIO.output(23, GPIO.HIGH)
        GPIO.output(22, GPIO.HIGH)
        time.sleep(motor_bladecleaner_time_sleep)
        GPIO.output(23, GPIO.HIGH)
        GPIO.output(22, GPIO.LOW)
        time.sleep(motor_bladecleaner_time_sleep)
        i+=1
#Cut Function
def singlecut():
    if GPIO.input(5)==0:
        time.sleep(.2)
        GPIO.output(25,GPIO.LOW)
        time.sleep(.4)
        GPIO.output(25,GPIO.HIGH)
        time.sleep(0.1)

def ac():
    if GPIO.input(24)==1:
        GPIO.output(24, GPIO.LOW)
    else:
        GPIO.output(24, GPIO.HIGH)
        
def recalibratehome():
    if GPIO.input(8)==1 and GPIO.input(5)==0:
        movezaxishome()
        moveyaxishome()
        moveyaxisforward(450)
        movezaxis(102)
        movexaxishome()
        movexaxismiddle(-1)
        movezaxishome()
        moveyaxishome()
        switchbuttonstate()
    else:
        home()
        switchbuttonstate()
        
def home():
    movezaxishome()
    moveyaxishome()

def changeblade():
    moveyaxisforward(700)
    switchbuttonstate()

def movebladeinital(step1,step2):
    _thread.start_new_thread(moveyaxisforward,(step2,))
    _thread.start_new_thread(movexaxis,(step1,))
    #_thread.start_new_thread(cleanbladehome,())
    time.sleep(.7)
    movezaxis(109)
    
def moveyz(step1,step2):
    _thread.start_new_thread(movexaxismiddle,(step1,))
    _thread.start_new_thread(movezaxishome,())
    _thread.start_new_thread(moveyaxisforward,(step2,))
    _thread.start_new_thread(cleanbladehome,())

def piecuthome():
    _thread.start_new_thread(movezaxishome,())
    _thread.start_new_thread(moveyaxishome,())
    #_thread.start_new_thread(cleanbladehome,())
def piecutlast():
    _thread.start_new_thread(singlecut,())
    _thread.start_new_thread(cleanbladehome,())
#*************Pizza Cut Selection***************
    
def largecut():
    if(GPIO.input(8)==0 and GPIO.input(2)==0 and GPIO.input(7)==0):
        movebladeinital(-110,450)
        singlecut()
        movexaxis(210)
        singlecut()
        moveyz(-30,150)
        time.sleep(.6)
        singlecut()
        moveyaxisbackward(110)
        singlecut()
        moveyaxisbackward(110)
        singlecut()
        moveyaxisbackward(110)
        singlecut()
        moveyaxisbackward(110)
        singlecut()
        moveyaxisbackward(110)
        singlecut()
        moveyaxishome()
        time.sleep(.5)
        cleanblade()
        switchbuttonstate()
    else:
        switchbuttonstate()

def largehhcut():
    movebladeinital(-180,450)
    singlecut()
    movexaxis(180)
    singlecut()
    moveyz(-30,185)
    time.sleep(.6)
    singlecut()
    moveyaxisbackward(80)
    singlecut()
    moveyaxisbackward(80)
    singlecut()
    moveyaxisbackward(80)
    singlecut()
    moveyaxisbackward(80)
    singlecut()
    moveyaxisbackward(80)
    singlecut()
    moveyaxisbackward(80)
    singlecut()
    moveyaxishome()
    cleanblade()
    switchbuttonstate()

def mediumcut():
    movebladeinital(-120,450)
    singlecut()
    movexaxisright()
    singlecut()
    moveyz(-30,185)
    time.sleep(.6)
    singlecut()
    moveyaxis2in()
    singlecut()
    moveyaxis2in()
    singlecut()
    moveyaxis2in()
    singlecut()
    moveyaxis2in()
    singlecut()
    moveyaxishome()
    cleanblade()
    switchbuttonstate()
    
def smallcut():
    movebladeinital(-250,450)
    singlecut()
    movexaxis(180)
    singlecut()
    moveyz(70,0)
    time.sleep(.6)
    singlecut()
    moveyaxisbackward(90)
    singlecut()
    moveyaxisbackward(90)
    singlecut()
    moveyaxisbackward(90)
    singlecut()
    moveyaxisbackward(90)
    singlecut()
    moveyaxishome()
    cleanblade()
    switchbuttonstate()
    
def individualcut():
    moveyaxishalfforward()
    movezaxiscw()
    singlecut()
    moveyz()
    time.sleep(.6)
    singlecut()
    moveyaxis1in()
    singlecut()
    moveyaxis1in()
    singlecut()
    moveyaxishome()
    cleanblade()
    switchbuttonstate()
    
def piecut():
    moveyaxishalfforward()
    singlecut()
    #cleanbladehome()
    movezaxiscw45()
    singlecut()
    movezaxiscw45()
    singlecut()
    movezaxiscw45()
    piecutlast()
    time.sleep(.75)
    piecuthome()
    time.sleep(1)
    cleanblade()
    switchbuttonstate()
#**************************************Screen*************************************************
window.title("EDGE EX CUTTER")
namelabel=Label(window, text="EDGE EXPONENTIAL SM^RT CUTTER", font=font)

namelabel.place(x=100,y=0)
partylabel=Label(window, text="Party Cut:", font=font)
partylabel.place(x=0,y=35)
longtext= """
14\"
Half & Half
"""
text14=Button(window, text="14\"", font=font, bg="black", fg="white", command=largecut,height=4, width=7)
text14.place(x=639, y=70)
text14hh=Button(window, text=longtext, font=font, bg="black", fg="white", command=largehhcut,height=4, width=8)
text14hh.place(x=467, y=70)
text12=Button(window, text="12\"", font=font, bg="black", fg="white", command=mediumcut,height=4,width=7)
text12.place(x=313, y=70)
text10=Button(window, text="10\"", font=font, bg="black", fg="white", command=smallcut,height=4, width=7)
text10.place(x=159, y=70)
text07=Button(window, text="7\"", font=font, bg="black", fg="white", command=individualcut,height=4,width=7)
text07.place(x=5, y=70)

pielabel=Label(window, text="Pie Cut:", font=font)
pielabel.place(x=0,y=227)
textpiecut=Button(window, text="All Sizes", font=font, bg="black", fg="white", command=piecut, height=4,width=7)
textpiecut.place(x=5, y=262)
safetylabel=Label(window, text="Safety System Status:", font=font)
safetylabel.place(x=159, y=227)

homebutton= Button(window, text="Home", font=font, bg="yellow", fg="black", command=recalibratehome,height=1, width=7)
homebutton.place(x=5, y=430)
cleanbutton= Button(window, text="Clean Blade", font=font, bg="yellow", fg="black", command=cleanblade,height=1, width=9)
cleanbutton.place(x=159, y=430)
changebladebutton= Button(window, text="Change Blade", font=font, bg="yellow", fg="black", command=changeblade,height=1, width=10)
changebladebutton.place(x=350, y=430)
acbutton= Button(window, text="A/C", font=font, bg="yellow", fg="black", command=ac, height=1, width=3)
acbutton.place(x=557, y=430)
exitbutton= Button(window, text="EXIT", font=font, bg="red2", fg="white", command=killscreen,height=1, width=7)
exitbutton.place(x=639, y=430)
switchbuttonstate()
window.mainloop()