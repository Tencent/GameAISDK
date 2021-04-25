# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import time
import platform
import traceback

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QBrush, QCursor
from PyQt5.QtWidgets import QTreeWidgetItem, QComboBox, QInputDialog, QFileDialog

from ...common.define import SDK_RUN_MODE, RunType, RunTypeText, RUN_TYPE_KEYWORD, MediaType, Mode, MULTI_RESOLUTION, \
    ITEM_TYPE_PHONE_SERIAL, DEVICE_SUCCESS_STATE, LONG_EDGE, PHONE_BG_COLOR, UI_PATH, TASK_PATH, REFER_PATH, \
    WINDOW_WIDTH_NAME, WINDOW_HEIGHT_NAME, SPY_WINDOW_NAME, WINDOW_QPATH_NAME, WINDOW_HANDLE_NAME, CANVAS_FPS_KEYWORD

from ...common.singleton import Singleton
from ...common.tool_timer import ToolTimer
from ...context.app_context import g_app_context
from ..canvas.data_source import DataSource
from ..dialog.tip_dialog import show_warning_tips, show_critical_tips
from .project_data_manager import g_project_data_mgr, MediaSourceNode
from .ai_tree.ai_tree import AITree
from .scene_tree.scene_tree import SceneTree
from .tree_manager import tree_mgr
from .ui_tree.ui_tree import UITree
from ..utils import create_tree_item, cvimg_to_qtimg, get_sub_nodes, set_log_text, is_str_valid, \
    get_item_value_by_type, str_to_bool
from ..common_widget.label_qline_edit import LabelQLineEdit
from ..canvas.ui_canvas import canvas
from ..main_window.tool_window import ui
from ...project.project_manager import g_project_manager
from ..tree.applications_tree.apps_tree import AppTree
from ...subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from ...WrappedDeviceAPI.wrappedDeviceConfig import Platform, DeviceType

IS_WINDOWS_SYSTEM = platform.platform().lower().startswith('win')
if IS_WINDOWS_SYSTEM:
    import win32process
    import win32gui
    from ...WrappedDeviceAPI.deviceAPI.pcDevice.windows.win32driver import probe, by

logger = logging.getLogger("sdktool")

ROOT_NODE_TEXT_IN_RIGHT_TREE = "project"
ROOT_NODE_TYPE_IN_RIGHT_TREE = "project_node_type"


class ProjectNode(metaclass=Singleton):
    source_changed_signal = pyqtSignal(str, str)

    def __init__(self, name=None, directory=None, data_path=None):
        super(ProjectNode, self).__init__()
        self.__name = name
        self.__directory = directory
        self.__data_path = data_path
        self.__logger = logging.getLogger('sdktool')
        self.__type_text = None
        self.__left_tree = None
        self.__right_tree = None
        self.__timer = ToolTimer()
        self.__timer.set_fps(1)
        self.__data_source = DataSource()
        self.__timer.time_signal.signal[str].connect(self.get_frame)
        self.__cur_frame = None
        self.__phone_tool_bar = None

        self._cursor_pos = None
        self._cursor_timestamp = None

        self.__media_source = None

        tree_mgr.set_object(Mode.PROJECT, self)

        self.__cursor_moved_timer = ToolTimer()
        self.__cursor_moved_timer.set_fps(1)
        self.__cursor_moved_timer.time_signal.signal[str].connect(self.handle_cursor_move)

    def finish(self):
        """程序退出时，需调用

        """
        logger.info('ProjectNode.finish')
        self.__timer.stop()
        self.__cursor_moved_timer.stop()

    def set_name(self, name=None):
        self.__name = name

    def set_directory(self, directory=None):
        self.__directory = directory

    def set_data_path(self, data_path):
        self.__data_path = data_path

    def set_phone_tool(self, phone_tool_bar):
        self.__phone_tool_bar = phone_tool_bar

    def add_to_right_tree(self):
        if self.__right_tree is None:
            self.__logger.error("input tree is None")
            return

        root = QTreeWidgetItem(self.__right_tree)
        root.setText(0, ROOT_NODE_TEXT_IN_RIGHT_TREE)
        root.setText(2, ROOT_NODE_TYPE_IN_RIGHT_TREE)

        # 工程名
        name = g_project_data_mgr.get_name()
        root.addChild(create_tree_item("name", name, edit=True))

        # 运行模式
        run_type_item = create_tree_item(key=RUN_TYPE_KEYWORD, node_type=RUN_TYPE_KEYWORD, edit=False)
        combobox = QComboBox()

        combobox.addItems(SDK_RUN_MODE)
        combobox.currentTextChanged.connect(self._value_changed)
        root.addChild(run_type_item)

        run_type = g_project_manager.get_run_type()
        if run_type == RunTypeText.AI:
            g_project_data_mgr.set_run_type(RunType.AI)
        elif run_type == RunTypeText.UI_AI:
            g_project_data_mgr.set_run_type(RunType.UI_AI)
        elif run_type == RunTypeText.AUTO_EXPLORER:
            g_project_data_mgr.set_run_type(RunType.AUTO_EXPLORER)
        else:
            show_warning_tips('error run type:%s' % run_type)
        if run_type:
            combobox.setCurrentText(run_type)
        self.__right_tree.setItemWidget(run_type_item, 1, combobox)

        # 多分辨率
        multi_resolution_item = create_tree_item(key=MULTI_RESOLUTION, node_type=MULTI_RESOLUTION, edit=False)
        resolution_box = QComboBox()
        resolution_box.addItems([
            'False',
            'True'
        ])
        multi_resolution = g_project_manager.get_multi_resolution()
        resolution_box.setCurrentText(str(multi_resolution))

        resolution_box.currentTextChanged.connect(self._change_solution_type)
        root.addChild(multi_resolution_item)
        self.__right_tree.setItemWidget(multi_resolution_item, 1, resolution_box)

        # 刷新频率
        canvas_fps_item = create_tree_item(key=CANVAS_FPS_KEYWORD, node_type=CANVAS_FPS_KEYWORD, edit=False)
        cbx_canvas_fps = QComboBox()

        cbx_canvas_fps.addItems(['1', '5', '10'])
        cbx_canvas_fps.currentTextChanged.connect(self._canvas_fps_value_changed)
        root.addChild(canvas_fps_item)

        canvas_fps = g_project_manager.get_canvas_fps()
        if canvas_fps:
            value = int(canvas_fps)
            if value <= 0:
                value = 1
            cbx_canvas_fps.setCurrentText(str(value))
        self.__right_tree.setItemWidget(canvas_fps_item, 1, cbx_canvas_fps)

        # 图像来源
        self.add_data_source_node(root, self.__right_tree)

        root.setExpanded(True)

    def _canvas_fps_value_changed(self, text):
        fps_value = int(text)
        g_project_manager.set_canvas_fps(fps_value)
        self.__timer.set_fps(fps_value)

    def add_to_left_tree(self, project_name):
        if self.__left_tree is None:
            logger.info("input tree is None")
            return
        self.__left_tree.clear()
        self.__name = project_name
        tree_mgr.set_mode(None)
        root = QTreeWidgetItem(self.__left_tree)
        root.setText(0, self.__name)

        return root

    def add_data_source_node(self, root, tree, value_dict=None):
        if value_dict is None:
            value_dict = dict()
        if self.__media_source is None:
            self.__media_source = MediaSourceNode()
            g_project_data_mgr.set_media_source(self.__media_source)

        source_node = create_tree_item("source")
        root.addChild(source_node)
        # node.setText(0, "sample image source")
        data_type = create_tree_item("media type:", "", edit=True)
        source_node.addChild(data_type)
        combobox = QComboBox()
        cbx_items = ["", MediaType.ANDROID]
        if IS_WINDOWS_SYSTEM:
            cbx_items.append(MediaType.WINDOWS)
        combobox.addItems(cbx_items)

        device_type = g_project_manager.get_device_type(DeviceType.Android.value)
        if device_type:
            if device_type == MediaType.WINDOWS and not IS_WINDOWS_SYSTEM:
                show_critical_tips('当前系统不支持Windows系统窗口类型，请选用其他类型')
                device_type = ""
            else:
                combobox.setCurrentText(device_type)

        logger.debug("add_data_source media source type %s", device_type)
        # if device_type == MediaType.VIDEO:
        #     raise ValueError('video not support')
        if device_type == MediaType.ANDROID:
            combobox.setCurrentText(MediaType.ANDROID)
            self._load_phone_item(source_node)
            self.__media_source.type = MediaType.ANDROID

        elif device_type == MediaType.WINDOWS:
            combobox.setCurrentText(MediaType.WINDOWS)
            self._load_windows_item(source_node)
            self.__media_source.type = MediaType.WINDOWS

        else:
            combobox.setCurrentIndex(-1)

        tree.setItemWidget(data_type, 1, combobox)
        data_type.setExpanded(True)

        def combobox_text_change():
            if g_app_context.get_info('phone', False):
                if not self.__timer.is_stopped():
                    self.__timer.stop()
                self.__data_source.finish()

            text = combobox.currentText()
            cur_item = self.__right_tree.currentItem()

            # 删除同级节点中除当前节点外的其他所有节点
            sub_nodes = get_sub_nodes(source_node)
            for sub_node in sub_nodes:
                if sub_node != cur_item:
                    self.__logger.debug("remove child %s", sub_node.text(0))
                    source_node.removeChild(sub_node)

            self._create_data_source_item(node=source_node, text=text)

        combobox.currentTextChanged.connect(combobox_text_change)

        source_node.setExpanded(True)

    def new_project(self, left_tree, right_tree):
        if self.__left_tree is None:
            self.__left_tree = left_tree
        if self.__right_tree is None:
            self.__right_tree = right_tree

        # 判断工程是否存在，存在的话，不允许重建
        name = g_project_data_mgr.get_name()
        if name is not None:
            show_warning_tips('已加载工程，请重打开工具后再新建项目')
            return

        text, ok = QInputDialog.getText(None, '输入工程名称', '工程名称: ')
        if ok and text:
            self._new_project(text)
            tree_mgr.set_mode(Mode.PROJECT)

    def load_project(self, left_tree, right_tree):
        if self.__left_tree is None:
            self.__left_tree = left_tree

        if self.__right_tree is None:
            self.__right_tree = right_tree
        else:
            # 清除右树
            logger.debug("clear right tree")
            self.__right_tree.clear()

        if bsa.has_service_running():
            show_warning_tips("请在调试或执行停止后，再加载工程")
            return

        prj_dir = os.getcwd()
        sdk_tool_path = os.environ.get('AI_SDK_TOOL_PATH')
        if sdk_tool_path and os.path.exists(sdk_tool_path):
            prj_dir = os.path.join(sdk_tool_path, 'project')

        file_path, _ = QFileDialog.getOpenFileName(None, "选择工程文件", prj_dir, "prj(*.prj *.aisdk)")

        # 如果未选择，则直接退出
        if len(file_path) == 0:
            logger.info("give up select project file")
            return
        self._load_project(file_path)

    def _load_project_node(self):
        self.__right_tree.clear()
        logger.debug("load project node")
        self.add_to_right_tree()

    def load_project_node(self):
        if not self.save_previous_rtree():
            logger.error("save previous tree failed")
            return False
        self._load_project_node()
        return True

    @staticmethod
    def _get_hwnd_by_qpath(query_path):
        hwnds = probe.Win32Probe().search_element(by.QPath(query_path))
        cnt = len(hwnds)
        if cnt == 1:
            return hwnds[0]
        if cnt > 1:
            show_warning_tips('found multi windows by qpath(%s)' % query_path)
        else:
            show_warning_tips('failed to find window by qpath(%s)' % query_path)
        return None

    def update_right_tree(self):
        item = self.__right_tree.currentItem()
        item_type = item.text(2)
        item_text = item.text(1)
        if item_type == ITEM_TYPE_PHONE_SERIAL:
            self.select_phone()
        elif item_type == SPY_WINDOW_NAME:
            self.spy_window()
        elif item_type == WINDOW_QPATH_NAME:
            query_path = item_text
            hwnd = self._get_hwnd_by_qpath(query_path)
            if hwnd:
                self._update_window_item_prop(hwnd, update_qpath=False)
                self.select_window(hwnd)
        elif item_type == WINDOW_HANDLE_NAME:
            if item_text and item_text.isdigit() and int(item_text) > 0:
                hwnd = int(item_text)
                self._update_window_item_prop(hwnd)
                self.select_window(hwnd)

    def select_window(self, serial):
        set_log_text(" select window handle {}".format(serial))
        # 先断开之前的链接
        self.__data_source.finish()
        self._init_window(serial)

        ui.set_ui_canvas(canvas)
        # 重置画布状态为空
        canvas.reset_state()
        canvas.mode = None

        g_app_context.set_info("phone", True)
        canvas.update_dev_toolbar()

        if self.__timer.is_stopped():
            # 开始收帧
            self.__timer.start()

    def select_phone(self):
        # 判断选择的是否为手机
        item = self.__right_tree.currentItem()

        # 判断当前的手机状态
        serial = item.text(0)
        device_state = item.text(1)
        if device_state != DEVICE_SUCCESS_STATE:
            show_warning_tips("device state is not ready")
            return
        set_log_text(" select phone {}".format(serial))

        # 先断开之前的链接
        self.__data_source.finish()
        self._init_phone(item, serial)

        ui.set_ui_canvas(canvas)
        # 重置画布状态为空
        canvas.reset_state()
        canvas.mode = None

        g_app_context.set_info("phone", True)
        canvas.update_dev_toolbar()

        if self.__timer.is_stopped():
            # 开始收帧
            self.__timer.start()

    def save_previous_rtree(self):
        # 保存之前的右树
        pre_mode = tree_mgr.get_mode()
        logger.debug("pre mode is %s", pre_mode)
        if pre_mode is not None and pre_mode != Mode.PROJECT:
            pre_tree = tree_mgr.get_object(pre_mode)
            return pre_tree.save_previous_rtree()

        # 保存当前设置
        self.save_project()
        return True

    def line_text_change(self, before, after):
        self.source_changed_signal.emit(before, after)
        self.__media_source.url = after

    def handle_path_text_change(self, before, after):
        self.source_changed_signal.emit(before, after)
        self.__media_source.handle_path = after

    def _change_solution_type(self, text):
        node = self.__right_tree.currentItem()
        node.setText(1, text)
        g_project_manager.set_multi_resolution(str_to_bool(text))

    def _value_changed(self, text):
        node = self.__right_tree.currentItem()
        if not node:
            return

        node.setText(1, text)
        node_name = node.text(0)
        if node_name == RUN_TYPE_KEYWORD:
            if text == RunTypeText.AI:
                g_project_data_mgr.set_run_type(RunType.AI)
            elif text == RunTypeText.UI_AI:
                g_project_data_mgr.set_run_type(RunType.UI_AI)
            elif text == RunTypeText.AUTO_EXPLORER:
                g_project_data_mgr.set_run_type(RunType.AUTO_EXPLORER)
            else:
                raise ValueError('error run type(%s)' % text)
            g_project_manager.set_run_type(text)
        elif node_name == LONG_EDGE:
            if text.strip().isdigit():
                long_edge = int(text)
                g_project_manager.set_long_edge(long_edge)
                g_app_context.set_info("phone_long_edge", str(long_edge))
                self.__media_source.long_edge = long_edge

    def _create_video_item(self, node, video_url):
        # link_item = create_tree_item("link", value=value_dict.get("link"), edit=True)
        link_item = create_tree_item("link", value=video_url, edit=True)
        link_edit = LabelQLineEdit()
        link_edit.setPlaceholderText("....")
        node.addChild(link_item)
        self.__right_tree.setItemWidget(link_item, 1, link_edit)
        link_edit.textModified.connect(self.line_text_change)

    @staticmethod
    def _generate_qpath(hwnd):
        from ...WrappedDeviceAPI.deviceAPI.pcDevice.windows.win32driver.probe import Win32Probe
        sep_list = ['/', '|', '!', '$']

        win32_probe = Win32Probe()
        values = [win32_probe.get_property(hwnd, 'text'), win32_probe.get_property(hwnd, 'CLASSNAME')]
        props = []
        top_level_window_hwnd = win32_probe.get_property(hwnd, 'TOPLEVELWINDOW')
        if top_level_window_hwnd != hwnd:
            p_text = win32_probe.get_property(top_level_window_hwnd, 'text')
            p_cls_name = win32_probe.get_property(top_level_window_hwnd, 'CLASSNAME')
            values.extend([p_cls_name, p_text])
            props.append('text="%s" && type="%s"' % (p_text, p_cls_name))
        props.append('text="%s" && type="%s"' % (values[0], values[1]))

        sep = None
        for i in sep_list:
            found = False
            for v in values:
                if i in v:
                    found = True
                    break
            if not found:
                sep = i
                break

        if sep is None:
            logger.error('qpath sep is not found')
            return ''

        qpath = '%s%s' % (sep, sep.join(props))

        return qpath

    def _update_window_item_prop(self, hwnd, update_qpath=True):
        rc = win32gui.GetWindowRect(hwnd)
        l, t, r, b = rc
        w = r - l
        h = b - t
        g_app_context.set_info('window_hwnd', hwnd)
        self._set_window_item_value(WINDOW_HANDLE_NAME, str(hwnd))
        if update_qpath:
            self._set_window_item_value(WINDOW_QPATH_NAME, self._generate_qpath(hwnd))
        self._set_window_item_value(WINDOW_WIDTH_NAME, str(w))
        self._set_window_item_value(WINDOW_HEIGHT_NAME, str(h))

    def handle_cursor_move(self):
        ct = time.time()
        pos = QCursor.pos()
        if pos == self._cursor_pos:
            if ct - self._cursor_timestamp > 3:
                x, y = pos.x(), pos.y()
                hwnd = win32gui.WindowFromPoint((x, y))
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid != os.getpid():
                    self.__cursor_moved_timer.stop()
                    self._update_window_item_prop(hwnd)
                    self.select_window(hwnd)
        else:
            self._cursor_pos = pos
            self._cursor_timestamp = ct

    def spy_window(self):
        g_app_context.set_info('window_hwnd', 0)
        self._cursor_pos = QCursor.pos()
        self._cursor_timestamp = time.time()
        self.__cursor_moved_timer.start()

    @staticmethod
    def _load_windows_item(node):
        logger.info('load window items')

        tips = "提示: 双击'Spy Window', 鼠标移动到目标窗口上，悬停3秒"
        spy_window_item = create_tree_item(SPY_WINDOW_NAME,
                                           node_type=SPY_WINDOW_NAME,
                                           value=tips,
                                           edit=False)
        node.addChild(spy_window_item)

        window_hwnd = g_app_context.get_info('window_hwnd', '')
        window_handle_item = create_tree_item(WINDOW_HANDLE_NAME,
                                              value=str(window_hwnd),
                                              node_type=WINDOW_HANDLE_NAME,
                                              edit=True)
        node.addChild(window_handle_item)

        qpath = g_project_manager.get_window_qpath('')
        window_qpath_item = create_tree_item(WINDOW_QPATH_NAME,
                                             value=qpath,
                                             node_type=WINDOW_QPATH_NAME,
                                             edit=True)
        node.addChild(window_qpath_item)

        window_size = g_project_manager.get_window_size()
        w, h = '0', '0'
        if window_size:
            w, h = str(window_size[0]), str(window_size[1])
        window_width_item = create_tree_item(key=WINDOW_WIDTH_NAME,
                                             value=w,
                                             node_type=WINDOW_WIDTH_NAME,
                                             edit=True)
        node.addChild(window_width_item)
        window_height_item = create_tree_item(key=WINDOW_HEIGHT_NAME,
                                              value=h,
                                              node_type=WINDOW_HEIGHT_NAME,
                                              edit=True)
        node.addChild(window_height_item)

    def _set_window_item_value(self, item_type, item_value):
        """ 为指定类型的item设置数值

        :param item_type:
        :param item_value:
        :return:
        """
        self.__right_tree.currentItem()
        cur_item = self.__right_tree.currentItem()
        sub_nodes = get_sub_nodes(cur_item.parent())
        for sub_node in sub_nodes:
            if sub_node.text(2) == item_type:
                sub_node.setText(1, item_value)

    def _load_phone_item(self, node):
        # 长边的设置
        long_edge = g_project_manager.get_long_edge()
        long_edge_item = create_tree_item(key=LONG_EDGE, value=str(long_edge), node_type=LONG_EDGE, edit=True)
        node.addChild(long_edge_item)

        phone_item = create_tree_item("Serial No.", value="ADB Status", edit=False)
        node.addChild(phone_item)

        phone_infos = self._get_phone_list()
        for phone_info in phone_infos:
            serial_no = phone_info.get('serial')
            state = phone_info.get("state")

            phone_info = create_tree_item(key=serial_no, value=state, node_type=ITEM_TYPE_PHONE_SERIAL, edit=False)
            node.addChild(phone_info)

            # 设置之前选中手机的背景色
            if serial_no == self.__media_source.select_phone_serial:
                bg_color = QBrush(PHONE_BG_COLOR)
                phone_info.setBackground(0, bg_color)
                phone_info.setBackground(1, bg_color)

    @staticmethod
    def _get_phone_list():
        # 获取设备信息列表
        result = os.popen("adb devices")
        res = result.read()
        lines = res.splitlines()
        infos = []
        for index, line in enumerate(lines):
            # 0:line: adb devices
            if index == 0:
                continue

            # 0:serial, 1:state
            sub_line = line.split('\t')
            size = len(sub_line)
            if size < 2:
                continue
            info = {"serial": sub_line[0], "state": sub_line[1]}
            infos.append(info)
        return infos

    def _create_data_source_item(self, node, text):
        if text == MediaType.ANDROID:
            self.__media_source.type = MediaType.ANDROID
            self._load_phone_item(node)

        elif text == MediaType.WINDOWS:
            self.__media_source.type = MediaType.WINDOWS
            self._load_windows_item(node)

        logger.debug("**************media source type %s**************", self.__media_source.type)

    def _new_project(self, name):
        if not self.save_previous_rtree():
            return False

        self.__right_tree.clear()

        old_name = g_project_data_mgr.get_name()
        if old_name == name:
            show_warning_tips("project %s have already exist" % name)
            return False

        # 检查命名是否合法(数字或是英文字符)
        if not is_str_valid(name):
            show_warning_tips('%s is not valid(char or num)' % name)
            return False

        # 清空之前的项目设置
        g_project_manager.clear()
        g_project_data_mgr.clear()

        # self.__name = name

        project_file_path = g_project_manager.create(name)
        if not project_file_path:
            show_warning_tips("project {} have already exist".format(name))

            return False

        logger.debug("project file path: %s", project_file_path)
        g_project_data_mgr.set_project_file_path(project_file_path)

        # g_project_data_mgr.set_name(name)
        self.add_to_left_tree(name)
        self.add_to_right_tree()
        canvas.reset_state()
        return True

    def _load_project(self, project_file_path):
        # 加载工程名
        logger.debug("project file path is %s", project_file_path)

        g_project_data_mgr.set_project_file_path(project_file_path)
        rename_file, new_project_file_path = g_project_data_mgr.adjust_project_file_path()
        if rename_file:
            project_file_path = new_project_file_path

        if not g_project_manager.load(project_file_path):
            logger.error("load project %s failed", project_file_path)
            return

        # 创建工程节点树
        project_name = g_project_data_mgr.get_name()
        project_node = self.add_to_left_tree(project_name)

        # 清空画布
        canvas.reset_state()

        # 加载左树配置
        node_name = g_project_manager.get_left_tree_node_name()
        if not node_name:
            return

        project_dir = os.path.dirname(project_file_path)

        # 加载工程类型
        if 'UIExplore' in node_name:
            run_type = g_project_manager.get_run_type()
            if run_type == RunTypeText.AUTO_EXPLORER:
                AppTree().new_ui_explore_node()
            else:
                show_warning_tips('"run type"数值(%s)错误, 应为AutoExplore，请正确修改后保存再打开工程' % run_type)

        # 加载配置
        if 'UI' in node_name:
            ui_config = os.path.join(project_dir, UI_PATH)
            if os.path.exists(ui_config):
                ui_tree = UITree()
                ui_tree.init(self.__left_tree, self.__right_tree)
                ui_tree.load_ui(ui_config)

        if 'Scene' in node_name:
            task_config = os.path.join(project_dir, TASK_PATH)
            if os.path.exists(task_config):
                refer_config = os.path.join(project_dir, REFER_PATH)
                if not os.path.exists(refer_config):
                    refer_config = None

                scene_tree = SceneTree()
                scene_tree.init(self.__left_tree, self.__right_tree)
                scene_tree.load_scene(task_config, refer_config)
            else:
                logger.debug("%s not exist ", TASK_PATH)

        if 'AI' in node_name:
            ai_tree = AITree()
            ai_tree.load_ai(project_dir)

        # 默认展示工程节点的右树内容
        self._load_project_node()
        self.__left_tree.setCurrentItem(project_node)
        tree_mgr.set_mode(Mode.PROJECT)

    def _save_node_tree_info(self, node_name):
        if 'UIExplore' in node_name:
            AppTree().save_labels()

        if 'UI' in node_name:
            ui_tree = UITree()
            ui_tree.save_ui()

        if 'Scene' in node_name:
            scene_tree = SceneTree()
            scene_tree.save_scene()

        if 'AI' in node_name:
            ai_tree = AITree()
            ai_tree.save_ai()

    def save_project(self):
        try:
            # 保存当前加载的节点
            node_name = []
            if self.__left_tree:
                project_node = self.__left_tree.topLevelItem(0)
                sub_nodes = get_sub_nodes(project_node)

                for node in sub_nodes:
                    node_name.append(node.text(0))

            if not node_name:
                return

            g_project_manager.set_left_tree_node_name(node_name)

            # 保存当前设备类型以及相关的信息
            device_type = DeviceType.Android.value
            device_platform = Platform.Local.value

            if self.__media_source.type == MediaType.WINDOWS:
                device_type = DeviceType.Windows.value

                right_tree_root_item = self.__right_tree.topLevelItem(0)
                qpath = get_item_value_by_type(WINDOW_QPATH_NAME, right_tree_root_item)
                if qpath:
                    g_project_manager.set_window_qpath(qpath)
                width = get_item_value_by_type(WINDOW_WIDTH_NAME, right_tree_root_item)
                if width and width.isdigit():
                    width = int(width)
                height = get_item_value_by_type(WINDOW_HEIGHT_NAME, right_tree_root_item)
                if height and height.isdigit():
                    height = int(height)
                if width and height:
                    g_project_manager.set_window_size([width, height])
            elif self.__media_source.type == MediaType.ANDROID:
                device_platform = Platform.WeTest.value
                right_tree_root_item = self.__right_tree.topLevelItem(0)
                long_edge = get_item_value_by_type(LONG_EDGE, right_tree_root_item)
                if long_edge and long_edge.isdigit():
                    g_project_manager.set_long_edge(int(long_edge))

            g_project_manager.set_device_type(device_type)
            g_project_manager.set_device_platform(device_platform)

            self._save_node_tree_info(node_name)

            success = g_project_manager.save()
            if success:
                folder = g_project_manager.get_project_path()
                cwd = os.getcwd()
                set_log_text("save config '{}/{}' success".format(cwd, folder))
            else:
                set_log_text("save failed")

        except RuntimeError as err:
            exp = traceback.format_exc()
            logger.error('save project error:%s', exp)
            show_critical_tips("{}".format(err))

    def get_frame(self):
        # 当加载某一项时， 源为图像，手机状态为释放状态
        phone_state = g_app_context.get_info("phone") or False
        if self.__phone_tool_bar is not None:
            self.__phone_tool_bar.setChecked(phone_state)

        # 手机不在运行状态
        if not phone_state:
            return

        # 在绘图中，不更新
        if canvas.drawing() and canvas.get_pixmap() is not None:
            return

        # 否则从手机源中更新画布，收帧失败结束收帧
        if self.__data_source is not None:
            frame = self.__data_source.get_frame()
            if frame is not None:
                pixmap = cvimg_to_qtimg(frame)
                canvas.load_pixmap(pixmap)
                self.__cur_frame = pixmap
        else:
            logger.debug("data source is None")

    def _init_phone(self, node, serial):
        set_log_text("begin connect phone {}".format(serial))
        self.__media_source.select_phone_serial = serial
        # is_portrait = False
        parent = node.parent()
        for index in range(parent.childCount()):
            child = parent.child(index)
            # if child.text(0) == 'portrait':
            #     is_portrait = child.text(1)
            #     is_portrait = bool(is_portrait)
            #     self.__media_source.is_portrait = is_portrait
            if child.text(0) == LONG_EDGE:
                self.__media_source.long_edge = int(child.text(1))

        ret = self.__data_source.init_phone(serial=serial,
                                            device_type=DeviceType.Android.value,
                                            platform=Platform.Local.value,
                                            long_edge=self.__media_source.long_edge)
        if ret:
            set_log_text("connect phone{} success: ret {}".format(serial, ret))

            # 设置设备id到全局变量中
            g_app_context.set_info("phone_serial", serial)
            g_app_context.set_info("phone_long_edge", str(self.__media_source.long_edge))

            img = None
            for _ in range(50):
                img = self.__data_source.get_frame()
                if img is not None:
                    h, w = img.shape[:2]
                    if h > w:
                        g_app_context.set_info("phone_short_edge", str(w))
                    else:
                        g_app_context.set_info("phone_short_edge", str(h))
                    break
                time.sleep(0.2)
            if img is None:
                show_critical_tips('failed to get image')

    def _init_window(self, serial=None):
        self.__media_source.select_phone_serial = serial
        # self.__media_source.is_portrait = None
        self.__media_source.long_edge = None

        ret = self.__data_source.init_phone(serial=serial,
                                            device_type=DeviceType.Windows.value,
                                            platform=Platform.Local.value)
        if ret:
            set_log_text("init window({}) success: ret {}".format(serial, ret))

            # 设置设备id到全局变量中
            g_app_context.set_info("phone_serial", str(serial))

            img = None
            for _ in range(50):
                img = self.__data_source.get_frame()
                if img is not None:
                    break
                time.sleep(0.2)
            if img is None:
                show_critical_tips('failed to get image')
