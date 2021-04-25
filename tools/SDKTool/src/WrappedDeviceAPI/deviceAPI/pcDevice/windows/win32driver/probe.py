# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import re
import pythoncom
import win32gui
import win32con
import win32api
import win32process
import locale
import ctypes

from .keyboard import Keyboard

MAX_DEPTH = "MAXDEPTH"
INSTANCE = "INSTANCE"
os_encoding = locale.getdefaultlocale(None)[1]


def set_foreground_window(hwnd):
    fwnd = win32gui.GetForegroundWindow()
    if fwnd == hwnd:
        return
    if fwnd == 0:
        try:
            win32gui.SetForegroundWindow(hwnd)
            return
        except win32api.error:
            return

    ftid, _ = win32process.GetWindowThreadProcessId(fwnd)
    wtid, _ = win32process.GetWindowThreadProcessId(hwnd)

    ctypes.windll.user32.AttachThreadInput(wtid, ftid, True)
    st = time.time()
    while (time.time() - st) < 5:
        if win32gui.GetForegroundWindow() == hwnd:
            break
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        time.sleep(0.5)

    ctypes.windll.user32.AttachThreadInput(wtid, ftid, False)


class Win32Probe(object):

    def wait_for_element(self, locator, root=None, timeOut=20):
        st = time.time()
        while time.time() - st < timeOut:
            eles = self.search_element(locator, root)
            if eles:
                return eles
            time.sleep(0.5)
        return None

    def search_element(self, locator=None, root=None):
        if root is None:
            root = win32gui.GetDesktopWindow()
        if isinstance(root, int):
            pass
        elif hasattr(root, 'Id'):
            root = getattr(root, 'Id')
        else:
            raise TypeError('root type(%s) not support!' % type(root))

        if not win32gui.IsWindow(root):
            raise ValueError('Window(%s) is not valid' % root)

        if locator is None:
            return [root]

        if not hasattr(locator, 'loads'):
            raise TypeError('type(%s) not supported' % type(locator))
        qpath = locator.loads()
        foundCtrls, _ = self._recursive_find(root, qpath)
        return foundCtrls

    def _is_value_matched(self, expected_value, real_value, regular=False):
        """ 数值比较

        :param expected_value: 期待数值
        :param real_value: 真实数值
        :param regular: bool, 是否正则
        :return: True or False
        """
        # operator, exp_prop_value = props[propname]
        if isinstance(real_value, bool):
            if real_value != bool(expected_value):
                return False

        elif isinstance(real_value, int):
            if re.search('^0x', expected_value) is not None:
                n_expected_value = int(expected_value, 16)
            else:
                n_expected_value = int(expected_value)
            if real_value != n_expected_value:
                return False

        elif isinstance(expected_value, str):
            if not regular:
                is_matched = (real_value == expected_value)
            else:
                is_matched = True if re.search(expected_value, real_value) else False
            if not is_matched:
                return False
        else:
            raise Exception('不支持控件属性值类型：%s' % type(real_value))

        return True

    def _match_control(self, control, props):
        """控件是否匹配给定的属性

        :param control: 控件
        :param props: 要匹配的控件属性字典，如{'classname':['=', 'window']}
        """
        for key, value in props.items():
            try:
                act_prop_value = self.get_property(control, key)
                if act_prop_value is not None:
                    operator, exp_prop_value = value
                    is_regular = (operator != '==')
                    if self._is_value_matched(exp_prop_value, act_prop_value, is_regular):
                        continue
            except (pythoncom.com_error, ValueError):
                pass
            except win32gui.error as e:
                if e.winerror != 1400:  # 无效窗口句柄
                    raise e
                pass
            return False

        return True

    @staticmethod
    def __enum_childwin_callback(hwnd, hwnds):
        parent = hwnds[0]
        if parent is None:
            hwnds.append(hwnd)
        else:
            hparent = ctypes.windll.user32.GetAncestor(hwnd, win32con.GA_PARENT)
            if hparent == parent:
                hwnds.append(hwnd)

    def __get_children(self, hwnd):
        hwnds = []
        if hwnd == win32gui.GetDesktopWindow():
            hwnds.append(None)
            win32gui.EnumWindows(self.__enum_childwin_callback, hwnds)
        else:
            hwnds.append(hwnd)
            try:
                win32gui.EnumChildWindows(hwnd, self.__enum_childwin_callback, hwnds)
            except win32gui.error as e:
                if e.winerror == 0 or e.winerror == 1400:  # 1400是无效窗口错误
                    pass
                else:
                    raise e

        del hwnds[0]
        return hwnds

    def _recursive_find(self, root, qpath):
        """递归查找控件

        :param root: 根控件
        :param qpath: 解析后的qpath结构
        :return: 返回(found_controls, remain_qpath)， 其中found_controls是找到的控件，remain_qpath
        是未能找到控件时剩下的未能匹配的qpath。
        """
        qpath = qpath[:]
        props = qpath[0]
        props = dict((entry[0].upper(), entry[1]) for entry in list(props.items()))  # 使属性值大小写不敏感
        max_depth = 1  # 默认depth是1
        if MAX_DEPTH in props:
            max_depth = int(props[MAX_DEPTH][1])
            if max_depth <= 0:
                raise Exception("MaxDepth=%s应该>=1" % max_depth)
            del props[MAX_DEPTH]

        instance = None  # 默认没有index属性
        if INSTANCE in props:
            instance = int(props[INSTANCE][1])
            del props[INSTANCE]

        children = self.__get_children(root)
        found_child_controls = []
        for ctrl in children:
            if self._match_control(ctrl, props):
                found_child_controls.append(ctrl)

            if max_depth > 1:
                props_copy = props.copy()
                props_copy[MAX_DEPTH] = ['=', str(max_depth - 1)]
                _controls, _ = self._recursive_find(ctrl, [props_copy])
                found_child_controls += _controls

        if not found_child_controls:
            return [], qpath

        if instance is not None:
            try:
                found_child_controls = [found_child_controls[instance]]
            except IndexError:
                return [], qpath

        qpath.pop(0)

        if not qpath:  # 找到控件
            return found_child_controls, qpath

        # 在子孙中继续寻找
        found_ctrls = []
        error_path = qpath
        for child_control in found_child_controls:
            ctrls, remain_qpath = self._recursive_find(child_control, qpath)
            found_ctrls += ctrls
            if len(remain_qpath) < len(error_path):
                error_path = remain_qpath
        return found_ctrls, error_path

    def set_property(self, element, propertyName, value):
        validProperties = ['TEXT', 'FOCUS', 'ACTIVE']
        name = propertyName.upper()
        if name not in validProperties:
            raise ValueError('%s not supported!' % name)
        if name == 'FOCUS' and value is True:
            current_id = win32api.GetCurrentThreadId()
            target_id = win32process.GetWindowThreadProcessId(element)[0]
            win32process.AttachThreadInput(target_id, current_id, True)
            win32gui.SetFocus(element)
            win32process.AttachThreadInput(target_id, current_id, False)
        elif name == 'TEXT':
            pass
        elif name == 'active' and value is True:
            fwnd = win32gui.GetForegroundWindow()
            if fwnd == element:
                return
            if fwnd == 0:
                try:
                    win32gui.SetForegroundWindow(element)
                    return
                except win32api.error:
                    # 防止有菜单弹出导致异常
                    Keyboard.input_keys('{ESC}')
                    win32gui.SetForegroundWindow(element)
                    return

            ftid, _ = win32process.GetWindowThreadProcessId(fwnd)
            wtid, _ = win32process.GetWindowThreadProcessId(element)

            ctypes.windll.user32.AttachThreadInput(wtid, ftid, True)
            st = time.time()
            while (time.time()-st) < 5:
                if win32gui.GetForegroundWindow() == element:
                    break
                ctypes.windll.user32.SetForegroundWindow(element)
                time.sleep(0.5)

            ctypes.windll.user32.AttachThreadInput(wtid, ftid, False)

    def __encode_locale(self, s, encoding='utf-8'):
        try:
            return s.decode(os_encoding).encode(encoding)
        except UnicodeDecodeError:
            return s
        except AttributeError:
            return s

    def __get_text(self, hwnd):
        buf_size = 0
        try:
            textlength = ctypes.c_long(0)
            hr = ctypes.windll.user32.SendMessageTimeoutA(hwnd,
                                                          win32con.WM_GETTEXTLENGTH,
                                                          0, 0, 0, 200,
                                                          ctypes.byref(textlength))
            if hr == 0 or textlength.value < 0:
                return ""

            buf_size = textlength.value*2 + 1
        except win32gui.error:
            return ""

        if buf_size <= 0:
            return ""

        pybuffer = win32gui.PyMakeBuffer(buf_size)
        ret = win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, buf_size, pybuffer)
        if ret:
            address, _ = win32gui.PyGetBufferAddressAndLen(pybuffer)
            text = win32gui.PyGetString(address, ret)
            return text

        return ""

    def get_property(self, element, propertyName):
        valid_properties = ['TEXT', 'TYPE', 'CLASSNAME', 'VISIBLE', 'RECT', 'TOPLEVELWINDOW', 'ACTIVE']
        name = propertyName.upper()
        if name not in valid_properties:
            raise ValueError('%s not supported!' % name)

        if isinstance(element, int) and not win32gui.IsWindow(element):
            return None

        result = None
        if name == 'TEXT':
            result = self.__get_text(element)

        elif name in ['CLASSNAME', 'TYPE']:
            result = self.__encode_locale(win32gui.GetClassName(element))

        elif name == 'VISIBLE':
            result = True if win32gui.IsWindowVisible(element) == 1 else False

        elif name == 'RECT':
            result = win32gui.GetWindowRect(element)

        elif name == 'TOPLEVELWINDOW':
            if isinstance(element, int):
                style = win32gui.GetWindowLong(element, win32con.GWL_STYLE)
                if (style & win32con.WS_CHILDWINDOW) == 0:
                    return element

                if element == win32gui.GetDesktopWindow():
                    return None

                parent = element
                while (style & win32con.WS_CHILDWINDOW) > 0:
                    parent = win32gui.GetParent(parent)
                    style = win32gui.GetWindowLong(parent, win32con.GWL_STYLE)
                result = parent

        return result
