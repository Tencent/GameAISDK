# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import time
import logging
from ....config_manager.common.utils import is_dir_has_file, get_files_count, save_file, load_file
from ....subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from ....common.utils import backend_service_monitor


class AutoLabelImages(object):
    SERVICE_NAME = 'auto_label'

    def __init__(self, logger=None):
        self._logger = logger
        self.__auto_label_path = ""

        # set model api path
        ai_sdk_path = os.environ.get('AI_SDK_PATH')
        if not ai_sdk_path:
            raise Exception('environment AI_SDK_PATH is not set')
        self.__refine_det_path = os.path.join(ai_sdk_path, "Modules", "RefineDet")

    @property
    def auto_label_path(self):
        return self.__auto_label_path

    @auto_label_path.setter
    def auto_label_path(self, label_path):
        if not isinstance(label_path, (str, )):
            msg = "auto_label_path type error, only support str, type:{}".format(type(label_path))
            print(msg) if self._logger is None else self._logger.info(msg)
            return
        self.__auto_label_path = label_path

    def begin_label(self):
        # ...................auto label subprocess begin..................
        if not os.path.exists(self.__refine_det_path):
            msg = "refine_det_path Path {} is not exist".format(self.__refine_det_path)
            print(msg) if self._logger is None else self._logger.info(msg)
            return msg

        has_image = is_dir_has_file(self.__auto_label_path)
        if not has_image:
            msg = "failed, no image in {}, please check".format(self.__auto_label_path)
            print(msg) if self._logger is None else self._logger.info(msg)
            return msg

        current_path = os.getcwd()
        # set current work dir
        os.chdir(self.__refine_det_path)
        run_program = "python detect_mutilple_images.py --test_images {}".format(self.__auto_label_path)
        is_ok, desc = bsa.start_service(service_name=self.SERVICE_NAME, run_programs=[run_program],
                                        process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                        callback_func=backend_service_monitor)
        os.chdir(current_path)

        if not is_ok:
            msg = "open action sample failed, {}".format(desc)
            print(msg) if self._logger is None else self._logger.error(msg)
            return msg
        else:
            msg = "run action sample create pid: {} SubProcess".format(bsa.get_pids(self.SERVICE_NAME))
            print(msg) if self._logger is None else self._logger.info(msg)

        # ...................Auto label subprocess end..................
        image_count = get_files_count(self.__auto_label_path)
        json_file_count = get_files_count(self.__auto_label_path, ".json")
        while json_file_count < image_count:
            msg = "json count is {}/{}".format(json_file_count, image_count)
            print(msg) if self._logger is None else self._logger.info(msg)

            time.sleep(1.0)
            json_file_count = get_files_count(self.__auto_label_path, ".json")
        msg = "auto label image completed, will kill subprocess: {}".format(bsa.get_pids(self.SERVICE_NAME))
        print(msg) if self._logger is None else self._logger.info(msg)
        bsa.stop_service(service_name=self.SERVICE_NAME)
        msg = "auto label image subprocess killed successful: {}".format(bsa.get_pids(self.SERVICE_NAME))
        print(msg) if self._logger is None else self._logger.info(msg)
        return msg


logger = logging.getLogger('sdktool')
auto_label_image_inst = AutoLabelImages(logger)
