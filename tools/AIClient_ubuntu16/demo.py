
import os
import sys
import signal

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

    def finish(self):
        self.action_execute_inst.finish()

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
            signal.signal(signal.SIGUSR1, restart_ai)
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
        main_inst.finish()


if __name__ == "__main__":
    start_ai()
