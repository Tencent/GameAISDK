# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

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

from aiframework.AIFrameWork import AIFrameWork
from util.config_path_mgr import SYS_CONFIG_DIR
# os.environ["CUDA_VISIBLE_DEVICES"] = ""

logPath = "../log/Agent"
if not os.path.exists(logPath):
    os.makedirs(logPath)

AGENT_LOG_FILE = 'cfg/platform/AgentLog.ini'

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
    sys.exit(1)

def SigRestartAction(sigNum, frame):
    """
    signal handler for SIGUSR2
    """
    aiFramework.RestartAIAction()

def InstallSignalHandler():
    platformType = platform.system()
    if platformType == 'Linux':
        signal.signal(signal.SIGINT, SigExit)
        signal.signal(signal.SIGUSR1, SigStopAction)
        signal.signal(signal.SIGUSR2, SigRestartAction)

def SetLogLevel(logLevel):
    file_config = os.path.join(SYS_CONFIG_DIR, AGENT_LOG_FILE)
    logging.config.fileConfig(file_config)

    logger = logging.getLogger('agent')
    if logLevel == 'debug':
        logger.setLevel(logging.DEBUG)
    elif logLevel == 'info':
        logger.setLevel(logging.INFO)
    elif logLevel == 'warnning':
        logger.setLevel(logging.WARNING)
    elif logLevel == 'error':
        logger.setLevel(logging.ERROR)
    else:
        pass

def RunFrameWork(runMode):
    if runMode == 'train':
        logger = logging.getLogger('agent')
        logger.info('train the model, runMode:{0}'.format(runMode))
        from aiframework.IMTrainFrameWork import IMTrainFrameWork
        imTrainFrameWork = IMTrainFrameWork()
        if imTrainFrameWork.Init() is True:
            imTrainFrameWork.Train()
        imTrainFrameWork.Finish()
    else:
        logger = logging.getLogger('agent')
        logger.info('run the model, runMode:{0}'.format(runMode))
        if aiFramework.Init() is True:
            logger.info('after init, runMode:{0}'.format(runMode))
            aiFramework.Run(True)
        logger.info('finish run ai framework, runMode:{0}'.format(runMode))
        aiFramework.Finish()

def Main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--mode', type=str, default='test', choices=['test', 'train'], help='set run mode')
    parser.add_argument('--loglevel', type=str, default='default',
                        choices=['default', 'debug', 'info', 'warnning', 'error'], help='set log level')
    parser.add_argument('--debug', type=bool, default=False, help='debug with sdktool (True/False)')
    parser.add_argument('--cfgpath', type=str, default='', help='config path')

    args = parser.parse_args()
    if args.cfgpath:
        cfg_path = args.cfgpath
        if os.path.isfile(cfg_path):
            cfg_dir= os.path.dirname(cfg_path)
            os.environ['AI_SDK_PROJECT_PATH'] = cfg_dir
            os.environ['AI_SDK_PROJECT_FILE_PATH'] = cfg_path
        else:
            os.environ['AI_SDK_PROJECT_PATH'] = cfg_path
            proj_name = os.path.splitext(os.path.basename(cfg_path))[0]
            file_path = os.path.join(cfg_path, '%s.prj' % proj_name)
            if os.path.exists(file_path):
                os.environ['AI_SDK_PROJECT_FILE_PATH'] = file_path
            else:
                file_path = os.path.join(cfg_path, 'prj.aisdk')
                if os.path.exists(file_path):
                    os.environ['AI_SDK_PROJECT_FILE_PATH'] = file_path
                else:
                    raise Exception('project config file(%s) is not found' % file_path)


    InstallSignalHandler()

    try:
        SetLogLevel(args.loglevel)
        RunFrameWork(args.mode)
    except Exception as e:
        msg = traceback.format_exc()
        logger = logging.getLogger('agent')
        logger.error('exception: {0} msg: {1}'.format(e, msg))

if __name__ == '__main__':
    Main()
