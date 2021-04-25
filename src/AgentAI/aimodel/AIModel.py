# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from abc import ABCMeta, abstractmethod

class AIModel(object):
    """
    AI Model interface class, define abstract interface
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        self.logger = logging.getLogger('agent')
        self.agentEnv = None

    @abstractmethod
    def Init(self, agentEnv):
        """
        Abstract interface, Init AIModel object
        """
        self.agentEnv = agentEnv

    @abstractmethod
    def Finish(self):
        """
        Abstract interface, Exit AIModel object
        """
        self.logger.info("execute the default finished")

    @abstractmethod
    def OnEpisodeStart(self):
        """
        Abstract interface, do something when episode start
        """
        self.logger.info("execute the default start")

    @abstractmethod
    def OnEpisodeOver(self):
        """
        Abstract interface, do something when episode over
        """
        self.logger.info("execute the default over")

    @abstractmethod
    def OnEnterEpisode(self):
        """
        Abstract interface, do something when enter episode
        """
        self.logger.info("execute the default enter")

    @abstractmethod
    def OnLeaveEpisode(self):
        """
        Abstract interface, do something when leave episode
        """
        self.logger.info("execute the default leave")

    @abstractmethod
    def TrainOneStep(self):
        """
        Abstract interface, one step (usually means get a image frame) when train AIModel
        """
        self.logger.info("execute the default train one step")

    @abstractmethod
    def TestOneStep(self):
        """
        Abstract interface, one step (usually means get a image frame) when run AI test
        """
        self.logger.info("execute the default test one step")
