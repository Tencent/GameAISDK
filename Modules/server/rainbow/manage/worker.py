# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from collections import deque
from log.log import LOG
import queue
import time
import torch


ACTION_SPACE = 3
HISTORY_LENGTH = 4
INPUT_WIDTH = 84
INPUT_HEIGHT = 84
LOG_FREQUENCY = 5000


class Env(object):
    def __init__(self, index):
        self.__index = index
        self.__frame_info_queue = queue.Queue()  # 帧队列
        self.__action_info_queue = queue.Queue()  # 操作队列

    def put_frame_info(self, frame_info):
        self.__frame_info_queue.put(frame_info)
        return

    def put_action_info(self, action_index, frame_index):
        action_info = (action_index, frame_index)
        self.__action_info_queue.put(action_info)
        return

    def get_frame_info(self):
        """
        get newest frame information
        """

        prev = self._get_frame_info()

        while True:
            curr = self._get_frame_info()
            if curr is None:
                if prev is None:
                    time.sleep(0.003)
                    continue
                else:
                    curr = prev
                    break
            else:
                prev = curr

        return curr

    def get_action_info(self):
        try:
            action_info = self.__action_info_queue.get_nowait()
        except queue.Empty:
            return None
        else:
            return action_info

    def _get_frame_info(self):
        try:
            frame_info = self.__frame_info_queue.get_nowait()
        except queue.Empty:
            return None
        else:
            return frame_info


class Worker(object):
    """
    worker, predict action
    """

    def __init__(self, index, master):
        LOG.info('init worker-{}'.format(index))

        self.__index = index
        self.__master = master

        self.__env = Env(index)

        # self.__device = torch.device('cuda')
        self.__device = torch.device('cpu')

        self.__step = 0

    def set_frame_info(self, frame_info):
        self.__env.put_frame_info(frame_info)
        return

    def get_action_info(self):
        return self.__env.get_action_info()

    def work(self):
        LOG.info('worker-{} is running'.format(self.__index))
        try:
            while True:
                LOG.info('worker-{} starts episode'.format(self.__index))

                buffer = deque([], maxlen=HISTORY_LENGTH)
                for _ in range(HISTORY_LENGTH):
                    buffer.append(torch.zeros(INPUT_WIDTH, INPUT_HEIGHT, device=self.__device))

                image, _, _, frame_index = self.__env.get_frame_info()
                buffer.append(torch.tensor(image, dtype=torch.float32, device=self.__device).div_(255))
                state = torch.stack(list(buffer), 0)

                while True:
                    start_time = time.time()
                    LOG.info("begin to get action")
                    action_index = self.__master.rainbow.act(state)
                    LOG.info("get the action finished, action_index is {}".format(action_index))

                    end_time = time.time()
                    if self.__step % LOG_FREQUENCY == 0:
                        cost_time = (end_time - start_time) * 1000
                        LOG.info('worker-{} costs {:.2f} ms to inference at step {}'.format(self.__index, cost_time,
                                                                                            self.__step))

                    self.__env.put_action_info(action_index, frame_index)

                    LOG.info("begin to get the frame info")
                    image, reward, done, frame_index = self.__env.get_frame_info()
                    LOG.info("get the frame info finished")
                    self.__master.send_transition(self.__index, state, action_index, reward, done)
                    buffer.append(torch.tensor(image, dtype=torch.float32, device=self.__device).div_(255))
                    state = torch.stack(list(buffer), 0)

                    self.__step += 1
                    if self.__step % LOG_FREQUENCY == 0:
                        LOG.info('worker-{} runs step {}'.format(self.__index, self.__step))

                    if done is True:
                        LOG.info('worker-{} finishes episode'.format(self.__index))
                        break
        except Exception as err:
            LOG.info('Work execute failed, err:{}'.format(err))
        finally:
            LOG.info('Work execute finally')
        return
