# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import signal
import logging.config

__current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['AI_SDK_TOOL_PATH'] = __current_dir
__ai_sdk_path = os.path.abspath(os.path.join(__current_dir, '..', '..'))
if os.path.exists(os.path.join(__ai_sdk_path, 'bin')):
    os.environ['AI_SDK_PATH'] = __ai_sdk_path

from src.ui.main_window.tool_main_window import SDKMainWindow
from src.ui.main_window.tool_window import ui, tool_app
from src.subprocess_service.subprocess_service_manager import backend_service_manager
main_window = SDKMainWindow(ui)


def sig_handle(sig_num, _):
    LOG.info("signal {} received, is going to shut...".format(sig_num))
    main_window.finish()
    backend_service_manager.exit_all_service()
    exit(-1)


if __name__ == "__main__":
    logging.config.fileConfig("cfg/log.ini")
    LOG = logging.getLogger('sdktool')
    LOG.setLevel(logging.DEBUG)
    signal.signal(signal.SIGINT, sig_handle)
    try:
        ui.setup_ui(main_window)
        main_window.show()
        main_window.init()
        tool_app.exec_()
    except Exception as e:
        print(e)
        backend_service_manager.exit_all_service()
