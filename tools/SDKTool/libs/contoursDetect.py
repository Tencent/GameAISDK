# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import cv2
import numpy as np

def GetAngel(prePoint, cenPoint, point):
    x = np.array([cenPoint[0][0] - prePoint[0][0], cenPoint[0][1] - prePoint[0][1]])
    y = np.array([point[0][0] - cenPoint[0][0], point[0][1] - cenPoint[0][1]])

    Lx = np.sqrt(x.dot(x))
    Ly = np.sqrt(y.dot(y))

    cos_angel = x.dot(y) / (Lx * Ly)

    angel = np.arccos(cos_angel)
    angel = angel * 180 / np.pi
    return angel

def GetContour(contour):
    prePoint = None
    cenPoint = None
    newContour = list()
    count = 0
    for point in contour:
        if count % 20 != 1:
            count += 1
            continue

        count += 1
        if prePoint is None:
            prePoint = point
            newContour.append(prePoint[0])
            continue

        if cenPoint is None:
            cenPoint = point
            continue

        angel = GetAngel(prePoint, cenPoint, point)

        if angel < 8:
            prePoint = cenPoint
            cenPoint = point
        else:
            newContour.append(cenPoint[0])
            prePoint = cenPoint
            cenPoint = point

    return newContour

def GetMask(labels):
    width = labels.shape[1]
    height = labels.shape[0]

    mask = np.zeros([height, width], dtype="uint8")

    prePix = -1
    for x in range(width):
        for y in range(height):
            if x == 0:
                prePix = labels[y, x]
            else:
                if labels[y, x] != prePix:
                    mask[y, x] = 255
                    prePix = labels[y, x]

    for y in range(height):
        for x in range(width):
            if y == 0:
                prePix = labels[y, x]
            else:
                if labels[y, x] != prePix:
                    mask[y, x] = 255
                    prePix = labels[y, x]

    return mask