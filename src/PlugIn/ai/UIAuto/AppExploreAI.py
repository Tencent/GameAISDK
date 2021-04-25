# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import cv2
import os
import sys
import threading
import time
from queue import Queue
import numpy as np
import json
import platform

from aimodel.AIModel import AIModel
from util import util


_is_windows_system = platform.platform().lower().startswith('window')
_is_linux_system = platform.platform().lower().startswith('linux')
if _is_windows_system:
    from .windows.Coverage import Coverage
    from .windows.Utils.Image import GetLocalImage, ResizeImage, MatchImage, MatchImageWithRect, MatchMask, IsBlackImage
    from .windows.Utils.Rectangle import IOU
    pluginPath = './PlugIn/ai/UIAuto/windows/DetectRefineNet'
elif _is_linux_system:
    from .ubuntu.Coverage import Coverage
    from .ubuntu.Utils.Image import GetLocalImage, ResizeImage, MatchImage, MatchImageWithRect, MatchMask, IsBlackImage
    from .ubuntu.Utils.Rectangle import IOU
    pluginPath = './PlugIn/ai/UIAuto/ubuntu/DetectRefineNet'
else:
    raise Exception('system is not support!')


# multi-thread setting
THREAD_NUMBER = 8

# get state
STATE_INTERVAL_TIME = 0.50  # second
STATE_STABLE_THRESHOLD = 0.95

# get button list
BUTTON_NAME_LIST = ['close', 'other', 'return', 'tag']
BUTTON_MIN_WIDTH = 15
BUTTON_MIN_HEIGHT = 15

# process no button
MAX_NO_BUTTON_TIMES = 5

# get group ID
GET_GROUP_ID_THRESHOLD = 0.90
IMAGE_WEIGHT = 0.50
MASK_WEIGHT = 0.50

# get scene ID
GET_SCENE_ID_THRESHOLD = 0.95

# image match
IMAGE_RESIZE_RATIO = 0.40

# process stuck
MAX_STUCK_TIMES = 20

UI_AUTO_CFG = "cfg/task/agent/UiAutoExplore.json"


class AI(AIModel):
    def __init__(self):
        AIModel.__init__(self)
        self.__agentEnv = None
        self.__groupList = list()
        self.__noButtonCount = 0
        self.__stuckCount = 0
        self.__clickCount = 0
        self.__prevGroupID = None
        self.__prevSceneID = None
        self.__prevButtonID = None
        self.__nextGroupID = None
        self.__nextSceneID = None

        # UI explore setting
        self.__maxClickNumber = 2000
        self.__waitTime = 2
        self.__graphFolder = None
        self.__actionFolder = None
        self.__explorePath = None

        # button detection setting
        self.__modelType = None
        self.__detector = None
        self.__mask = None

        # UI coverage setting
        self.__computeCoverage = True
        self.__sampleFolder = None
        self.__orbThreshold = 0.10

        # debug setting
        self.__showButton = False
        self.__showCostTime = True
        self.__showImageRatio = 1.0
        self.__testGetState = False

    def Init(self, agentEnv):
        self.__agentEnv = agentEnv
        try:
            ui_auto_cfg_path = util.ConvertToSDKFilePath(UI_AUTO_CFG)
            self.logger.info('read cfg path:%s' % ui_auto_cfg_path)
            uiAutoCfg = json.load(open(ui_auto_cfg_path, 'r'))
        except Exception as err:
            self.logger.error('cannot read {}, error: {}'.format(UI_AUTO_CFG, err))
            return False

        # UI explore setting
        self.__maxClickNumber = uiAutoCfg['UiExplore'].get('MaxClickNumber')
        self.__waitTime = uiAutoCfg['UiExplore'].get('WaitTime')

        outputFolder = os.path.join(util.ConvertToSDKFilePath(''), uiAutoCfg['UiExplore'].get('OutputFolder'))

        if not os.path.exists(outputFolder):
            os.makedirs(outputFolder)

        self.__graphFolder = os.path.join(outputFolder, 'Graph')
        if not os.path.exists(self.__graphFolder):
            os.makedirs(self.__graphFolder)

        self.__actionFolder = os.path.join(outputFolder, 'Action')
        if not os.path.exists(self.__actionFolder):
            os.makedirs(self.__actionFolder)

        self.__explorePath = os.path.join(outputFolder, 'explore_path.txt')

        ret = self._InitDetector(uiAutoCfg)
        if ret is False:
            self.logger.error('initialize Detector failed')
            return False

        # UI coverage setting
        self.__computeCoverage = uiAutoCfg['UiCoverage'].get('ComputeCoverage')
        self.__sampleFolder = util.ConvertToSDKFilePath(uiAutoCfg['UiCoverage'].get('SampleFolder'))
        self.__orbThreshold = uiAutoCfg['UiCoverage'].get('ORBThreshold')

        # debug setting
        if uiAutoCfg.get('Debug', '') != '':
            self.__showButton = uiAutoCfg['Debug'].get('ShowButton')
            self.__showCostTime = uiAutoCfg['Debug'].get('ShowCostTime')
            self.__showImageRatio = uiAutoCfg['Debug'].get('ShowImageRatio')
            self.__testGetState = uiAutoCfg['Debug'].get('TestGetState')

        return True

    def Finish(self):
        pass

    def OnEpisodeStart(self):
        pass

    def TestOneStep(self):
        # ---------------- get state ------------------------------------------------------------ #
        if self.__showCostTime:
            startTime = time.time()

        image, buttonList = self._GetState()

        if self.__showCostTime:
            endTime = time.time()
            self.logger.info('get state time: {} s'.format(round((endTime - startTime), 4)))

        if image is None:
            self.logger.info('UI is switching')
            return True

        if self.__testGetState:
            self.logger.info('test get state')
            return True
        # --------------------------------------------------------------------------------------- #

        # ---------------- process no button ---------------------------------------------------- #
        # check no button
        if len(buttonList) == 0:
            # count no button
            self.__noButtonCount += 1
            self.logger.info('there is no button in the image')

            # if the count of no button is more than max times, click randomly
            if self.__noButtonCount >= MAX_NO_BUTTON_TIMES:
                self._RandomClick(image.shape[1], image.shape[0])
            return True
        else:
            # clear counter
            self.__noButtonCount = 0
        # --------------------------------------------------------------------------------------- #

        groupID = None
        sceneID = None

        # ---------------- get group ID --------------------------------------------------------- #
        if self.__showCostTime:
            startTime = time.time()

        if groupID is None:
            groupID = self._GetGroupID(image, buttonList)

        # if there is no group id, add a new group
        if groupID is None:
            groupID = self._AddGroup()

        if self.__showCostTime:
            endTime = time.time()
            self.logger.info('get group id time: {} s'.format(round((endTime - startTime), 4)))
        # --------------------------------------------------------------------------------------- #

        # ---------------- get scene ID ----------------------------------------------- --------- #
        if self.__showCostTime:
            startTime = time.time()

        if not sceneID:
            sceneID = self._GetSceneID(groupID, image, buttonList)

        # if there is no scene id, add a new scene and update table list in the group
        if not sceneID:
            sceneID = self._AddScene(groupID, image, buttonList)
            self._UpdateTableList(groupID)
            self._UpdateButtonInfo(groupID)

        if self.__showCostTime:
            endTime = time.time()
            self.logger.info('get scene id time: {} s'.format(round((endTime - startTime), 4)))
        # --------------------------------------------------------------------------------------- #

        self.logger.info('group id: {} -------- scene id: {}'.format(groupID, sceneID))

        # ---------------- process stuck -------------------------------------------------------- #
        # check stuck
        if self.__prevGroupID == groupID and self.__prevSceneID == sceneID:
            # count stuck
            self.__stuckCount += 1

            # if stuck more than max stuck times, click randomly
            if self.__stuckCount > MAX_STUCK_TIMES:
                self.logger.info('game stuck')

                self._RandomClick(image.shape[1], image.shape[0])
                return True
        else:
            # clear counter
            self.__stuckCount = 0
        # --------------------------------------------------------------------------------------- #

        buttonID = self._GetButtonID(groupID, sceneID)

        self._ClickButton(groupID, sceneID, buttonID)

        # ---------------- update --------------------------------------------------------------- #
        startTime = time.time()
        self._Update(groupID, sceneID, buttonID, image)
        endTime = time.time()
        costTime = endTime - startTime

        if self.__showCostTime:
            self.logger.info('update time: {} s'.format(round(costTime, 4)))

        if costTime < self.__waitTime:
            time.sleep(self.__waitTime - costTime)
        return True

    def _InitDetector(self, uiAutoCfg):
        self.__modelType = uiAutoCfg['ButtonDetection'].get('ModelType')
        if self.__modelType != 'Yolov3' and self.__modelType != 'RefineNet':
            self.logger.error('unknown model type: {}'.format(self.__modelType))
            return False

        sys.path.append(pluginPath)
        if self.__modelType == 'Yolov3':
            if _is_windows_system:
                from .windows.Yolov3.OpencvYolov3 import OpencvYolov3 as Yolov3
            else:
                from .ubuntu.Yolov3.OpencvYolov3 import OpencvYolov3 as Yolov3

            param = dict()
            param['cfgPath'] = util.ConvertToSDKFilePath(uiAutoCfg['ButtonDetection'].get('CfgPath'))
            param['weightsPath'] = util.ConvertToSDKFilePath(uiAutoCfg['ButtonDetection'].get('WeightsPath'))
            param['namesPath'] = util.ConvertToSDKFilePath(uiAutoCfg['ButtonDetection'].get('NamesPath'))
            param['threshold'] = uiAutoCfg['ButtonDetection'].get('Threshold')

            self.__detector = Yolov3()
            ret = self.__detector.Init(param)
            if ret is False:
                self.logger.error('initialize Yolov3 failed')
                return False

        if self.__modelType == 'RefineNet':
            if _is_windows_system:
                from .windows.DetectRefineNet import DetectRefineNet
            else:
                from .ubuntu.DetectRefineNet import DetectRefineNet
            pthModelPath = util.ConvertToSDKFilePath(uiAutoCfg['ButtonDetection'].get('PthModelPath'))
            threshold = uiAutoCfg['ButtonDetection'].get('Threshold')

            labels = ('__background__', 'return', 'close', 'tag', 'other')
            self.__detector = DetectRefineNet.DetectRefineNet(labels, img_dim=320, num_classes=5, obj_thresh=threshold,
                                                              nms_thresh=0.10,
                                                              version='Refine_hc2net_version3',
                                                              onnx_model='',
                                                              trained_model=pthModelPath,
                                                              nmsType='normal',
                                                              platform='pytorch')
            if not self.__detector:
                self.logger.error('initialize RefineNet failed')
                return False

        if uiAutoCfg['ButtonDetection'].get('MaskPath', '') != '':
            maskPath = util.ConvertToSDKFilePath(uiAutoCfg['ButtonDetection'].get('MaskPath'))
            maskImage = cv2.imread(maskPath)
            if not maskImage:
                self.logger.error('cannot read mask image in {}'.format(maskPath))
                return False

            grayImage = cv2.cvtColor(maskImage, cv2.COLOR_BGR2GRAY)
            _, self.__mask = cv2.threshold(grayImage, 127, 255, 0)
        else:
            self.__mask = None
        return True

    def _GetState(self):
        # get one image as image1
        self.__agentEnv.GetState()  # clear tbus
        state1 = self.__agentEnv.GetState()  # get current state
        image1 = state1['image']

        # check image1
        if IsBlackImage(image1):
            self.logger.info('image1 is black image')
            return None, []

        # get button list in image1
        startTime = time.time()
        buttonList = self._GetButtonList(image1)
        endTime = time.time()
        costTime = endTime - startTime

        if costTime < STATE_INTERVAL_TIME:
            time.sleep(STATE_INTERVAL_TIME - costTime)

        # get another image as image2
        self.__agentEnv.GetState()  # clear tbus
        state2 = self.__agentEnv.GetState()  # get current state
        image2 = state2['image']

        # check image2
        if IsBlackImage(image2):
            self.logger.info('image2 is black image')
            return None, []

        if len(buttonList) == 0:
            # if no button, match image1 and image2 directly
            resize1 = ResizeImage(image1, IMAGE_RESIZE_RATIO)
            resize2 = ResizeImage(image2, IMAGE_RESIZE_RATIO)
            score = MatchImage(resize1, resize2)

        else:
            # match image1 and image2 in button locations
            tmp = 0.0
            for button in buttonList:
                local1 = GetLocalImage(image1, [button['x'], button['y'], button['w'], button['h']])
                local2 = GetLocalImage(image2, [button['x'], button['y'], button['w'], button['h']])
                tmp += MatchImage(local1, local2)

            score = tmp / len(buttonList)

        if score >= STATE_STABLE_THRESHOLD:
            return image1, buttonList
        else:
            self.logger.info('image1 does not match image2')
            # cv2.imwrite(str(startTime) + '.jpg', image1)
            # cv2.imwrite(str(endTime) + '.jpg', image2)
            return None, []

    def _GetButtonList(self, image):
        buttonList = list()

        # add mask on image
        if self.__mask:
            detImage = cv2.bitwise_and(image, image, mask=self.__mask)
        else:
            detImage = image.copy()

        startTime = time.time()
        result = {}
        # button detection using Yolov3
        if self.__modelType == 'Yolov3':
            result = self.__detector.Run(detImage)
        # button detection using RefineNet
        elif self.__modelType == 'RefineNet':
            result = self.__detector.predict(detImage)
        else:
            self.logger.info('modelType:{} error'.format(self.__modelType))
            return buttonList

        endTime = time.time()
        self.logger.info('button detection time: {} s'.format(round(endTime - startTime, 4)))

        # get button list from result
        if result['flag']:
            id = 0
            for bbox in result['bboxes']:
                # exclude buttons not in name list
                if bbox['name'] not in BUTTON_NAME_LIST:
                    continue

                # exclude buttons with small size
                if bbox['w'] < BUTTON_MIN_WIDTH or bbox['h'] < BUTTON_MIN_HEIGHT:
                    continue

                # consider tag as other
                if bbox['name'] == 'tag':
                    bbox['name'] = 'other'

                button = dict()
                button['buttonID'] = id
                button['x'] = bbox['x']
                button['y'] = bbox['y']
                button['w'] = bbox['w']
                button['h'] = bbox['h']
                button['name'] = bbox['name']
                button['score'] = bbox['score']

                button['count'] = 0  # click count
                button['type'] = None  # private or public
                button['tableID'] = None
                button['nextGroupID'] = None
                button['nextSceneID'] = None

                buttonList.append(button)
                id += 1

        if self.__showButton:
            self._ShowButtonList(image, buttonList)
        return buttonList

    def _ShowButtonList(self, image, buttonList):
        showImage = image.copy()

        for button in buttonList:
            pt1 = (button['x'], button['y'])
            pt2 = (button['x'] + button['w'], button['y'] + button['h'])
            cv2.rectangle(showImage, pt1, pt2, (0, 0, 255), 2)

            pt = (button['x'], button['y'] + button['h'] // 2)
            cv2.putText(showImage, button['name'], pt, cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

        if self.__showImageRatio != 1.0:
            height, width = showImage.shape[:2]
            showImage = cv2.resize(showImage,
                                   (int(width * self.__showImageRatio), int(height * self.__showImageRatio)))

        cv2.imshow('ShowButton', showImage)
        cv2.waitKey(1)
        return True

    def _GetGroupID(self, image, buttonList):
        numGroup = len(self.__groupList)

        # if group list is empty, return none
        if numGroup == 0:
            return None

        # generate matching image and matching mask
        mask = self._GenerateMask(image, buttonList)
        matchMask = ResizeImage(mask, IMAGE_RESIZE_RATIO)
        matchImage = ResizeImage(image, IMAGE_RESIZE_RATIO)

        # match groups using multi-threads
        inputQueue = Queue()
        outputQueue = Queue()

        # fill matching data in input queue
        for id in range(numGroup):
            group = self.__groupList[id]
            inputQueue.put([id, group])

        # set and start multi-threads
        threadList = list()
        for i in range(THREAD_NUMBER):
            thread = threading.Thread(target=self._MatchInGroups, args=(inputQueue, matchImage, matchMask, outputQueue))
            thread.start()
            threadList.append(thread)

        for thread in threadList:
            thread.join()

        # get matching score from output queue
        groupID = None
        maxScore = 0.0
        while not outputQueue.empty():
            [id, score] = outputQueue.get()
            if maxScore < score:
                groupID = id
                maxScore = score

        if maxScore > GET_GROUP_ID_THRESHOLD:
            return groupID
        else:
            return None

    def _GenerateMask(self, image, buttonList):
        mask = np.zeros((image.shape[0], image.shape[1]), dtype='uint8')

        for button in buttonList:
            sx = button['x']
            ex = button['x'] + button['w']
            sy = button['y']
            ey = button['y'] + button['h']

            mask[sy:ey, sx:ex] = np.ones((button['h'], button['w']), dtype='uint8') * 255

        return mask

    def _MatchInGroups(self, inputQueue, image, mask, outputQueue):
        while True:
            if not inputQueue.empty():
                [id, group] = inputQueue.get()
                score = self._MatchInGroup(group, image, mask)
                outputQueue.put([id, score])
            else:
                break

    def _MatchInGroup(self, group, image, mask):
        maxScore = 0.0
        for scene in group['sceneList']:
            imageScore = MatchImage(image, scene['matchImage'])
            maskScore = MatchMask(mask, scene['matchMask'])
            score = IMAGE_WEIGHT * imageScore + MASK_WEIGHT * maskScore
            if maxScore < score:
                maxScore = score
        return maxScore

    def _AddGroup(self):
        groupID = len(self.__groupList)

        group = dict()
        group['groupID'] = groupID
        group['sceneList'] = list()
        group['tableList'] = list()

        self.__groupList.append(group)
        self.logger.info('add a new group {}'.format(groupID))
        return groupID

    def _GetSceneID(self, groupID, image, buttonList):
        group = self.__groupList[groupID]
        numScene = len(group['sceneList'])

        # if scene list is empty, return none
        if numScene == 0:
            return None

        # match scenes
        sceneID = None
        for i in range(numScene):
            scene = group['sceneList'][i]
            flag = self._MatchButtonInScene(image, buttonList, scene['image'], scene['buttonList'])
            if flag:
                sceneID = i
                break
        return sceneID

    def _MatchButtonInScene(self, image1, buttonList1, image2, buttonList2):
        # use one button list to match image1 and image2
        flag1 = True
        for b1 in buttonList1:
            local1 = GetLocalImage(image1, [b1['x'], b1['y'], b1['w'], b1['h']])
            local2 = GetLocalImage(image2, [b1['x'], b1['y'], b1['w'], b1['h']])
            score = MatchImage(local1, local2)

            if score < GET_SCENE_ID_THRESHOLD:
                flag1 = False
                break

        if not flag1:
            return False

        # use another button list to match image1 and image2
        flag2 = True
        for b2 in buttonList2:
            local1 = GetLocalImage(image1, [b2['x'], b2['y'], b2['w'], b2['h']])
            local2 = GetLocalImage(image2, [b2['x'], b2['y'], b2['w'], b2['h']])
            score = MatchImage(local1, local2)

            if score < GET_SCENE_ID_THRESHOLD:
                flag2 = False
                break

        if not flag2:
            return False
        return True

    def _AddScene(self, groupID, image, buttonList):
        sceneList = self.__groupList[groupID]['sceneList']
        sceneID = len(sceneList)

        scene = dict()
        scene['sceneID'] = sceneID
        scene['image'] = image
        scene['buttonList'] = buttonList

        # generate matching image and matching mask
        mask = self._GenerateMask(image, buttonList)
        scene['matchMask'] = ResizeImage(mask, IMAGE_RESIZE_RATIO)
        scene['matchImage'] = ResizeImage(image, IMAGE_RESIZE_RATIO)

        scene['save'] = True

        sceneList.append(scene)
        self.logger.info('add a new scene in group {}'.format(groupID))
        return sceneID

    def _RandomClick(self, width, height, gridSize=20):
        col = np.random.randint(width // gridSize)
        row = np.random.randint(height // gridSize)

        action = dict()
        action['type'] = 'click'
        action['x'] = np.random.randint(col * gridSize + gridSize // 2)
        action['y'] = np.random.randint(row * gridSize + gridSize // 2)

        if self.__mask:
            if self.__mask[action['y'], action['x']] == 0:
                return True

        self.logger.info('random click ({}, {})'.format(action['x'], action['y']))
        self.__agentEnv.DoAction(action)
        time.sleep(0.5)
        return True

    def _UpdateTableList(self, groupID):
        group = self.__groupList[groupID]
        scene = group['sceneList'][-1]
        buttonList = scene['buttonList']

        if len(group['tableList']) == 0:
            for button in buttonList:
                self._AddTable(group, scene, button)

            return True

        for button in buttonList:
            buttonRect = [button['x'], button['y'], button['w'], button['h']]

            id = 0
            maxOverlap = -1.0
            for table in group['tableList']:
                tableRect = [table['x'], table['y'], table['w'], table['h']]
                overlap = IOU(buttonRect, tableRect)
                if overlap > maxOverlap:
                    tableID = id
                    maxOverlap = overlap

                id += 1

            if maxOverlap > 0.5:
                group['tableList'][tableID]['table'].append(
                    {'sceneID': scene['sceneID'], 'buttonID': button['buttonID']})
            else:
                self._AddTable(group, scene, button)
        return True

    def _AddTable(self, group, scene, button):
        table = dict()
        table['tableID'] = len(group['tableList'])
        table['image'] = scene['image']
        table['name'] = button['name']
        table['count'] = 0
        table['x'] = button['x']
        table['y'] = button['y']
        table['w'] = button['w']
        table['h'] = button['h']
        table['nextGroupID'] = None
        table['nextSceneID'] = None

        table['table'] = list()  # lookup table
        table['table'].append({'sceneID': scene['sceneID'], 'buttonID': button['buttonID']})
        group['tableList'].append(table)
        return True

    def _MatchTag(self, tag, scene, button):
        image1 = tag['image']
        rect1 = [tag['x'], tag['y'], tag['w'], tag['h']]

        image2 = scene['image']
        rect2 = [button['x'], button['y'], button['w'], button['h']]

        score = MatchImageWithRect(image1, rect1, image2, rect2)
        return score

    def _UpdateButtonInfo(self, groupID):
        group = self.__groupList[groupID]
        sceneNum = len(group['sceneList'])

        for table in group['tableList']:
            count = 0
            nextGroupID = None
            nextSceneID = None
            for item in table['table']:
                sID = item['sceneID']
                bID = item['buttonID']
                button = group['sceneList'][sID]['buttonList'][bID]

                if button['count'] > count:
                    count = button['count']

                if button['nextGroupID'] and button['nextSceneID']:
                    nextGroupID = button['nextGroupID']
                    nextSceneID = button['nextSceneID']

            table['count'] = count
            table['nextGroupID'] = nextGroupID
            table['nextSceneID'] = nextSceneID

            tableNum = len(table['table'])
            for item in table['table']:
                sID = item['sceneID']
                bID = item['buttonID']
                button = group['sceneList'][sID]['buttonList'][bID]

                button['tableID'] = table['tableID']
                button['count'] = table['count']

                if not button['nextGroupID']:
                    button['nextGroupID'] = table['nextGroupID']

                if not button['nextSceneID']:
                    button['nextSceneID'] = table['nextSceneID']

                if tableNum == sceneNum:
                    button['type'] = 'public'
                else:
                    button['type'] = 'private'
        return True

    def _GetButtonID(self, groupID, sceneID):
        buttonList = self.__groupList[groupID]['sceneList'][sceneID]['buttonList']

        if len(buttonList) == 1:
            return 0

        # find one 0-count other button in the current scene
        buttonID = self._FindButtonID(buttonList, nameList=['other'])
        if buttonID:
            return buttonID

        # find one tag button with 0-count other button in the next scenes
        for button in buttonList:
            if button['name'] == 'other':
                nextGroupID = button['nextGroupID']
                nextSceneID = button['nextSceneID']

                if not nextGroupID or not nextSceneID:
                    continue

                nextButtonList = self.__groupList[nextGroupID]['sceneList'][nextSceneID]['buttonList']
                if self._FindButtonID(nextButtonList, nameList=['other']):
                    buttonID = button['buttonID']
                    break

        if buttonID:
            return buttonID

        # find one button with count 0 in the current scene
        buttonID = self._FindButtonID(buttonList)
        if buttonID:
            return buttonID

        # find one button with count 0 in the next scenes
        for button in buttonList:
            nextGroupID = button['nextGroupID']
            nextSceneID = button['nextSceneID']

            if not nextGroupID or not nextSceneID:
                continue

            nextButtonList = self.__groupList[nextGroupID]['sceneList'][nextSceneID]['buttonList']
            if self._FindButtonID(nextButtonList):
                buttonID = button['buttonID']
                break

        if buttonID:
            return buttonID

        # if there is no button with count 0 in the current, next and next-next scenes, randomly select
        buttonID = self._RandomGetButtonID(buttonList)
        return buttonID

    def _FindButtonID(self, buttonList, nameList=None, count=0):
        buttonIDList = list()
        for button in buttonList:
            if not nameList:
                if button['count'] == count:
                    buttonIDList.append(button['buttonID'])

            else:
                if button['name'] in nameList and button['count'] == count:
                    buttonIDList.append(button['buttonID'])

        if len(buttonIDList) == 0:
            return None

        buttonID = buttonIDList[np.random.randint(len(buttonIDList))]
        return buttonID

    def _RandomGetButtonID(self, buttonList):
        # buttonID = np.random.randint(len(buttonList))

        total = 0
        scoreList = list()
        for button in buttonList:
            if button['name'] == 'return' or button['name'] == 'close':
                score = 3
            else:
                score = 1

            scoreList.append(score)
            total = score + total

        i = 0
        prop = np.zeros([1, len(buttonList)])
        for score in scoreList:
            prop[0, i] = score / total
            i = i + 1

        buttonID = np.random.choice(range(prop.shape[1]), p=prop.ravel())
        return buttonID

    def _ClickButton(self, groupID, sceneID, buttonID):
        button = self.__groupList[groupID]['sceneList'][sceneID]['buttonList'][buttonID]

        action = dict()
        action['type'] = 'click'
        action['x'] = button['x'] + button['w'] // 2
        action['y'] = button['y'] + button['h'] // 2

        self.__agentEnv.DoAction(action)
        return True

    def _Update(self, groupID, sceneID, buttonID, image):
        self._AddButtonCount(groupID, sceneID, buttonID)
        self._AddButtonNext(groupID, sceneID, buttonID)
        self._UpdateButtonInfo(groupID)

        if self.__prevGroupID:
            self._UpdateButtonInfo(self.__prevGroupID)

        with open(self.__explorePath, 'a') as f:
            f.write(str(groupID) + ' ' + str(sceneID) + ' ' + str(buttonID) + '\n')
        # save current information
        self.__prevGroupID = groupID
        self.__prevSceneID = sceneID
        self.__prevButtonID = buttonID

        self.__nextGroupID = self.__groupList[groupID]['sceneList'][sceneID]['buttonList'][buttonID]['nextGroupID']
        self.__nextSceneID = self.__groupList[groupID]['sceneList'][sceneID]['buttonList'][buttonID]['nextSceneID']

        # count click
        self.__clickCount += 1
        self.logger.info('total click count: {}'.format(self.__clickCount))

        # save graph (image and json)
        self._SaveGraph(self.__graphFolder)

        # save explore action sequence
        button = self.__groupList[groupID]['sceneList'][sceneID]['buttonList'][buttonID]
        self._SaveAction(self.__actionFolder, image, button)

        # if click number is more than max click number, end UI explore
        if self.__clickCount >= self.__maxClickNumber:
            self.__agentEnv.start = False
            self.__agentEnv.over = True

            if self.__computeCoverage:
                Coverage(self.__sampleFolder, self.__graphFolder, self.__orbThreshold)
        return True

    def _AddButtonCount(self, groupID, sceneID, buttonID):
        group = self.__groupList[groupID]
        scene = group['sceneList'][sceneID]
        button = scene['buttonList'][buttonID]

        button['count'] += 1

        if button['type'] == 'private':
            scene['save'] = True
        else:
            for s in group['sceneList']:
                s['save'] = True
        return True

    def _AddButtonNext(self, groupID, sceneID, buttonID):
        if not self.__prevGroupID or not self.__prevSceneID or not self.__prevButtonID:
            return True

        # update next group id and next scene id in the previous button
        group = self.__groupList[self.__prevGroupID]
        scene = group['sceneList'][self.__prevSceneID]
        button = scene['buttonList'][self.__prevButtonID]

        button['nextGroupID'] = groupID
        button['nextSceneID'] = sceneID

        if button['type'] == 'private':
            scene['save'] = True
        else:
            for s in group['sceneList']:
                s['save'] = True
        return True

    def _SaveGraph(self, saveFolder):
        for groupID in range(len(self.__groupList)):
            group = self.__groupList[groupID]

            for sceneID in range(len(group['sceneList'])):
                scene = group['sceneList'][sceneID]
                if scene['save']:
                    self._SaveImage(saveFolder, groupID, sceneID)
                    self._SaveJson(saveFolder, groupID, sceneID)
                    scene['save'] = False
        return True

    def _SaveImage(self, saveFolder, groupID, sceneID):
        scene = self.__groupList[groupID]['sceneList'][sceneID]

        filename = 'group' + str(groupID) + '_scene' + str(sceneID) + '.jpg'
        imagePath = os.path.join(saveFolder, filename)
        cv2.imwrite(imagePath, scene['image'])

        # if not os.path.exists(imagePath):
        #     cv2.imwrite(imagePath, scene['image'])

        drawImage = scene['image'].copy()

        for button in scene['buttonList']:
            pt1 = (button['x'], button['y'])
            pt2 = (button['x'] + button['w'], button['y'] + button['h'])
            if button['type'] == 'public':
                cv2.rectangle(drawImage, pt1, pt2, (0, 0, 255), 2)  # red

            if button['type'] == 'private':
                cv2.rectangle(drawImage, pt1, pt2, (0, 255, 0), 2)  # green

            if button['count'] > 0:
                x = button['x'] + button['w'] // 2
                y = button['y'] + button['h'] // 2
                cv2.circle(drawImage, (x, y), 5, (0, 0, 255), 3)

        filename = 'group' + str(groupID) + '_scene' + str(sceneID) + '.png'
        imagePath = os.path.join(saveFolder, filename)
        cv2.imwrite(imagePath, drawImage)
        return True

    def _SaveJson(self, saveFolder, groupID, sceneID):
        filename = 'group' + str(groupID) + '_scene' + str(sceneID) + '.json'

        jsonData = dict()
        jsonData['fileName'] = filename.replace('json', 'jpg')
        jsonData['scene'] = ''
        jsonData['labels'] = list()

        scene = self.__groupList[groupID]['sceneList'][sceneID]
        for button in scene['buttonList']:
            label = dict()
            label['label'] = button['name']
            label['name'] = button['name']
            label['clickNum'] = int(button['count'])
            label['x'] = button['x']
            label['y'] = button['y']
            label['w'] = button['w']
            label['h'] = button['h']
            if not button['nextGroupID']:
                label['nextUI'] = ''
            else:
                label['nextUI'] = 'group' + str(button['nextGroupID']) + '_' + 'scene' + \
                                  str(button['nextSceneID']) + '.jpg'
            jsonData['labels'].append(label)

        jsonPath = os.path.join(saveFolder, filename)
        with open(jsonPath, 'w') as f:
            json.dump(jsonData, f, indent=4)
        return True

    def _SaveAction(self, saveFolder, image, button):
        filename = str(self.__clickCount) + '.jpg'
        imagePath = os.path.join(saveFolder, filename)

        drawImage = image.copy()
        pt1 = (button['x'], button['y'])
        pt2 = (button['x'] + button['w'], button['y'] + button['h'])
        cv2.rectangle(drawImage, pt1, pt2, (0, 0, 255), 2)  # red
        cv2.imwrite(imagePath, drawImage)
        return True
