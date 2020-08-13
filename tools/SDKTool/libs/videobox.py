# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from cv2 import *
from libs.canvas import *

class CustomSlider(QSlider):
    costomSliderClicked = pyqtSignal()
    
    def __init__(self, parent = None):
        super(CustomSlider, self).__init__(parent)
        
        
        
    def mousePressEvent(self, QMouseEvent):
        super(CustomSlider, self).mousePressEvent(QMouseEvent)
        pos = QMouseEvent.pos().x() / self.width()
        self.setValue(pos * (self.maximum() - self.minimum() + self.minimum()))
        self.costomSliderClicked.emit()
    

class VideoBox():

    VIDEO_TYPE_OFFLINE = 0
    VIDEO_TYPE_REAL_TIME = 1

    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    video_url = ""

    def __init__(self, canvas=None, ui=None):
        self.canvas = canvas
        self.ui = ui
        self.frameCount = 0
        self.videoTime = 0.
        self.preslidervalue = 0
        self.isChangeSlider = False

        self.ui.pushButton_videostart.setEnabled(False)
        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        self.ui.pushButton_videostart.clicked.connect(self.switch_video)
        self.ui.pushButton_videoleft.setEnabled(False)
        self.ui.pushButton_videoleft.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.ui.pushButton_videoleft.clicked.connect(self.backwardframe)
        self.ui.pushButton_videoright.setEnabled(False)
        self.ui.pushButton_videoright.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.ui.pushButton_videoright.clicked.connect(self.show_video_images)

        self.ui.horizontalSlider.costomSliderClicked.connect(self.slider_changed)
        self.ui.horizontalSlider.sliderMoved.connect(self.slider_changed)
        
        # timer 设置
        self.playCapture = VideoCapture()
        self.timer = VideoTimer()
        self.timer.timeSignal.signal[str].connect(self.show_video_images)
        
    def change_slider(self):
        framepos = self.playCapture.get(CAP_PROP_POS_FRAMES)
        slidervalue = int(framepos * 1000 / self.frameCount)
        time = int(self.playCapture.get(CAP_PROP_POS_MSEC) / 1000)
        self.ui.label.setText(self.ms2text(time))
        if slidervalue != self.preslidervalue:
            self.ui.horizontalSlider.setValue(slidervalue)
            self.preslidervalue = slidervalue
        
    def slider_changed(self):
        value = self.ui.horizontalSlider.value()
        time = value * self.videoTime / 1000
        # if self.preslidervalue > value:
        #     framePos = (value + 1) * self.frameCount / 1000
        print(self.playCapture.get(CAP_PROP_POS_MSEC))
        print(time)
        
        self.playCapture.set(CAP_PROP_POS_MSEC, time * 1000)
        
    def ms2text(self, s):
        second = int(s % 60)
        if second < 10:
            textSecond = "0" + str(second)
        else:
            textSecond = str(second)
        value = int(s / 60)
        minute = int(value % 60)
        if minute < 10:
            textMinute = "0" + str(minute)
        else:
            textMinute = str(minute)
        hour = int(value / 60)
        if hour < 10:
            textHour = "0" + str(hour)
        else:
            textHour = str(hour)
        
        text = str(textHour) + " : " + str(textMinute) + " : " + str(textSecond)
        return text

    def reset(self):
        self.timer.stop()
        self.playCapture.release()
        self.status = VideoBox.STATUS_INIT
        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))

    def set_timer_fps(self):
        self.playCapture.open(self.video_url)
        fps = self.playCapture.get(CAP_PROP_FPS)
        self.timer.set_fps(fps)
        self.playCapture.release()

    def set_video(self, url=None, video_type=VIDEO_TYPE_OFFLINE, auto_play=False):
        if url is None:
            return
        self.reset()
        self.video_url = url
        self.video_type = video_type
        self.auto_play = auto_play
        self.set_timer_fps()
        if self.auto_play:
            self.switch_video()

    def play(self):
        if self.video_url == "" or self.video_url is None:
            return
        if not self.playCapture.isOpened():
            self.playCapture.open(self.video_url)
        self.timer.start()
        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))
        self.status = VideoBox.STATUS_PLAYING
        
    def backwardframe(self):
        if self.playCapture.isOpened():
            framePos = self.playCapture.get(CAP_PROP_POS_FRAMES)
            if framePos == 0:
                return
            self.playCapture.set(CAP_PROP_POS_FRAMES, framePos - 1)
            success, frame = self.playCapture.retrieve()
            if success:
                height, width = frame.shape[:2]
                if frame.ndim == 3:
                    rgb = cvtColor(frame, COLOR_BGR2RGB)
                elif frame.ndim == 2:
                    rgb = cvtColor(frame, COLOR_GRAY2BGR)

                temp_image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
                temp_pixmap = QPixmap.fromImage(temp_image)
                self.ui.mainWindow.image = temp_image
                self.ui.mainWindow.canvas.loadPixmap(temp_pixmap)
                self.ui.mainWindow.canvas.setEnabled(True)
                self.ui.mainWindow.adjustScale(initial=True)
                self.ui.mainWindow.paintCanvas()

                self.change_slider()
            else:
                print("read failed, no frame data")
                success, frame = self.playCapture.read()
                if not success and self.video_type is VideoBox.VIDEO_TYPE_OFFLINE:
                    print("play finished")  # 判断本地文件播放完毕
                    self.reset()
                    self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaStop))
                return
        else:
            print("open file or capturing device error, init again")
            self.reset()
            
            

    def stop(self):
        if self.video_url == "" or self.video_url is None:
            return
        if self.playCapture.isOpened():
            self.timer.stop()
            if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
                self.playCapture.release()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        self.status = VideoBox.STATUS_PAUSE

    def re_play(self):
        if self.video_url == "" or self.video_url is None:
            return
        self.playCapture.release()
        self.playCapture.open(self.video_url)
        self.timer.start()
        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))
        self.status = VideoBox.STATUS_PLAYING

    def show_video_images(self):
        if self.playCapture.isOpened():
            success, frame = self.playCapture.read()
            if success:
                height, width = frame.shape[:2]
                if frame.ndim == 3:
                    rgb = cvtColor(frame, COLOR_BGR2RGB)
                elif frame.ndim == 2:
                    rgb = cvtColor(frame, COLOR_GRAY2BGR)

                temp_image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
                temp_pixmap = QPixmap.fromImage(temp_image)
                self.ui.mainWindow.image = temp_image
                self.ui.mainWindow.canvas.loadPixmap(temp_pixmap)
                self.ui.mainWindow.canvas.setEnabled(True)
                self.ui.mainWindow.adjustScale(initial=True)
                self.ui.mainWindow.paintCanvas()
                
                self.change_slider()
            else:
                print("read failed, no frame data")
                success, frame = self.playCapture.read()
                if not success and self.video_type is VideoBox.VIDEO_TYPE_OFFLINE:
                    print("play finished")  # 判断本地文件播放完毕
                    self.reset()
                    self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaStop))
                return
        else:
            print("open file or capturing device error, init again")
            self.reset()

    def switch_video(self):
        if self.video_url == "" or self.video_url is None:
            return
        if self.status is VideoBox.STATUS_INIT:
            self.playCapture.open(self.video_url)
            self.frameCount = self.playCapture.get(CAP_PROP_FRAME_COUNT)
            self.videoTime = self.frameCount / self.playCapture.get(CAP_PROP_FPS)
            self.preslidervalue = 0
            self.timer.start()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))
        elif self.status is VideoBox.STATUS_PLAYING:
            self.timer.stop()
            if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
                self.playCapture.release()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.status is VideoBox.STATUS_PAUSE:
            if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
                self.playCapture.open(self.video_url)
            self.timer.start()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))

        self.status = (VideoBox.STATUS_PLAYING,
                       VideoBox.STATUS_PAUSE,
                       VideoBox.STATUS_PLAYING)[self.status]


class Communicate(QObject):

    signal = pyqtSignal(str)


class VideoTimer(QThread):

    def __init__(self, frequent=50):
        QThread.__init__(self)
        self.stopped = False
        self.frequent = frequent
        self.timeSignal = Communicate()
        self.mutex = QMutex()

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
        while True:
            if self.stopped:
                return
            self.timeSignal.signal.emit("1")
            time.sleep(1 / self.frequent)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, fps):
        self.frequent = fps