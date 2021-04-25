# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import ctypes
import win32con
import win32api
from ctypes import wintypes

ULONG_PTR = wintypes.WPARAM

_SHIFT = {'~': '`', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
          '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.', '?': '/'}

_MODIFIERS = [
    win32con.VK_SHIFT,
    win32con.VK_CONTROL,
    win32con.VK_MENU,
    win32con.VK_LWIN,
    win32con.VK_RWIN,
]

_MODIFIER_KEY_MAP = {
    '+': win32con.VK_SHIFT,
    '^': win32con.VK_CONTROL,
    '%': win32con.VK_MENU,
}

_CODES = {
    'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117,
    'F7': 118, 'F8': 119, 'F9': 120, 'F10': 121, 'F11': 122, 'F12': 123,
    'BKSP': 8, 'TAB': 9, 'ENTER': 13, 'ESC': 27, 'END': 35, 'HOME': 36, 'INSERT': 45, 'DEL': 46,
    'PGUP': 33, 'PGDN': 34, 'LEFT': 37, 'UP': 38, 'RIGHT': 39, 'DOWN': 40, 'PRINT': 44,
    'SHIFT': 16, 'CTRL': 17, 'MENU': 18, 'ALT': 18,
    'APPS': 93, 'CAPS': 20, 'WIN': 91, 'LWIN': 91, 'RWIN': 92
    }


def _scan2vkey(scan):
    return 0xff & ctypes.windll.user32.VkKeyScanW(ctypes.c_wchar("%c" % scan))


class _KeyboardEvent(object):
    KEYEVENTF_EXTENDEDKEY = 1
    KEYEVENTF_KEYUP = 2
    KEYEVENTF_UNICODE = 4
    KEYEVENTF_SCANCODE = 8


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ULONG_PTR),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', wintypes.DWORD),
    ]

    def __init__(self, *args, **kwargs):
        super(_KEYBDINPUT, self).__init__(*args, **kwargs)
        if not self.dwFlags & _KeyboardEvent.KEYEVENTF_UNICODE:
            self.wScan = ctypes.windll.MapVirtualKeyExW(self.wVk, 0, 0)


class _UNION_INPUT_STRUCTS(ctypes.Union):
    "The C Union type representing a single Event of any type"
    _fields_ = [
        ('mi', _MOUSEINPUT),
        ('ki', _KEYBDINPUT),
        ('hi', _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _fields_ = [
        ('type', wintypes.DWORD),
        ('_', _UNION_INPUT_STRUCTS),
    ]


class KeyInputError(Exception):
    """键盘输入错误
    """
    def __init__(self, *args, **kwargs):
        pass


class Key(object):
    """一个按键
    """

    def __init__(self, key):
        """Constructor

        :type key: number or charactor
        :param key: 按键
        """
        self._flag = 0
        self._modifiers = []
        if isinstance(key, str):
            self._scan = ord(key)
            if self._scan < 256:  # ASCII code
                self._vk = _scan2vkey(self._scan)
                if key.isupper() or key in _SHIFT:  # 按下shift键
                    self._modifiers.append(Key(_MODIFIER_KEY_MAP['+']))
            else:  # unicode
                self._vk = 0
                self._flag |= _KeyboardEvent.KEYEVENTF_UNICODE
        elif isinstance(key, int):  # virtual Key
            self._vk = key
            self._scan = ctypes.windll.user32.MapVirtualKeyW(self._vk, 0)
            if self._is_extended_key(self._vk):
                self._flag |= _KeyboardEvent.KEYEVENTF_EXTENDEDKEY
        else:
            raise KeyInputError('Key is not a number or string')

        # 若是以下虚拟键则需要同步
        # 暂只对最主要的SHIFT、CTRL、ALT键进行同步
        self._SyncVKeys = [win32con.VK_SHIFT, win32con.VK_LSHIFT, win32con.VK_RSHIFT,
         win32con.VK_CONTROL, win32con.VK_LCONTROL, win32con.VK_RCONTROL,
         win32con.VK_MENU, win32con.VK_LMENU, win32con.VK_RMENU]

    def append_modifier_key(self, key):
        """Modifier Key comes with the key

        :type key: Key
        :param key: Ctrl, Shift or Atl Key
        """
        self._modifiers.append(key)

    def _is_extended_key(self, vkey):
        return 33 <= vkey <= 46 or 91 <= vkey <= 93

    def press_key(self):
        """ 按下按键

        :return:
        """
        self._input_key(up=False)

    def release_key(self):
        """ 释放按键

        :return:
        """
        self._input_key(up=True)

    def _input_key(self, up):
        inp = _INPUT()
        inp.type = 1
        inp._.ki.wVk = self._vk
        inp._.ki.wScan = self._scan
        inp._.ki.dwFlags |= self._flag
        if up:
            inp._.ki.dwFlags |= _KeyboardEvent.KEYEVENTF_KEYUP

        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

    def input_key(self):
        """键盘模拟输入按键
        """
        for mkey in self._modifiers:
            mkey.press_key()

        self.press_key()
        self.release_key()
        for mkey in self._modifiers:
            mkey.release_key()

    def _post_key(self, hwnd, up):
        """给某个窗口发送按钮"""
        if up:
            ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_KEYUP, self._vk, self._scan << 16 | 0xc0000001)
        else:
            ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_KEYDOWN, self._vk, self._scan << 16 | 1)
        time.sleep(0.01)  # 必须加，否则有些控件响应不了，会产生问题

    def post_key(self, hwnd):
        """将按键消息发到hwnd

        :hwnd: int, 目标窗口句柄
        """
        for mkey in self._modifiers:
            mkey.press_key()
            time.sleep(0.01)  # 必须加，否则下面实际寄送的键盘按键消息可能比这个消息更快到达目标窗口

        if self._scan < 256:
            self._post_key(hwnd, up=False)
            self._post_key(hwnd, up=True)
        else:
            ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_CHAR, self._scan, 1)

        for mkey in self._modifiers:
            mkey.release_key()

    def is_pressed(self):
        """该键是否被按下
        """
        return (win32api.GetAsyncKeyState(self._vk) & 0x8000) == 0

    def is_troggled(self):
        """该键是否被开启，如CAps Lock或Num Lock等
        """
        return (win32api.GetKeyState(self._vk) & 1) != 0


class Keyboard(object):
    """键盘输入类，实现了两种键盘输入方式。

    一类方法使用模拟键盘输入的方式。
    另一类方法使用Windows消息的机制将字符串直接发送的窗口。

    键盘输入类支持以下字符的输入。
    1、特殊字符：^, +, %,  {, }
        '^'表示Control键，同'{CTRL}'。'+'表示Shift键，同'{SHIFT}'。'%'表示Alt键，同'{ALT}'。
        '^', '+', '%'可以单独或同时使用，如'^a'表示CTRL+a，’^%a'表示CTRL+ALT+a。
        {}： 大括号用来输入特殊字符本身和虚键，如‘{+}’输入加号，'{F1}'输入F1虚键，'{}}'表示输入'}'字符。
    2、ASCII字符：除了特殊字符需要｛｝来转义，其他ASCII码字符直接输入，
    3、Unicode字符：直接输入，如"测试"。
    4、虚键：
        {F1}, {F2},...{F12}
        {Tab},{CAPS},{ESC},{BKSP},{HOME},{INSERT},{DEL},{END},{ENTER}
        {PGUP},{PGDN},{LEFT},{RIGHT},{UP},{DOWN},{CTRL},{SHIFT},{ALT},{APPS}..
           注意：当使用联合键时，注意此类的问题,input_keys('^W')和input_keys('%w')，字母'w'的大小写产生的效果可能不一样
    """

    _keyclass = Key
    _pressedkey = None

    @staticmethod
    def _parse_keys(keystring):
        keys = []
        modifiers = []
        index = 0
        while index < len(keystring):
            c = keystring[index]
            index += 1

            # Escape or named key
            if c == "{":
                end_pos = keystring.find("}", index)
                if end_pos == -1:
                    raise KeyInputError('`}` not found')
                elif end_pos == index and keystring[end_pos+1] == '}':  # {}}
                    index += 2
                    code = '}'
                else:
                    code = keystring[index:end_pos]
                    index = end_pos + 1

                if code in list(_CODES.keys()):
                    key = _CODES[code]
                elif len(code) == 1:
                    key = code
                else:
                    raise KeyInputError("Code '%s' is not supported" % code)

            # unmatched "}"
            elif c == '}':
                raise KeyInputError('`}` should be preceeded by `{`')

            elif c in list(_MODIFIER_KEY_MAP.keys()):
                key = _MODIFIER_KEY_MAP[c]

            # so it is a normal character
            else:
                key = c
            if key in _MODIFIERS:
                modifiers.append(key)
            else:
                akey = Keyboard._keyclass(key)
                for mkey in modifiers:
                    akey.append_modifier_key(Keyboard._keyclass(mkey))
                modifiers = []
                keys.append(akey)
        for akey in modifiers:
            keys.append(Keyboard._keyclass(akey))

        return keys

    @staticmethod
    def input_keys(keys, interval=0.01):
        """模拟键盘输入字符串

        :type keys: utf-8 str or unicode
        :param keys: 键盘输入字符串,可输入组合键，如"{CTRL}{MENU}a"
        :type interval: number
        :param interval: 输入的字符和字符之间的暂停间隔。
        """
        keys = Keyboard._parse_keys(keys)
        for k in keys:
            k.input_key()
            time.sleep(interval)


    @staticmethod
    def post_keys(hwnd, keys, interval=0.01):
        """将字符串以窗口消息的方式发送到指定win32窗口。

        :type hwnd: number
        :param hwnd: windows窗口句柄
        :type keys: utf8 str 或者 unicode
        :param keys: 键盘输入字符串
        :type interval: number
        :param interval: 输入的字符和字符之间的暂停间隔。
        """
        keys = Keyboard._parse_keys(keys)

        for k in keys:
            k.post_key(hwnd)
            time.sleep(interval)

    @staticmethod
    def press_key(key):
        """按下某个键
        """
        if Keyboard._pressedkey:
            raise ValueError("尚有按键未释放,请先对按键进行释放,未释放的按键为: %s" % Keyboard._pressedkey)

        keys = Keyboard._parse_keys(key)
        if len(keys) != 1:
            raise ValueError("输入参数错误,只支持输入一个键,key: %s" % key)
        keys[0].press_key()
        Keyboard._pressedkey = key

    @staticmethod
    def release_key(key=None):
        """释放上一个被按下的键
        """
        if not Keyboard._pressedkey:
            raise Exception("没有可释放的按键")

        key = Keyboard._pressedkey
        keys = Keyboard._parse_keys(key)
        if len(keys) != 1:
            raise ValueError("输入参数错误,只支持输入一个键,key: %s" % key)
        keys[0].release_key()
        Keyboard._pressedkey = None

    @staticmethod
    def is_pressed(key):
        """是否被按下
        """
        keys = Keyboard._parse_keys(key)
        if len(keys) != 1:
            raise ValueError("输入参数错误,只支持输入一个键,key: %s" % key)
        return keys[0].is_pressed()

    @staticmethod
    def clear():
        """释放被按下的按键
        """
        if Keyboard._pressedkey:
            Keyboard.release_key()

    @staticmethod
    def is_troggled(key):
        """是否开启，如Caps Lock或Num Lock等
        """
        keys = Keyboard._parse_keys(key)
        if len(keys) != 1:
            raise ValueError("输入参数错误,只支持输入一个键,key: %s" % key)
        return keys[0].is_troggled()
