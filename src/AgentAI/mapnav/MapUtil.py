# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import math

MAP_OBSTACLE = 0
MAP_GROUND = 250
MAP_VISITED = 100

def IsSameDirection(srcAngle, destAngle, angleThr):
    """
    If diff of srcAngle and destAngle exceed the angleThr, return False.
    Otherwise return True
    """
    diffAngle = (360 + destAngle - srcAngle) % 360
    if (0 <= diffAngle <= angleThr) or (360 - angleThr <= diffAngle <= 360):
        return True

    return False

def IsReachDest(srcPoint, destPoint, distanceThr):
    """
    If distance from srcPoint to destPoint exceed distanceThr, return False.
    Otherwise return True
    """
    diffX = destPoint[0] - srcPoint[0]
    diffY = destPoint[1] - srcPoint[1]

    dist = math.sqrt(diffX * diffX + diffY * diffY)
    if dist < distanceThr:
        return True

    return False

def GetDestAngle(srcPoint, destPoint):
    """
    Calculate angle from srcPoint to destPoint
    """
    diffX = destPoint[0] - srcPoint[0]
    diffY = destPoint[1] - srcPoint[1]

    if diffY == 0:
        diffY == 0.01

    destAngle = 0

    if diffX >= 0 and diffY < 0:
        destAngle = math.atan(abs(diffX/diffY)) * 180 / 3.14
    elif diffX >= 0 and diffY > 0:
        destAngle = 180 - math.atan(abs(diffX/diffY)) * 180 / 3.14
    elif diffX < 0 and diffY > 0:
        destAngle = math.atan(abs(diffX/diffY)) * 180 / 3.14 + 180
    elif diffX < 0 and diffY < 0:
        destAngle = 360 - math.atan(abs(diffX/diffY)) * 180 / 3.14

    return int(destAngle)
