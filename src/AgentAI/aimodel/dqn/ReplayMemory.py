# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import random
import logging
from collections import deque

import numpy as np
import cv2

class ReplayMemory(object):
    """
    Experience replay memory for dqn
    """

    def __init__(self, maxSize, termDelayFrame, stateRecentFrame, showState):
        #store replay (key, value) in dict
        self.maxSize = maxSize
        self.termDelayFrame = termDelayFrame
        self.stateRecentFrame = stateRecentFrame
        self.showState = showState
        self.replayNum = 0
        self.keyIndicate = 0
        self.replayTable = [None for x in range(0, maxSize)]

        #replay buffer
        self.replayBuffer = deque()
        self.maxBufferLen = self.termDelayFrame + self.stateRecentFrame

        #store key in set, for random mini batch
        self.keySet = set()

        #logger handle
        self.logger = logging.getLogger('agent')

    def Add(self, action, reward, state, terminal, variables=None):
        """
        Add one sample (s, a, r, t) to replay memory
        """
        self.replayBuffer.append((action, reward, state, terminal, variables))

        if len(self.replayBuffer) < self.maxBufferLen:
            if terminal is True:
                self.replayBuffer.clear()
            return

        if len(self.replayBuffer) > self.maxBufferLen:
            self.logger.error('replay buffer length too long')

        if terminal is True:
            for x in range(0, self.termDelayFrame):
                self.replayBuffer.pop()

            for x in range(0, self.stateRecentFrame):
                replay = self.replayBuffer[x]
                a = replay[0]
                r = replay[1]
                #before game over, recent frame reward should not be positive
                if r > 0:
                    r = 0
                s = replay[2]
                t = replay[3]
                if x == self.stateRecentFrame - 1:
                    r = reward
                    #r = -1.0
                    t = True
                variables = replay[4]
                self._InsertNew(a, r, s, variables, t, 0)
            self.replayBuffer.clear()
        else:
            replay = self.replayBuffer.popleft()
            a = replay[0]
            r = replay[1]
            s = replay[2]
            t = replay[3]
            variables = replay[4]
            self._InsertNew(a, r, s, variables, t, 1)


    def _InsertNew(self, action, reward, state, variables, terminal, flag):
        if self.showState is True:
            cv2.imshow('replay', state)
            cv2.waitKey(1)

        #add new replay
        self.replayTable[self.keyIndicate] = (action, reward, state, terminal, flag, variables)

        if flag == 1:
            self.keySet.add(self.keyIndicate)
        else:
            self.keySet.discard(self.keyIndicate)

        self.keyIndicate = (self.keyIndicate + 1) % self.maxSize

        #update replay number
        if self.replayNum < self.maxSize:
            self.replayNum += 1

    def Random(self, batchSize):
        """
        Random batchSize sample from replay memory
        """
        validCount = 0
        batch = list()

        keys = random.sample(self.keySet, batchSize + self.stateRecentFrame)
        invalidKeys = [(self.keyIndicate - x) % self.replayNum \
                    for x in range(1, self.stateRecentFrame + 1)]

        for x in keys:
            if x in invalidKeys:
                continue

            replays = [self.replayTable[(x+i) % self.replayNum] \
                    for i in range(0, self.stateRecentFrame + 1)]
            if replays[0][4] == 0:
                self.logger.error('flag error in replay memory')

            imgs = [replay[2] for replay in replays]
            a = replays[self.stateRecentFrame-1][0]
            r = replays[self.stateRecentFrame-1][1]
            t = replays[self.stateRecentFrame-1][3]

            state0 = np.stack(imgs[0 : self.stateRecentFrame], axis=2)
            state1 = np.stack(imgs[1 : self.stateRecentFrame + 1], axis=2)

            variables0 = replays[self.stateRecentFrame-1][5]
            variables1 = replays[self.stateRecentFrame][5]

            if variables0 is None:
                batch.append((state0, a, r, state1, t))
            else:
                batch.append((state0, a, r, state1, t, variables0, variables1))
            validCount += 1
            if validCount == batchSize:
                break

        return batch
