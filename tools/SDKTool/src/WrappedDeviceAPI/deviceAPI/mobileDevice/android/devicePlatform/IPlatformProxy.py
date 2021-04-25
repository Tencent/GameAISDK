# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from abc import ABCMeta, abstractmethod

PP_RET_OK = 0
PP_RET_ERR = -1
PP_RET_ERR_SOCKET_EXCEPTION = -2

# 手机设备信息
class DeviceInfo(object):
    def __init__(self):
        self.display_width = None          # 截屏的宽
        self.display_height = None         # 截屏的高
        self.touch_width = None            # 触点坐标的宽 
        self.touch_height = None           # 触点坐标的高
        self.touch_slot_number = None      # 最大触点数

class IPlatformProxy(object):
    __metaclass__ = ABCMeta
    
    def __init__(self):
        pass

    @abstractmethod
    # 初始化
    # param serial 手机串号
    # param is_portrait 是否为竖屏
    # param long_edge 长边的长度
    # param kwargs中传入自己需要的一些参数，比如minicap端口号和minitouch端口号
    # return True or False
    def init(self, serial=None, is_portrait=True, long_edge=720, **kwargs):
        raise NotImplementedError()
    
    @abstractmethod
    # 回收资源
    # return True or False
    def deinit(self):
        pass

    @abstractmethod
    # 手机触点抬起操作
    # param contact 触点号
    # return None
    def touch_up(self, contact=0):
        raise NotImplementedError()

    @abstractmethod
    # 手机触点按压操作
    # param px 按压点的x坐标
    # param py 按压点的y坐标
    # param contact 按压的触点号
    # param pressure 按压力度
    # return None
    def touch_down(self, px, py, contact=0, pressure=50):
        raise NotImplementedError()

    @abstractmethod
    # 手机滑动操作
    # param px 滑动目的点的x坐标
    # param py 滑动目的点的y坐标
    # param contact 滑动目的的触点号
    # param pressure 滑动力度
    # return None
    def touch_move(self, px, py, contact=0, pressure=50):
        raise NotImplementedError()
    
    @abstractmethod
    # 手机端等待一段时间
    # param milliseconds时间，单位ms
    # return None
    def touch_wait(self, milliseconds):
        raise NotImplementedError()

    @abstractmethod
    # 释放所有触点
    # return None
    def touch_reset(self):
        raise NotImplementedError()

    @abstractmethod
    # 等待手机动作队列中的动作做完后，执行的一系列释放触点等操作
    # return None
    def touch_finish(self):
        raise NotImplementedError()
    
    @abstractmethod
    # 获取手机图像接口
    # return image
    def get_image(self):
        raise NotImplementedError()
    
    @abstractmethod
    # 获取手机设备相关信息
    # return Deviceinfo类的变量
    def get_device_info(self):
        raise NotImplementedError()
    
    @abstractmethod
    # 获取手机朝向
    # return 0表示朝上，1表示朝右，2表示朝下，3表示朝左
    def get_rotation(self):
        raise NotImplementedError()


    '''
    * 以下为TuringLab自用的接口
    '''
    def install_app(self, apk_path):
        pass

    def launch_app(self, package_name, activity_name):
        pass

    def exit_app(self, package_name):
        pass

    def current_app(self):
        pass

    def clear_app_data(self, app_package_name):
        pass

    def key(self, key):
        pass

    def text(self, text):
        pass

    def sleep(self):
        pass

    def wake(self):
        pass

    def vm_size(self):
        pass

    def take_screen_shot(self, target_path):
        pass

    def get_screen_ori(self):
        pass

    def adb_click(self, px, py):
        pass

    def adb_swipe(self, sx, sy, ex, ey, duration_ms=50):
        pass

    def device_param(self, packageName):
        pass
