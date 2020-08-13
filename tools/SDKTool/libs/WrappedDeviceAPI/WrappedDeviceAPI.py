# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import cv2
import traceback

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, __dir__)

from platformdefult.adbkit.ADBClient import ADBClient
from devicePlatform.IPlatformProxy import *
from gamedevice.AndroidGameDevice import *
from .APIDefine import *

projectdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# self.__logger = logging.getLogger('DeviceAPI')

class IDeviceAPI(object):
    def __init__(self, deviceType='Android', moduleName=None):
        if deviceType == 'Android':
            self.__device = AndroidGameDevice(moduleName)
        # elif deviceType == 'IOS':
        #     self.__device = IOSGameDevice()
        # elif deviceType == 'Windows':
        #     self.__device = WindowsGameDevice()
        # elif deviceType == 'Video':
        #     self.__device = VideoGameDevice()
        else:
            self.__device = AbstractGameDevice()

        self.__height = -1
        self.__width = -1
        self.__pid = os.getpid()
        self.__serial = '*'

    '''
        describe：初始化
        param[0],str类型：手机序列号,默认为None，当接入一个设备时可不指定序列号，当接入多个设备时需要指定
        param[1],bool类型：手机为横屏还是竖屏，True为竖屏，False为横屏
        param[2],int类型：长边的长度
        param[3],str类型：指定日志目录,默认为/tmp/LogDeviceAPI
        param[4],枚举类型：指定日志级别，取值为[LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR, LOG_CRITICAL]，默认为LOG_DEBUG
        param[5],bool类型：是否show出图片
        param[5],字典    ：一些组件需要的参数，可以自己定义，例如端口号等等
        return,bool, strError
    '''
    def Initialize(self, deviceSerial=None, isPortrait=False, long_edge=1280,
                   logDir=projectdir + '/py_log/LogDeviceAPI/', level=LOG_DEBUG, showRawScreen=False, **kwargs):
        if not self._LogInit(logDir, level, LOG_DEFAULT):
            return False

        try:
            if deviceSerial is not None:
                logDir = logDir + '/' + deviceSerial + '/'
                self.__serial = deviceSerial

                if not self._LogInit(logDir, level, deviceSerial):
                    return False, "init log failed"

            if not self.__device.Initialize(deviceSerial, isPortrait, long_edge, kwargs):
                self.__logger.error('DeviceAPI initial failed')
                return False, "DeviceAPI initial failed"
            self.__showScreen = showRawScreen
            self.__maxContact = self.__device.GetMaxContact()
            maxContact = self.__maxContact
            exec("self.__maxContact = maxContact")
            self.__height, self.__width, strError = self.__device.GetScreenResolution()
            if self.__height == -1 and self.__width == -1:
                self.__logger.error(strError)
                return False, strError

            if isPortrait:
                height = long_edge
                width = self.__width * height / self.__height
            else:
                width = long_edge
                height = self.__width * width / self.__height
            # width = self.__width
            # height = self.__height
            exec("self.__width = width")
            exec("self.__height = height")

            self.__logger.info("init successful")
            return True, ""
        except Exception as e:
            self.__logger.error(e)
            traceback.print_exc()
            return False, str(e)

    '''
        describe:回收资源
        return True or False
    '''
    def DeInitialize(self):
        return self.__device.DeInitialize()

    '''
        describe:获取当前图像帧
        return：Mat类型的图像, strError
    '''
    def GetFrame(self):
        try:
            self._CheckException()
            err, image = self.__device.GetFrame()
            if err != PP_RET_OK:
                raise Exception('get image error')
            if image is not None and self.__showScreen:
                self.__logger.info("get image")
                cv2.imshow('pid:' + str(self.__pid) + ' serial:' + str(self.__serial), image)
                cv2.waitKey(1)

            if image is None:
                self.__logger.warning('image is None')
                return None, "image is None"
            else:
                return image, str()
        except Exception as e:
            self.__logger.error(e)
            traceback.print_exc()
            self.__logger.warning('image is None')
            return None, str(e)

    '''
        ==========================================================================================================
        ============================================TouchCMD==================================================
        ==========================================================================================================

        describe:让手机执行动作
        aType参数表示动作类型[TOUCH_CLICK, TOUCH_DOWN, TOUCH_UP, TOUCH_SWIPE, TOUCH_MOVE]
        sx为x坐标，当aType为[TOUCH_CLICK, TOUCH_DOWN]时表示按压点的x坐标，当aType为[TOUCH_SWIPE, TOUCH_MOVE]时表示起始点的x坐标
        sy为y坐标，当aType为[TOUCH_CLICK, TOUCH_DOWN]时表示按压点的y坐标，当aType为[TOUCH_SWIPE, TOUCH_MOVE]时表示起始点的y坐标
        ex为x坐标，当aType为[TOUCH_SWIPE, TOUCH_MOVE]时表示结束点的x坐标
        ex为y坐标，当aType为[TOUCH_SWIPE, TOUCH_MOVE]时表示结束点的y坐标
        DaType为执行该操作的方式，有minitouch方式和ADB命令方式，分别表示为[DACT_TOUCH, DACT_ADB]，默认为DACT_TOUCH
        contact为触点，默认为0
        durationMS为执行一次动作持续的时间，在aType为[TOUCH_CLICK, TOUCH_SWIPE]时使用，当aType为TOUCH_CLICK时默认为-1，当aType为TOUCH_SWIPE时默认为50
        needUp仅在aType为TOUCH_SWIPE时使用，表示滑动后是否需要抬起，默认为True
        return:True or False
    '''
    def TouchCMD(self, **kwargs):
        try:
            self._CheckException()
            for key in kwargs.keys():
                if key not in TOUCH_KEY:
                    self.__logger.error('wrong key of kwargs: {0}'.format(key))
                    return False

            neededFlag, actionType = self._GetValuesInkwargs('aType', True, None, kwargs)
            if not neededFlag:
                self.__logger.error('aType is needed when exec TouchCommand')
                return False

            # describe:执行点击操作
            # sx为横坐标，相对于初始化时传入的坐标系
            # sy为纵坐标，相对于初始化时传入的坐标系
            # contact为触点，默认为0
            # durantionMS为动作持续时间，默认为-1
            # wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
            # return True or False
            if actionType == TOUCH_CLICK:
                neededFlag, px = self._GetValuesInkwargs('sx', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sx', actionType, px, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, py = self._GetValuesInkwargs('sy', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sy', actionType, py, int, 'var >= 0 and var < self.__height'):
                    return False
                neededFlag, contact = self._GetValuesInkwargs('contact', False, 0, kwargs)
                if not self._CheckVar(neededFlag, 'contact', actionType, contact, int, 'var >= 0 and var <= self.__maxContact'):
                    return False
                neededFlag, durationMS = self._GetValuesInkwargs('durationMS', False, -1, kwargs)
                if not self._CheckVar(neededFlag, 'durationMS', actionType, durationMS, int, 'var >= -1'):
                    return False
                neededFlag, wait_time = self._GetValuesInkwargs('wait_time', False, 0, kwargs)
                if not neededFlag or not (isinstance(wait_time, int) or isinstance(wait_time, float)) or wait_time < 0:
                    self.__logger.error("wrong wait_time when exec click, wait_time:{0}".format(wait_time))
                    return False

                self.__logger.info("platform click, x: {0}, y {1}, contact: {2}, durationMS: {3}, waitTime: {4}".format(px, py, contact, durationMS, wait_time))
                self.__device.Click(px, py, contact, durationMS, wait_time)

            # describe: 执行按压操作
            # sx为横坐标，相对于初始化时传入的坐标系
            # sy为纵坐标，相对于初始化时传入的坐标系
            # contact为触点，默认为0
            # wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
            # return True or False
            elif actionType == TOUCH_DOWN:
                neededFlag, px = self._GetValuesInkwargs('sx', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sx', actionType, px, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, py = self._GetValuesInkwargs('sy', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sy', actionType, py, int, 'var >= 0 and var < self.__height'):
                    return False
                neededFlag, contact = self._GetValuesInkwargs('contact', False, 0, kwargs)
                if not self._CheckVar(neededFlag, 'contact', actionType, contact, int, 'var >= 0 and var <= self.__maxContact'):
                    return False
                neededFlag, wait_time = self._GetValuesInkwargs('wait_time', False, 0, kwargs)
                if not neededFlag or not (isinstance(wait_time, int) or isinstance(wait_time, float)) or wait_time < 0:
                    self.__logger.error("wrong wait_time when exec down, wait_time:{0}".format(wait_time))
                    return False

                self.__logger.info("platform down, x: {0}, y {1}, contact: {2}, waitTime: {3}".format(px, py, contact, wait_time))
                self.__device.Down(px, py, contact, wait_time)

            # describe: 执行抬起操作
            # wait_time为执行动作后，手机端等待时间，单位为秒，默认为0
            # return True or False
            elif actionType == TOUCH_UP:
                neededFlag, contact = self._GetValuesInkwargs('contact', False, 0, kwargs)
                if not self._CheckVar(neededFlag, 'contact', actionType, contact, int, 'var >= 0 and var <= self.__maxContact'):
                    return False
                neededFlag, wait_time = self._GetValuesInkwargs('wait_time', False, 0, kwargs)
                if not neededFlag or not (isinstance(wait_time, int) or isinstance(wait_time, float)) or wait_time < 0:
                    self.__logger.error("wrong wait_time when exec up, wait_time:{0}".format(wait_time))
                    return False

                self.__logger.info("platform up, contact: {0}, waitTime: {1}".format(contact, wait_time))
                self.__device.Up(contact, wait_time)

            # describe: 执行滑动
            # sx, sy为起始点的坐标
            # ex, ey为终止点的坐标
            # DaType表示执行动作的实现方式，有minitouch和ADB两种[DACT_TOUCH, DACT_ADB], 默认为DACT_TOUCH
            # contact为触点，默认为0
            # durantionMS为动作持续时间，默认为50
            # needUp表示滑动后是否抬起，默认为True
            # wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
            # return True or False
            elif actionType == TOUCH_SWIPE:
                neededFlag, sx = self._GetValuesInkwargs('sx', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sx', actionType, sx, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, sy = self._GetValuesInkwargs('sy', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sy', actionType, sy, int, 'var >= 0 and var < self.__height'):
                    return False
                neededFlag, ex = self._GetValuesInkwargs('ex', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'ex', actionType, ex, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, ey = self._GetValuesInkwargs('ey', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'ey', actionType, ey, int, 'var >= 0 and var < self.__height'):
                    return False
                neededFlag, contact = self._GetValuesInkwargs('contact', False, 0, kwargs)
                if not self._CheckVar(neededFlag, 'contact', actionType, contact, int, 'var >= 0 and var <= self.__maxContact'):
                    return False
                neededFlag, durationMS = self._GetValuesInkwargs('durationMS', False, 50, kwargs)
                if not self._CheckVar(neededFlag, 'durationMS', actionType, durationMS, int, 'var >= 0'):
                    return False
                neededFlag, needUp = self._GetValuesInkwargs('needUp', False, True, kwargs)
                if not self._CheckVar(neededFlag, 'needUp', actionType, needUp, bool, 'True'):
                    return False
                neededFlag, wait_time = self._GetValuesInkwargs('wait_time', False, 0, kwargs)
                if not neededFlag or not (isinstance(wait_time, int) or isinstance(wait_time, float)) or wait_time < 0:
                    self.__logger.error("wrong wait_time when exec swipe, wait_time:{0}".format(wait_time))
                    return False

                self.__logger.info("platform swipe, sx: {0}, sy {1}, ex: {2}, ey {3}, contact: {4}, waitTime: {5}".format(sx, sy, ex, ey, contact, wait_time))
                self.__device.Swipe(sx, sy, ex, ey, contact, durationMS, needUp, wait_time)

            # describe: 执行滑动操作，与swipe不同的是他只有终止点，通过多个move可以组合成一个swipe
            # sx为横坐标，相对于初始化时传入的坐标系
            # sy为纵坐标，相对于初始化时传入的坐标系
            # contact为触点，默认为0
            # wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
            # return True or False
            elif actionType == TOUCH_MOVE:
                neededFlag, px = self._GetValuesInkwargs('sx', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sx', actionType, px, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, py = self._GetValuesInkwargs('sy', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sy', actionType, py, int, 'var >= 0 and var < self.__height'):
                    return False
                neededFlag, contact = self._GetValuesInkwargs('contact', False, 0, kwargs)
                if not self._CheckVar(neededFlag, 'contact', actionType, contact, int, 'var >= 0 and var <= self.__maxContact'):
                    return False
                neededFlag, wait_time = self._GetValuesInkwargs('wait_time', False, 0, kwargs)
                if not neededFlag or not (isinstance(wait_time, int) or isinstance(wait_time, float)) or wait_time < 0:
                    self.__logger.error("wrong wait_time when exec move, wait_time:{0}".format(wait_time))
                    return False

                self.__logger.info("platform move, px: {0}, py {1}, contact: {2}, waitTime: {3}".format(px, py, contact,wait_time))
                self.__device.Move(px, py, contact, wait_time)

            # describe: 执行滑动操作，与move不同的是它进行了补点操作
            # sx为横坐标，相对于初始化时传入的坐标系
            # sy为纵坐标，相对于初始化时传入的坐标系
            # contact为触点，默认为0
            # wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
            # return True or False
            elif actionType == TOUCH_SWIPEMOVE:
                neededFlag, px = self._GetValuesInkwargs('sx', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sx', actionType, px, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, py = self._GetValuesInkwargs('sy', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sy', actionType, py, int, 'var >= 0 and var < self.__height'):
                    return False
                neededFlag, contact = self._GetValuesInkwargs('contact', False, 0, kwargs)
                if not self._CheckVar(neededFlag, 'contact', actionType, contact, int,'var >= 0 and var <= self.__maxContact'):
                    return False
                neededFlag, durationMS = self._GetValuesInkwargs('durationMS', False, 50, kwargs)
                if not self._CheckVar(neededFlag, 'durationMS', actionType, durationMS, int, 'var >= 0'):
                    return False
                neededFlag, wait_time = self._GetValuesInkwargs('wait_time', False, 0, kwargs)
                if not neededFlag or not (isinstance(wait_time, int) or isinstance(wait_time, float)) or wait_time < 0:
                    self.__logger.error("wrong wait_time when exec swipemove, wait_time:{0}".format(wait_time))
                    return False

                self.__logger.info("platform swipemove, px: {0}, py {1}, contact: {2}, durationMS: {3} waitTime: {4}".format(px, py, contact, durationMS, wait_time))
                self.__device.SwipeMove(px, py, contact, durationMS, wait_time)

            # describe: reset
            # wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
            # return True or False
            elif actionType == TOUCH_RESET:
                neededFlag, wait_time = self._GetValuesInkwargs('wait_time', False, 0, kwargs)
                if not neededFlag or not (isinstance(wait_time, int) or isinstance(wait_time, float)) or wait_time < 0:
                    self.__logger.error("wrong wait_time when exec reset, wait_time:{0}".format(wait_time))
                    return False

                self.__logger.info("platform reset, waitTime: {0}".format(wait_time))
                self.__device.Reset(wait_time=wait_time)

            else:
                self.__logger.error('Wrong aType when TouchCommand, aType:{0}'.format(actionType))
                return False

            return True
        except Exception as e:
            self.__logger.error(e)
            traceback.print_exc()
            return False

    '''
        ==========================================================================================================
        ============================================DeviceCMD=================================================
        ==========================================================================================================

        describe:执行设备相关的操作
        aType:操作类型[DEVICE_INSTALL, DEVICE_START, DEVICE_EXIT, DEVICE_CURAPP, DEVICE_CLEARAPP, DEVICE_KEY,
                      DEVICE_TEXT, DEVICE_SLEEP, DEVICE_WAKE, DEVICE_WMSIZE, DEVICE_BINDRO, DEVICE_SCREENSHOT,
                      DEVICE_SCREENORI, DEVICE_PARAM]
        APKPath:安装包路径
        PKGName：包名
        ActivityName：包的activity
        key：字母
        text：键盘输入的字符串
    '''
    def DeviceCMD(self, **kwargs):
        try:
            self._CheckException()
            neededFlag, actionType = self._GetValuesInkwargs('aType', True, None, kwargs)
            if not neededFlag:
                self.__logger.error('aType is needed when exec DeviceCommand')
                return False

            if actionType == DEVICE_INSTALL:
                neededFlag, APKPath = self._GetValuesInkwargs('APKPath', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'APKPath', actionType, APKPath, str, 'True'):
                    return False
                if not self.__device.InstallAPP(APKPath):
                    self.__logger.error('install app failed: {0}'.format(APKPath))
                    return False

            elif actionType == DEVICE_START:
                neededFlag, PKGName = self._GetValuesInkwargs('PKGName', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'PKGName', actionType, PKGName, str, 'True'):
                    return False
                neededFlag, ActivName = self._GetValuesInkwargs('ActivityName', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'ActivityName', actionType, ActivName, str, 'True'):
                    return False

                self.__device.LaunchAPP(PKGName, ActivName)

            elif actionType == DEVICE_EXIT:
                neededFlag, PKGName = self._GetValuesInkwargs('PKGName', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'PKGName', actionType, PKGName, str, 'True'):
                    return False

                self.__device.ExitAPP(PKGName)

            elif actionType == DEVICE_CURAPP:
                return self.__device.CurrentApp()

            elif actionType == DEVICE_CLEARAPP:
                neededFlag, PKGName = self._GetValuesInkwargs('PKGName', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'PKGName', actionType, PKGName, str, 'True'):
                    return False

                self.__device.ClearAppData(PKGName)

            elif actionType == DEVICE_KEY:
                neededFlag, key = self._GetValuesInkwargs('key', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'key', actionType, key, str, 'True'):
                    return False

                self.__device.Key(key)

            elif actionType == DEVICE_TEXT:
                neededFlag, text = self._GetValuesInkwargs('text', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'text', actionType, text, str, 'True'):
                    return False

                self.__device.Text(text)

            elif actionType == DEVICE_SLEEP:
                self.__device.Sleep()

            elif actionType == DEVICE_WAKE:
                self.__device.Wake()

            elif actionType == DEVICE_WMSIZE:
                return self.__device.WMSize()

            # elif actionType == DEVICE_BINDRO:
            #     neededFlag, rotation = self._GetValuesInkwargs('rotation', True, None, kwargs)
            #     if not self._CheckVar(neededFlag, 'rotation', actionType, rotation, int, 'var in ROTATION_LIST'):
            #         return False
            #
            #     self.__device.BindRotation(rotation)

            elif actionType == DEVICE_SCREENSHOT:
                neededFlag, targetPath = self._GetValuesInkwargs('targetPath', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'targetPath', actionType, targetPath, str, 'True'):
                    return False

                self.__device.TakeScreenshot(targetPath)

            elif actionType == DEVICE_SCREENORI:
                return self.__device.GetScreenOri()

            elif actionType == DEVICE_MAXCONTACT:
                return self.__maxContact
            elif actionType == DEVICE_CLICK:
                neededFlag, px = self._GetValuesInkwargs('px', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'px', actionType, px, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, py = self._GetValuesInkwargs('py', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'py', actionType, py, int, 'var >= 0 and var < self.__height'):
                    return False

                self.__device.ADBClick(px, py)
            elif actionType == DEVICE_SWIPE:
                neededFlag, sx = self._GetValuesInkwargs('sx', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sx', actionType, sx, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, sy = self._GetValuesInkwargs('sy', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'sy', actionType, sy, int, 'var >= 0 and var < self.__height'):
                    return False
                neededFlag, ex = self._GetValuesInkwargs('ex', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'ex', actionType, ex, int, 'var >= 0 and var < self.__width'):
                    return False
                neededFlag, ey = self._GetValuesInkwargs('ey', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'ey', actionType, ey, int, 'var >= 0 and var < self.__height'):
                    return False
                neededFlag, durationMS = self._GetValuesInkwargs('durationMS', False, 50, kwargs)
                if not self._CheckVar(neededFlag, 'durationMS', actionType, durationMS, int, 'var >= 0'):
                    return False

                self.__device.ADBSwipe(sx, sy, ex, ey, durationMS=durationMS)

            elif actionType == DEVICE_PARAM:
                neededFlag, packageName = self._GetValuesInkwargs('PKGName', True, None, kwargs)
                if not self._CheckVar(neededFlag, 'PKGName', actionType, packageName, str, 'True'):
                    return False
                return self.__device.GetDeviceParame(packageName)

            else:
                self.__logger.error('wrong aType when exec DeviceCommand, aType:{0}'.format(actionType))
                return False

            return True
        except Exception as e:
            self.__logger.error(e)
            traceback.print_exc()
            return False
    
    def Finish(self):
        try:
            self._CheckException()
            self.__device.Finish()
        except Exception as e:
            self.__logger.error(e)
            traceback.print_exc()
            return False
        
    def _GetandCheck(self, varname, needed, default, kwargs, actionType, type, describ):
        try:
            neededFlag, var = self._GetValuesInkwargs(varname, needed, default, kwargs)
            if not self._CheckVar(neededFlag, varname, actionType, var, type, describ):
                return False
            return var
        except Exception as e:
            self.__logger.error(e)
            return False
    
    def _GetValuesInkwargs(self, key, isNessesary, defaultValue, kwargs):
        try:
            if not isNessesary:
                if key not in kwargs:
                    return True, defaultValue
                else:
                    return True, kwargs[key]
            else:
                return True, kwargs[key]
        except Exception as e:
            self.__logger.error(e)
            return False

    def _CheckVar(self, needFlag, varname, aType, var, typed, execd):
        try:
            if not needFlag:
                self.__logger.error('can not find {0}'.format(varname))
                return False

            if not isinstance(var, typed):
                self.__logger.error('wrong type of {0}: {1}, {2} is needed'.format(varname, type(var), typed))
                return False

            if not eval(execd):
                self.__logger.error('wrong value of {0}: {1}'.format(varname, var))
                return False

            return True
        except Exception as e:
            self.__logger.error(e)
            return False
    
    def _LogInit(self, logDir, level, deviceSerial):
        try:
            if not isinstance(logDir, str):
                logging.WARNING('wrong logDir when init LOG, logDir:{0}, use default logDir: /tmp/LogDeviceAPI/'.format(logDir))
                logDir = '/tmp/LogDeviceAPI/'
            
            if level not in LOG_LIST:
                logging.WARNING('wrong level when init LOG, level:{0}, use default level: DEBUG'.format(level))
                level = LOG_DEBUG
            
            if not os.path.exists(logDir):
                os.makedirs(logDir)
        
            console = logging.StreamHandler()
            formatter = logging.Formatter(LOG_FORMAT)
            console.setFormatter(formatter)

            fileHandler = RotatingFileHandler(filename=logDir + '/DeviceAPI.log',
                                              maxBytes=2048000,
                                              backupCount=10)
            formatter = logging.Formatter(LOG_FORMAT)
            fileHandler.setFormatter(formatter)

            self.__logger = logging.getLogger(deviceSerial)
            self.__logger.addHandler(fileHandler)
            self.__logger.addHandler(console)
            self.__logger.setLevel(level)
            
            return True
        except Exception as e:
            logging.error(e)
            return False

    def _CheckException(self):
        if exceptionQueue.empty() is False:
            errorStr = exceptionQueue.get()
            while exceptionQueue.empty() is False:
                errorStr = exceptionQueue.get()
            raise Exception(errorStr)