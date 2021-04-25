# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import traceback
import ctypes
import platform
import logging

import win32gui
import win32con
import cv2
import numpy as np

_is_windows = platform.platform().upper().startswith('WINDOWS')

logger = logging.getLogger('capture')

COLOR_BGR2GRAY = 6  # cv2.COLOR_BGR2GRAY
COLOR_RGB2GRAY = 7  # cv2.COLOR_RGB2GRAY
COLOR_BGRA2BGR = cv2.COLOR_BGRA2BGR
CAPTUREBLT = 0x40000000


class BITMAPINFOHEADER(ctypes.Structure):
    """BITMAP Info Header
    """
    _fields_ = [
        ('biSize', ctypes.c_uint32),
        ('biWidth', ctypes.c_long),
        ('biHeight', ctypes.c_long),
        ('biPlanes', ctypes.c_uint16),
        ('biBitCount', ctypes.c_uint16),
        ('biCompression', ctypes.c_uint32),
        ('biSizeImage', ctypes.c_uint32),
        ('biXPelsPerMeter', ctypes.c_long),
        ('biYPelsPerMeter', ctypes.c_long),
        ('biClrUsed', ctypes.c_uint32),
        ('biClrImportant', ctypes.c_uint32)
                ]


class RGBTRIPLE(ctypes.Structure):
    """RGB Define
    """
    _fields_ = [
        ('rgbBlue', ctypes.c_byte),
        ('rgbGreen', ctypes.c_byte),
        ('rgbRed', ctypes.c_byte),
        ('rgbReserved', ctypes.c_byte),
                ]


class BITMAPINFO(ctypes.Structure):
    """BITMAP Info
    """
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmciColors', RGBTRIPLE * 1)]


def roi(src, rc):
    l, t, r, b = rc
    h, w = src.shape[:2]
    if (r-l) >= w:
        return src
    if (b-t) >= h:
        return src

    return src[t:b, l:r].copy()


def reshape(src, w, h, channels):
    return np.reshape(src, (h, w, channels))


def from_buffer(buff, dtype='uint8'):
    return np.frombuffer(buff, dtype=dtype)


def cvt_color(src, flags=COLOR_BGR2GRAY):
    return cv2.cvtColor(src, flags)


def get_image(hwnd=None):
    if hwnd is None:
        hwnd = win32gui.GetDesktopWindow()

    try:
        dc = ctypes.windll.user32.GetWindowDC(hwnd)
        cdc = ctypes.windll.gdi32.CreateCompatibleDC(dc)

        l, t, r, b = win32gui.GetWindowRect(hwnd)
        w = r - l
        h = b - t

        lpBits = ctypes.c_void_p(0)
        bmiCapture = BITMAPINFO()
        bmiCapture.bmiHeader.biSize = ctypes.sizeof(BITMAPINFO)
        bmiCapture.bmiHeader.biWidth = w
        bmiCapture.bmiHeader.biHeight = h
        bmiCapture.bmiHeader.biPlanes = 1
        bmiCapture.bmiHeader.biBitCount = 32
        bmiCapture.bmiHeader.biCompression = win32con.BI_RGB
        bmiCapture.bmiHeader.biSizeImage = 0
        bmiCapture.bmiHeader.biXPelsPerMeter = 0
        bmiCapture.bmiHeader.biYPelsPerMeter = 0
        bmiCapture.bmiHeader.biClrUsed = 0
        bmiCapture.bmiHeader.biClrImportant = 0

        hbm_capture = ctypes.windll.gdi32.CreateDIBSection(cdc,
                                                          ctypes.byref(bmiCapture),
                                                          win32con.DIB_RGB_COLORS,
                                                          ctypes.byref(lpBits),
                                                          None,
                                                          0)

        cpy_bytes = 0
        image_data = None
        if hbm_capture:

            hbmOld = ctypes.windll.gdi32.SelectObject(cdc, hbm_capture)
            ctypes.windll.gdi32.BitBlt(cdc,
                                       0,
                                       0,
                                       w,
                                       h,
                                       dc,
                                       0,
                                       0,
                                       win32con.SRCCOPY|CAPTUREBLT)
            # realWidth = int((24*w+31)/32)*4
            # alloced_bytes = realWidth * h
            alloced_bytes = w * h * 4

            pBuf = ctypes.create_string_buffer(alloced_bytes)
            # A bottom-up DIB is specified by setting the height to a positive number,
            # while a top-down DIB is specified by setting the height to a negative number.
            bmiCapture.bmiHeader.biHeight = 0 - h
            cpy_bytes = ctypes.windll.gdi32.GetDIBits(cdc,
                                                      hbm_capture,
                                                      0,
                                                      h,
                                                      ctypes.byref(pBuf),
                                                      ctypes.byref(bmiCapture),
                                                      win32con.DIB_RGB_COLORS)

            if cpy_bytes == h:
                # 去掉X通道 。buff[start:end:step]
                pBuf2 = ctypes.create_string_buffer(h * w * 3)
                pBuf2[0::3] = pBuf[0::4]
                pBuf2[1::3] = pBuf[1::4]
                pBuf2[2::3] = pBuf[2::4]
                image_data = reshape(from_buffer(pBuf2), w, h, 3)

            ctypes.windll.gdi32.SelectObject(cdc, hbmOld)
            ctypes.windll.gdi32.DeleteObject(hbm_capture)

        ctypes.windll.gdi32.DeleteDC(cdc)
        ctypes.windll.gdi32.DeleteDC(dc)
        return image_data

    except ValueError:
        traceback.print_exc()
        logger.error(traceback.format_exc())
        return None
