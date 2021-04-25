# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import os
import logging
import traceback
import time
import cv2

from PyQt5.Qt import QIcon
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPixmap, QCursor, QImage
from PyQt5.QtWidgets import QTreeWidgetItem, QAction, QMenu

from .auto_label_image import AutoLabelImage
from .define import TRAIN_PARAMS, ITEM_TYPE_IMAGE, CHILD_ITEM_KEYS, TOP_LEVEL_TREE_KEYS, PATH_NAME_LIST, RUN_PARAMS, \
    UI_AUTO_EXPLORE_RUN_FILTER_KEYS, QICON_IMGS
from .explore_result import ExploreResult
from .train_sample import CNNTrainSample
from ....main_window.tool_window import ui
from ....tree.tree_manager import tree_mgr
from .....project.project_manager import g_project_manager
from .....context.app_context import g_app_context
from ....canvas.ui_canvas import canvas
from ....canvas.shape import Shape
from ....utils import get_sub_nodes, create_tree_item, create_bool_tree_item, get_tree_top_nodes, \
    get_file_list, get_image_list
from .usr_label_image import UsrLabelImage

from .....config_manager.ui_auto_explore.ui_explore_api import explore_train_get_params, auto_get_label_path, \
    user_get_label_path, auto_save_label_path, ui_explore_config_get, explore_result_get_path, \
    explore_result_save_path, explore_run_get_params, explore_run_save_params, explore_train_get_data_path, \
    explore_train_save_params
from .....common.define import Mode, BIN_PATH, IO_PROCESS_NAME, AI_PROCESS_NAME, GAMEREG_PROCESS_NAME, \
    MC_PROCESS_UI_AI_MODE_NAME, PHONE_CLIENT_PROCESS_NAME, UI_PROCESS_NAME, RunTypeText, MC_PROCESS_AI_MODE_NAME, \
    PHONE_CLIENT_PATH, AI_CONFIG_ALGORITHM_PATH
from ....utils import set_log_text
from ....canvas.data_source import g_data_source
from .....subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from .....common.utils import rm_dir_files
from .....common.tool_timer import ToolTimer
from .utils import filter_params
from ....dialog.tip_dialog import show_warning_tips

logger = logging.getLogger("sdktool")


class UIExploreNode(object):
    SERVICE_NAME = 'ui_auto_explore'

    def __init__(self):
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.root = None
        self.__last_clicked_node = None

        self.usr_label_image = UsrLabelImage(usr_label_path=None, canvas=canvas, ui=ui)
        # train_sample_path = explore_train_get_data_path()
        self.__trainSample = CNNTrainSample(None)
        result_path = explore_result_get_path()
        self.__explore_result = ExploreResult(result_path)
        self.__actionAddImg = QAction()
        self.__actionChgImg = QAction()
        self.__actionDelImg = QAction()
        self.__actionDelDir = QAction()
        self.__addSampleFolder = QAction()
        self._run_timer = ToolTimer()
        self._run_timer.set_fps(1)
        self._run_timer.time_signal.signal[str].connect(self.__run_progress_display)
        self._action_dir = None
        self._max_click_number = 0
        self.backend_process_running = True
        self.init_action()

    def init_action(self):
        self.__actionAddImg.setText("增加图片")
        self.__actionAddImg.triggered.connect(self.on_action_add_usr_image)

        self.__actionChgImg.setText("替换图片")
        self.__actionChgImg.triggered.connect(self.on_action_chg_usr_image)

        self.__actionDelImg.setText("删除图片")
        self.__actionDelImg.triggered.connect(self.on_action_del_usr_image)

        self.__actionDelDir.setText("删除目录")
        self.__actionDelDir.triggered.connect(self.on_action_del_usr_dir)

        self.__addSampleFolder.setText("增加目录")
        self.__addSampleFolder.triggered.connect(self.on_action_add_folder)

    def reset_state(self):
        self.__explore_result.reset()
        canvas.reset_state()
        canvas.add_ui_graph(None)

    def clear_config(self):
        pass

    def clear_right_tree_signal(self):
        pass

    @staticmethod
    def _save_previous_rtree():
        """ 保存右树

        """
        pre_mode = tree_mgr.get_mode()
        logger.debug("pre mode is %s", pre_mode)
        if pre_mode is not None and pre_mode != Mode.UI_AUTO_EXPLORE:
            pre_tree = tree_mgr.get_object(pre_mode)
            return pre_tree.save_previous_rtree()

    def _save_last_label(self, primary_node):
        # 保存标签文件
        node_type = primary_node.text(2)
        text0 = primary_node.text(0)
        if node_type == ITEM_TYPE_IMAGE:
            if self.__last_clicked_node:
                last_clicked_node_file_name = self.__last_clicked_node.text(0)
                last_clicked_node_type = self.__last_clicked_node.text(2)
                if last_clicked_node_file_name != text0 and last_clicked_node_type == ITEM_TYPE_IMAGE:
                    pre_tree = tree_mgr.get_object(Mode.UI_AUTO_EXPLORE)
                    pre_tree.save_previous_rtree()
        self.__last_clicked_node = primary_node

    def update_right_tree(self, primary_node):
        g_app_context.set_info('enable_device_operation', False)
        g_app_context.set_info("phone", False)

        self._save_previous_rtree()
        self._save_last_label(primary_node)

        self.__right_tree.clear()
        text0 = primary_node.text(0)
        text1 = primary_node.text(1)

        # 如果没有父节点，则不做操作，只对子节点进行操作
        parent_node = primary_node.parent()
        if parent_node is None:
            return

        key = primary_node.text(0)
        # 双击'开始自动标记'
        if key in CHILD_ITEM_KEYS[1][0]:
            auto_label = AutoLabelImage(ui.get_canvas())
            path = auto_get_label_path()
            # auto_label.set_path(TEST_PATH)
            auto_label.set_path(path)
            auto_label.label()

        logger.debug("update right tree, text0 %s, text1 %s", text0, text1)
        # 双击 "路径"
        if text0 in PATH_NAME_LIST:
            # 0: "路径"， 1:路径值 2:对应的左树节点，比如"Step1: 样本自动标记"下的路径，则在第三列中存储的未“Step1: 样本自动标记”
            self.on_click_path_item(primary_node, parent_node)

        # 实时生成样本
        if text0 == CHILD_ITEM_KEYS[0][1]:
            g_app_context.set_info("phone", True)
            self.generate_real_samples(text1)

        # 图像类型
        node_type = primary_node.text(2)
        if node_type == ITEM_TYPE_IMAGE:
            self.on_click_image_item()

        # 样本修改
        if text0 == CHILD_ITEM_KEYS[2][0]:
            self.on_modify_sample()

        # 打包样本
        if text0 == CHILD_ITEM_KEYS[2][1]:
            self.on_package_sample()

        # 双击训练参数设置
        if text0 == CHILD_ITEM_KEYS[3][0]:
            self.on_click_param_item()

        # 双击开始训练
        if text0 == CHILD_ITEM_KEYS[3][1]:
            self.on_train()

        # 双击停止训练
        if text0 == CHILD_ITEM_KEYS[3][2]:
            self.on_stop_train()

        # 结果分析
        if text0 == CHILD_ITEM_KEYS[3][3]:
            self.on_analyze_train()

        # 双击运行参数设置
        if text0 == CHILD_ITEM_KEYS[4][0]:
            self.on_click_run_param_item()

        # 双击开始执行
        if text0 == CHILD_ITEM_KEYS[4][1]:
            self.on_run()

        # 双击停止运行
        if text0 == CHILD_ITEM_KEYS[4][2]:
            self.on_stop()


        # 图分析
        if text0 == CHILD_ITEM_KEYS[5][0]:
            self.on_ui_graph()

        # 覆盖率分析
        if text0 == CHILD_ITEM_KEYS[5][1]:
            self.on_coverage()

        # UI详细覆盖分析
        if text0 == CHILD_ITEM_KEYS[5][2]:
            self.on_ui_coverage()

    def set_image_list(self):
        path = user_get_label_path()
        label_image_list = get_image_list(path)
        self.usr_label_image.set_image_list(label_image_list)

    def on_click_image_item(self):
        item = self.__left_tree.currentItem()
        img_path = item.text(3)
        logger.debug("imgPath is %s", img_path)

        label_image_list = self.usr_label_image.image_list
        if img_path in label_image_list:
            label_image_index = label_image_list.index(img_path)
            self.usr_label_image.set_image_index(label_image_index)

        try:
            canvas.mouse_move_flag = False
            # phone_state = AppContext().get_info('phone')
            canvas.reset_state()
            self.load_label_image(img_path)

        except RuntimeError as error:
            logger.error("find image %s failed error %s", img_path, error)

    def load_label_image(self, image_file):
        # 判断图像文件是否存在
        if not os.path.exists(image_file):
            raise Exception("image {} is not exist".format(image_file))

        # 加载图像文件
        frame = QImage(image_file)
        # self.image = frame
        pix = QPixmap.fromImage(frame)
        canvas.load_pixmap(pix)
        canvas.update()
        canvas.setEnabled(True)

        # 在右树显示标签信息
        self.__right_tree.clear()
        item = QTreeWidgetItem(self.__right_tree)
        item.setText(0, 'fileName')
        item.setText(1, os.path.basename(image_file))
        item.setText(2, image_file)

        scene_item = QTreeWidgetItem(self.__right_tree)
        scene_item.setText(0, 'scene')

        labels_item = QTreeWidgetItem(self.__right_tree)
        labels_item.setText(0, 'labels')
        labels_item.setExpanded(True)

        self.load_label_json(image_file, scene_item, labels_item)
        canvas.update()

    @staticmethod
    def load_label_json(label_image_name, scene_item, labels_item):
        # 清除画布的一些数据
        canvas.item_shape.clear()

        # 读取json文件
        label_json_path = label_image_name[:label_image_name.rfind('.')] + ".json"
        if os.path.exists(label_json_path) is False:
            canvas.set_editing()
            return

        try:
            with open(label_json_path, 'r') as f:
                label_json_dict = json.load(f)
        except IOError as e:
            raise e

        scene_name = label_json_dict["scene"]
        # self.__ui.treeWidget.topLevelItem(1).setText(1, sceneName)
        scene_item.setText(1, scene_name)

        # 对每个label，读取其内容并展示在画布上
        shapes = []
        for labelShape in label_json_dict["labels"]:
            label_text = labelShape["label"]
            # labelName = labelShape["name"]

            label_w = int(labelShape['w'])
            label_h = int(labelShape['h'])
            if label_w == 0 or label_h == 0:
                continue

            tree_label_item = create_tree_item(key=label_text)
            labels_item.addChild(tree_label_item)

            node_x = create_tree_item(key='x', value=labelShape['x'])
            node_y = create_tree_item(key='y', value=labelShape['y'])
            node_w = create_tree_item(key='w', value=labelShape['w'])
            node_h = create_tree_item(key='h', value=labelShape['h'])
            tree_label_item.addChild(node_x)
            tree_label_item.addChild(node_y)
            tree_label_item.addChild(node_w)
            tree_label_item.addChild(node_h)
            tree_label_item.setExpanded(False)

            # 创建shape（方框），表示标签，展示在画布上
            shape = Shape(name=Shape.RECT)
            shape.set_label(label_text)

            # if label_click_num > 0:
            #     shape.setLabel(str(label_click_num))
            width = labelShape['w']
            height = labelShape['h']
            if width < 0 or height < 0:
                raise Exception("{} file is wrong".format(label_json_path))

            point1 = QPoint(int(labelShape['x']), int(labelShape['y']))
            point2 = QPoint(int(labelShape['x']) + int(labelShape['w']),
                            int(labelShape['y']))
            point3 = QPoint(int(labelShape['x']) + int(labelShape['w']),
                            int(labelShape['y']) + int(labelShape['h']))
            point4 = QPoint(int(labelShape['x']),
                            int(labelShape['y']) + int(labelShape['h']))
            shape.add_point(point1)
            shape.add_point(point2)
            shape.add_point(point3)
            shape.add_point(point4)

            shapes.append(shape)
            canvas.set_rect_tree_item(tree_label_item)
            canvas.set_editing()
            canvas.shape_tree[shape] = tree_label_item

        canvas.load_shapes(shapes)
        canvas.update()

    @staticmethod
    def save_path(parent_key, path):
        if parent_key == TOP_LEVEL_TREE_KEYS[0]:
            auto_save_label_path(path)

    def backend_process_monitor(self, is_ok, desc, *args, **kwargs):
        """Backend process status service

            :param is_ok: all process is alive if is_ok=True, or has some one process exit
            :param desc: describe all process info
            :param args: extend args
            :param kwargs: extend args
        """
        if not is_ok:
            self.backend_process_running = False
        logger.info('process status: %s, %s, %s, %s', is_ok, desc, args, kwargs)

    @staticmethod
    def _stop_service(service_name):
        is_ok, desc = bsa.stop_service(service_name=service_name)
        if not is_ok:
            logger.error('stop service %s failed, desc: %s', service_name, desc)
            return False
        logger.info('stop service %s success', service_name)
        return True

    def stop_multi_process(self):
        logger.info('begin to stop test')
        self._stop_service(self.SERVICE_NAME)
        logger.info('stop-test finished!')

    def exist_multi_process(self):
        bsa.exist_process(self.SERVICE_NAME)

    def _start_multi_process(self):
        # 结束之前的手机通信模块
        if g_app_context.get_info('phone', False):
            g_app_context.set_info('phone', False)
            g_data_source.finish()

        self.backend_process_running = True
        # 进入bin目录
        os.chdir(BIN_PATH)
        text = '******** start ui explore ********\n'
        set_log_text(text)
        run_type = g_project_manager.get_run_type()
        logger.info("run type is %s", run_type)

        run_programs = []
        # mc
        run_program = MC_PROCESS_AI_MODE_NAME
        if run_type == RunTypeText.UI_AI:
            run_program = MC_PROCESS_UI_AI_MODE_NAME
        run_programs.append(run_program)

        # io
        run_programs.append(IO_PROCESS_NAME)

        # agent
        run_program = "%s --mode=test --cfgpath=%s" % (AI_PROCESS_NAME, g_project_manager.get_project_property_file())
        run_programs.append(run_program)

        # ui
        if run_type == RunTypeText.UI_AI:
            run_program = "%s cfgpath %s" % (UI_PROCESS_NAME, g_project_manager.get_project_property_file())
            run_programs.append(run_program)

        # game_reg
        run_program = "%s cfgpath %s" % (GAMEREG_PROCESS_NAME, g_project_manager.get_project_property_file())
        run_programs.append(run_program)

        is_ok, desc = bsa.start_service(service_name=self.SERVICE_NAME,
                                        run_programs=run_programs,
                                        process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                        callback_func=self.backend_process_monitor,
                                        start_internal=10)
        if not is_ok:
            msg = "start {} service failed, {}\n".format(self.SERVICE_NAME, desc)
            text += msg
            logger.error(msg)
        else:
            msg = 'start {} service success, pid: {}\n'.format(self.SERVICE_NAME,
                                                               bsa.get_pids(service_name=self.SERVICE_NAME))
            text += msg
            logger.info(msg)
        set_log_text(text)


        # aiclient
        try:
            os.chdir(PHONE_CLIENT_PATH)
            # 启动 phone client，在SDKTool中启动失败
            logger.info('start phone client: %s', PHONE_CLIENT_PROCESS_NAME)
            is_ok, desc = bsa.start_service(service_name=self.SERVICE_NAME,
                                            run_programs=PHONE_CLIENT_PROCESS_NAME,
                                            process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                            callback_func=self.backend_process_monitor)
            text += desc
            time.sleep(1)
            if not is_ok and bsa.exist_process(service_name=self.SERVICE_NAME):
                logger.error("phone_client_process failed, %s", desc)
                text += "phone_client_process failed \n"
                raise Exception('start aiclient failed, will try again')
            else:
                text += "******please wait minutes to start******\n"

        except RuntimeError:
            # 第一次启动失败，尝试再启动一次
            is_ok, desc = bsa.start_service(run_programs=PHONE_CLIENT_PROCESS_NAME,
                                            service_name=self.SERVICE_NAME,
                                            process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                            callback_func=self.backend_process_monitor)
            time.sleep(1)
            if not is_ok and bsa.exist_process(service_name=self.SERVICE_NAME):
                set_log_text(text)
                return False

        set_log_text(text)
        return True

    def on_run(self):
        self.__right_tree.clear()
        try:
            # 设置run_result的路径
            project_path = g_project_manager.get_project_path()
            params = ui_explore_config_get()
            output_dir = 'data/run_result'
            if params and 'UiExplore' in params:
                output_dir = params['UiExplore'].get('OutputFolder')
            output_dir = os.path.join(project_path, output_dir)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            graph_dir = os.path.join(output_dir, 'Graph')
            action_dir = os.path.join(output_dir, 'Action')

            # remove graph and action dir and files
            logger.info('clear output dir: [%s, ]', output_dir)
            is_ok, desc = rm_dir_files(graph_dir)
            logger.debug("rm %s result: %s, %s", graph_dir, is_ok, desc)
            is_ok, desc = rm_dir_files(action_dir)
            logger.debug("rm %s result: %s, %s", action_dir, is_ok, desc)

            logger.info('set explore result:%s', graph_dir)
            explore_result_save_path(graph_dir)

            # 需删除'cfg/task/agent/Algorithm.json'，agentai的加载插件的逻辑需要
            project_path = g_project_manager.get_project_path()
            algorithm_json_path = os.path.join(project_path, AI_CONFIG_ALGORITHM_PATH)
            if os.path.exists(algorithm_json_path):
                os.remove(algorithm_json_path)

            # 从配置文件中读取参数并保存
            run_params = explore_run_get_params()
            max_click_number = run_params.get('MaxClickNumber', 100)
            explore_run_save_params(run_params)

            # run
            current_path = os.getcwd()
            # 启动进程
            success = self._start_multi_process()
            os.chdir(current_path)
            if not success:
                self._stop_service(self.SERVICE_NAME)
                return False

            # start run
            self._action_dir = action_dir
            self._max_click_number = max_click_number
            self._run_timer.start()

        except RuntimeError:
            exp = traceback.format_exc()
            logger.error(exp)

    @staticmethod
    def __display_clicked_image(image_path, text=''):
        img_data = cv2.imread(image_path)
        if img_data is None:
            return

        height, width, depth = img_data.shape

        if text:
            x = int(width / 3)
            y = int(height / 3)
            cv2.putText(img_data,
                        text,
                        (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2)

        rgb = cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB)

        image = QImage(rgb.data, width, height, width * depth, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        canvas.mouse_move_flag = False
        canvas.reset_state()
        canvas.load_pixmap(pixmap)
        canvas.setEnabled(True)
        canvas.update()

    def __run_progress_display(self):
        action_dir = self._action_dir
        max_click_number = self._max_click_number
        if not os.path.exists(action_dir):
            return

        raw_file_list = os.listdir(action_dir)
        file_list = list(filter(lambda img: img.endswith("jpg") or img.endswith("png"), raw_file_list))
        max_action_file_name = len(file_list)

        if max_action_file_name == 0:
            return

        # display image
        clicked_image_path = os.path.join(action_dir, '%s.jpg' % max_action_file_name)
        logger.info('clicked jpg:%s', clicked_image_path)
        text = '%s / %s' % (max_action_file_name, max_click_number)
        # set_log_text('run process: %s' % text)
        self.__display_clicked_image(clicked_image_path, text)

        # is over
        coverage_file = os.path.join(explore_result_get_path(), "coverage.json")
        if not self.backend_process_running or os.path.exists(coverage_file):
            if not self.backend_process_running:
                text = "ui auto explore failed due to backend process except exit, please check config and restart"
            else:
                text = "ui auto explore finished, you can check the result in next step"
            logger.info(text)
            set_log_text('%s' % text)
            if clicked_image_path:
                self.__display_clicked_image(clicked_image_path, '==end(reach max clicked number)==')

            logger.info('reach max click number or time out')
            logger.info('stop run timer')
            self._run_timer.stop()
            logger.info('stop backend process')
            self.stop_multi_process()

    def on_stop(self):
        """停止运行
        """
        self._run_timer.stop()
        self.stop_multi_process()

    def _cbx_text_changed(self, text):
        current_item = self.__right_tree.currentItem()
        current_item.setText(1, text)

    def on_click_run_param_item(self):
        self.__right_tree.clear()
        params_node = QTreeWidgetItem(self.__right_tree)
        params_node.setText(0, "参数设置")
        params = explore_run_get_params()
        new_params = RUN_PARAMS.copy()
        new_params.update(params)

        new_params = filter_params(new_params, UI_AUTO_EXPLORE_RUN_FILTER_KEYS)
        # 不显示ComputeCoverage 参数
        if "ComputeCoverage" in new_params:
            new_params.pop("ComputeCoverage")

        for param_key, value in new_params.items():
            if isinstance(value, bool):
                cbx_item = create_bool_tree_item(value)
                cbx_item.currentTextChanged.connect(self._cbx_text_changed)

                param_node = QTreeWidgetItem(params_node)
                param_node.setText(0, param_key)
                self.__right_tree.setItemWidget(param_node, 1, cbx_item)

                params_node.addChild(param_node)
            else:
                param_node = create_tree_item(key=param_key, value=value, edit=True)
                params_node.addChild(param_node)
        explore_run_save_params(new_params)
        params_node.setExpanded(True)

    def on_click_param_item(self):
        if bsa.exist_process(CNNTrainSample.TRAIN_SAMPLE_SERVICE_NAME):
            show_warning_tips('请先停止训练!')
            return

        self.__right_tree.clear()
        params_node = QTreeWidgetItem(self.__right_tree)
        params_node.setText(0, "参数设置")

        new_params = explore_train_get_params().copy()
        for k, v in TRAIN_PARAMS.items():
            if k not in new_params:
                new_params[k] = v

        for param_key, value in new_params.items():
            param_node = create_tree_item(key=param_key, value=value, edit=True)
            params_node.addChild(param_node)
        explore_train_save_params(new_params)
        params_node.setExpanded(True)

    def on_click_path_item(self, node, parent_node):
        # 0: "路径"， 1:路径值 2:对应的左树节点，比如"Step1: 样本自动标记"下的路径，则在第三列中存储的未“Step1: 样本自动标记”
        right_node = QTreeWidgetItem(self.__right_tree)
        node_text0 = node.text(0)
        right_node.setText(0, node_text0)

        node_text1 = node.text(1)
        right_node.setText(1, node_text1)

        parent_node_text0 = parent_node.text(0)
        self.save_path(parent_node_text0, node_text1)

        right_node.setText(2, parent_node_text0)

    def generate_real_samples(self, samples_dir):
        samples_list_item = QTreeWidgetItem(self.__right_tree)
        samples_list_item.setIcon(0, QIcon(QICON_IMGS[2][0]))
        samples_list_item.setText(0, "样本")
        samples_list_item.setText(2, samples_dir)
        get_file_list(samples_dir, samples_list_item, 1)
        samples_list_item.setExpanded(True)
        canvas.set_samples_tree_item(samples_list_item)
        if g_app_context.get_info('device_connected', False) and g_app_context.get_info("phone", False):
            g_app_context.set_info('enable_device_operation', True)

    def on_modify_sample(self):
        try:
            path = user_get_label_path()
            item = self.__left_tree.currentItem()
            # 清除之前的节点
            sub_nodes = get_sub_nodes(item)
            for sub_node in sub_nodes:
                item.removeChild(sub_node)
            # 重建子节点，刷新样本目录
            get_file_list(path, item, 1)
        except RuntimeError as e:
            logger.error(e)

    def on_package_sample(self):
        try:
            path = user_get_label_path()
            self.usr_label_image.set_path(path)
            self.usr_label_image.package_sample()
        except RuntimeError as e:
            logger.error(e)

    def on_train(self):
        try:
            train_sample_path = explore_train_get_data_path()
            self.__trainSample.set_sample_path(train_sample_path)
            self.__trainSample.run()
        except RuntimeError:
            exp = traceback.format_exc()
            logger.error(exp)

    def on_stop_train(self):
        try:
            self.__trainSample.finish_train()
        except RuntimeError:
            exp = traceback.format_exc()
            logger.error(exp)

    def on_analyze_train(self):
        try:
            train_sample_path = explore_train_get_data_path()
            self.__trainSample.set_sample_path(train_sample_path)
            self.__trainSample.analyze_result()
        except RuntimeError:
            exp = traceback.format_exc()
            logger.error(exp)

    def on_ui_graph(self):
        try:
            explore_path = explore_result_get_path()
            if not explore_path or not os.path.exists(explore_path):
                set_log_text('未找到结果目录:%s' % explore_path)
                return
            self.__explore_result.set_path(explore_path)
            self.__explore_result.ui_graph()
        except RuntimeError:
            exp = traceback.format_exc()
            logger.error(exp)

    def on_coverage(self):
        try:
            explore_path = explore_result_get_path()
            self.__explore_result.set_path(explore_path)
            self.__explore_result.coverage()
        except RuntimeError as e:
            logger.error(e)

    def on_ui_coverage(self):
        try:
            explore_path = explore_result_get_path()
            self.__explore_result.set_path(explore_path)
            self.__explore_result.ui_coverage()
        except RuntimeError as e:
            logger.error(e)

    def on_right_click(self):
        try:
            logger.debug("UI Explore on right click")
            item = self.__left_tree.currentItem()

            logger.debug("item 0 %s item 2 %s", item.text(0), item.text(2))
            right_menu = QMenu(self.__left_tree)

            if item.text(2) == ITEM_TYPE_IMAGE:
                right_menu.addAction(self.__actionChgImg)
                right_menu.addAction(self.__actionDelImg)

            right_menu.exec_(QCursor.pos())

            # reset current  item None
            self.__left_tree.setCurrentItem(None)

        except RuntimeError as e:
            logger.error(e)

    def on_action_add_usr_image(self):
        try:
            # self.usr_label_image.set_path(self.__usrLabelPath)
            self.usr_label_image.add_usr_image()
        except RuntimeError as e:
            logger.error(e)

    def on_action_chg_usr_image(self):
        try:
            self.usr_label_image.chg_usr_image()

            # 需要更改的图像为正在展示的图像，则需要清空正在展示的右树的数据
            if self._is_same_image():
                ui.tree_widget_right.clear()

        except RuntimeError as e:
            logger.error(e)

    def on_action_del_usr_image(self):
        try:
            # self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.usr_label_image.del_usr_image()

            # 需要删除的图像为正在展示的图像，则需要清空正在展示的右树的数据
            if self._is_same_image():
                ui.tree_widget_right.clear()
        except RuntimeError:
            exp = traceback.format_exc()
            logger.error(exp)

    def on_action_del_usr_dir(self):
        try:
            # self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.usr_label_image.del_usr_dir()
        except RuntimeError as e:
            logger.error(e)

    def on_action_add_folder(self):
        try:
            # self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.usr_label_image.add_folder()
        except RuntimeError as e:
            logger.error(e)

    @staticmethod
    def _is_same_image():
        if ui.tree_widget_left:
            left_node = ui.tree_widget_left.currentItem()
            left_node_name = left_node.text(0)
            right_top_nodes = get_tree_top_nodes(ui.tree_widget_right)
            right_node_name = None
            for node in right_top_nodes:
                if node.text(0) == 'fileName':
                    right_node_name = node.text(1)

            return left_node_name == right_node_name
        return False

    @staticmethod
    def _save_diff_mode_tree():
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.UI_AUTO_EXPLORE and pre_mode is not None:
            pre_tree = tree_mgr.get_object(pre_mode)
            return pre_tree.save_previous_rtree()

        tree_mgr.set_mode(Mode.UI_AUTO_EXPLORE)
        return True
