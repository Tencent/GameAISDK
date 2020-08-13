# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import base64

import cv2
import numpy as np

from common.Define import *

LOG = logging.getLogger('IOService')


def ImgDecode(imgData, sendType):
    """
    decode img data based on sendType
    :param imgData: img data(bytes)
    :param sendType: send type enum:
                                    RAW_IMG_SEND_TYPE
                                    BINARY_IMG_SEND_TYPE
                                    CV2_EN_DECODE_IMG_SEND_TYPE
                                    BASE_64_DECODE_IMG_SEND_TYPE
    :return:
    """
    img = imgData
    if sendType == RAW_IMG_SEND_TYPE:
        pass
    elif sendType == BINARY_IMG_SEND_TYPE:
        try:
            nparr = np.asarray(bytearray(imgData), dtype=np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as err:
            LOG.error('img decode err:{}'.format(err))
            LOG.error('sendType:{}'.format(sendType))
            img = None
    elif sendType == CV2_EN_DECODE_IMG_SEND_TYPE:
        try:
            nparr = np.fromstring(imgData, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as err:
            LOG.error('img decode err:{}'.format(err))
            LOG.error('sendType:{}'.format(sendType))
            img = None
    elif sendType == BASE_64_DECODE_IMG_SEND_TYPE:
        try:
            imgByte = base64.b64decode(imgData)
            nparr = np.fromstring(imgByte, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as err:
            LOG.error('img decode err:{}'.format(err))
            LOG.error('sendType:{}'.format(sendType))
            img = None
    return img
