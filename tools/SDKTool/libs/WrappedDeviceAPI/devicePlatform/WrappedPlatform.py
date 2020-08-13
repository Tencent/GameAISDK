# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import importlib
import numpy as np

from APIDefine import *
from plugin.GetPlatformInstance import GetPlatformInstance


class PlatformWrapper(object):
    def __init__(self, moduleName=None):
        self.__moduleName = moduleName
        self.__actionClass = None
        self.__platformInstance = None
        self.__contactState = []
    
    def Initialize(self, serial=None, isPortrait=False, long_edge=1280, kwargs=None):
        if serial is None:
            self.__logger = logging.getLogger(LOG_DEFAULT)
        else:
            self.__logger = logging.getLogger(serial)
        self.__logger.info("platform getinstance")
        self.__platformInstance = GetPlatformInstance(serial, self.__moduleName)
        if self.__platformInstance is None:
            self.__logger.error('get platform class failed')
            return False, "get platform class failed"
        self.__logger.info("platform init")

        ret, strError = self.__platformInstance.init(serial, isPortrait, long_edge, **kwargs)
        if ret is False:
            self.__logger.error('platform class initialize failed')
            return False, strError
        self.__logger.info("platform init successful")
        self.__contactState = [None] * self.GetMaxContact()
        return True, str()

    def DeInitialize(self):
        return self.__platformInstance.deinit()
    
    def GetFrame(self):
        PPRET, ScreenImg = self.__platformInstance.get_image()
        if PPRET != 0:
            self.__logger.error('Get frame failed, error code:{0}'.format(PPRET))
            
        return PPRET, ScreenImg
    
    def Down(self, px, py, contact=0, pressure=50):
        self.__platformInstance.touch_down(px, py, contact, pressure)
        # if PPRET != 0:
        #     self.__logger.error('touch down failed, error code:{0}'.format(PPRET))
        self.__contactState[contact] = (px, py)

    def Up(self, contact=0):
        self.__platformInstance.touch_up(contact)
        # if PPRET != 0:
        #     self.__logger.error('touch up failed, error code:{0}'.format(PPRET))
        self.__contactState[contact] = None

    def Move(self, px, py, contact=0, pressure=50):
        self.__platformInstance.touch_move(px, py, contact, pressure)
        # if PPRET != 0:
        #     self.__logger.error('touch move failed, error code:{0}'.format(PPRET))
        if self.__contactState[contact] is not None:
            self.__contactState[contact] = (px, py)
        else:
            self.__logger.warning('contact {0} not down when move to ({1}, {2})'.format(contact, px, py))
        
    def SwipeMove(self, px, py, contact=0, durationMS=50, pressure=50):
        if self.__contactState[contact] is not None:
            self._AddPoint(self.__contactState[contact][0], self.__contactState[contact][1], px, py, contact, durationMS, pressure)
        else:
            self.__logger.warning('contact {0} not down when swipemove to ({1}, {2})'.format(contact, px, py))

    def Click(self, px, py, contact=0, durationMS=-1, pressure=50):
        if durationMS < 0:
            durationMS = 50
            
        self.Down(px, py, contact, pressure)
        self.Wait(durationMS)
        self.Up(contact)
        
    def UpAll(self):
        for contact in range(self.GetMaxContact()):
            self.Up(contact)

    def SwipeDownMoveUp(self, sx, sy, ex, ey, contact=0, durationMS=50, pressure=50):
        self.Up(contact)
        self.Down(sx, sy, contact, pressure)
        self.Wait(WAITTIME_POINT)
        self._AddPoint(sx, sy, ex, ey, contact, durationMS, pressure)
        self.Up(contact)

    def SwipeDownMove(self, sx, sy, ex, ey, contact=0, durationMS=50, pressure=50):
        self.Up(contact)
        self.Down(sx, sy, contact, pressure)
        self.Wait(WAITTIME_POINT)
        self._AddPoint(sx, sy, ex, ey, contact, durationMS, pressure)
        
    def Wait(self, waitMS):
        self.__platformInstance.touch_wait(waitMS)
        # if PPRET != 0:
        #     self.__logger.error('touch wait failed, error code:{0}'.format(PPRET))
        
    def GetScreenResolution(self):
        deviciInfo, strError = self.__platformInstance.get_device_info()
        # if PPRET != 0:
        #     self.__logger.error('get device info failed, error code:{0}'.format(PPRET))
        if deviciInfo is None:
            return -1, -1, strError
        
        return deviciInfo.display_height, deviciInfo.display_width, str()
    
    def GetMaxContact(self):
        deviciInfo, strError = self.__platformInstance.get_device_info()
        # if PPRET != 0:
        #     self.__logger.error('get device info failed, error code:{0}'.format(PPRET))
        if deviciInfo is None:
            raise Exception("get contact number failed")

        return deviciInfo.touch_slot_number
    
    def Reset(self):
        self.__platformInstance.touch_reset()
        # if PPRET != 0:
        #     self.__logger.error('touch reset failed, error code:{0}'.format(PPRET))

    def Finish(self):
        self.__platformInstance.touch_finish()

    def InstallAPP(self, APKPath):
        return self.__platformInstance.install_app(APKPath)

    def LauchAPP(self, PackageName, ActivityName):
        self.__platformInstance.launch_app(PackageName, ActivityName)

    def ExitAPP(self, PackageName):
        self.__platformInstance.exit_app(PackageName)

    def CurrentApp(self):
        return self.__platformInstance.current_app()

    def ClearAppData(self, appPackageName):
        self.__platformInstance.clear_app_data(appPackageName)

    def Key(self, Key):
        self.__platformInstance.key(Key)

    def Text(self, Text):
        self.__platformInstance.text(Text)

    def Sleep(self):
        self.__platformInstance.sleep()

    def Wake(self):
        self.__platformInstance.wake()

    def WMSize(self):
        return self.__platformInstance.vm_size()

    def TakeScreenshot(self, targetPath):
        self.__platformInstance.take_screen_shot(targetPath)

    def GetScreenOri(self):
        return self.__platformInstance.get_screen_ori()

    def ADBClick(self, px, py):
        self.__platformInstance.adb_click(px, py)

    def ADBSwipe(self, sx, sy, ex, ey, durationMS=50):
        self.__platformInstance.adb_swipe(sx, sy, ex, ey, duration_ms=durationMS)

    def DeviceParam(self, packageName):
        return self.__platformInstance.device_param(packageName)

    def _AddPoint(self, sx, sy, ex, ey, contact=0, durationMS=50, pressure=50):
        beginPoint = np.array([sx, sy])
        targetPoint = np.array([ex, ey])
        numMovingPoints = int(durationMS / WAITTIME_POINT)
        movingX = np.linspace(beginPoint[0], targetPoint[0], numMovingPoints).astype(int)
        movingY = np.linspace(beginPoint[1], targetPoint[1], numMovingPoints).astype(int)

        for i in range(numMovingPoints - 1):
            self.Move(movingX[i + 1], movingY[i + 1], contact=contact, pressure=pressure)
            self.Wait(WAITTIME_POINT)
    
    # def _GetClass(self):
    #     # try:
    #     for file in os.listdir(parentdir + PLUGIN_TOUCH_DIR):
    #         if os.path.isfile(parentdir + PLUGIN_TOUCH_DIR + file):
    #             moduleName = file[:file.find('.')]
    #             module = importlib.import_module(moduleName)
    #             if self.__className in dir(module):
    #                 self.__actionClass = getattr(module, self.__className)
    #                 return True
    #
    #     # except Exception as err:
    #     #     self.__logger.error('exception when looking for action class:{0}'.format(err))
    #     #     return False
    #     self.__logger.error('can not find action class')
    #     return False
