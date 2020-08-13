"""
In this example, we demonstrate how to create simple camera viewer using Opencv3 and PyQt5

Author: Berrouba.A
Last edited: 21 Feb 2018
"""
# In[]
import sys
import os
# import some PyQt5 modules
from PyQt5 import QtCore, QtGui, QtWidgets,uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer,Qt
# import Opencv module
import cv2
import pandas as pd
import numpy as np
#from layout.main_layout import *
Ui_MainWindow, _ = uic.loadUiType("designer/main_layout.ui")
from lib.ultil import *
from easymodbus.modbusClient import ModbusClient

# In[]

cap             =   cv2.VideoCapture(0)
frame1=cap.read()
cap2            =   cv2.VideoCapture(1)
frame1=cap.read()

var_ip          =   "10.179.190.211"
var_port        =   502
modbus_client   =   ModbusClient(var_ip,var_port)
modbus_client.connect()

para_recipe = ""
# In[]
class MainWindow2(QtWidgets.QMainWindow):
    # class constructor
    def __init__(self):
        # call QWidget constructor
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # create a timer
        self.timer_camera1 = QTimer()
        self.timer_camera2 = QTimer()
        self.timer_modbus = QTimer()
        self.timer_recipe = QTimer()
        # set timer timeout callback function
        self.timer_camera1.timeout.connect(self.viewCam1)
        self.timer_camera2.timeout.connect(self.viewCam2)
        self.timer_modbus.timeout.connect(self.scanDigitalInput)
        self.timer_recipe.timeout.connect(self.scanRecipe)

        self.timer_camera1.start(1)
        self.timer_camera2.start(1)
        self.timer_modbus.start(1)
        self.timer_recipe.start(1)

        self.ui.actionClose.triggered.connect(lambda: self.closeMainWindow())
        self.ui.pbt_tray.clicked.connect(lambda: self.pbt_tray_clicked())
        self.ui.pbt_lighting.clicked.connect(lambda: self.pbt_lighting_clicked())
        self.ui.pbt_detect.clicked.connect(lambda: self.pbt_detect_clicked())


    # view camera
    def viewCam1(self):
        global image1
        # read image in BGR format
        ret, image1 = cap.read()
        # convert image to RGB format
        image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
        # get image infos
        height, width, channel = image1.shape
        step = channel * width
        # create QImage from image
        qImg = QImage(image1.data, width, height, step, QImage.Format_RGB888)
        # show image in img_label
        self.ui.lb_live1.setPixmap(QPixmap.fromImage(qImg))
    
    def viewCam2(self):
        global image2
        # read image in BGR format
        ret, image2 = cap2.read()
        # convert image to RGB format
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
        height, width, channel = image2.shape
        step = channel * width
        qImg = QImage(image2.data, width, height, step, QImage.Format_RGB888)
        self.ui.lb_live2.setPixmap(QPixmap.fromImage(qImg))

    def scanDigitalInput(self):
        discrete_inputs = modbus_client.read_discreteinputs(0,4)
        if(discrete_inputs[0]==True):
            self.ui.lb_di_0.setText("ON")
            self.ui.lb_di_0.setStyleSheet("background-color: green;")
        else:
            self.ui.lb_di_0.setText("OFF")
            self.ui.lb_di_0.setStyleSheet("background-color: yellow;")

        if(discrete_inputs[1]==True):
            self.ui.lb_di_1.setText("ON")
            self.ui.lb_di_1.setStyleSheet("background-color: green;")
        else:
            self.ui.lb_di_1.setText("OFF")
            self.ui.lb_di_1.setStyleSheet("background-color: yellow;")
        
        if(discrete_inputs[2]==True):
            self.ui.lb_di_2.setText("ON")
            self.ui.lb_di_2.setStyleSheet("background-color: green;")
        else:
            self.ui.lb_di_2.setText("OFF")
            self.ui.lb_di_2.setStyleSheet("background-color: yellow;")
        
        if(discrete_inputs[3]==True):
            self.ui.lb_di_3.setText("ON")
            self.ui.lb_di_3.setStyleSheet("background-color: green;")
        else:
            self.ui.lb_di_3.setText("OFF")
            self.ui.lb_di_3.setStyleSheet("background-color: yellow;")
    
    def closeMainWindow(self):
        cap.release()
        self.close()
    
    def pbt_tray_clicked(self):
        if(self.ui.lb_tray.text()=="ON"):
            modbus_client.write_single_coil(0,0)
            self.ui.lb_tray.setText("OFF")
            self.ui.lb_tray.setStyleSheet("background-color: yellow;")
        elif(self.ui.lb_tray.text()=="OFF"):
            modbus_client.write_single_coil(0,1)
            self.ui.lb_tray.setText("ON")
            self.ui.lb_tray.setStyleSheet("background-color: green;")
    
    def pbt_lighting_clicked(self):
        if(self.ui.lb_lighting.text()=="ON"):
            modbus_client.write_single_coil(1,0)
            self.ui.lb_lighting.setText("OFF")
            self.ui.lb_lighting.setStyleSheet("background-color: yellow;")
        elif(self.ui.lb_lighting.text()=="OFF"):
            modbus_client.write_single_coil(1,1)
            self.ui.lb_lighting.setText("ON")
            self.ui.lb_lighting.setStyleSheet("background-color: green;")

    def scanRecipe(self):
        global para_recipe
        with open("static/recipe/recipe.txt",'r') as fr:
            para_recipe = fr.readline()
        self.ui.lb_tray_id.setText(para_recipe)
    
    def pbt_detect_clicked(self):
        image=cv2.vconcat([image1,image2])
        df,trays,traysstr,traysdf,frame_drawed = tray_reader(image)
        var_result = check_result(traysstr,para_recipe,self)
        
        self.ui.lb_result.setText(var_result)
        frame_drawed = cv2.cvtColor(frame_drawed, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_drawed.shape
        step = channel * width
        qImg = QImage(frame_drawed.data, width, height, step, QImage.Format_RGB888)
        self.ui.lb_imageframe1.setPixmap(QPixmap.fromImage(qImg))
        print(trays)
        print(traysstr)
        model=TableModel(traysdf)
        self.ui.tableView.setModel(model)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    # create and show mainWindow
    mainWindow = MainWindow2()
    mainWindow.show()

    sys.exit(app.exec_())
