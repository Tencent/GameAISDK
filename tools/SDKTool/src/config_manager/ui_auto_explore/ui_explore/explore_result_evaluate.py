# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging

from ...common.utils import load_json_file
from ...ui_auto_explore.ui_explore_define import IMAGE_POSTFIX


class ExploreResultEvaluate(object):
    COVERAGE_FILE = "coverage.json"

    def __init__(self, logger=None):
        self.__result_evaluate_path = None
        self._logger = logger

    @property
    def result_evaluate_path(self):
        return self.__result_evaluate_path

    @result_evaluate_path.setter
    def result_evaluate_path(self, evaluate_path):
        if not isinstance(evaluate_path, (str, )):
            msg = "result_evaluate_path type error, only support str, type: {}".format(type(evaluate_path))
            print(msg) if self._logger is None else self._logger.info(msg)
            return

        self.__result_evaluate_path = evaluate_path

    def graph_analysis_result(self):
        file_list = os.listdir(self.__result_evaluate_path)
        img_list = [item for item in file_list if item.split('.')[1] in IMAGE_POSTFIX]

        image_label_dict = dict()
        for item in img_list:
            key = item.split('.')[0]
            json_file = os.path.join(self.__result_evaluate_path, "{}.json".format(key))
            if os.path.exists(json_file):
                image_label_dict[key] = dict()
                image_label_dict[key]["image"] = item
                image_label_dict[key]["label"] = json_file

        msg = "images count {}, pairs count {}".format(len(img_list), len(image_label_dict))
        print(msg) if self._logger is None else self._logger.info(msg)

        for key, value in image_label_dict.items():
            json_file = os.path.join(self.__result_evaluate_path, value.get("label"))
            content = load_json_file(json_file)
            if not content or content.get("labels"):
                msg = "{} label is none".format(json_file)
                print(msg) if self._logger is None else self._logger.warning(msg)
                continue
            label_list = content.get("labels")
            cur_image = content.get("fileName")
            image_label_dict[key]["label_list"] = label_list
            image_label_dict[key]["file_name"] = cur_image
        return image_label_dict

    def __load_coverage_file(self):
        coverage_file = os.path.join(self.__result_evaluate_path, self.COVERAGE_FILE)
        if not os.path.exists(coverage_file):
            msg = "coverage file {} not exists".format(coverage_file)
            print(msg) if self._logger is None else self._logger.error(msg)
            return {}
        coverage_info = load_json_file(coverage_file)
        if not coverage_info:
            msg = "no content in coverage file"
            print(msg) if self._logger is None else self._logger.error(msg)
        return coverage_info

    def get_coverage_info(self):
        coverage_info = self.__load_coverage_file()
        return coverage_info.get("button", {}), coverage_info.get("scene", {})

    def get_coverage_detail(self):
        coverage_info = self.__load_coverage_file()
        return coverage_info.get("coverList", [])


logger = logging.getLogger('sdktool')
explore_result_evaluate_inst = ExploreResultEvaluate(logger)
