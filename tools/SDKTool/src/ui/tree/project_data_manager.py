# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import json
import logging
from collections import OrderedDict

from ...common.define import RunType, PROCESS_NAMES, DEFAULT_LONG_EDGE, UI_PATH, TASK_PATH, REFER_PATH, path_keys, \
    AI_CONFIG_IM_ACTION_PATH, AI_CONFIG_DQN_ACTION_PATH, AI_CONFIG_RAINBOW_ACTION_PATH, AI_CONFIG_IM_LEARNING_PATH, \
    AI_CONFIG_DQN_LEARNING_PATH, AI_CONFIG_RAINBOW_LEARNING_PATH, DEFAULT_DATA_IMAGES_FOLDER
from ...common.singleton import Singleton


logger = logging.getLogger("sdktool")


def change_image_path(config, repl, text):
    """ 修改配置中配置项属于文件路径的数值

    :param config: dict，配置项
    :param repl: 需要被替换的子字符串
    :param text: 将要替换的字符串
    :return:
    """
    if not isinstance(config, (dict, OrderedDict)):
        return

    repl = repl.replace('\\', '/')
    for key, value in config.items():
        if key in path_keys:
            # 当前路径下不存在图像文件时，需要更改图像文件路径
            new_value = value.replace('\\', '/')
            if repl in new_value:
                # 兼容旧目录结构
                new_value = new_value.replace(repl, text)

            config[key] = new_value

        elif isinstance(value, (dict, OrderedDict)):
            change_image_path(value, repl, text)
        elif isinstance(value, list):
            for sub_item in value:
                change_image_path(sub_item, repl, text)


class MediaSourceNode(object):
    """
    选择媒体的节点所保存的信息
    """

    def __init__(self):
        self.type = None
        self.url = None
        # self.is_portrait = False
        self.phone_serials = []
        self.select_phone_serial = None
        self.long_edge = DEFAULT_LONG_EDGE

    def is_ready(self):
        if self.select_phone_serial is not None:
            return True
        return False


class ProjectDataManager(metaclass=Singleton):
    def __init__(self):
        self.__name = None
        self.__old_project_data_path = None
        self.__old_sdk_data_path = None
        self.__project_data_path = None
        self.__sdk_data_path = None
        self.__project_file_path = None
        self.__project_dir_path = None
        self.__media_source = None
        self.__run_type = None
        self.__process_log_level = None
        self._init()

    def _init(self):
        self.__name = None  # 名称
        self.__project_data_path = None  # 工程路径
        self.__sdk_data_path = None  # 数据路径
        self.__media_source = None  # 媒体类型
        self.__run_type = RunType.UI_AI  # 运行方式
        self.__process_log_level = dict()  # 日志级别
        # self.__multi_resolution = False           # 是否支持多分辨率
        self.__project_file_path = None
        self.__project_dir_path = None
        self.__old_project_data_path = None
        self.__old_sdk_data_path = None
        for name in PROCESS_NAMES:
            self.__process_log_level[name] = 'DEBUG'

    def clear(self):
        self._init()

    def set_name(self, name: str):
        self.__name = name
        self.__old_project_data_path = os.path.join(self.__project_dir_path, 'data', self.__name)
        self.__old_sdk_data_path = os.path.join('data', self.__name)
        self.__project_data_path = os.path.join(self.__project_dir_path, DEFAULT_DATA_IMAGES_FOLDER)
        self.__sdk_data_path = DEFAULT_DATA_IMAGES_FOLDER

    def get_name(self):
        return self.__name

    def get_project_data_path(self):
        return self.__project_data_path

    def get_sdk_data_path(self):
        return self.__sdk_data_path

    def _rename_old_folder_name(self):
        """ 修改旧目录文件夹名称，并修改所有配置项

        :return:
        """
        if os.path.exists(self.__old_project_data_path):
            if os.path.exists(self.__project_data_path):
                os.rmdir(self.__project_data_path)
            os.rename(self.__old_project_data_path, self.__project_data_path)
        self._convert_all_files()

    def _convert_cfg_files(self, file_path):
        """ 修改配置文件中的文件路径

        :param file_path:
        :return:
        """
        if not os.path.exists(file_path):
            return

        config = {}
        with open(file_path, encoding='utf-8') as fd:
            content = fd.read()
            config = json.loads(content, object_pairs_hook=OrderedDict)
            if config:
                change_image_path(config, self.__old_sdk_data_path, DEFAULT_DATA_IMAGES_FOLDER)

        if config:
            with open(file_path, 'w', encoding='utf-8') as fd:
                fd.write(json.dumps(config, indent=4, ensure_ascii=False))

    def _convert_all_files(self):
        self._convert_cfg_files(os.path.join(self.__project_dir_path, UI_PATH))
        self._convert_cfg_files(os.path.join(self.__project_dir_path, TASK_PATH))
        self._convert_cfg_files(os.path.join(self.__project_dir_path, REFER_PATH))

        self._convert_cfg_files(os.path.join(self.__project_dir_path, AI_CONFIG_IM_ACTION_PATH))
        self._convert_cfg_files(os.path.join(self.__project_dir_path, AI_CONFIG_DQN_ACTION_PATH))
        self._convert_cfg_files(os.path.join(self.__project_dir_path, AI_CONFIG_RAINBOW_ACTION_PATH))
        self._convert_cfg_files(os.path.join(self.__project_dir_path, AI_CONFIG_IM_LEARNING_PATH))
        self._convert_cfg_files(os.path.join(self.__project_dir_path, AI_CONFIG_DQN_LEARNING_PATH))
        self._convert_cfg_files(os.path.join(self.__project_dir_path, AI_CONFIG_RAINBOW_LEARNING_PATH))

    def adjust_project_file_path(self):
        if self.__project_file_path is None:
            raise ValueError('please set project file path first')

        rename_file = False
        project_dir, file_name = os.path.split(self.__project_file_path)
        if file_name.endswith('.aisdk'):
            project_name = os.path.basename(project_dir)
            new_project_file_path = os.path.join(project_dir, '%s.prj' % project_name)
            if os.path.exists(new_project_file_path):
                os.remove(new_project_file_path)
            os.rename(self.__project_file_path, new_project_file_path)
            rename_file = True
            self.__project_file_path = new_project_file_path

            self.set_name(project_name)
            self._rename_old_folder_name()
        return rename_file, self.__project_file_path

    def set_project_file_path(self, project_file_path):
        if not os.path.exists(project_file_path):
            raise ValueError('project file(%s) is not found' % project_file_path)

        self.__project_file_path = project_file_path

        _, file_name = os.path.split(project_file_path)
        project_name = os.path.splitext(file_name)[0]

        cwd = os.getcwd()
        cwd_linux_format = cwd.replace('\\', '/')
        project_file_path_linux_format = project_file_path.replace('\\', '/')
        if cwd_linux_format in project_file_path_linux_format:
            project_dir_path = os.path.dirname(project_file_path_linux_format).replace(cwd_linux_format, '')
        else:
            project_dir_path = os.path.dirname(project_file_path_linux_format)
        self.__project_dir_path = project_dir_path.strip('/')
        self.set_name(project_name)

    def change_to_sdk_path(self, tool_path: str):
        sdk_path = tool_path.replace('\\', '/').replace(self.__project_data_path.replace('\\', '/'),
                                                        self.__sdk_data_path.replace('\\', '/'))
        return sdk_path

    def change_to_tool_path(self, sdk_path: str):
        tool_path = sdk_path.replace('\\', '/').replace(self.__sdk_data_path.replace('\\', '/'),
                                                        self.__project_data_path.replace('\\', '/'))
        if not os.path.exists(tool_path):
            logger.error('file(%s) is not found!' % tool_path)
        return tool_path

    def get_project_path(self):
        return self.__project_dir_path

    def set_media_source(self, source: MediaSourceNode):
        self.__media_source = source

    def get_media_source(self):
        return self.__media_source

    def get_run_type(self):
        return self.__run_type

    def set_run_type(self, run_type: RunType):
        self.__run_type = run_type

    def is_ready(self):
        if self.__name is None:
            return False
        return self.__media_source.is_ready()

    def get_log_level(self):
        return self.__process_log_level

    def set_log_level(self, log_level):
        self.__process_log_level = log_level


g_project_data_mgr = ProjectDataManager()
