import sys
import time
import threading
import RPi.GPIO as GPIO
import stepper
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.IN,pull_up_down=GPIO.PUD_UP) #limit switch
GPIO.setup(4, GPIO.OUT) #power to linear actuator
GPIO.setup(21, GPIO.OUT) #Direction to linear actuator
GPIO.output(4, GPIO.HIGH)#relay initiation
GPIO.output(21, GPIO.HIGH) #relay initiation
m1=stepper.motor(26,13) #turntable
m2=stepper.motor(19,20) #gantry

m1_ratio=3200 #steps per rev
m2_ratio=-1600/3.75 #steps per inch

shutdown=True


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
    if GPIO.input(17):
        m2.ramp(-6*m2_ratio)
    while GPIO.input(17):
        if shutdown:
            stop()
            return
        time.sleep(.05)
    m2.stop()

def cut():
    GPIO.output(4, GPIO.LOW)
    GPIO.output(21, GPIO.LOW)
    time.sleep(.175)#.18
    GPIO.output(21, GPIO.HIGH)
    time.sleep(.25)
    GPIO.output(4, GPIO.HIGH)

def clean():
    GPIO.output(4, GPIO.LOW)
    GPIO.output(21, GPIO.LOW)
    time.sleep(.5)
    GPIO.output(21, GPIO.HIGH)
    time.sleep(.5)
    GPIO.output(4, GPIO.HIGH)

#7.2" to center
info={7:[5.5,1.75,1.75,-1.75],
      10:[4.2,1.6,1.6,1.7,-1.08,-2.50],
      12:[3.2,2,2,2,2,-2.5,-3.0],
      14:[2.2,2,2,2,2,2,-3.25,-3.5]
      }

def partycut(cut_array,speed=12800,ramp=.2):
    cut_program=threading.Thread(target=partycut_thread,args=(cut_array,speed,ramp,))
    cut_program.start()

def partycut_thread(cut_array,speed,ramp):
    global shutdown
    shutdown=False
    home()
    for i in [j for j in cut_array if j>0]:
        if shutdown: return
        m2.accel(i*m2_ratio,speed,ramp)
        if shutdown: return
        cut()
    rotate = threading.Thread(target=m1.accel, args=(-m1_ratio/3.5,speed/2,ramp*2,))
    rotate.start()
    for i in [j for j in cut_array if j<0]:
        if shutdown: return
        m2.accel(i*m2_ratio,speed,ramp)
        rotate.join()
        if shutdown: return
        cut()
    if shutdown: return
    rotate = threading.Thread(target=m1.accel, args=(m1_ratio/3.5,speed/2,ramp*2,))
    rotate.start()
    if shutdown: return
    home()
    rotate.join()
    clean()
    shutdown=True

def piecut(speed=12800,ramp=.1):
    cut_program=threading.Thread(target=piecut_thread,args=(speed,ramp,))
    cut_program.start()

def piecut_thread(speed,ramp):
    global shutdown
    shutdown=False
    home
    move1 = threading.Thread(target=m2.accel, args=(7.2*m2_ratio,speed,ramp,))
    move1.start()
    if shutdown: return
    m1.accel(m1_ratio/4,speed/3,ramp*3)
    if shutdown: return
    move1.join()
    cut()
    for i in [1,2,3]:
        if shutdown: return
        m1.accel(-m1_ratio/8,speed/3,ramp*3)
        if shutdown: return
        cut()
    if shutdown: return
    move2 = threading.Thread(target=home)
    move2.start()
    m1.accel(m1_ratio/8,speed/3,ramp*3)
    if shutdown: return
    move2.join()
    clean()
    shutdown=True


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")

        self.setFixedSize(800, 480)

        flags = Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)

        self.setCursor(Qt.BlankCursor)

        # Layout
        layout = QHBoxLayout()

        # Kill Button

        sider_layout = QVBoxLayout()

        home_screen = QPushButton("HOME")
        home_screen.setObjectName("sideButton")
        home_screen.clicked.connect(self.home_screen_clicked)
        sider_layout.addWidget(home_screen)

        wifi_screen = QPushButton("WIFI")
        wifi_screen.setObjectName("sideButton")
        sider_layout.addWidget(wifi_screen)

        help_screen = QPushButton("HELP")
        help_screen.setObjectName("sideButton")
        sider_layout.addWidget(help_screen)

        sider_layout.addStretch()

        layout.addLayout(sider_layout)

        config_layout = QVBoxLayout()

        tabs = QTabWidget()

        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        tabs.addTab(self.tab1, "DIAL")
        tabs.addTab(self.tab2, "SLIDER")
        tabs.addTab(self.tab3, "MISC")

        self.dial_tab()
        self.slider_tab()
        self.misc_tab()

        config_layout.addWidget(tabs)

        layout.addLayout(config_layout, stretch=1)

        self.setLayout(layout)

    def dial_tab(self):
        dial_layout = QHBoxLayout()

        dial = QDial()
        dial.setNotchesVisible(True)
        dial.setValue(50)
        dial.setMinimum(0)
        dial.setMaximum(100)

        dial_layout.addWidget(dial)

        self.tab1.setLayout(dial_layout)

    def slider_tab(self):
        slider_layout = QHBoxLayout()

        slider1 = QSlider()
        slider_layout.addWidget(slider1)

        slider2 = QSlider()
        slider_layout.addWidget(slider2)

        slider3 = QSlider()
        slider_layout.addWidget(slider3)

        self.tab2.setLayout(slider_layout)

    def misc_tab(self):
        misc_layout = QVBoxLayout()

        date_time = QDateTimeEdit()
        misc_layout.addWidget(date_time)

        line_edit = QLineEdit()
        misc_layout.addWidget(line_edit)

        spin_box = QSpinBox()
        misc_layout.addWidget(spin_box)

        prog_bar = QProgressBar()
        misc_layout.addWidget(prog_bar)

        self.tab3.setLayout(misc_layout)

    def home_screen_clicked(self):
        self.hide()


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = SettingsWindow()

        self.setWindowTitle("Sm^rt Cutter")

        self.setFixedSize(800, 480)

        flags = Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)

        self.setCursor(Qt.BlankCursor)

        # Layout
        layout = QVBoxLayout()

        # Kill Button

        header_layout = QHBoxLayout()

        kill_screen = QPushButton(" X ")
        kill_screen.setObjectName("stopButton")
        kill_screen.clicked.connect(self.kill_screen_clicked)

        header_layout.addWidget(kill_screen)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Title

        title_label = QLabel("S M ^ R T CUTTER")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(title_label)

        # Size Buttons

        size_layout = QHBoxLayout()

        size_14_button = QPushButton("14\"")
        size_14_button.setObjectName("sizeButton")
        size_14_button.setFixedSize(150, 200)
        size_14_button.clicked.connect(lambda: partycut(info[14]))
        size_layout.addWidget(size_14_button)

        size_12_button = QPushButton("12\"")
        size_12_button.setObjectName("sizeButton")
        size_12_button.setFixedSize(150, 200)
        size_12_button.clicked.connect(lambda: partycut(info[12]))
        size_layout.addWidget(size_12_button)

        size_10_button = QPushButton("10\"")
        size_10_button.setObjectName("sizeButton")
        size_10_button.setFixedSize(150,200)
        size_10_button.clicked.connect(lambda: partycut(info[10]))
        size_layout.addWidget(size_10_button)

        size_7_button = QPushButton("7\"")
        size_7_button.setObjectName("sizeButton")
        size_7_button.setFixedSize(150, 200)
        size_7_button.clicked.connect(lambda: partycut(info[7]))
        size_layout.addWidget(size_7_button)

        layout.addLayout(size_layout)

        # Misc Buttons

        misc_layout = QHBoxLayout()

        pie_cut_button = QPushButton("Pie Cut")
        pie_cut_button.setObjectName("defaultButton")
        pie_cut_button.clicked.connect(piecut)
        pie_cut_button.setFixedSize(250,90)
        misc_layout.addWidget(pie_cut_button)

        stop_button = QPushButton("STOP")
        stop_button.setObjectName("stopButton")
        stop_button.clicked.connect(stop)
        stop_button.setFixedSize(250,90)
        misc_layout.addWidget(stop_button)

        settings_button = QPushButton("\u2699_\u2699")
        settings_button.setObjectName("defaultButton")
        settings_button.clicked.connect(lambda checked: self.toggle_window(self.settings))
        settings_button.setFixedSize(250,90)
        misc_layout.addWidget(settings_button)

        layout.addLayout(misc_layout)

        # Footer

        footer_label = QLabel("SM^RT Cutter | version b.5.0 \t\t\t\t\t\t Ag\u00e1pe Automation 2022")
        footer_label.setObjectName("footer")
        footer_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        layout.addWidget(footer_label)

        widgets = QWidget()
        widgets.setLayout(layout)

        self.setCentralWidget(widgets)
        self.show()

    def kill_screen_clicked(self):
        self.close()

    def toggle_window(self, window):
        if window.isVisible():
            window.hide()
        else:
            window.show()


app = QApplication(sys.argv)

app.setStyleSheet("""
    QLabel#title {
        font-size: 40px;
        font-family: Helvetica;
    }
    QLabel#footer {
        text-align: center;
    }
    QPushButton#sizeButton {
        background-color: #32CD32;
        font-size: 50px;
        font-family: Helvetica;
        font-weight: bold;
        border-radius: 15px;
        border-color: #2db32d;
        border-width: 2px;
        border-style: outset;
    }
    QPushButton#sizeButton::pressed {
        background-color: lime;
    }
    QPushButton#defaultButton {
        background-color: #E8E8E8;
        font-size: 50px;
        font-family: Helvetica;
        font-weight: bold;
        border-radius: 15px;
        border-color: #d1d1d1;
        border-width: 2px;
        border-style: outset;
    }
    QPushButton#defaultButton::pressed {
        background-color: #F0F0F0;
    }
    QPushButton#stopButton {
        background-color: red;
        font-size: 50px;
        font-family: Helvetica;
        font-weight: bold;
        border-radius: 15px;
        border-color: #cc0202;
        border-width: 2px;
        border-style: outset;
    }
    QPushButton#stopButton::pressed {
        background-color: #EE4B2B;
    }
    QPushButton#sideButton {
        background-color: #E8E8E8;
        font-size: 50px;
        font-family: Helvetica;
        border-color: #d1d1d1;
        border-width: 2px;
        border-style: outset;
    }
    QTabWidget {
        font-size: 20px;
        font-family: Helvetica;
    }
    QSlider::groove:horizontal {
        border: 1px solid #bbb;
        background: white;
        width: 10px;
        border-radius: 4px;
    }
    
    QSlider::sub-page:vertical {
        background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #fff, stop: 0.4999 #eee, stop: 0.5 #ddd, stop: 1 #eee );
        border: 1px solid #777;
        width: 10px;
        border-radius: 4px;
    }
    
    QSlider::add-page:vertical {
        background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #78d, stop: 0.4999 #46a, stop: 0.5 #45a, stop: 1 #238 );
        border: 1px solid #777;
        width: 10px;
        border-radius: 4px;
    }
    
    QSlider::handle:vertical {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc);
        border: 1px solid #777;
        height: 13px;
        margin-top: -2px;
        margin-bottom: -2px;
        border-radius: 4px;
    }
    
    QSlider::handle:vertical:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fff, stop:1 #ddd);
        border: 1px solid #444;
        border-radius: 4px;
    }
    
    QSlider::sub-page:vertical:disabled {
        background: #bbb;
        border-color: #999;
    }
    
    QSlider::add-page:vertical:disabled {
        background: #eee;
        border-color: #999;
    }
    
    QSlider::handle:vertical:disabled {
        background: #eee;
        border: 1px solid #aaa;
        border-radius: 4px;
    }
""")

window = MainWindow()
window.show()

app.exec()
