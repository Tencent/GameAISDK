# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import logging
import shutil
from .define import WIN_PYPLOT_FONT, LINUX_PYPLOT_FONT


logger = logging.getLogger('sdktool')


def rm_dir_files(path):
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except Exception as err:
        msg = "rm path: {} failed, err:{}".format(path, err)
        logger.error(msg)
        return False, msg
    return True, ""


def get_font():
    font_type = WIN_PYPLOT_FONT if sys.platform == 'win32' else LINUX_PYPLOT_FONT
    return font_type, False


def backend_service_monitor(service_state, desc, *args, **kwargs):
    """Backend process status service

    :param service_state: service state, 0 - exception; 1 - running; 2 - over, see src.subprocess_service.process_timer
    :param desc: describe all process info
    :param args: extend args
    :param kwargs: extend args
    """
    logger.info('service state({}), {}'.format(service_state, desc))
