# -*- coding: utf-8 -*-
"""
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
        pass

    @abstractmethod
    def OnEpisodeStart(self):
        """
        Abstract interface, do something when episode start
        """
        pass

    @abstractmethod
    def OnEpisodeOver(self):
        """
        Abstract interface, do something when episode over
        """
        pass

    @abstractmethod
    def OnEnterEpisode(self):
        """
        Abstract interface, do something when enter episode
        """
        pass

    @abstractmethod
    def OnLeaveEpisode(self):
        """
        Abstract interface, do something when leave episode
        """
        pass

    @abstractmethod
    def TrainOneStep(self):
        """
        Abstract interface, one step (usually means get a image frame) when train AIModel
        """
        pass

    @abstractmethod
    def TestOneStep(self):
        """
        Abstract interface, one step (usually means get a image frame) when run AI test
        """
        pass
