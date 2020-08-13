# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import configparser
import subprocess
import signal
from cv2 import *
from abc import ABCMeta, abstractmethod
from libs.WrappedDeviceAPI.WrappedDeviceAPI import *
from libs.canvas import *

platform = sys.platform
cfgPath = "cfg/SDKTool.ini"
TBUS_PATH = "cfg/bus.ini"

# 调试的基类，实现大部分调试的功能，通过定义几个虚函数给子类来实现模块的扩展
class AbstractDebug(object):
    __metaclass__ = ABCMeta

    VIDEO_TYPE_OFFLINE = 0       # 在线视频
    VIDEO_TYPE_REAL_TIME = 1     # 离线示频

    # 播放的三个状态
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
        self.gameRegChild = None
        self.logger = logging.getLogger("sdktool")

        '''创建左，右，暂停三个按钮，并连接对应的槽函数'''
        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        self.ui.pushButton_videostart.clicked.connect(self._switch_video)
        self.ui.pushButton_videoleft.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.ui.pushButton_videoleft.clicked.connect(self._backward_frame)
        self.ui.pushButton_videoright.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.ui.pushButton_videoright.clicked.connect(self._next_frame)
        self.set_enabled(False)

        self.ui.horizontalSlider.costomSliderClicked.connect(self._slider_changed)
        self.ui.horizontalSlider.sliderMoved.connect(self._slider_changed)

        self.status = AbstractDebug.STATUS_INIT

        '''timer 设置'''
        self.playCapture = VideoCapture()
        self.timer = ToolTimer()
        self.timer.timeSignal.signal[str].connect(self._next_frame)
        self.timer.timeSignal.signal[str].connect(self._show_result)
        self.config = configparser.ConfigParser()
        self.config.read(cfgPath)
        self.testPath = self.config.get("configure", "Path")
        self.testPrograme = self.testPath

        '''
            读取配置文件，判断是手机输送图片还是视频读取图片
            如果使用公共组建获取图片，则还需要解析公共组建的配置文件
        '''
        self.mode = self.config.get("debug", "mode")
        if self.mode == "video":
            video_url = self.config.get("configure", "videoPath")
            self._set_video(url=video_url, video_type=AbstractDebug.VIDEO_TYPE_OFFLINE, auto_play=False)
        if self.mode == "phone":
            self.phoneTool = self.config.get("phone", "common_tool")
            if self.phoneTool == '0':
                self.phoneInstance = IDeviceAPI('Android')
            elif self.phoneTool == '1':
                self.phoneInstance = IDeviceAPI('Android', 'PlatformWeTest')
            else:
                self.logger.error("wrong common tool type: {}".format(self.phoneTool))
                return

            logPath = self.config.get("phone", "log_path")
            serial = self.config.get("phone", "serial")
            if serial == "":
                serial = None
            logLevel = self._parse_loglevel(self.config.get("phone", "log_level"))
            isPortrait = self.config.get("phone", "is_portrait") == 'True'
            longEdge = int(self.config.get("phone", "long_edge"))

            ret, strError = self.phoneInstance.Initialize(deviceSerial=serial, isPortrait=isPortrait,
                                                          long_edge=longEdge,
                                                          logDir=logPath, level=logLevel, showRawScreen=False)
            if ret is False:
                self.logger.error("device tool init failed: {}".format(strError))
                return
        self.__imageList = []
        self.__imageIndex = 0
        if self.mode == "image":
            self._readImageConf()

    def _readImageConf(self):
        fps = self.config.get("configure", "fps")
        if fps is None:
            fps = 5
        else:
            fps = float(fps)

        self.logger.info("fps is {}".format(fps))
        self.timer.set_fps(fps)
        imgPath = self.config.get("configure", "imagePath")
        if os.path.isdir(imgPath):
            for root, dirs, files in os.walk(imgPath):
                for file in files:
                    if os.path.splitext(file)[1] in [".png", ".bmp", ".jpg", ".jpeg"]:
                        path = os.path.join(root, file)
                        if path not in self.__imageList:
                            self.__imageList.append(path)
        elif os.path.isfile(imgPath):
            self.__imageList.append(imgPath)
        else:
            self.logger.error("{} is not a file or dir", imgPath)

    @abstractmethod
    def initialize(self):
        '''初始化函数，可重写它来执行一些最开始的必要的逻辑'''
        raise NotImplementedError()

    @abstractmethod
    def send_frame(self, frame=None):
        '''发送帧消息，包括但不限于图像，因此需要各个模块自己实现自己的发送消息逻辑'''
        raise NotImplementedError()

    @abstractmethod
    def recv_result(self):
        '''接受返回的结果，需要各个模块自己实现'''
        raise NotImplementedError()

    def _parse_loglevel(self, logLevel):
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
            self.logger.error('log level is not correct, using info level')
            return LOG_INFO

    def _show_result(self):
        '''展示图像结果，与timer绑定，定时刷新'''
        frame = self.recv_result()
        if frame is None:
            self.logger.debug("frame is None")
            return

        height, width = frame.shape[:2]
        if frame.ndim == 3:
            rgb = cvtColor(frame, COLOR_BGR2RGB)
        elif frame.ndim == 2:
            rgb = cvtColor(frame, COLOR_GRAY2BGR)
        if rgb is None:
            return

        temp_image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
        temp_pixmap = QPixmap.fromImage(temp_image)
        self.ui.mainWindow.image = temp_image
        self.ui.mainWindow.canvas.loadPixmap(temp_pixmap)
        self.ui.mainWindow.canvas.mouseFlag = False
        self.ui.mainWindow.canvas.setEnabled(True)
        self.ui.mainWindow.adjustScale(initial=True)
        self.ui.mainWindow.paintCanvas()

        self._change_slider()

    def start_test(self):
        '''开始测试，与测试按钮绑定，点击测试按钮则执行此函数'''
        currentPath = os.getcwd()
        os.chdir(self.testPath)
        if platform == 'win32':
            self.gameRegChild = subprocess.Popen(self.testPrograme, shell=False)
        else:
            os.system('ipcs | awk \'{if($6==0) printf "ipcrm shm %d\n",$2}\'| sh')
            self.gameRegChild = subprocess.Popen(self.testPrograme, shell=True, preexec_fn=os.setsid)
        os.chdir(currentPath)

        time.sleep(1)
        self.initialize()   # 每次点击测试按钮时，都要执行各个初始化模块的逻辑
        self.set_enabled(True)

    def finish(self):
        self.stop_test()
        if self.mode == "phone" and self.phoneInstance is not None:
            self.phoneInstance.DeInitialize()

    def stop_test(self):
        '''停止测试'''
        if self.gameRegChild is None:
            return

        self._stop()
        if platform == 'win32':
            cmd = 'taskkill.exe /pid {} /f'.format(str(self.gameRegChild.pid))
            os.popen(cmd)
        else:
            os.killpg(self.gameRegChild.pid, signal.SIGUSR1)
        self.set_enabled(False)

    def _stop(self):
        '''关闭视频，回收资源'''
        self.frameSeq = 1
        # if self.video_url == "" or self.video_url is None:
        #     return
        if self.playCapture.isOpened():
            if self.video_type is AbstractDebug.VIDEO_TYPE_REAL_TIME:
                self.playCapture.release()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        self.status = AbstractDebug.STATUS_PAUSE
        self.timer.stop()
        self.__imageIndex = 0

    def _switch_video(self):
        '''与暂停/开始按钮绑定，点击按钮则切换状态'''
        # if self.video_url == "" or self.video_url is None:
        #     return

        if self.status is AbstractDebug.STATUS_INIT:
            if self.mode == "video":
                self.playCapture.open(self.video_url)
                self.frameCount = self.playCapture.get(CAP_PROP_FRAME_COUNT)
                if self.playCapture.get(CAP_PROP_FPS) == 0:
                    logger.error("open video {} failed, get CAP_PROP_FPS failed", self.video_url)
                    return

                self.videoTime = self.frameCount / self.playCapture.get(CAP_PROP_FPS)
                self.preslidervalue = 0
            self.timer.start()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))
        elif self.status is AbstractDebug.STATUS_PLAYING:
            self.timer.stop()
            if self.mode == "video":
                if self.video_type is AbstractDebug.VIDEO_TYPE_REAL_TIME:
                    self.playCapture.release()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.status is AbstractDebug.STATUS_PAUSE:
            if self.mode == "video":
                if self.video_type is AbstractDebug.VIDEO_TYPE_REAL_TIME:
                    self.playCapture.open(self.video_url)
            self.timer.start()
            self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))

        self.status = (AbstractDebug.STATUS_PLAYING,
                       AbstractDebug.STATUS_PAUSE,
                       AbstractDebug.STATUS_PLAYING)[self.status]

    def _set_video(self, url=None, video_type=VIDEO_TYPE_OFFLINE, auto_play=False):
        '''设置视频'''
        if url is None:
            return
        self._reset()
        self.video_url = url
        self.video_type = video_type
        self.auto_play = auto_play
        self._set_timer_fps()
        if self.auto_play:
            self._switch_video()

    def _set_timer_fps(self):
        '''设置帧率'''
        self.playCapture.open(self.video_url)
        fps = self.playCapture.get(CAP_PROP_FPS)
        self.timer.set_fps(fps)
        self.playCapture.release()

    def _reset(self):
        '''视频播放完后释放资源'''
        self.timer.stop()
        self.playCapture.release()
        self.status = AbstractDebug.STATUS_INIT
        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        self.__imageIndex = 0

    def set_enabled(self, flag):
        '''将按钮状态设为enable'''
        self.ui.pushButton_videostart.setEnabled(flag)
        self.ui.pushButton_videoleft.setEnabled(flag)
        self.ui.pushButton_videoright.setEnabled(flag)
        self.ui.horizontalSlider.setEnabled(flag)
        self.ui.label.setEnabled(flag)

    def _ms2text(self, s):
        '''毫秒转换为时间显示，比如04:13:32'''
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

    def _change_slider(self):
        '''拖动进度条时执行此函数，修改视频当前的播放进度'''
        if self.mode != "video":
            return

        framepos = self.playCapture.get(CAP_PROP_POS_FRAMES)
        slidervalue = int(framepos * 1000 / self.frameCount)
        time = int(self.playCapture.get(CAP_PROP_POS_MSEC) / 1000)
        self.ui.label.setText(self._ms2text(time))
        if slidervalue != self.preslidervalue:
            self.ui.horizontalSlider.setValue(slidervalue)
            self.preslidervalue = slidervalue

    def _slider_changed(self):
        '''当视频播放进度改变时，修改相应的进度条'''
        if self.mode != "video":
            return

        value = self.ui.horizontalSlider.value()
        time = value * self.videoTime / 1000
        self.playCapture.set(CAP_PROP_POS_MSEC, time * 1000)

    def _backward_frame(self):
        '''快退，回退一帧，与快退按钮绑定'''
        if self.mode != "video":
            return

        if self.playCapture.isOpened():
            framePos = self.playCapture.get(CAP_PROP_POS_FRAMES)
            if framePos == 0:
                return
            self.playCapture.set(CAP_PROP_POS_FRAMES, framePos - 1)
            success, frame = self.playCapture.retrieve()
            # 执行发送帧消息的函数，将消息发送给对应的进程（当前有GameReg和UI）
            if success:
                self.send_frame(frame)
                self._show_result()
            else:
                self.logger.error("read failed, no frame data")
                success, frame = self.playCapture.read()
                if not success and self.video_type is AbstractDebug.VIDEO_TYPE_OFFLINE:
                    self.logger.error("play finished")  # 判断本地文件播放完毕
                    self._reset()
                    self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaStop))
                return
        else:
            self.logger.error("open file or capturing device error, init again")
            self._reset()

    def _next_frame(self):
        '''
            将下一帧的数据发送给对应进程，与其绑定的元素有两个：
            1： 快进按钮
            2： timer
        '''
        if self.mode == "phone":
            # 从手机获取下一帧图片
            frame, strError = self.phoneInstance.GetFrame()
            if frame is None:
                if strError != "":
                    self.logger.error("get frame failed: {}".format(strError))
                return

            self.send_frame(frame)
            self._show_result()

        elif self.mode == "video":
            # 从视频获取下一帧图片
            if self.playCapture.isOpened():
                success, frame = self.playCapture.read()
                if success:
                    self.send_frame(frame)
                    self._show_result()
                else:
                    self.logger.error("read failed, no frame data")
                    success, frame = self.playCapture.read()
                    if not success and self.video_type is AbstractDebug.VIDEO_TYPE_OFFLINE:
                        self.logger.info("play finished")  # 判断本地文件播放完毕
                        self._reset()
                        self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaStop))
                    return
            else:
                self.logger.error("open file or capturing device error, init again")
                self._reset()

        elif self.mode == "image":
            if self.__imageIndex >= len(self.__imageList):
                self.logger.error("play finished")  # 判断本地文件播放完毕
                self._reset()
                self.ui.pushButton_videostart.setIcon(self.ui.mainWindow.style().standardIcon(QStyle.SP_MediaStop))
                return

            imagePath = self.__imageList[self.__imageIndex]
            self.logger.info("read image path is {}".format(imagePath))
            self.__imageIndex += 1

            if not os.path.exists(imagePath):
                self.logger.error("file {} not exist".format(imagePath))
                return

            # frame = cv2.imread(imagePath)
            frame = cv2.imdecode(np.fromfile(imagePath, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                self.logger.error("read image {} failed".format(imagePath))
                return

            self.send_frame(frame)
            self._show_result()


# 信号的封装
class Communicate(QObject):
    signal = pyqtSignal(str)

# 定时器，通过继承QThread类来实现
class ToolTimer(QThread):

    def __init__(self, frequent=50):
        QThread.__init__(self)
        self.stopped = False
        self.frequent = frequent
        self.timeSignal = Communicate()
        self.mutex = QMutex()

    def run(self):
        '''重写QThread类的run函数，若线程启动，则会被执行'''
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