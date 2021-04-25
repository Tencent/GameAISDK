# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import cv2
import numpy as np
import os

__dir__ = os.path.dirname(os.path.abspath(__file__))


def _get_rotate_angle(x1, y1, x2, y2):
    epsilonTer = 1.0e-6
    nyPI = np.arccos(-1.0)
    dist = np.sqrt(x1 * x1 + y1 * y1)
    x1 /= dist
    y1 /= dist
    dist = np.sqrt(x2 * x2 + y2 * y2)
    x2 /= dist
    y2 /= dist
    dot = x1 * x2 + y1 * y2

    if np.abs(dot - 1.0) <= epsilonTer:
        angle = 0.0
    elif np.abs(dot + 1.0) <= epsilonTer:
        angle = nyPI
    else:
        angle = np.arccos(dot)
        cross = x1 * y2 - x2 * y1
        if cross < 0:
            angle = 2 * nyPI - angle

    degree = angle * 180.0 / nyPI

    return degree


def obtain_angle_image(radiusBig, radiusSmall, angleNum):
    angleImageList = []
    angleImageEdgeList = []
    successFlag = False

    if radiusBig < radiusSmall:
        return successFlag, angleImageList, angleImageEdgeList

    angleStep = 360. / angleNum
    circleImage = cv2.imread(os.path.join(__dir__, 'circle.png'))
    _, circleImage = cv2.threshold(circleImage, 100, 255, cv2.THRESH_BINARY)

    circleImageBig = cv2.resize(circleImage, (radiusBig * 2, radiusBig * 2))

    circleImageSmall = 255 - cv2.resize(circleImage, (radiusSmall * 2, radiusSmall * 2))

    ringImage = circleImageBig

    ringImageSmallTmp = ringImage[radiusBig - radiusSmall: radiusBig + radiusSmall,
                        radiusBig - radiusSmall: radiusBig + radiusSmall]

    ringImageSmallTmp[circleImageSmall == 0] = 0
    ringImage[radiusBig - radiusSmall: radiusBig + radiusSmall,
    radiusBig - radiusSmall: radiusBig + radiusSmall] = ringImageSmallTmp

    locRing = np.argwhere(ringImage == 255)
    angleImage = np.zeros([ringImage.shape[0], ringImage.shape[1]])
    for n in range(len(locRing)):
        locRingTmp = locRing[n]
        angle = _get_rotate_angle(0, -10, locRingTmp[0] - radiusBig, locRingTmp[1] - radiusBig)
        angleImage[locRingTmp[1], locRingTmp[0]] = (np.floor(
            (angle + angleStep / 2) / angleStep)) % angleNum + 1

    for n in range(angleNum):
        angleImageTmp = ((angleImage == (n + 1)) * 255).astype(np.uint8)
        angleImageTmpEdge = cv2.Canny(angleImageTmp, 50, 150)
        angleImageList.append(angleImageTmp)
        angleImageEdgeList.append(angleImageTmpEdge)

    return successFlag, angleImageList, angleImageEdgeList


def draw_angle(img, angleImg, color):
    for ch in range(3):
        img[:, :, ch][angleImg == 255] = color[ch]


def get_angle_image(radiusBig, radiusSmall, angleNum):
    angleImageEdgeListRet = []
    successFlag, angleImageList, angleImageEdgeList = obtain_angle_image(radiusBig, radiusSmall,
                                                                       angleNum)

    for angleImg in angleImageEdgeList:
        kernel = np.ones((3, 3), np.uint8)
        angleImg = cv2.dilate(angleImg, kernel, iterations=1)
        angleImageEdgeListRet.append(angleImg)

    return successFlag, angleImageList, angleImageEdgeListRet
