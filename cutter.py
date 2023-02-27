_version='b.6.0'
import RPi.GPIO as GPIO
import time
import threading
import stepper
from tkinter import *
import tkinter.ttk as ttk
import tkinter.font as font

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.IN,pull_up_down=GPIO.PUD_UP) #limit switch
GPIO.setup(4, GPIO.OUT) #power to linear actuator
GPIO.setup(21, GPIO.OUT) #Direction to linear actuator
GPIO.output(4, GPIO.HIGH)#relay initiation
GPIO.output(21, GPIO.HIGH) #relay initiation
m1=stepper.motor(26,13) #turntable
m2=stepper.motor(19,20) #gantry

m1_ratio=1600 #steps per rev
m2_ratio=-800/3.75 #steps per inch 

shutdown=True

#default info file
#7.2" to center
info={7:[5.5,1.75,1.75,-1.75],
      10:[4.2,1.6,1.6,1.7,-1.08,-2.50],
      12:[3.2,2,2,2,2,-2.5,-3.0],
      14:[2.5,2,2,2,2,2,-3.0,-3.5],
      'cutdepth':18,
      'cut1':[None,7.2,5.5,4.2,3.2,2.5],
      'cutwidth':[None,None,1.75,1.65,2,2],
      'rotpercent':[None,13,25,25,25,25],
      'cutn1':[None,None,1.7,1.7,2.5,3],
      'cutn2':[None,None,None,2.5,3,3.5]
      }

def killscreen():
    window.destroy()
def stop():
    global shutdown
    shutdown=True
    m1.stop()
    m2.stop()
def home():
    global shutdown
    shutdown=False
    GPIO.output(4, GPIO.LOW)
    GPIO.output(21, GPIO.HIGH)
    if GPIO.input(17):
        m2.ramp(-10*m2_ratio,.1)
    while GPIO.input(17):
        if shutdown:
            stop()
            return
        time.sleep(.05)
    m2.stop()
    GPIO.output(4, GPIO.HIGH)
    
def cut(t_cut=0):
    if t_cut<=0 or t_cut>=.5:
        t_cut=info['cutdepth']/100
    GPIO.output(21, GPIO.LOW)
    GPIO.output(4, GPIO.LOW) #go
    time.sleep(t_cut) #down duration/distance
    GPIO.output(21, GPIO.HIGH)
    time.sleep(t_cut+.02) #up duration/distance (hit limit switch)
    GPIO.output(4, GPIO.HIGH) #stop
    
def clean():
#     GPIO.output(21, GPIO.HIGH)
#     GPIO.output(4, GPIO.HIGH)
    pass

def partycut(size):
    cut_program=threading.Thread(target=partycut_thread,args=(size,))
    cut_program.start()
def partycut_thread(size,speed=12800,ramp=.1):
    timer=time.time()
    global shutdown
    shutdown=False
    home()
    
    #create cut array
    num_cuts={7:2,10:4,12:4,14:5}
    num_cuts=num_cuts[size]
    sz_index={7:2,10:3,12:4,14:5}
    size=sz_index[size]
    cut_array=[info['cut1'][size]]
    for j in range(num_cuts):
        cut_array.append(info['cutwidth'][size])
    cut_array.append(-info['cutn1'][size])
    if size>2: cut_array.append(-info['cutn2'][size])
    print(cut_array)
    
    #run machine
    for i in [j for j in cut_array if j>0]:
        if shutdown: return
        m2.accel(i*m2_ratio,speed,ramp)
        if shutdown: return
        cut_thread=threading.Thread(target=cut)
        cut_thread.start()
        time.sleep(info['cutdepth']/100*1.2)
    rotate = threading.Thread(target=m1.accel, args=(-m1_ratio*info['rotpercent'][size]/100,speed/2,ramp*5,))
    rotate.start()
    for i in [j for j in cut_array if j<0]:
        if shutdown: return
        m2.accel(i*m2_ratio,speed,ramp)
        rotate.join()
        if shutdown: return
        cut_thread=threading.Thread(target=cut)
        cut_thread.start()
        time.sleep(info['cutdepth']/100*1.2)
    time.sleep(info['cutdepth']/100*.8)
    if shutdown: return
    rotate = threading.Thread(target=m1.accel, args=(m1_ratio*info['rotpercent'][size]/100,speed/4,ramp*5,))
    rotate.start()
    if shutdown: return
    cut_thread.join()
    home()
    rotate.join()
    #clean()
    shutdown=True
    timer=round(time.time()-timer,2)
    time_label.config(text=str(timer)+' seconds')

def piecut(speed=12800,ramp=.1):
    cut_program=threading.Thread(target=piecut_thread,args=(speed,ramp,))
    cut_program.start()
def piecut_thread(speed,ramp):
    timer=time.time()
    global shutdown
    shutdown=False
    home
    move1 = threading.Thread(target=m2.accel, args=(info['cut1'][1]*m2_ratio,speed,ramp,))
    move1.start()
    if shutdown: return
    m1.accel(m1_ratio*info['rotpercent'][1]/50,speed/3,ramp*3)
    if shutdown: return
    move1.join()
    cut_thread=threading.Thread(target=cut)
    cut_thread.start()
    time.sleep(info['cutdepth']/50-.05)
    for i in [1,2,3]:
        if shutdown: return
        m1.accel(-m1_ratio*info['rotpercent'][1]/100,speed/3,ramp*3)
        if shutdown: return
        cut_thread=threading.Thread(target=cut)
        cut_thread.start()
        time.sleep(info['cutdepth']/50-.05)
    cut_thread.join()
    if shutdown: return
    move1 = threading.Thread(target=m2.accel, args=(-info['cut1'][1]*m2_ratio,speed,ramp,))
    move1.start()
    m1.accel(m1_ratio*info['rotpercent'][1]/100,speed/3,ramp*3)
    move1.join()
    move2 = threading.Thread(target=home)
    move2.start()
    if shutdown: return
    move2.join()
    #clean()
    shutdown=True
    timer=round(time.time()-timer,2)
    time_label.config(text=str(timer)+' seconds')
#************************************Screen Design***************************************
#screen setup
def settingsscreen():
    setwin=Toplevel(window)
    setwin.overrideredirect(1)
    setwin.geometry('800x480')
    backbutton=Button(setwin, text="\u2b05", font=font, bg="red2", fg="white", command=setwin.destroy)
    backbutton.place(x=0,y=0)
    ttk.Style().configure('TNotebook.Tab',font=font)
    size_tab=ttk.Notebook(setwin)
    size_tab.pack()
    tab_name=['General',' Pie ',' 7" ',' 10" ',' 12" ',' 14" ']
    frame=[]
    cut1=[]
    rotpercent=[]
    cutwidth=[]
    cutn1=[]
    cutn2=[]
    frame=[Frame(size_tab,width=700,height=400),Frame(size_tab),Frame(size_tab),Frame(size_tab),Frame(size_tab),Frame(size_tab)]
    for i in range(len(tab_name)):
        frame[i].pack()
        size_tab.add(frame[i],text=tab_name[i])
        cut1.append(None)
        cutwidth.append(None)
        rotpercent.append(None)
        cutn1.append(None)
        cutn2.append(None)

    #General Tab
    cutdepth=IntVar()
    cutdepth.set(info['cutdepth'])
    Label(frame[0],text='Cut Depth',font=font,padx=40).grid(row=0,column=0)
    Scale(frame[0],variable=cutdepth,orient=HORIZONTAL,length=260,width=35,from_=10,to=30,tickinterval=10).grid(row=0,column=1)
    
    #Pie Tab
    cut1[1]=DoubleVar()
    cut1[1].set(info['cut1'][1])
    Label(frame[1],text='Center Dist.',font=font).grid(row=0,column=0)
    Scale(frame[1],variable=cut1[1],orient=HORIZONTAL,length=260,width=35,from_=6,to=8,tickinterval=1,resolution=.1).grid(row=0,column=1)
    rotpercent[1]=DoubleVar()
    rotpercent[1].set(info['rotpercent'][1])
    Label(frame[1],text='Rotation%',font=font).grid(row=1,column=0)
    Scale(frame[1],variable=rotpercent[1],orient=HORIZONTAL,length=260,width=35,from_=10,to=15,tickinterval=1,resolution=.5).grid(row=1,column=1)

    #Party Tabs
    for i in [2,3,4,5]:
        cut1[i]=DoubleVar()
        cut1[i].set(info['cut1'][i])
        Label(frame[i],text='1st Cut\nDist.',font=font).grid(row=0,column=0)
        Scale(frame[i],variable=cut1[i],orient=HORIZONTAL,length=260,width=35,from_=2,to=6,tickinterval=2,resolution=.25).grid(row=0,column=1)
        cutwidth[i]=DoubleVar()
        cutwidth[i].set(info['cutwidth'][i])
        Label(frame[i],text='Slice\nWidth',font=font).grid(row=1,column=0)
        Scale(frame[i],variable=cutwidth[i],orient=HORIZONTAL,length=260,width=35,from_=1,to=3,tickinterval=1,resolution=.25).grid(row=1,column=1)
        rotpercent[i]=IntVar()
        rotpercent[i].set(info['rotpercent'][i])
        Label(frame[i],text='Rotation%',font=font).grid(row=2,column=0)
        Scale(frame[i],variable=rotpercent[i],orient=HORIZONTAL,length=260,width=35,from_=20,to=30,tickinterval=5).grid(row=2,column=1)
        cutn1[i]=DoubleVar()
        cutn1[i].set(info['cutn1'][i])
        Label(frame[i],text='1st Lat.\nCut Dist.',font=font).grid(row=3,column=0)
        Scale(frame[i],variable=cutn1[i],orient=HORIZONTAL,length=260,width=35,from_=1,to=4,tickinterval=1,resolution=.25).grid(row=3,column=1)
        if i!=2:        
            cutn2[i]=DoubleVar()
            cutn2[i].set(info['cutn2'][i])
            Label(frame[i],text='2nd Lat.\nCut Dist.',font=font).grid(row=4,column=0)
            Scale(frame[i],variable=cutn2[i],orient=HORIZONTAL,length=260,width=35,from_=1,to=4,tickinterval=1,resolution=.25).grid(row=4,column=1)
    
    backbutton.config(command=lambda:[write_info_dict(),setwin.destroy(),print(info)])
    
    def write_info_dict():
        info['cutdepth']=cutdepth.get()
        for i in [1,2,3,4,5]:
            info['cut1'][i]=cut1[i].get()
            info['rotpercent'][i]=rotpercent[i].get()
        for i in [2,3,4,5]:
            info['cutwidth'][i]=cutwidth[i].get()
            info['cutn1'][i]=cutn1[i].get()
            if i!=2: info['cutn2'][i]=cutn2[i].get()
            
window=Tk()
bold=font.Font(family='Helvetica', size=50, weight='bold')
font=font.Font(family='Helvetica', size=24, weight='normal')
window.overrideredirect(1)
window.geometry('800x480')
window.config(cursor=NONE)
window.title("Sm^rt Cutter")
Label(window, text="S M ^ R T   C U T T E R").pack(pady=5,side=TOP)
Label(window, text="SM^RT Cutter | version "+_version+"\t\t\t\t\t\t Ag\u00e1pe Automation 2023").pack(side=BOTTOM)
Button(window, text="X",font=font,relief=FLAT,activebackground=window['bg'],command=killscreen).place(x=0,y=0)
Button(window,text="\u2699",font=font,relief=FLAT,activebackground=window['bg'],command=settingsscreen).place(x=750,y=0)
time_label=Label(window)
time_label.place(x=350,y=458)

frame1=Frame(window,borderwidth=8,relief=SUNKEN)
frame1.pack(pady=10,side=TOP)
text14=Button(frame1, text='\u25cd\n14"',font=bold,bg="green",fg="white",command=lambda:partycut(14),height=3,width=3,activebackground='green',activeforeground='white')
text14.pack(side=RIGHT)
text12=Button(frame1, text='\u25cd\n12"',font=bold,bg="green",fg="white",command=lambda:partycut(12),height=3,width=3,activebackground='green',activeforeground='white')
text12.pack(side=RIGHT)
text10=Button(frame1, text='\u25cd\n10"',font=bold,bg="green",fg="white",command=lambda:partycut(10),height=3,width=3,activebackground='green',activeforeground='white')
text10.pack(side=RIGHT)
text07=Button(frame1, text='\u25cd\n7"',font=bold,bg="green",fg="white",command=lambda:partycut(7),height=3,width=3,activebackground='green',activeforeground='white')
text07.pack(side=RIGHT)
textpiecut=Button(frame1, text="\u2733\nPIE", font=bold, bg="green", fg="white", command=piecut,height=3,width=3,activebackground='green',activeforeground='white')
textpiecut.pack(side=LEFT)

frame2=Frame(window,borderwidth=8,relief=SUNKEN)
frame2.pack(side=TOP)
Button(frame2,text="STOP",font=bold,bg='red',fg='white',command=stop,height=2,width=18).pack(side=BOTTOM)



    
    
window.mainloop()

