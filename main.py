from tkinter import *
import tkinter.font as font
import sys
import tkinter as tk
from PIL import Image
from PIL import ImageDraw
import PIL.Image
import PIL.ImageTk

def size_cut(size):
    print(size + "CUT")

def pie_cut():
    print("PIECUT")

def hand_toss():
    print("HANDTOSS")

def gluten_free():
    print("GLUTENFREE")

def thicker():
    print("THICKER")

def stop():
    print("STOP")

def settings_screen():
    print("SETTINGSCREEN")

filepath = '/Users/InkAl/OneDrive/Desktop/cutter/'
donatos_path = filepath + "donatos.png"

main_bg = "#FFFFFF"

# Screen set up
screen = Tk()
# screen.overrideredirect(1)
screen.geometry('800x480')
screen.configure(bg=main_bg)
screen.title("Sm^rt Cutter")
# screen.config(cursor="none")

title_font = font.Font(family='Helvetica', size=12,weight='normal')
other_font = font.Font(family='Helvetica', size=20, weight='normal')
stop_font = font.Font(family='Helvetica', size=50, weight='bold')
main_size_font = font.Font(family='Helvetica', size=52, weight='bold')

# ROW 0

titleLabel = Label(screen, text = "SM^RT CUTTER",font=title_font, borderwidth=1, relief="ridge")

titleLabel.grid(row = 0, column = 0, sticky = "news", columnspan = 4,pady=(0,3))

# ROW 1

pieCutButton = Button(screen, command=pie_cut, text="PIE CUT", font=other_font, borderwidth=3, relief="ridge")
handTossButton = Button(screen, command=hand_toss, text="HAND\nTOSSED", font=other_font, borderwidth=3, relief="ridge")
glutenFreeButton = Button(screen, command=gluten_free, text="GLUTEN\nFREE", font=other_font, borderwidth=3, relief="ridge")
thickerButton = Button(screen, command=thicker, text="THICKER", font=other_font, borderwidth=3, relief="ridge")

pieCutButton.grid(row=1,column=0,sticky="news",padx=(0,3),pady=3)
handTossButton.grid(row=1,column=1,sticky="news",padx=3,pady=3)
glutenFreeButton.grid(row=1,column=2,sticky="news",padx=3,pady=3)
thickerButton.grid(row=1,column=3,sticky="news",padx=(3,0),pady=3)

# ROW 2

sevenButton = Button(screen, command= lambda:size_cut("7"), text="7\"", font=main_size_font, bg="lime green",activebackground="lime green",activeforeground="white",fg="white", disabledforeground="white", height=2, borderwidth=3, relief="ridge")
tenButton = Button(screen, command= lambda:size_cut("10"), text="10\"", font=main_size_font, bg="lime green",activebackground="lime green",activeforeground="white",fg="white", disabledforeground="white", borderwidth=3, relief="ridge")
twelveButton = Button(screen, command= lambda:size_cut("12"), text="12\"", font=main_size_font, bg="lime green",activebackground="lime green",activeforeground="white",fg="white", disabledforeground="white", borderwidth=3, relief="ridge")
fourteenButton = Button(screen, command= lambda:size_cut("14"), text="14\"", font=main_size_font, bg="lime green",activebackground="lime green",activeforeground="white",fg="white", disabledforeground="white", borderwidth=3, relief="ridge")

sevenButton.grid(row=2,column=0,sticky="news",padx=(0,3),pady=3)
tenButton.grid(row=2,column=1,sticky="news",padx=3,pady=3)
twelveButton.grid(row=2,column=2,sticky="news",padx=3,pady=3)
fourteenButton.grid(row=2,column=3,sticky="news",padx=(3,0),pady=3)

# ROW 3

img = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((170, 37), PIL.Image.ANTIALIAS))

logoLabel = Label(screen, image=img, borderwidth=1, relief="ridge")
stopButton = Button(screen,command=stop,text="STOP",font=stop_font,activebackground="red2", activeforeground="white", bg="red2",fg="white", borderwidth=3, relief="ridge")
calibButton = Button(screen,command=settings_screen,text="\u2699",font=stop_font, borderwidth=3, relief="ridge")

logoLabel.grid(row=3,column=0,sticky="news",padx=(0,3),pady=(3,0))
stopButton.grid(row=3,column=1,sticky="news",columnspan=2, padx=3,pady=(3,0))
calibButton.grid(row=3,column=3,sticky="news",padx=(3,0),pady=(3,0))

screen.columnconfigure(0,weight=1)
screen.columnconfigure(1,weight=1)
screen.columnconfigure(2,weight=1)
screen.columnconfigure(3,weight=1)
mainloop()
