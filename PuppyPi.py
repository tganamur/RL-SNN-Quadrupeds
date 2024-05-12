#!/usr/bin/env python3
# encoding: utf-8
import os
import re
import cv2
import sys
import math
import time
import sqlite3
import threading
import resource_rc
from socket import * 

from PuppyUi import Ui_Form
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from language import language

from ServoCmd import *
from ActionGroupControl import runActionGroup, stopActionGroup

import numpy as np

WORKING_DIR = '/home/pi/PuppyPi_PC_Software'
SERVO_MIDDLE_VALUE = 1500

from PuppyInstantiate import PuppyInstantiate as puppy



class MainWindow(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)                               
        self.setWindowIcon(QIcon(':/images/Puppy.png'))
        self.tabWidget.setCurrentIndex(0)  # 设置默认标签为第一个标签
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置选中整行，若不设置默认选中单元格
        self.message = QMessageBox()
        # self.timer = QTimer()
        self.resetServos_ = False
        self.path = WORKING_DIR
        self.actdir = self.path + "/ActionGroups/"
        self.button_controlaction_clicked('refresh')
        self.button_control_action_coord_clicked(self.Button_Refresh_Coord.objectName())

        ########################主界面###############################
        self.horizontalSliderServoDeviation = [self.horizontalSlider_deviation1, self.horizontalSlider_deviation2, self.horizontalSlider_deviation3
                                        , self.horizontalSlider_deviation4, self.horizontalSlider_deviation5, self.horizontalSlider_deviation6
                                        , self.horizontalSlider_deviation7, self.horizontalSlider_deviation8, ]

        self.servoDeviationLabel = [self.label_d1, self.label_d2, self.label_d3, self.label_d4
                                , self.label_d5, self.label_d6, self.label_d7, self.label_d8]
        
        for idx, ServoD in enumerate(self.horizontalSliderServoDeviation):
            d = getServoDeviation(idx + 1)
            ServoD.setValue(d)
            self.servoDeviationLabel[idx].setText(str(d))
            
        self.readDevOk = True

        self.horizontalSlider_deviation1.valueChanged.connect(lambda: self.servoDeviationValuechange(self.horizontalSlider_deviation1.objectName()))
        self.horizontalSlider_deviation2.valueChanged.connect(lambda: self.servoDeviationValuechange(self.horizontalSlider_deviation2.objectName()))
        self.horizontalSlider_deviation3.valueChanged.connect(lambda: self.servoDeviationValuechange(self.horizontalSlider_deviation3.objectName()))
        self.horizontalSlider_deviation4.valueChanged.connect(lambda: self.servoDeviationValuechange(self.horizontalSlider_deviation4.objectName()))
        self.horizontalSlider_deviation5.valueChanged.connect(lambda: self.servoDeviationValuechange(self.horizontalSlider_deviation5.objectName()))
        self.horizontalSlider_deviation6.valueChanged.connect(lambda: self.servoDeviationValuechange(self.horizontalSlider_deviation6.objectName()))
        self.horizontalSlider_deviation7.valueChanged.connect(lambda: self.servoDeviationValuechange(self.horizontalSlider_deviation7.objectName()))
        self.horizontalSlider_deviation8.valueChanged.connect(lambda: self.servoDeviationValuechange(self.horizontalSlider_deviation8.objectName()))


        self.LineEditServo = [self.lineEdit_servo1, self.lineEdit_servo2, self.lineEdit_servo3, self.lineEdit_servo4
                                , self.lineEdit_servo5, self.lineEdit_servo6, self.lineEdit_servo7, self.lineEdit_servo8]
        for s in self.LineEditServo:
            s.setValidator(QIntValidator(500, 2500))
        
        # 滑竿同步对应文本框的数值,及滑竿控制相应舵机转动与valuechange函数绑定
        self.horizontalSliderServo = [self.horizontalSlider_servo1, self.horizontalSlider_servo2, self.horizontalSlider_servo3
                                        , self.horizontalSlider_servo4, self.horizontalSlider_servo5, self.horizontalSlider_servo6
                                        , self.horizontalSlider_servo7, self.horizontalSlider_servo8,]
        for s in self.horizontalSliderServo:
            s.setMinimum(500)
            s.setMaximum(2500)

        self.horizontalSlider_servo1.valueChanged.connect(lambda: self.horizontalSliderServoValuechange(self.horizontalSlider_servo1.objectName()))
        self.horizontalSlider_servo2.valueChanged.connect(lambda: self.horizontalSliderServoValuechange(self.horizontalSlider_servo2.objectName()))
        self.horizontalSlider_servo3.valueChanged.connect(lambda: self.horizontalSliderServoValuechange(self.horizontalSlider_servo3.objectName()))
        self.horizontalSlider_servo4.valueChanged.connect(lambda: self.horizontalSliderServoValuechange(self.horizontalSlider_servo4.objectName()))
        self.horizontalSlider_servo5.valueChanged.connect(lambda: self.horizontalSliderServoValuechange(self.horizontalSlider_servo5.objectName()))
        self.horizontalSlider_servo6.valueChanged.connect(lambda: self.horizontalSliderServoValuechange(self.horizontalSlider_servo6.objectName()))
        self.horizontalSlider_servo7.valueChanged.connect(lambda: self.horizontalSliderServoValuechange(self.horizontalSlider_servo7.objectName()))
        self.horizontalSlider_servo8.valueChanged.connect(lambda: self.horizontalSliderServoValuechange(self.horizontalSlider_servo8.objectName()))


        # self.chinese = True
        self.language = 'Chinese'                        
        self.radioButton_zn.toggled.connect(lambda: self.LanguageSetting(self.radioButton_zn))
        self.radioButton_en.toggled.connect(lambda: self.LanguageSetting(self.radioButton_en))
        self.radioButton_zn.setChecked(True)
        

        # tableWidget点击获取定位的信号与icon_position函数（添加运行图标）绑定
        self.tableWidget.pressed.connect(self.icon_position)
        self.lineEdit_time.setValidator(QIntValidator(20, 30000))

        # 将编辑动作组的按钮点击时的信号与button_editaction_clicked函数绑定
        self.Button_ServoPowerDown.pressed.connect(lambda: self.button_editaction_clicked('servoPowerDown'))
        self.Button_AngularReadback.pressed.connect(lambda: self.button_editaction_clicked('angularReadback'))
        self.Button_AddAction.pressed.connect(lambda: self.button_editaction_clicked('addAction'))
        self.Button_DelectAction.pressed.connect(lambda: self.button_editaction_clicked('delectAction'))
        self.Button_DelectAllAction.pressed.connect(lambda: self.button_editaction_clicked('delectAllAction'))                                                 
        self.Button_UpdateAction.pressed.connect(lambda: self.button_editaction_clicked('updateAction'))
        self.Button_InsertAction.pressed.connect(lambda: self.button_editaction_clicked('insertAction'))
        self.Button_MoveUpAction.pressed.connect(lambda: self.button_editaction_clicked('moveUpAction'))
        self.Button_MoveDownAction.pressed.connect(lambda: self.button_editaction_clicked('moveDownAction'))        

        # 将运行及停止运行按钮点击的信号与button_runonline函数绑定
        self.Button_Run.clicked.connect(lambda: self.button_run('run'))

        self.Button_OpenActionGroup.pressed.connect(lambda: self.button_flie_operate('openActionGroup'))
        self.Button_SaveActionGroup.pressed.connect(lambda: self.button_flie_operate('saveActionGroup'))
        # self.Button_ReadDeviation.pressed.connect(lambda: self.button_flie_operate('readDeviation'))
        self.Button_DownloadDeviation.pressed.connect(lambda: self.button_flie_operate('downloadDeviation'))
        self.Button_TandemActionGroup.pressed.connect(lambda: self.button_flie_operate('tandemActionGroup'))
        self.Button_ReSetServos.pressed.connect(lambda: self.button_re_clicked('reSetServos'))
        

        # 将控制动作的按钮点击的信号与action_control_clicked函数绑定
        self.Button_DelectSingle.pressed.connect(lambda: self.button_controlaction_clicked('delectSingle'))
        self.Button_AllDelect.pressed.connect(lambda: self.button_controlaction_clicked('allDelect'))
        self.Button_RunAction.pressed.connect(lambda: self.button_controlaction_clicked('runAction'))
        self.Button_StopAction.pressed.connect(lambda: self.button_controlaction_clicked('stopAction'))
        self.Button_Refresh.pressed.connect(lambda: self.button_controlaction_clicked('refresh'))
        self.Button_Quit.pressed.connect(lambda: self.button_controlaction_clicked('quit'))

        
        
        # self.devNew = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.dev_change = False 
        self.totalTime = 0
        self.row = 0

        for idx, ServoD in enumerate(self.horizontalSliderServoDeviation):
            self.servoDeviationLabel[idx].setText(str(ServoD.value()))


        #################################坐标控制界面1#######################################    
        self.coordNameToIndexTable = {'legFR_X':0, 'legFR_Y':1, 'legFR_Z':2, 
                                        'legFL_X':3, 'legFL_Y':4, 'legFL_Z':5, 
                                        'legBR_X':6, 'legBR_Y':7, 'legBR_Z':8, 
                                        'legBL_X':9, 'legBL_Y':10, 'legBL_Z':11, }

        self.default_reset_coord = np.array([[ 0.,  0., 0., 0.],
                                             [ 0.,  0., 0., 0.],
                                             [-10,   -10,  -10,   -10, ]])
        self.doubleSpinBox_legs = [self.doubleSpinBox_legFR_X, self.doubleSpinBox_legFR_Y, self.doubleSpinBox_legFR_Z
                                , self.doubleSpinBox_legFL_X, self.doubleSpinBox_legFL_Y, self.doubleSpinBox_legFL_Z
                                , self.doubleSpinBox_legBR_X, self.doubleSpinBox_legBR_Y, self.doubleSpinBox_legBR_Z
                                , self.doubleSpinBox_legBL_X, self.doubleSpinBox_legBL_Y, self.doubleSpinBox_legBL_Z]
        for i,leg in enumerate(self.doubleSpinBox_legs):
            leg.setValue(self.default_reset_coord.T.flatten()[i])
            if '_Z' in leg.objectName():
                leg.setMinimum(-15)
                leg.setMaximum(-1)
            if '_X' in leg.objectName():
                leg.setMinimum(-15)
                leg.setMaximum(15)

        self.doubleSpinBox_legFL_X.valueChanged.connect(lambda: self.coordValueChange('legFL_X'))
        self.doubleSpinBox_legFL_Y.valueChanged.connect(lambda: self.coordValueChange('legFL_Y'))
        self.doubleSpinBox_legFL_Z.valueChanged.connect(lambda: self.coordValueChange('legFL_Z'))
        self.doubleSpinBox_legFR_X.valueChanged.connect(lambda: self.coordValueChange('legFR_X'))
        self.doubleSpinBox_legFR_Y.valueChanged.connect(lambda: self.coordValueChange('legFR_Y'))
        self.doubleSpinBox_legFR_Z.valueChanged.connect(lambda: self.coordValueChange('legFR_Z'))
        self.doubleSpinBox_legBL_X.valueChanged.connect(lambda: self.coordValueChange('legBL_X'))
        self.doubleSpinBox_legBL_Y.valueChanged.connect(lambda: self.coordValueChange('legBL_Y'))
        self.doubleSpinBox_legBL_Z.valueChanged.connect(lambda: self.coordValueChange('legBL_Z'))
        self.doubleSpinBox_legBR_X.valueChanged.connect(lambda: self.coordValueChange('legBR_X'))
        self.doubleSpinBox_legBR_Y.valueChanged.connect(lambda: self.coordValueChange('legBR_Y'))
        self.doubleSpinBox_legBR_Z.valueChanged.connect(lambda: self.coordValueChange('legBR_Z'))
        
        for s in self.doubleSpinBox_legs:
            s.setKeyboardTracking(False)

        self.tableWidget_Coord.pressed.connect(self.icon_position_coord)
        self.Button_SaveActionGroup_Coord.pressed.connect(lambda: self.button_flie_operate(self.Button_SaveActionGroup_Coord.objectName()))
        self.Button_OpenActionGroup_Coord.pressed.connect(lambda: self.button_flie_operate(self.Button_OpenActionGroup_Coord.objectName()))
        self.Button_TandemActionGroup_Coord.pressed.connect(lambda: self.button_flie_operate(self.Button_TandemActionGroup_Coord.objectName()))

        self.Button_AddCoord.pressed.connect(lambda: self.button_editCoord_clicked(self.Button_AddCoord.objectName()))
        self.Button_UpdateCoord.pressed.connect(lambda: self.button_editCoord_clicked(self.Button_UpdateCoord.objectName()))
        self.Button_DelectCoord.pressed.connect(lambda: self.button_editCoord_clicked(self.Button_DelectCoord.objectName()))
        self.Button_DelectAllCoord.pressed.connect(lambda: self.button_editCoord_clicked(self.Button_DelectAllCoord.objectName()))
        self.Button_InsertCoord.pressed.connect(lambda: self.button_editCoord_clicked(self.Button_InsertCoord.objectName()))
        self.Button_Run_Coord.pressed.connect(lambda: self.button_editCoord_clicked(self.Button_Run_Coord.objectName()))
        self.Button_MoveUpCoord.pressed.connect(lambda: self.button_editCoord_clicked(self.Button_MoveUpCoord.objectName()))
        self.Button_MoveDownCoord.pressed.connect(lambda: self.button_editCoord_clicked(self.Button_MoveDownCoord.objectName()))

        # 将坐标运行及停止运行按钮点击的信号与button_run_coord_online函数绑定
        self.Button_Run_Coord.clicked.connect(lambda: self.button_run_coord(self.Button_Run_Coord.objectName()))
        self.Button_Reset_Coord.pressed.connect(lambda: self.button_reset_coord(self.Button_Reset_Coord.objectName()))

        # 将控制坐标动作的按钮点击的信号与action_control_clicked函数绑定
        self.Button_DelectSingle_Coord.pressed.connect(lambda: self.button_control_action_coord_clicked(self.Button_DelectSingle_Coord.objectName()))
        self.Button_AllDelect_Coord.pressed.connect(lambda: self.button_control_action_coord_clicked(self.Button_AllDelect_Coord.objectName()))
        self.Button_RunAction_Coord.pressed.connect(lambda: self.button_control_action_coord_clicked(self.Button_RunAction_Coord.objectName()))
        self.Button_StopAction_Coord.pressed.connect(lambda: self.button_control_action_coord_clicked(self.Button_StopAction_Coord.objectName()))
        self.Button_Refresh_Coord.pressed.connect(lambda: self.button_control_action_coord_clicked(self.Button_Refresh_Coord.objectName()))

        self.totalTime_coord = 0
        self.mask_coordValueChange = False
        
        #################################副界面1#######################################
        self.id = 0
        self.dev = 0
        self.servoTemp = 0
        self.servoMin = 0
        self.servoMax = 0
        self.servoMinV = 0
        self.servoMaxV = 0
        self.servoMove = 0
        self.horizontalSlider_servoTemp.valueChanged.connect(lambda: self.horizontalSlider_valuechange('servoTemp'))
        self.horizontalSlider_servoMin.valueChanged.connect(lambda: self.horizontalSlider_valuechange('servoMin'))
        self.horizontalSlider_servoMax.valueChanged.connect(lambda: self.horizontalSlider_valuechange('servoMax'))
        self.horizontalSlider_servoMinV.valueChanged.connect(lambda: self.horizontalSlider_valuechange('servoMinV'))
        self.horizontalSlider_servoMaxV.valueChanged.connect(lambda: self.horizontalSlider_valuechange('servoMaxV'))
        self.horizontalSlider_servoMove.valueChanged.connect(lambda: self.horizontalSlider_valuechange('servoMove'))

        self.pushButton_read.pressed.connect(lambda: self.button_clicked('read'))
        self.pushButton_set.pressed.connect(lambda: self.button_clicked('set'))
        self.pushButton_default.pressed.connect(lambda: self.button_clicked('default'))
        self.pushButton_quit2.pressed.connect(lambda: self.button_clicked('quit2'))
        self.pushButton_resetPos.pressed.connect(lambda: self.button_clicked('resetPos'))
        
        self.validator2 = QIntValidator(-125, 125)
        self.lineEdit_servoDev.setValidator(self.validator2)
        
        self.tabWidget.currentChanged['int'].connect(self.tabchange)
        self.readOrNot = False
        for s in self.LineEditServo:
            s.setText(str(SERVO_MIDDLE_VALUE))
        self.tabWidget.removeTab(2)
        self.tabWidget.setCurrentIndex(1)

    def message_From(self, str):
        try:
            QMessageBox.about(self, '', str)
            time.sleep(0.01)
        except:
            pass


    # 弹窗提示函数
    def message_delect(self, str):
        messageBox = QMessageBox()
        messageBox.setWindowTitle(' ')
        messageBox.setText(str)
        messageBox.addButton(QPushButton('OK'), QMessageBox.YesRole)
        messageBox.addButton(QPushButton('Cancel'), QMessageBox.NoRole)
        return messageBox.exec_()


    # 窗口退出
    def closeEvent(self, e):        
        # result = QMessageBox.question(self,
        #                             "关闭窗口提醒",
        #                             "exit?",
        #                             QMessageBox.Yes | QMessageBox.No,
        #                             QMessageBox.No)
        result = QMessageBox.Yes
        if result == QMessageBox.Yes:
            self.camera_ui = True
            self.camera_ui_break = True
            QWidget.closeEvent(self, e)

            # try:
            #     rospy.ServiceProxy('/puppy_control/set_running', SetBool)(True)
            # except rospy.ServiceException as e:
            #     print("Service call failed: %s"%e)
        else:
            e.ignore()
    
    def LanguageSetting(self, name):
        if name.text() == '中文':
            self.language = 'Chinese'
        else:
            self.language = 'English'

        self.PanelLanguage(self.language)
            

    def keyPressEvent(self, event):
        if (event.key() == 16777220 or event.key() == 16777221) and self.tabWidget.currentIndex() == 0:
            self.resetServos_ = True

            for idx, l in enumerate(self.LineEditServo):
                pulse = int(l.text())
                self.horizontalSliderServo[idx].setValue(pulse)
                setServoPulse(idx+1, pulse, SERVO_MIDDLE_VALUE)

            self.resetServos_ = False
    
    def tabchange(self):
        if self.tabWidget.currentIndex() == 2:
        # if self.tabWidget.getTabText(self.tabWidget.currentIndex()) == '舵机调试工具':
            # if self.chinese:
            #     self.message_From('使用此面板时，请确保只连接了一个舵机，否则会引起冲突！')
            # else:
            #     self.message_From('Before debugging servo,make sure that the servo controller is connected with ONE servo.Otherwise it may cause a conflict!')
            self.message_From(language['MessageBox']['tabchange'][self.language])
    
    # 滑竿同步对应文本框的数值,及滑竿控制相应舵机转动
    def horizontalSliderServoValuechange(self, name):
        if not self.resetServos_:
            try:
                servoId = int(name[-2:])
            except:
                servoId = int(name[-1])

            servoAngle = str(self.horizontalSliderServo[servoId-1].value())
            self.LineEditServo[servoId-1].setText(servoAngle)
            setServoPulse(servoId, int(servoAngle), 20)
            
            
    def servoDeviationValuechange(self, name):
        try:
            servoId = int(name[-2:])
        except:
            servoId = int(name[-1])
        d = self.horizontalSliderServoDeviation[servoId-1].value()
        self.servoDeviationLabel[servoId-1].setText(str(d))
        setServoPulse(servoId,self.horizontalSliderServo[servoId -1].value(),0)
        time.sleep(0.03)
        setServoDeviation(servoId, d)
 

    def coordValueChange(self, name):
        if self.mask_coordValueChange:
            return
        
        rotated_foot_locations = np.array(
            [[ self.doubleSpinBox_legFR_X.value(),  self.doubleSpinBox_legFL_X.value(), self.doubleSpinBox_legBR_X.value(), self.doubleSpinBox_legBL_X.value()],
            [self.doubleSpinBox_legFR_Y.value(),   self.doubleSpinBox_legFL_Y.value(),  self.doubleSpinBox_legBR_Y.value(),   self.doubleSpinBox_legBL_Y.value(), ],
            [self.doubleSpinBox_legFR_Z.value(),    self.doubleSpinBox_legFL_Z.value(),    self.doubleSpinBox_legBR_Z.value(),    self.doubleSpinBox_legBL_Z.value(),   ]])
        
        rotated_foot_locations = rotated_foot_locations/100

        joint_angles = puppy.fourLegsRelativeCoordControl(rotated_foot_locations)
        puppy.servo_force_run()
        puppy.sendServoAngle(joint_angles)#, force_execute = True

        # msg = Polygon(list(map(Point32, rotated_foot_locations[0,:], rotated_foot_locations[1,:], rotated_foot_locations[2,:])))
        # self.fourLegsRelativeCoordControl_pub.publish(msg)
        

    def button_reset_coord(self, name):
        self.mask_coordValueChange = True

        for i, value in enumerate(self.default_reset_coord.T.flatten()) :
            self.doubleSpinBox_legs[i].setValue(float(value))
        # joint_angles = four_legs_inverse_kinematics_manual(reset/100,config)
        # hardware_interface.set_actuator_postions(joint_angles, 800)
        joint_angles = puppy.fourLegsRelativeCoordControl(self.default_reset_coord/100)
        puppy.servo_force_run()
        puppy.sendServoAngle(joint_angles, 800)#, force_execute = True

        self.mask_coordValueChange = False
        
    # 复位按钮点击事件
    def button_re_clicked(self, name):
        self.resetServos_ = True
        if name == 'reSetServos':
            for idx, l in enumerate(self.LineEditServo):
                l.setText(str(SERVO_MIDDLE_VALUE))
                self.horizontalSliderServo[idx].setValue(SERVO_MIDDLE_VALUE)
                setServoPulse(idx+1, SERVO_MIDDLE_VALUE, 1000)

            self.resetServos_ = False

    # 选项卡选择标签状态，获取对应舵机数值
    def tabindex(self, index):
        array = []
        for value in self.horizontalSliderServo:
            array.append(str(value.value()))
        return array

    def getIndexData(self, index):
        data = []
        for j in range(2, self.tableWidget.columnCount()):
            data.append(str(self.tableWidget.item(index, j).text()))
        return data

    def getIndexDataCoord(self, index):
        data = []
        for j in range(2, self.tableWidget_Coord.columnCount()):
            data.append(str(self.tableWidget_Coord.item(index, j).text()))
        return data

    # 往tableWidget表格添加一行数据的函数
    def add_line(self, item, timer, servoPulse):
        self.tableWidget.setItem(item, 1, QtWidgets.QTableWidgetItem(str(item + 1)))
        self.tableWidget.setItem(item, 2, QtWidgets.QTableWidgetItem(timer))
        for i, value in enumerate(servoPulse):
            self.tableWidget.setItem(item, i+3, QtWidgets.QTableWidgetItem(value))

    def add_line_coord(self, item, time, coord):
        self.tableWidget_Coord.setItem(item, 1, QtWidgets.QTableWidgetItem(str(item + 1)))
        self.tableWidget_Coord.setItem(item, 2, QtWidgets.QTableWidgetItem(time))
        for i, value in enumerate(coord):
            self.tableWidget_Coord.setItem(item, i+3, QtWidgets.QTableWidgetItem(value))

    def get_coord_array(self):
        array = []
        for value in self.doubleSpinBox_legs:
            array.append(str(value.value()))
        return array

    # 在定位行添加运行图标按钮
    def icon_position(self):
        toolButton_run = QtWidgets.QToolButton()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/index.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        toolButton_run.setIcon(icon)
        toolButton_run.setObjectName("toolButton_run")
        item = self.tableWidget.currentRow()
        self.tableWidget.setCellWidget(item, 0, toolButton_run)
        for i in range(self.tableWidget.rowCount()):
            if i != item:
                self.tableWidget.removeCellWidget(i, 0)
        toolButton_run.clicked.connect(self.action_one)

    def action_one(self):
        self.resetServos_ = True
        item = self.tableWidget.currentRow()
        # alist = []
        try:
            timer = int(self.tableWidget.item(self.tableWidget.currentRow(), 2).text())
            
            for i in range(0, self.tableWidget.columnCount()-3):
                value = self.tableWidget.item(item, i+3).text()
                setServoPulse(i+1, int(value), timer)
                self.horizontalSliderServo[i].setValue(int(value))
                self.LineEditServo[i].setText(value)

              
        except BaseException as e:
            print(e)
            self.message_From(language['MessageBox']['action_one'][self.language])
            # if self.chinese:
            #     self.message_From('运行出错!')
            # else:
            #     self.message_From('Running error')
        self.resetServos_ = False

    def icon_position_coord(self):
        toolButton_run = QtWidgets.QToolButton()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/index.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        toolButton_run.setIcon(icon)
        toolButton_run.setObjectName("toolButton_run")
        item = self.tableWidget_Coord.currentRow()
        self.tableWidget_Coord.setCellWidget(item, 0, toolButton_run)
        for i in range(self.tableWidget_Coord.rowCount()):
            if i != item:
                self.tableWidget_Coord.removeCellWidget(i, 0)
        toolButton_run.clicked.connect(self.action_one_coord)

    def action_one_coord(self):
        self.resetServos_ = True
        item = self.tableWidget_Coord.currentRow()
        
        try:
            time = int(self.tableWidget_Coord.item(self.tableWidget_Coord.currentRow(), 2).text())
            self.mask_coordValueChange = True
            rotated_foot_locations = np.zeros(12)
            for i in range(0, self.tableWidget_Coord.columnCount()-3):
                value = self.tableWidget_Coord.item(item, i+3).text()
                self.doubleSpinBox_legs[i].setValue(float(value))
                rotated_foot_locations[i] = float(value)
            rotated_foot_locations = rotated_foot_locations.reshape(4,3)
            rotated_foot_locations = rotated_foot_locations.T
            rotated_foot_locations = rotated_foot_locations/100

            joint_angles = puppy.fourLegsRelativeCoordControl(rotated_foot_locations)
            puppy.servo_force_run()
            puppy.sendServoAngle(joint_angles, time)#, force_execute = True

            
            self.mask_coordValueChange = False
        except BaseException as e:
            print(e)
            self.message_From(language['MessageBox']['action_one_coord'][self.language])
            # if self.chinese:
            #     self.message_From('运行出错')
            # else:
            #     self.message_From('Running error')
        self.resetServos_ = False



    def button_editCoord_clicked(self, name):
        coordList = self.get_coord_array()
        RowCont = self.tableWidget_Coord.rowCount()
        item = self.tableWidget_Coord.currentRow()
        if name == self.Button_AddCoord.objectName():    # 添加坐标
            if self.spinBox_run_coord_time.value() < 5:
                self.message_From(language['MessageBox']['Button_AddCoord'][self.language])
                # if self.chinese:
                #     self.message_From('运行时间必须大于5')
                # else:
                #     self.message_From('Run time must greater than 5')
                return
            self.tableWidget_Coord.insertRow(RowCont)    # 增加一行
            self.tableWidget_Coord.selectRow(RowCont)    # 定位最后一行为选中行
            self.add_line_coord(RowCont, str(self.spinBox_run_coord_time.value()), coordList)
            self.totalTime_coord += self.spinBox_run_coord_time.value()
            self.label_TotalTime_coord.setText(str((self.totalTime_coord)/1000.0))

        if name == self.Button_DelectCoord.objectName():    # 删除坐标
            if RowCont != 0:
                self.totalTime_coord -= int(self.tableWidget_Coord.item(item, 2).text())
                self.tableWidget_Coord.removeRow(item)  # 删除选定行                
                self.label_TotalTime_coord.setText(str((self.totalTime_coord)/1000.0))
        if name == self.Button_DelectAllCoord.objectName():
            # result = self.message_delect('此操作会删除列表中的所有动作，是否继续？')
            result = self.message_delect(language['MessageBox']['Button_DelectAllCoord'][self.language])
            if result == 0:                              
                for i in range(RowCont):
                    self.tableWidget_Coord.removeRow(0)
                self.totalTime_coord = 0
                self.label_TotalTime_coord.setText(str(self.totalTime_coord))
            else:
                pass
        if name == self.Button_UpdateCoord.objectName():    # 更新坐标
            if self.spinBox_run_coord_time.value() < 5:
                self.message_From(language['MessageBox']['Button_UpdateCoord'][self.language])
                
                # if self.chinese:
                #     self.message_From('运行时间必须大于5')
                # else:
                #     self.message_From('Run time must greater than 5')
                return

            self.add_line_coord(item, str(self.spinBox_run_coord_time.value()), coordList)
            self.totalTime_coord = 0
            for i in range(RowCont):
                self.totalTime_coord += int(self.tableWidget_Coord.item(i,2).text())
            self.label_TotalTime_coord.setText(str((self.totalTime_coord)/1000.0))            
        if name == self.Button_InsertCoord.objectName():    # 插入坐标
            if item == -1:
                return
            if self.spinBox_run_coord_time.value() < 5:
                self.message_From(language['MessageBox']['Button_InsertCoord'][self.language])
                
                # if self.chinese:
                #     self.message_From('运行时间必须大于5')
                # else:
                #     self.message_From('Run time must greater than 5')
                return

            self.tableWidget_Coord.insertRow(item)       # 插入一行
            self.tableWidget_Coord.selectRow(item)
            self.add_line_coord(item, str(self.spinBox_run_coord_time.value()), coordList)
            # self.totalTime += int(self.lineEdit_time.text())
            self.totalTime_coord += self.spinBox_run_coord_time.value()
            self.label_TotalTime_coord.setText(str((self.totalTime_coord)/1000.0))
        if name == self.Button_MoveUpCoord.objectName():
            if item == 0 or item == -1:
                return
            current_data = self.getIndexDataCoord(item)
            uplist_data = self.getIndexDataCoord(item - 1)
            # print(current_data)
            # print(uplist_data)
            self.add_line_coord(item - 1, current_data[0], current_data[1:])
            self.add_line_coord(item, uplist_data[0], uplist_data[1:])
            self.tableWidget_Coord.selectRow(item - 1) 

        if name == self.Button_MoveDownCoord.objectName():
            if item == RowCont - 1:
                return
            current_data = self.getIndexDataCoord(item)
            downlist_data = self.getIndexDataCoord(item + 1)           
            self.add_line_coord(item + 1, current_data[0], current_data[1:])
            self.add_line_coord(item, downlist_data[0], downlist_data[1:])
            self.tableWidget_Coord.selectRow(item + 1)
                             
        for i in range(self.tableWidget_Coord.rowCount()):    #刷新编号值
            self.tableWidget_Coord.item(i , 1).setFlags(self.tableWidget_Coord.item(i , 1).flags() & ~Qt.ItemIsEditable)
            self.tableWidget_Coord.setItem(i,1,QtWidgets.QTableWidgetItem(str(i + 1)))

        self.icon_position_coord()
    # 编辑动作组按钮点击事件
    def button_editaction_clicked(self, name):
        servoPulseList = self.tabindex(self.tabWidget.currentIndex())
        RowCont = self.tableWidget.rowCount()
        item = self.tableWidget.currentRow()
        if name == 'servoPowerDown':
            for id in range(0, self.tableWidget.columnCount()-3):
                unloadServo(id+1)
            self.message_From(language['MessageBox']['servoPowerDown'][self.language])
                
            # if self.chinese:
            #     self.message_From('掉电成功')
            # else:
            #     self.message_From('success')
        if name == 'angularReadback':
            self.tableWidget.insertRow(RowCont)    # 增加一行
            self.tableWidget.selectRow(RowCont)    # 定位最后一行为选中行
            use_time = int(self.lineEdit_time.text())
            # data = [RowCont, str(use_time)]
            data = []
            for i in range(0, self.tableWidget.columnCount()-3):
                pulse = getServoPulse(i+1)
                if pulse is None:
                    return
                else:
                    data.append(str(pulse))                                       
            if use_time < 5:
                if self.chinese:
                    self.message_From('运行时间必须大于5ms')
                else:
                    self.message_From('Run time must be greater than 5ms')
                return         
            self.add_line(RowCont, str(use_time), data)
            self.totalTime += use_time
            self.label_TotalTime.setText(str((self.totalTime)/1000.0))            
        if name == 'addAction':    # 添加动作
            if int(self.lineEdit_time.text()) < 5:
                self.message_From(language['MessageBox']['addAction'][self.language])
            
                # if self.chinese:
                #     self.message_From('运行时间必须大于5')
                # else:
                #     self.message_From('Run time must greater than 5')
                return
            self.tableWidget.insertRow(RowCont)    # 增加一行
            self.tableWidget.selectRow(RowCont)    # 定位最后一行为选中行
            self.add_line(RowCont, str(self.lineEdit_time.text()), servoPulseList)
            self.totalTime += int(self.lineEdit_time.text())
            self.label_TotalTime.setText(str((self.totalTime)/1000.0))
        if name == 'delectAction':    # 删除动作
            if RowCont != 0:
                self.totalTime -= int(self.tableWidget.item(item, 2).text())
                self.tableWidget.removeRow(item)  # 删除选定行                
                self.label_TotalTime.setText(str((self.totalTime)/1000.0))
        if name == 'delectAllAction':
            # result = self.message_delect('此操作会删除列表中的所有动作，是否继续？')
            result = self.message_delect(language['MessageBox']['delectAllAction'][self.language])
            if result == 0:                              
                for i in range(RowCont):
                    self.tableWidget.removeRow(0)
                self.totalTime = 0
                self.label_TotalTime.setText(str(self.totalTime))
            else:
                pass          
        if name == 'updateAction':    # 更新动作
            if int(self.lineEdit_time.text()) < 5:
                self.message_From(language['MessageBox']['updateAction'][self.language])
            
                # if self.chinese:
                #     self.message_From('运行时间必须大于5')
                # else:
                #     self.message_From('Run time must greater than 5')
                return

            self.add_line(item, str(self.lineEdit_time.text()), servoPulseList)
            self.totalTime = 0
            for i in range(RowCont):
                self.totalTime += int(self.tableWidget.item(i,2).text())
            self.label_TotalTime.setText(str((self.totalTime)/1000.0))            
        if name == 'insertAction':    # 插入动作
            if item == -1:
                return
            if int(self.lineEdit_time.text()) < 5:
                self.message_From(language['MessageBox']['updateAction'][self.language])
            
                # if self.chinese:
                #     self.message_From('运行时间必须大于5')
                # else:
                #     self.message_From('Run time must greater than 5')
                return

            self.tableWidget.insertRow(item)       # 插入一行
            self.tableWidget.selectRow(item)
            self.add_line(item, str(self.lineEdit_time.text()), servoPulseList)
            self.totalTime += int(self.lineEdit_time.text())
            self.label_TotalTime.setText(str((self.totalTime)/1000.0))
        if name == 'moveUpAction':
            if item == 0 or item == -1:
                return
            current_data = self.getIndexData(item)
            uplist_data = self.getIndexData(item - 1)
            self.add_line(item - 1, current_data[0], current_data[1:])
            self.add_line(item, uplist_data[0], uplist_data[1:])
            self.tableWidget.selectRow(item - 1) 

            
        if name == 'moveDownAction':
            if item == RowCont - 1:
                return
            current_data = self.getIndexData(item)
            downlist_data = self.getIndexData(item + 1)           
            self.add_line(item + 1, current_data[0], current_data[1:])
            self.add_line(item, downlist_data[0], downlist_data[1:])
            self.tableWidget.selectRow(item + 1)
                             
        for i in range(self.tableWidget.rowCount()):    #刷新编号值
            self.tableWidget.item(i , 1).setFlags(self.tableWidget.item(i , 1).flags() & ~Qt.ItemIsEditable)
            self.tableWidget.setItem(i,1,QtWidgets.QTableWidgetItem(str(i + 1)))
        self.icon_position()

    # 在线坐标运行按钮点击事件
    def button_run_coord(self, name):
        if self.tableWidget_Coord.rowCount() == 0:
            self.message_From(language['MessageBox']['Button_Run_Coord_Run'][self.language])
            
            # if self.chinese:
            #     self.message_From('请先添加动作!')
            # else:
            #     self.message_From('Add action first!')
        else:
            if self.Button_Run_Coord.text() == '运行' or self.Button_Run_Coord.text() == 'Run':
                # self.message_From(language['MessageBox']['Button_Run_Coord_Run'][self.language])
            
                if self.language == 'Chinese':
                    self.Button_Run_Coord.setText('停止')
                else:
                    self.Button_Run_Coord.setText('Stop')
                self.row = self.tableWidget_Coord.currentRow()
                self.tableWidget_Coord.selectRow(self.row)
                self.icon_position_coord()
                self.timer_coord = QTimer()
                self.timer_coord_time_list = [0]*self.row
                # self.action_online(self.row)
                # print("self.row",self.row)
                if self.checkBox_run_Coord_cycle.isChecked():
                    for i in range(self.row, self.tableWidget_Coord.rowCount()):
                        s = self.tableWidget_Coord.item(i,2).text()
                        # self.timer_coord.start(int(s))       # 设置计时间隔并启动
                        self.timer_coord_time_list.append(int(s))
                    self.timer_coord.timeout.connect(self.operate1_coord)
                else:
                    for i in range(self.row, self.tableWidget_Coord.rowCount()):
                        s = self.tableWidget_Coord.item(i,2).text()
                        # self.timer_coord.start(int(s))       # 设置计时间隔并启动
                        self.timer_coord_time_list.append(int(s))
                    self.timer_coord.timeout.connect(self.operate2_coord)
                self.action_one_coord()
                self.timer_coord.start(self.timer_coord_time_list[self.row])
            elif self.Button_Run_Coord.text() == '停止' or self.Button_Run_Coord.text() == 'Stop':
                self.timer_coord.stop()
                if self.language == 'Chinese':
                    self.Button_Run_Coord.setText('运行')
                else:
                    self.Button_Run_Coord.setText('Run')
                self.message_From(language['MessageBox']['Button_Run_Coord_Stop'][self.language])
                
                # if self.chinese:
                #     self.Button_Run_Coord.setText('运行')
                #     self.message_From('运行结束!')
                # else:
                #     self.Button_Run_Coord.setText('Run')
                #     self.message_From('Run over!')  

    def operate1_coord(self):
        item = self.tableWidget_Coord.currentRow()
        if item == self.tableWidget_Coord.rowCount() - 1:
            self.tableWidget_Coord.selectRow(self.row)
            # self.action_online(self.row)
            self.action_one_coord()
        else:
            self.tableWidget_Coord.selectRow(item + 1)
            # self.action_online(item + 1)
            self.action_one_coord()
        self.timer_coord.start(self.timer_coord_time_list[self.tableWidget_Coord.currentRow()])
        self.icon_position_coord()

    def operate2_coord(self):
        item = self.tableWidget_Coord.currentRow()
        if item == self.tableWidget_Coord.rowCount() - 1:
            self.timer_coord.stop()
            if self.language == 'Chinese':
                self.Button_Run_Coord.setText('运行')
            else:
                self.Button_Run_Coord.setText('Run')

            # if self.chinese:
            #     self.Button_Run_Coord.setText('运行')
            #     self.message_From('运行结束!')
            # else:
            #     self.Button_Run_Coord.setText('Run')
            #     self.message_From('Run over!') 
            self.message_From(language['MessageBox']['Button_Run_Coord_Stop'][self.language])
                
        else:
            self.tableWidget_Coord.selectRow(item + 1)
            # self.action_online(item + 1)
            self.action_one_coord()
            self.timer_coord.start(self.timer_coord_time_list[self.tableWidget_Coord.currentRow()])
        self.icon_position_coord()

    # 在线运行按钮点击事件
    def button_run(self, name):
        if self.tableWidget.rowCount() == 0:
            self.message_From(language['MessageBox']['button_run'][self.language])
            
            # if self.chinese:
            #     self.message_From('请先添加动作!')
            # else:
            #     self.message_From('Add action first!')
        else:
            if name == 'run':
                if self.Button_Run.text() == '运行' or self.Button_Run.text() == 'Run':
                    if self.language == 'Chinese':
                        self.Button_Run.setText('停止')
                    else:
                        self.Button_Run.setText('Stop')
                    self.row = self.tableWidget.currentRow()
                    self.tableWidget.selectRow(self.row)
                    self.icon_position()
                    self.timer = QTimer()
                    self.timer_time_list = [0]*self.row
                    # self.action_online(self.row)
                    if self.checkBox.isChecked():
                        for i in range(self.tableWidget.rowCount() - self.row):
                            s = self.tableWidget.item(i,2).text()
                            self.timer_time_list.append(int(s) )
                        self.timer.timeout.connect(self.operate1)
                        #     self.timer.start(int(s))       # 设置计时间隔并启动
                        # self.timer.timeout.connect(self.operate1)
                    else:
                        for i in range(self.tableWidget.rowCount() - self.row):
                            s = self.tableWidget.item(i,2).text()
                            self.timer_time_list.append(int(s) )
                        self.timer.timeout.connect(self.operate2)
                    self.action_one()
                    self.timer.start(self.timer_time_list[self.row])
                        #     self.timer.start(int(s))       # 设置计时间隔并启动
                        # self.timer.timeout.connect(self.operate2)
                elif self.Button_Run.text() == '停止' or self.Button_Run.text() == 'Stop':
                    self.timer.stop()
                    if self.language == 'Chinese':
                        self.Button_Run.setText('运行')
                        # self.message_From('运行结束!')
                    else:
                        self.Button_Run.setText('Run')
                        # self.message_From('Run over!')  
                    self.message_From(language['MessageBox']['Button_Run_Stop'][self.language])
            
    def operate1(self):
        item = self.tableWidget.currentRow()
        if item == self.tableWidget.rowCount() - 1:
            self.tableWidget.selectRow(self.row)
            # self.action_online(self.row)
            self.action_one()
        else:
            self.tableWidget.selectRow(item + 1)
            # self.action_online(item + 1)
            self.action_one()
        self.timer.start(self.timer_time_list[self.tableWidget.currentRow()])
        self.icon_position()

    def operate2(self):
        item = self.tableWidget.currentRow()
        if item == self.tableWidget.rowCount() - 1:
            self.timer.stop()
            # if self.chinese:
            if self.language == 'Chinese':
                self.Button_Run.setText('运行')
                # self.message_From('运行结束!')
            else:
                self.Button_Run.setText('Run')
                # self.message_From('Run over!') 
            self.message_From(language['MessageBox']['operate2'][self.language])
            
        else:
            self.tableWidget.selectRow(item + 1)
            # self.action_online(item + 1)
            self.action_one()
            self.timer.start(self.timer_time_list[self.tableWidget.currentRow()])
        self.icon_position()

    def action_online(self, item):
        try:
            time = int(self.tableWidget.item(item, 2).text())
            for j in range(0, self.tableWidget.columnCount()-3):
                # data.extend([j+1, int(self.tableWidget.item(item, j+3).text())])
                setServoPulse(j+1, int(self.tableWidget.item(item, j+3).text()), time)     
        except Exception:
            self.timer.stop()
            # if self.chinese:
            if self.language == 'Chinese':
                self.Button_Run.setText('运行')
                # self.message_From('运行出错!')
            else:
                self.Button_Run.setText('Run')
                # self.message_From('Run error!')              
            self.message_From(language['MessageBox']['action_online'][self.language])
            
    # 文件打开及保存按钮点击事件
    def button_flie_operate(self, name):
        try:            
            if name == 'openActionGroup' or name == self.Button_OpenActionGroup_Coord.objectName():
                dig_o = QFileDialog()
                dig_o.setFileMode(QFileDialog.ExistingFile)
                if name == 'openActionGroup':
                    dig_o.setNameFilter('d6a Flies(*.d6a)')
                    openfile = dig_o.getOpenFileName(self, 'OpenFile', '', 'd6a Flies(*.d6a)')
                elif name == self.Button_OpenActionGroup_Coord.objectName():
                    dig_o.setNameFilter('d6a Flies(*.d6ac)')
                    openfile = dig_o.getOpenFileName(self, 'OpenFile', '', 'd6a Flies(*.d6ac)')
                # 打开单个文件
                # 参数一：设置父组件；参数二：QFileDialog的标题
                # 参数三：默认打开的目录，“.”点表示程序运行目录，/表示当前盘符根目录
                # 参数四：对话框的文件扩展名过滤器Filter，比如使用 Image files(*.jpg *.gif) 表示只能显示扩展名为.jpg或者.gif文件
                # 设置多个文件扩展名过滤，使用双引号隔开；“All Files(*);;PDF Files(*.pdf);;Text Files(*.txt)”
                path = openfile[0]
                try:
                    if path != '':
                        rbt = QSqlDatabase.addDatabase("QSQLITE")
                        rbt.setDatabaseName(path)
                        if name == 'openActionGroup':
                            if rbt.open():
                                actgrp = QSqlQuery()
                                if (actgrp.exec("select * from ActionGroup ")):
                                    self.tableWidget.setRowCount(0)
                                    self.tableWidget.clearContents()
                                    self.totalTime = 0
                                    while (actgrp.next()):
                                        count = self.tableWidget.rowCount()
                                        self.tableWidget.setRowCount(count + 1)
                                        for i in range(self.tableWidget.columnCount()-1):
                                            self.tableWidget.setItem(count, i + 1, QtWidgets.QTableWidgetItem(str(actgrp.value(i))))
                                            if i == 1:
                                                self.totalTime += actgrp.value(i)
                                            self.tableWidget.update()
                                            self.tableWidget.selectRow(count)
                                        self.tableWidget.item(count , 1).setFlags(self.tableWidget.item(count , 1).flags() & ~Qt.ItemIsEditable)                                        
                            self.icon_position()
                            rbt.close()
                            self.label_TotalTime.setText(str(self.totalTime/1000.0))
                        elif name == self.Button_OpenActionGroup_Coord.objectName():
                            if rbt.open():
                                actgrp = QSqlQuery()
                                if (actgrp.exec("select * from ActionGroup ")):
                                    self.tableWidget_Coord.setRowCount(0)
                                    self.tableWidget_Coord.clearContents()
                                    self.totalTime_coord = 0
                                    while (actgrp.next()):
                                        count = self.tableWidget_Coord.rowCount()
                                        self.tableWidget_Coord.setRowCount(count + 1)
                                        for i in range(self.tableWidget_Coord.columnCount()-1):
      
                                            self.tableWidget_Coord.setItem(count, i + 1, QtWidgets.QTableWidgetItem(str(actgrp.value(i))))
                                            if i == 1:
                                                self.totalTime_coord += actgrp.value(i)
                                            self.tableWidget_Coord.update()
                                            self.tableWidget_Coord.selectRow(count)
                                        self.tableWidget_Coord.item(count , 1).setFlags(self.tableWidget_Coord.item(count , 1).flags() & ~Qt.ItemIsEditable)                                        
                            self.icon_position_coord()
                            rbt.close()
                            self.label_TotalTime_coord.setText(str(self.totalTime_coord/1000.0))
                except:
                    self.message_From(language['MessageBox']['button_flie_operate'][self.language])
            
                    # if self.chinese:
                    #     self.message_From('动作组错误')
                    # else:
                    #     self.message_From('Wrong action format')
                    
            if name == 'saveActionGroup' or name == self.Button_SaveActionGroup_Coord.objectName():
                dig_s = QFileDialog()
                if name == 'saveActionGroup': 
                    if self.tableWidget.rowCount() == 0:
                        self.message_From(language['MessageBox']['saveActionGroup'][self.language])
            
                        # if self.chinese:
                        #     self.message_From('动作列表是空的哦，没啥要保存的')
                        # else:
                        #     self.message_From('The action list is empty，nothing to save')
                        return
                    savefile = dig_s.getSaveFileName(self, 'Savefile', '', 'd6a Flies(*.d6a)')
                elif name == self.Button_SaveActionGroup_Coord.objectName():
                    if self.tableWidget_Coord.rowCount() == 0:
                        self.message_From(language['MessageBox']['Button_SaveActionGroup_Coord'][self.language])
            
                        # if self.chinese:
                        #     self.message_From('动作列表是空的哦，没啥要保存的')
                        # else:
                        #     self.message_From('The action list is empty，nothing to save')
                        return
                    savefile = dig_s.getSaveFileName(self, 'Savefile', '', 'd6a Flies(*.d6ac)')
                path = savefile[0]
                if os.path.isfile(path):
                    os.system('sudo rm ' + path)

                if path != '':
                    if name == 'saveActionGroup':                     
                        if path[-4:] == '.d6a':conn = sqlite3.connect(path)
                        else:conn = sqlite3.connect(path + '.d6a')
                    elif name == self.Button_SaveActionGroup_Coord.objectName():                    
                        if path[-5:] == '.d6ac':conn = sqlite3.connect(path)
                        else:conn = sqlite3.connect(path + '.d6ac')
                    
                    c = conn.cursor()  
                    if name == 'saveActionGroup':
                        execute_str = '''CREATE TABLE ActionGroup([Index] INTEGER PRIMARY KEY AUTOINCREMENT
                        NOT NULL ON CONFLICT FAIL
                        UNIQUE ON CONFLICT ABORT,
                        Time INT'''
                        for idx in range(len(self.horizontalSliderServo)):
                            execute_str = execute_str + ',Servo' + str(idx+1) + ' INT'
                        execute_str += ');'
                        c.execute(execute_str)    
                        
                                          
                        # c.execute('''CREATE TABLE ActionGroup([Index] INTEGER PRIMARY KEY AUTOINCREMENT
                        # NOT NULL ON CONFLICT FAIL
                        # UNIQUE ON CONFLICT ABORT,
                        # Time INT,
                        # Servo1 INT,
                        # Servo2 INT,
                        # Servo3 INT,
                        # Servo4 INT,
                        # Servo5 INT,
                        # Servo6 INT,
                        # Servo7 INT,
                        # Servo8 INT);''')                      
                        insert_sql_str_0 = "INSERT INTO ActionGroup(Time"
                        for idx in range(len(self.horizontalSliderServo)):
                            insert_sql_str_0 = insert_sql_str_0 + ' ,Servo' + str(idx+1)
                        insert_sql_str_0 += ') VALUES('
                        for i in range(self.tableWidget.rowCount()):
                            # insert_sql = "INSERT INTO ActionGroup(Time, Servo1, Servo2, Servo3, Servo4, Servo5, Servo6, Servo7, Servo8) VALUES("
                            insert_sql_str = insert_sql_str_0
                            for j in range(2, self.tableWidget.columnCount()):
                                if j == self.tableWidget.columnCount() - 1:
                                    insert_sql_str += str(self.tableWidget.item(i, j).text())
                                else:
                                    insert_sql_str += str(self.tableWidget.item(i, j).text()) + ','
                            
                            insert_sql_str += ");"
                            c.execute(insert_sql_str)
                    elif name == self.Button_SaveActionGroup_Coord.objectName():
                        c.execute('''CREATE TABLE ActionGroup([Index] INTEGER PRIMARY KEY AUTOINCREMENT
                        NOT NULL ON CONFLICT FAIL
                        UNIQUE ON CONFLICT ABORT,
                        Time INT,
                        C1 FLOAT,
                        C2 FLOAT,
                        C3 FLOAT,
                        C4 FLOAT,
                        C5 FLOAT,
                        C6 FLOAT,
                        C7 FLOAT,
                        C8 FLOAT,
                        C9 FLOAT,
                        C10 FLOAT,
                        C11 FLOAT,
                        C12 FLOAT);''')                      
                        for i in range(self.tableWidget_Coord.rowCount()):
                            insert_sql = "INSERT INTO ActionGroup(Time, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12) VALUES("
                            for j in range(2, self.tableWidget_Coord.columnCount()):
                                if j == self.tableWidget_Coord.columnCount() - 1:
                                    insert_sql += str(self.tableWidget_Coord.item(i, j).text())
                                else:
                                    insert_sql += str(self.tableWidget_Coord.item(i, j).text()) + ','
                            
                            insert_sql += ");"
                            c.execute(insert_sql)
                    
                    conn.commit()
                    conn.close()
                    self.button_controlaction_clicked('refresh')
                    self.button_control_action_coord_clicked(self.Button_Refresh_Coord.objectName())
            # if name == 'readDeviation':
            #     id = ''
            #     self.readDevOk = True

            #     for i in range(0, self.tableWidget.columnCount()-3):
            #         dev = getBusServoDeviation(i+1)
            #         if dev == None:
            #             id += (' id' + str(i+1))
            #         elif dev > 125:  # 负数
            #             self.horizontalSliderServoDeviation[i].setValue(-(0xff - (dev - 1)))                        
            #         else:
            #             self.horizontalSliderServoDeviation[i].setValue(dev)


            #     if id == '':
            #         if self.chinese:
            #             self.message_From('读取偏差成功!')
            #         else:
            #             self.message_From('success!')
            #     else:
            #         if self.chinese:
            #             self.message_From(id + '号舵机偏差读取失败!')
            #         else:
            #             self.message_From('Failed to read the deviation of' + id)
            if name == 'downloadDeviation':
                saveServoDeviation("all")
                self.message_From(language['MessageBox']['downloadDeviation'][self.language])
            
                # if self.chinese:
                #     self.message_From('保存偏差成功!')
                # else:
                #     self.message_From('success!')

                # if self.readDevOk:                    
                #     for id in range(1, 13):
                #         saveServoDeviation(id)
                #     if self.chinese:
                #         self.message_From('下载偏差成功!')
                #     else:
                #         self.message_From('success!')
                # else:
                #     if self.chinese:
                #         self.message_From('请先读取偏差！')
                #     else:
                #         self.message_From('Please read the deviation first！')
            if name == 'tandemActionGroup':
                dig_t = QFileDialog()
                dig_t.setFileMode(QFileDialog.ExistingFile)
                dig_t.setNameFilter('d6a Flies(*.d6a)')
                openfile = dig_t.getOpenFileName(self, 'OpenFile', '', 'd6a Flies(*.d6a)')
                # 打开单个文件
                # 参数一：设置父组件；参数二：QFileDialog的标题
                # 参数三：默认打开的目录，“.”点表示程序运行目录，/表示当前盘符根目录
                # 参数四：对话框的文件扩展名过滤器Filter，比如使用 Image files(*.jpg *.gif) 表示只能显示扩展名为.jpg或者.gif文件
                # 设置多个文件扩展名过滤，使用双引号隔开；“All Files(*);;PDF Files(*.pdf);;Text Files(*.txt)”
                path = openfile[0]
                try:
                    if path != '':
                        tbt = QSqlDatabase.addDatabase("QSQLITE")
                        tbt.setDatabaseName(path)
                        if tbt.open():
                            actgrp = QSqlQuery()
                            if (actgrp.exec("select * from ActionGroup ")):
                                while (actgrp.next()):
                                    count = self.tableWidget.rowCount()
                                    self.tableWidget.setRowCount(count + 1)
                                    for i in range(self.tableWidget.columnCount()-1):
                                        if i == 0:
                                            self.tableWidget.setItem(count, i + 1, QtWidgets.QTableWidgetItem(str(count + 1)))
                                        else:                      
                                            self.tableWidget.setItem(count, i + 1, QtWidgets.QTableWidgetItem(str(actgrp.value(i))))
                                        if i == 1:
                                            self.totalTime += actgrp.value(i)
                                        self.tableWidget.update()
                                        self.tableWidget.selectRow(count)
                                    self.tableWidget.item(count , 1).setFlags(self.tableWidget.item(count , 1).flags() & ~Qt.ItemIsEditable)
                        self.icon_position()
                        tbt.close()
                        self.label_TotalTime.setText(str(self.totalTime/1000.0))
                except:
                    self.message_From(language['MessageBox']['tandemActionGroup'][self.language])
            
                    # if self.chinese:
                    #     self.message_From('动作组错误')
                    # else:
                    #     self.message_From('Wrong action format')
            if name == self.Button_TandemActionGroup_Coord.objectName():
                dig_t = QFileDialog()
                dig_t.setFileMode(QFileDialog.ExistingFile)
                dig_t.setNameFilter('d6a Flies(*.d6ac)')
                openfile = dig_t.getOpenFileName(self, 'OpenFile', '', 'd6a Flies(*.d6ac)')

                path = openfile[0]
                try:
                    if path != '':
                        tbt = QSqlDatabase.addDatabase("QSQLITE")
                        tbt.setDatabaseName(path)
                        if tbt.open():
                            actgrp = QSqlQuery()
                            if (actgrp.exec("select * from ActionGroup ")):
                                while (actgrp.next()):
                                    count = self.tableWidget_Coord.rowCount()
                                    self.tableWidget_Coord.setRowCount(count + 1)
                                    for i in range(self.tableWidget_Coord.columnCount()-1):
                                        if i == 0:
                                            self.tableWidget_Coord.setItem(count, i + 1, QtWidgets.QTableWidgetItem(str(count + 1)))
                                        else:                      
                                            self.tableWidget_Coord.setItem(count, i + 1, QtWidgets.QTableWidgetItem(str(actgrp.value(i))))
                                        if i == 1:
                                            self.totalTime_coord += actgrp.value(i)
                                        self.tableWidget_Coord.update()
                                        self.tableWidget_Coord.selectRow(count)
                                    self.tableWidget_Coord.item(count , 1).setFlags(self.tableWidget_Coord.item(count , 1).flags() & ~Qt.ItemIsEditable)
                        self.icon_position_coord()
                        tbt.close()
                        self.label_TotalTime_coord.setText(str(self.totalTime_coord/1000.0))
                except:
                    self.message_From(language['MessageBox']['Button_TandemActionGroup_Coord'][self.language])
            
                    # if self.chinese:
                    #     self.message_From('动作组错误')
                    # else:
                    #     self.message_From('Wrong action format')
        except BaseException as e:
            print(e)

    def listActions(self, path, format = '.d6a'):
        if not os.path.exists(path):
            os.mkdir(path)
        pathlist = os.listdir(path)
        actList = []
        
        for f in pathlist:
            if f[0] == '.':
                pass
            else:
                if format == '.d6a':
                    if f[-4:] == format:
                        f.replace('-', '')
                        if f:
                            actList.append(f[0:-4])
                elif format == '.d6ac':
                    if f[-5:] == format:
                        f.replace('-', '')
                        if f:
                            actList.append(f[0:-5])
        return actList
    
    def refresh_action(self):
        actList = self.listActions(self.actdir)
        actList.sort()
        
        if len(actList) != 0:        
            self.comboBox_action.clear()
            for i in range(0, len(actList)):
                self.comboBox_action.addItem(actList[i])
        else:
            self.comboBox_action.clear()

    def refresh_action_coord(self):
        actList = self.listActions(self.actdir,'.d6ac')
        actList.sort()
        
        if len(actList) != 0:        
            self.comboBox_action_Coord.clear()
            for i in range(0, len(actList)):
                self.comboBox_action_Coord.addItem(actList[i])
        else:
            self.comboBox_action_Coord.clear()


    # 控制动作组按钮点击事件
    def button_controlaction_clicked(self, name):
        if name == 'delectSingle':
            if str(self.comboBox_action.currentText()) != "":
                os.remove(self.actdir + str(self.comboBox_action.currentText()) + ".d6a")            
                self.refresh_action()
        if name == 'allDelect':
            # result = self.message_delect('此操作会删除所有动作组，是否继续？')
            result = self.message_delect(language['MessageBox']['allDelect'][self.language])
            
            if result == 0:                              
                actList = self.listActions(self.actdir)
                for d in actList:
                    os.remove(self.actdir + d + '.d6a')
            else:
                pass
            self.refresh_action()
        if name == 'runAction':   # 动作组运行
            runActionGroup(self.comboBox_action.currentText() + '.d6a')            
        if name == 'stopAction':   # 停止运行
            stopActionGroup()
        if name == 'refresh':
            self.refresh_action()
        if name == 'quit':
            self.camera_ui = True
            self.camera_ui_break = True
            try:
                self.cap.release()
            except:
                pass
            sys.exit()
            
    def button_control_action_coord_clicked(self, name):
        if name == self.Button_DelectSingle_Coord.objectName():
            if str(self.comboBox_action_Coord.currentText()) != "":
                os.remove(self.actdir + str(self.comboBox_action_Coord.currentText()) + ".d6ac")            
                self.refresh_action_coord()
        if name == self.Button_AllDelect_Coord.objectName():
            # result = self.message_delect('此操作会删除所有动作组，是否继续？')
            result = self.message_delect(language['MessageBox']['allDelect'][self.language])
            
            if result == 0:                              
                actList = self.listActions(self.actdir,format = '.d6ac')
                for d in actList:
                    os.remove(self.actdir + d + '.d6ac')
            else:
                pass
            self.refresh_action_coord()
        if name == self.Button_RunAction_Coord.objectName():   # 动作组运行
            runActionGroup(self.comboBox_action_Coord.currentText()+'.d6ac')            
        if name == self.Button_StopAction_Coord.objectName():   # 停止运行
            stopActionGroup()
        if name == self.Button_Refresh_Coord.objectName():
            self.refresh_action_coord()
    ################################################################################################
    def horizontalSlider_valuechange(self, name):
        if name == 'servoTemp':
            self.temp = str(self.horizontalSlider_servoTemp.value())
            self.label_servoTemp.setText(self.temp + '℃')
        if name == 'servoMin':
            self.servoMin = str(self.horizontalSlider_servoMin.value())
            self.label_servoMin.setText(self.servoMin)
        if name == 'servoMax':
            self.servoMax = str(self.horizontalSlider_servoMax.value())
            self.label_servoMax.setText(self.servoMax)
        if name == 'servoMinV':
            self.servoMinV = str(self.horizontalSlider_servoMinV.value()/10)
            self.label_servoMinV.setText(self.servoMinV + 'V')
        if name == 'servoMaxV':
            self.servoMaxV = str(self.horizontalSlider_servoMaxV.value()/10)
            self.label_servoMaxV.setText(self.servoMaxV + 'V')
        if name == 'servoMove':
            self.servoMove = str(self.horizontalSlider_servoMove.value())            
            self.label_servoMove.setText(self.servoMove)
            setServoPulse(self.id, int(self.servoMove), 0)
    
    def button_clicked(self, name):
        if name == 'read':
            try:
                self.id = getBusServoID()
                if self.id is None:
                    if self.chinese:
                        self.message_From('读取id失败')
                    else:
                        self.message_From('Failed to read ID')
                    return
                self.readOrNot = True
                self.dev = getBusServoDeviation(self.id)
                if self.dev > 125:
                    self.dev = -(0xff-(self.dev - 1))
                self.servoTemp = getBusServoTempLimit(self.id)
                (self.servoMin, self.servoMax) = getBusServoAngleLimit(self.id)
                (self.servoMinV, self.servoMaxV) = getBusServoVinLimit(self.id)
                self.servoMove = getServoPulse(self.id)
                
                currentVin = getBusServoVin(self.id)

                currentTemp = getBusServoTemp(self.id)

                self.lineEdit_servoID.setText(str(self.id))
                self.lineEdit_servoDev.setText(str(self.dev))
                
                self.horizontalSlider_servoTemp.setValue(self.servoTemp)
                self.horizontalSlider_servoMin.setValue(self.servoMin)
                self.horizontalSlider_servoMax.setValue(self.servoMax)
                MinV = self.servoMinV
                MaxV = self.servoMaxV            
                self.horizontalSlider_servoMinV.setValue(int(MinV/100))
                self.horizontalSlider_servoMaxV.setValue(int(MaxV/100))

                self.label_servoCurrentP.setText(str(self.servoMove))
                self.label_servoCurrentV.setText(str(round(currentVin/1000.0, 2)) + 'V')
                self.label_servoCurrentTemp.setText(str(currentTemp) + '℃')

                self.horizontalSlider_servoMove.setValue(self.servoMove)
            except:
                if self.chinese:
                    self.message_From('读取超时')
                else:
                    self.message_From('Read timeout')
                return
            if self.chinese:
                self.message_From('读取成功')
            else:
                self.message_From('success')
            
        if name == 'set':
            if self.readOrNot is False:
                if self.chinese:
                    self.message_From('请先读取，否则无法获取舵机信息，从而进行设置！')
                else:
                    self.message_From('Read first！')
                return
            id = self.lineEdit_servoID.text()
            if id == '':
                if self.chinese:
                    self.message_From('舵机id参数为空，无法设置')
                else:
                    self.message_From('Please input id')
                return           
            dev = self.lineEdit_servoDev.text()
            if dev is '':
                dev = 0
            dev = int(dev)
            if dev > 125 or dev < -125:
                if self.chinese:
                    self.message_From('偏差参数超出可调节范围-125～125，无法设置')
                else:
                    self.message_From('Deviation out of range -125~125')
                return          
            temp = self.horizontalSlider_servoTemp.value()
            pos_min = self.horizontalSlider_servoMin.value()
            pos_max = self.horizontalSlider_servoMax.value()
            if pos_min > pos_max:
                if self.chinese:
                    self.message_From('舵机范围参数错误，无法设置')
                else:
                    self.message_From('Wrong angle range')
                return
            vin_min = self.horizontalSlider_servoMinV.value()
            vin_max = self.horizontalSlider_servoMaxV.value()
            if vin_min > vin_max:
                if self.chinese:
                    self.message_From('舵机电压范围参数错误，无法设置')
                else:
                    self.message_From('Wrong voltage range')
                return
            pos = self.horizontalSlider_servoMove.value()
            
            id = int(id)
            
            try:
                setBusServoID(self.id, id)
                time.sleep(0.01)
                if getBusServoID() != id:
                    if self.chinese:
                        self.message_From('id设置失败！')
                    else:
                        self.message_From('failed！')
                    return
                setBusServoDeviation(id, dev)
                time.sleep(0.01)
                saveServoDeviation(id)
                time.sleep(0.01)
                d = getBusServoDeviation(id)
                if d > 125:
                    d = -(0xff-(d - 1))               
                if d != dev:
                    if self.chinese:
                        self.message_From('偏差设置失败！')
                    else:
                        self.message_From('failed！')
                    return            
                setBusServoMaxTemp(id, temp)
                time.sleep(0.01)
                if getBusServoTempLimit(id) != temp:
                    if self.chinese:
                        self.message_From('温度设置失败！')
                    else:
                        self.message_From('failed！')

                    return 
                setBusServoAngleLimit(id, pos_min, pos_max)
                time.sleep(0.01)
                if getBusServoAngleLimit(id) != (pos_min, pos_max):
                    if self.chinese:
                        self.message_From('角度范围设置失败！')
                    else:
                        self.message_From('failed！')
                    return 
                setBusServoVinLimit(id, vin_min*100, vin_max*100)
                time.sleep(0.01)
                if getBusServoVinLimit(id) != (vin_min*100, vin_max*100):
                    if self.chinese:
                        self.message_From('电压范围设置失败！')
                    else:
                        self.message_From('failed！')
                    return 
                setServoPulse(id, pos, 0)
            except:
                if self.chinese:
                    self.message_From('设置超时!')
                else:
                    self.message_From('Timeout!')
                return                
            
            self.message_From('设置成功')
            
        if name == 'default':
            if self.readOrNot is False:
                if self.chinese:
                    self.message_From('请先读取，否则无法获取舵机信息，从而进行设置！')
                else:
                    self.message_From('Read first！')
                return
            try:
                setBusServoID(self.id, 1)
                time.sleep(0.01)
                if getBusServoID() != 1:
                    if self.chinese:
                        self.message_From('id设置失败！')
                    else:
                        self.message_From('failed！')
                    return
                setBusServoDeviation(1, 0)
                time.sleep(0.01)
                saveServoDeviation(1)
                time.sleep(0.01)
                if getBusServoDeviation(1) != 0:
                    if self.chinese:
                        self.message_From('偏差设置失败！')
                    else:
                        self.message_From('failed！')
                    return
                setBusServoMaxTemp(1, 85)
                time.sleep(0.01)
                if getBusServoTempLimit(1) != 85:
                    if self.chinese:
                        self.message_From('温度设置失败！')
                    else:
                        self.message_From('failed！')
                    return
                setBusServoAngleLimit(1, 0, 1000)
                time.sleep(0.01)
                if getBusServoAngleLimit(1) != (0, 1000):
                    if self.chinese:
                        self.message_From('角度范围设置失败！')
                    else:
                        self.message_From('failed！')
                    return          
                setBusServoVinLimit(1, 4500, 12000)
                time.sleep(0.01)
                if getBusServoVinLimit(1) != (4500, 12000):
                    if self.chinese:
                        self.message_From('电压范围设置失败！')
                    else:
                        self.message_From('failed！')
                    return             
                setServoPulse(1, SERVO_MIDDLE_VALUE, 0)
            except:
                if self.chinese:
                    self.message_From('设置超时!')
                else:
                    self.message_From('Timeout!')
                return
            if self.chinese:
                self.message_From('设置成功')
            else:
                self.message_From('success')
        if name == 'quit2':
            self.camera_ui = True
            self.camera_ui_break = True
            try:
                self.cap.release()
            except:
                pass          
            sys.exit()
        if name == 'resetPos':
            self.horizontalSlider_servoMove.setValue(SERVO_MIDDLE_VALUE)
            setServoPulse(self.id, SERVO_MIDDLE_VALUE, 0)
    def PanelLanguage(self, lang):
        _translate = QCoreApplication.translate

        self.label_action.setText(_translate("Form", language['label_action'][lang]))
        self.Button_DelectSingle.setText(_translate("Form", language['Button_DelectSingle'][lang]))
        self.Button_AllDelect.setText(_translate("Form", language['Button_AllDelect'][lang]))
        self.Button_RunAction.setText(_translate("Form", language['Button_RunAction'][lang]))
        self.Button_StopAction.setText(_translate("Form", language['Button_StopAction'][lang]))
        self.Button_Quit.setText(_translate("Form", language['Button_Quit'][lang]))
        self.Button_Refresh.setText(_translate("Form", language['Button_Refresh'][lang]))
        self.checkBox.setText(_translate("Form", language['checkBox'][lang]))
        self.Button_Run.setText(_translate("Form", language['Button_Run'][lang]))
        self.Button_DownloadDeviation.setText(_translate("Form", language['Button_DownloadDeviation'][lang]))
        self.Button_ReSetServos.setText(_translate("Form", language['Button_ReSetServos'][lang]))
        self.Button_ServoPowerDown.setText(_translate("Form", language['Button_ServoPowerDown'][lang]))
        self.tableWidget.horizontalHeaderItem(1).setText(_translate("Form", language['tableWidget.horizontalHeaderItem(1)'][lang]))
        self.tableWidget.horizontalHeaderItem(2).setText(_translate("Form", language['tableWidget.horizontalHeaderItem(2)'][lang]))
        # print(self.tableWidget.horizontalHeaderItem(1).)
        # item = self.tableWidget.horizontalHeaderItem(3)
        # item.setText(_translate("Form", "ID:1"))
        # item = self.tableWidget.horizontalHeaderItem(4)
        # item.setText(_translate("Form", "ID:2"))
        # item = self.tableWidget.horizontalHeaderItem(5)
        # item.setText(_translate("Form", "ID:3"))
        # item = self.tableWidget.horizontalHeaderItem(6)
        # item.setText(_translate("Form", "ID:4"))
        # item = self.tableWidget.horizontalHeaderItem(7)
        # item.setText(_translate("Form", "ID:5"))
        # item = self.tableWidget.horizontalHeaderItem(8)
        # item.setText(_translate("Form", "ID:6"))
        # item = self.tableWidget.horizontalHeaderItem(9)
        # item.setText(_translate("Form", "ID:7"))
        # item = self.tableWidget.horizontalHeaderItem(10)
        # item.setText(_translate("Form", "ID:8"))
        self.Button_OpenActionGroup.setText(_translate("Form", language['Button_OpenActionGroup'][lang]))
        self.Button_SaveActionGroup.setText(_translate("Form", language['Button_SaveActionGroup'][lang]))
        self.Button_TandemActionGroup.setText(_translate("Form", language['Button_TandemActionGroup'][lang]))
        self.label_time.setText(_translate("Form", language['label_time'][lang]))
        # self.lineEdit_time.setText(_translate("Form", "1000"))
        self.Button_AddAction.setText(_translate("Form", language['Button_AddAction'][lang]))
        self.Button_DelectAction.setText(_translate("Form", language['Button_DelectAction'][lang]))
        self.Button_UpdateAction.setText(_translate("Form", language['Button_UpdateAction'][lang]))
        self.Button_InsertAction.setText(_translate("Form", language['Button_InsertAction'][lang]))
        self.Button_MoveUpAction.setText(_translate("Form", language['Button_MoveUpAction'][lang]))
        self.Button_MoveDownAction.setText(_translate("Form", language['Button_MoveDownAction'][lang]))
        self.label_time_2.setText(_translate("Form", language['label_time_2'][lang]))
        # self.label.setText(_translate("Form", "ms"))
        # self.label_5.setText(_translate("Form", "s"))
        # self.label_TotalTime.setText(_translate("Form", "0"))
        self.Button_DelectAllAction.setText(_translate("Form", language['Button_DelectAllAction'][lang]))
        # self.Button_AngularReadback.setText(_translate("Form", "角度回读"))
        # self.label_ID1.setText(_translate("Form", "ID:1"))
        # self.lineEdit_servo1.setText(_translate("Form", "1500"))
        # self.label_d1.setText(_translate("Form", "0"))
        self.label_servoL_1.setText(_translate("Form", language['label_servoL_1'][lang]))
        self.label_servoR_1.setText(_translate("Form", language['label_servoR_1'][lang]))
        # self.label_ID5.setText(_translate("Form", "ID:5"))
        # self.lineEdit_servo5.setText(_translate("Form", "1500"))
        # self.label_d5.setText(_translate("Form", "0"))
        self.label_servoL_5.setText(_translate("Form", language['label_servoL_5'][lang]))
        self.label_servoR_5.setText(_translate("Form", language['label_servoR_5'][lang]))
        # self.label_ID6.setText(_translate("Form", "ID:6"))
        # self.lineEdit_servo6.setText(_translate("Form", "1500"))
        # self.label_d6.setText(_translate("Form", "0"))
        self.label_servoR_6.setText(_translate("Form", language['label_servoR_6'][lang]))
        self.label_servoL_6.setText(_translate("Form", language['label_servoL_6'][lang]))
        self.radioButton_zn.setText(_translate("Form", "中文"))
        self.radioButton_en.setText(_translate("Form", "English"))
        # self.label_ID2.setText(_translate("Form", "ID:2"))
        # self.lineEdit_servo2.setText(_translate("Form", "1500"))
        self.label_servoL_2.setText(_translate("Form", language['label_servoL_2'][lang]))
        # self.label_d2.setText(_translate("Form", "0"))
        self.label_servoR_2.setText(_translate("Form", language['label_servoR_2'][lang]))
        # self.label_ID1_2.setText(_translate("Form", "ID:7"))
        # self.lineEdit_servo7.setText(_translate("Form", "1500"))
        # self.label_d7.setText(_translate("Form", "0"))
        self.label_servoL_7.setText(_translate("Form", language['label_servoL_7'][lang]))
        self.label_servoR_7.setText(_translate("Form", language['label_servoR_7'][lang]))
        # self.label_ID3.setText(_translate("Form", "ID:3"))
        # self.lineEdit_servo3.setText(_translate("Form", "1500"))
        self.label_servoR_3.setText(_translate("Form", language['label_servoR_3'][lang]))
        # self.label_d3.setText(_translate("Form", "0"))
        self.label_servoL_3.setText(_translate("Form", language['label_servoL_3'][lang]))
        # self.label_ID4.setText(_translate("Form", "ID:4"))
        # self.lineEdit_servo4.setText(_translate("Form", "1500"))
        self.label_servoR_4.setText(_translate("Form", language['label_servoR_4'][lang]))
        # self.label_d4.setText(_translate("Form", "0"))
        self.label_servoL_4.setText(_translate("Form", language['label_servoL_4'][lang]))
        # self.label_ID1_3.setText(_translate("Form", "ID:8"))
        # self.lineEdit_servo8.setText(_translate("Form", "1500"))
        # self.label_d8.setText(_translate("Form", "0"))
        self.label_servoL_8.setText(_translate("Form", language['label_servoL_8'][lang]))
        self.label_servoR_8.setText(_translate("Form", language['label_servoR_8'][lang]))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _translate("Form", language['tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1)'][lang]))
        item = self.tableWidget_Coord.horizontalHeaderItem(1).setText(_translate("Form", language['tableWidget_Coord.horizontalHeaderItem(1)'][lang]))
        # item.setText(_translate("Form", "编号"))
        item = self.tableWidget_Coord.horizontalHeaderItem(2).setText(_translate("Form", language['tableWidget_Coord.horizontalHeaderItem(2)'][lang]))
        # item.setText(_translate("Form", "时间"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(3)
        # item.setText(_translate("Form", "FR-X"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(4)
        # item.setText(_translate("Form", "FR-Y"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(5)
        # item.setText(_translate("Form", "FR-Z"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(6)
        # item.setText(_translate("Form", "FL-X"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(7)
        # item.setText(_translate("Form", "FL-Y"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(8)
        # item.setText(_translate("Form", "FL-Z"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(9)
        # item.setText(_translate("Form", "BR-X"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(10)
        # item.setText(_translate("Form", "BR-Y"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(11)
        # item.setText(_translate("Form", "BR-Z"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(12)
        # item.setText(_translate("Form", "BL-X"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(13)
        # item.setText(_translate("Form", "BL-Y"))
        # item = self.tableWidget_Coord.horizontalHeaderItem(14)
        # item.setText(_translate("Form", "BL-Z"))
        self.checkBox_run_Coord_cycle.setText(_translate("Form", language['checkBox_run_Coord_cycle'][lang]))
        self.Button_Run_Coord.setText(_translate("Form", language['Button_Run_Coord'][lang]))
        self.Button_Reset_Coord.setText(_translate("Form", language['Button_Reset_Coord'][lang]))
        self.label_time_4.setText(_translate("Form", language['label_time_4'][lang]))
        self.Button_AddCoord.setText(_translate("Form", language['Button_AddCoord'][lang]))
        self.Button_DelectCoord.setText(_translate("Form", language['Button_DelectCoord'][lang]))
        self.Button_UpdateCoord.setText(_translate("Form", language['Button_UpdateCoord'][lang]))
        self.Button_MoveUpCoord.setText(_translate("Form", language['Button_MoveUpCoord'][lang]))
        self.Button_MoveDownCoord.setText(_translate("Form", language['Button_MoveDownCoord'][lang]))
        # self.label_41.setText(_translate("Form", "ms"))
        self.Button_DelectAllCoord.setText(_translate("Form", language['Button_DelectAllCoord'][lang]))
        self.label_time_3.setText(_translate("Form", language['label_time_3'][lang]))
        # self.label_TotalTime_coord.setText(_translate("Form", "0"))
        # self.label_40.setText(_translate("Form", "s"))
        self.Button_InsertCoord.setText(_translate("Form", language['Button_InsertCoord'][lang]))
        self.Button_OpenActionGroup_Coord.setText(_translate("Form", language['Button_OpenActionGroup_Coord'][lang]))
        self.Button_SaveActionGroup_Coord.setText(_translate("Form", language['Button_SaveActionGroup_Coord'][lang]))
        self.Button_TandemActionGroup_Coord.setText(_translate("Form", language['Button_TandemActionGroup_Coord'][lang]))
        self.label_action_2.setText(_translate("Form", language['label_action_2'][lang]))
        self.Button_DelectSingle_Coord.setText(_translate("Form", language['Button_DelectSingle_Coord'][lang]))
        self.Button_AllDelect_Coord.setText(_translate("Form", language['Button_AllDelect_Coord'][lang]))
        self.Button_RunAction_Coord.setText(_translate("Form", language['Button_RunAction_Coord'][lang]))
        self.Button_StopAction_Coord.setText(_translate("Form", language['Button_StopAction_Coord'][lang]))
        self.Button_Refresh_Coord.setText(_translate("Form", language['Button_Refresh_Coord'][lang]))
        self.pushButton_quit2.setText(_translate("Form", language['pushButton_quit2'][lang]))
        # self.label_42.setText(_translate("Form", "<html><head/><body><p>X</p><p>Y</p><p>Z</p></body></html>"))
        # self.label_43.setText(_translate("Form", "<html><head/><body><p>X</p><p>Y</p><p>Z</p></body></html>"))
        # self.label_44.setText(_translate("Form", "<html><head/><body><p>X</p><p>Y</p><p>Z</p></body></html>"))
        # self.label_45.setText(_translate("Form", "<html><head/><body><p>X</p><p>Y</p><p>Z</p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Form", language['tabWidget.setTabText(self.tabWidget.indexOf(self.tab)'][lang]))
        # self.pushButton_read.setText(_translate("Form", "读取"))
        # self.pushButton_set.setText(_translate("Form", "设置"))
        # self.pushButton_default.setText(_translate("Form", "默认"))
        # self.label_17.setText(_translate("Form", "角度范围"))
        # self.label_servoMin.setText(_translate("Form", "0"))
        # self.label_servoMax.setText(_translate("Form", "1000"))
        # self.label_19.setText(_translate("Form", "电压范围"))
        # self.label_servoMinV.setText(_translate("Form", "4.5V"))
        # self.label_servoMaxV.setText(_translate("Form", "12V"))
        # self.label_20.setText(_translate("Form", "温度范围"))
        # self.label_servoTemp.setText(_translate("Form", "85℃"))
        # self.label_21.setText(_translate("Form", "当前角度："))
        # self.label_22.setText(_translate("Form", "当前温度："))
        # self.label_23.setText(_translate("Form", "当前电压："))
        # self.label_11.setText(_translate("Form", "舵机ID"))
        # self.lineEdit_servoID.setText(_translate("Form", "1"))
        # self.label_32.setText(_translate("Form", "ID"))
        # self.label_14.setText(_translate("Form", "舵机偏差"))
        # self.label_24.setText(_translate("Form", "-125~125"))
        # self.label_34.setText(_translate("Form", "舵机调试"))
        # self.label_servoMove.setText(_translate("Form", "500"))
        # self.pushButton_resetPos.setText(_translate("Form", "中位"))
        # self.label_36.setText(_translate("Form", "<html><head/><body><p><span style=\" color:#ff0000;\">注意：使用下面的功能时，请确保控制器只连接了一个舵机，否则会引起冲突!</span></p></body></html>"))
        # self.pushButton_quit3.setText(_translate("Form", "退出"))
        # self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Form", "舵机调试工具"))



if __name__ == "__main__":  
    app = QtWidgets.QApplication(sys.argv)
    myshow = MainWindow()
    myshow.show()
    sys.exit(app.exec_())