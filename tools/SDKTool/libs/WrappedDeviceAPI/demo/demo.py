# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import cv2
import sys
import os
import queue

__dir__ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, __dir__)
from WrappedDeviceAPI import *


def sample():
    deviceAPI = IDeviceAPI('Android')

    '''
       describe：初始化
       param[0],str类型：手机序列号,默认为None，当接入一个设备时可不指定序列号，当接入多个设备时需要指定
       param[1],bool类型：手机为横屏还是竖屏，True为竖屏，False为横屏
       param[2],int类型：长边的长度
       param[3],str类型：指定日志目录,默认为/tmp/LogDeviceAPI
       param[4],枚举类型：指定日志级别，取值为[LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR, LOG_CRITICAL]，默认为LOG_DEBUG
       param[5],bool类型：是否show出图片
       param[5],字典    ：一些组件需要的参数，可以自己定义，例如端口号等等
       return,bool类型，成功返回True，失败返回False
   '''
    if not deviceAPI.Initialize('908fedc0', False, 720, 1280, '/tmp/LogDeviceAPI', LOG_DEBUG):
        return False
    
    '''
    describe:获取当前图像帧
    return：Mat类型的图像
    '''
    frame = deviceAPI.GetFrame()
    if frame is None:
        return False
    
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
    # deviceAPI.TouchCMD(aType=[TOUCH_CLICK, TOUCH_DOWN, TOUCH_UP, TOUCH_SWIPE, TOUCH_MOVE],
    #                        sx=int,
    #                        sy=int,
    #                        ex=int,
    #                        ey=int,
    #                        contact=0,
    #                        durationMS=50,
    #                        needUp=True,
    #                        wait_time=0)
    
    '''
        describe:执行点击操作
        sx为横坐标，相对于初始化时传入的坐标系
        sy为纵坐标，相对于初始化时传入的坐标系
        contact为触点，默认为0
        durantionMS为动作持续时间，默认为-1
        wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
        return True or False
    '''
    if not deviceAPI.TouchCMD(aType=TOUCH_CLICK, sx=300, sy=300, contact=0, durantionMS=-1, wait_time=0):
        return False
    
    '''
        describe:执行按压操作
        sx为横坐标，相对于初始化时传入的坐标系
        sy为纵坐标，相对于初始化时传入的坐标系
        contact为触点，默认为0
        wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
        return True or False
    '''
    if not deviceAPI.TouchCMD(aType=TOUCH_DOWN, sx=300, sy=300, contact=0, wait_time=0):
        return False
    
    '''
        describe:执行抬起操作
        wait_time为执行动作后，手机端等待时间，单位为秒，默认为0
        return True or False
    '''
    if not deviceAPI.TouchCMD(aType=TOUCH_UP, contact=1, wait_time=0):
        return False
    
    '''
        describe:执行滑动
        sx, sy为起始点的坐标
        ex, ey为终止点的坐标
        DaType表示执行动作的实现方式，有minitouch和ADB两种[DACT_TOUCH, DACT_ADB],默认为DACT_TOUCH
        contact为触点，默认为0
        durantionMS为动作持续时间，默认为50
        needUp表示滑动后是否抬起，默认为True
        wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
        return True or False
    '''
    if not deviceAPI.TouchCMD(aType=TOUCH_SWIPE,
                              sx=500,
                              sy=500,
                              ex=600,
                              ey=600,
                              contact=0,
                              durationMS=500,
                              needUp=False,
                              wait_time=0):
        return False
    
    '''
        describe:执行滑动操作，与swipe不同的是他只有终止点，通过多个move可以组合成一个swipe
        sx为横坐标，相对于初始化时传入的坐标系
        sy为纵坐标，相对于初始化时传入的坐标系
        contact为触点，默认为0
        wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
        return True or False
    '''
    if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=300, sy=300, contact=0, wait_time=0):
        return False

    '''
        describe:执行滑动操作，与move不同的是它进行了补点操作
        sx为横坐标，相对于初始化时传入的坐标系
        sy为纵坐标，相对于初始化时传入的坐标系
        contact为触点，默认为0
        wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
        return True or False
    '''
    if not deviceAPI.TouchCMD(aType=TOUCH_SWIPEMOVE, sx=300, sy=300, durationMS=50, contact=0, wait_time=0):
        return False

    '''
        describe:reset
        wait_time为执行动作后，手机端等待时间，单位为毫秒，默认为0
        return True or False
    '''
    if not deviceAPI.TouchCMD(aType=TOUCH_RESET, wait_time=0):
        return False
    '''
    ==========================================================================================================
    ============================================DeviceCMD=================================================
    ==========================================================================================================

    describe:执行设备相关的操作
    aType:操作类型[DEVICE_INSTALL, DEVICE_START, DEVICE_EXIT, DEVICE_CURAPP, DEVICE_CLEARAPP, DEVICE_KEY,
                  DEVICE_TEXT, DEVICE_SLEEP, DEVICE_WAKE, DEVICE_WMSIZE, DEVICE_BINDRO, DEVICE_SCREENSHOT,
                  DEVICE_SCREENORI]
    APKPath:安装包路径
    PKGName：包名
    ActivityName：包的activity
    key：
    '''
    # deviceAPI.DeviceCMD(aType=[DEVICE_INSTALL, DEVICE_START, DEVICE_EXIT, DEVICE_CURAPP, DEVICE_CLEARAPP, DEVICE_KEY,
    #                                DEVICE_TEXT, DEVICE_SLEEP, DEVICE_WAKE, DEVICE_WMSIZE, DEVICE_BINDRO, DEVICE_SCREENSHOT,
    #                                DEVICE_SCREENORI],
    #                         APKPath=str,
    #                         PKGName=str,
    #                         ActivityName=str,
    #                         key=str,
    #                         text=str,
    #                         rotation=str,
    #                         targetPath=str)
    
    '''
    aType为DEVICE_INSTALL时表示安装app
    APKPath为所需参数，表示apk包在PC端的存放路径
    return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_INSTALL, APKPath='/home/ting/kidting/game_ai_sdk/data/qqspeed/game.apk'):
        return False
    
    '''
        aType为DEVICE_START时表示启动app
        APKPath为所需参数，表示apk包在PC端的存放路径
        ActivityName为apk包启动的activity
        return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_START, PKGName='com.tencent.tmgp.speedmobile',
                               ActivityName='com.tencent.tmgp.speedmobile.speedmobile'):
        return False
    
    '''
        aType为DEVICE_CURAPP时表示获取当前app
        return 字典，currentAPP = {'package': str(), 'activity': str()}
    '''
    currentAPP = deviceAPI.DeviceCMD(aType=DEVICE_CURAPP)

    '''
        aType为DEVICE_PARAM时表示获取当前app运行时，手机的性能参数
        PKGName为所需参数，表示APP包名
        return deviceParam为字典，分别存有CPU, 内存， 电量， 温度这四个参数
        
        deviceParam = {
            'cpu': float,
            'mem': float,
            'temperature': float,
            'battery': int
        }
    '''
    deviceParam = deviceAPI.DeviceCMD(aType=DEVICE_PARAM, PKGName='com.tencent.tmgp.speedmobile')
    
    '''
        aType为DEVICE_CLEARAPP时表示清空app数据
        PKGName为所需参数，表示APP包名
        return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_CLEARAPP, PKGName='com.tencent.tmgp.speedmobile'):
        return False
    
    '''
        aType为DEVICE_EXIT时表示退出app
        PKGName为所需参数，表示APP包名
        return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_EXIT, PKGName='com.tencent.tmgp.speedmobile'):
        return False
    
    '''
        aType为DEVICE_KEY时表示输入手机键盘的按键
        key为所需参数，str类型，表示手机具体按键
        return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_KEY, key='cmd'):
        return False
    
    '''
        aType为DEVICE_TEXT时表示输入字符串
        text为所需参数，str类型，表示具体输入的字符串
        return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_TEXT, text='abc'):
        return False
    
    '''
        aType为DEVICE_SLEEP时表示设备锁屏
        return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_SLEEP):
        return False
    
    '''
        aType为DEVICE_WAKE时表示设备解锁启动
        return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_WAKE):
        return False
    
    '''
        aType为DEVICE_WMSIZE时表示获取设备的分辨率
        return height, width
    '''
    height, width = deviceAPI.DeviceCMD(aType=DEVICE_WMSIZE)
    if height == -1 or width == -1:
        return False
    
    # '''
    #     aType为DEVICE_BINDRO时表示设置设备锁定朝向
    #     return height, width
    # '''
    # height, width = deviceAPI.DeviceCMD(aType=DEVICE_BINDRO)
    # if height == -1 or width == -1:
    #     return False
    
    '''
        aType为DEVICE_SCREENSHOT时表示快照，截屏
        targetPath表示在PC端存放的路径
        return True or False
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_SCREENSHOT, targetPath='./test.png'):
        return False
    
    '''
        aType为DEVICE_SCREENORI时表示返回设备当前时横屏还是竖屏
        return UI_SCREEN_ORI_PORTRAIT or UI_SCREEN_ORI_LANDSCAPE
    '''
    res = deviceAPI.DeviceCMD(aType=DEVICE_SCREENORI)
    if res == UI_SCREEN_ORI_PORTRAIT:
        print('竖屏')
    elif res == UI_SCREEN_ORI_LANDSCAPE:
        print('横屏')
    else:
        return False
    
    '''
        describe:获取最大触点数
        return int
    '''
    maxContact = deviceAPI.DeviceCMD(aType=DEVICE_MAXCONTACT)
    if maxContact < 0:
        return False
    
    '''
        describe:用ADB命令执行点击操作
        return int
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_CLICK, px=300, py=300):
        return False
    
    '''
        describe:用ADB命令执行滑动操作（需要先执行点击后，才能看到滑动效果，将会瞬间滑动到指定的坐标上）
        return int
    '''
    if not deviceAPI.DeviceCMD(aType=DEVICE_SWIPE, sx=300, sy=300, ex=500, ey=500, durationMS=50):
        return False
    
    '''
        describe:等待所有指令发送至手机端，在程序退出时使用
    '''
    deviceAPI.Finish()
    
    '''
    ==========================================================================================================
    ==========================================================================================================
    ==========================================================================================================
    '''



def demo1():
    # deviceAPI1 = IDeviceAPI('Android', 'PlatformWeTest')
    # deviceAPI2 = IDeviceAPI('Android', 'PlatformWeTest')
    deviceAPI1 = IDeviceAPI('Android')
    deviceAPI2 = IDeviceAPI('Android')
    deviceAPI1.Initialize(deviceSerial='4da2dea3', height=200, width=1280, logDir='./log', minitouchPort=1122, minicapPort=1133)
    deviceAPI2.Initialize(deviceSerial='9889db384258523633', height=200, width=1280, logDir='./log', minitouchPort=1144, minicapPort=1155)
    # maxContact = deviceAPI.DeviceCMD(aType=DEVICE_MAXCONTACT)

    # begin = time.time()
    # for i in range(10):
    #     if not deviceAPI1.TouchCMD(aType=TOUCH_CLICK, sx=300, sy=300, durationMS=1000, wait_time=1000):
    #             print('click failed')
    #     end = time.time()
    #     print(end - begin)
    #
    #     if not deviceAPI.TouchCMD(aType=TOUCH_DOWN, sx=100, sy=100, wait_time=1000):
    #         print('click failed')
    #     # if not deviceAPI.TouchCMD(aType=TOUCH_UP):
    #     print('up failed')
    # if not deviceAPI.TouchCMD(aType=TOUCH_CLICK, sx=500, sy=500, contact=0, durantionMS=50, wait_time=1000):
    #     return False

    # if not deviceAPI1.DeviceCMD(aType=DEVICE_SWIPE, sx=640, sy=100, ex=640, ey=300, durationMS=1000):
    #     print('click failed')

    # time.sleep(100000)
    # return None

    if not deviceAPI1.TouchCMD(aType=TOUCH_DOWN, sx=640, sy=100, wait_time=1000):
        print('click failed')

    if not deviceAPI2.TouchCMD(aType=TOUCH_DOWN, sx=200, sy=200, wait_time=50):
        print('click failed')

    if not deviceAPI1.TouchCMD(aType=TOUCH_SWIPEMOVE, sx=640, sy=300, durationMS=1000, contact=0, wait_time=1000):
        return False
    if not deviceAPI2.TouchCMD(aType=TOUCH_SWIPEMOVE, sx=100, sy=100, durationMS=1000, contact=0, wait_time=1000):
        return False
    if not deviceAPI1.TouchCMD(aType=TOUCH_SWIPEMOVE, sx=100, sy=100, durationMS=1000, contact=0, wait_time=1000):
        return False
    if not deviceAPI2.TouchCMD(aType=TOUCH_SWIPEMOVE, sx=200, sy=200, durationMS=1000, contact=0, wait_time=1000):
        return False
    # print(maxContact)
    # if not deviceAPI.TouchCMD(aType=TOUCH_SWIPE, sx=200, sy=200, ex=400, ey=400, wait_time=1000, durationMS=500):
    #     print('swipe failed')
    #     return False
    # if not deviceAPI.TouchCMD(aType=TOUCH_DOWN, sx=300, sy=300, wait_time=1000):
    #     print('click failed')
    #     return False
    # if not deviceAPI.TouchCMD(aType=TOUCH_DOWN, sx=500, sy=500, contact=1, wait_time=1000):
    #     print('click failed')
    #     return False
    # for i in range(10):
    #     if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=500, sy=500, wait_time=1000):
    #         print('click failed')
    #         return False
    #     if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=400, sy=400, contact=1, wait_time=1000):
    #         print('click failed')
    #         return False
    #     if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=400, sy=400, wait_time=1000):
    #         print('click failed')
    #         return False
    #     if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=500, sy=500, contact=1, wait_time=1000):
    #         print('click failed')
    #         return False
    #     # time.sleep(1)
    #
    # if not deviceAPI.TouchCMD(aType=TOUCH_UP, contact=1, wait_time=1000):
    #     print('click failed')
    #     return False
    #
    # if not deviceAPI.TouchCMD(aType=TOUCH_RESET):
    #     print('reset failed')
    #     return False
    time.sleep(5)
    for i in range(100000):
        frame1 = deviceAPI1.GetFrame()
        frame2 = deviceAPI2.GetFrame()
        if frame1 is not None:
            cv2.imshow('test1', frame1)
            cv2.waitKey(1)

        if frame2 is not None:
            cv2.imshow('test2', frame2)
            cv2.waitKey(1)
        #     #time.sleep(1)

def demo():
    # deviceAPI1 = IDeviceAPI('Android', 'PlatformWeTest')
    deviceAPI1 = IDeviceAPI('Android')
    flag, strerror = deviceAPI1.Initialize(isPortrait=False, long_edge=1280, logDir='./log', level=LOG_INFO, showRawScreen=False)
    print(flag)
    print(strerror)
    # maxContact = deviceAPI.DeviceCMD(aType=DEVICE_MAXCONTACT)

    # begin = time.time()
    # for i in range(10):
    #     if not deviceAPI1.TouchCMD(aType=TOUCH_CLICK, sx=300, sy=300, durationMS=1000, wait_time=1000):
    #             print('click failed')
    #     end = time.time()
    #     print(end - begin)
    #
    #     if not deviceAPI.TouchCMD(aType=TOUCH_DOWN, sx=100, sy=100, wait_time=1000):
    #         print('click failed')
    #     # if not deviceAPI.TouchCMD(aType=TOUCH_UP):
    #     #     print('up failed')
    # pkgName = deviceAPI1.DeviceCMD(aType=DEVICE_CURAPP)
    # parameter= deviceAPI1.DeviceCMD(aType=DEVICE_PARAM, PKGName=pkgName['package'])
    # print(parameter)
    # exit(0)
    if not deviceAPI1.TouchCMD(aType=TOUCH_CLICK, sx=1130, sy=442, contact=0, durationMS=5000, wait_time=1000):
        return False

    if not deviceAPI1.DeviceCMD(aType=DEVICE_SWIPE, sx=640, sy=100, ex=640, ey=300, durationMS=1000):
        print('click failed')

    # time.sleep(100000)
    # return None
    # if not deviceAPI1.TouchCMD(aType=TOUCH_DOWN, sx=100, sy=100, wait_time=5000):
    #     print('click failed')
    # if not deviceAPI1.TouchCMD(aType=TOUCH_UP):
    #     print('up failed')
    # begin = time.time()
    if not deviceAPI1.TouchCMD(aType=TOUCH_CLICK, sx=1270, sy=300, durationMS=5000, wait_time=1000):
        print('click failed')
    # end = time.time()
    # print("action:{}".format(end - begin))

    begin = time.time()
    if not deviceAPI1.TouchCMD(aType=TOUCH_SWIPEMOVE, sx=100, sy=300, durationMS=1000, contact=0, wait_time=1000):
        return False
    if not deviceAPI1.TouchCMD(aType=TOUCH_SWIPEMOVE, sx=100, sy=100, durationMS=1000, contact=0, wait_time=1000):
        return False
    end = time.time()
    # print("action:{}".format(end - begin))
    # print(maxContact)
    # if not deviceAPI.TouchCMD(aType=TOUCH_SWIPE, sx=200, sy=200, ex=400, ey=400, wait_time=1000, durationMS=500):
    #     print('swipe failed')
    #     return False
    # if not deviceAPI.TouchCMD(aType=TOUCH_DOWN, sx=300, sy=300, wait_time=1000):
    #     print('click failed')
    #     return False
    # if not deviceAPI.TouchCMD(aType=TOUCH_DOWN, sx=500, sy=500, contact=1, wait_time=1000):
    #     print('click failed')
    #     return False
    # for i in range(10):
    #     if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=500, sy=500, wait_time=1000):
    #         print('click failed')
    #         return False
    #     if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=400, sy=400, contact=1, wait_time=1000):
    #         print('click failed')
    #         return False
    #     if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=400, sy=400, wait_time=1000):
    #         print('click failed')
    #         return False
    #     if not deviceAPI.TouchCMD(aType=TOUCH_MOVE, sx=500, sy=500, contact=1, wait_time=1000):
    #         print('click failed')
    #         return False
    #     # time.sleep(1)
    #
    # if not deviceAPI.TouchCMD(aType=TOUCH_UP, contact=1, wait_time=1000):
    #     print('click failed')
    #     return False
    #
    # if not deviceAPI.TouchCMD(aType=TOUCH_RESET):
    #     print('reset failed')
    #     return False
    # print('action down')
    time.sleep(5)
    count = 0

    abegin = time.time()
    while True:
        begin = time.time()
        frame1, error = deviceAPI1.GetFrame()
        end = time.time()
        # print('getframe: {0}', format(count))
        # print('getframe: {0}', format(end - begin))
        if frame1 is not None:
            # cv2.imwrite('test.png', frame1)
            count += 1
            # if count == 500:
            #     break
            cv2.imshow('test1', frame1)
            cv2.waitKey(1)
    aend = time.time()
    # print((aend - abegin)/501)


if __name__ == '__main__':
    # sample()
    demo()
