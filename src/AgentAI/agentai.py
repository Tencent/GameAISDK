# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import argparse
import platform
import signal
import logging
import logging.config
import traceback

sys.path.append('AgentAI')
sys.path.append('AgentAI/protocol')
sys.path.append('API')

#import os
#os.environ["CUDA_VISIBLE_DEVICES"] = ""

from aiframework.AIFrameWork import AIFrameWork

logPath = "../log/Agent"
if not os.path.exists(logPath):
    os.mkdir(logPath)

logging.config.fileConfig('../cfg/platform/AgentLog.ini')
aiFramework = AIFrameWork()

def SigExit(sigNum, frame):
    """
    signal handler for SIGINT
    """
    aiFramework.Finish()
    sys.exit(0)

def SigStopAction(sigNum, frame):
    """
    signal handler for SIGUSR1
    """
    aiFramework.StopAIAction()

def SigRestartAction(sigNum, frame):
    """
    signal handler for SIGUSR2
    """
    aiFramework.RestartAIAction()

if __name__ == '__main__':
    platformType = platform.system()
    if platformType == 'Linux':
        signal.signal(signal.SIGINT, SigExit)
        signal.signal(signal.SIGUSR1, SigStopAction)
        signal.signal(signal.SIGUSR2, SigRestartAction)

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--mode', type=str, default='test', choices=['test', 'train'], help='mode')
    parser.add_argument('--index', type=int, default=1, help='index')
    args = parser.parse_args()

    try:
        if args.mode == 'train':
            from aiframework.IMTrainFrameWork import IMTrainFrameWork
            imTrainFrameWork = IMTrainFrameWork()
            if imTrainFrameWork.Init() is True:
                imTrainFrameWork.Train()
            imTrainFrameWork.Finish()
        else:
            if aiFramework.Init() is True:
                aiFramework.Run(True)
            aiFramework.Finish()
    except Exception as e:
        msg = traceback.format_exc()
        logger = logging.getLogger('agent')
        logger.error('exception: {0} msg: {1}'.format(e, msg))
