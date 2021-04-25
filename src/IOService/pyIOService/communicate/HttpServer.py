# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import queue
import time
import json
import threading

from http.server import HTTPServer, BaseHTTPRequestHandler

LOG = logging.getLogger('IOService')
SEND_QUEUE = queue.Queue()
RECV_QUEUE = queue.Queue()

UI_ACTION_TIMEOUT = os.getenv('UI_ACTION_TIMEOUT', 5)


class ResquestHandler(BaseHTTPRequestHandler):
    """
    HTTP Server request handler
    """
    @staticmethod
    def _GetUIAction(msgData, timeout=0):
        """
        Initialize this module, load config from cfg
        :param msgData:
        :param timeout:
        :return: UI action msg
        """
        timeDeadLine = time.time() + timeout
        RECV_QUEUE.put_nowait(msgData)

        uiActionData = None
        while time.time() < timeDeadLine:
            while not SEND_QUEUE.empty():
                uiActionData = SEND_QUEUE.get_nowait()
            if uiActionData is not None and uiActionData['img_id'] == msgData['img_id']:
                break
            time.sleep(0.002)

        return uiActionData

    def do_POST(self):
        """
        http server post handler
        :return:
        """
        LOG.info(self.command)
        LOG.info(self.path)
        LOG.info(self.headers)

        try:
            length = int(self.headers.get('content-length'))
            requesData = self.rfile.read(length)
            requesData = requesData.decode('utf-8')
            requesData = json.loads(requesData)

            if self.path != '/ui_action':
                self.send_error(404, 'Page not Found!')
                return

            if not isinstance(requesData, dict):
                responseData = dict()
                responseData["error"] = -1
                responseData["errstr"] = "request data error"
                responseData["data"] = {}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(responseData).encode('utf-8'))
                return

            uiTimeOut = float(UI_ACTION_TIMEOUT)
            uiActionData = self._GetUIAction(requesData, timeout=uiTimeOut)

            responseData = dict()
            if uiActionData is None:
                responseData["error"] = -1
                responseData["errstr"] = "time out, get nothing from ui"
                responseData["data"] = {}
            else:
                responseData["error"] = 0
                responseData["errstr"] = ""
                responseData["data"] = uiActionData

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(responseData).encode('utf-8'))
        except KeyError as e:
            LOG.error('do_Post error: %s', e)


class HTTPServerThread(threading.Thread):
    """
    HTTP Server Thread implement
    """
    def __init__(self, serverPort):
        threading.Thread.__init__(self)
        self.__serverPort = serverPort
        self.__server = HTTPServer(('', self.__serverPort), ResquestHandler)

    def run(self):
        """
        Http server thread run funciton
        :return:
        """
        self.__server.serve_forever()

    def finish(self):
        """
        Stop http server thread
        :return:
        """
        self.__server.shutdown()


class HttpServer(object):
    """
    Socket Server implement for communication with AIClient
    """
    def __init__(self):
        self.__sendQueue = SEND_QUEUE
        self.__recvQueue = RECV_QUEUE
        self.__httpServerThread = None

    def Initialize(self, cfg):
        """
        Initialize this module, load config from cfg
        :param cfg:
        :return: True or false
        """
        self.__httpServerThread = HTTPServerThread(cfg['recv_port'])
        self.__httpServerThread.setDaemon(True)
        self.__httpServerThread.start()
        LOG.info('Start HTTP, listen port: %s', cfg['recv_port'])
        return True

    def Finish(self):
        """
        Finish this module
        :return:
        """
        if self.__httpServerThread is not None:
            self.__httpServerThread.finish()

    def Send(self, msgBuff):
        """
        Send the msgBuff to HTTP Server
        :param msgBuff: the msg buff to be sent
        :return:
        """
        self.__sendQueue.put_nowait(msgBuff)

    def Recv(self):
        """
        Receive the msg from HTTP Server
        :return: A list contains the msgs received
        """
        msgBuffList = []
        while not self.__recvQueue.empty():
            msgBuff = self.__recvQueue.get_nowait()
            msgBuffList.append(msgBuff)

        return msgBuffList
