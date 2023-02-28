from tkinter import *
from customtkinter import *
import tkinter.font as font
import sys
import tkinter as tk
from PIL import Image
from PIL import ImageDraw
import PIL.Image
import PIL.ImageTk

set_appearance_mode("Light")

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
screen.overrideredirect(1)
screen.geometry('800x480')
screen.configure(bg=main_bg)
screen.title("Sm^rt Cutter")
screen.config(cursor="none")

title_font = ('Helvetica', 12)
other_font = ('Helvetica', 20)
stop_font = ('Helvetica', 50)
main_size_font = ('Helvetica', 52)

main_color = "#ECECED"
other_color = "#CCCDD0"

# ROW 0

titleLabel = CTkLabel(screen, text = "SM^RT CUTTER", text_font=title_font)

titleLabel.grid(row = 0, column = 0, sticky = "news", columnspan = 4,pady=(0,3))

# ROW 1

pieCutButton = CTkButton(screen, command=pie_cut, text="PIE CUT", text_font=other_font, text_color="black", corner_radius=10, fg_color=other_color, hover_color=main_color)
handTossButton = CTkButton(screen, command=hand_toss, text="HAND\nTOSSED", text_font=other_font, text_color="black", corner_radius=10, fg_color=other_color, hover_color=main_color)
glutenFreeButton = CTkButton(screen, command=gluten_free, text="GLUTEN\nFREE", text_font=other_font, text_color="black", corner_radius=10, fg_color=other_color, hover_color=main_color)
thickerButton = CTkButton(screen, command=thicker, text="THICKER", text_font=other_font, text_color="black", corner_radius=10, fg_color=other_color, hover_color=main_color)

pieCutButton.grid(row=1,column=0,sticky="news",padx=(0,3),pady=3)
handTossButton.grid(row=1,column=1,sticky="news",padx=3,pady=3)
glutenFreeButton.grid(row=1,column=2,sticky="news",padx=3,pady=3)
thickerButton.grid(row=1,column=3,sticky="news",padx=(3,0),pady=3)

# ROW 2

sevenButton = CTkButton(screen, command= lambda:size_cut("7"), text="7\"", text_font=main_size_font, text_color="white",fg_color="lime green", hover_color="#65DA65",corner_radius=10, height=220, width=150)
tenButton = CTkButton(screen, command= lambda:size_cut("10"), text="10\"", text_font=main_size_font, text_color="white",fg_color="lime green", hover_color="#65DA65",corner_radius=10,height=220, width=150)
twelveButton = CTkButton(screen, command= lambda:size_cut("12"), text="12\"", text_font=main_size_font, text_color="white",fg_color="lime green", hover_color="#65DA65",corner_radius=10,height=220, width=150)
fourteenButton = CTkButton(screen, command= lambda:size_cut("14"), text="14\"", text_font=main_size_font, text_color="white",fg_color="lime green", hover_color="#65DA65",corner_radius=10,height=220, width=150)

sevenButton.grid(row=2,column=0,sticky="news",padx=(0,3),pady=3)
tenButton.grid(row=2,column=1,sticky="news",padx=3,pady=3)
twelveButton.grid(row=2,column=2,sticky="news",padx=3,pady=3)
fourteenButton.grid(row=2,column=3,sticky="news",padx=(3,0),pady=3)

# ROW 3

img = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((150, 31), PIL.Image.ANTIALIAS))

logoLabel = CTkButton(screen, text="",image=img, hover=False, fg_color=main_color,corner_radius=10, border_width=0, width=150)
stopButton = CTkButton(screen,command=stop,text="STOP", text_font=stop_font,text_color="white",fg_color="red", hover_color="#FF4040",corner_radius=10, height=140)
calibButton = CTkButton(screen,command=settings_screen,text="\u2699",text_font=stop_font, fg_color=other_color, hover_color=main_color,corner_radius=10, width=150)

logoLabel.grid(row=3,column=0,sticky="news",padx=(0,3),pady=(3,0))
stopButton.grid(row=3,column=1,sticky="news",columnspan=2, padx=3,pady=(3,0))
calibButton.grid(row=3,column=3,sticky="news",padx=(3,0),pady=(3,0))

screen.columnconfigure(0,weight=1)
screen.columnconfigure(1,weight=1)
screen.columnconfigure(2,weight=1)
screen.columnconfigure(3,weight=1)
mainloop()