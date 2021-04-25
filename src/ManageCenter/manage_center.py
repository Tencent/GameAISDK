# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

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
from util.config_path_mgr import SYS_CONFIG_DIR, DEFAULT_USER_CONFIG_DIR

os.makedirs('../log/ManageCenter', exist_ok=True)

MC_TASK_CFG_FILE = 'cfg/task/mc/MCTask.json'
MC_CFG_FILE = 'cfg/platform/MC.ini'
MC_LOG_CFG_FILE = 'cfg/platform/MCLog.ini'

LOG = None


def main():
    """
    ManageCenter main entry
    :return:
    """
    global LOG
    try:
        parser = argparse.ArgumentParser(description='')
        parser.add_argument('--cfgpath', type=str, default='', help='config path')
        parser.add_argument('--runType', type=str, default='AI',
                            help='The run type of services, ex. AI or UI or UI+AI, default is AI')
        args = parser.parse_args()
        os.environ['AI_SDK_PROJECT_PATH'] = os.path.dirname(args.cfgpath) if args.cfgpath else DEFAULT_USER_CONFIG_DIR

        task_cfg_path = os.path.join(os.environ.get('AI_SDK_PROJECT_PATH'), MC_TASK_CFG_FILE)
        platform_cfg_path = os.path.join(SYS_CONFIG_DIR, MC_CFG_FILE)
        log_cfg_path = os.path.join(SYS_CONFIG_DIR, MC_LOG_CFG_FILE)

        logging.config.fileConfig(log_cfg_path)
        LOG = logging.getLogger('ManageCenter')

        LOG.info('Task Cfg Path: {}'.format(task_cfg_path))

        manage_center = ManageCenter(taskCfgPath=task_cfg_path,
                                     platformCfgPath=platform_cfg_path)

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
