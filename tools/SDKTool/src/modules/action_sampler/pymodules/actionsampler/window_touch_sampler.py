# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import time
import threading
from queue import Queue

import cv2
import win32gui
import win32con
import win32api

from WrappedDeviceAPI.deviceAdapter import DeviceAdapter, DeviceType

# ActionSampler模块的定义
ACTION_TYPE_PRESS_DOWN = 1  # 按压动作
ACTION_TYPE_PRESS_UP = 2  # 松开动作
ACTION_TYPE_CLICK = 3  # 点击动作


class HookEventType(object):
    MOUSE = "mouse"
    KEYBOARD = "keyboard"

LOG = logging.getLogger('action_sampler')

mouse_queue = Queue()
kb_queue = Queue()
_last_mouse_evt = None
_last_kb_evt = None
_mouse_detect_thread_running = False
_keys_code = []


def uninstall_mouse_hook_proc():
    global _mouse_detect_thread_running
    _mouse_detect_thread_running = False
    time.sleep(0.1)


def detect_mouse_event(keys_code):
    global _mouse_detect_thread_running, mouse_queue, kb_queue
    _mouse_detect_thread_running = True
    is_up = True
    key_up_map = {}
    for k in keys_code:
        key_up_map[k] = True
    while _mouse_detect_thread_running:
        escape_key_down = ((win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000) != 0)
        if escape_key_down:
            LOG.info('unhook')
            break

        left_down = ((win32api.GetAsyncKeyState(0x1) & 0x8000) != 0)

        if left_down and is_up:
            x, y = win32api.GetCursorPos()
            mouse_queue.put((win32con.WM_LBUTTONDOWN, x, y, time.time()))
            is_up = False

        if not left_down and not is_up:
            is_up = True
            mouse_queue.put((win32con.WM_LBUTTONUP, x, y, time.time()))

        for key_code in keys_code:
            key_down = ((win32api.GetAsyncKeyState(key_code) & 0x8000) != 0)
            if key_down and key_up_map[key_code]:
                kb_queue.put((win32con.WM_KEYDOWN, key_code, time.time()))
                key_up_map[key_code] = False

            if not key_down and not key_up_map[key_code]:
                key_up_map[key_code] = True
                kb_queue.put((win32con.WM_KEYUP, key_code, time.time()))

        time.sleep(0.01)

    _mouse_detect_thread_running = False


def install_mouse_hook_proc(target_func, keys_code=[]):
    global _mouse_detect_thread_running
    LOG.info('hook mouse')
    mouse_thread = threading.Thread(target=target_func, args=(keys_code, ), name="mouse_hook_thread")
    mouse_thread.daemon = True
    mouse_thread.start()
    return mouse_thread


def unhook_all():
    uninstall_mouse_hook_proc()


def parse_mouse_evts():
    global _last_mouse_evt, mouse_queue
    ret = []
    while mouse_queue.qsize() > 0:
        msgid, x, y, ts = mouse_queue.get_nowait()
        if msgid == win32con.WM_LBUTTONUP:
            if _last_mouse_evt and ts-_last_mouse_evt[2] < 0.2:
                ret.append((ACTION_TYPE_CLICK, [x, y], ts))
            else:
                if _last_mouse_evt:
                    ret.append(_last_mouse_evt)
                ret.append((ACTION_TYPE_PRESS_UP, [x, y], ts))
                _last_mouse_evt = None

        if msgid == win32con.WM_LBUTTONDOWN:
            _last_mouse_evt = (ACTION_TYPE_PRESS_DOWN, [x, y], ts)

    return ret


def parse_keyboard_evts():
    global _last_kb_evt, kb_queue
    ret = []
    while kb_queue.qsize() > 0:
        msgid, vkcode, ts = kb_queue.get_nowait()
        if msgid == win32con.WM_KEYUP:
            if _last_kb_evt and ts-_last_kb_evt[2] < 0.2:
                ret.append((ACTION_TYPE_CLICK, vkcode, ts))
            else:
                if _last_kb_evt:
                    ret.append(_last_kb_evt)
                ret.append((ACTION_TYPE_PRESS_UP, vkcode, ts))
                _last_kb_evt = None

        if msgid == win32con.WM_KEYDOWN:
            _last_kb_evt = (ACTION_TYPE_PRESS_DOWN, vkcode, ts)

    return ret


class WindowTouchSampler(object):
    def __init__(self, hwnd=None):
        self.__hwnd = hwnd
        self.__window_instance = DeviceAdapter(DeviceType.Windows.value)
        self.__frame_width = 0
        self.__frame_height = 0
        rc = win32gui.GetWindowRect(self.__hwnd)
        self.__window_width = rc[2] - rc[0]
        self.__window_height = rc[3] - rc[1]
        LOG.info('window size, w:%s, h:%s' % (self.__window_width, self.__window_height))

    def init(self, widht, height, keys_code=[]):
        self.__window_instance.initialize(hwnd=self.__hwnd)
        self.__frame_width = widht
        self.__frame_height = height
        LOG.info('input frame size, w:%s, h:%s' % (self.__frame_width, self.__frame_height))
        keys_code.append(win32con.VK_F1)
        keys_code.append(win32con.VK_F2)
        LOG.info('key codes:%s' % str(keys_code))
        mouse_thread = install_mouse_hook_proc(detect_mouse_event, keys_code)
        if mouse_thread:
            LOG.info("mouse hook installed")

    def deinit(self):
        """ 中止录制

        :return:
        """
        uninstall_mouse_hook_proc()

    def get_sample(self):
        img_data = self.__window_instance.getScreen()
        if img_data is None:
            return None, None

        img_data = cv2.resize(img_data, (self.__frame_width, self.__frame_height))

        pts = []
        evts = parse_mouse_evts()
        if evts:
            LOG.info("mouse evts:%s" % evts)
            for evt in evts:
                msgid, pt, ts = evt
                x, y = pt
                hwnd = win32gui.WindowFromPoint((x, y))
                if hwnd != self.__hwnd:
                    continue
                c_x, c_y = win32gui.ScreenToClient(self.__hwnd, (x, y))
                if c_x <= 0 or c_x >= self.__window_width:
                    continue
                if c_y <= 0 or c_y >= self.__window_height:
                    continue
                p_x = int(self.__frame_width * c_x / self.__window_width)
                p_y = int(self.__frame_height * c_y / self.__window_height)
                pts.append([HookEventType.MOUSE, msgid, [p_x, p_y]])

        evts = parse_keyboard_evts()
        if evts:
            LOG.info("key evts:%s" % evts)
            for evt in evts:
                msgid, vk, ts = evt
                pts.append([HookEventType.KEYBOARD, msgid, vk])

        return img_data, pts
