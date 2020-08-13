# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging.config
import os
import platform
import signal
import sys
import traceback

sys.path.insert(0, 'pyIOService')
sys.path.append('pyIOService/protocol')

from IOService import IOService

DEFAULT_TASK_CFG_PATH = '/cfg/task/io/IOTask.json'
DEFAULT_PLATFORM_CFG_PATH = '../cfg/platform/IO.ini'
DEFAULT_LOG_CFG_FILE = '../cfg/platform/IOLog.ini'

os.makedirs('../log/IOService', exist_ok=True)
logging.config.fileConfig(DEFAULT_LOG_CFG_FILE)
LOG = logging.getLogger('IOService')

ai_sdk_path = os.getenv('AI_SDK_PATH', '..')
TASK_CFG_PATH = ai_sdk_path + DEFAULT_TASK_CFG_PATH
LOG.info('Task Cfg Path: {}'.format(TASK_CFG_PATH))


def main():
    """
    IOService main entry
    :return:
    """
    try:
        io_service = IOService(taskCfgPath=TASK_CFG_PATH,
                               platformCfgPath=DEFAULT_PLATFORM_CFG_PATH)

        def SigHandle(sigNum, frame):
            """
            signal handler for SIGUSR1 or SIGINT, exit this process
            """
            io_service.SetExited()

        platformType = platform.system()
        if platformType == 'Linux':
            signal.signal(signal.SIGUSR1, SigHandle)
        signal.signal(signal.SIGINT, SigHandle)

        if io_service.Initialize():
            LOG.info('==== IOService is going to run ====')
            io_service.Run()
            io_service.Finish()
            LOG.info('==== IOService exit.... ====')
        else:
            LOG.error('==== IOService Init failed! ====')

    except Exception as e:
        traceMsg = traceback.format_exc()
        LOG.error('exception: {0} trace msg: {1}'.format(e, traceMsg))


if __name__ == '__main__':
    main()
