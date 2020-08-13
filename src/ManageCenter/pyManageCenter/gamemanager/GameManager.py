# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from common.Define import *

LOG = logging.getLogger('ManageCenter')


class GameManager(object):
    """
    GameManager, manage the game context information, such as GameFrame, GameState, GameData, FrameSeq ...
    """
    def __init__(self):
        self.__gameFrame = None
        self.__gameState = GAME_STATE_NONE
        self.__prevGameSate = GAME_STATE_NONE
        self.__frameSeq = 0
        self.__gameData = None

    def Reset(self):
        """
        Reset the game context information
        :return:
        """
        self.__gameFrame = None
        self.__gameState = GAME_STATE_NONE
        self.__prevGameSate = GAME_STATE_NONE
        self.__frameSeq = 0
        self.__gameData = None

    def GetGameFrame(self):
        """
        Get the current frame
        :return: the current frame
        """
        return self.__gameFrame

    def SetGameFrame(self, frame, frameSeq=None):
        """
        Set the current frame, used for update frame
        :param frame: the frame
        :param frameSeq: the frame sequence
        :return:
        """
        self.__gameFrame = frame
        if frameSeq is None:
            self.__frameSeq += 1
        else:
            self.__frameSeq = frameSeq

    def GetGameState(self):
        """
        Get the current GameState
        :return: the current GameState
        """
        return self.__gameState

    def SetGameState(self, newState):
        """
        Set the current GameState, used for update GameState
        :param newState: the new GameState to be setted
        :return:
        """
        self.__prevGameSate = self.__gameState
        self.__gameState = newState

    def GetPrevGameState(self):
        """
        Get the previous GameState
        :return: the previous GameState
        """
        return self.__prevGameSate

    def GameStarted(self):
        """
        Whether the Game has started
        :return: True means the Game has started
        """
        return self.__gameState == GAME_STATE_START

    def GetFrameSeq(self):
        """
        Get the current FrameSeq
        :return: the current FrameSeq
        """
        return self.__frameSeq

    def SetFrameSeq(self, frameSeq):
        """
        Set the current FrameSeq, used for update FrameSeq
        :param frameSeq: the frame sequence
        :return:
        """
        self.__frameSeq = frameSeq

    def GetGameData(self):
        """
        Get the current GameData
        :return: the current GameData
        """
        return self.__gameData

    def SetGameData(self, data, frameSeq=None):
        """
        Set the current GameData, used for update GameData
        :param data: the current GameData
        :param frameSeq: the frame sequence
        :return:
        """
        self.__gameData = data
        if frameSeq is None:
            self.__frameSeq += 1
        else:
            self.__frameSeq = frameSeq
