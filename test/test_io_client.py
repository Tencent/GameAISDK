# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging.config
import os
import sys
import time
import unittest
from unittest import TestCase
from unittest import mock

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORK_DIR, 'bin/pyIOService'))

from IOService import IOService
from common.Define import *

DEFAULT_TASK_CFG_PATH = '/cfg/task/io/IOTask.json'
DEFAULT_PLATFORM_CFG_PATH = '../cfg/platform/IO.ini'
DEFAULT_LOG_CFG_FILE = '../cfg/platform/IOLog.ini'

os.makedirs('../log/IOService', exist_ok=True)
logging.config.fileConfig(DEFAULT_LOG_CFG_FILE)
LOG = logging.getLogger('IOService')

ai_sdk_path = os.getenv('AI_SDK_PATH', '..')
TASK_CFG_PATH = ai_sdk_path + DEFAULT_TASK_CFG_PATH
LOG.info('Task Cfg Path: {}'.format(TASK_CFG_PATH))

# mock testcase data
mock_client_data = {'msg_id': MSG_ID_CLIENT_DATA, 'key': '0', 'frame': None, 'frame_seq': 0,
                    'send_img_type': RAW_IMG_SEND_TYPE}
mock_client_req = {'msg_id': MSG_ID_CLIENT_REQ, 'key': '0'}
mock_client_change_game_state = {'msg_id': MSG_ID_CHANGE_GAME_STATE, 'key': '0',
                                 'game_state': GAME_STATE_START}
mock_client_pause = {'msg_id': MSG_ID_PAUSE, 'key': '0'}
mock_client_restore = {'msg_id': MSG_ID_RESTORE, 'key': '0'}
mock_client_restart = {'msg_id': MSG_ID_RESTART, 'key': '0'}


class TestIOWithClient(TestCase):
    def setUp(self):
        self.io_service = IOService(taskCfgPath=TASK_CFG_PATH,
                                    platformCfgPath=DEFAULT_PLATFORM_CFG_PATH)

    def tearDown(self):
        self.io_service.Finish()

    def test_recv_client(self):
        ret = self.io_service.Initialize()
        self.assertEqual(ret, True)

        self.io_service._IOService__clientSocket.Recv = mock.MagicMock(
            return_value=[mock_client_data])
        self.assertEqual(self.io_service._IOService__msgHandler._UpdateClientMsg(), True)

        self.io_service._IOService__clientSocket.Recv = mock.MagicMock(
            return_value=[mock_client_req])
        self.assertEqual(self.io_service._IOService__msgHandler._UpdateClientMsg(), True)

        self.io_service._IOService__clientSocket.Recv = mock.MagicMock(
            return_value=[mock_client_change_game_state])
        self.assertEqual(self.io_service._IOService__msgHandler._UpdateClientMsg(), True)

        self.io_service._IOService__clientSocket.Recv = mock.MagicMock(
            return_value=[mock_client_pause])
        self.assertEqual(self.io_service._IOService__msgHandler._UpdateClientMsg(), True)

        self.io_service._IOService__clientSocket.Recv = mock.MagicMock(
            return_value=[mock_client_restore])
        self.assertEqual(self.io_service._IOService__msgHandler._UpdateClientMsg(), True)

        self.io_service._IOService__clientSocket.Recv = mock.MagicMock(
            return_value=[mock_client_restart])
        self.assertEqual(self.io_service._IOService__msgHandler._UpdateClientMsg(), True)


if __name__ == '__main__':
    unittest.main()
