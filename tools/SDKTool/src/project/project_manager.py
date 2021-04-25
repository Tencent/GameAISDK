# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import json
from datetime import datetime
import platform
import shutil

from ..config_manager.ui.ui_manager import UIManager
from ..config_manager.task.task_manager import TaskManager
from ..config_manager.ai.ai_manager import AIManager
from ..common.define import RunTypeText, UI_PATH, TASK_PATH, REFER_PATH, DEFAULT_PROJECT_CONFIG_FOLDER, \
    DEFAULT_TASK_IO_CONFIG_FOLDER, DEFAULT_TASK_MC_CONFIG_FOLDER, DEFAULT_DATA_IM_CONFIG_FOLDER, \
    DEFAULT_DATA_IMAGES_FOLDER, AI_CONFIG_DIR
from ..common.singleton import Singleton
from ..context.app_context import g_app_context


DEFAULT_PROJECT_DIR = './project'
UI_CONFIG_DIR = 'cfg/task/ui'
TASK_CONFIG_DIR = 'cfg/task/gameReg'


class ProjectManager(metaclass=Singleton):
    def __init__(self):
        self.__project_name = None
        self.__project_path = None
        self.__project_property_file = None

    def __modify_path_seperator(self, p):
        """ 修改路径符

        :param p:
        :return:
        """
        _is_windows = platform.platform().lower().startswith('win')
        if _is_windows:
            p = os.path.abspath(p).replace('/', os.path.sep)
        else:
            p = os.path.abspath(p).replace('\\', os.path.sep)
        return p

    def __copy_default_config_files(self):
        """ 复制缺省的配置文件到新建的工程目录

        :return:
        """
        ai_sdk_tool_path = os.environ.get('AI_SDK_TOOL_PATH')
        if ai_sdk_tool_path:
            tpls_folder = os.path.join(ai_sdk_tool_path, DEFAULT_PROJECT_CONFIG_FOLDER)
            # copy config folders
            for item in [DEFAULT_TASK_IO_CONFIG_FOLDER, DEFAULT_TASK_MC_CONFIG_FOLDER]:
                src_folder = os.path.join(tpls_folder, item)
                dst_folder = os.path.join(self.__project_path, item)
                if not os.path.exists(dst_folder):
                    shutil.copytree(src_folder, dst_folder)

            # copy config files
            for item in [AI_CONFIG_DIR, TASK_CONFIG_DIR, DEFAULT_DATA_IM_CONFIG_FOLDER]:
                src_folder = os.path.join(tpls_folder, item)
                for f_name in os.listdir(src_folder):
                    src_file = os.path.join(src_folder, f_name)
                    dst_folder = os.path.join(self.__project_path, item)
                    if not os.path.exists(dst_folder):
                        os.makedirs(dst_folder)
                    dst_file = os.path.join(dst_folder, f_name)
                    if not os.path.isdir(dst_file) and not os.path.exists(dst_file):
                        shutil.copy2(src_file, dst_folder)

    def create(self, project_name: str) -> bool:
        """ 创建空的工程

        :param project_name:
        :return:
        """
        project_path = os.path.join(DEFAULT_PROJECT_DIR, project_name)
        if os.path.isdir(project_path):
            return None

        self.__project_name = project_name
        self.__project_path = self.__modify_path_seperator(project_path)
        os.environ['AI_SDK_PROJECT_PATH'] = self.__project_path
        self._create_project_dir()
        self.__project_property_file = os.path.join(self.__project_path, '%s.prj' % project_name)
        self.__create_property_file()
        self.__copy_default_config_files()

        return self.__project_property_file

    # 加载配置
    def load(self, project_file_path: str) -> bool:
        if not os.path.isfile(project_file_path):
            print('{} is not found!'.format(project_file_path))
            return False
        self.__project_property_file = project_file_path
        project_dir, file_name = os.path.split(project_file_path)

        self.__project_path = self.__modify_path_seperator(project_dir.rstrip('/').rstrip('\\'))
        os.environ['AI_SDK_PROJECT_PATH'] = self.__project_path

        if file_name.endswith('.aisdk'):
            self.__project_name = os.path.basename(self.__project_path)
        else:
            self.__project_name = os.path.splitext(file_name)[0]

        self.__copy_default_config_files()
        if not os.path.exists(self.__project_property_file):
            self.__create_property_file()

        # 加载工程属性
        multi_resolution = self.get_multi_resolution()
        # ProjectDataManager().set_multi_resolution(multi_resolution)

        node_name = self.get_left_tree_node_name()

        if 'UI' in node_name:
            #load ui config file
            ui_config_file = self.get_ui_file()
            if os.path.isfile(ui_config_file):
                ui_mgr = UIManager()
                if not ui_mgr.load_config(ui_config_file):
                    print('load {} failed!'.format(ui_config_file))
                    return False

        if 'Scene' in node_name:
            #load task and reger config file
            refer_file = self.get_refer_file()
            if not os.path.isfile(refer_file):
                refer_file = None

            # 任务配置
            task_file = self.get_task_file()
            if os.path.isfile(task_file):
                task_mgr = TaskManager()
                if not task_mgr.load_config(task_file, refer_file):
                    return False

        if 'AI' in node_name:
            #load ai config file
            ai_mgr = AIManager()
            if not ai_mgr.load_config(self.__project_path):
                return False

        self._create_project_dir()
        return True

    def clear(self) -> None:
        #clear ui config
        ui_mgr = UIManager()
        ui_mgr.clear_config()

        #clear task config
        task_mgr = TaskManager()
        task_mgr.clear_config()

        #clear ai config
        ai_mgr = AIManager()
        ai_mgr.clear_config()

    # 保存工程
    def save(self) -> bool:

        ui_mgr = UIManager()
        ui_config_file = self.get_ui_file()
        if not ui_mgr.dump_config(ui_config_file):
            print('save ui file failed!')
            return False

        task_mgr = TaskManager()
        task_file = self.get_task_file()
        refer_file = self.get_refer_file()
        if not task_mgr.dump_config(task_file, refer_file):
            print('save task file failed!')
            return False

        ai_mgr = AIManager()
        if not ai_mgr.dump_config(self.__project_path):
            print('save ai file failed!')
            return False

        # 保存工程属性

        self.__set_project_property()
        return True

    def __create_property_file(self):
        """ 创建工程属性文件

        :return:
        """
        if not self.__project_property_file:
            raise ValueError('project property file is not set')

        if not os.path.exists(self.__project_property_file):
            with open(self.__project_property_file, 'w', encoding='UTF8') as fd:
                project_property = {
                    'run_type': RunTypeText.UI_AI,
                    'created_time': datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'modified_time': datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'left_tree_node_name': [],
                    'multi_resolution': True,
                    'source': {}
                }
                fd.write(json.dumps(project_property))

            g_app_context.set_info('run_type', RunTypeText.UI_AI)

    def __load_project_property(self):
        """ 加载工程属性

        :return:
        """
        project_property = {}
        if not self.__project_property_file:
            return {}
        with open(self.__project_property_file, encoding='utf8') as fd:
            content = fd.read()
            if content:
                project_property = json.loads(content)

        run_type = project_property.get('run_type', RunTypeText.UI_AI)
        g_app_context.set_info('run_type', run_type)

        return project_property

    def get_run_type(self):
        """ 获取运行类型

        :return:
        """
        project_property = self.__load_project_property()
        return project_property.get('run_type')

    def __set_project_property(self, key=None, value=''):
        """ 设置工程属性

        :param key: str or None, 默认为None，仅修改时间
        :param value:
        :return:
        """
        project_property = self.__load_project_property()
        if not project_property:
            return

        if key:
            project_property[key] = value

        if key == 'run_type':
            g_app_context.set_info('run_type', value)

        project_property['modified_time'] = datetime.now().strftime('%Y%m%d_%H%M%S')

        with open(self.__project_property_file, 'w', encoding='UTF8') as fd:
            fd.write(json.dumps(project_property))

    def set_left_tree_node_name(self, node_name: list):
        """ 设置左树下的所有节点名称

        :param node_name: []，元素仅限['AI', 'UI', 'Scene', 'AutoExplore']
        :return:
        """
        self.__set_project_property('left_tree_node_name', node_name)


    def get_left_tree_node_name(self):
        """ 左树下的所有节点名称

        :return: list
        """
        project_property = self.__load_project_property()
        node_name = project_property.get('left_tree_node_name', [])
        if not node_name:
            # 兼容之前的工程设置
            ui_file = self.get_ui_file()
            if ui_file and os.path.exists(ui_file):
                node_name.append('UI')

            task_file = self.get_task_file()
            if task_file and os.path.exists(task_file):
                node_name.append('Scene')
                node_name.append('AI')  # AI节点必须有Scene节点

            label_path = os.path.join(self.__project_path, 'data', 'samples')
            if os.path.exists(label_path):
                files = os.listdir(label_path)
                if len(files) > 0:
                    node_name.append('UIExplore')

        return node_name

    def set_run_type(self, run_type=None):
        """ 设置运行类型

        :param run_type:
        :return:
        """
        self.__set_project_property('run_type', run_type)

    def set_device_type(self, device_type):
        """ 设置设备类型

        :param device_type:
        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        if not source_info:
            source_info = {}
        source_info['device_type'] = device_type
        self.__set_project_property('source', source_info)
        # self.__set_project_property('device_type', device_type)

    def get_device_type(self, default_value=None):
        """ 获取设备类型

        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        if not source_info:
            return default_value
        return source_info.get('device_type', default_value)

    def set_device_platform(self, platform_type='Local'):
        """ 设置设备平台类型

        :param platform_type:
        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        if not source_info:
            source_info = {}
        source_info['platform'] = platform_type
        self.__set_project_property('source', source_info)

    def get_device_platform(self, default_value=None):
        """ 获取设备平台类型

        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        if not source_info:
            return default_value
        return source_info.get('platform', default_value)

    def set_canvas_fps(self, canvas_fps):
        """ 设置画布刷新频率

        :param canvas_fps:
        :return:
        """
        self.__set_project_property('canvas_fps', str(canvas_fps))

    def get_canvas_fps(self, default_value=5):
        """ 获取设备类型

        :return:
        """
        project_property = self.__load_project_property()
        return float(project_property.get('canvas_fps', default_value))

    def set_long_edge(self, long_edge):
        """ 如果是android类型，设置长边

        :param long_edge:
        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        source_info['long_edge'] = long_edge
        self.__set_project_property('source', source_info)

    def get_long_edge(self, default_value=1280):
        """ 获取长边

        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        return source_info.get('long_edge', default_value)

    def set_window_qpath(self, qpath):
        """ 设置窗口查询路径

        :param qpath:
        :attention: 当device_type为Windows时，需设置此数值
        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        source_info['window_qpath'] = qpath
        self.__set_project_property('source', source_info)
        # self.__set_project_property('window_qpath', qpath)

    def get_window_qpath(self, default_value=None):
        """ 获取窗口查询路径

        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        return source_info.get('window_qpath', default_value)

    def set_window_size(self, window_size):
        """ 设置窗口大小

        :param window_size:
        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        source_info['window_size'] = json.dumps(window_size)
        self.__set_project_property('source', source_info)

        # self.__set_project_property('window_size', json.dumps(window_size))

    def get_window_size(self, default_value=None):
        """ 获取窗口大小

        :return:
        """
        project_property = self.__load_project_property()
        source_info = project_property.get('source')
        window_size = source_info.get('window_size')
        if window_size:
            return json.loads(window_size)
        return default_value

    def set_multi_resolution(self, multi_resolution=False):
        self.__set_project_property('multi_resolution', multi_resolution)

    def get_multi_resolution(self, default_value=True):
        """ 获取多分辨率类型

        :return:
        """
        project_property = self.__load_project_property()
        return bool(project_property.get('multi_resolution', default_value))

    def get_project_property_file(self) -> str:
        return self.__project_property_file

    def get_project_path(self) -> str:
        return self.__project_path

    def get_data_path(self) -> str:
        return os.path.join(self.__project_path, DEFAULT_DATA_IMAGES_FOLDER)

    def get_ui_file(self) -> str:
        return os.path.join(self.__project_path, UI_PATH)

    def get_task_file(self) -> str:
        return os.path.join(self.__project_path, TASK_PATH)

    def get_refer_file(self) -> str:
        return os.path.join(self.__project_path, REFER_PATH)

    def _create_project_dir(self):
        os.makedirs(os.path.join(self.__project_path, UI_CONFIG_DIR), exist_ok=True)
        os.makedirs(os.path.join(self.__project_path, TASK_CONFIG_DIR), exist_ok=True)
        os.makedirs(os.path.join(self.__project_path, AI_CONFIG_DIR), exist_ok=True)
        os.makedirs(os.path.join(self.__project_path, DEFAULT_DATA_IMAGES_FOLDER), exist_ok=True)

g_project_manager = ProjectManager()
