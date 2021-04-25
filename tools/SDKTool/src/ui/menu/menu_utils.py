# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import time
import zipfile

from PyQt5 import QtWidgets

from ..dialog.tip_dialog import show_message_tips
from ...common.define import DEFAULT_MENU_WIDTH


class MenuPackLog(object):
    def __init__(self, menu_bar):
        self.path = os.environ['AI_SDK_TOOL_PATH']
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("Utils")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())

        self.action_train = QtWidgets.QAction()
        self.action_train.setText("PackLog")

    def define_action(self):
        self.__menu.addAction(self.action_train)

    def set_slot(self, left_root=None, right_root=None):
        self.action_train.triggered.connect(self.__packfile)

    def set_sub_menu(self):
        pass

    def __packfile(self):
        '''
        打包日志
        '''
        # 拼接所有log路径
        sdk_log_path = self.path + '/log'
        root_log_path = self.path + '/../../log'
        refineDet_path = self.path + '/../../Modules/RefineDet/log'
        dict_log = [sdk_log_path, root_log_path, refineDet_path]
        # 时间戳命名
        times = int(time.time())
        save_name = '{}'.format(os.path.dirname(self.path) + '/{}.zip'.format(times))

        try:
            # 遍历log日志下的所有文件
            for paths in dict_log:
                if os.path.exists(paths):
                    self._make_zip(paths, save_name)
            # tips
            show_message_tips('文件打包成功,保存路径为:\n{}'.format(save_name))
        except Exception as er:
            show_message_tips('文件打包失败：', er)

    def _make_zip(self, source_dir, save_name):
        '''
        pack_log
        '''
        zipFile = zipfile.ZipFile(save_name, 'a')
        for parent, dirnames, filenames in os.walk(source_dir):
            for filename in filenames:
                pathfile = os.path.join(parent, filename)
                zipFile.write(pathfile, '{}'.format(filename), zipfile.ZIP_DEFLATED)
        zipFile.close()
