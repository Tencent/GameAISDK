# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import json
import traceback
from src.config_manager.common.utils import make_targz, load_file, save_file, delete_file


class UserLabelImage(object):
    # CUR_DIR = os.path.dirname(os.path.abspath(__file__))
    # CACHE_LABEL_PATH_FILE = os.path.join(CUR_DIR, "../../../../../../data/cache/user_label_path.txt")

    def __init__(self, logger=None):
        self.__user_label_path = None
        self._logger = logger

        # # load previous read path
        # self.__user_label_path = load_file(self.CACHE_LABEL_PATH_FILE)
        # if not os.path.exists(self.__user_label_path):
        #     self.__user_label_path = ""

    @property
    def user_label_path(self):
        return self.__user_label_path

    @user_label_path.setter
    def user_label_path(self, label_path):
        if not isinstance(label_path, str):
            msg = "label_path type error, only support str, type:{}".format(type(label_path))
            print(msg) if self._logger is None else self._logger.info(msg)
            return
        # save_file(self.CACHE_LABEL_PATH_FILE, label_path)
        self.__user_label_path = label_path

    def save_label2file(self, file_name, image_path_name, scene_name, labels):
        # save image label to file
        label_json_dict = dict()
        label_json_dict["fileName"] = file_name
        label_json_dict["scene"] = scene_name
        label_json_dict["labels"] = list()

        for idx, label_obj in enumerate(labels):
            label_dict = {}
            label_dict["label"] = label_obj.get("label")
            label_dict["name"] = label_obj.get("name", "")
            label_dict["clickNum"] = label_obj.get("click_num")

            label_dict["x"] = min(int(label_obj.get("points")[0]), int(label_obj.get("points")[2]))
            label_dict["y"] = min(int(label_obj.get("points")[1]), int(label_obj.get("points")[3]))
            label_dict["w"] = abs(int(label_obj.get("points")[0]) - int(label_obj.get("points")[2]))
            label_dict["h"] = abs(int(label_obj.get("points")[1]) - int(label_obj.get("points")[3]))

            label_json_dict["labels"].append(label_dict)

        # save json file
        json_file_name = image_path_name[: image_path_name.rfind('.')] + ".json"
        if len(label_json_dict["labels"]) > 0:
            with open(json_file_name, "w") as f:
                json.dump(label_json_dict, f, indent=4, separators=(',', ':'))

    def load_label_json(self, image_path_name):
        # read label json file
        json_file = image_path_name[:image_path_name.rfind('.')] + ".json"
        if os.path.exists(json_file) is False:
            return {}
        try:
            with open(json_file, 'r') as f:
                label_json_dict = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            msg = traceback.format_exc()
            print(msg) if self._logger is None else self._logger.error(msg)
            return {}

        labels = label_json_dict.get("labels")
        label_json_dict["labels"] = []
        for idx, label_obj in enumerate(labels):
            label_dict = {}
            label_dict["label"] = label_obj.get("label")
            label_dict["name"] = label_obj.get("name", "")
            label_dict["click_num"] = label_obj.get("clickNum")

            points = [
                label_obj.get("x"),
                label_obj.get("y"),
                label_obj.get("x") + label_obj.get("w"),
                label_obj.get("y") + label_obj.get("h")]
            label_dict["points"] = points
            label_json_dict["labels"].append(label_dict)
        return label_json_dict

    def delete_image_and_label(self, image_path_name):
        json_file = image_path_name[:image_path_name.rfind('.')] + ".json"
        delete_file(json_file)
        delete_file(image_path_name)


logger = logging.getLogger('sdktool')
user_label_image_inst = UserLabelImage(logger)
