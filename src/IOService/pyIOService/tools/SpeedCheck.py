# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import time

LOG = logging.getLogger('IOService')

RECORD_INTERVAL_NUM = 100
PROCESS_IMG_TIME_INTERVAL = 50


class IOSpeedCheck(object):
    """
    Speed Check module, output the statistic result to log
    """

    def __init__(self):
        self.__imgRecvDict = {}
        self.__processImgDict = {}
        self.__imgRecvNum = 0
        self.__processActionNum = 0
        self.__processImgNum = 0
        self.__avgActionProcessTime = 0
        self.__avgImgProcessTime = 0

    def AddRecvImg(self, imgID):
        """
        When recv an img, call this
        :param imgID: frameSeq
        :return:
        """
        self.__imgRecvDict[imgID] = time.time()
        self.__imgRecvNum += 1

    def AddSendAction(self, imgID):
        """
        When send an action, call this
        :param imgID: frameSeq
        :return:
        """
        if imgID in self.__imgRecvDict:
            diffTime = time.time() - self.__imgRecvDict[imgID]
            self.__avgActionProcessTime = (self.__avgActionProcessTime * self.__processActionNum + diffTime) / (
                    self.__processActionNum + 1)
            self.__processActionNum += 1

            self.__processImgDict[imgID] = time.time()
            if len(self.__processImgDict) % PROCESS_IMG_TIME_INTERVAL == 0:
                sumTime = 0
                for key in self.__processImgDict:
                    sumTime += self.__processImgDict[key] - self.__imgRecvDict[key]

                self.__avgImgProcessTime = (self.__avgImgProcessTime * self.__processImgNum + sumTime) / (
                        self.__processImgNum + len(self.__processImgDict))
                self.__processImgNum += len(self.__processImgDict)
                self.__processImgDict = {}
                keyList = []
                for key in self.__imgRecvDict:
                    if key <= imgID:
                        keyList.append(key)
                for key in keyList:
                    del self.__imgRecvDict[key]

            if self.__processActionNum % RECORD_INTERVAL_NUM == 0:
                maxRecvImgID = self._GetMaxImgID()
                LOG.info("current_process_img_id:{}".format(imgID))
                LOG.info("recv max imgID:{}".format(maxRecvImgID))
                LOG.info("process action num:{a}, avg_action_process_time:{b}".
                         format(a=self.__processActionNum, b=self.__avgActionProcessTime))
                LOG.info("process_img num:{a}, avg_img_process_time:{b}".
                         format(a=self.__processImgNum, b=self.__avgImgProcessTime))

    def _GetMaxImgID(self):
        maxImgID = -1
        for imgID in self.__imgRecvDict:
            if maxImgID < imgID:
                maxImgID = imgID
        return maxImgID
