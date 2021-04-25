# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import re

import logging
import time
import traceback
import os
from collections import OrderedDict
import urllib.request
import threading
import platform

import matplotlib.pyplot as plot
import numpy
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import QComboBox, QTreeWidgetItem

from ...canvas.data_source import DataSource
from ...main_window.tool_window import ui
from ....common.define import TRAIN_NAME, CONFIG_RECORD, START_RECORD, STOP_RECORD, START_TRAIN, STOP_TRAIN, \
    BOOL_FLAGS, ACTION_SAMPLE_PATH, RECORD_ANDROID_GUIDANCE_IMG, RECORD_WINDOWS_GUIDANCE_IMG, SDK_PATH, BIN_PATH
from ...canvas.canvas_signal import canvas_signal_inst
from ...dialog.label_dialog import LabelDialog
from ...dialog.tip_dialog import show_warning_tips
from ...utils import set_log_text, get_sub_nodes, create_tree_item, ExecResult, get_tree_top_nodes, save_action, \
    valid_number_value, filter_info_log, is_image
from .train_data import TrainData
from ....context.app_context import AppContext
from ....project.project_manager import g_project_manager
from ....subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from ....common.utils import backend_service_monitor
from ....WrappedDeviceAPI.wrappedDeviceConfig import DeviceType

IS_WINDOWS_SYSTEM = platform.platform().lower().startswith('win')
if IS_WINDOWS_SYSTEM:
    from ....WrappedDeviceAPI.deviceAPI.pcDevice.windows.win32driver import probe, by


logger = logging.getLogger("sdktool")


class TrainNode(QObject):
    ACTION_SAMPLE_SERVICE_NAME = 'train_node_action_sample'
    AISDK_TRAIN_SERVICE_NAME = 'train_node_train'

    clear_right_tree_signal = pyqtSignal(ExecResult)
    log_signal = pyqtSignal(str)
    run_signal = pyqtSignal(str, str, bool)

    def __init__(self):
        super().__init__()
        # self.__record_process = None
        self.__train_process = None
        self.__node = None
        self.__data = TrainData()
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__over = False
        self._http_server_port = 52808
        self._is_training = False

    def create_node(self, run_node):
        if run_node is None:
            logger.error("run node is none, create train node failed")
            return

        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        self.__right_tree.clear()

        sub_nodes = get_sub_nodes(run_node)
        for sub_node in sub_nodes:
            if sub_node.text(0) == TRAIN_NAME:
                self.__node = sub_node
                break

        if self.__node is None:
            self.__node = create_tree_item(key=TRAIN_NAME, edit=False)
            run_node.addChild(self.__node)
            run_node.setExpanded(True)
        else:
            for _ in range(self.__node.childCount()):
                self.__node.takeChild(0)

        sub_names = [CONFIG_RECORD, START_RECORD, STOP_RECORD, START_TRAIN, STOP_TRAIN]
        for sub_name in sub_names:
            self.__node.addChild(create_tree_item(key=sub_name, node_type=sub_name, edit=False))

        self.__node.setExpanded(True)

    def config_record(self):
        # 保存右树
        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        self.__right_tree.clear()
        param = self.__data.load_record_data()
        for key, value in param.items():
            self.create_complex_node(key=key, value=value)

    def _combobox_text_changed(self, text):
        current_item = self.__right_tree.currentItem()
        current_item.setText(1, text)

    def create_complex_node(self, key, value, root=None, edit_flag=True):
        # 0: key, 1:value, 2:type
        if root is None:
            sub_node = QTreeWidgetItem(self.__right_tree)
            sub_node.setText(0, key)
        else:
            sub_node = create_tree_item(key=key, edit=edit_flag)
            root.addChild(sub_node)
            root.setExpanded(True)

        logger.debug("value %s type %s", value, type(value))
        if isinstance(value, bool):
            combobox = QComboBox()
            combobox.addItems(BOOL_FLAGS)
            # combobox.setCurrentIndex(-1)
            combobox.setCurrentText(str(value))
            combobox.currentTextChanged.connect(self._combobox_text_changed)
            sub_node.setText(1, str(value))
            self.__right_tree.setItemWidget(sub_node, 1, combobox)

        elif isinstance(value, (int, float, str)):
            logger.debug("key %s value %s type str", key, value)
            sub_node.setText(1, str(value))
            sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)

        elif isinstance(value, (dict, OrderedDict)):
            logger.debug("value %s type dict", value)
            for sub_key, sub_value in value.items():
                self.create_complex_node(key=sub_key, value=sub_value, root=sub_node, edit_flag=edit_flag)

            sub_node.setExpanded(True)

    @staticmethod
    def _stop_canvas_phone():
        data_source = DataSource()
        data_source.finish()

    def show_train_info(self):
        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        self.__right_tree.clear()
        network_param = self.__data.get_network_parameter()
        if network_param is None:
            logger.error("train info is none")
            return

        # 展示，不可编辑
        for key, value in network_param.items():
            item = QTreeWidgetItem(self.__right_tree)
            item.setText(0, key)
            item.setText(1, str(value))

    def show_record_info(self):
        param = self.__data.load_record_data()
        if param is None:
            return
        # 展示，不可编辑
        for key, value in param.items():
            item = QTreeWidgetItem(self.__right_tree)
            item.setText(0, key)
            item.setText(1, str(value))

    def is_training(self):
        return bsa.exist_service(service_name=self.AISDK_TRAIN_SERVICE_NAME)

    def is_recording(self):
        return bsa.exist_process(self.ACTION_SAMPLE_SERVICE_NAME)

    def _notify_record_process_stop(self):
        """ 通知录制进程退出

        :return:
        """
        def notify_record_process_stop():
            cmd = 'http://127.0.0.1:%s?method=quit' % self._http_server_port
            logger.info('http get request: %s', cmd)
            urllib.request.urlopen(cmd)

        pthread = threading.Thread(target=notify_record_process_stop, name='notify_record_process_stop', daemon=True)
        pthread.start()
        pthread.join(5)

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

    def start_record(self):
        # 判断是否已启动录制程序
        if bsa.exist_process(self.ACTION_SAMPLE_SERVICE_NAME):
            msg = "record is already start..."
            logger.info(msg)
            set_log_text(msg)
            return

        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        self.__right_tree.clear()

        try:
            # 转换为录制所需要的配置文件
            self.__data.save_record_data()
            self.__data.save_sample_action()

            current_path = os.getcwd()
            os.chdir(ACTION_SAMPLE_PATH)
            time.sleep(0.5)

            data_source = DataSource()
            data_source.finish()

            app_ctx = AppContext()
            app_ctx.set_info("phone", False)

            serial = app_ctx.get_info("phone_serial", None)
            device_type = g_project_manager.get_device_type()
            if serial is None and device_type == DeviceType.Windows.value:
                qpath = g_project_manager.get_window_qpath()
                serial = self._get_hwnd_by_qpath(qpath)

            if serial:
                run_program = "python main.py -s %s -p %s -m %s" % (serial, self._http_server_port, device_type)
            else:
                run_program = "python main.py -p %s -m %s" % (self._http_server_port, device_type)

            is_ok, desc = bsa.start_service(service_name=self.ACTION_SAMPLE_SERVICE_NAME,
                                            run_programs=run_program,
                                            process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                            callback_func=backend_service_monitor,
                                            start_internal=10)
            if not is_ok:
                msg = "start service %s failed, %s" % (self.ACTION_SAMPLE_SERVICE_NAME, desc)
                raise RuntimeError(msg)
            else:
                logger.info("start service %s success", self.ACTION_SAMPLE_SERVICE_NAME)
            os.chdir(current_path)

            self.run_signal.emit('record', STOP_RECORD, True)

            if device_type == DeviceType.Android.value:
                image_name = RECORD_ANDROID_GUIDANCE_IMG
            elif device_type == DeviceType.Windows.value:
                image_name = RECORD_WINDOWS_GUIDANCE_IMG
            else:
                raise ValueError('unknown device type:%s' % device_type)

            canvas_signal_inst.canvas_show_img(image_name)
            self.show_record_info()
            set_log_text("****start record*****")
        except RuntimeError as err:
            cb_msg = traceback.format_exc()
            msg = "start record failed: {}\n traceback {}".format(str(err), cb_msg)
            logger.error(msg)
            set_log_text(msg)

    def _stop_record(self):
        # 尝试通过http请求通知录制进程退出
        if bsa.exist_service(self.ACTION_SAMPLE_SERVICE_NAME):
            self._notify_record_process_stop()

        is_ok, _ = bsa.stop_service(service_name=self.ACTION_SAMPLE_SERVICE_NAME)
        if not is_ok:
            logger.error("stop service %s failed", self.ACTION_SAMPLE_SERVICE_NAME)
            return
        logger.info("stop service %s success", self.ACTION_SAMPLE_SERVICE_NAME)
        self.run_signal.emit('record', '', False)
        set_log_text('stop record success')

    def stop_record(self):
        dlg = LabelDialog(text="please confirm to stop record sample", title="confirm")
        dlg.finish_signal.connect(self._stop_record)
        dlg.pop_up()

    def save_record_config(self):
        """ 保存录制的配置

        :return:
        """
        tree_param = OrderedDict()
        top_level_nodes = get_tree_top_nodes(self.__right_tree)
        for top_level_node in top_level_nodes:
            node_key = top_level_node.text(0)
            if top_level_node.childCount() == 0:
                node_value = top_level_node.text(1)
                tree_param[node_key] = node_value
            else:
                tree_param[node_key] = save_action(top_level_node)

        valid_number_value(tree_param)
        # 添加保存路径
        self.__data.save_record_data(tree_param)

    @staticmethod
    def _parser_acc_log(str_line):
        # 以后面字符串为例， without lstm:'Iteration 0....20: train_acc is 0.5877976190476191 and val_acc is 0.6546875'
        iter_info_no_lstm = re.findall(r"Iteration (.+?): train_acc is", str_line)
        # NetworkLSTM: Iter 5....20: train_acc is 0.6646706576118926 and val_acc is 0.6973478939157566
        iter_info_lstm = re.findall(r"Iter (.+?): train_acc is", str_line)

        iter_info = iter_info_lstm if len(iter_info_lstm) > len(iter_info_no_lstm) else iter_info_no_lstm

        if len(iter_info) < 1:
            return -1, -1
        # ['0....20']--->'0....20'
        sub_iter_info = iter_info[0]

        # '0....20'--->['0', '20']
        iter_data = sub_iter_info.split('....')

        # '0'--->0
        iter_data = int(iter_data[0])

        train_acc_info = re.findall(r"train_acc is (.+?) and val_acc is", str_line)
        if len(train_acc_info) < 1:
            return -1, -1

        # ['0.5877976190476191'(str)]--->0.5877976190476191
        acc_data = float(train_acc_info[0])

        return iter_data, acc_data

    @staticmethod
    def _parser_progress(line):
        # 17/18 [===========================>..] - ETA: 1s - loss: 8.9437 - acc: 0.9062
        # 日志举例：48/48 [==============================] - 6s 115ms/step - loss: 0.5667 - out_task0
        # target_line = re.findall(r"out_task0_loss:(.+?)out_task1_loss: ", line)
        target_line = re.findall(r"loss:", line)
        if len(target_line) == 0:
            return -1, -1
        try:
            cur_num_index = line.index('/')
            cur_num = line[0:cur_num_index]
            cur_num = int(cur_num)
            # 截取cur_num到结尾的字符
            batch_num = line[cur_num_index+1:]
            batch_num = batch_num.split()[0]
            batch_num = int(batch_num)
            return cur_num, batch_num
        except RuntimeError as err:
            logger.error("error: %s", str(err))
            return -1, -1

    def _parser_log(self):
        if self.__train_process is None:
            return -1, -1, -1, -1, None

        self.__train_process.stdout.flush()
        line = self.__train_process.stdout.readline()
        if line is None:
            return -1, -1, -1, -1, None
        try:
            str_line = line.decode('utf-8')
        except ValueError as err:
            logger.error('error line:%s', str(err))
            logger.error('error line:%s', line)
            return -1, -1, -1, -1, None
        iter_data, acc_data = self._parser_acc_log(str_line)
        cur_num, batch_num = self._parser_progress(str_line)

        return iter_data, acc_data, cur_num, batch_num, str_line

    def _paint_train_log(self):
        network_param = self.__data.get_network_parameter()
        if network_param is None:
            logger.error("network param is none")
            return

        begin = time.time()
        # 获取最大训练值
        max_epoch = network_param['trainIter']
        max_epoch = int(max_epoch)

        def _paint_windows_percent(cur_iter, cur_num, batch_num, percent_data, time_data):
            # 绘制进度图
            if cur_num >= 0:
                # 如：epoch为20, batch_num=48，共计20×48个数据
                max_data = max_epoch * batch_num
                # 单位秒
                current = cur_iter * batch_num + cur_num
                percent = int(current * 100.0 / max_data)
                if percent in percent_data:
                    return
                percent_data.append(percent)
                cur_time = time.time()
                cost = int((cur_time - begin) * 1000)
                time_data.append(cost)

                plot.plot(time_data, percent_data, '', c='g')

        def _paint_Linux_percent(cur_iter, cur_num, batch_num, percent_data, time_data, pre_time):
            if -1 not in [batch_num, cur_num]:
                # 如：epoch为20, batch_num=48，共计20×48个数据
                max_data = max_epoch * batch_num
                cur_time = time.time()
                interval = cur_time - pre_time
                batch_cost = interval / batch_num
                for i in range(1, batch_num + 1):
                    # 单位秒
                    current = cur_iter * batch_num + i
                    percent = int(current * 100.0 / max_data)
                    if percent in percent_data:
                        continue

                    percent_data.append(percent)

                    cur_time = time.time()
                    cost = int((cur_time - begin) * 1000)
                    time_data.append(cost)

                    plot.plot(time_data, percent_data, '', c='g')
                    time.sleep(batch_cost)
                    # 保存图像
                    plot_image_path = './test2.jpg'
                    plot.savefig(plot_image_path)

                    canvas_signal_inst.canvas_show_img(plot_image_path)

        def _paint_log():
            font1 = {'family': 'Times New Roman', 'weight': 'normal', 'size': 15}
            iter_datas = []
            acc_datas = []
            cur_iter = 0
            pre_time = begin
            percent_data = []
            time_data = []

            logger.info("************start paint log************")
            self.__over = False
            log_text = ''
            while not self.__over:
                try:
                    iter_data, acc_data, cur_num, batch_num, str_line = self._parser_log()

                    # 记录日志内容
                    if str_line is not None:
                        str_line = filter_info_log(str_line)
                        log_text += str_line
                        self.log_signal.emit(log_text)

                    if -1 not in [iter_data, acc_data]:
                        # 日志输出的迭代次数从0开始
                        iter_data = iter_data + 1
                        iter_datas.append(iter_data)
                        acc_datas.append(acc_data)
                        cur_iter = iter_data

                    # 清空plot
                    plot.close('all')
                    _, (ax1, ax2) = plot.subplots(2, 1)
                    # ax2 = plot.subplot(2, 1, 2)
                    plot.sca(ax2)
                    # 绘制x轴，y轴
                    plot.xlabel('epoch', font1)
                    plot.ylabel('acc', font1)
                    # x的范围
                    plot.xticks(numpy.arange(1, max_epoch+1, step=1))
                    if len(iter_datas) > 0:
                        plot.plot(iter_datas, acc_datas, '', c='g')

                    # 绘制标题
                    if cur_iter < max_epoch:
                        plot.title('train(epoch current/max: {}/{})'.format(cur_iter, max_epoch), font1)
                    else:
                        plot.title('train over, max epoch: {}'.format(max_epoch), font1)
                        self.__over = True

                    # ax1 = plot.subplot(2, 1, 1)
                    plot.sca(ax1)
                    # 绘制x轴
                    plot.title('process')
                    plot.xlabel('cost time(ms)', font1)
                    # 绘制y轴
                    plot.ylabel('percent(%)', font1)
                    plot.plot(time_data, percent_data, '', c='g')
                    plot.tight_layout()

                    # 绘制进度图
                    if IS_WINDOWS_SYSTEM:
                        _paint_windows_percent(cur_iter, cur_num, batch_num, percent_data, time_data)
                    else:
                        _paint_Linux_percent(cur_iter, cur_num, batch_num, percent_data, time_data, pre_time)
                        pre_time = time.time()

                    # 保存图像
                    plot_image_path = 'test2.jpg'
                    plot.savefig(plot_image_path)
                    if not is_image(plot_image_path):
                        continue

                    # 加载图像文件
                    canvas_signal_inst.canvas_show_img(plot_image_path)

                    if self.__over:
                        ai_sdk_path = os.environ.get('AI_SDK_PATH')
                        if ai_sdk_path is None:
                            ai_sdk_path = SDK_PATH

                        log_text += "train over....\n save mode to path: '{}/data/ImitationModel/'.".format(ai_sdk_path)
                        self.log_signal.emit(log_text)
                        plot.close(1)
                except RuntimeError as e:
                    exp = traceback.format_exc()
                    logger.error("************ %s %s ****", str(e), exp)

        paint_log_thread = threading.Thread(target=_paint_log, args=())
        paint_log_thread.start()

    def start_train(self):
        # 判断是否已启动训练程序
        if bsa.exist_service(service_name=self.AISDK_TRAIN_SERVICE_NAME):
            logger.info("train is already start...")
            set_log_text("train is already start...")
            return

        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        self.__right_tree.clear()
        try:
            # 停止已有连接
            data_source = DataSource()
            data_source.finish()

            app_ctx = AppContext()
            app_ctx.set_info("phone", False)

            # 进入bin目录
            current_path = os.getcwd()
            os.chdir(BIN_PATH)
            time.sleep(1)
            project_config_path = g_project_manager.get_project_property_file()
            run_program = 'python agentai.py --mode=train --cfgpath=%s' % project_config_path

            is_ok, desc = bsa.start_service(service_name=self.AISDK_TRAIN_SERVICE_NAME,
                                            run_programs=run_program,
                                            process_param_type=bsa.SUBPROCESS_STDOUT_TYPE,
                                            callback_func=backend_service_monitor)
            if not is_ok:
                raise Exception('start service {} failed, {}'.format(self.AISDK_TRAIN_SERVICE_NAME, desc))

            self.__train_process = bsa.get_processes(self.AISDK_TRAIN_SERVICE_NAME)
            os.chdir(current_path)
            self.run_signal.emit('train', STOP_TRAIN, True)

            # 显示训练信息
            self.show_train_info()
            set_log_text("start train")
            self._is_training = True

            # 绘制训练信息
            self._paint_train_log()
        except RuntimeError as err:
            msg = traceback.format_exc()
            msg = "start train failed: {}, traceback {}".format(err, msg)
            logger.error(msg)
            set_log_text(msg)

    def _stop_train(self):
        self.run_signal.emit('train', '', False)
        if not bsa.exist_service(service_name=self.AISDK_TRAIN_SERVICE_NAME):
            return
        if not self._is_training:
            return
        logger.info("stop train process")
        bsa.stop_service(service_name=self.AISDK_TRAIN_SERVICE_NAME)

        self.__train_process = None
        self._is_training = False

    def stop_train(self):
        self.__over = True

        # 等待1s,等待线程处理结束
        set_log_text('stop train..')
        self._stop_train()
        time.sleep(1)
        app_ctx = AppContext()
        app_ctx.set_info("phone", True)

    def finish(self):
        self._stop_record()
        self._stop_train()
