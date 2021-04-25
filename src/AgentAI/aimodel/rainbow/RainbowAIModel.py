# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import select
import socket
import struct
import time

from aimodel.AIModel import AIModel
from util import util

#SERVER_CFG_FILE = 'cfg/task/Server.ini'

LEARNING_CFG_FILE = 'cfg/task/agent/RainbowLearning.json'

MAGIC_NUMBER = 967345
LOG_FREQUENCY = 50
OVER_TIME = 0.18


class RainbowAIModel(AIModel):
    def __init__(self):
        AIModel.__init__(self)
        self.__proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__env = None
        self.__done = True
        self.__sendTime = None
        self.__recvTime = None
        self.__width = -1
        self.__height = -1
        self.__envCfgPath = None

    def Init(self, agentEnv):
        self.logger.info("enter the ProxyAI init")
        self.__env = agentEnv

        self.__envCfgPath = util.ConvertToSDKFilePath(LEARNING_CFG_FILE)

        if not self._GetServerAddr():
            self.logger.error('GetServerAddr failed!')
            return False

        # 连接server
        self.__proxySocket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        ret = self.__proxySocket.connect_ex((self.__address, self.__port))
        if ret != 0:
            self.logger.error('connect server failed, error = {}'.format(ret))
            return False
        self.logger.info("leave the ProxyAI init")
        return True

    def Finish(self):
        self.__proxySocket.close()

    def TrainOneStep(self):
        """
        Abstract interface implement, run one step (usually means get a image frame)
        when trian DQN AI model
        """
        self.logger.info("execute the default train one step in rainbow model")

    # 1. 获取操作ID，执行相关操作
    # 2. 从gamereg获取状态信息
    # 3. 发送状态信息到server
    def TestOneStep(self):
        self.logger.debug("begin to test one step")
        if self.__done is True:
            self.logger.warning("test one step has done, send the action to the client")
            actionIndex = 0
            self.__env.DoAction(actionIndex)
        else:
            actionIndex = self._GetActionIndex()
            self.logger.debug("get the action index,index: %d", actionIndex)
            # control do action time after send state
            self.__recvTime = time.time()
            passTime = self.__recvTime - self.__sendTime
            if passTime < OVER_TIME:
                time.sleep(OVER_TIME - passTime)
            else:
                self.logger.warning('receive action over time : {:.2f} ms', passTime * 1000)

            # 执行操作
            self.__env.DoAction(actionIndex)

        state = self.__env.GetState()
        self.__sendTime = time.time()
        if state is None:
            self.__done = True
            time.sleep(0.001)
            return True

        # 发送信息给server
        image = state[0]
        reward = state[1]
        done = state[2]
        frameIndex = state[3]
        self._SendState(image, reward, done, frameIndex)

        if frameIndex % 50 == 0:
            self.__env.DoAction(3)

        self.__done = done
        time.sleep(0.001)

        return True

    def _SendState(self, image, reward, done, frameIndex):
        terminal = 1 if done else 0
        imageBytes = image.tobytes()

        dataLength = 16 + len(imageBytes)
        headerBytes = struct.pack('iifii', dataLength, MAGIC_NUMBER, reward, terminal, frameIndex)

        #socket.MSG_WAITALL
        dataBytes = headerBytes + imageBytes
        self.logger.debug("send state to the server, reward={}， frameIndex={}".format(reward, frameIndex))
        self.__proxySocket.sendall(dataBytes)
        self.logger.debug("send state to the server success, reward={}, frameIndex={}".format(reward, frameIndex))

        if frameIndex % LOG_FREQUENCY == 0:
            self.logger.info('send state: frame index = {}, reward = {:.2f}'.format(frameIndex, reward))

        return True

    def _GetActionIndex(self):
        prev = self._RecvAction()

        # 获取操作信息
        while True:
            curr = self._RecvAction()
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

    def _RecvAction(self):
        ready = select.select([self.__proxySocket], [], [], 0)
        if ready[0]:
            dataBytes = self.__proxySocket.recv(12, socket.MSG_WAITALL)
            if len(dataBytes) == 0:
                return None

            if len(dataBytes) != 12:
                self.logger.error('the length of data bytes is not 12')
            else:
                magic, actionIndex, frameIndex = struct.unpack('iii', dataBytes)
                if magic != MAGIC_NUMBER:
                    self.logger.error('error magic number')
                    return None

                self.logger.debug(
                    'receive action: frame index = {}, action index = {}'.format(frameIndex, actionIndex))
                if frameIndex % LOG_FREQUENCY == 0:
                    self.logger.info('receive action: frame index = {}, action index = {}'.format(frameIndex,
                                                                                                  actionIndex))
                return actionIndex

    def _GetServerAddr(self):

        if os.path.exists(self.__envCfgPath) is False:
            self.logger.error('Rainbow learning cfg not exist,file:{}'.format(self.__envCfgPath))
            return False

        try:
            config = util.get_configure(self.__envCfgPath)
            # svrFile = util.ConvertToSDKFilePath(SERVER_CFG_FILE)
            # config = configparser.ConfigParser()
            # config.read(svrFile)
            self.__address = config['server']['hostIp']  # config.get('Server', 'Address', fallback='127.0.0.1')
            self.__port = config['server']['hostPort']   # config.getint('Server', 'Port', fallback=8080)
            self.logger.info('Server addr: {} port: {}.'.format(self.__address, self.__port))
        except Exception as e:
            self.logger.error('Load server cfg file failed, error: {}.'.format(e))
            return False
        return True
