# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import signal
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT_DIR, "log")
sys.path.append(ROOT_DIR)

from aiclient.start_service import ActionExecute
from aiclient.py_logger import setup_logging
from aiclient.aiclientapi.tool_manage import communicate_config as com_config

pause_flag = False


class Main(object):

    def __init__(self):
        setup_logging()
        self.action_execute_inst = ActionExecute()

    def init(self):
        return self.action_execute_inst.init()

    def exit_adb(self):
        if sys.platform.startswith("linux"):
            # kill adb
            time.sleep(5)
            cmd_str = "ps -ef|grep 'adb -s' |grep -v grep |awk '{print $2}'|xargs kill -9"
            os.system(cmd_str)

    def finish(self):
        self.action_execute_inst.finish()
        self.exit_adb()

    def run(self):
        self.action_execute_inst.run()

    def restart_ai(self):
        self.action_execute_inst.restart_ai()

    def start_game(self):
        self.action_execute_inst.start_game()

    def pause_ai(self):
        self.action_execute_inst.pause_ai()

    def restore_ai(self):
        self.action_execute_inst.restore_ai()

    def stop_ai(self):
        self.action_execute_inst.stop_ai()

    def add_signal(self):

        def exit_aiclient(sig_num, frame):
            print("begin to stop aiclient......")
            self.finish()
            exit(1)

        def restart_ai(siga_num, frame):
            self.restart_ai()
            self.start_game()

        def pause_ai(sig_num, frame):
            global pause_flag
            if not pause_flag:
                self.pause_ai()
                pause_flag = True
            else:
                self.restore_ai()
                pause_flag = False

        if sys.platform.startswith("win"):
            pass
        elif sys.platform.startswith("linux"):
            # signal.SIGUSR1 restart sig, signal.SIGUSR2 pause and restore sig
            signal.signal(signal.SIGUSR1, exit_aiclient)
            # signal.signal(signal.SIGUSR1, restart_ai)
            signal.signal(signal.SIGUSR2, pause_ai)


def set_com_config():
    com_config.terminate = False
    com_config.test_id = "0"
    com_config.game_id = 0
    com_config.game_version = "0"
    com_config.runtimes = 0


def start_ai():
    set_com_config()
    main_inst = Main()
    try:
        if main_inst.init():
            main_inst.add_signal()
            main_inst.run()
        main_inst.finish()
    except KeyboardInterrupt:
        print("KeyboardInterrupt .......................")
        main_inst.finish()


if __name__ == "__main__":
    start_ai()
