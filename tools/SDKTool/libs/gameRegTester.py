# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import configparser
import signal
import subprocess
from .WrappedDeviceAPI.WrappedDeviceAPI import *
from libs.AgentAPI.AgentAPIMgr import *
from cv2 import *
from libs.canvas import *

cfgPath = "cfg/SDKTool.ini"
TBUS_PATH = "cfg/bus.ini"

class CustomSlider(QSlider):
    costomSliderClicked = pyqtSignal()
    
    def __init__(self, parent = None):
        super(CustomSlider, self).__init__(parent)
        

    def mousePressEvent(self, QMouseEvent):
        super(CustomSlider, self).mousePressEvent(QMouseEvent)
        pos = QMouseEvent.pos().x() / self.width()
        self.setValue(pos * (self.maximum() - self.minimum() + self.minimum()))
        self.costomSliderClicked.emit()
    

class GameRegTester():

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
        self.frameSeq = 1
        self.__logger = logging.getLogger("sdktool")

        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        self.ui.pushButton_videostart.clicked.connect(self.switch_video)
        self.ui.pushButton_videoleft.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.ui.pushButton_videoleft.clicked.connect(self.backwardframe)
        self.ui.pushButton_videoright.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.ui.pushButton_videoright.clicked.connect(self.show_video_images)
        self.set_enabled(False)

        self.ui.horizontalSlider.costomSliderClicked.connect(self.slider_changed)
        self.ui.horizontalSlider.sliderMoved.connect(self.slider_changed)
        
        # timer 设置
        self.playCapture = VideoCapture()
        self.timer = VideoTimer()
        self.timer.timeSignal.signal[str].connect(self.show_video_images)
        self.timer.timeSignal.signal[str].connect(self.RecvFromGameReg)
        self.config = configparser.ConfigParser()
        self.config.read(cfgPath)

        self.gameRegPath = self.config.get("configure", "Path")
        self.debug = self.config.get("debug", "debug")
        if self.debug == "GameReg":
            self.TestPrograme = self.gameRegPath + '/GameReg'
        elif self.debug == "UI":
            self.TestPrograme = self.gameRegPath + '/UIRecognize'
        else:
            self.__logger.error("wrong mode of debug: {}".format(self.debug))
            return

        self.mode = self.config.get("debug", "mode")
        if self.mode == "phone":
            self.phoneTool = self.config.get("phone", "common_tool")
            if self.phoneTool == '0':
                self.phoneInstance = IDeviceAPI('Android')
            elif self.phoneTool == '1':
                self.phoneInstance = IDeviceAPI('Android', 'PlatformWeTest')
            else:
                self.__logger.error("wrong common tool type: {}".format(self.phoneTool))
                return

            logPath = self.config.get("phone", "log_path")
            serial = self.config.get("phone", "serial")
            if serial == "":
                serial = None
            logLevel = self.ParseLogLevel(self.config.get("phone", "log_level"))
            isPortrait = self.config.get("phone", "is_portrait") == 'True'
            longEdge = int(self.config.get("phone", "long_edge"))

            ret, strError = self.phoneInstance.Initialize(deviceSerial=serial, isPortrait=isPortrait, long_edge=longEdge,
                                                          logDir=logPath, level=logLevel, showRawScreen=False)
            if ret is False:
                self.__logger.error("device tool init failed: {}".format(strError))
                return

        video_url = self.config.get("configure", "videoPath")
        self.set_video(url=video_url, video_type=GameRegTester.VIDEO_TYPE_OFFLINE, auto_play=False)

    def ParseLogLevel(self, logLevel):
        if logLevel == "LOG_DEBUG":
            return LOG_DEBUG
        elif logLevel == "LOG_INFO":
            return LOG_INFO
        elif logLevel == "LOG_WARNING":
            return LOG_WARNING
        elif logLevel == "LOG_ERROR":
            return LOG_ERROR
        elif logLevel == "LOG_CRITICAL":
            return LOG_CRITICAL
        else:
            self.__logger.error('log level is not correct, using info level')
            return LOG_INFO
        
    def start_test(self):
        currentPath = os.getcwd()
        os.chdir(self.gameRegPath)
        self.gameRegChild = subprocess.Popen(self.TestPrograme, shell=True, preexec_fn=os.setsid)
        os.chdir(currentPath)

        self.GameRegAPI = AgentAPIMgr()
        time.sleep(1)
        env_dist = os.environ
        sdkPath = env_dist['AI_SDK_PATH']
        if sdkPath is None:
            logging.error('there is no AI_SDK_PATH')
            return

        self.GameRegAPI.Initialize(sdkPath + "/cfg/task/gameReg/task_SDKTool.json",
                                   sdkPath + "/cfg/task/gameReg/refer_SDKTool.json",
                                   selfAddr="SDKToolAddr",
                                   cfgPath=TBUS_PATH)

        if self.debug == "GameReg":
            self.GameRegAPI.SendCmd(MSG_SEND_GROUP_ID, 1)
        self.set_enabled(True)
        
    def stop_test(self):
        self.stop()
        os.killpg(self.gameRegChild.pid, signal.SIGINT)
        self.set_enabled(False)
        
    def GenerateImgDict(self, srcImg):
        srcImgDict = dict()
        srcImgDict['frameSeq'] = self.frameSeq
        self.frameSeq += 1
        srcImgDict['image'] = srcImg
        srcImgDict['width'] = srcImg.shape[1]
        srcImgDict['height'] = srcImg.shape[0]
        srcImgDict['deviceIndex'] = 1
        
        return srcImgDict
        
    def set_enabled(self, flag):
        self.ui.pushButton_videostart.setEnabled(flag)
        self.ui.pushButton_videoleft.setEnabled(flag)
        self.ui.pushButton_videoright.setEnabled(flag)
        self.ui.horizontalSlider.setEnabled(flag)
        self.ui.label.setEnabled(flag)
        
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
        self.status = GameRegTester.STATUS_INIT
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
        self.status = GameRegTester.STATUS_PLAYING
        
    def backwardframe(self):
        if self.playCapture.isOpened():
            framePos = self.playCapture.get(CAP_PROP_POS_FRAMES)
            if framePos == 0:
                return
            self.playCapture.set(CAP_PROP_POS_FRAMES, framePos - 1)
            success, frame = self.playCapture.retrieve()
            if success:
                self.send_frame(frame)
            else:
                print("read failed, no frame data")
                success, frame = self.playCapture.read()
                if not success and self.video_type is GameRegTester.VIDEO_TYPE_OFFLINE:
                    print("play finished")  # 判断本地文件播放完毕
                    self.reset()
                    self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaStop))
                return
        else:
            print("open file or capturing device error, init again")
            self.reset()
            
    def RecvFromGameReg(self):
        # pass
        if self.debug == "GameReg":
            GameResult = self.GameRegAPI.GetInfo(GAME_RESULT_INFO)
            if GameResult is None:
                return
            frame = GameResult['image']
        elif self.debug == "UI":
            UIResult = self.GameRegAPI.RecvUIResult()
            if UIResult is None:
                return
            frame = self.ProcUIResult(UIResult)
        else:
            self.__logger.error('wrong debug mode: {}'.format(self.debug))
            return

        if frame is not None:
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

    def ProcUIResult(self, UIResult):
        if UIResult is None:
            self.__logger.error('UIResult is None')
            return None

        frame = UIResult['image']
        if frame is None:
            self.__logger.error('image is None')
            return None

        UIType = UIResult['type']
        self.__logger.info('UI type: {}'.format(UIType))
        width, height = frame.shape[:2]
        if UIType == PB_UI_ACTION_CLICK:
            cv2.putText(frame, "click", (UIResult['points'][0]['x'], UIResult['points'][0]['y']), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
            cv2.circle(frame, (UIResult['points'][0]['x'], UIResult['points'][0]['y']), 8, (0, 0, 255), -1)
        elif UIType == PB_UI_ACTION_DRAG:
            cv2.putText(frame, "drag", (UIResult['points'][0]['x'], UIResult['points'][0]['y']), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
            cv2.line(frame, (UIResult['points'][0]['x'], UIResult['points'][0]['y']),
                     (UIResult['points'][1]['x'], UIResult['points'][1]['y']), (0, 0, 255), 3)

        return frame
            
    def send_frame(self, frame):
        if self.debug == "GameReg":
            srcImgDict = self.GenerateImgDict(frame)
            ret = self.GameRegAPI.SendSrcImage(srcImgDict)
            if ret is False:
                logging.error('send frame failed')
        elif self.debug == "UI":
            srcImgDict = self.GenerateImgDict(frame)
            ret = self.GameRegAPI.SendUISrcImage(srcImgDict)
            if ret is False:
                logging.error('send frame failed')

        # height, width = frame.shape[:2]
        # if frame.ndim == 3:
        #     rgb = cvtColor(frame, COLOR_BGR2RGB)
        # elif frame.ndim == 2:
        #     rgb = cvtColor(frame, COLOR_GRAY2BGR)
        #
        # temp_image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
        # temp_pixmap = QPixmap.fromImage(temp_image)
        # self.ui.mainWindow.image = temp_image
        # self.ui.mainWindow.canvas.loadPixmap(temp_pixmap)
        # self.ui.mainWindow.canvas.setEnabled(True)
        # self.ui.mainWindow.adjustScale(initial=True)
        # self.ui.mainWindow.paintCanvas()
        #
        # self.change_slider()
        
    

    def stop(self):
        self.frameSeq = 1
        if self.video_url == "" or self.video_url is None:
            return
        if self.playCapture.isOpened():
            self.timer.stop()
            if self.video_type is GameRegTester.VIDEO_TYPE_REAL_TIME:
                self.playCapture.release()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        self.status = GameRegTester.STATUS_PAUSE

    def re_play(self):
        if self.video_url == "" or self.video_url is None:
            return
        self.playCapture.release()
        self.playCapture.open(self.video_url)
        self.timer.start()
        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))
        self.status = GameRegTester.STATUS_PLAYING

    def show_video_images(self):
        if self.mode == "phone":
            frame, strError = self.phoneInstance.GetFrame()
            if frame is None:
                if strError != "":
                    self.__logger.error("get frame failed: {}".format(strError))
                return

            self.send_frame(frame)

        elif self.mode == "video":
            if self.playCapture.isOpened():
                success, frame = self.playCapture.read()
                if success:
                    self.send_frame(frame)
                else:
                    print("read failed, no frame data")
                    success, frame = self.playCapture.read()
                    if not success and self.video_type is GameRegTester.VIDEO_TYPE_OFFLINE:
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
        if self.status is GameRegTester.STATUS_INIT:
            self.playCapture.open(self.video_url)
            self.frameCount = self.playCapture.get(CAP_PROP_FRAME_COUNT)
            self.videoTime = self.frameCount / self.playCapture.get(CAP_PROP_FPS)
            self.preslidervalue = 0
            self.timer.start()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))
        elif self.status is GameRegTester.STATUS_PLAYING:
            self.timer.stop()
            if self.video_type is GameRegTester.VIDEO_TYPE_REAL_TIME:
                self.playCapture.release()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.status is GameRegTester.STATUS_PAUSE:
            if self.video_type is GameRegTester.VIDEO_TYPE_REAL_TIME:
                self.playCapture.open(self.video_url)
            self.timer.start()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))

        self.status = (GameRegTester.STATUS_PLAYING,
                       GameRegTester.STATUS_PAUSE,
                       GameRegTester.STATUS_PLAYING)[self.status]


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