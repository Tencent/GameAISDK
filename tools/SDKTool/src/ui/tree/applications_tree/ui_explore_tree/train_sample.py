# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import time
import shutil
import logging
import threading
import json

import matplotlib.pyplot as plot
import zmq
from PyQt5.QtWidgets import QApplication

from ....canvas.ui_canvas import canvas
from ....canvas.canvas_signal import canvas_signal_inst
from ....dialog.tip_dialog import show_warning_tips, show_message_tips
from ....tree.applications_tree.ui_explore_tree.json_to_refine_det_txt import json_to_refine_det_txt
from ....utils import del_files, get_files_count, set_log_text
from .....subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from .....subprocess_service.process_timer import ProcessTimer
from .....project.project_manager import g_project_manager
from .....config_manager.ui_auto_explore.ui_explore_api import explore_train_get_params
from .define import TRAIN_PARAMS

platform = sys.platform


BASE_TRAIN_EPOCH = 55
_test_dataset_file = "test_dataset.txt"
_train_dataset_file = "train_dataset.txt"
REFINE_HC2NET_DATA_PTH = "Final_Refine_hc2net_version3_self_dataset.pth"


class TrainLogParam(object):
    def __init__(self):
        self.loss = []
        self.sum_loss = 0
        self.exit_paint = False
        self.exit_recv = False

        self.epoch = 0
        self.epoch_size = 0
        self.step = 0
        self.batch_size = 0

        self.current_epoch = 0
        self.current_step = 0
        self.notify_num = 0
        self.total_time = 0

    def set_exit_paint_log(self, flag):
        self.exit_paint = flag

    def set_exit_recv_log(self, flag):
        self.exit_recv = flag

    def set_exit(self, flag):
        self.exit_paint = flag
        self.exit_recv = flag

    def is_valid(self):
        return not self.exit_recv


class CNNTrainSample(object):
    TRAIN_SAMPLE_SERVICE_NAME = 'train_sample'
    ANALYZE_SERVICE_NAME = 'analyze_result'

    def __init__(self, sample_path):
        self.__train_sample_path = sample_path
        self.__logger = logging.getLogger('sdktool')
        self.__canvas = canvas
        # self.__ui = ui

        ai_sdk_path = os.environ.get('AI_SDK_PATH')
        self.__refine_det_path = os.path.join(ai_sdk_path, "Modules", "RefineDet")

        self.__run_result_path = None

        self.__pre_dir = None
        self.__grd_dir = None
        self.__results_dir = None

        self.__map_path = None
        self.__weight_file = \
            os.path.join(self.__refine_det_path,
                         "weights/Refine_hc2net_version3_320/model/Final_Refine_hc2net_version3_self_dataset.pth")
        # weight_file 由文件目录和文件名称组成。
        # 文件目录： --save_folder('weights'), --version('Refine_hc2net_version3') + '_' + --size(320), --date('model')
        # 文件名： 'Final_' + --version('Refine_hc2net_version3') + '_' + --dataset(self_dataset) + '.pth'

        self.__train_param_dict = {}
        self.__paint_log_thread = None
        self.__recvLogThread = None
        self.__mapThread = None
        self.__lock = threading.Lock()
        self.__train_log_param = None
        self.__process_running = False
        self.__socket = None

    def __init_test_map(self):
        """ 初始化test_map目录

        :return:
        """
        self.__run_result_path = os.path.join(g_project_manager.get_project_path(), "data", "run_result", "test_map")

        self.__pre_dir = os.path.join(self.__run_result_path, "pre")
        if not os.path.exists(self.__pre_dir):
            os.makedirs(self.__pre_dir)

        self.__grd_dir = os.path.join(self.__run_result_path, "grd")
        if not os.path.exists(self.__grd_dir):
            os.makedirs(self.__grd_dir)

        self.__results_dir = os.path.join(self.__run_result_path, "results")
        if not os.path.exists(self.__results_dir):
            os.makedirs(self.__results_dir)

        self.__map_path = os.path.join(self.__results_dir, "mAP.jpg")

    def set_sample_path(self, path):
        self.__train_sample_path = path

    def get_sample_path(self):
        return self.__train_sample_path

    def _clear_files(self):
        if self.__pre_dir and os.path.isdir(self.__pre_dir):
            del_files(self.__pre_dir)

        if self.__grd_dir and os.path.isdir(self.__grd_dir):
            del_files(self.__grd_dir)

        if self.__results_dir and os.path.isdir(self.__results_dir):
            del_files(self.__results_dir)

        if self.__map_path and os.path.exists(self.__map_path):
            os.remove(self.__map_path)

    def _pre_load_model(self):
        src_test_data_file = self._get_dataset_path(_test_dataset_file)
        dst_model_file = self._get_model_path()
        if not os.path.exists(dst_model_file) or not os.path.exists(src_test_data_file):
            self.__logger.error("weight file or test data not exist, model_file: {}, "
                                "test_data_file: {}".format(dst_model_file, _test_dataset_file))
            return False
        else:
            shutil.copyfile(dst_model_file, self.__weight_file)
        return True

    def _get_model_path(self):
        model_file = os.path.join(g_project_manager.get_project_path(), "data", REFINE_HC2NET_DATA_PTH)
        return model_file

    def _get_dataset_path(self, dataset_file):
        """
        :param dataset_file: train dataset or test dataset
        :return:
        """
        dataset_path = os.path.join(g_project_manager.get_project_path(), "data", dataset_file)
        return dataset_path

    def run(self):
        if not bsa.exist_service(service_name=self.TRAIN_SAMPLE_SERVICE_NAME):
            self.__logger.info("start train")
            self.__init_test_map()
            self._clear_files()
            is_ok, desc = self._train_sample()
            if is_ok:
                self._paint_train_log()
            else:
                show_warning_tips(desc)
        else:
            show_warning_tips('正在训练中，请先停止训练后再启动')

    def _train_sample(self):
        if not self.__train_sample_path or not os.path.exists(self.__train_sample_path):
            raise ValueError('train sample path(%s) is not valid' % self.__train_sample_path)

        image_count = get_files_count(self.__train_sample_path)
        if image_count <= 0:
            text = "failed, no image in {}, please check".format(self.__train_sample_path)
            show_warning_tips(text)
            return

        current_path = os.getcwd()
        if not os.path.exists(self.__refine_det_path):
            raise Exception("refineDetPath: {} is not exist".format(self.__refine_det_path))

        # 训练前，先删除上次训练结果文件
        if os.path.exists(self.__weight_file):
            os.remove(self.__weight_file)

        canvas_signal_inst.reset_state()
        self.__train_log_param = TrainLogParam()

        os.chdir(self.__refine_det_path)
        time.sleep(1)
        train_param_dict = explore_train_get_params().copy()
        for k, v in TRAIN_PARAMS.items():
            if k not in train_param_dict:
                train_param_dict[k] = v

        self.__train_param_dict = train_param_dict

        run_program_param_keys = ['batch_size', 'num_workers']
        run_program_params = dict()
        for param_key, param_value in train_param_dict.items():
            if param_key in run_program_param_keys:
                run_program_params[param_key] = param_value

        is_debug = bool(train_param_dict.get("is_debug", False))
        train_dataset_path = self._get_dataset_path(_train_dataset_file)
        test_dataset_path = self._get_dataset_path(_test_dataset_file)
        json_to_refine_det_txt(self.__train_sample_path, train_dataset_path, test_dataset_path, is_debug)

        max_epoch = train_param_dict.get("微调次数", 5)
        max_epoch = int(max_epoch) + BASE_TRAIN_EPOCH

        run_program = "python train_val.py --max_epoch {} --train_label_list {}".format(max_epoch, train_dataset_path)
        for k, v in run_program_params.items():
            run_program = " {} --{} {}".format(run_program, k, str(v))
        self.__logger.info(run_program)
        self.__process_running = True
        is_ok, desc = bsa.start_service(service_name=self.TRAIN_SAMPLE_SERVICE_NAME,
                                        run_programs=run_program,
                                        process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                        callback_func=self._process_monitor_callback)
        if not is_ok:
            self.__logger.error("start train sample failed: %s", desc)
        else:
            self.__logger.info('start train sample success '
                               'pid: %s', bsa.get_pids(service_name=self.TRAIN_SAMPLE_SERVICE_NAME))
        time.sleep(1)
        os.chdir(current_path)
        return is_ok, desc

    def _save_weight(self):
        src_test_data_file = self._get_dataset_path(_test_dataset_file)
        if not os.path.exists(self.__weight_file) or not os.path.exists(src_test_data_file):
            raise Exception("weight file or test data not exist, weight_file: {}, "
                            "test_data_file: {}".format(self.__weight_file, src_test_data_file))
        else:
            dst_model_file = self._get_model_path()
            shutil.copyfile(self.__weight_file, dst_model_file)

    def __build_socket(self):
        self.__delete_socket()
        context = zmq.Context()
        self.__socket = context.socket(zmq.PULL)
        self.__socket.bind("tcp://*:5558")

    def __delete_socket(self):
        try:
            if self.__socket:
                self.__socket.close()
        except BlockingIOError:
            self.__logger.error('failed to close socket')
        finally:
            self.__socket = None

    def _paint_train_log(self):
        set_log_text("训练网络模型")

        max_epoch = int(self.__train_param_dict.get("微调次数", 5))
        self.__train_log_param.epoch = max_epoch

        def _paint_log(train_log_param, lock):
            font1 = {'family': 'Times New Roman', 'weight': 'normal', 'size': 12}
            self.__logger.info("************start paint log************")

            while not train_log_param.exit_paint:
                if not self.__process_running:
                    self.__logger.error('remote process quit')
                    break

                time.sleep(3)
                speed = 0 if train_log_param.notify_num == 0 else \
                    train_log_param.total_time / train_log_param.notify_num
                avg_loss = 0 if train_log_param.notify_num == 0 else \
                    train_log_param.sum_loss / train_log_param.notify_num

                msg = 'epoch: %s/%s, step: %s/%s, speed: %.3f(s), avg_loss:%.3f' % (train_log_param.current_epoch,
                                                                                    train_log_param.epoch,
                                                                                    train_log_param.current_step,
                                                                                    train_log_param.step,
                                                                                    speed, avg_loss)
                self.__logger.info(msg)

                plot.figure(num=1, clear=True)
                plot.xlabel('epoch', font1)
                plot.ylabel('loss', font1)
                plot.plot(range(len(train_log_param.loss)), train_log_param.loss, '', c='g')
                if train_log_param.current_epoch < max_epoch or \
                        (train_log_param.current_epoch == train_log_param.epoch and
                         train_log_param.current_step < train_log_param.step):
                    plot.title('train ' + msg)
                else:
                    plot.title('train over, max epoch: {}'.format(max_epoch), font1)

                name = './test2.jpg'
                plot.savefig(name)
                # 加载图像文件
                canvas_signal_inst.canvas_show_img(name)

                if len(train_log_param.loss) > 0 and \
                        train_log_param.current_epoch == train_log_param.epoch and \
                        train_log_param.current_step == train_log_param.step:
                    self.__logger.info("reach max epoch")
                    break
            train_log_param.set_exit_paint_log(False)
            self.__logger.info("************exit paint log************")
            self.__logger.info('stop service(%s)', self.TRAIN_SAMPLE_SERVICE_NAME)
            # self.finish_train()

        self.__paint_log_thread = threading.Thread(target=_paint_log, args=(self.__train_log_param, self.__lock))
        self.__paint_log_thread.start()

        def _recv_log(socket, train_log_param, lock, paint_log_thread):
            """ if state = running, data format:
            {
                'state': 'running',
                'epoch': epoch,
                'epoch_size': epoch_size,
                'epoch_iter': iteration % epoch_size,
                'iteration': iteration,
                'al': al,
                'ac': ac,
                'ol': ol,
                'oc': oc,
                'batch_time': batch_time,
                'lr': lr
            }

            :param socket:
            :param train_log_param:
            :param lock:
            :param paint_log_thread:
            :return:
            """
            self.__logger.info("************start recv log************")
            all_finished = False
            while not train_log_param.exit_recv:
                if not self.__process_running:
                    self.__logger.error('remote process quit')
                    break

                self.__logger.debug("recv loss %s", train_log_param.loss)
                try:
                    data = socket.recv(flags=zmq.NOBLOCK)
                    if not data:
                        continue
                    self.__logger.info(b"recv log data is: %s", data)
                    data = json.loads(data.decode('utf-8'))

                except zmq.ZMQError as err:
                    self.__logger.warning("zmq receive warning: {}".format(err))
                    time.sleep(5)
                    continue

                self.__logger.debug("recv log data is %s", data)
                state = data.get('state')
                if state == 'over':
                    self._save_weight()
                    self.__logger.info("************recv over************")
                    all_finished = True
                    train_log_param.current_epoch = train_log_param.epoch
                    train_log_param.current_step = train_log_param.step
                    break

                cur_loss = data.get('al')
                cur_epoch = data.get('epoch')
                epoch_size = data.get('epoch_size', 1)
                epoch_iter = data.get('epoch_iter', 0)
                batch_time = data.get('batch_time', 0)

                train_log_param.total_time += batch_time
                train_log_param.current_epoch = int(cur_epoch - BASE_TRAIN_EPOCH)
                train_log_param.sum_loss += cur_loss
                train_log_param.notify_num += 1
                train_log_param.current_step = epoch_iter + 1
                train_log_param.step = epoch_size

                if (epoch_iter + 1) == epoch_size:
                    train_log_param.loss.append(cur_loss)

                self.__logger.info("cur_epoch:%s, BASE_TRAIN_EPOCH:%s, epoch_size:%s, epoch_iter:%s",
                                   cur_epoch, BASE_TRAIN_EPOCH, epoch_size, epoch_iter)

            self.__logger.info("************exit recv log************")
            train_log_param.set_exit_recv_log(False)

            # 等待绘制线程退出
            paint_log_thread.join(10)

            # 设置训练结束
            self.finish_train()
            if not all_finished:
                self.__logger.error('train task is not finished!')

        self.__socket = None
        self.__build_socket()
        self.__recvLogThread = threading.Thread(target=_recv_log,
                                                args=(self.__socket,
                                                      self.__train_log_param,
                                                      self.__lock,
                                                      self.__paint_log_thread))
        self.__recvLogThread.start()

    def _compute_map(self):
        self.__logger.info("********start compute map************")
        while self.__process_running:
            data = self.__socket.recv().decode('utf-8')
            self.__logger.info("recv log data is %s", data)
            if data == 'over':
                self.__logger.info("recv over")
                break
            else:
                time.sleep(1)

        if os.path.exists(self.__map_path):
            self.__logger.info("process success")
            # 加载图像文件
            canvas_signal_inst.canvas_show_img(self.__map_path)
        else:
            raise Exception("image not exist {}".format(self.__map_path))
        self.__logger.info("********exit compute map********")

    def _process_monitor_callback(self, service_state, desc, *args, **kwargs):
        self.__logger.info("service state(%s), desc(%s), args: %s, kwargs:%s", service_state, desc, args, kwargs)
        if service_state != ProcessTimer.SERVICE_STATE_RUNING:
            self.__process_running = False

    def _show_compute_process(self, target_count=0):
        if target_count == 0:
            show_warning_tips('target count is 0')
            return

        if not self.__pre_dir or not os.path.exists(self.__pre_dir):
            show_warning_tips('target dir(%s) is empty' % self.__pre_dir)
            return

        txt_count = get_files_count(self.__pre_dir, ".txt")
        self.__canvas.create_process_bar("计算map", "处理中", 0, target_count)
        self.__logger.info("********start show compute information************")
        all_finished = False
        while self.__process_running:
            if txt_count >= target_count:
                all_finished = True
                break
            self.__logger.debug("txt count is %s, target_count %s", txt_count, target_count)
            self.__canvas.set_bar_cur_value(txt_count)
            QApplication.processEvents()
            time.sleep(0.5)
            txt_count = get_files_count(self.__pre_dir, ".txt")

        self.__canvas.close_bar()
        if all_finished:
            show_message_tips("处理完成")
        else:
            show_warning_tips('分析进程异常退出')
        self.__logger.info("********exit show compute information************")

    def analyze_result(self):
        if bsa.has_service_running():
            show_warning_tips('已有服务在运行，请先停止')
            return

        current_path = os.getcwd()
        if not os.path.exists(self.__refine_det_path):
            show_warning_tips("refineDetPath: {} is not exist".format(self.__refine_det_path))
            return
            # raise Exception("refineDetPath: {} is not exist".format(self.__refine_det_path))

        os.chdir(self.__refine_det_path)
        self.__init_test_map()
        self._clear_files()
        if not self._pre_load_model():
            show_warning_tips("预加载model失败")
            return

        # 必须有训练结果文件，才能进行分析
        if not self.__weight_file or not os.path.exists(self.__weight_file):
            self.__logger.warning('taret file(%s) is not found', self.__weight_file)
            show_warning_tips('请先完成训练!')
            return

        target_count = 0
        test_dataset_path = self._get_dataset_path(_test_dataset_file)
        with open(test_dataset_path) as fd:
            content = fd.read()
            lines = content.strip().strip('\n').strip('\r').split('\n')
            target_count = len(lines)

        run_program = "python detectmap.py --save_folder {} --label_list {}".format(self.__run_result_path,
                                                                                    test_dataset_path)
        self.__logger.info("**********detectmap**********")

        self.__process_running = True
        self.__socket = None
        self.__build_socket()

        is_ok, desc = bsa.start_service(service_name=self.ANALYZE_SERVICE_NAME,
                                        run_programs=run_program,
                                        process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                        callback_func=self._process_monitor_callback)

        if not is_ok:
            self.__logger.error("start %s service failed, %s", self.ANALYZE_SERVICE_NAME, desc)
            show_warning_tips(desc)
            self.__delete_socket()
            return
        self.__logger.info('start %s service success, pid: %s', self.ANALYZE_SERVICE_NAME,
                           bsa.get_pids(service_name=self.ANALYZE_SERVICE_NAME))

        os.chdir(current_path)

        set_log_text("计算mAP")

        self.__mapThread = threading.Thread(target=self._compute_map)
        self.__mapThread.start()

        # move function ShowCompProcess to thread, may be wrong
        self._show_compute_process(target_count)
        self.__mapThread.join(5)
        self.__mapThread = None
        self.__delete_socket()
        self.finish_map()

    def finish_map(self):
        self.__logger.info("finish map process pid: %s", bsa.get_pids(service_name=self.ANALYZE_SERVICE_NAME))
        is_ok, _ = bsa.stop_service(service_name=self.ANALYZE_SERVICE_NAME)
        if not is_ok:
            self.__logger.error("stop train sample failed")
        else:
            self.__logger.info("stop train sample success")

    def finish_train(self):
        self.__delete_socket()
        self.__logger.info("finish train process pid: %s", bsa.get_pids(service_name=self.TRAIN_SAMPLE_SERVICE_NAME))
        is_ok, desc = bsa.stop_service(service_name=self.TRAIN_SAMPLE_SERVICE_NAME)
        if not is_ok:
            self.__logger.error("stop train sample failed，desc:%s", desc)
        else:
            self.__logger.info("stop train sample success")
        if self.__train_log_param is not None:
            self.__lock.acquire()
            self.__train_log_param.set_exit(True)
            self.__lock.release()
            time.sleep(2)
