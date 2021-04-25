# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import csv
import json
import logging
import os
import time
import cv2
import platform
import numpy as np

is_windows = platform.platform().lower().startswith('win')

from .adb_touch_sampler import ADBTouchSampler
if is_windows:
    from .window_touch_sampler import WindowTouchSampler, HookEventType
from WrappedDeviceAPI.deviceAdapter import DeviceType
from .circle import draw_angle, get_angle_image

CFG_FILE = 'cfg/cfg.json'

"""
AI_ACTION_TYPES = [
    'down',
    'up',
    'click',
    'swipe',
    'joystick',
    'key'
]
"""

ACTION_TYPE_NONE = 0  # 空动作
ACTION_TYPE_PRESS_DOWN = 1  # 按压动作
ACTION_TYPE_PRESS_UP = 2  # 松开动作
ACTION_TYPE_CLICK = 3  # 点击动作
ACTION_TYPE_SWIPE_ONCE = 4  # 滑一次动作
ACTION_TYPE_JOY_STICK = 5  # 摇杆动作
ACTION_TYPE_SIMULATOR_KEY = 6  # 模拟器键盘

COLOR_RED = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)

np.seterr(divide='ignore', invalid='ignore')

LOG = logging.getLogger('action_sampler')


class ActionSampler(object):
    def __init__(self, device_id=None, device_type=DeviceType.Android.value):
        self.__device_id = device_id
        self.__device_type = device_type
        self.__actionsContextList = dict()  # 存放配置的动作信息，每个元素对应一个定义动作的信息

        self.__actionResultSet = set()  # 存放采集到的动作结果ID
        self.__noneActionId = -1  # none动作ID，默认先设置为-1，如果用户配置了，则会覆盖
        self.__frame = None
        self.__frameCount = 0
        self.__outputTimestamp = time.time()
        self.__exited = False
        self.__isDebug = False
        self.__frameTime = None
        self.__isOutputAsVideo = False
        self.__sampleOutputDir = None
        self.__sampleFramePrefix = None
        self.__videoWriter = None
        self.__sampleData = list()  # 存放动作样本结果的列表，最终输出到csv文件
        self.__now = time.time()
        self.__outputFlag = False
        self.__checkedFlag = False

    def init(self):
        self._load_config()
        if self.__device_type == DeviceType.Android.value:
            long_edge = self.__frameHeight
            short_edge = self.__frameWidth
            if self.__frameHeight < self.__frameWidth:
                long_edge = self.__frameWidth
                short_edge = self.__frameHeight

            self.__touchSampler = ADBTouchSampler(self.__device_id)
            self.__touchSampler.init(long_edge, short_edge)

        elif self.__device_type == DeviceType.Windows.value:
            keys_code = self.__get_keys_code()
            self.__device_id = int(self.__device_id)
            self.__touchSampler = WindowTouchSampler(self.__device_id)
            self.__touchSampler.init(self.__frameWidth, self.__frameHeight, keys_code)

        self.__frameTime = 1. / self.__frameFPS

        return True

    def set_exited(self):
        self.__exited = True

    def run(self):
        if self.__device_type == DeviceType.Android.value:
            while not self.__exited:
                self._update()
                time.sleep(0.001)
        elif self.__device_type == DeviceType.Windows.value:
            while not self.__exited:
                self._update_window()
                time.sleep(0.05)

    def finish(self):
        self.set_exited()
        if self.__outputFlag:
            self._output_csv()
            self._finish_video()
        self.__touchSampler.deinit()

    def _init_output(self):
        self.__sampleOutputDir = self._create_sample_dir()
        self.__sampleFramePrefix = self._create_sample_prefix()

        # 如果是输出视频，则创建videowriter
        if self.__isOutputAsVideo:
            self.__videoWriter = self._create_video()
            if self.__videoWriter is None:
                LOG.error('Create video failed!')
                return False
        return True

    def _update_window(self):
        frame, evts = self.__touchSampler.get_sample()
        if frame is None:  # 如果图片帧是None，则直接返回
            return

        self.__frame = frame
        self._convert_to_actions(evts)  # 根据触点坐标，计算定义的动作是否发生

        if self.__isDebug:
            self._show_window(self.__frame.copy(), evts)

        self.__now = time.time()
        if self.__now - self.__outputTimestamp > self.__frameTime:  # 按帧率时间控制输出频率
            self._output_result(self.__frame, self.__actionResultSet)
            self.__outputTimestamp = self.__now
            self.__actionResultSet.clear()

        recording_status = self._check_recording_status(evts)
        if recording_status == 1:
            self._init_output()
            self.__outputFlag = True
        elif recording_status == 2:
            self._output_csv()
            self._finish_video()
            self.__frameCount = 0
            self.__outputFlag = False

    def _update(self):
        frame, points = self.__touchSampler.get_sample()
        if frame is None:  # 如果图片帧是None，则直接返回
            return

        self.__frame = frame
        self._convert_points_to_actions(points)  # 根据触点坐标，计算定义的动作是否发生

        if self.__isDebug:
            self._debug(self.__frame.copy(), self.__actionResultSet, points)

        self.__now = time.time()
        if self.__now - self.__outputTimestamp > self.__frameTime:  # 按帧率时间控制输出频率
            self._output_result(self.__frame, self.__actionResultSet)
            self.__outputTimestamp = self.__now
            self.__actionResultSet.clear()

        # 检查是否有4指同按的切换
        if self._check_switch(points):
            self.__touchSampler.detect_rotation()
            if not self.__outputFlag:  # 如果之前是结束状态，则变为采集状态
                self._init_output()
                self.__outputFlag = True
            else:  # 如果之前是采集状态，则变为结束状态
                self._output_csv()
                self._finish_video()
                self.__frameCount = 0
                self.__outputFlag = False

    def _check_switch(self, points):
        """
        检测是否有4指同时按住触发切换的逻辑。先判断大于3个触点按住，然后判断触点是否全部松开，则触发返回True并重置状态。
        """
        if self.__checkedFlag:
            if len(points) == 0:
                self.__checkedFlag = False
                return True
        else:
            if len(points) > 3:
                self.__checkedFlag = True
        return False

    def _check_recording_status(self, evts):
        for evt in evts:
            evt_type, action_type, value = evt
            if evt_type == HookEventType.KEYBOARD:
                if value == 112:  # F1
                    return 1  # start
                elif value == 113:  # F2
                    return 2
        return 0

    def _debug(self, frame, actionResultSet, points):
        for actionId, actionContext in self.__actionsContextList.items():
            actionType = actionContext.get('type')
            if actionType == ACTION_TYPE_JOY_STICK:
                startx = actionContext.get('startX')
                endx = actionContext.get('endX')
                starty = actionContext.get('startY')
                endy = actionContext.get('endY')
                angleImg = actionContext.get('actionRegionEdge')
                x1 = actionContext.get('x') + startx
                y1 = actionContext.get('y') + starty
                if actionId in actionResultSet:
                    color = COLOR_RED
                else:
                    color = COLOR_GREEN
                cv2.putText(frame, str(actionId), (x1, y1), cv2.FONT_HERSHEY_COMPLEX, 0.5, color, 1)
                draw_angle(frame[starty:endy, startx:endx], angleImg, color)

            elif actionType != ACTION_TYPE_NONE:
                x1 = actionContext.get('regionX1')
                y1 = actionContext.get('regionY1')
                x2 = actionContext.get('regionX2')
                y2 = actionContext.get('regionY2')
                if actionId in actionResultSet:
                    color = COLOR_RED
                else:
                    color = COLOR_GREEN
                cv2.putText(frame, str(actionId), (x1, y1), cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=2)

        cv2.putText(frame, str(self.__frameCount), (0, 30),
                    cv2.FONT_HERSHEY_COMPLEX, 1, COLOR_GREEN, 2)

        for p in points:
            cv2.circle(frame, (p.x, p.y), 15, COLOR_RED, thickness=4)
        cv2.imshow('frame', frame)
        cv2.waitKey(1)

    def _show_window(self, frame, evts):
        for action_id, action_context in self.__actionsContextList.items():
            action_type = action_context.get('type', ACTION_TYPE_NONE)
            if action_type in [ACTION_TYPE_CLICK, ACTION_TYPE_PRESS_DOWN,
                               ACTION_TYPE_PRESS_UP, ACTION_TYPE_SIMULATOR_KEY]:
                x1 = action_context.get('regionX1')
                y1 = action_context.get('regionY1')
                x2 = action_context.get('regionX2')
                y2 = action_context.get('regionY2')
                if action_id in self.__actionResultSet:
                    color = COLOR_RED
                    if action_type == ACTION_TYPE_SIMULATOR_KEY:
                        for evt in evts:
                            evt_type, action_type, value = evt
                            alpha = action_context.get('alphabet').upper()
                            kb_value = chr(value).upper()
                            if kb_value == alpha:
                                x, y = int((x1 + x2) / 2), int((y1 + y2) / 2)
                                cv2.circle(frame, (x, y), 15, COLOR_RED, thickness=4)
                else:
                    color = COLOR_GREEN

                cv2.putText(frame, str(action_id), (x1, y1), cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=2)


        for evt in evts:
            evt_type, action_type, value = evt
            if evt_type == HookEventType.MOUSE:
                x, y = value
                cv2.circle(frame, (x, y), 15, COLOR_RED, thickness=4)

        cv2.putText(frame, str(self.__frameCount), (0, 30),
                    cv2.FONT_HERSHEY_COMPLEX, 1, COLOR_GREEN, 2)

        cv2.imshow('frame', frame)
        cv2.waitKey(1)

    def _output_result(self, frame, actionResultSet):
        if not self.__outputFlag:
            return

        # 构造图片帧文件名称
        sampleFramePath = self.__sampleOutputDir + self.__sampleFramePrefix \
                          + str(self.__frameCount) + '.jpg'
        self._output_frame(frame, sampleFramePath)

        if self.__frameCount > 0:
            # 动作是基于上一帧图片做出的，所以要晚一帧
            sampleDataPath = self.__sampleOutputDir + self.__sampleFramePrefix + str(
                self.__frameCount - 1) + '.jpg'

            # 判断是否记录时间
            if self.__isLogTimestamp:
                sampleData = [self._get_timestamp(self.__now), sampleDataPath]
            else:
                sampleData = [sampleDataPath]

            for actionId in actionResultSet:
                # 小于0的ID预留给None动作
                if actionId >= 0:
                    actionName = self.__actionsContextList[actionId].get('name')
                else:
                    actionName = 'none'

                sampleData.extend([actionId, actionName])

            self.__sampleData.append(sampleData)

        self.__frameCount += 1

    def _output_frame(self, frame, sampleFramePath):
        if self.__isOutputAsVideo:
            self.__videoWriter.write(frame)
        else:
            cv2.imwrite(sampleFramePath, frame)

    def _output_csv(self):
        csvfilePath = self.__sampleOutputDir + self.__sampleFramePrefix + 'data.csv'
        with open(csvfilePath, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)

            # 判断是否记录时间，记录时间则多一列timestamp
            if self.__isLogTimestamp:
                writer.writerow(["timestamp", "name", "action", "action_name"])
            else:
                writer.writerow(["name", "action", "action_name"])

            writer.writerows(self.__sampleData)

        self.__sampleData.clear()
        self.__sampleOutputDir = None
        self.__sampleFramePrefix = None

    def _create_sample_prefix(self):
        prefix = '{0}_{1}X{2}_'.format(self.__timestamp, self.__frameWidth, self.__frameHeight)
        return prefix

    def _create_sample_dir(self):
        self.__timestamp = time.strftime("%Y-%m-%d_%H_%M_%S")
        # command by berryjwang
        # sampleDir = 'output/' + self.__gameName + '/' + self.__timestamp + '/'
        sampleDir = self.__savePath + '/' + self.__gameName + '/' + self.__timestamp + '/'
        if not os.path.exists(sampleDir):
            os.makedirs(sampleDir)
        return sampleDir

    def _create_video(self):
        sampleFramePath = self.__sampleOutputDir + self.__sampleFramePrefix + 'video.avi'
        fourcc = cv2.VideoWriter_fourcc(*'DIVX')
        videoWriter = cv2.VideoWriter(sampleFramePath,
                                      fourcc, self.__frameFPS,
                                      (self.__frameWidth, self.__frameHeight))
        return videoWriter

    def _finish_video(self):
        if self.__videoWriter is not None:
            self.__videoWriter.release()
            self.__videoWriter = None

    def __get_keys_code(self):
        keys_code = []
        for action_id, action_context in self.__actionsContextList.items():
            action_type = action_context.get('type', ACTION_TYPE_NONE)
            if action_type == ACTION_TYPE_SIMULATOR_KEY:
                alpha = action_context.get('alphabet').upper()
                if alpha:
                    keys_code.append(ord(alpha))

        return keys_code

    def _get_action_id(self, evt):
        """ 获取action id

        :param evt:
        :return:
        """
        hook_evt_type, hook_action_type, value = evt
        for action_id, action_context in self.__actionsContextList.items():
            action_type = action_context.get('type', ACTION_TYPE_NONE)
            if action_type in [ACTION_TYPE_CLICK, ACTION_TYPE_PRESS_DOWN, ACTION_TYPE_PRESS_UP] and \
                hook_evt_type == HookEventType.MOUSE:
                if action_type == hook_action_type:
                    pt_x, pt_y = value
                    if action_context['regionX1'] <= pt_x <= action_context['regionX2'] and \
                        action_context['regionY1'] <= pt_y <= action_context['regionY2']:
                        return action_id

            elif action_type == ACTION_TYPE_SIMULATOR_KEY and hook_evt_type == HookEventType.KEYBOARD:
                alpha = action_context.get('alphabet').upper()
                kb_value = chr(value).upper()
                if kb_value == alpha:
                    return action_id

        return -1

    def _convert_to_actions(self, evts):
        for evt in evts:
            action_id = self._get_action_id(evt)
            if action_id != -1:
                self.__actionResultSet.add(action_id)
        if len(self.__actionResultSet) == 0:
            self.__actionResultSet.add(self.__noneActionId)
        else:
            LOG.info('action result set:%s' % self.__actionResultSet)

    def __convert_swipe_once_action(self, points, action_id, action_context):
        """ 转换swipe_once动作

        :param points:
        :param action_id:
        :param action_context:
        :return:
        """
        last_down_point = action_context['point']
        this_down_point = None
        for point in points:
            if self._is_inside(point, action_context):
                this_down_point = point

        if last_down_point and this_down_point:
            # 判断
            if this_down_point.trackingId == last_down_point.trackingId:  # 确保一定是同一个触点
                dirVect = this_down_point - last_down_point  # 采集到的同一个触点移动计算出的向量
                dirActionVect = action_context['dirVect']  # 配置动作计算出的向量

                # 判断上面两个向量的方向是否相等（误差范围内）
                if self._is_direction_equal(dirVect, dirActionVect,
                                            action_context.get('dirRange', 90)):
                    self.__actionResultSet.add(action_id)

        action_context['point'] = this_down_point

    def __convert_press_up_action(self, points, action_id, action_context):
        """ 转换press_up动作

        :param points:
        :param action_id:
        :param action_context:
        :return:
        """
        last_down_point = action_context['point']
        this_down_point = None
        # 判断一下是否有出现在区域框中的点
        for point in points:
            if self._is_inside(point, action_context):
                this_down_point = point

        # 上一次有point但是这次没有，则认为是发生了up
        if last_down_point and not this_down_point:
            if this_down_point.trackingId == last_down_point.trackingId:  # 确保一定是同一个触点
                self.__actionResultSet.add(action_id)

        # 记录作为上一次的point
        action_context['point'] = this_down_point

    def _convert_points_to_actions(self, points):
        for actionId, actionContext in self.__actionsContextList.items():  # 遍历配置的动作，判断是否有发生，如果有，则输出到结果队列中
            action_type = actionContext.get('type')
            if action_type == ACTION_TYPE_NONE:
                pass

            elif action_type in [ACTION_TYPE_PRESS_DOWN, ACTION_TYPE_CLICK]:
                # 判断一下是否有出现在区域框中的点，有的话则认为发生了对应的动作
                for point in points:
                    if self._is_inside(point, actionContext):
                        self.__actionResultSet.add(actionId)

            elif action_type == ACTION_TYPE_JOY_STICK:
                # 判断一下是否有出现在区域框中的点，有的话则认为发生了对应的动作
                actionRegion = actionContext['actionRegion']
                for point in points:
                    tmpPointX = point.x - actionContext['startX']
                    tmpPointY = point.y - actionContext['startY']
                    if self._is_in_region(tmpPointX, tmpPointY, actionRegion):
                        self.__actionResultSet.add(actionId)

            elif action_type == ACTION_TYPE_PRESS_UP:
                self.__convert_press_up_action(points, actionId, actionContext)

            elif action_type == ACTION_TYPE_SWIPE_ONCE:
                self.__convert_swipe_once_action(points, actionId, actionContext)

        # 检查结果是否为空，如果为空，说明没做动作，则添加none动作；如果不为空，说明有做动作，则一定不会有none动作
        if len(self.__actionResultSet) == 0:
            self.__actionResultSet.add(self.__noneActionId)
        elif len(self.__actionResultSet) > 1:
            self.__actionResultSet.discard(self.__noneActionId)

        # 记录作为上一次的点，因为某些动作需要依据上一次的点做判断
        self.__lastPoints = points

    def _load_config(self):
        with open(CFG_FILE) as fileData:
            data = json.load(fileData)
            self.__gameName = data['GameName']
            self.__savePath = data['SavePath']
            self.__frameFPS = data['FrameFPS']
            self.__frameHeight = data['FrameHeight']
            self.__frameWidth = data['FrameWidth']
            self.__actionCfgFile = data['ActionCfgFile']
            self.__isDebug = data['Debug']
            self.__isOutputAsVideo = data['OutputAsVideo']
            self.__isLogTimestamp = data.get('LogTimestamp', True)

        self._load_action_config(self.__actionCfgFile)

    def _load_action_config(self, actionCfgFile):
        with open(actionCfgFile) as fileData:
            data = json.load(fileData)
            self.__screenActionHeight = data['screenHeight']
            self.__screenActionWidth = data['screenWidth']
            ratio = self.__frameHeight / self.__screenActionHeight
            for actionContext in data['actions']:
                actionType = actionContext.get('type')
                actionId = actionContext.get('id')
                if actionId is None:
                    continue

                if actionType == ACTION_TYPE_NONE:
                    self.__noneActionId = actionId  # 如果定义了none动作，则使用定义的ID覆盖
                    regionX1 = 0
                    regionY1 = 0
                    regionX2 = 0
                    regionY2 = 0
                elif actionType == ACTION_TYPE_PRESS_UP:
                    actionContext['point'] = None
                    regionX1 = actionContext.get('startRectx')
                    regionY1 = actionContext.get('startRecty')
                    regionX2 = actionContext.get('startRectx') + actionContext.get('width')
                    regionY2 = actionContext.get('startRecty') + actionContext.get('height')
                elif actionType == ACTION_TYPE_SIMULATOR_KEY:
                    regionX1 = actionContext.get('startRectx')
                    regionY1 = actionContext.get('startRecty')
                    regionX2 = actionContext.get('startRectx') + actionContext.get('width')
                    regionY2 = actionContext.get('startRecty') + actionContext.get('height')
                    actionContext['alphabet'] = actionContext.get('alphabet')
                    actionContext['key_type'] = actionContext.get('actionType')

                elif actionType == ACTION_TYPE_SWIPE_ONCE:
                    actionContext['point'] = None
                    #  计算一个大的矩形框，刚好邻接startRect和endRect两个矩形框，作为动作有效区域
                    regionX1 = min(actionContext.get('startRectx'), actionContext.get('endRectx'))
                    regionY1 = min(actionContext.get('startRecty'), actionContext.get('endRecty'))
                    regionX2 = max(actionContext.get('startRectx') + actionContext.get('startRectWidth'),
                                   actionContext.get('endRectx') + actionContext.get('endRectWidth'))
                    regionY2 = max(actionContext.get('startRecty') + actionContext.get('startRectHeight'),
                                   actionContext.get('endRecty') + actionContext.get('endRectHeight'))
                    sx = actionContext.get('startX')
                    sy = actionContext.get('startY')
                    ex = actionContext.get('endX')
                    ey = actionContext.get('endY')
                    actionContext['dirVect'] = np.array([ex - sx, ey - sy]) * ratio

                elif actionType == ACTION_TYPE_JOY_STICK:
                    actionContext['centerx'] = int(actionContext['centerx'] * ratio)
                    actionContext['centery'] = int(actionContext['centery'] * ratio)
                    actionContext['rangeInner'] = int(actionContext['rangeInner'] * ratio)
                    actionContext['rangeOuter'] = int(actionContext['rangeOuter'] * ratio)
                    startx = actionContext['centerx'] - actionContext['rangeOuter']
                    endx = actionContext['centerx'] + actionContext['rangeOuter']
                    starty = actionContext['centery'] - actionContext['rangeOuter']
                    endy = actionContext['centery'] + actionContext['rangeOuter']
                    num = actionContext.get('QuantizedNumber')
                    name = actionContext.get('name')

                    successFlag, angleImageList, angleImageEdgeList = get_angle_image(
                        radiusBig=actionContext['rangeOuter'],
                        radiusSmall=actionContext['rangeInner'],
                        angleNum=num)

                    # 量化了QuantizedNumber个角度，就构造QuantizedNumber个子动作，从actionId开始
                    for i in range(num):
                        context = dict()
                        context['name'] = '{}_{}'.format(name, i)
                        context['type'] = ACTION_TYPE_JOY_STICK
                        context['startX'] = startx
                        context['endX'] = endx
                        context['startY'] = starty
                        context['endY'] = endy
                        context['actionRegion'] = angleImageList[i]  # 子动作的有效区域mask，用于判断点的坐标是否发生在该区域

                        # 下面都是用于debug显示的信息
                        context['actionRegionEdge'] = angleImageEdgeList[i]  # 区域轮廓
                        result = np.argwhere(context['actionRegion'] == 255)[:, 1]
                        if result:
                            media_x = np.median(result)
                            if np.isnan(media_x):
                                context['x'] = np.nan_to_num(media_x)
                            else:
                                context['x'] = int(media_x)

                            media_y = np.median(np.argwhere(context['actionRegion'] == 255)[:, 0])
                            if np.isnan(media_y):
                                context['y'] = np.nan_to_num(media_y)
                            else:
                                context['y'] = int(media_y)
                        else:
                            LOG.warning('action cotext(%s) error, so quit.' % str(actionContext))
                            continue

                        # context['x'] = int(np.median(np.argwhere(context['actionRegion'] == 255)[:, 1]))  # 区域中心坐标x
                        # context['y'] = int(np.median(np.argwhere(context['actionRegion'] == 255)[:, 0]))  # 区域中心坐标y
                        self.__actionsContextList[actionId + i] = context
                    continue
                else:
                    regionX1 = actionContext.get('startRectx')
                    regionY1 = actionContext.get('startRecty')
                    regionX2 = actionContext.get('startRectx') + actionContext.get('width')
                    regionY2 = actionContext.get('startRecty') + actionContext.get('height')

                actionContext['regionX1'] = int(regionX1 * ratio)
                actionContext['regionY1'] = int(regionY1 * ratio)
                actionContext['regionX2'] = int(regionX2 * ratio)
                actionContext['regionY2'] = int(regionY2 * ratio)
                self.__actionsContextList[actionId] = actionContext

    def _is_inside(self, point, actionContext):
        """
        根据动作定义的矩形框来判断point是否在矩形框内部
        """
        x1 = actionContext.get('regionX1')
        y1 = actionContext.get('regionY1')
        x2 = actionContext.get('regionX2')
        y2 = actionContext.get('regionY2')
        if point.x < x1 or point.x >= x2 or point.y < y1 or point.y >= y2:
            return False
        return True

    def _is_in_region(self, px, py, regionMat):
        """
        根据regionMat[py, px] == 255来判断(px, py)是否在区域中，regionMat相当于一个mask
        """
        try:
            ret = regionMat[py, px] == 255
        except IndexError:
            return False
        return ret

    def _is_direction_equal(self, vect1, vect2, range=90):
        """
        判断两个向量vect1和vect2的方向是否相等，误差范围是±(range/2)
        """
        length1 = np.sqrt(vect1.dot(vect1))
        length2 = np.sqrt(vect2.dot(vect2))
        cosAngle = vect1.dot(vect2) / (length1 * length2)
        angle = np.arccos(cosAngle)
        angle = angle * 360 / 2 / np.pi

        if -range / 2 < angle < range / 2:
            return True
        else:
            return False

    def _get_timestamp(self, ct):
        localTime = time.localtime(ct)
        timestamp = str(time.strftime("%Y%m%d%H%M%S", localTime))
        msec = (ct - int(ct)) * 1000
        timestamp = timestamp + str(".%03d" % msec)
        return timestamp
