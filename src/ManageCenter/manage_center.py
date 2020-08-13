# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import argparse
import logging.config
import os
import platform
import signal
import sys
import traceback

sys.path.insert(0, 'pyManageCenter')
sys.path.append('pyManageCenter/protocol')

from ManageCenter import ManageCenter

DEFAULT_TASK_CFG_PATH = '/cfg/task/mc/MCTask.json'
DEFAULT_PLATFORM_CFG_PATH = '../cfg/platform/MC.ini'
DEFAULT_LOG_CFG_FILE = '../cfg/platform/MCLog.ini'

os.makedirs('../log/ManageCenter', exist_ok=True)
logging.config.fileConfig(DEFAULT_LOG_CFG_FILE)
LOG = logging.getLogger('ManageCenter')

ai_sdk_path = os.getenv('AI_SDK_PATH', '..')
TASK_CFG_PATH = ai_sdk_path + DEFAULT_TASK_CFG_PATH
LOG.info('Task Cfg Path: {}'.format(TASK_CFG_PATH))


def main():
    """
    ManageCenter main entry
    :return:
    """
    try:
        parser = argparse.ArgumentParser(description='')
        parser.add_argument('--runType', type=str, default='AI',
                            help='The run type of services, ex. AI or UI or UI+AI, default is AI')
        args = parser.parse_args()

        manage_center = ManageCenter(taskCfgPath=TASK_CFG_PATH,
                                     platformCfgPath=DEFAULT_PLATFORM_CFG_PATH)

        def SigHandle(sigNum, frame):
            """
            signal handler for SIGUSR1 or SIGINT, exit this process
            """
            manage_center.SetExited()

        platformType = platform.system()
        if platformType == 'Linux':
            signal.signal(signal.SIGUSR1, SigHandle)
        signal.signal(signal.SIGINT, SigHandle)

        if manage_center.Initialize(args.runType):
            LOG.info('==== ManageCenter is going to run ====')
            manage_center.Run()
            manage_center.Finish()
            LOG.info('==== ManageCenter exit.... ====')
        else:
            LOG.error('==== ManageCenter Init failed! ====')

    except Exception as e:
        traceMsg = traceback.format_exc()
        LOG.error('exception: {0} trace msg: {1}'.format(e, traceMsg))


if __name__ == '__main__':
    main()
