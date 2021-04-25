# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

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
import argparse

sys.path.insert(0, 'pyIOService')
sys.path.append('pyIOService/protocol')

from IOService import IOService
from util.config_path_mgr import SYS_CONFIG_DIR, DEFAULT_USER_CONFIG_DIR

os.makedirs('../log/IOService', exist_ok=True)

IO_TASK_CFG_FILE = 'cfg/task/io/IOTask.json'
IO_CFG_FILE = 'cfg/platform/IO.ini'
IO_LOF_CFG_FILE = 'cfg/platform/IOLog.ini'

LOG = None


def main():
    """
    IOService main entry
    :return:
    """
    global LOG
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--cfgpath', type=str, default='', help='config path')
    args = parser.parse_args()

    os.environ['AI_SDK_PROJECT_PATH'] = os.path.dirname(args.cfgpath) if args.cfgpath else DEFAULT_USER_CONFIG_DIR

    task_cfg_path = os.path.join(os.environ.get('AI_SDK_PROJECT_PATH'), IO_TASK_CFG_FILE)
    platform_cfg_path = os.path.join(SYS_CONFIG_DIR, IO_CFG_FILE)
    log_cfg_path = os.path.join(SYS_CONFIG_DIR, IO_LOF_CFG_FILE)

    logging.config.fileConfig(log_cfg_path)
    LOG = logging.getLogger('IOService')

    LOG.info('Task Cfg Path: {}'.format(task_cfg_path))

    try:
        io_service = IOService(taskCfgPath=task_cfg_path,
                               platformCfgPath=platform_cfg_path)

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
